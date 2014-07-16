import pandas as pd
import psycopg2
import csv
import requests
from bs4 import BeautifulSoup
import time


def get_meta (soup_object):
    titles, inventors, references = [],[],[]
    for meta in soup_object.find_all('meta'):
        attrs = meta.attrs
        if 'scheme' in attrs: 
            if meta['scheme'] == 'inventor':
                inventors.append(meta['content'])
            elif meta['scheme'] == 'references' and meta['content'][:2] == 'US':
                references.append(meta['content'])
        elif 'name' in attrs and meta['name'] == 'DC.title':
            titles.append(meta['content']) 
    return (titles, inventors, references)


def filter_text (raw_text, st_pt, end_pt):
    st = raw_text.find(st_pt)
    if st == -1:
        return ''
    end = raw_text.find(end_pt, st)
    return raw_text[st + len(st_pt) : end]
    

def scrape_patents (pat_list):
    titles = []
    inventors = []
    references = []
    abstracts = []
    claims = []
    descriptions = []
    
    for pn in pat_list:
        url = 'http://www.freepatentsonline.com/' + str(pn) + '.html'
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
    
        meta_fields = get_meta(soup)
        titles += meta_fields[0]
        inventors.append(meta_fields[1])
        references.append(meta_fields[2])
    
        raw_text = soup.div.text
        abstracts.append(filter_text(raw_text, 'Abstract:\n\n', '\n\n\n'))
        claims.append(filter_text(raw_text, 'Claims:\n\n', '\n\n\n'))
        descriptions.append(filter_text(raw_text, 'Description:\n\n', '\n\n\n'))
    
        time.sleep(10)
        
    return titles, inventors, references, abstracts, claims, descriptions