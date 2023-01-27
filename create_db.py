import sqlite3
from config import db_path

def sql_create_tables(db_full_path:str) -> None:
    queries = []

    queries.append('''
                   CREATE TABLE IF NOT EXISTS processed_files (file_name,
                                                               processed_datetime,
                                                               PRIMARY KEY(file_name))
                   ''')
    
    queries.append('''
                   CREATE TABLE IF NOT EXISTS geek_job_vacancies (company_name,
                                                                  vacancy_name,
                                                                  vacancy_address,
                                                                  vacancy_tags,
                                                                  vacancy_date,
                                                                  vacancy_salary_from INTEGER,
                                                                  vacancy_salary_to INTEGER,
                                                                  vacancy_salary_currency,
                                                                  vacancy_link,
                                                                  PRIMARY KEY(vacancy_date, vacancy_link))
                   ''')
    
    queries.append('''
                   CREATE INDEX IF NOT EXISTS idx_geek_job_salary ON
                   geek_job_vacancies(vacancy_salary_from, vacancy_salary_to, vacancy_salary_currency)
                   ''')
    
    queries.append('''
                   CREATE TABLE IF NOT EXISTS get_match_vacancies (company_name,
                                                                   vacancy_name,
                                                                   vacancy_grade,
                                                                   vacancy_work_type,
                                                                   vacancy_date,
                                                                   vacancy_salary_from INTEGER,
                                                                   vacancy_salary_to INTEGER,
                                                                   vacancy_salary_currency,
                                                                   vacancy_link,
                                                                   PRIMARY KEY(vacancy_date, vacancy_link))
                   ''')

    queries.append('''
                   CREATE INDEX IF NOT EXISTS idx_get_match_salary ON
                   get_match_vacancies(vacancy_salary_from, vacancy_salary_to, vacancy_salary_currency)
                   ''')

    queries.append('''
                   CREATE TABLE IF NOT EXISTS habr_career_vacancies (company_name,
                                                                     vacancy_name,
                                                                     vacancy_work_type,
                                                                     vacancy_tags,
                                                                     vacancy_date,
                                                                     vacancy_salary_from INTEGER,
                                                                     vacancy_salary_to INTEGER,
                                                                     vacancy_salary_currency,
                                                                     vacancy_link,
                                                                     PRIMARY KEY(vacancy_date, vacancy_link))  
                   ''')
    
    queries.append('''
                   CREATE INDEX IF NOT EXISTS idx_habr_career_salary ON
                   habr_career_vacancies(vacancy_salary_from, vacancy_salary_to, vacancy_salary_currency)
                   ''')

    queries.append('''
                   CREATE TABLE IF NOT EXISTS head_hunter_vacancies (hh_role,
                                                                     company_name,
                                                                     vacancy_link,
                                                                     vacancy_name,
                                                                     vacancy_address,
                                                                     vacancy_date,
                                                                     vacancy_salary_from INTEGER,
                                                                     vacancy_salary_to INTEGER,
                                                                     vacancy_salary_currency,
                                                                     company_link,
                                                                     vacancy_requirements,
                                                                     vacancy_responsibilities,
                                                                     PRIMARY KEY(vacancy_date, vacancy_link)) 
                   ''')
    
    queries.append('''
                   CREATE INDEX IF NOT EXISTS idx_head_hunter_salary ON
                   head_hunter_vacancies(vacancy_salary_from, vacancy_salary_to, vacancy_salary_currency)
                   ''')
    
    queries.append('''
                   CREATE TABLE IF NOT EXISTS currency_to_ruble_rates (currency,
                                                                       ruble_amount,
                                                                       date,
                                                                       PRIMARY KEY(currency, date))
             ''')

    with sqlite3.connect(db_full_path) as db:
        cursor = db.cursor()
        for query in queries:
            cursor.execute(query)

