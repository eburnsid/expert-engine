'''
Simulated annealing to optimize parameters in Scott's model.

(C) 2014 Erin Burnside
'''

import psycopg2
import random
import math
import numpy as np
import basic_model

def sim_annealing (param_num, cost_func, agg_func, temp, cool):
    init_params = [random.random() for ii in range(param_num)]
    print init_params
    old_cost = cost_func(init_params, agg_func)
    
    while temp > 0.1:
        ii = random.randint(0, param_num - 1)
        step = random.uniform(-1, 1)
        print ii, step
        
        new_params = init_params[:]
        new_params[ii] += step
        if new_params[ii] > 1:
            new_params[ii] = 1
        elif new_params[ii] < 0:
            new_params[ii] = 0
        print new_params
            
        new_cost = cost_func(new_params, agg_func)
        prob = pow(math.e, (- old_cost - new_cost)/temp)
        print prob
        
        if (new_cost < old_cost or random.random() < prob):
            init_params = new_params
            old_cost = new_cost
            
        temp = temp * cool

    return init_params
    
    
if __name__ == "__main__":
    print sim_annealing (17, basic_model.cost_function, np.mean, 10000, 0.95)