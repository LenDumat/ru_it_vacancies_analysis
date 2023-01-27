from crontab import CronTab
from pathlib import Path
import os

current_folder = Path.cwd()
venv_python = os.path.join('vacancies_venv', 'bin', 'python3')

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

    job = cron.new(command=f'cd {current_folder} && {venv_python} currency_rates.py')
    job.setall('05 00 * * *')