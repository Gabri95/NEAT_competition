
import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import pickle
import numpy as np
import math


from mysubsumption.layer import Layer

class RacerLayer1(Layer):
    def __init__(self, model_path):
        super(RacerLayer1, self).__init__()

        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
            self.model.reset()


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
                array.append(d / 200.0)
                
        #array.append(carstate.distance_from_center)
        return np.array(array)

    

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
                
                self.accelerate(output[0], output[1], carstate, command)

                if len(output) == 3:
                    # use this if the steering is just one output
                    self.steer(output[2], 0, carstate, command)
                else:
                    # use this command if there are 2 steering outputs
                    self.steer(output[2], output[3], carstate, command)
                    
        except:
            print('Error!')
            raise
        
        return True
    
    def applicable(self, carstate: State):
        return True
    
    



