from io import BytesIO
import sqlite3
import base64
import re
import dash
import pandas as pd
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from config import db_path
from dash import html, dcc
from dash_bootstrap_templates import load_figure_template
from transliterate import translit
from fuzzywuzzy import fuzz
from wordcloud import WordCloud

#request max and min vacancy dates from db
with sqlite3.connect(db_path) as db:
    query_df = 'SELECT * FROM salaries_view'
    df = pd.read_sql(query_df, db)

    query_min_date = 'SELECT MIN(date) FROM salaries_view'
    query_max_date = 'SELECT MAX(date) FROM salaries_view'
    cur = db.cursor()
    min_date = cur.execute(query_min_date).fetchone()[0]
    max_date = cur.execute(query_max_date).fetchone()[0]

#define grades list
grades_list = list(df.grade.unique())
grades_list.remove(None)
grades_list.append('Все грейды')

#define roles in HH dataset
roles_list = list(df.hh_role.unique())
roles_list.remove(None)
roles_list.append('Все роли')

#parts of dashboard
header_card = \
dbc.Row([
    dbc.Col(
        html.Div(
            html.H2(
                children='Анализ рынка IT-вакансий РФ', 
                style={'text-align': 'center'}
            )
        ), width=15
    )]
)

about_card = \
dbc.Row([
    html.H4('Интро'),
    dbc.Row([
        html.Br(),
        html.Br(),
        html.Label('В данном анализе рассматривается 4 сайта с вакансиями IT рынка РФ'),
        html.Label('HabrCareer. Дата начала парсинга - 24 октября 2022'),
        html.Label('GeekJob. Дата начала парсинга - 27 октября 2022'),
        html.Label('GetMatch. Дата начала парсинга - 31 октября 2022'),
        html.Label('HeadHunter. Дата начала парсинга - 14 ноября 2022')
    ], style={'text-align': 'left'})
])

salary_part = \
dbc.Row([
    html.H4('График зарплат'),
    html.Br(),
    html.Br(),
    dbc.Row([
        html.Label('Данный график показывает распределение зарплат.'),
        html.Label('Как считается зарплата?'),
        html.Label('1. Все зарплаты указаны после вычета налогов. Это делается ещё на этапе парсинга.'),
        html.Label('2. Как правило, в вакансиях указывается зарплатная вилка. Где указан диапазон - берётся среднее число, в остальных случаях берётся указанное число.'),
        html.Label(id='total_count'),
        html.Label(id='count')
    ], style={'text-align': 'left'}),
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                dcc.Graph(id='salaries_graph')
            ),
            html.Abbr('Фильтр по датам', title='Отфильтровать датасет по дате публикации вакансий (включительно)'),
            dbc.Col([
                dcc.DatePickerRange(
                    id='date_picker',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date
                )]),
        ], width=9),
        dbc.Col([
            html.Label('Выбрать датасет'),
            dcc.Dropdown(
                options=['HeadHunter', 'HabrCareer', 'GeekJob', 'GetMatch', 'Все источники'],
                value='Все источники',
                id='dataset_dropdown',
                style={'color': 'black', 'background-color': 'white'}
            ),
            html.Br(),
            html.Abbr('Выбрать грейд', title='Отфильтровать по грейду\nПлохо работает с датасетами где явно не указан грейд (HeadHunter, GeekJob)\n"Все грейды" включает вакансии, где грейд не был указан'),
            dcc.Dropdown(
                options=['Intern', 'Junior', 'Middle', 'Senior', 'Lead', 'Все грейды'],
                value='Все грейды',
                id='grade_dropdown',
                style={'color': 'black', 'background-color': 'white'}
            ),
            html.Br(),
            html.Abbr("Выбрать валюту", title='Выбрать в какой валюте была указана зарплата.\nВсе валюты конвертируются в рубли по курсу на дату публикации вакансии.'),
            dcc.Dropdown(
                options=['₽', '$', '€', 'Все валюты'],
                value='Все валюты',
                id='currency_dropdown',
                style={'color': 'black', 'background-color': 'white'}
            ),
            html.Br(),
            html.Abbr('Выбрать профессиональную роль', title='Только для датасета с HeadHunter'),
            dcc.Dropdown(
                options=list(roles_list),
                value='Все роли',
                id='hh_roles_dropdown',
                style={'color': 'black', 'background-color': 'white'}
            ),
            html.Br(),
            html.Br(),
            html.Abbr("Обработка выбросов", title='Убирает выбросы по 1% двухстороннему перцентилю'),
            dcc.RadioItems(
                options=['Все данные', 'Убрать выбросы'],
                value='Все данные',
                id='hh_outliers'
            ),
            html.Br(), html.Br(),
            html.Abbr("Доп. статистика", title="Показать дополнительную статистику \nQn - n'ый перцентиль"),
            dcc.RadioItems(
                options=['Посчитать статистич. параметры', 'Очистить'], 
                value='Очистить график',
                id='stats'
            )
        ])
    ])
])

