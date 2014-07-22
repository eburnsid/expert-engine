'''
Collects patent reference data for creating reference graph.

(C) 2014 Erin Burnside
'''


import pandas as pd
import psycopg2
import csv
import requests
from bs4 import BeautifulSoup
import random
import time


def get_pending (root, cur):
    table_name = "ref_" + str(root)
    query1 = "SELECT ref_out FROM " 
    query2 = " WHERE ref_out NOT IN (SELECT ref_in FROM "
    query3 = ") GROUP BY ref_out;"
    cur.execute(query1 + table_name + query2 + table_name + query3)
    pending_pats = [pending[0] for pending in cur.fetchall()]
    return pending_pats
    

def get_completed (root, cur):
    table_name = "ref_" + str(root)
    query = "SELECT ref_in FROM " + table_name + " GROUP BY ref_in;"
    cur.execute(query)
    completed_pats = [completed[0] for completed in cur.fetchall()]
    return completed_pats


def get_referencers(pat_num):
    url1 = 'http://www.freepatentsonline.com/result.html?sort=relevance&srch=top&query_txt=REFN%2F'
    url2 = str(pat_num)
    url3 = '&submit=&patents=on'
    r = requests.get(url1 + url2 + url3)
    soup = BeautifulSoup(r.text)

    new_refs = []
    for td in soup.find_all('td'):
        if td['width'] == "15%" and td.text[7].isdigit() == True:
            new_ref = int(td.text[7:14])
            new_refs.append(new_ref)
        
    return new_refs
    
    
def get_referenced (pat_num):
    url = 'http://www.freepatentsonline.com/' + str(pat_num) + '.html'
    r = requests.get(url)
    soup = BeautifulSoup(r.text)    
    
    new_refs = []
    for meta in soup.find_all('meta'):
        attrs = meta.attrs
        if 'scheme' in attrs: 
            if meta['scheme'] == 'references' and meta['content'][:2] == 'US' \
            and len(meta['content']) == 9 and meta['content'][2].isdigit() == True:
                new_refs.append(int(meta['content'][2:]))
    return new_refs
    
    
def add_reference (root, ref_in, ref_out, cur):
    table_name = "ref_" + str(root)
    query = "INSERT INTO " + table_name + " (ref_in, ref_out) VALUES (%s, %s);"
    cur.execute(query, (ref_in, ref_out))
    
    
def get_network(root, completed_pats, pending_pats, conn, cur):
    if pending_pats == []:
        pending_pats += get_pending(root, cur)
        completed_pats += get_completed(root, cur)
    
    pat_num = pending_pats[0]
    new_refs_in = get_referencers(pat_num)
    for refi in new_refs_in:
        if refi not in completed_pats and refi not in pending_pats:
            pending_pats.append(refi)
    
    new_refs_out = get_referenced(pat_num)
    for refo in new_refs_out:
        add_reference(root, pat_num, refo, cur)
        if refo not in completed_pats and refo not in pending_pats:
            pending_pats.append(refo)
        conn.commit()
    completed_pats.append(pending_pats.pop(0))
    
    if len(pending_pats) != 0:
        time.sleep(5 + 10 * random.random())
        get_network(root, completed_pats, pending_pats, conn, cur)
    
    
if __name__ == "__main__":
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    get_network(5643446, [], [], conn, cur)
    