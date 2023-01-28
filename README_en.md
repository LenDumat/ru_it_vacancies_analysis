[По-русски](README.md) | In-English

# Russian IT-vacancies analysis
## Table of contents
 + [Why?](#why)
 + [Description](#description)
 + [Demo](#demo)
 + [Deployment](#installation)
 + [Concllusions](#conclusions)
 
 ### <a name="why"></a> Why?
 There are a lot of unpredictable things start to happen in Eastern Europe in 2022. Hence it can be interesting to look at some numbers in these days and try to answer on 2 questions related to IT sphere:
 1. Is it so bad?
 2. Where it's going?
 
 ### <a name="description"></a> Description
 #### Problem formulation 
 Scrape the open source data related to IT-vacancies in Russia. From this data build analytical dashboard which may help in understanding of market condition.
 
 #### Project description
 1. 5 web crawlers, which are scraping data from the following sources:
    * [HeadHunter](https://hh.ru/) - using official [API](https://github.com/hhru/api)
    * [HabrCareer](https://career.habr.com/) - had to parse the data
    * [GeekJob](https://geekjob.ru/) - had to parse the data
    * [GetMatch](https://getmatch.ru/) - had to parse the data
    * [Сайт ЦБ РФ](http://www.cbr.ru/) - collecting currencies exchange rates using official [API](http://www.cbr.ru/development/sxml/)
 2. SQLite DB to store all data scraped on above step
 3. [Dash](https://dash.plotly.com/) - dashboard application
 
 #### ~~Beatiful~~ pic
 ![Vacancies Parser](https://user-images.githubusercontent.com/35892153/215205911-fb030c1a-24ca-48f3-810e-649aafab3169.jpg)

 ### <a name="demo"></a> Demo
 Check the dashboard [here](http://46.29.163.180:8050/).
 If something not working, here is the gif representation of how it looks like:
 ![Анимация](https://user-images.githubusercontent.com/35892153/215260179-dd339550-80b8-47f1-b7be-5b3f795e6c2e.gif)

 ### <a name="installation"></a> Deployment
 Here you can find instruction how to deploy this on your own Linux machine. Ofc, there are [more easier ways](https://dash.plotly.com/deployment) with use of cloud hostings, but it's boring.
 What you'll need:
 1. Linux machine with at least 1 Gb RAM, some CPU and >10 Gb of mem. I used Ubuntu 20.
 2. Proxies list - at least one proxy. If you have more, then speed of web crawlers will be greater.
 
 Deployment steps:
 1. Clone the repo
 2. Create virtual env
   ```
   pip install virtualenv
   virtualenv vacancies_venv 
   source vacancies_venv/bin/activate
   ```
 2. Install packages from requirements.txt
   ```
   pip install -r requirements.txt
   ```
 3. Insert working proxies in proxies.txt. Format defined in the file.
 4. Run create_cron.py to create cron jobs.
   ```
   python3 create_cron.py
   ```
 5. Run create_db.py to create DB and it's objects.
   ```
   python3 create_db.py
   ```
 6. Start gunicorn
   ```
   gunicorn dash_app:server -b :8050
   ```
 7. ~~Thumbs up, subscribe to my channel~~

 ### <a name="conclusions"></a> Conclusions
 I haven't luck to answer questions raised in [Why?](#why) section. To answer them I'll need to collect data for some time, at least half a year.
 
 But I learned how not to do such projects:
 1. Bad idea to make some calculation in Dash. Better to make Dash or any other BI tool to show data, not calculate it.
 2. Cron - not the best scheduler. If no limitiations on hardware, then better to use Luigi or Airflow
 3. Better to have plan on structure of project before it finished
 ![image](https://user-images.githubusercontent.com/35892153/215257265-5f29b4de-2053-4489-9006-fbff4cdd9569.png)
