'''
Given parameters, an aggregation function, and a model, computes the 
associated value of the cost function.

(C) 2014 Erin Burnside
'''


import psycopg2


def cost_function (model, params):
    '''
    INPUT: FUNCTION NAME model, DICT OF ARGUMENTS params
    OUTPUT: INT cost
    
    Pulls all patents in which the following two conditions are met:
    1. the patent is associated with exactly one expert; 2. the expert
    associated with the patent is associated with at least one 
    additional patent. Computes the cost function for each of these 
    patents, where the cost for each prediction is defined as the index
    at which the true expert appears in the prediction list (i.e. 0 if
    the true expert is at the top of the list, and 1 additional point
    for every slot further down the list before the expert appears).
    '''
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
    query = 'SELECT * FROM one_expert_pats AS oep '
    query += 'JOIN many_pat_experts AS mpe ON oep.index = mpe.index;'
    cur.execute(query)
    
    cost = 0
    for star in cur.fetchall():
        params['test_pat'] = star[1]
        print params['test_pat'], star[2]
        matches = model(**params)
        for (ii, match) in enumerate(matches):
            if match[0] == star[2]:
                cost += ii
                print cost
                break
    
    return cost