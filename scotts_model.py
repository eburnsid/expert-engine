import psycopg2


def get_cpc (pat_num, table = "cpcs", cur):
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
    
    compute_group_score(level_slice)


if __name__ == "__main__":
    pass