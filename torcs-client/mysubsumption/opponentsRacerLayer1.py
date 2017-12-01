import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.opponentsLayer1 import OpponentsLayer1
import math

class OpponentsRacerLayer1(OpponentsLayer1):
    
    def __init__(self, model_path, threshold=20):
        super(OpponentsRacerLayer1, self).__init__(model_path, threshold)
    
    def applicable(self, carstate: State):
        return True





