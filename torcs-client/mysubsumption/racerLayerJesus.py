import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
from mysubsumption.layer import Layer
import pickle
import numpy as np
import math

class RacerLayerJesus(Layer):
    def __init__(self, model_path):
        super(RacerLayerJesus, self).__init__()

        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
            self.model.reset()


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
                array.append(d / 200.0)
    
        array.append(carstate.distance_from_center)
        
        return np.array(array)

    

    def step(self, carstate: State, command: Command):
        
        
        
        # if carstate.gear <= 0:
        #     carstate.gear = 1
        #
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
                    brake = -1*output[0]

                if max(carstate.distances_from_edge[8:11]) > 100 and carstate.gear >= 1:
                    print('  ---------  JESUS TAKES THE WHEEL  ---------')
                    
                    # if carstate.distances_from_edge[9] < 150:
                    #     dist = sum(carstate.distances_from_edge[8:11]) / 3.0
                    # else:
                    #     dist = carstate.distances_from_edge[9]

                    dist = max(carstate.distances_from_edge[8:11])
                    
                    accelerator = max(command.accelerator, min(1, dist / 150.0) ** 2)
                    brake = 0
                

                self.accelerate(accelerator, brake, carstate, command)

                print('Accelerator =', command.accelerator)
                
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
    
    def applicable(self, carstate: State):
        return True
    
    



