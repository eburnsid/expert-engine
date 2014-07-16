'''
This module is for converting existing .csv files containing patent data into usable SQL tables in the 'patents' database. These tables will include:

* 'cpcs': a table mapping all patent numbers to their respective Cooperative Patent Classification (CPC) codes, with one row for each pairing of patent number to code and each patent number having at least one but likely many codes
* 'exp_to_pat': a table mapping experts to the patents on which they have previously testified, with one row for each pairing of expert to patent and the possibility of seeing both experts and patents repeated
* 'cpc_exps': a subset of 'cpcs' that will contain only those patent numbers that are currently tied to an expert witness

'''


import pandas as pd
import psycopg2
import csv


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



if __name__ == '__main__':
	conn = psycopg2.connect(database = 'patents', user = 'postgres')
	cur = conn.cursor()

	cur.execute("CREATE TABLE cpcs(pat_num INT, cpc TEXT);")
	conn.commit()

	add_to_cpcs('data/pat_to_cpc_mini.csv', 4291218)