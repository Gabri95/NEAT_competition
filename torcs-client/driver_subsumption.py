from pytocl.driver import Driver
from pytocl.car import State, Command
import math
import time as tm
import sys
import os.path
import numpy as np


from mysubsumption.racerLayer1 import RacerLayer1
from mysubsumption.racerLayer2 import RacerLayer2
from mysubsumption.racerLayer3 import RacerLayer3
from mysubsumption.racerLayer4 import RacerLayer4
from mysubsumption.unstuckLayer import UnstuckLayer
from mysubsumption.opponentsLayer1 import OpponentsLayer1
from mysubsumption.opponentsRacerLayer1 import OpponentsRacerLayer1
from mysubsumption.opponentsLayer2 import OpponentsLayer2
from mysubsumption.opponentsRacerLayer2 import OpponentsRacerLayer2
from mysubsumption.opponentsRacerLayer3 import OpponentsRacerLayer3
from mysubsumption.opponentsRacerLayer4 import OpponentsRacerLayer4
from mysubsumption.opponentsRacerLayer5 import OpponentsRacerLayer5


from mysubsumption.unstuckLayer2 import UnstuckLayer2

from mysubsumption.racerLayer import RacerLayer
from mysubsumption.opponentsLayer import OpponentsLayer
from mysubsumption.opponentsLayer import OpponentsRacerLayer

from configparser import ConfigParser

sys.path.insert(0, '../')

layers_type = {
    'RacerLayer1' : RacerLayer1,
    'RacerLayer2' : RacerLayer2,
    'RacerLayer3' : RacerLayer3,
    'RacerLayer4' : RacerLayer4,
    'UnstuckLayer' :UnstuckLayer,
    'UnstuckLayer2' :UnstuckLayer2,
    'OpponentsLayer1' : OpponentsLayer1,
    'OpponentsRacerLayer1' : OpponentsRacerLayer1,
    'OpponentsLayer2' : OpponentsLayer2,
    'OpponentsRacerLayer2' : OpponentsRacerLayer2,
    'OpponentsRacerLayer3' : OpponentsRacerLayer3,
    'OpponentsRacerLayer4' : OpponentsRacerLayer4,
    'OpponentsRacerLayer' : OpponentsRacerLayer,
    'OpponentsLayer' : OpponentsLayer,
    'RacerLayer' : RacerLayer,
    'OpponentsRacerLayer5' : OpponentsRacerLayer5
}