grade_part = \
dbc.Row([
    html.H4('График грейдов'),
    html.Br(),
    html.Br(),
    dbc.Row([
        html.Label('На данном графике представлено процентное соотношение вакансий с разбивкой по грейдам.'),
        html.Label('Характеристика по источникам:'),
        html.Label('1. HeadHunter. Грейд явно не указан в вакансии. Он вытащен на основе названия вакансий.'),
        html.Label('2. GeekJob. То же самое.'),
        html.Label('3. HabrCareer. Грейд указан явно в вакансии. \
                    При том этот источник является одним из самых популярных в ру сегменте => по нему можно относительно точно измерить рынок.'),
        html.Label('4. GetMatch. Грейд указан явно, но сайт для высоких грейдов => точно рынок не измерить.'),
    ], style={'text-align': 'left'}),
    dbc.Col([
        dcc.Loading(
            dcc.Graph(id='grades_graph')
        ),
    ], width=9),
    dbc.Col([
        html.Label('Выбрать датасет'),
        dcc.Dropdown(
            options=['HeadHunter', 'HabrCareer', 'GeekJob', 'GetMatch', 'Все источники'],
            value='Все источники',
            id='dataset_dropdown_1',
            style={'color': 'black', 'background-color': 'white'}
        ),
        html.Br(),
        html.Abbr("Фильтр по датам", title='Отфильтровать датасет по дате публикации вакансий (включительно)'),
        dcc.DatePickerRange(
            id='date_picker1',
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=min_date,
            end_date=max_date
        )
    ])
])

activity_part = \
dbc.Row([
    html.H4('График активности найма по компаниям'),
    html.Br(),
    html.Br(),
    dbc.Row([
        html.Label('Показывает топ-10 компаний по количеству вакансий в указанном источнике.')
    ], style={'text-align': 'left'}),
    dbc.Col([
        dcc.Loading(
            dcc.Graph(id='activity_graph')
        ),
    ], width=9),
    dbc.Col([
        html.Label('Выбрать датасет'),
        dcc.Dropdown(
            options=['HeadHunter', 'HabrCareer', 'GeekJob', 'GetMatch', 'Все источники'],
            value='Все источники',
            id='dataset_dropdown_2',
            style={'color': 'black', 'background-color': 'white'}
        ),
        html.Br(),
        html.Abbr('Фильтр по датам', title='Отфильтровать датасет по дате публикации вакансий (включительно)'),
        dbc.Col([
            dcc.DatePickerRange(
                id='date_picker2',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=min_date,
                end_date=max_date
            )]),
        html.Br(),
        html.Abbr('Обработка повторений', title='Объединить похожие названия компаний и пересчитать количество\nОбъединятся компании, которые: \n1. После транслитерации на русский совпадают\n2. У которых расстояние Левенштейна <5'),
        dcc.RadioItems(
            options=['Объединённые данные', 'Сырые данные'], 
            value='Сырые данные',
            id='aggregation'
        )
    ])
])

