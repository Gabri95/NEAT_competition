import sys

sys.path.insert(0, '../')

from pytocl.car import State, Command, MPS_PER_KMH
from pytocl.controller import CompositeController, ProportionalController, \
    IntegrationController, DerivativeController
from mysubsumption.layer import Layer
import numpy as np
import math


class UnstuckLayer4(Layer):
    def __init__(self, ):
        super(UnstuckLayer4, self).__init__()
        
        self.stuck_count = 0
        self.instantiatePIDControllers()
        
        self.attempts = 0
        self.attempts_limit = 100
        
        self.last_applicable = False
        
        self.last_action = 0  # 1: forward, 2: backward
        self.time_threshold = 30
    
    def instantiatePIDControllers(self):
        self.steering_ctrl = CompositeController(
            ProportionalController(-0.5),
            IntegrationController(-0.1, integral_limit=1),
            DerivativeController(-1)
        )
        self.reverse_ctrl = CompositeController(
            ProportionalController(3.7),
            # IntegrationController(0.1, integral_limit=1.5),
            # DerivativeController(0.5)
        )
        
        self.forward_ctrl = CompositeController(
            ProportionalController(3.7),
            # IntegrationController(0.1, integral_limit=1.5),
            # DerivativeController(0.5)
        )
    
    def update(self, carstate: State):
        # min_dist = min(carstate.distances_from_edge)
        v = get_projected_speed(carstate.speed_x, carstate.speed_y, carstate.angle)
        if v < 5 or (carstate.speed_x < 0 and carstate.gear == -1):  # and min_dist < 4
            self.stuck_count += 1
        else:
            self.stuck_count = 0
    
    def applicable(self, carstate: State):
        
        self.update(carstate)
        min_dist = min(carstate.distances_from_edge)
        
        if math.fabs(carstate.distance_from_center) >  1.2:
        	result = True
        elif min_dist < 3 and math.fabs(carstate.distance_from_center) > 0.6:
            result = self.stuck_count > self.time_threshold
        else:
            result = self.stuck_count > 3 * self.time_threshold
        
        if not result:
            print(self.stuck_count / self.time_threshold, '% getting stuck')
        
        if not self.last_applicable and result:
            self.steering_ctrl.reset()
            self.forward_ctrl.reset()
            self.reverse_ctrl.reset()
            self.attempts = 0
        
        self.last_applicable = result
        return result
    
    def step(self, carstate: State, command: Command):
        
        if math.fabs(self.attempts) >= self.attempts_limit:
            self.attempts = 0  # -1 * self.attempts_limit
            self.last_action = 0
        
        position = np.sign(carstate.distance_from_center) * carstate.angle
        
        dist = carstate.distance_from_center
        
        threshold = 0.8
        slope = 3
        
        action = self.last_action
        
        if math.fabs(dist) <= threshold:
            target_angle = 0
        else:
            target_angle = np.arctan(slope * (dist - threshold * np.sign(dist))) * 180.0 / math.pi
        
        print('Target angle =', target_angle)
        
        if math.fabs(carstate.angle) > 165:
            if self.attempts >= 0:
                print('WRONG DIRECTION! GO FORWARD!', self.attempts)
                self.forward(carstate, 70, command)
            else:
                print('WRONG DIRECTION! GO BACKWARD!', self.attempts)
                self.reverse(carstate, -40, command)
            
            self.steer(carstate, 0, command)
        else:
            
            if carstate.speed_x >= 2 and math.fabs(carstate.angle) < 30 and math.fabs(dist) < 1.2:
                print("LET'S GO FORWARD!")
                self.forward(carstate, 100, command)
                self.steer(carstate, target_angle, command)
            elif (position >= -20 and self.attempts >= 0) or (
                            carstate.distances_from_edge[9] > 5 and math.fabs(carstate.angle) < 100):
                print('GO FORWARD!', self.attempts)
                self.forward(carstate, 80, command)
                self.steer(carstate, target_angle, command)
            else:
                print('GO BACKWARD!', self.attempts)
                self.reverse(carstate, -50, command)
                self.steer(carstate, -1 * target_angle, command)
            
            if math.fabs(carstate.speed_x) < 3:
                self.attempts += self.last_action
            
            if action * self.last_action < 0:
                self.stuck_count = 0
            
            if command.gear * carstate.gear < 0:
                self.steering_ctrl.reset()
            
            return True
    
    def forward(self, carstate, target_speed, command):
        
        self.last_action = 1
        command.gear = 1
        
        if not carstate.gear or carstate.gear <= 0:
            self.forward_ctrl.reset()
        
        if carstate.speed_x < -2:
            command.accelerator = 0
            command.brake = 1
        else:
            # compensate engine deceleration, but invisible to controller to
            # prevent braking:
            speed_error = 1.0025 * target_speed * MPS_PER_KMH - carstate.speed_x
            # get_projected_speed(carstate.speed_x, carstate.speed_y,carstate.angle)
            
            acceleration = self.forward_ctrl.control(
                speed_error,
                carstate.current_lap_time
            )
            
            # stabilize use of gas and brake:
            acceleration = math.pow(acceleration, 3)
            
            if acceleration > 0:
                # if abs(carstate.distance_from_center) >= 1:
                #     # off track, reduced grip:
                #     acceleration = min(0.4, acceleration)
                command.accelerator = min(acceleration, 1)
            else:
                command.brake = min(-acceleration, 1)
    
    def reverse(self, carstate, target_speed, command):
        
        if carstate.gear >= 0:
            self.reverse_ctrl.reset()
        
        command.gear = -1
        
        self.last_action = -1
        
        if carstate.speed_x > 2:
            command.accelerator = 0
            command.brake = 1
        else:
            # compensate engine deceleration, but invisible to controller to
            # prevent braking:
            speed_error = 1.0025 * target_speed * MPS_PER_KMH - carstate.speed_x
            
            acceleration = self.reverse_ctrl.control(
                speed_error,
                carstate.current_lap_time
            )
            
            # stabilize use of gas and brake:
            acceleration = math.pow(acceleration, 3)
            
            acceleration *= -1
            
            if acceleration > 0:
                # if abs(carstate.distance_from_center) >= 1:
                #     # off track, reduced grip:
                #     acceleration = min(0.4, acceleration)
                
                command.accelerator = min(acceleration, 1)
            
            else:
                command.brake = min(-acceleration, 1)
    
    def steer(self, carstate, target_angle, command):
        
        steering_error = target_angle - carstate.angle
        command.steering = np.sign(command.gear) * self.steering_ctrl.control(
            steering_error,
            carstate.current_lap_time
        )
        command.steering = max(-1, min(command.steering, 1))


def get_projected_speed(speed_x, speed_y, angle):
    velocity = get_velocity(speed_x, speed_y)
    return velocity[1] * math.cos(math.radians(angle - velocity[0]))


def get_velocity(speed_x, speed_y):
    return np.angle(speed_x + 1j * speed_y, True), np.sqrt(speed_x ** 2 + speed_y ** 2)



