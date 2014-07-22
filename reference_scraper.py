'''
Collects patent reference data for creating reference graph. Main function takes a
"root" patent (currently will be one that is linked to an expert) and inserts into
a SQL table all referencer-referenced patent pairs that are linked to this root.

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
'''
INPUT: INT root, PSYCOPG CURSOR cur
OUTPUT: LIST OF INTS pending_pats

For instances in which the table has been partially filled, this determines 
all patents (stored by patent number in the list pending_pats) that have been 
identified as linked to the graph but that have not yet had these 
links investigated. 
'''
    table_name = "ref_" + str(root)
    query1 = "SELECT ref_out FROM " 
    query2 = " WHERE ref_out NOT IN (SELECT ref_in FROM "
    query3 = ") GROUP BY ref_out;"
    cur.execute(query1 + table_name + query2 + table_name + query3)
    pending_pats = [pending[0] for pending in cur.fetchall()]
    return pending_pats
    

def get_completed (root, cur):
'''
INPUT: INT root, PSYCOPG CURSOR cur
OUTPUT: LIST OF INTS completed_pats

For instances in which the table has been partially filled, this determines 
all patents (stored by patent number in the list completed_pats) that have been 
identified as linked to the graph and had all their links investigated.
'''
    table_name = "ref_" + str(root)
    query = "SELECT ref_in FROM " + table_name + " GROUP BY ref_in;"
    cur.execute(query)
    completed_pats = [completed[0] for completed in cur.fetchall()]
    return completed_pats


def get_referencers(pat_num):
'''
INPUT: INT pat_num
OUTPUT: LIST OF INTS new_refs 

Takes any US patent number and returns the patent numbers of all other US patents
that cite the given one as a reference.
'''
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
'''
INPUT: INT pat_num
OUTPUT: LIST OF INTS new_refs 

Takes any US patent number and returns the patent numbers of all other US patents
that are cited by that patent as references.
'''
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
'''
INPUT: INT root, INT ref_in, INT ref_out PSYCOPG CURSOR cur
OUTPUT: NONE

Queries the SQL table with the name "ref_<root>" to insert a row linking ref_in (the
patent doing the referencing) to ref_out (the patent being referenced).
'''
    table_name = "ref_" + str(root)
    query = "INSERT INTO " + table_name + " (ref_in, ref_out) VALUES (%s, %s);"
    cur.execute(query, (ref_in, ref_out))
    
    
def get_network(root, completed_pats, pending_pats, conn, cur):
'''
INPUT: INT root, LIST OF INTS completed_pats, LIST OF INTS pending_pats,
    PSYCOPG CONNECTION conn, PSYCOPG CURSOR cur
OUTPUT: NONE

If pending_pats is empty, the associated SQL table is queried to find all patents that
have been found to be in the network but not investigated (pending_pats) and
all those that have been found to be in the network and also investigated
(completed_pats). If still empty (meaning the SQL table has nothing in it),
the root is assumed to be the only pending patent and added to pending_pat.

The first patent on pending_pats is investigated to find all links both forwards
and backwards. All links are added to the end of pending_pats, but only forward
links are added to the SQL table to prevent duplication. 

The patent being investigated is added to completed_pats, and the function is called
recursively using the updated pending and completed patent lists.
'''
    if pending_pats == []:
        pending_pats += get_pending(root, cur)
        completed_pats += get_completed(root, cur)
        if pending_pats == []:
            pending_pats.append(root)
    
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
    