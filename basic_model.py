'''
Backbone of Scott's initial model using CPC codes to predict experts. Allows for user
input of parameters and aggregation function to allow for simulated annealing optimization.

(C) 2014 Erin Burnside
'''


import psycopg2
import random
import math
import numpy as np


def get_cpc (pat_num, cur, table = "cpcs"):
    query = 'SELECT * FROM %s WHERE pat_num = %s;' % (table, '%s')
    cur.execute(query, [pat_num])
    return [code[1] for code in cur.fetchall()]


def score_first_half (cpc_half_1, cpc_half_2, params):
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
    cpcs = sorted([cpc_sh_1, cpc_sh_2])
    
    query = "SELECT * FROM levels WHERE cpc LIKE '" + cpc_fh + "/%';"
    cur.execute(query)
    
    levels = [(cpc.split('/')[1], level) for (id, cpc, level) in cur.fetchall()]
    level_slice = [(cpc, level) for (cpc, level) in levels if (cpc >= cpcs[0]) and (cpc <= cpcs[1])]
    
    return compute_group_score(level_slice, params)


def compute_score (pat_1, pat_2, cur, params, table = "cpcs"):
    cpcs_1 = get_cpc(pat_1, cur, table)
    cpcs_2 = get_cpc(pat_2, cur, table)
    
    scores = []
    for cpc_1 in cpcs_1:
        cpc_spl_1 = cpc_1.split('/')
        for cpc_2 in cpcs_2:
            if cpc_1 == cpc_2:
                scores.append(sum(params[:-1]))
                continue
            cpc_spl_2 = cpc_2.split('/')
            score = 0
            score = score + score_first_half(cpc_spl_1[0], cpc_spl_2[0], params[:5])
            if score == sum(params[:5]):
                score = score + score_second_half(cpc_spl_1[0], cpc_spl_1[1], \
                            cpc_spl_2[1], params[5:], cur)
            
            scores.append(score)
            
    return scores


def predict_expert (pat_num, params, agg_func, table = "cpcs", testing = False):
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
    query = "SELECT pat_num FROM exp_cpcs GROUP BY pat_num;"
    cur.execute(query)
    if testing == True:
        training_patents = [pat[0] for pat in cur.fetchall()]
        training_patents.remove(pat_num)
    
    mean_scores = []
    for pat_num_2 in training_patents:
        mean_scores.append((pat_num_2, \
                            agg_func(compute_score(pat_num, pat_num_2, cur, params, table = table))))
    
    mean_scores.sort(key = lambda x: x[1], reverse = True)
    
    experts = []
    for (patent, score) in mean_scores[:10]:
        query = "SELECT record FROM experts WHERE pat_num = %s;"
        cur.execute(query, [patent])
        experts += [(int(expert[0]), score) for expert in cur.fetchall() if expert[0] \
                    not in [exp[0] for exp in experts]]                    
    return experts


def cost_function (params, agg_func):
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
    query = 'SELECT * FROM one_expert_pats AS oep \
                JOIN many_pat_experts AS mpe ON oep.index = mpe.index;'
    cur.execute(query)
    
    cost = 0
    tested = 0
    for star in cur.fetchall():
        tested += 1
        test_patent = star[1]
        print test_patent
        matches = predict_expert(test_patent, params, agg_func, table = "exp_cpcs", testing = True)
        if star[2] not in [match[0] for match in matches[:5]]:
            cost += 1
    
    print cost
    print '\n\n\n\n'
    return cost
