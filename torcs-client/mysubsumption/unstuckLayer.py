import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
from mysubsumption.layer import Layer
import numpy as np
import math

class UnstuckLayer(Layer):
    def __init__(self, ):
        super(UnstuckLayer, self).__init__()
        
        self.stuck_count = 0

    def applicable(self, carstate: State):
        
        min_dist = min(carstate.distances_from_edge)
        if carstate.speed_x < 2 \
                and (math.fabs(carstate.distance_from_center) >= 0.93 or (min_dist < 2.5 and min_dist >= 0)) \
                and math.fabs(carstate.angle) > 15 \
                and carstate.angle * carstate.distance_from_center < 0:
            self.stuck_count += 1
            print(self.stuck_count, '% getting stuck')
        else:
            self.stuck_count = 0
        #if self.stuck_count < 100 or math.fabs(carstate.angle) < 30 or carstate.angle * carstate.distance_from_center >= 0:
    
        return self.stuck_count > 100

    def step(self, carstate: State, command: Command):
        command.accelerator = min(1, (carstate.distance_from_center - 0.2) ** 4) #2 - min(carstate.distances_from_edge)
        command.gear = -1
        command.brake = 0.0
        command.clutch = 0.0
        command.steering = -1 * carstate.angle * np.pi / (180.0 * 0.785398) *1.5
        
        return True
    
    
    
    



