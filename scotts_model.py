'''
Implements the initial model devised by Scott to compute similarity scores for
patents based on CPC codes. 

(C) 2014 Erin Burnside
'''

import psycopg2
import numpy as np
import basic_model


def scotts_model ():
    params = [10 for ii in range(17)]
    return basic_model.cost_function(params, max)
    

if __name__ == "__main__":
    scotts_model()