import sqlite3, glob, fnmatch, csv, os, re
from datetime import datetime
from config import db_path, data_destination

def get_processed_files(db_path: str, data_destination) -> list:
    with sqlite3.connect(db_path) as db:
        db.row_factory = lambda cursor, row: row[0]
        cursor = db.cursor()
        files_processed = cursor.execute('SELECT file_name FROM processed_files').fetchall()
    
    files = [os.path.basename(x) for x in glob.glob(os.path.join(data_destination, '*.csv'))]
    files_to_process = []
    for file in files:
        if file not in files_processed:
            files_to_process.append(file)

    return files_to_process



def sql_insert_processed_file(file, db_path) -> None:
    query = '''
            INSERT OR IGNORE INTO processed_files
            VALUES(?, datetime('now','localtime'))
            '''
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute(query, [file])
    

def sql_insert_head_hunter(rows: list, db_path: str) -> None:
    hh_role = lambda row: row[0] if (row[0]) else None
    company_name = lambda row: row[7] if (row[7]) else None
    vacancy_link = lambda row: row[2] if (row[2]) else None
    vacancy_name = lambda row: row[3] if (row[3]) else None
    vacancy_address = lambda row: row[4] if (row[4]) else None
    vacancy_date = lambda row: row[5][:10] if (row[5]) else None
    vacancy_salary_from = lambda salary_string: None if not (salary_string[0].isdigit()) else salary_string[0]
    vacancy_salary_to = lambda salary_string: None if not (salary_string[1].isdigit()) else salary_string[1]
    #vacancy_salary_currency = lambda salary_string: None if (salary_string[2] == 'null') else salary_string[2]
    def vacancy_salary_currency(salary_string):
        if salary_string[2] == 'RUR':
            return '₽'
        elif salary_string[2] == 'USD':
            return '$'
        elif salary_string[2] == 'EUR':
            return '€'
        else:
            return None
    company_link = lambda row: row[8] if (row[8]) else None
    vacancy_requirements = lambda row: row[9] if (row[9]) else None
    vacancy_responsibilities = lambda row: row[10] if (row[10]) else None

    query = '''
            INSERT OR IGNORE INTO head_hunter_vacancies
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
    
    with sqlite3.connect(db_path) as db:
        for row in rows:
            salary_string = row[6]
            for char in [']', '[', '\'', ',']:
                salary_string = salary_string.replace(char, '')
            salary_string = salary_string.split()

            cursor = db.cursor()
            cursor.execute(query, (hh_role(row),
                                    company_name(row),
                                    vacancy_link(row),
                                    vacancy_name(row),
                                    vacancy_address(row),
                                    vacancy_date(row),
                                    vacancy_salary_from(salary_string),
                                    vacancy_salary_to(salary_string),
                                    vacancy_salary_currency(salary_string),
                                    company_link(row),
                                    vacancy_requirements(row),
                                    vacancy_responsibilities(row)))


def sql_insert_habr_career(rows: list, db_path: str) -> None:
    company_name = lambda row: row[0] if (row[0]) else None
    vacancy_name = lambda row: row[1] if (row[1]) else None
    vacancy_work_type = lambda row: row[2] if (row[2]) else None
    vacancy_tags = lambda row: row[3] if (row[3]) else None
    vacancy_date = lambda row: row[4][:10] if (row[4]) else None
    vacancy_salary_from = lambda salary_string: None if not (salary_string[0].isdigit()) else salary_string[0]
    vacancy_salary_to = lambda salary_string: None if not (salary_string[1].isdigit()) else salary_string[1]
    vacancy_salary_currency = lambda salary_string: None if (salary_string[2] == 'null') else salary_string[2]
    vacancy_link = lambda row: row[6] if (row[6]) else None

    query = '''
            INSERT OR IGNORE INTO habr_career_vacancies
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

    with sqlite3.connect(db_path) as db:
        for row in rows:
            salary_string = row[5]
            for char in [']', '[', '\'', ',']:
                salary_string = salary_string.replace(char, '')
            salary_string = salary_string.split()

            cursor = db.cursor()
            cursor.execute(query, (company_name(row),
                                   vacancy_name(row),
                                   vacancy_work_type(row),
                                   vacancy_tags(row),
                                   vacancy_date(row),
                                   vacancy_salary_from(salary_string),
                                   vacancy_salary_to(salary_string),
                                   vacancy_salary_currency(salary_string),
                                   vacancy_link(row)))


def replace_month(date_string: str) -> str:
    date = ''
    month_name = ''
    month_dict = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12',
    }
    
    if 'сегодня' in date_string:
        return datetime.now().strftime("%YYYY-%mm-%dd")
    if 'г.' in date_string:
        date_string = date_string.replace(' г.', '')

    for char in date_string:
        month_name += char if char.isalpha() else '' 
    date_list = date_string.replace(month_name, month_dict[month_name]).split(' ')
    for i, char in enumerate(date_list):
        date_list[i] = '0'+char if len(char)<2 else char
    date = '-'.join(reversed(date_list))

    if len(date) < 6:
        today_month = datetime.now().month
        today_day = datetime.now().day
        today_year = datetime.now().year
        data_month = int(date[:2])
        data_day = date[3:5]
        if int(data_month) < int(today_month):
            date = str(today_year) + '-' + date
        elif int(data_month) == int(today_month) and int(data_day) <= int(today_day):
            date = str(today_year) + '-' + date
        else:
            date = str(today_year-1) + '-' + date

    return date


