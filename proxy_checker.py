import requests
import sys
import os
import logging
from bs4 import BeautifulSoup
from config import ip_check_url

logger = logging.getLogger(__name__)

def get_ip_and_ua(useragent = None, proxy = None) -> str:
    try:
        if useragent is not None and proxy is not None:
            r = requests.get(url=ip_check_url, headers={'User-Agent': useragent}, proxies={'https': 'https://'+proxy}, timeout=5)
        elif useragent is not None:
            r = requests.get(url=ip_check_url, headers={'User-Agent': useragent}, timeout=5)
        elif proxy is not None:
            r = requests.get(url=ip_check_url, proxies={'https': 'https://'+proxy}, timeout=5)
        else:
            r = requests.get(url=ip_check_url, timeout=5)
    except:
        return [None, None]

    soup = BeautifulSoup(r.text, 'lxml')
    result_list = []
    result_list.append(soup.find('span', class_ = 'ip').text.strip())
    result_list.append(soup.find('span', class_ = 'ip').find_next_sibling('span').text.strip())
    return result_list


def get_all_proxies(proxies_path: str = 'proxies.txt') -> list:
    proxies = []
    with open(os.path.join(sys.path[0], proxies_path), 'r') as file:
        for line in file:
            if line[0] != '#':
                proxies.append(line.strip())
    return proxies


def get_correct_proxies(proxies_path: str = 'proxies.txt') -> list:
    my_ip = get_ip_and_ua()[0]
    proxies_list = get_all_proxies(proxies_path = proxies_path)
    correct_proxy_count = 0
    correct_proxies_list = []

    for proxy in proxies_list:
        proxy_ip = get_ip_and_ua(proxy=proxy)[0]
        if proxy_ip != my_ip and proxy_ip is not None:
            correct_proxy_count += 1
            correct_proxies_list.append(proxy)
    
    logging.info(str(len(correct_proxies_list)) + ' out of ' + str(len(proxies_list)) + ' proxies are working correctly')
    if len(correct_proxies_list) != len(proxies_list):
        logging.info('Incorrect proxies:')
        for proxy in proxies_list:
            if proxy not in correct_proxies_list:
                logging.info(proxy)
                
    return correct_proxies_list

def main():
    get_correct_proxies()

if __name__ == '__main__':
    main()