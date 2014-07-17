import psycopg2


def get_cpc (pat_num, table = "cpcs"):
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
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


if __name__ == "__main__":
    pass