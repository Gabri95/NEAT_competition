import sys
sys.path.insert(0, '../')

from pytocl.car import State, Command
import numpy as np
from mysubsumption.opponentsRacerLayer6 import OpponentsRacerLayer6

class OpponentsLayer6(OpponentsRacerLayer6):
    
    def __init__(self, model_path, threshold=30):
        super(OpponentsLayer6, self).__init__(model_path, threshold)
    
    def applicable(self, carstate: State):
        return min(carstate.opponents[9:27]) < self.threshold
    
