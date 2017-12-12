
import math
import numpy as np

def evaluate(results):
    
    fitness = 0
    
    
    record = retrieveFromTimelimit(results['configuration'], 110)

    if len(record) == 0:
        fitness = -1000
    else:
        duration, distance, laps, distance_from_start, damage, avg_penalty, avg_speed, race_position, distFromLeader, avgDistFromLeader, penalty = record[:11]
        print('\t\tDistance = ', distance)
        print('\t\tDistance from Leader = ', distFromLeader)
        print('\t\tAverage Distance from Leader = ', avgDistFromLeader)
        print('\t\tRace Position = ', race_position)
        print('\t\tDuration = ', duration)
        print('\t\tDamage = ', damage)
        print('\t\tPenalty = ', penalty)
        print('\t\tAvgSpeed = ', avg_speed)

        fitness = distance + avg_speed +10*avg_speed - 20*penalty 
        

    return fitness
    
    
    
def retrieveFromTimelimit(values, timelimit):
    last_result = []
    later_time = 0
    
    if values is None:
        return []
    
    for val in values:
        if np.isnan(val).any() or (timelimit is not None and val[0] > timelimit):
            break
        elif val[0] > later_time:
            last_result = val
            later_time = val[0]

    if timelimit is not None and len(last_result) > 0 and last_result[0] < timelimit:
        last_result[6] *= last_result[0] / timelimit
        last_result[0] = timelimit

    
    return last_result
    