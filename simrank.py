'''
Implementation of SimRank algorithm for patent references. SimRank 
operates under the assumption that if two items are reference by similar
items that they are also somewhat similar. One of the use cases in the
initial paper is determining similarity of academic literature; the same
idea applies to citation of patents.

(C) 2014 Erin Burnside
'''


import cPickle

import pandas as pd
import numpy as np
import psycopg2


def get_edge_list (root, conn):
    '''
    INPUT: INT root, PSYCOPG2 CONNECTION conn
    OUTPUT: PANDAS DATAFRAME edge_df
    
    Creates a Pandas dataframe of all the edges in the specified SQL 
    database.
    '''
    query = 'SELECT * FROM ref_' + str(root) + ';'
    
    edge_df = pd.io.sql.read_frame(query, conn)
    return edge_df


def find_w (root, conn):
    '''
    INPUT: INT root, PSYCOPG2 CONNECTION conn
    OUTPUT: 2-DIM NUMPY ARRAY w, 2-DIM NUMPY ARRAY pat_arr
    
    Uses the edge list to find the n x n matrix w used for the matrix-
    based implementation of SimRank.
    '''
    edge_df = get_edge_list(root, conn)
    pat_arr = np.unique(np.append(edge_df['ref_in'], edge_df['ref_out']))

    w = np.zeros((pat_arr.shape[0], pat_arr.shape[0]))
    for ii in range(pat_arr.shape[0]):
        print ii
        ii_edge_df = edge_df[edge_df['ref_in'] == pat_arr[ii]]['ref_out']
        for jj in range(pat_arr.shape[0]):
            if pat_arr[jj] in [pat_num for pat_num in ii_edge_df]:
                jj_edge_df = edge_df[edge_df['ref_out'] == pat_arr[jj]]
                w[ii][jj] = 1. / jj_edge_df.shape[0]
                print w[ii][jj]
                    
    return w, pat_arr


def pickle_arr (sr_arr, filename):
    '''
    INPUT: 2-DIM NUMPY ARRAY s, STRING filename
    OUTPUT: NONE
    
    Used for pickling both s and w so that calculations can be resumed 
    mid-SimRank if necessary.
    '''
    f = open(filename, 'wb')
    cPickle.dump(sr_arr, f)
    f.close()


def add_col (root, conn):
    '''
    INPUT: INT root, PSYCOPG2 CONNECTION conn
    OUTPUT: NONE
    
    Adds a column to the simrank table corresponding to the root patent.
    '''
    cur = conn.cursor()
    query = 'ALTER TABLE simrank ADD '
    query += '%s NUMERIC DEFAULT 0;' % ('pat_' + str(root),)
    cur.execute(query)
    conn.commit()   


def add_row (conn, pat_num):
    '''
    INPUT: PSYCOPG2 CONNECTION conn, 2-DIM NUMPY ARRAY pat_arr, INT ii
    OUTPUT: NONE
    
    Adds row for
    '''
    cur = conn.cursor()
    query1 = 'SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS' 
    query1 += " WHERE table_name = 'simrank';"
    cur.execute(query1)
    new_row = tuple([pat_num] + [0 for ii in range(cur.fetchall()[0][0] - 1)])
    query2 = 'INSERT INTO simrank VALUES ' + str(new_row) + ';'
    cur.execute(query2)
    conn.commit() 


def insert_scores (s, root, pat_arr, conn):
    '''
    INPUT: 2-DIM NUMPY ARRAY s, 2-DIM NUMPY ARRAY pat_arr, INT root,
         PSYCOPG2 CONNECTION conn
    OUTPUT: NONE
    
    Pulls final scores from s matrix and inserts into SQL for future 
    retrieval.
    '''
    root_index = np.where(pat_arr == root)[0]
    cur = conn.cursor()
    for (ii, score) in enumerate(s[root_index][0]):
        pat_num = pat_arr[ii]
        if score != 0:
            query1 = 'SELECT * FROM simrank WHERE pat_num = ' 
            query1 += str(pat_num) + ';'
            cur.execute(query1)
            if cur.fetchall() == []:
                add_row(conn, pat_num)
            query2 = 'UPDATE simrank SET pat_' + str(root)
            query2 += ' = %s WHERE pat_num = %s;'
            cur.execute(query2, (score, pat_num))
            conn.commit()


def simrank (root, conn, c, w=None):
    '''
    INPUT: INT root, PSYCOPG2 CONNECTION conn, INT c
    OUTPUT: NONE
    
    Complete calculated of SimRank for a specified root patent with 
    reference network already present in SQL.
    '''
    if not w:
        w, pat_arr = find_w(root, conn)
        pickle_arr(w, 'w' + str(root) + '.pkl')
    
    s_new = np.identity(w.shape[0])
    for ii in range(10):
        s_old = s_new
        s_new = np.dot(np.dot(c * w.T,s_old),w)
        for jj in range(s_new.shape[0]):
            s_new[jj][jj] = 1
    
    # add_col(root, conn)
    insert_scores(s_new, root, pat_arr, conn)
    

if __name__ == "__main__":
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    simrank(5352605, conn, 0.8)