amount_part = \
dbc.Row([
    html.H4('График активности найма'),
    html.Br(),
    html.Br(),
    dbc.Row([
        html.Label('Показывает количество вакансий, аггрегированные за определённый промежуток времени.')
    ], style={'text-align': 'left'}),
    dbc.Col([
        dcc.Loading(
            dcc.Graph(id='amount_graph')
        ),
    ], width=9),
    dbc.Col([
        html.Label('Выбрать датасет'),
        dcc.Dropdown(
            options=['HeadHunter', 'HabrCareer', 'GeekJob', 'GetMatch', 'Все источники'],
            value='Все источники',
            id='dataset_dropdown_3',
            style={'color': 'black', 'background-color': 'white'}
        ),
        html.Br(),
        html.Abbr('Фильтр по датам', title='Отфильтровать датасет по дате публикации вакансий (включительно)'),
        dcc.DatePickerRange(
                id='date_picker3',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date='2022-11-14',
                end_date='2022-12-31'
            ),
        html.Br(),
        html.Abbr('Сгруппировать по', title='Выбрать параметр группировки'),
        dcc.RadioItems(
            ['Дням', 'Неделям', 'Месяцам'], 
            value='Неделям',
            id='groupby'
        )
    ])
])

word_cloud_part = \
dbc.Row([
    html.H4('Частые слова в названиях вакансий'),
    html.Br(),
    html.Br(),
    dbc.Row([
        html.Label('Взвешенное облако слов по названию вакансий в указанном источнике.'),
        html.Label('"Взвешенный" - размер слов подобран по их количеству повторений в названиях вакансий.')
    ], style={'text-align': 'left'}),
    html.Br(),html.Br(),
    dbc.Col([
        dcc.Loading(
            html.Img(id='wordcloud')
        )
    ], width=9),
    dbc.Col([
        html.Label('Выбрать датасет'),
        dcc.Dropdown(
            options=['HeadHunter', 'HabrCareer', 'GeekJob', 'GetMatch', 'Все источники'],
            value='Все источники',
            id='dataset_dropdown_4',
            style={'color': 'black', 'background-color': 'white'}
        ),
    ])
])

#instance of dash app
load_figure_template('DARLKY')
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])
server = app.server

#layout of dash app
app.layout = \
html.Div([
    dbc.Container([
        dbc.Card([
            dbc.CardBody(header_card)
        ], className='text-center shadow')
    ], fluid=True),
    html.Br(),
    dbc.Container([
        dbc.Card([
            dbc.CardBody(about_card)
        ], className='text-center shadow')
    ], fluid=True),
    html.Br(),
    dbc.Container([
        dbc.Card([
            dbc.CardBody(salary_part)
        ], className='text-center shadow')
    ], fluid=True),
    html.Br(),
    dbc.Container([
        dbc.Card([
            dbc.CardBody(grade_part)
        ], className='text-center shadow')
    ], fluid=True),
    html.Br(),
    dbc.Container([
        dbc.Card([
            dbc.CardBody(activity_part)
        ], className='text-center shadow')
    ], fluid=True),
    html.Br(),
    dbc.Container([
        dbc.Card([
            dbc.CardBody(amount_part)
        ], className='text-center shadow')
    ], fluid=True),
    html.Br(),
    dbc.Container([
        dbc.Card([
            dbc.CardBody(word_cloud_part)
        ], className='text-center shadow')
    ], fluid=True),
])

