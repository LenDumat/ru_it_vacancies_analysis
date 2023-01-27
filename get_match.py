import random
import re
import math
import os
import requests
import asyncio
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from vacancies_crawler import vacancies_crawler, delete_old_file
from proxy_checker import get_correct_proxies
from config import data_destination, gm_vacancies_urls, proxies_path, gm_log_path
from datetime import datetime

def gm_replace_page(page, url: str) -> str:
    return re.sub('p=1', 'p=' + str(page), url)

def gm_get_total_pages(url, ua, proxies):
    response = requests.get(url=url, headers={'User-Agent': ua.random}, proxies={'https': 'https://'+random.choice(proxies)}, timeout=5)
    soup = BeautifulSoup(response.text, 'lxml')
    vacancies_count_on_page = len(soup.findAll('div', {'class': 'b-vacancy-card'}))
    vacancies_count_overall = soup.find('h5', {'class': 'b-vacancies-list__count'}).get_text()
    vacancies_count_overall = int(re.findall(r'\d+', vacancies_count_overall)[0]) 
    total_pages = math.ceil(vacancies_count_overall/vacancies_count_on_page)

    return total_pages

def gm_split_salary_string(salary_string: str) -> list:
    salary_string = salary_string.split('/')[0]
    salary_list = []

    if '—‍' in salary_string.lower():
        salary_list = re.findall(r'\d+', salary_string.replace(' ', ''))
        salary_list.append(salary_string[-1])
    else:
        salary_list = [re.findall(r'\d+', salary_string.replace(' ', ''))[-1], '', salary_string[-1]]

    salary_list = [value if value else 'null' for value in salary_list]

    return salary_list

async def gm_parse_page(session, url, ua, proxies: list, vacancies_list: list) -> None:
    while not proxies:
        await asyncio.sleep(1)
    proxy = proxies.pop()
    await asyncio.sleep(random.uniform(5, 60))
    async with session.get(url, headers=ua, proxy='http://'+proxy) as resp:
        response = await resp.text()
        proxies.append(proxy)
        soup = BeautifulSoup(response, 'html.parser') 
        vacancies = soup.findAll('div', {'class': 'b-vacancy-card'})
        for vacancy in vacancies:
            try:
                name = vacancy.find('a', {'target': '_blank'}).get_text()
            except:
                name = ''
            
            if 'middle' in url:
                grade = 'middle'
            elif 'senior' in url:
                grade = 'senior'
            elif 'lead' in url:
                grade = 'lead'
            else:
                grade = ''

            try:
                company = vacancy.find('h4').get_text()[2:]
            except:
                company = ''

            try:
                salary = vacancy.find('div', {'class': 'b-vacancy-card-subtitle__salary ng-star-inserted'}).get_text()
                salary = gm_split_salary_string(salary)
            except:
                salary = ['null', 'null', 'null']

            try:
                locs = vacancy.find('div', {'class': 'b-vacancy-card-subtitle__locations'}).get_text()[9:].split('или')
                location = ', '.join(locs).replace(' — на выбор', '').replace(' , ', ',')
            except:
                location = ''

            try:
                skills = vacancy.find('div', {'class': 'b-vacancy-card-subtitle__stack ng-star-inserted'}).get_text(separator = ',')
                skills = skills.strip().replace(' ,', ',')
            except:
                skills = ''

            try:
                link = vacancy.find('h3').find('a').attrs['href']
                link = 'https://getmatch.ru' + link
            except:
                link = ''

            try:
                date = vacancy.find('div', {'class', 'b-vacancy-card-header__publish-date ng-star-inserted'}).get_text()
            except:
                date = ''

            vacancies_list.append([name,
                                   grade,
                                   company,
                                   location,
                                   salary,
                                   date,
                                   link])

def main():
    logging.basicConfig(filename=gm_log_path, 
                        level=logging.INFO, filemode='a', format="%(asctime)s %(levelname)s %(message)s")
    logging.info('Started GetMatch parser')
    ua = UserAgent()
    proxies = get_correct_proxies(proxies_path)
    
    #asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) #for windows only

    filename = os.path.join(data_destination, f'GetMatch_{datetime.today().strftime("%Y-%m-%d")}.csv')
    if delete_old_file(filename):
        logging.info('deleted old file ' + filename)

    for gm_vacancies_url in gm_vacancies_urls:
        gm_total_pages = gm_get_total_pages(url = gm_vacancies_url, ua = ua, proxies = proxies)
        asyncio.run(vacancies_crawler(source = 'GetMatch',
                                    url = gm_vacancies_url, 
                                    proxies = proxies, 
                                    ua = ua,
                                    total_pages = gm_total_pages, 
                                    filename = filename,
                                    replace_page = gm_replace_page, 
                                    parse_page = gm_parse_page))

    logging.info('Finished GetMatch parser')


if __name__ == '__main__':
    main()
