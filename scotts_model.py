import psycopg2


def get_cpc (pat_num, cur, table = "cpcs"):
    query = 'SELECT * FROM %s WHERE pat_num = %s;' % (table, '%s')
    cur.execute(query, [pat_num])
    return [code[1] for code in cur.fetchall()]


def score_first_half (cpc_half_1, cpc_half_2):
    score = 0
    
    for chs in zip(cpc_half_1[0:4], cpc_half_2[0:4]):
        if chs[0] == chs[1]:
            score += 10
        else:
            break
            
    if score == 40 and cpc_half_1[4:] == cpc_half_2[4:]:
        return score + 30
    elif score == 40:
        return score + 20
    return score
    

def compute_group_score (level_slice):
    cpc_level = sorted([level_slice[0][1],level_slice[-1][1]])
    
    if cpc_level[0] == 0:
        return 10
    
    elif cpc_level[0] == cpc_level[1] and cpc_level[0] == 1:
        return 0
    
    elif cpc_level[0] == cpc_level[1]:
        for ii in range(1, cpc_level[0]):
            if ii in [code[1] for code in level_slice[1:-1]]:
                return 10 * (ii - 1)
        return 10 * (cpc_level[0] - 1)
    
    else:        
        for ii in range(1, cpc_level[0] + 1):
            if ii in [code[1] for code in level_slice[1:-1]]:
                return 10 * (ii - 1)
        return 10 * cpc_level[0]
        

def score_second_half (cpc_fh, cpc_sh_1, cpc_sh_2, cur):
    cpcs = sorted([cpc_sh_1, cpc_sh_2])
    
    query = "SELECT * FROM levels WHERE cpc LIKE '" + cpc_fh + "/%';"
    cur.execute(query)
    
    levels = [(cpc.split('/')[1], level) for (id, cpc, level) in cur.fetchall()]
    level_slice = [(cpc, level) for (cpc, level) in levels if (cpc >= cpcs[0]) and (cpc <= cpcs[1])]
    
    return compute_group_score(level_slice)


def compute_score (pat_1, pat_2, cur, table = "cpcs"):
    cpcs_1 = get_cpc(pat_1, cur, table)
    cpcs_2 = get_cpc(pat_2, cur, table)
    
    scores = []
    for cpc_1 in cpcs_1:
        cpc_spl_1 = cpc_1.split('/')
        for cpc_2 in cpcs_2:
            if cpc_1 == cpc_2:
                scores.append(200)
                continue
            cpc_spl_2 = cpc_2.split('/')
            score = 0
            score += score_first_half(cpc_spl_1[0], cpc_spl_2[0])
            if score == 70:
                score += score_second_half(cpc_spl_1[0], cpc_spl_1[1], cpc_spl_2[1], cur)
            
            scores.append(score)
            
    return scores


def predict_expert (pat_num, table = "cpcs"):
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
    query = "SELECT pat_num FROM exp_cpcs GROUP BY pat_num;"
    cur.execute(query)
    
    max_scores = []
    for pat_num_2 in cur.fetchall():
        max_scores.append((pat_num_2, max(compute_score(pat_num, pat_num_2, cur, table = table))))
    
    max_scores.sort(key = lambda x: x[1], reverse = True)
    print max_scores
    
    experts = []
    for (patent, score) in max_scores[:10]:
        print patent
        query = "SELECT record FROM experts WHERE pat_num = %s;"
        cur.execute(query, [patent])
        experts += [(int(expert[0]), score) for expert in cur.fetchall() if expert[0] \
                    not in [exp[0] for exp in experts]]                    
    return experts

if __name__ == "__main__":
    print predict_expert (5012813, table = "exp_cpcs")