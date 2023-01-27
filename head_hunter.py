import requests
import time
import logging
import random
import os
import tqdm
import glob
from fake_useragent import UserAgent
from datetime import datetime
from csv import writer
from proxy_checker import get_correct_proxies
from config import proxies_path, hh_log_path, data_destination

def insert_to_file(filename: str, vacancies_list: list) -> None:
    logging.info(f"Inserting {str(len(vacancies_list))} vacancies")
    with open(filename, 'a', encoding='utf-8', newline='') as f_object:
        while vacancies_list:
            writer_object = writer(f_object, delimiter = '|')
            writer_object.writerow(vacancies_list.pop())


def delete_old_file(filename: str) -> bool:
    try:
        os.remove(filename)
        return True
    except OSError:
        return False


def hh_get_it_roles(hh_roles_url: str, ua, proxies: list) -> dict:
    professional_roles = hh_request_api(url=hh_roles_url, params=None, ua=ua, proxies=proxies)
    it_roles_dict = {} #first value is id, second is the name
    for spec_list in professional_roles['categories']:
        if spec_list['name'] == 'Информационные технологии':
            for role in spec_list['roles']:
                it_roles_dict[role['id']] = role['name']
    return it_roles_dict


def hh_get_all_areas(hh_area_url: str, ua, proxies) -> list:
    areas_list = [[]]
    data = hh_request_api(url=hh_area_url, params=None, ua=ua, proxies=proxies)
    for area in data['areas']:
        if (area['name'] == 'Москва') or (area['name'] == 'Санкт-Петербург'):
            areas_list.append([area['id']])
        else:
            areas_list[0].append(area['id'])
    return areas_list


def hh_get_experience_list(hh_exp_url: str, ua, proxies) -> list:
    experience_list = []
    data = hh_request_api(url=hh_exp_url, params=None, ua=ua, proxies=proxies)
    for row in data['experience']:
        experience_list.append(row['id'])
    return experience_list


def hh_request_api(url: str, params: dict, ua, proxies: list): 
    time.sleep(random.uniform(0, 3))
    return requests.get(url, 
                        params, 
                        headers={'User-Agent': ua.random}, 
                        proxies={'https': 'https://'+random.choice(proxies)}, 
                        timeout=5).json()


def hh_calculate_salary_string(salary_dict: dict) -> list:
    if salary_dict is not None:
        salary_list = [salary_dict['from'],
                       salary_dict['to'],
                       salary_dict['currency']]

        if salary_dict['gross']:
            if salary_list[0] is not None:
                salary_list[0] = int(round(salary_list[0]*0.87))
            if salary_list[1] is not None:
                salary_list[1] = int(round(salary_list[1]*0.87))
    else:
        salary_list = ['null', 'null', 'null']
    return salary_list


def hh_parse_page(vacancy_role, elem) -> list:
    try:
        vacancy_id = elem['id']
    except:
        vacancy_id = ''

    try:
        vacancy_url = elem['alternate_url']
    except:
        vacancy_url = '' 

    try:
        vacancy_name = elem['name']
    except:
        vacancy_name = ''

    try:
        vacancy_address = elem['address']['raw']
    except:
        vacancy_address = ''

    try:
        vacancy_datetime = elem['created_at']
    except:
        vacancy_datetime = ''

    try:
        vacancy_salary = elem['salary']
    except:
        vacancy_salary = None
    vacancy_salary = hh_calculate_salary_string(vacancy_salary)

    try:
        employer_name = elem['employer']['name']
    except:
        employer_name = ''

    try:
        employer_url = elem['employer']['alternate_url']
    except:
        employer_url = ''

    try:
        vacancy_requirements = elem['snippet']['requirement']
    except:
        vacancy_requirements = ''

    try:
        vacancy_responsibility = elem['snippet']['responsibility']
    except:
        vacancy_responsibility = ''
        
    return [vacancy_role,
            vacancy_id,
            vacancy_url,
            vacancy_name,
            vacancy_address,
            vacancy_datetime,
            vacancy_salary,
            employer_name,
            employer_url,
            vacancy_requirements,
            vacancy_responsibility]


