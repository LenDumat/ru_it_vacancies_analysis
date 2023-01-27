import asyncio, aiohttp, os, logging
from tqdm.asyncio import tqdm
from csv import writer

async def vacancies_crawler(source: str, url: str, proxies: list, ua: callable, 
                            total_pages: int, filename: str, replace_page: callable, parse_page: callable) -> None:
    async with aiohttp.ClientSession(trust_env=True) as session:
        tasks = []
        vacancies_list = []
    
        for i in range(total_pages):
            page = replace_page(i+1, url)
            task = asyncio.create_task(parse_page(session=session, url=page, ua={'User-Agent': ua.random}, 
                                                  proxies=proxies, vacancies_list = vacancies_list))
            tasks.append(task)

        logging.info('Found ' + str(total_pages) + ' pages of vacancies in ' + source)
        #await asyncio.gather(*tasks)
        for future in tqdm(asyncio.as_completed(tasks)):
            await future
            insert_to_file(filename, vacancies_list)


def insert_to_file(filename: str, vacancies_list: list) -> None:
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