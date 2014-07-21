'''
This module is for converting existing .csv files containing patent data into usable SQL tables 
in the 'patents' database. These tables will include:

* 'cpcs': A table mapping all patent numbers to their respective Cooperative Patent 
    Classification (CPC) codes, with one row for each pairing of patent number to 
    code and each patent number having at least one but likely many codes. Table initially
    created in psql with query "CREATE TABLE cpcs(pat_num INT, cpc TEXT);" and built out with
    function add_to_cpcs.
* 'experts': A table mapping experts to the patents on which they have previously testified, 
    with one row for each pairing of expert to patent and the possibility of seeing both 
    experts and patents repeated. Created by calling add_to_experts.
* 'exp_cpcs': A subset of 'cpcs' that will contain only those patent numbers that are 
    currently tied to an expert witness. Not created in this module but included here for 
    reference. Created in psql with query "CREATE TABLE exp_cpcs AS (SELECT * FROM cpcs 
    WHERE pat_num IN (SELECT pat_num FROM experts));"
* 'inventors': A table mapping all experts in the database to each patent on which they have
    previously testified. Many experts have testified on multiple patents, and some patents
    have more than one expert.
* 'patent_text': A table containing all text data for each patent associated with an expert,
    which includes its title, abstract, all claims and its description.
* 'references': A table mapping all patents with an associated expert to each of the patents
    that they cite as references. Most patents have multiple references, and some references may 
    occur multiple times.
* 'levels' : A table with all CPC codes in order and the "level" of each code. The level indicates
    how granular the code is intended to be and which codes are considered subsets of other codes.

© 2014 Erin Burnside
'''


import pandas as pd
import psycopg2
import csv
from sqlalchemy import create_engine
import patent_scraper


def add_to_cpcs (data_file, cutoff):
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
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


def add_to_experts (ctp_data_file, etc_data_file, engine):
    df_ctp = create_ctp(ctp_data_file)
    df_etc = pd.read_csv(etc_data_file)
    
    df = df_ctp.merge(df_rtc, left_on = 'case_num', right_on = 'case')
    df.drop('case', axis = 1, inplace = True)
    
    df.to_sql('experts', engine)
    
    return df_ctp
    

def use_scraper(df, pat_column):
    pat_list = df[pat_column].tolist()
    df['titles'], df['inventors'], df['refs'], df['abstr'], df['claims'], df['descr'] = patent_scraper.scrape_patents(pat_list)
    

def create_one_to_many (df, one_col, many_col):
    otm_list = []
    
    for ii, one in enumerate(df[one_col]):
        for many in df[many_col].iloc[ii]:
            otm_list.append([one, many])
        
    df_otm = pd.DataFrame(otm_list)
    return df_otm

    
def add_pat_text_tables(df, pat_column, engine):
    use_scraper(df, pat_column) 
    
    df_text = df[['pat_num','titles','abstr','claims','descr']]
    df_text.to_sql('patent_text', engine)
    
    create_one_to_many(df, 'pat_num', 'inventors').to_sql('inventors', engine)
    create_one_to_many(df, 'pat_num', 'refs').to_sql('references', engine)

    
def add_cpc_levels (data_file, engine):
    df_levels = pd.read_csv(data_file)
    df_levels.drop('id', axis = 1, inplace = True)
    df_levels.to_sql('levels', engine)
    
               
if __name__ == '__main__':
    add_to_cpcs('data/pat_to_cpc_mini.csv', 4291218)
    
    engine = create_engine('postgresql://erinburnside:@localhost/patents')
    df_ctp = add_to_experts('data/case_to_pat.csv', 'data/record_to_case.csv', engine)
    
    add_pat_text_tables(df_ctp, 'pat_num', engine)
    add_cpc_levels('/data/cpc_table.csv', engine)