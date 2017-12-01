import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
from mysubsumption.racerLayer1 import RacerLayer1
import numpy as np
import math


class RacerLayer3(RacerLayer1):
    def __init__(self, model_path):
        super(RacerLayer3, self).__init__(model_path)


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
            else:
                array.append(1 - (d/200.0))
        
        return np.array(array)
