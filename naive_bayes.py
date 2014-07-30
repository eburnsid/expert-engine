'''
Building Naive Bayes model.

(C) 2014 Erin Burnside
'''


import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
import psycopg2


def grab_all_text (text_table, expert_table, cur, test_pat):
    '''
    INPUT: STRING text_table, STRING expert_table, PSYCOPG2 CURSOR cur,
        optional INT test_pat
    OUTPUT: PANDAS DATAFRAME text_df
    
    Joins text data per patent to expert id for each expert and returns
    this information in a dataframe.
    '''
    query = 'SELECT * FROM ' + text_table + ' AS t JOIN ' + expert_table 
    query += ' AS e ON t.pat_num = e.pat_num;'
    cur.execute(query)
    
    text_list = []
    for line in cur.fetchall():
        pat_num = line[1]
        if pat_num != test_pat:
            raw_text = line[3] + ' ' + line[4] + ' ' + line[5]
            expert = line[8]
            text_list.append([pat_num, expert, raw_text])
    df_text = pd.DataFrame(text_list, 
                           columns = ['pat_num', 'expert', 'raw_text'])
   
    return df_text
    

def vectorize_text(df_text, text_col):
    '''
    INPUT: PANDAS DATAFRAME text_df, STRING text_col
    OUTPUT: 2-DIM SPARSE ARRAY tfidf_arr, SKLEARN OBJECT tfidf_vect
    
    Vectorizes patent text and returns the vectorized text and the
    vectorizer.
    '''
    tfidf_vect = TfidfVectorizer(stop_words = 'english')
    tfidf_arr = tfidf_vect.fit_transform(df_text[text_col])
    
    return tfidf_arr, tfidf_vect
    
    
def naive_bayes (text_table, expert_table, test_pat, cur):
    '''
    INPUT: STRING text_table, STRING expert_table, INT test_pat,
        PSYCOPG2 CURSOR cur
    OUTPUT: SKLEARN OBJECT tfidf_vect, SKLEARN OBJECT nb_clf,
        PANDAS DATAFRAME df_text
    
    Takes the names of SQL tables containing patent text and expert data
    and returns text vectorizer, Naive Bayes classifier, and a dataframe
    tying text data to expert ids.
    '''
    df_text = grab_all_text(text_table, expert_table, cur, test_pat)
    tfidf_arr, tfidf_vect = vectorize_text(df_text, 'raw_text')
    
    nb_clf = MultinomialNB(class_prior = np.ones(446)/(446.))
    nb_clf.fit(tfidf_arr, df_text['expert'])
    
    return tfidf_vect, nb_clf, df_text


def predict_expert (text_table, expert_table, test_pat, cur):
    '''
    INPUT: STRING text_table, STRING test_pat, PSYCOPG2 CURSOR cur,
        SKLEARN OBJECT tfidf_vect, SKLEARN OBJECT nb_clf,
        PANDAS DATAFRAME df_text
    OUTPUT: PANDAS DATAFRAME df_exp
    
    Uses probabilities for each label given by Naive Bayes to predict
    the experts that are most likely to be a good match for the patent
    test_pat.
    '''
    query = 'SELECT * FROM ' + text_table + ' WHERE pat_num = '
    query += str(test_pat) + ';'
    cur.execute(query)
    
    line = cur.fetchall()
    raw_text = [line[0][3] + ' ' + line[0][4] + ' ' + line[0][5]]
    
    tfidf_vect, nb_clf, df_text = naive_bayes(text_table, expert_table, test_pat, cur)
    
    tfidf_text = tfidf_vect.transform(raw_text) 
    df_exp = pd.DataFrame(nb_clf.classes_, columns=['experts'], 
                          index = nb_clf.classes_)
    df_exp['probs'] = nb_clf.predict_proba(tfidf_text)[0]
    
    experts = [(row[0],row[1]) for (index, row) in df_exp.iterrows()]
    experts.sort(key=lambda x: x[1], reverse=True)

    return experts
        

if __name__ == "__main__":
    pass
    
'''
Cost: 1315
High Cost Patents: 
5888038 (cost = 310)
5133352 (cost = 280)
6305849 (cost = 343)
6473405 (cost = 57)
6408309 (cost = 82)
4701069 (cost = 39)
6205432 (cost = 30)
5573552 (cost = 78)
'''