#wordcloud graph
@app.callback(
    [dash.dependencies.Output('wordcloud', 'src')],
    [dash.dependencies.Input('dataset_dropdown_4', 'value')]
)
def update_wordcloud(dataset_type):
    #filter the data
    dff = df.copy()
    if dataset_type != 'Все источники':
        dff = dff[dff.source==dataset_type]

    img = BytesIO()
    result_word=[]

    for vacancy_desc in dff['vacancy_name'].str.split(): #run through each vacancy descriptions
        for word in vacancy_desc: #run through each word in vacancy description
            sub = re.sub(r'[()🇬🇧]', '', word).lower()
            sub = re.sub(r'[/-]', ' ', sub).lower()
            for elem in sub.split(): #run through each splitted word in words
                if len(elem)>1: #pick only words with more than 1 char in it
                    if elem not in ('по', 'на', 'для', 'г.', 'г', 'со'): #filter russian prepositions
                        result_word.append(elem)

    dff = pd.DataFrame(result_word, columns=['word']).value_counts().reset_index(name ='count')
    text = dict(dff.head(1250).values)

    wordcloud = WordCloud(width=1000, height=600, max_words=1250, background_color='white').fit_words(text)
    wordcloud.to_image().save(img, format='PNG')

    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode()),

#amount of vacancies in time graph
@app.callback(
    [dash.dependencies.Output('amount_graph', 'figure')],
    [dash.dependencies.Input('dataset_dropdown_3', 'value'),
    dash.dependencies.Input('date_picker3', 'start_date'),
    dash.dependencies.Input('date_picker3', 'end_date'),
    dash.dependencies.Input('groupby', 'value')]
)
def update_graph_amount(dataset_type, start_date, end_date, groupby):
    #filter the data
    dff = df.copy()
    dff = dff[(dff.date>=start_date)&(dff.date<=end_date)]
    if dataset_type != 'Все источники':
        dff = dff[dff.source==dataset_type]

    fig = go.Figure()

    if groupby == 'Неделям':
        dff['week'] = pd.to_datetime(dff['date'], format='%Y-%m-%d').dt.isocalendar().week
        dff = dff.groupby('week')['date'].count().reset_index(name ='count')

        fig.add_trace(go.Line(
            x=dff['week'],
            y=dff['count']
        ))

        #add axis annotaions
        fig.update_layout(
            yaxis_title='Количество вакансий',
            xaxis_title='Неделя',
        )

    if groupby == 'Месяцам':
        dff['month'] = pd.to_datetime(dff['date'], format='%Y-%m-%d').dt.month
        dff = dff.groupby('month')['date'].count().reset_index(name ='count')

        fig.add_trace(go.Line(
            x=dff['month'],
            y=dff['count']
        ))

        #add axis annotaions
        fig.update_layout(
            yaxis_title="Количество вакансий",
            xaxis_title="Месяц",
        )

    if groupby == 'Дням':
        dff = dff.groupby('date')['date'].count().reset_index(name ='count')

        fig.add_trace(go.Line(
            x=dff['date'],
            y=dff['count']
        ))

        #add axis annotaions
        fig.update_layout(
            yaxis_title="Количество вакансий",
            xaxis_title="День",
        )

    fig.update_traces(marker=dict(line=dict(width=1,
                                  color='black'))
    )

    return fig,

#top companies by amount graph 
@app.callback(
    [dash.dependencies.Output('activity_graph', 'figure')],
    [dash.dependencies.Input('dataset_dropdown_2', 'value'),
    dash.dependencies.Input('date_picker2', 'start_date'),
    dash.dependencies.Input('date_picker2', 'end_date'),
    dash.dependencies.Input('aggregation', 'value')]
)
def update_graph_activity(dataset_type, start_date, end_date, aggregation_type):
    #filter the data
    dff = df.copy()
    dff = dff[(dff.date>=start_date)&(dff.date<=end_date)]
    if dataset_type != 'Все источники':
        dff = dff[dff.source==dataset_type]

    dff = dff.groupby('company_name')['date'].count().reset_index(name ='count')
    dff = dff.sort_values('count', ascending=False)
    if aggregation_type == 'Объединённые данные':
        companies = dict(dff[dff['count']>1].values) #copy the companies where vacancies count > 1 to separate dict
        result_dict = {}
        while len(result_dict)<10 and len(companies)>0: #iterate over all companies
            company = next(iter(companies))
            result_dict[company] = companies.get(company) #put first company from first to second dict
            companies.pop(company)
            for search_company in companies.copy(): #iterate over first dict
                if translit(company.lower(), 'ru') == translit(search_company.lower(), 'ru') or \
                fuzz.partial_ratio(company.lower(), search_company.lower()) > 95: #if company name match
                    result_dict[company] += companies.get(search_company) #increment count of company vacancies in 2nd dict
                    companies.pop(search_company) #delete entry from 2nd dict

        result_dict = dict(sorted(result_dict.items(), key=lambda x:x[1], reverse=True)) #sort dict by keys in descending order
    else:
        result_dict = dict(dff.head(10).values)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(result_dict.keys()),
        y=list(result_dict.values())
    ))

    fig.update_traces(marker=dict(line=dict(width=1,
                                  color='black'))
    )

    #add axis annotaions
    fig.update_layout(
        yaxis_title="Количество вакансий",
        xaxis_title="Компании",
    )

    return fig,

