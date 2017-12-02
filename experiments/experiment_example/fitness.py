
import math
import numpy as np

tracks = {
'e-track-1': {'length': 3243.64, 'bestlaptime': 67, 'laps': 2}
}



def evaluate(results):
    
    fitness = 0
    
    for name, params in tracks.items():
    
        record = retrieveFromTimelimit(results[name], 0.9*params['bestlaptime']*params['laps'])
    
        if len(record) == 0:
            fitness += -1 + -0.5 -1 -50
        else:
            duration, distance, laps, distance_from_start, damage, avg_penalty, avg_speed, race_position, distFromLeader, avgDistFromLeader, penalty = record[:11]
            print('\t', name, ':')
            print('\t\tDistance = ', distance)
            print('\t\tDistance from Leader = ', distFromLeader)
            print('\t\tAverage Distance from Leader = ', avgDistFromLeader)
            print('\t\tRace Position = ', race_position)
            print('\t\tDuration = ', duration)
            print('\t\tDamage = ', damage)
            print('\t\tPenalty = ', penalty)
            print('\t\tAvgSpeed = ', avg_speed)

        fitness += distance + avg_speed - 3*penalty - 0.5*damage
        

    return fitness
    
    
    


def retrieveFromTimelimit(values, timelimit):
    last_result = []
    later_time = 0
    if timelimit is not None:
        for val in values:
            if later_time > timelimit or np.isnan(val).any():
                break
            elif val[0] > later_time and val[0] <= timelimit:
                last_result = val
                later_time = val[0]

        if len(last_result) > 0 and last_result[0] < timelimit:
            last_result[6] *= last_result[0] / timelimit
            last_result[0] = timelimit
    elif len(values) > 0:
        last_result = values[-1]
    else:
        last_result = []
    
    return last_result
    