def sql_insert_get_match(rows: list, db_path: str) -> None:
    company_name = lambda row: row[2] if (row[2]) else None
    vacancy_name = lambda row: row[0] if (row[0]) else None
    vacancy_grade = lambda row: row[1] if (row[1]) else None
    vacancy_work_type = lambda row: row[3] if (row[3]) else None
    vacancy_date = lambda row: re.sub('Y|m|d', '', replace_month(row[5])) if (row[5]) else None
    vacancy_salary_from = lambda salary_string: None if not (salary_string[0].isdigit()) else salary_string[0]
    vacancy_salary_to = lambda salary_string: None if not (salary_string[1].isdigit()) else salary_string[1]
    vacancy_salary_currency = lambda salary_string: None if (salary_string[2] == 'null') else salary_string[2]
    vacancy_link = lambda row: row[6] if (row[6]) else None

    query = '''
            INSERT OR IGNORE INTO get_match_vacancies
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

    with sqlite3.connect(db_path) as db:
        for row in rows:
            salary_string = row[4]
            for char in [']', '[', '\'', ',']:
                salary_string = salary_string.replace(char, '')
            salary_string = salary_string.split()

            cursor = db.cursor()
            cursor.execute(query, (company_name(row),
                                   vacancy_name(row),
                                   vacancy_grade(row),
                                   vacancy_work_type(row),
                                   vacancy_date(row),
                                   vacancy_salary_from(salary_string),
                                   vacancy_salary_to(salary_string),
                                   vacancy_salary_currency(salary_string),
                                   vacancy_link(row)))


def sql_insert_geek_job(rows: list, db_path: str) -> None:
    company_name = lambda row: row[0] if (row[0]) else None
    vacancy_name = lambda row: row[1] if (row[1]) else None
    vacancy_address = lambda row: row[2] if (row[2]) else None
    vacancy_tags = lambda row: row[3] if (row[3]) else None
    vacancy_date = lambda row: replace_month(row[4]) if (row[4]) else None
    vacancy_salary_from = lambda salary_string: None if not (salary_string[0].isdigit()) else salary_string[0]
    vacancy_salary_to = lambda salary_string: None if not (salary_string[1].isdigit()) else salary_string[1]
    vacancy_salary_currency = lambda salary_string: None if (salary_string[2] == 'null') else salary_string[2]
    vacancy_link = lambda row: row[6] if (row[6]) else None

    query = '''
            INSERT OR IGNORE INTO geek_job_vacancies
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

    with sqlite3.connect(db_path) as db:
        for row in rows:
            salary_string = row[5]
            for char in [']', '[', '\'', ',']:
                salary_string = salary_string.replace(char, '')
            salary_string = salary_string.split()
            cursor = db.cursor()
            cursor.execute(query, (company_name(row),
                                   vacancy_name(row),
                                   vacancy_address(row),
                                   vacancy_tags(row),
                                   vacancy_date(row),
                                   vacancy_salary_from(salary_string),
                                   vacancy_salary_to(salary_string),
                                   vacancy_salary_currency(salary_string),
                                   vacancy_link(row)))


def main():
    files_to_process = get_processed_files(db_path, data_destination)
    for filename in files_to_process:
        file = os.path.join(data_destination, filename)
        if fnmatch.fnmatch(file, '*HeadHunter*'):
            rows = []
            with open(file, 'r', encoding='UTF-8') as f:
                csvreader = csv.reader(f, delimiter='|')
                for row in csvreader:
                    rows.append(row)
            sql_insert_head_hunter(rows, db_path)
            sql_insert_processed_file(filename, db_path)
        elif fnmatch.fnmatch(file, '*HabrCareer*'):
            rows = []
            with open(file, 'r', encoding='UTF-8') as f:
                csvreader = csv.reader(f, delimiter='|')
                for row in csvreader:
                    rows.append(row)
            sql_insert_habr_career(rows, db_path)
            sql_insert_processed_file(filename, db_path)
        elif fnmatch.fnmatch(file, '*GetMatch*'):
            rows = []
            with open(file, 'r', encoding='UTF-8') as f:
                csvreader = csv.reader(f, delimiter='|')
                for row in csvreader:
                    rows.append(row)
            sql_insert_get_match(rows, db_path)
            sql_insert_processed_file(filename, db_path)
        elif fnmatch.fnmatch(file, '*GeekJob*'):
            rows = []
            with open(file, 'r', encoding='UTF-8') as f:
                csvreader = csv.reader(f, delimiter='|')
                for row in csvreader:
                    rows.append(row)
            sql_insert_geek_job(rows, db_path)
            sql_insert_processed_file(filename, db_path)


if __name__ == '__main__':
    main()