import random
import os
import re
import requests
import asyncio
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from vacancies_crawler import vacancies_crawler, delete_old_file
from proxy_checker import get_correct_proxies
from config import data_destination, gj_vacancies_url, proxies_path, gj_log_path
from datetime import datetime


def gj_replace_page(page_num, url: str) -> str:
    return re.sub('1', str(page_num), url)


def gj_get_total_pages(url, ua, proxies) -> int:
    response = requests.get(url=url, headers={'User-Agent': ua.random}, proxies={'https': 'https://'+random.choice(proxies)}, timeout=5)
    soup = BeautifulSoup(response.text, 'lxml')
    footer = soup.find('section', {'class': 'col s12 m12 center-align'})
    total_pages = footer.find({'small'}).get_text()
    total_pages = re.findall(r'\d+', total_pages)[0]

    return int(total_pages)


def gj_split_salary_string(salary_string: str) -> list:
    if ('—' in salary_string.lower()):
        salary_list = re.findall('\d*\.?\d+', salary_string.replace(' ', ''))
        salary_list.append(salary_string[-1])
        salary_list[0] = int(salary_list[0])*1000
        salary_list[1] = int(salary_list[1])*1000
    elif 'от' in salary_string.lower():
        salary_list = [re.findall('\d*\.?\d+', salary_string.replace(' ', ''))[-1], 'null', salary_string[-1]]
        salary_list[0] = int(salary_list[0])*1000
    elif any(char.isdigit() for char in salary_string.lower()):
        salary_list = ['null', re.findall('\d*\.?\d+', salary_string.replace(' ', ''))[-1], salary_string[-1]]
        salary_list[1] = int(salary_list[1])*1000
    else:
        salary_list = ['null', 'null', 'null']

    salary_list = [value if value else 'null' for value in salary_list]
    
    return salary_list


async def gj_parse_page(session, url, ua, proxies: list, vacancies_list: list) -> None:
    while not proxies:
        await asyncio.sleep(1)
    proxy = proxies.pop()
    await asyncio.sleep(random.uniform(5, 60))
    async with session.get(url, headers=ua, proxy='http://'+proxy) as resp:
        response = await resp.text()
        proxies.append(proxy)
        soup = BeautifulSoup(response, 'lxml') 
        vacancies = soup.find('ul', {'class': 'collection serp-list'})
        for vacancy in vacancies.findChildren('li', {'class': 'collection-item avatar'}): 
            try:
                company = vacancy.find('p', {'class': 'truncate company-name'})
                company = str(company.get_text()).lstrip()
            except:
                company = ''

            try:
                name = vacancy.find('p', {'class': 'truncate vacancy-name'})
                name = name.get_text()
            except:
                name = ''

            try:
                infos = vacancy.find('div', {'class': 'info'})
                infos = str(infos).split('<br/>')
            
                location = BeautifulSoup(infos[0], 'lxml').get_text()
                salary = BeautifulSoup(infos[1], 'lxml').get_text()
                salary = gj_split_salary_string(salary)
            except:
                location = ''
                salary = ['null', 'null', 'null']

            try:
                attributes = []
                bs_attributes = vacancy.find('div', {'class': 'info'}).findNext('div', {'class': 'info'})
                for attribute in bs_attributes.find_all('span'):
                    attributes.append(attribute.get_text())
                attributes = ', '.join(attributes)
            except:
                attributes = ''

            try:
                publication_time = vacancy.find('time', {'class': 'truncate datetime-info'})
                publication_time = publication_time.get_text()
            except:
                publication_time = ''
            
            try:        
                link = vacancy.find('p', {'class': 'truncate vacancy-name'}) #find vacancy publication datetime
                link = link.find('a')
                link = 'https://geekjob.ru' + str(link.attrs['href']) 
                #bad idea to concatenate url's like that, but I didn't come up with elegant solution so far
            except:
                link = ''

            vacancies_list.append([company, 
                                   name,
                                   location, 
                                   attributes, 
                                   publication_time, 
                                   salary, 
                                   link])


def main():
    logging.basicConfig(filename=gj_log_path, 
                        level=logging.INFO, filemode='a', format="%(asctime)s %(levelname)s %(message)s")
    logging.info('Started Geek Job parser')
    ua = UserAgent()
    proxies = get_correct_proxies(proxies_path)
    gj_total_pages = gj_get_total_pages(url = gj_vacancies_url, ua = ua, proxies = proxies)

    filename = os.path.join(data_destination, f'GeekJob_{datetime.today().strftime("%Y-%m-%d")}.csv')
    if delete_old_file(filename):
        logging.info('deleted old file ' + filename)
    
    #asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) #for windows only
    asyncio.run(vacancies_crawler(source = 'Geek Job',
                                  url = gj_vacancies_url, 
                                  proxies = proxies, 
                                  ua = ua,
                                  total_pages = gj_total_pages, 
                                  filename = filename,
                                  replace_page = gj_replace_page, 
                                  parse_page = gj_parse_page))

    logging.info('Finished Geek Job parser')
    

if __name__ == '__main__':
    main()
