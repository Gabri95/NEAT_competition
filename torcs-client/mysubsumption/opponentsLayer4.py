import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.racerLayer2 import RacerLayer2
import math

class OpponentsLayer4(RacerLayer2):
    
    def __init__(self, model_path, threshold=20):
        super(OpponentsLayer4, self).__init__(model_path)
        
        self.threshold = threshold
    
    def applicable(self, carstate: State):
        return min(carstate.opponents[7:29]) < self.threshold
    
    def processInput(self, carstate: State):
        
        array = list()
        
        array.append(carstate.angle / 180.0)
        
        array.append(carstate.speed_x / 50.0)
        #array.append(carstate.speed_y / 40.0)

        
        
        for idxs in [[0], [2], [4], [7, 9, 11], [14], [16], [18]]:
            d = min([carstate.distances_from_edge[j] for j in idxs])
            if math.fabs(carstate.distance_from_center) > 1 or d < 0:
                array.append(-1)
            else:
                array.append(d/200.0)

        array.append(carstate.distance_from_center)

        #for idxs in [range(0, 9), range(9, 11), range(13, 15), range(16, 18), range(18, 20), range(21, 23), range(25, 27), range(27, 36)]:
        #for idxs in [range(9, 11), range(13, 15), range(16, 18), range(18, 20), range(21, 23), range(25, 27)]:
        for idxs in [[10], [13], [16, 17], [18, 19], [22], [25]]:
            d = min([carstate.opponents[j] for j in idxs])
            if d > 199.8:
                array.append(0)
            else:
                array.append(max(0, 1 - d/(self.threshold*1.5)))
        
        return np.array(array)
    
    
