'''
Creates a combination model that averages results from text analysis, 
the CPC-based model and SimRank to predict the best experts for each 
patent.

(C) 2014 Erin Burnside
'''


import psycopg2
import numpy as np
import pandas as pd
from sklearn.preprocessing import scale

import naive_bayes
import basic_model
import simrank


def add_next_model (df, col_name, model, params):
    '''
    INPUT: PANDAS DATAFRAME df, STRING col_name, FUNCTION model, 
        DICT params
    OUTPUT: NONE
    
    Adds scores from the specified model with the given params to df in
    column col_name.
    '''
    df[col_name] = np.zeros(df.shape[0])
    exps = model(**params)
    for (expert, score) in exps:
        df.loc[expert, col_name] = score


def predict_top_n (pat_nums, text_table, expert_table, params, n):
    '''
    INPUT: LIST OF INTS pat_nums, STRING text_table, 
        STRING expert_table, LIST OF FLOATS params, INT n
    OUTPUT: NONE
    
    Predicts the n most relevant experts for the patents in list 
    pat_nums and outputs each patent's top picks to a csv.
    '''
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
    for test_pat in pat_nums:
        matches = naive_bayes.predict_expert(text_table, expert_table, 
                                             test_pat, cur)
        experts = [match[0] for match in matches]
        scores = [match[1] for match in matches]
        df_matches = pd.DataFrame(scores, columns=['nb'], index=experts)
        
        cpc_params = {'test_pat': test_pat, 'params': params, 
                      'agg_func': np.mean}
        add_next_model(df_matches, 'cpcs', basic_model.predict_expert, 
                       cpc_params)
        
        sr_params = {'pat_num': test_pat, 'conn': conn}
        add_next_model(df_matches, 'sr', simrank.predict_expert, sr_params)
        
        df_matches[['nb','cpcs','sr']] = scale(df_matches[['nb','cpcs','sr']])
        df_matches['mean'] = df_matches[['nb', 'cpcs', 'sr']].mean(axis=1)

        df_matches.sort(columns='mean', ascending=False, inplace=True)             
        df_n_matches = df_matches.iloc[:n]

        file_name = str(test_pat) + ".csv"
        df_n_matches.to_csv(file_name)