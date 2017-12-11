
import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
from mysubsumption.layer import Layer


class SimpleLayer(Layer):
    
    
    def step(self, carstate : State, command : Command):

        command.accelerator = 1
        command.brake = 0
        command.gear = carstate.gear

        if command.gear >= 0 and carstate.rpm > 8000:
            command.gear = min(6, command.gear + 1)

        if carstate.rpm < 2500 and command.gear > 1:
            command.gear = command.gear - 1

        if not command.gear:
            command.gear = carstate.gear or 1


    def applicable(self, carstate):
        return True

    
