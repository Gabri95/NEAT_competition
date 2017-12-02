import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.opponentsLayer2 import OpponentsLayer2
import math

class OpponentsRacerLayer2(OpponentsLayer2):
    
    def __init__(self, model_path, threshold=20):
        super(OpponentsRacerLayer2, self).__init__(model_path, threshold)
    
    def applicable(self, carstate: State):
        return True





