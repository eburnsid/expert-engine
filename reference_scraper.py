'''
Collects patent reference data for creating reference graph. Main 
function takes a "root" patent (currently will be one that is linked to 
an expert) and inserts into a SQL table all referencer-referenced patent 
pairs that are linked to this root.

(C) 2014 Erin Burnside
'''


import time

import requests
from bs4 import BeautifulSoup
import psycopg2


def get_exp_pat_nums (cur):
    '''
    INPUT: PSYCOPG CURSOR cur
    OUTPUT: LIST OF INTS pat_nums
    
    Pulls list of all patent numbers associated with experts from SQL
    and returns this list.
    '''
    
    query = "SELECT pat_num FROM experts GROUP BY pat_num;"
    cur.execute(query)
    pat_nums = [pat_num[0] for pat_num in cur.fetchall()]
    return pat_nums


def get_pending (root, cur):
    '''
    INPUT: INT root, PSYCOPG CURSOR cur
    OUTPUT: LIST OF INTS pending_pats

    For instances in which the table has been partially filled, this 
    determines all patents (stored by patent number in the list 
    pending_pats) that have been identified as linked to the graph but 
    that have not yet had these links investigated. 
    '''
    
    table_name = 'ref_' + str(root)
    query = 'SELECT ref_out FROM ' + table_name
    query += ' WHERE ref_out NOT IN (SELECT ref_in FROM ' + table_name
    query += ') GROUP BY ref_out;'
    cur.execute(query)
    pending_pats = [pending[0] for pending in cur.fetchall()]
    return pending_pats
    

def get_completed (root, cur):
    '''
    INPUT: INT root, PSYCOPG CURSOR cur
    OUTPUT: LIST OF INTS completed_pats

    For instances in which the table has been partially filled, this 
    determines all patents (stored by patent number in the list 
    completed_pats) that have been identified as linked to the graph and 
    had all their links investigated.
    '''
    
    table_name = 'ref_' + str(root)
    query = 'SELECT ref_in FROM ' + table_name + ' GROUP BY ref_in;'
    cur.execute(query)
    completed_pats = [completed[0] for completed in cur.fetchall()]
    return completed_pats


def get_referencers (pat_num):
    '''
    INPUT: INT pat_num
    OUTPUT: LIST OF INTS new_refs 

    Takes any US patent number and returns the patent numbers of all 
    other US patents that cite the given one as a reference.
    '''
    
    url = 'http://www.freepatentsonline.com/'
    url += 'result.html?sort=relevance&srch=top&query_txt=REFN%2F'
    url += str(pat_num)
    url += '&submit=&patents=on'
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    new_refs = []
    for td in soup.find_all('td'):
        if td['width'] == '15%' and td.text[7].isdigit() == True:
            new_ref = int(td.text[7:14])
            new_refs.append(new_ref)
        
    return new_refs
    
    
def get_referenced (pat_num):
    '''
    INPUT: INT pat_num
    OUTPUT: LIST OF INTS new_refs 

    Takes any US patent number and returns the patent numbers of all 
    other US patents that are cited by that patent as references.
    '''
    
    url = 'http://www.freepatentsonline.com/' + str(pat_num) + '.html'
    r = requests.get(url)
    soup = BeautifulSoup(r.text)    
    
    new_refs = []
    for meta in soup.find_all('meta'):
        attrs = meta.attrs
        if 'scheme' in attrs: 
            if (meta['scheme'] == 'references' and 
                    meta['content'].startswith('US') and 
                    len(meta['content']) == 9 and 
                    meta['content'][2].isdigit() == True):
                new_refs.append(int(meta['content'][2:]))
    return new_refs
    
    
def add_reference (root, ref_in, ref_out, cur, level):
    '''
    INPUT: INT root, INT ref_in, INT ref_out PSYCOPG CURSOR cur
    OUTPUT: NONE

    Queries the SQL table with the name "ref_<root>" to insert a row 
    linking ref_in (the patent doing the referencing) to ref_out (the 
    patent being referenced).
    '''
    
    table_name = 'ref_' + str(root)
    query = 'INSERT INTO ' + table_name 
    query += ' (ref_in, ref_out, level) VALUES (%s, %s, %s);'
    cur.execute(query, (ref_in, ref_out, level))
    
    
def get_one_network(root, conn, cur, completed_pats=[], pending_pats=[],  
                    level=0, max_level=2):
    '''
    INPUT: INT root, LIST OF INTS completed_pats, LIST OF INTS 
        pending_pats, PSYCOPG CONNECTION conn, PSYCOPG CURSOR cur
    OUTPUT: NONE

    If pending_pats is empty, the root is assumed to be the only pending 
    patent and added to pending_pat.

    The first patent on pending_pats is investigated to find all links 
    both forwards and backwards. All links are added to the end of 
    pending_pats, but only forward links are added to the SQL table to 
    prevent duplication (until max_level is reached, at which point both 
    forward and backward links are added). 

    The patent being investigated is added to completed_pats, and the 
    function is called recursively using the updated pending and 
    completed patent lists.
    '''
    
    if level > max_level:
        return
    
    if pending_pats == []:
        pending_pats.append(root)
        print pending_pats

    new_pending_pats = []
    
    for pat_num in pending_pats:
        
        new_refs_in = get_referencers(pat_num)
        for refi in new_refs_in:
            if refi not in completed_pats and refi not in pending_pats:
                new_pending_pats.append(refi)
                if level == max_level:
                    add_reference(root, refi, pat_num, cur, level)

        new_refs_out = get_referenced(pat_num)
        for refo in new_refs_out:
            add_reference(root, pat_num, refo, cur, level)
            if refo not in completed_pats and refo not in pending_pats:
                new_pending_pats.append(refo)
            conn.commit()
        
        completed_pats.append(pending_pats.pop(0))
        print pat_num, level
        time.sleep(1)

    pending_pats += new_pending_pats

    if len(pending_pats) != 0:
        level += 1
        get_network(root, conn, cur, completed_pats, pending_pats, level)
    

def get_all_networks (db_name, user, pat_nums=[]):
    '''
    INPUT: STRING db_name, STRING user, LIST OF INTS pat_nums
    OUTPUT: NONE
    
    Scrapes reference networks for all patent numbers listed in pat_nums
    and inserts them into tables in the specified SQL database. If no
    patent numbers are specified, will complete for all patents
    associated with experts.
    '''
    conn = psycopg2.connect(database=db_name, user=user)
    cur = conn.cursor()
    if pat_nums == []:
        pat_nums = get_exp_pat_nums(cur)

    for pat_num in pat_nums:
        query = 'CREATE TABLE ref_' + str(int(pat_num))
        query += ' (ref_in INT, ref_out INT, level INT);'
        cur.execute(query)
        conn.commit()
        get_one_network(int(pat_num), conn, cur, completed_pats=[], 
                        pending_pats=[])

    
if __name__ == '__main__':
    get_all_networks('patents', 'postgres')