class SubsumptionDriver(Driver):
    def __init__(self, driver_config, out_file=None):
        super(SubsumptionDriver, self).__init__(logdata=False)

        self.out_file = out_file
        
        self.layers = parseConfiguration(driver_config)
        self.size = len(self.layers)
        
        if self.size == 0:
            raise Exception('Error! No layer set!')
        

        self.last_lap_time = 0
        self.curr_time = -10.0
        self.time = 0.0
        self.distance = -1.0
        self.distance_from_start = 0.0
        self.laps = -1
        self.damage = 0
        self.offroad_penalty = 0
        self.iterations_count = 0
        self.avg_speed = 0
        self.z = 0

        self.stopped = False
        self.projected_speed = 0

        self.race_position = -1
        self.avgDistFromLeader = 0
        self.distFromLeader = 0

        self.results = []

        print('Driver initialization completed')
        

    def drive(self, carstate: State) -> Command:
        
        print('Drive')
        
        self.print_log(carstate)
        
        self.update(carstate)
        
        try:
            
            command = Command()
            
            l = self.size -1
            
            while not self.layers[l].applicable(carstate) and l >= 0:
                l -= 1
            
            if l < 0:
                print('Error!!! No layer applicable!!!!!')
            else:
                print('Using layer', l)
                self.layers[l].step(carstate, command)
                
                #while l >= 0:
                #   self.layers[l].step(carstate, Command())
                #   l -= 1
                
                
        except:
            print('Error!')
            self.saveResults()
            raise
        
        if self.data_logger:
            self.data_logger.log(carstate, command)
        
        return command


    def saveResults(self):
        if self.out_file is not None:
            with open(self.out_file, 'w') as f:
                for r in self.results:
                    # f.write("{}: {}, {}".format(self.name, self.distance, self.curr_time))
                    f.write(", ".join([str(v) for v in r]) + '\n')
                f.close()

    def on_shutdown(self):
        """
        Server requested driver shutdown.

        Optionally implement this event handler to clean up or write data
        before the application is stopped.
        """
        print('Client ShutDown')

        self.append_current_results()

        self.saveResults()

        if self.data_logger:
            self.data_logger.close()
            self.data_logger = None

    def update(self, carstate):

        self.projected_speed = get_projected_speed(carstate.speed_x, carstate.speed_y, carstate.angle)

        self.avg_speed += self.projected_speed
        self.distance = carstate.distance_raced

        if self.laps >= 0 and self.curr_time > carstate.current_lap_time:
            self.time += carstate.last_lap_time
            self.laps += 1
        elif self.laps < 0 and self.distance_from_start - carstate.distance_from_start > 400:
            self.time += carstate.last_lap_time
            self.laps += 1

        self.last_lap_time = carstate.last_lap_time
        self.distance_from_start = carstate.distance_from_start
        self.curr_time = carstate.current_lap_time
        self.damage = carstate.damage
        self.z = carstate.z
        self.race_position = carstate.race_position

        self.offroad_penalty += (max(0, math.fabs(carstate.distance_from_center) - 0.985)) ** 2

        self.iterations_count += 1

        self.distFromLeader = carstate.distFromLeader
        self.avgDistFromLeader += carstate.distFromLeader

        if self.iterations_count % 100 == 0:
            self.append_current_results()

    def append_current_results(self):
        self.results.append([
            self.time + self.curr_time,
            self.distance,
            self.laps,
            self.distance_from_start,
            self.damage,
            math.sqrt(self.offroad_penalty / self.iterations_count) if self.iterations_count > 0 else 0,
            self.avg_speed / self.iterations_count if self.iterations_count > 0 else 0,
            self.race_position,
            self.distFromLeader,
            self.avgDistFromLeader / self.iterations_count if self.iterations_count > 0 else 0,
            math.sqrt(self.offroad_penalty)
        ])

    def print_log(self, carstate):
        print(tm.ctime())
        print('iter = ', self.iterations_count)
        # print('wheel velocities =', carstate.wheel_velocities)
        if self.iterations_count > 0:
            print('estimated distance raced = ',
                  (self.time + self.curr_time) * self.avg_speed / self.iterations_count)
        print('distance raced = ', carstate.distance_raced)
        print('min distances = ', min(carstate.distances_from_edge))
        print('distance center = ', carstate.distance_from_center)

        print('projected speed =', self.projected_speed)
        print('vx = ', carstate.speed_x)
        print('vy = ', carstate.speed_y)
        print('angle = ', carstate.angle)

        print('AVG demage per meter', self.damage / math.fabs(self.distance) if self.distance != 0.0 else 0)
        # print('self curr_time', self.curr_time)
        # print('self dist from start', self.distance_from_start)
        # print('dist from start', carstate.distance_from_start)
        #
        # print('current lap time: ', carstate.current_lap_time)
        # print('last lap time: ', carstate.last_lap_time)
        # print('self laps: ', self.laps)
        # print('self time', self.time)
        print('damage = ', carstate.damage)
        # print('rpm = ', carstate.rpm)
        # print('gear = ', carstate.gear)
        print('offroad penalty = ', self.offroad_penalty)
        print('z = ', carstate.z)

        print('Distance from leader = ', carstate.distFromLeader)
        print('Laps = ', self.laps)



def get_projected_speed(speed_x, speed_y, angle):
    velocity = get_velocity(speed_x, speed_y)
    return velocity[1] * math.cos(math.radians(angle - velocity[0]))


def get_velocity(speed_x, speed_y):
    return np.angle(speed_x + 1j * speed_y, True), np.sqrt(speed_x ** 2 + speed_y ** 2)



def parseConfiguration(parameters_file):
    
    layers = []
    
    with open(parameters_file) as f:
        parameters = ConfigParser()
        parameters.read_file(f)
        
        l = 1
        
        while parameters.has_section('Layer' + str(l)):
            print('Parsing layer'+str(l))
            
            layer_name = parameters.get('Layer' + str(l), 'type')
            
            if layer_name in layers_type:
                if parameters.has_option('Layer' + str(l), 'model_path'):
                    
                    path = parameters.get('Layer' + str(l), 'model_path')
                    
                    #the path in the configuration file are relative to the configuration file
                    path = os.path.join(os.path.dirname(parameters_file), path)
                    
                    layer = layers_type[layer_name](path)
                else:
                    layer = layers_type[layer_name]()
                
                layers.append(layer)
            else:
                message = "Error! Layer {} in section {} doesn't exists!".format(layer_name, 'layer' + str(l))
                print(message)
                raise Exception(message)
            
            l += 1
        
        print(l -1, 'layers set in the configuration file')
    
    return layers