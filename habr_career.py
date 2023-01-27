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
from config import data_destination, hc_vacancies_url, proxies_path, hc_log_path
from datetime import datetime

def hc_replace_page(page, url: str) -> str:
    return re.sub('page=1', 'page=' + str(page), url)

def hc_get_total_pages(url, ua, proxies):
    response = requests.get(url=url, headers={'User-Agent': ua.random}, proxies={'https': 'https://'+random.choice(proxies)}, timeout=5)
    soup = BeautifulSoup(response.text, 'lxml')
    footer_string = soup.find('div', {'class': 'footer__statistics'}).text
    total_vacancies = int(re.findall(r'\d+', footer_string)[0])
    vacancies = soup.find('div', {'class': 'section-group section-group--gap-medium'})
    vacancies_on_one_page = len(vacancies.findChildren('div', {'class': 'vacancy-card'}))
    total_pages = math.ceil(total_vacancies/vacancies_on_one_page)

    return total_pages

def hc_split_salary_string(salary_string: str) -> list:
    salary_list = []

    if not salary_string:
        salary_list = ['null', 'null', 'null']
    elif 'от' in salary_string.lower() and 'до' in salary_string.lower():
        salary_list = re.findall(r'\d+', salary_string.replace(' ', ''))
        salary_list.append(salary_string[-1])
    elif 'от' in salary_string.lower():
        salary_list = [re.findall(r'\d+', salary_string.replace(' ', ''))[-1], 'null', salary_string[-1]]
    elif 'до' in salary_string.lower():
        salary_list = ['null', re.findall(r'\d+', salary_string.replace(' ', ''))[-1], salary_string[-1]]

    return salary_list

async def hc_parse_page(session, url, ua, proxies: list, vacancies_list: list) -> None:
    while not proxies:
        await asyncio.sleep(random.uniform(5, 15))
    proxy = proxies.pop()
    await asyncio.sleep(random.uniform(10, 30))
    async with session.get(url, headers=ua, proxy='http://'+proxy) as resp:
        response = await resp.text()
        proxies.append(proxy)
        soup = BeautifulSoup(response, 'html.parser')
        vacancies = soup.find('div', {'class': 'section-group section-group--gap-medium'})
        for vacancy in vacancies.findChildren('div', {'class': 'vacancy-card'}):
            try:
                about = vacancy.find('div', {'class': 'vacancy-card__company-title'}) #find company name
                about = str(about.get_text())
            except:
                about = 'null'

            try:
                location = vacancy.find('a', {'class': 'vacancy-card__title-link'}) #find vacancy name
                location = str(location.get_text())
            except:
                location = 'null'

            try:
                attributes = vacancy.find('div', {'class': 'vacancy-card__meta'}) #find vacancy attributes
                attributes = str(attributes.get_text()).replace(' • ', ', ')
            except:
                attributes = 'null'

            try:
                skills = vacancy.find('div', {'class': 'vacancy-card__skills'}) #find vacancy skills
                skills = str(skills.get_text()).replace(' • ', ', ')
            except:
                skills = 'null'

            try:
                publication_time = vacancy.find('time', {'class': 'basic-date'}) #find vacancy publication datetime
                publication_time = str(publication_time.attrs['datetime'])
            except:
                publication_time = 'null'

            try:
                salary_string = vacancy.find('div', {'class': 'basic-salary'}) #find vacancy salary
                salary = hc_split_salary_string(salary_string.get_text())
            except:
                salary = ['null', 'null', 'null']

            try:        
                link = vacancy.find('a', {'class': 'vacancy-card__title-link'}) #find vacancy publication datetime
                link = 'https://career.habr.com' + str(link.attrs['href']) 
                #bad idea to concatenate url's like that, but I didn't come up with elegant solution so far
            except:
                link = 'null'

            vacancies_list.append([about, 
                                   location, 
                                   attributes, 
                                   skills, 
                                   publication_time, 
                                   salary, 
                                   link])

def main():
    logging.basicConfig(filename=hc_log_path, 
                        level=logging.INFO, filemode='a', format="%(asctime)s %(levelname)s %(message)s")
    logging.info('Started Habr Career parser')
    ua = UserAgent()
    proxies = get_correct_proxies(proxies_path)
    hc_total_pages = hc_get_total_pages(url = hc_vacancies_url, ua = ua, proxies = proxies)

    filename = os.path.join(data_destination, f'HabrCareer_{datetime.today().strftime("%Y-%m-%d")}.csv')
    print(filename)
    if delete_old_file(filename):
        logging.info('deleted old file ' + filename)

    #asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) #for windows only
    asyncio.run(vacancies_crawler(source = 'Habr Career',
                                  url = hc_vacancies_url, 
                                  proxies = proxies, 
                                  ua = ua,
                                  total_pages = hc_total_pages,
                                  filename = filename, 
                                  replace_page = hc_replace_page, 
                                  parse_page = hc_parse_page))

    logging.info('Finished Habr Career parser')

if __name__ == '__main__':
    main()
