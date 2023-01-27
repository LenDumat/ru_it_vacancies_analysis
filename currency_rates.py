import sqlite3
import random
from datetime import datetime, timedelta
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from config import db_path, proxies_path
from proxy_checker import get_correct_proxies
from tqdm.asyncio import tqdm

def get_last_currency_rate(db_path: str) -> datetime.date:
    query1 = '''
            SELECT MAX(date)
            FROM currency_to_ruble_rates
            '''
    query2 = '''
            SELECT MIN(vacancy_date)
            FROM(
                SELECT vacancy_date
                FROM head_hunter_vacancies
                UNION
                SELECT vacancy_date
                FROM habr_career_vacancies
                UNION
                SELECT vacancy_date
                FROM get_match_vacancies
                UNION
                SELECT vacancy_date
                FROM geek_job_vacancies
            ) q
            '''

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        date = cursor.execute(query1).fetchone()[0]
        if date is None:
            date = cursor.execute(query2).fetchone()[0]
    return datetime.strptime(date, '%Y-%m-%d').date() + timedelta(days=1)

async def parse_page(session, url, ua, proxies: list, data: list, date: str) -> None:
    while not proxies:
        await asyncio.sleep(1)
    proxy = proxies.pop()
    await asyncio.sleep(random.uniform(5, 20))
    async with session.get(url, headers=ua, proxy='http://'+proxy) as resp:
        response = await resp.text()
        proxies.append(proxy)
        soup = BeautifulSoup(response, 'xml')
        dollar_rate = soup.find('Valute', {'ID': 'R01235'}).find('Value').get_text().replace(',', '.')
        euro_rate = soup.find('Valute', {'ID': 'R01239'}).find('Value').get_text().replace(',', '.')
        data.append(['$', dollar_rate, str(date)])
        data.append(['€', euro_rate, str(date)])
        data.append(['₽', 1, str(date)])

async def request_data(date: datetime.date, url: str, proxies: list, ua: callable, data: list) -> None:
    async with aiohttp.ClientSession(trust_env=True) as session:
        tasks = []

        while date <= datetime.now().date():
            task = asyncio.create_task(parse_page(session=session, url=url+date.strftime('%d/%m/%Y'), ua={'User-Agent': ua.random}, 
                                                  proxies=proxies, data = data, date=date))
            tasks.append(task)
            date += timedelta(days=1)
        print(len(tasks))
        #await asyncio.gather(*tasks)
        for future in tqdm(asyncio.as_completed(tasks)):
            await future

def insert_to_db(data: list, db_path: str) -> None:
    query = '''
            INSERT OR IGNORE INTO currency_to_ruble_rates
            VALUES(?, ?, ?)
            '''
    with sqlite3.connect(db_path) as db:
        for row in data:
            cursor = db.cursor()
            cursor.execute(query, (row[0], row[1], row[2]))

def main():
    ua = UserAgent()
    proxies = get_correct_proxies(proxies_path)
    date = get_last_currency_rate(db_path)
    url = 'http://www.cbr.ru/scripts/XML_daily.asp?date_req='
    data = []
    asyncio.run(request_data(date, url, proxies, ua, data))
    insert_to_db(data, db_path)

if __name__ == '__main__':
    main()