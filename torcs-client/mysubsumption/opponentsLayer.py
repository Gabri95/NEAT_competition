import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.racerLayer import RacerLayer
import math

class OpponentsLayer(RacerLayer):
    
    def __init__(self, model_path, threshold=20):
        super(OpponentsLayer, self).__init__(model_path)
        self.threshold = threshold

    def processInput(self, carstate: State):
    
        array = list()
    
        array.append(carstate.angle / 180.0)
    
        array.append(carstate.speed_x / 50.0)
        # array.append(carstate.speed_y / 40.0)
    
        array.append(carstate.distance_from_center)
    
        for idxs in [[0], [2], [4], [7, 9, 11], [14], [16], [18]]:
            d = min([carstate.distances_from_edge[j] for j in idxs])
            if math.fabs(carstate.distance_from_center) > 1 or d < 0:
                array.append(-1)
            else:
                array.append(d / 200.0)


        for idxs in [range(9, 11), range(13, 15), range(16, 18), range(18, 20), range(21, 23), range(25, 27)]:
            d = min([carstate.opponents[j] for j in idxs])
            if d < 0:
                array.append(-1)
            else:
                array.append(d / (self.threshold * 2))
        
        return np.array(array)
    
    
    def applicable(self, carstate: State):
        return min(carstate.opponents[9:27]) < self.threshold

    def step(self, carstate: State, command: Command):
    
        
    
        if carstate.gear <= 0:
            carstate.gear = 1
    
        input = self.processInput(carstate)
    
        if np.isnan(input).any():
            return False
    
        try:
            output = self.model.activate(input)
        
            for i in range(len(output)):
                if np.isnan(output[i]):
                    output[i] = 0.0
        
            print('Out = ' + str(output))
        
            accelerator = 0
            brake = 0
        
            if output[0] > 0:
                accelerator = output[0]
            else:
                brake = -1 * output[0]
        
            self.accelerate(accelerator, brake, carstate, command)
        
            if len(output) == 2:
                # use this if the steering is just one output
                self.steer(output[1], 0, carstate, command)
            else:
                # use this command if there are 2 steering outputs
                self.steer(output[1], output[2], carstate, command)
    
        except:
            print('Error!')
            raise
    
        return True


class OpponentsRacerLayer(OpponentsLayer):
    def __init__(self, model_path, threshold=20):
        super(OpponentsRacerLayer, self).__init__(model_path, threshold)
    
    def applicable(self, carstate: State):
        return True