def sql_create_views(db_full_path:str) -> None:
    queries = []

    queries.append('''
                   CREATE VIEW IF NOT EXISTS salaries_view AS
                   SELECT 
			  	     round((one+two)*ruble_amount/2) AS salary,
			  	     currency,
			  	     grade,
                     hh_role,
                     source,
                     vacancy_date AS date,
                     company_name,
                     vacancy_name
			       FROM(
			  	     SELECT 
			  	    	 COALESCE(vacancy_salary_from, vacancy_salary_to) AS one, 
			  	    	 COALESCE(vacancy_salary_to, vacancy_salary_from) AS two,
			  	    	 vacancy_salary_currency,
			  	    	 CASE
			  	    		 WHEN lower(vacancy_name) like '%intern%' or lower(vacancy_name) like '%стажёр%'
			  	    			 THEN 'intern'
			  	    		 WHEN lower(vacancy_name) like '%junior%' or lower(vacancy_name) like '%младший%'
			  	    			 THEN 'junior'
			  	    		 WHEN lower(vacancy_name) like '%middle%' or lower(vacancy_name) like '%мидл%'
			  	    			 THEN 'middle'
			  	    		 WHEN lower(vacancy_name) like '%senior%' or lower(vacancy_name) like '%сеньор%' or lower(vacancy_name) like '%старший%'
			  	    			 THEN 'senior'
			  	    		 WHEN lower(vacancy_name) like '%lead%' or lower(vacancy_name) like '%ведущий%'
			  	    			 THEN 'lead'
			  	    	 END AS grade,
                         hh_role,
			  	    	 vacancy_date,
                         'HeadHunter' AS source,
                         company_name,
                         vacancy_name
			  	     FROM head_hunter_vacancies
			  	    	 UNION ALL
			  	     SELECT 
			  	    	 COALESCE(vacancy_salary_from, vacancy_salary_to) AS one, 
			  	    	 COALESCE(vacancy_salary_to, vacancy_salary_from) AS two,
			  	    	 vacancy_salary_currency, 
			  	    	 CASE 
			  	    		 WHEN lower(vacancy_tags) like '%intern%'
			  	    			 THEN 'intern'
			  	    		 WHEN lower(vacancy_tags) like '%junior%'
			  	    			 THEN 'junior'
			  	    		 WHEN lower(vacancy_tags) like '%middle%'
			  	    			 THEN 'middle'
			  	    		 WHEN lower(vacancy_tags) like '%senior%'
			  	    			 THEN 'senior'
			  	    		 WHEN lower(vacancy_tags) like '%lead%'
			  	    			 THEN 'lead'
			  	    	 END AS grade,
                         NULL AS hh_role,
			  	    	 vacancy_date,
                         'HabrCareer' AS source,
                         company_name,
                         vacancy_name
			  	     FROM habr_career_vacancies
			  	    	 UNION ALL
			  	     SELECT 
			  	    	 COALESCE(vacancy_salary_from, vacancy_salary_to) AS one, 
			  	    	 COALESCE(vacancy_salary_to, vacancy_salary_from) AS two,
			  	    	 vacancy_salary_currency, 
			  	    	 vacancy_grade AS grade,
                         NULL AS hh_role,
			  	    	 vacancy_date,
                         'GetMatch' AS source,
                         company_name,
                         vacancy_name
			  	     FROM get_match_vacancies
			  	    	 UNION ALL
			  	     SELECT
			  	    	 COALESCE(vacancy_salary_from, vacancy_salary_to) AS one, 
			  	    	 COALESCE(vacancy_salary_to, vacancy_salary_from) AS two,
			  	    	 vacancy_salary_currency, 
			  	    	 CASE
			  	    		 WHEN lower(vacancy_name) like '%intern%' or lower(vacancy_name) like '%стажёр%'
			  	    			 THEN 'intern'
			  	    		 WHEN lower(vacancy_name) like '%junior%' or lower(vacancy_name) like '%младший%'
			  	    			 THEN 'junior'
			  	    		 WHEN lower(vacancy_name) like '%middle%' or lower(vacancy_name) like '%мидл%'
			  	    			 THEN 'middle'
			  	    		 WHEN lower(vacancy_name) like '%senior%' or lower(vacancy_name) like '%сеньор%' or lower(vacancy_name) like '%старший%'
			  	    			 THEN 'senior'
			  	    		 WHEN lower(vacancy_name) like '%lead%' or lower(vacancy_name) like '%ведущий%'
			  	    			 THEN 'lead'
			  	    	 END AS grade,
                         NULL AS hh_role,
			  	    	 vacancy_date,
                         'GeekJob' AS source,
                         company_name,
                         vacancy_name
			  	     FROM geek_job_vacancies
			       ) AS data
			       LEFT JOIN currency_to_ruble_rates AS rates ON
			  	     rates.currency = data.vacancy_salary_currency
			       AND rates.date = data.vacancy_date
                   ''')

    with sqlite3.connect(db_full_path) as db:
        cursor = db.cursor()
        for query in queries:
            cursor.execute(query)              

def main():
    db_full_path = db_path + 'vacancies.db'

    sql_create_tables(db_full_path)
    sql_create_views(db_full_path)

if __name__ == '__main__':
    main()