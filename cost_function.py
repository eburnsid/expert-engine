'''
Given parameters, an aggregation function, and a model, computes the 
associated value of the cost function.

(C) 2014 Erin Burnside
'''


import psycopg2


def cost_function (params, agg_func, model):
    '''
    INPUT: LIST OF FLOATS params, FUNCTION NAME agg_func, 
        FUNCTION NAME model
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
    tested = 0
    for star in cur.fetchall():
        tested += 1
        test_patent = star[1]
        print test_patent
        matches = model(test_patent, params, agg_func, table='exp_cpcs', 
                        testing=True)
        for (ii, match) in enumerate(matches):
            if match[0] == star[2]:
                cost += ii
                print cost
                break
    
    return cost