import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.racerLayer2 import RacerLayer2
import math

class OpponentsLayer2(RacerLayer2):
    
    def __init__(self, model_path, threshold=20):
        super(OpponentsLayer2, self).__init__(model_path)
        
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
                #array.append(1 -d / 200.0)
                array.append(np.exp(-(5 * d / 200.0)))
        
        

        for idxs in [range(0, 9), range(9, 11), range(13, 15), [16], [17], [18], [19], range(21, 23), range(25, 27), range(27, 36)]:
            d = min([carstate.opponents[j] for j in idxs])
            if d > 199.8:
                array.append(0)
            else:
                array.append(np.exp(-(3*d / self.threshold)**1.3))
        
        return np.array(array)
    
    
    def applicable(self, carstate: State):
        return min(carstate.opponents) < self.threshold

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
            
            if carstate.distances_from_edge[9] > 100:
                accelerator = 1
            elif output[0] > 0:
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


