
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
    
    
    def steer(self, left, right, carstate : State, command : Command):
        command.steering = left - right

    def accelerate(self, acceleration, brake, carstate, command):
        command.accelerator = acceleration
        command.gear = carstate.gear
        command.brake = brake