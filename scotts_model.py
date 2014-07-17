import psycopg2

def get_cpc (pat_num, table = "cpcs"):
    conn = psycopg2.connect(database = 'patents', user = 'postgres')
    cur = conn.cursor()
    
    query = 'SELECT * FROM %s WHERE pat_num = %s;' % (table, '%s')
    cur.execute(query, [pat_num])
    return [code[1] for code in cur.fetchall()]
