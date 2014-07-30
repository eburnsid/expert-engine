'''
Backbone of Scott's initial model using CPC codes to predict experts. 
Allows for user input of parameters and aggregation function to allow 
for simulated annealing optimization.

(C) 2014 Erin Burnside
'''


import psycopg2


def get_cpc (pat_num, cur, table='cpcs'):
    '''
    INPUT: INT pat_num, PSYCOPG2 CURSOR cur, optional STRING table
    OUTPUT: LIST OF STRINGS cpc_list
    
    Pulls all CPC codes for a given patent from SQL and returns them as 
    a list.
    '''
    query = 'SELECT * FROM %s WHERE pat_num = %s;' % (table, '%s')
    cur.execute(query, [pat_num])
    cpc_list = [code[1] for code in cur.fetchall()]
    
    return cpc_list


def score_first_half (cpc_half_1, cpc_half_2, params):
    '''
    INPUT: STRING cpc_half_1, STRING cpc_half_2, LIST OF FLOATS params
    OUTPUT: FLOAT score
    
    Compares the digits of the first half of two CPC scores to calculate
    a similarity score for the pair. The score is set with the 
    parameters specified in params.
    
    First compares section (first character) and scheme (next three) one 
    character at a time; then checks whether the class (remaining 
    characters) is an exact match.
    '''
    score = 0
    
    for (ii, chs) in enumerate(zip(cpc_half_1[0:4], cpc_half_2[0:4])):
        if chs[0] == chs[1]:
            score += params[ii]
        else:
            break
            
    if score == sum(params[0:4]) and cpc_half_1[4:] == cpc_half_2[4:]:
        return score + params[4]
    
    return score
    

def compute_group_score (level_slice, params):
    '''
    INPUT: LIST OF (STRING, INT) TUPLES level_slice, 
        LIST OF FLOATS params
    OUTPUT: FLOAT score
    
    CPC code groups are arranged in a hierarchical fashion, with levels
    ranging from 0-12 depending on how coarse (small numbers) or fine
    (large numbers) the group is. This function gives a score depending
    on how close the two CPC groups are in this hierarchy (i.e. do their
    groups share parents).
    '''
    cpc_level = sorted([level_slice[0][1],level_slice[-1][1]])
    
    params = [0] + params
    
    if cpc_level[0] == cpc_level[1] and cpc_level[0] == 1:
        return params[0]

    if cpc_level[0] == 0:
        return params[1]
    
    elif cpc_level[0] == cpc_level[1]:
        for ii in range(1, cpc_level[0]):
            if ii in [code[1] for code in level_slice[1:-1]]:
                return sum(params[0:ii])
        return sum(params[0:cpc_level[0]])
    
    else:        
        for ii in range(1, cpc_level[0] + 1):
            if ii in [code[1] for code in level_slice[1:-1]]:
                return sum(params[0:ii])
        return sum(params[0:cpc_level[0] + 1])
        

def score_second_half (cpc_fh, cpc_sh_1, cpc_sh_2, params, cur):
    '''
    INPUT: STRING cpc_fh, STRING cpc_sh_1, STRING cpc_sh_2,
        LIST OF FLOATS params, PSYCOPG2 CURSOR cur
    OUTPUT: FLOAT score
    
    Called when the first halves of two CPC codes are identical. Pulls
    from SQL a list of the hierarchy of the CPC group levels and feeds
    this and the params to compute_group_score.
    '''
    cpcs = sorted([cpc_sh_1, cpc_sh_2])
    
    query = "SELECT * FROM levels WHERE cpc LIKE '" + cpc_fh + "/%';"
    cur.execute(query)
    
    levels = [(cpc.split('/')[1], level) for (id, cpc, level) in 
              cur.fetchall()]
    level_slice = [(cpc, level) for (cpc, level) in levels if 
                   (cpc >= cpcs[0]) and (cpc <= cpcs[1])]
    
    return compute_group_score(level_slice, params)


def compute_scores (cpcs_1, pat_2, cur, params, table_2='cpcs'):
    '''
    INPUT: LIST OF STRINGS cpcs_1, INT pat_2, PSYCOPG2 CURSOR cur,
        LIST OF FLOATS params, optional STRING table_2
    OUTPUT: LIST OF FLOATS scores
    
    Given a list of CPC codes for one patent and the number of another
    patent, computes the similarity score based on the similarity of all
    possible pairings of both sets of CPCs. Takes information about one
    patent in the form of CPCs and the other in the form of a patent
    number to facilitate storage of difficult-to-grab CPCs (those in the
    largest SQL tables) in higher level functions for repeated use.
    '''
    cpcs_2 = get_cpc(pat_2, cur, table_2)
    
    scores = []
    for cpc_1 in cpcs_1:
        cpc_spl_1 = cpc_1.split('/')
        for cpc_2 in cpcs_2:
            if cpc_1 == cpc_2:
                scores.append(sum(params[:-1]))
                continue
            cpc_spl_2 = cpc_2.split('/')
            score = 0
            score += score_first_half(cpc_spl_1[0], cpc_spl_2[0], params[:5])
            if score == sum(params[:5]):
                score += score_second_half(cpc_spl_1[0], cpc_spl_1[1],
                                           cpc_spl_2[1], params[5:], cur)
            scores.append(score)
            
    return scores


def predict_expert (test_pat, params, agg_func, table='cpcs', testing=False):
    '''
    INPUT: INT pat_num, LIST OF FLOATS params, FUNCTION NAME agg_func,
        optional STRING table, optional BOOLEAN testing
    OUTPUT: LIST OF (INT, FLOAT) TUPLES experts
    
    Compare the patent given by pat_num to each of the patents with an
    associated expert and compute similarity scores based on CPCs for 
    each. Return a list of experts and their associated scores sorted 
    from highest to lowest score. In the case where the cost function is
    being calculated, testing should be set to True so that the test set
    can be removed from the list of training patents.
    '''
    conn = psycopg2.connect(database='patents', user='postgres')
    cur = conn.cursor()
    
    cpcs_1 = get_cpc(test_pat, cur, table)
    
    query = 'SELECT pat_num FROM exp_cpcs GROUP BY pat_num;'
    cur.execute(query)
    training_patents = [pat[0] for pat in cur.fetchall()]
    
    if testing:
        training_patents.remove(test_pat)
    
    agg_scores = []
    for pat_num_2 in training_patents:
        scores = compute_scores(cpcs_1, pat_num_2, cur, params, 
                                table_2='exp_cpcs')
        agg_scores.append((pat_num_2, agg_func(scores)))
    
    agg_scores.sort(key=lambda x: x[1], reverse=True)
    
    experts = []
    for (patent, score) in agg_scores:
        query = 'SELECT record FROM experts WHERE pat_num = %s;'
        cur.execute(query, [patent])
        experts += [(int(expert[0]), score) for expert in cur.fetchall() if 
                    expert[0] not in [exp[0] for exp in experts]]
                                        
    return experts