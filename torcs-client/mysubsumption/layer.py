
import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
from abc import ABC, abstractmethod


class Layer(ABC):
    
    @abstractmethod
    def step(self, carstate : State, command : Command):
        pass
    
    @abstractmethod
    def applicable(self, carstate):
        pass

    def shift(self, carstate, command):
        command.gear = max(1, carstate.gear)
        if command.gear >= 0 and command.brake < 0.1 and carstate.rpm > 8000:
            command.gear = min(6, command.gear + 1)
    
        if carstate.rpm < 2500 and command.gear > 1:
            command.gear = command.gear - 1
    
        if not command.gear or carstate.gear <= 0:
            command.gear = carstate.gear or 1
    
    def steer(self, left, right, carstate : State, command : Command):
        command.steering = left - right

    def accelerate(self, acceleration, brake, carstate, command):
        
        if carstate.speed_x < -2 and carstate.gear <= 0:
            command.accelerator = 0
            command.brake = 1
            command.gear = 1
        else:
            command.accelerator = acceleration
            command.gear = carstate.gear
            command.brake = brake
    
            self.shift(carstate, command)