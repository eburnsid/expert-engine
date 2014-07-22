'''
Simulated annealing optimization for parameters in Scott's model.

(C) 2014 Erin Burnside
'''

import psycopg2
import random
import math
import numpy as np
import basic_model


def shift_params (param_num, old_params):
'''
INPUT: INT param_num, LIST OF FLOATS old_params
OUTPUT: LIST OF FLOATS new_params

Randomly selects one of the parameters in list. Chooses an amount between -1 and 1 by
which to increment/decrement it. If it ends up outside the bounds of 0 and 1, the 
remaining amount is added to the other end (so amounts less than zero are subtracted 
from one to obtain the final value, while those greater than 1 are added to zero). Returns
the new parameters, which should be identical to the old ones except for the single changed
element.
'''
    ii = random.randint(0, param_num - 1)
    step = random.uniform(-1, 1)
    print ii, step
    
    new_params = old_params[:]
    new_params[ii] += step
    if new_params[ii] > 1:
        new_params[ii] = 0 + (new_params[ii] - 1)
    elif new_params[ii] < 0:
        new_params[ii] = 1 + new_params[ii]
    return new_params
    
      

def sim_annealing (param_num, cost_func, agg_func, temp, cool):
'''
INPUT: INT param_num, FUNCTION cost_func, FUNCTON agg_func, INT temp, FLOAT cool
OUTPUT: LIST OF FLOATS old_params

Creates a list of parameters between 0 and 1 of param_num length. Uses these in
the cost function with the given aggregation function to find a cost. Shifts the
parameters and recalculates cost. If the cost function has improved, the old parameters
are replaced with the new ones. If the cost function has gotten worse, the old parameters
are replaced with the new ones with probability "prob," which decreases with temperature. 
Temperature is decreased, and the parameters continue to be shifted until it reaches a
very low value (<0.1).
'''
    old_params = [random.random() for ii in range(param_num)]
    print old_params
    old_cost = cost_func(old_params, agg_func)
    
    while temp > 0.1:
        new_params = shift_params(param_num, old_params)
            
        new_cost = cost_func(new_params, agg_func)
        prob = pow(math.e, (- old_cost - new_cost)/temp)
        print prob
        
        if (new_cost < old_cost or random.random() < prob):
            old_params = new_params
            old_cost = new_cost
            
        temp = temp * cool

    return old_params
    
    
if __name__ == "__main__":
    print sim_annealing (17, basic_model.cost_function, np.mean, 10000, 0.95)