def main():
    logging.basicConfig(filename=hh_log_path, 
                        level=logging.INFO, 
                        filemode='a', 
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.info('Started Head hunter parser')

    filename = os.path.join(data_destination, 'HeadHunter_' + datetime.today().strftime('%Y-%m-%d') + '.csv')
    delete_old_file(filename)
    
    ua = UserAgent()
    proxies = get_correct_proxies(proxies_path)
    hh_vacancies_api_url  = 'https://api.hh.ru/vacancies'
    hh_area_url = 'https://api.hh.ru/areas/113'
    hh_roles_url = 'https://api.hh.ru/professional_roles'
    it_roles_dict = hh_get_it_roles(hh_roles_url, ua, proxies)
    areas_list = hh_get_all_areas(hh_area_url, ua, proxies)
    experience_list = hh_get_experience_list('https://api.hh.ru/dictionaries', ua, proxies)
    vacancies_list = []
    list_of_files = glob.glob(str(data_destination) + '/HeadHunter*')
    seconds = max(os.path.getctime(file) for file in list_of_files) + 3*60*60
    iso_timestamp = datetime.utcfromtimestamp(seconds).strftime("%Y-%m-%dT%H:%M:%S")

    logging.info(f"Number of roles to parse - {len(it_roles_dict.keys())}")
    #start
    for id, vacancy_role in tqdm.tqdm(it_roles_dict.items()):
        params = {
            'professional_role': id, 
            'area': 113, 
            'per_page': 100, 
            'date_from': iso_timestamp
        }
        
        data = hh_request_api(hh_vacancies_api_url, params, ua, proxies)
        logging.info(f"Role={vacancy_role}, Area=Russia, Items={data['found']}")
        if data['found'] < 100:
            for elem in data['items']:
                vacancies_list.append(hh_parse_page(vacancy_role, elem))
            insert_to_file(filename, vacancies_list)
        elif data['found'] > 100 and data['found'] <= 2000:
            for page in range(data['pages']):
                params['page'] = page
                data = hh_request_api(hh_vacancies_api_url, params, ua, proxies)
                for elem in data['items']:
                    vacancies_list.append(hh_parse_page(vacancy_role, elem))
            insert_to_file(filename, vacancies_list)
        else:
            #adding area splitting
            for areas in areas_list:
                params = {
                    'professional_role': id, 
                    'area': areas, 
                    'per_page': 100, 
                    'date_from': iso_timestamp
                }

                data = hh_request_api(hh_vacancies_api_url, params, ua, proxies)

                logging.info(f"--->"
                             f"Role={vacancy_role}, "
                             f"Area={'Москва' if areas[0]=='1' else ('Санкт-Петербург' if areas[0]=='2' else 'Регионы')}, "
                             f"Items={data['found']}")

                if data['found'] < 100:
                    for elem in data['items']:
                        vacancies_list.append(hh_parse_page(vacancy_role, elem))
                    insert_to_file(filename, vacancies_list)
                elif data['found'] > 100 and data['found'] <= 2000:
                    for page in range(data['pages']):
                        params['page'] = page
                        data = hh_request_api(hh_vacancies_api_url, params, ua, proxies)
                        for elem in data['items']:
                            vacancies_list.append(hh_parse_page(vacancy_role, elem))
                    insert_to_file(filename, vacancies_list)
                else:
                    #adding experience to the filter
                    for experience in experience_list:      
                        params = {
                            'professional_role': id, 
                            'area': areas, 
                            'per_page': 100, 
                            'date_from': iso_timestamp, 
                            'experience': experience
                        }

                        data = hh_request_api(hh_vacancies_api_url, params, ua, proxies)

                        logging.info(f"--->--->"
                                     f"Role={vacancy_role}, "
                                     f"Area={'Москва' if areas[0]=='1' else ('Санкт-Петербург' if areas[0]=='2' else 'Регионы')}, "
                                     f"Experience={experience}, "
                                     f"Items={data['found']}")

                        if data['found'] < 100:
                            for elem in data['items']:
                                vacancies_list.append(hh_parse_page(vacancy_role, elem))
                            insert_to_file(filename, vacancies_list)
                        else:
                            for page in range(data['pages']):
                                params['page'] = page
                                data = hh_request_api(hh_vacancies_api_url, params, ua, proxies)
                                for elem in data['items']:
                                    vacancies_list.append(hh_parse_page(vacancy_role, elem))
                            insert_to_file(filename, vacancies_list)
                

if __name__ == '__main__':
    main()
