'''
This module is for converting existing .csv files containing patent data into usable SQL tables in the 'patents' database. These tables will include:

* 'cpcs': a table mapping all patent numbers to their respective Cooperative Patent Classification (CPC) codes, with one row for each pairing of patent number to code and each patent number having at least one but likely many codes
* 'experts': a table mapping experts to the patents on which they have previously testified, with one row for each pairing of expert to patent and the possibility of seeing both experts and patents repeated
* 'exp_cpcs': a subset of 'cpcs' that will contain only those patent numbers that are currently tied to an expert witness

'''


import pandas as pd
import psycopg2
import csv
from sqlalchemy import create_engine


def add_to_cpcs (data_file, cutoff):
    with open(data_file, 'r') as csvfile:
        pat_reader = csv.reader(csvfile, delimiter = '|')
        ii = 0
        for row in pat_reader:
            if ii > cutoff:
                pat_num = int(row[0][:7])
                for jj in range(1, len(row) - 1):
                    query = "INSERT INTO cpcs (pat_num, cpc) VALUES (%s, %s);"
                    cur.execute(query,(pat_num, row[jj]))
				conn.commit()
            ii += 1    


def create_ctp (ctp_data_file):
    ctp_list = []
    
    with open(data_file, 'r') as csvfile:
        pat_reader = csv.reader(csvfile, delimiter = '|')
        next(pat_reader)
        for row in pat_reader:
            case_num = row[0][:-1]
            ctp_list = ctp_list + [(case_num, int(pat_num)) for pat_num in row[1:-1]]

    df_ctp = pd.DataFrame(ctp_list, columns = ['case_num','pat_num'])
    return df_ctp


def add_to_experts (ctp_data_file, etc_data_file):
    df_ctp = create_ctp(ctp_data_file)
    df_etc = pd.read_csv(etc_data_file)
    
    df = df_ctp.merge(df_rtc, left_on = 'case_num', right_on = 'case')
    df.drop('case', axis = 1, inplace = True)
    
    engine = create_engine('postgresql://erinburnside:@localhost/patents')
    df.to_sql('experts', engine)

               
if __name__ == '__main__':
	conn = psycopg2.connect(database = 'patents', user = 'postgres')
	cur = conn.cursor()

	cur.execute("CREATE TABLE cpcs(pat_num INT, cpc TEXT);")
	conn.commit()

	add_to_cpcs('data/pat_to_cpc_mini.csv', 4291218)
    add_to_experts('data/case_to_pat.csv', 'data/record_to_case.csv')
    
    exp_cpc_query = "CREATE TABLE exp_cpcs AS (SELECT * FROM cpcs WHERE pat_num IN (SELECT pat_num FROM experts));"
    cur.execute(exp_cpc_query)
    conn.commit()    