#grades graph
@app.callback(
    [dash.dependencies.Output('grades_graph', 'figure')],
    [dash.dependencies.Input('dataset_dropdown_1', 'value'),
     dash.dependencies.Input('date_picker1', 'start_date'),
     dash.dependencies.Input('date_picker1', 'end_date')]
)
def update_graph_grades(dataset_type, start_date, end_date):
    #filter the data
    dff = df.copy()
    dff = dff[(dff.date>=start_date)&(dff.date<=end_date)]
    if dataset_type != 'Все источники':
        dff = dff[dff.source==dataset_type]
    
    dff = dff.groupby('grade')['date'].count().reset_index(name ='count')
    grades = ['intern', 'junior', 'middle', 'senior', 'lead']
    counts = []
    for grade in grades:
        count = dff['count'][dff['grade']==grade].values
        count = 0 if count.size==0 else count[0]
        counts.append(count)

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=dff['grade'],
        values=dff['count'],
        hole = .3,
        direction='clockwise'
    ))

    fig.update_traces(marker=dict(line=dict(width=1,
                                  color='black'))
    )

    #add axis annotaions
    fig.update_layout(
        yaxis_title='Количество вакансий',
        xaxis_title='Грейд',
    )
    return fig,

#salaries graph
@app.callback(
    [dash.dependencies.Output('salaries_graph', 'figure'),
    dash.dependencies.Output('count', 'children'),
    dash.dependencies.Output('total_count', 'children'),
    dash.dependencies.Output('hh_roles_dropdown', 'disabled')],
    [dash.dependencies.Input('hh_roles_dropdown', 'value'),
    dash.dependencies.Input('hh_outliers', 'value'),
    dash.dependencies.Input('stats', 'value'),
    dash.dependencies.Input('dataset_dropdown', 'value'),
    dash.dependencies.Input('currency_dropdown', 'value'),
    dash.dependencies.Input('grade_dropdown', 'value'),
    dash.dependencies.Input('date_picker', 'start_date'),
    dash.dependencies.Input('date_picker', 'end_date')]
)
def update_graph_salaries(hh_role_value, hh_outliers, stats, dataset_type, currency_type, grade_type, start_date, end_date):
    #filter the data
    dff = df.copy()

    dff = dff[(dff.date>=start_date)&(dff.date<=end_date)]
    if dataset_type != 'Все источники':
        dff = dff[dff.source==dataset_type]
    if dataset_type == 'HeadHunter':
        if hh_role_value != 'Все роли':
            dff = dff[dff.hh_role==hh_role_value]
    if currency_type != 'Все валюты':
        dff = dff[dff.currency==currency_type]
    if grade_type != 'Все грейды':
        dff = dff[dff.grade==grade_type.lower()]

    tot_count = len(dff.index)
    total_count = f'Количество строк в датасете после применения текущих фильтров = {tot_count}.'
    dff = dff[dff.salary.notna()]

    #disable roles checkbox if dataset not from HH
    is_roles_disabled = False if dataset_type == 'HeadHunter' else True

    #drop outliers
    if hh_outliers == 'Убрать выбросы':
        q_low = dff.salary.quantile(0.01)
        q_high = dff.salary.quantile(0.99)
        dff = dff[(dff.salary < q_high) & (dff.salary > q_low)]

    sal_count = len(dff.index)
    salary_count = f'Из них строк с указанной зарплатой = {sal_count}.\n\
                    Зарплата указана в {round(sal_count/tot_count*100, 2)}% вакансий.'

    #build the graph
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dff.salary,
        xbins=dict(
            start=0,
            end=1000000,
            size=25000)
    ))

    #add statistics to the graph
    if stats == 'Посчитать статистич. параметры':
        quantile_50 = dff.salary.quantile(0.5)
        quantile_10 = dff.salary.quantile(0.1)
        quantile_90 = dff.salary.quantile(0.9)
        quantile_25 = dff.salary.quantile(0.25)
        quantile_75 = dff.salary.quantile(0.75)
        average = dff.salary.mean()

        fig.update_layout(
        shapes= [
            {
                'line': {'color': '#0f0f0f', 'dash': 'dot', 'width': 1},
                'type': 'line',
                'x0': quantile_50, 'x1': quantile_50,
                'y0': 1, 'y1': 0,
                'yref': 'paper'},
            {
                'line': {'color': '#0f0f0f', 'dash': 'dot', 'width': 1},
                'type': 'line',
                'x0': quantile_10, 'x1': quantile_10,
                'y0': -0.09, 'y1': 0,
                'yref': 'paper'},
            {
                'line': {'color': '#0f0f0f', 'dash': 'dot', 'width': 1},
                'type': 'line',
                'x0': quantile_90, 'x1': quantile_90,
                'y0': -0.09, 'y1': 0,
                'yref': 'paper'},
            {
                'line': {'color': '#0f0f0f', 'dash': 'dot', 'width': 1},
                'type': 'line',
                'x0': quantile_25, 'x1': quantile_25,
                'y0': 1.05, 'y1': 0,
                'yref': 'paper'},
            {
                'line': {'color': '#0f0f0f', 'dash': 'dot', 'width': 1},
                'type': 'line',
                'x0': quantile_75, 'x1': quantile_75,
                'y0': 1.05, 'y1': 0,
                'yref': 'paper'},
            {
                'line': {'color': '#0f0f0f', 'dash': 'dot', 'width': 1},
                'type': 'line',
                'x0': average, 'x1': average,
                'y0': -0.04, 'y1': 0,
                'yref': 'paper'}],
            annotations=[
                dict(
                    x=quantile_50, y=1.01,
                    xref='x', yref='paper',
                    ax=1, ay=1,
                    text='Q_50={:,.0f}'.format(quantile_50)),
                dict(
                    x=quantile_10, y=-0.1,
                    xref='x', yref='paper',
                    ax=1, ay=1,
                    text='Q_10={:,.0f}'.format(quantile_10)),
                dict(
                    x=quantile_90, y=-0.1,
                    xref='x', yref='paper',
                    ax=1, ay=1,
                    text='Q_90={:,.0f}'.format(quantile_90)),
                dict(
                    x=quantile_25, y=1.06,
                    xref='x', yref='paper',
                    ax=1, ay=1,
                    text='Q_25={:,.0f}'.format(quantile_25)),
                dict(
                    x=quantile_75, y=1.06,
                    xref='x', yref='paper',
                    ax=1, ay=1,
                    text='Q_75={:,.0f}'.format(quantile_75)),
                dict(
                    x=average, y=-0.05,
                    xref='x', yref='paper',
                    ax=1, ay=1,
                    text='average={:,.0f}'.format(average))
        ])

    #draw the strokes
    fig.update_traces(marker=dict(line=dict(width=1,
                                  color='black'))
    )

    #add axis annotaions
    fig.update_layout(
        yaxis_title='Количество вакансий',
        xaxis_title='Зарплата [₽]',
    )
    
    return fig, salary_count, total_count, is_roles_disabled

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
