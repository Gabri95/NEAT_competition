import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.racerLayer2 import RacerLayer2
import math

class OpponentsRacerLayer3(RacerLayer2):
    
    def __init__(self, model_path, threshold=20):
        super(OpponentsRacerLayer3, self).__init__(model_path)
        
        self.threshold = threshold
    
    def processInput(self, carstate: State):
        
        array = list()
        
        array.append(carstate.angle / 180.0)
        
        array.append(carstate.speed_x / 50.0)
        #array.append(carstate.speed_y / 40.0)

        array.append(carstate.distance_from_center)
        
        for idxs in [[0], [2], [4], [7, 9, 11], [14], [16], [18]]:
            d = min([carstate.distances_from_edge[j] for j in idxs])
            if math.fabs(carstate.distance_from_center) > 1 or d < 0:
                array.append(-1)
            elif d > 199.8:
                array.append(0)
            else:
                array.append(1 -d / 200.0)
                #array.append(np.exp(-(5 * d / 200.0)))
        
        

        #for idxs in [range(0, 9), range(9, 11), range(13, 15), range(16, 18), range(18, 20), range(21, 23), range(25, 27), range(27, 36)]:
        for idxs in [range(9, 11), range(13, 15), range(16, 18), range(18, 20), range(21, 23), range(25, 27)]:
            d = min([carstate.opponents[j] for j in idxs])
            if d > 199.8:
                array.append(0)
            else:
                #array.append(np.exp(-(3 * d / self.threshold) ** 1.3))
                #r = 10
                array.append(max(0, 1 - d/(self.threshold*1.5)))
                #array.append(1.0 / r * np.log(1 + np.exp(r * (1 - d / self.threshold))))
        
        return np.array(array)
    
