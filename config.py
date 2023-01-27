from datetime import datetime
from pathlib import Path

root_path = Path.cwd()

db_path = root_path / 'data_db' / 'vacancies.db'

# url's to parse
ip_check_url = 'https://sitespy.ru/my-ip'
hc_vacancies_url = 'https://career.habr.com/vacancies?page=1&type=all'
gj_vacancies_url = 'https://geekjob.ru/vacancies/1'
gm_vacancies_urls = ['https://getmatch.ru/vacancies?p=1&sa=150000&l=moscow&l=remote&l=relocate&l=saints_p&se=middle&pa=all',
                     'https://getmatch.ru/vacancies?p=1&sa=150000&l=moscow&l=remote&l=relocate&l=saints_p&se=senior&pa=all',
                     'https://getmatch.ru/vacancies?p=1&sa=150000&l=moscow&l=remote&l=relocate&l=saints_p&se=lead&pa=all']

# path's to data
proxies_path = root_path / 'proxies.txt'
data_destination = root_path / 'data'

# path's to logs
hc_log_path = root_path / 'log' / 'habr_career_{date}.log'.format(date = datetime.today().strftime('%Y-%m-%d'))
gj_log_path = root_path / 'log' / 'geek_job_{date}.log'.format(date = datetime.today().strftime('%Y-%m-%d'))
gm_log_path = root_path / 'log' / 'get_match_{date}.log'.format(date = datetime.today().strftime('%Y-%m-%d'))
hh_log_path = root_path / 'log' / 'head_hunter_{date}.log'.format(date = datetime.today().strftime('%Y-%m-%d'))
