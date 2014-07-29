'''
Simulated annealing optimization for parameters in Scott's model.

(C) 2014 Erin Burnside
'''

import psycopg2
import random
import math
import numpy as np
import cost_function
import basic_model


def shift_params (param_num, old_params):
    '''
    INPUT: INT param_num, LIST OF FLOATS old_params
    OUTPUT: LIST OF FLOATS new_params

    Randomly selects one of the parameters in list. Chooses an amount 
    between -0.1 and 0.1 by which to increment/decrement it. If it ends 
    up outside the bounds of 0 and 1, the remaining amount is added to 
    the other end (so amounts less than zero are subtracted from one to 
    obtain the final value, while those greater than 1 are added to 
    zero). Returns the new parameters, which should be identical to the 
    old ones except for the single changed element.
    '''
    ii = random.randint(0, param_num - 1)
    step = random.uniform(-0.1, 0.1)
    print ii, step
    
    new_params = old_params[:]
    new_params[ii] += step
    if new_params[ii] > 1:
        new_params[ii] = (new_params[ii] - 1)
    elif new_params[ii] < 0:
        new_params[ii] = 1 + new_params[ii]
    return new_params
    
      

def sim_annealing (param_num, cost_func, agg_func, temp, cool, model, 
                   old_params=[]):
    '''
    INPUT: INT param_num, FUNCTION cost_func, FUNCTON agg_func, 
        INT temp, FLOAT cool
    OUTPUT: LIST OF FLOATS old_params

    Creates a list of parameters between 0 and 1 of param_num length. 
    Uses these in the cost function with the given aggregation function 
    to find a cost. Shifts the parameters and recalculates cost. If the 
    cost function has improved, the old parameters are replaced with the 
    new ones. If the cost function has gotten worse, the old parameters 
    are replaced with the new ones with probability "prob," which 
    decreases with temperature. Temperature is decreased, and the 
    parameters continue to be shifted until temperature reaches a very 
    low value (<0.1).
    '''
    if old_params == []:
        old_params = [random.random() for ii in range(param_num)]
        print old_params
        print '\n\n'
        
    old_cost = cost_func(old_params, agg_func, model)
    
    while temp > 0.1:
        new_params = shift_params(param_num, old_params)
        print new_params
            
        new_cost = cost_func(new_params, agg_func, model)
        prob = pow(math.e, (-old_cost-new_cost) / temp)
        print prob
        
        if (new_cost < old_cost or random.random() < prob):
            old_params = new_params
            old_cost = new_cost
        
        print old_params
        print '\n\n'    
        temp = temp * cool

    return old_params
    
    
if __name__ == "__main__":
    print sim_annealing (17, cost_function.cost_function, np.mean, 10000, 
                         0.95, basic_model.predict_expert)
    
    
'''
Score: 1239
[0.40206028445304975, 0.1294731357957219, 0.2321915994106558, 
 0.9734734375019051, 0.3488640291388797, 0.33, 0.3986012093333169, 
 0.33, 0.3249364912440468, 0.33, 0.33, 0.3306967037958066, 0.33, 0.33, 
 0.33, 0.33, 0.33]
[0.40206028445304975, 0.1294731357957219, 0.2321915994106558, 
 0.9734734375019051, 0.3488640291388797, 0.33, 0.3986012093333169, 0.33, 
 0.3249364912440468, 0.3582610964974473, 0.33, 0.3306967037958066, 0.33, 
 0.33, 0.33, 0.33, 0.33]
[0.40206028445304975, 0.1294731357957219, 0.2321915994106558, 
 0.9734734375019051, 0.3488640291388797, 0.33, 0.3986012093333169, 0.33, 
 0.3249364912440468, 0.33, 0.33, 0.3306967037958066, 0.33, 
 0.2559817890527733, 0.33, 0.33, 0.33]
'''