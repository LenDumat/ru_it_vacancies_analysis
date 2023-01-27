from crontab import CronTab
from pathlib import Path
import os

current_folder = Path.cwd()
venv_python = os.path.join('vacancies_venv', 'bin', 'python3')
get_match = os.path.join(current_folder, 'get_match.py')
head_hunter = os.path.join(current_folder, 'head_hunter.py')
habr_career = os.path.join(current_folder, 'habr_career.py')
geek_job = os.path.join(current_folder, 'geek_job.py')
insert_to_db = os.path.join(current_folder, 'insert_to_db.py')

with CronTab(user='root') as cron:

    job = cron.new(command=f'cd {current_folder} && {venv_python} get_match.py')
    job.setall('30 20 * * *')

    job = cron.new(command=f'cd {current_folder} && {venv_python} head_hunter.py')
    job.setall('45 20 * * *')

    job = cron.new(command=f'cd {current_folder} && {venv_python} habr_career.py')
    job.setall('00 21 * * *')

    job = cron.new(command=f'cd {current_folder} && {venv_python} geek_job.py')
    job.setall('15 21 * * *')

    job = cron.new(command=f'cd {current_folder} && {venv_python} insert_to_db.py')
    job.setall('30 21 * * *')