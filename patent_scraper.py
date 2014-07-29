'''
Collects and formats online patent data (title, inventors, abstract, 
claims, description, references).

(C) 2014 Erin Burnside
'''


import time

import requests
from bs4 import BeautifulSoup


def get_meta (soup_object):
    '''
    INPUT: BS4 OBJECT soup_object
    OUTPUT: (LIST OF STRINGS titles, LIST OF STRINGS inventors, 
        LIST OF STRINGS references) TUPLE
    
    Gets relevant content from the "meta" sections of the Beautiful Soup
    patent object.
    '''
    titles, inventors, references = [],[],[]
    for meta in soup_object.find_all('meta'):
        attrs = meta.attrs
        if 'scheme' in attrs: 
            if meta['scheme'] == 'inventor':
                inventors.append(meta['content'])
            elif (meta['scheme'] == 'references' 
                  and meta['content'].startswith('US')):
                references.append(meta['content'])
        elif 'name' in attrs and meta['name'] == 'DC.title':
            titles.append(meta['content']) 
    return (titles, inventors, references)


def filter_text (raw_text, st_pt, end_pt):
    '''
    INPUT: STRING raw_text, INT st_pt, INT end_pt
    OUTPUT: STRING filt_text
    
    Takes raw text data from scraping a patent website and returns 
    content between the starting and ending markers.
    '''
    st = raw_text.find(st_pt)
    if st == -1:
        return ''
    end = raw_text.find(end_pt, st)
    filt_text = raw_text[(st + len(st_pt)):end]
    return filt_text

def scrape_patents (pat_list):
    '''
    INPUT: LIST OF INTS pat_list
    OUTPUT: LIST OF STRINGS titles, LIST OF STRINGS inventors, 
        LIST OF STRINGS references, LIST OF STRINGS abstracts,
        LIST OF STRINGS claims, LIST OF STRINGS descriptions
    
    Scrapes and formats important data (title, inventor(s), references,
    abstract, claims, and description) for each patent in pat_list.
    '''
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