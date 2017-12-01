
def evaluate(values, timelimit):

    last_result = []
    later_time = 0
    if timelimit is not None:
        for val in values:
            if later_time > timelimit:
                break
            elif val[0] > later_time and val[0] <= timelimit:
                last_result = val
                later_time = val[0]

        if last_result[0] < timelimit:
            last_result[6] *= last_result[0] / timelimit
            last_result[0] = timelimit
    else:
        last_result = values[-1]
    
    duration, distance, laps, distance_from_start, damage, penalty, avg_speed, race_position, distFromLeader, avgDistFromLeader = last_result[:10]
    
    if timelimit is not None:
        avg_speed *= duration / timelimit
        duration = timelimit

    #if len(values) < 100 or laps < 0:
    #    fitness = -10500 - 100*(race_position -1) + distance -100*penalty - 0.1*damage
    #else:
    #    fitness = distFromLeader - 100*(race_position -1) - 100*penalty - 0.1*damage
    
    fitness = - 100*(race_position -1) + distance - 100*penalty - 0.5*damage

    return fitness
    
    
