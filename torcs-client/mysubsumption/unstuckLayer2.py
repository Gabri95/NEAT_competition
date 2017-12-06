import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
from mysubsumption.layer import Layer
import numpy as np
import math

class UnstuckLayer2(Layer):
    def __init__(self, ):
        super(UnstuckLayer2, self).__init__()
        
        self.front_stuck = 0
        self.back_stuck = 0


    def updateFrontStuck(self, carstate: State):
        min_dist = min(carstate.distances_from_edge)
        if carstate.speed_x < 3 \
                and (math.fabs(carstate.distance_from_center) >= 0.93 or min_dist < 3) \
                and math.fabs(carstate.angle) > 15 \
                and carstate.angle * carstate.distance_from_center < 0:
            self.front_stuck += 1
            print(self.front_stuck, '% getting stuck')
        elif carstate.speed_x < 3 and carstate.rpm > 5000 and carstate.gear >= 0:
            self.front_stuck += 1
            print(self.front_stuck, '% getting stuck')
        else:
            self.front_stuck = 0

    
    def updateBackStuck(self, carstate: State):
        min_dist = min(carstate.distances_from_edge)
        if carstate.speed_x < 8 \
                and carstate.angle * np.sign(carstate.distance_from_center) >= -15:
                #and math.fabs(carstate.angle) < 90 \
            self.back_stuck += 1
            print(self.back_stuck, '% getting stuck')
        else:
            self.back_stuck = 0


    
    def applicable(self, carstate: State):
    
        self.updateBackStuck(carstate)
        self.updateFrontStuck(carstate)
        #if self.stuck_count < 100 or math.fabs(carstate.angle) < 30 or carstate.angle * carstate.distance_from_center >= 0:
    
        return self.front_stuck > 15 or self.back_stuck > 10

    def step(self, carstate: State, command: Command):
        
        if self.front_stuck > 30:
            d = min(carstate.distances_from_edge)
            command.accelerator = max(0, min(1, 1.3 - 0.7*d))
            command.gear = -1
            command.brake = 0.0
            command.clutch = 0.0
            command.steering = -1 * carstate.angle * np.pi / (180.0 * 0.785398)
        else:
            command.accelerator = 1
            command.gear = 1 if carstate.gear <= 0 else carstate.gear
            command.brake = 0.0
            command.clutch = 0.0
            command.steering = carstate.angle * np.pi / (180.0 * 0.785398)
            command.steering -= 0.35*np.sign(carstate.distance_from_center)*min(1.5, math.fabs(carstate.distance_from_center))
            
        
        return True
    
    
    
    



