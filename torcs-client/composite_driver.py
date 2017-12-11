from pytocl.driver import Driver
from pytocl.car import State, Command
import math
import time as tm
import sys
import os.path
import numpy as np
import pickle

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
from mysubsumption.opponentsRacerLayer6 import OpponentsRacerLayer6
from mysubsumption.opponentsLayer4 import OpponentsLayer4
from mysubsumption.opponentsLayer5 import OpponentsLayer5


from mysubsumption.unstuckLayer2 import UnstuckLayer2
from mysubsumption.unstuckLayer3 import UnstuckLayer3


from mysubsumption.simpleLayer import SimpleLayer

from mysubsumption.racerLayer import RacerLayer
from mysubsumption.opponentsLayer import OpponentsLayer
from mysubsumption.opponentsLayer import OpponentsRacerLayer



from mysubsumption.racerLayerJesus import RacerLayerJesus
from mysubsumption.racerLayerJesus2 import RacerLayerJesus2
from mysubsumption.racerLayerJesus3 import RacerLayerJesus3

from configparser import ConfigParser

sys.path.insert(0, '../')

layers_type = {
    'RacerLayer1' : RacerLayer1,
    'RacerLayer2' : RacerLayer2,
    'RacerLayer3' : RacerLayer3,
    'RacerLayer4' : RacerLayer4,
    'UnstuckLayer' :UnstuckLayer,
    'UnstuckLayer2' :UnstuckLayer2,
    'UnstuckLayer3' :UnstuckLayer3,
    'OpponentsLayer1' : OpponentsLayer1,
    'OpponentsRacerLayer1' : OpponentsRacerLayer1,
    'OpponentsLayer2' : OpponentsLayer2,
    'OpponentsRacerLayer2' : OpponentsRacerLayer2,
    'OpponentsRacerLayer3' : OpponentsRacerLayer3,
    'OpponentsRacerLayer4' : OpponentsRacerLayer4,
    'OpponentsRacerLayer' : OpponentsRacerLayer,
    'OpponentsLayer' : OpponentsLayer,
    'RacerLayer' : RacerLayer,
    'OpponentsRacerLayer5' : OpponentsRacerLayer5,
    'OpponentsRacerLayer6' : OpponentsRacerLayer6,
    'RacerLayerJesus' : RacerLayerJesus,
    'RacerLayerJesus3' : RacerLayerJesus3,
    'RacerLayerJesus2': RacerLayerJesus2,
    'SimpleLayer' : SimpleLayer,
    'OpponentsLayer4' : OpponentsLayer4,
    'OpponentsLayer5' : OpponentsLayer5
}


class CompositeDriver():
    def __init__(self, driver_config, out_file=None):

        self.out_file = out_file
        
        self.toplayers, self.layers, self.oracle = parseConfiguration(driver_config)
        
        
        if self.oracle is None:
            raise Exception('Error! No oracle model set')
        for i, l in enumerate(self.layers):
            if len(l) == 0:
                raise Exception('Error! No layers set in model' + str(i+1)+ '!')

        self.distance_from_center = 0
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

    @property
    def range_finder_angles(self):
        """Iterable of 19 fixed range finder directions [deg].

        The values are used once at startup of the client to set the directions
        of range finders. During regular execution, a 19-valued vector of track
        distances in these directions is returned in ``state.State.tracks``.
        """
        return -90, -75, -60, -45, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, \
               30, 45, 60, 75, 90

    
    def buildFeatures(self, carstate):
    
        array = list()
    
        array.append(carstate.angle / 180.0)
    
        array.append(carstate.speed_x / 50.0)

        array.append(carstate.distance_from_center)

        array.append(self.avg_speed / self.iterations_count if self.iterations_count > 0 else 0)
        array.append(carstate.race_position/10.0)
        
        for idxs in [[0], [3], [7], [9], [11], [13], [18]]:
            d = min([carstate.distances_from_edge[j] for j in idxs])
            if math.fabs(carstate.distance_from_center) > 1 or d < 0:
                array.append(-1)
            else:
                array.append(d / 200.0)
        
        for idxs in [range(9, 16), range(16, 20), range(20, 27)]:
            d = min([carstate.opponents[j] for j in idxs])
            array.append(d/200.0)
    
        return np.array(array)

    
    
    def runStack(self, carstate: State, command: Command, stack, stackname):
        l = len(stack) - 1
    
        while l >= 0 and not stack[l].applicable(carstate):
            l -= 1
    
        if l >= 0:
            print(stackname + ': USING LAYER', l)
            stack[l].step(carstate, command)
            return True
        else:
            return False
    
    def runModel(self, carstate: State) -> Command:
    
        top_command = Command()
        
        if self.runStack(carstate, top_command, self.toplayers, 'TopLayers'):
            return top_command
        
        else:
            commands = []
            
            for i, model in enumerate(self.layers):
                command = Command()
                
                if not self.runStack(carstate, command, model, 'model' + str(i+1)):
                    print('Error!!! No layer applicable in model{}!!!!!'.format(i+1))
                    
                commands.append(command)
                
            
            weight = self.oracle.activate(self.buildFeatures(carstate))
            #weight = sigmoid(weight)
            
            weights = [weight[0], 1.0 - weight[0]]
            
            
            
            print('ORACLE:', weights[0])
            
            N = 50
            s = ''
            for i in range(N):
                if i < int(weights[0]*N):
                    s+='0'
                else:
                    s+='1'
            print(s)
            
            command = Command()
            for i, w in enumerate(weight):
                command.accelerator = w * commands[i].accelerator * np.sign(commands[i].gear)
                command.brake = w * commands[i].brake
                command.steering = w * commands[i].steering
            
            self.shift(carstate, command)
            
            return command

    def shift(self, carstate, command):
        command.gear = max(1, carstate.gear)
        if command.gear >= 0 and command.brake < 0.1 and carstate.rpm > 8000:
            command.gear = min(6, command.gear + 1)
    
        if carstate.rpm < 2500 and command.gear > 1:
            command.gear = command.gear - 1
    
        if not command.gear or carstate.gear <= 0:
            command.gear = carstate.gear or 1
    
    def drive(self, carstate: State) -> Command:

        print('Drive')

        self.print_log(carstate)

        self.update(carstate)

        try:
            command = self.runModel(carstate)
        except:
            print('Error!')
            self.saveResults()
            raise

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
        # if self.iterations_count > 0:
        #     print('estimated distance raced = ',
        #           (self.time + self.curr_time) * self.avg_speed / self.iterations_count)
        #print('distance raced = ', carstate.distance_raced)
        print('min distances = ', min(carstate.distances_from_edge))
        print('distance center = ', carstate.distance_from_center)

        print('projected speed =', self.projected_speed)
        print('vx = ', carstate.speed_x)
        #print('vy = ', carstate.speed_y)
        print('angle = ', carstate.angle)

        #print('AVG demage per meter', self.damage / math.fabs(self.distance) if self.distance != 0.0 else 0)
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
        #print('z = ', carstate.z)

        print('Distance from leader = ', carstate.distFromLeader)
        #print('Laps = ', self.laps)



def get_projected_speed(speed_x, speed_y, angle):
    velocity = get_velocity(speed_x, speed_y)
    return velocity[1] * math.cos(math.radians(angle - velocity[0]))


def get_velocity(speed_x, speed_y):
    return np.angle(speed_x + 1j * speed_y, True), np.sqrt(speed_x ** 2 + speed_y ** 2)



def getLayer(parameters, model_section, directory):
    
    layer_name = parameters.get(model_section, 'type')
    
    if layer_name in layers_type:
        if parameters.has_option(model_section, 'model_path'):
            path = parameters.get(model_section, 'model_path')
            # the path in the configuration file are relative to the configuration file
            path = os.path.join(directory, path)
            layer = layers_type[layer_name](path)
        else:
            layer = layers_type[layer_name]()
        
        return layer
    else:
        message = "Error! Layer {} doesn't exists!".format(layer_name)
        print(message)
        raise Exception(message)




def parseConfiguration(parameters_file):
    
    with open(parameters_file) as f:
        parameters = ConfigParser()
        parameters.read_file(f)
        
        oracle_path = parameters.get('Models', 'oracle')
        oracle = pickle.load(open(os.path.join(os.path.dirname(parameters_file), oracle_path), "rb"))

        toplayers = []
        if parameters.has_option('Models', 'toplayers'):
            names = parameters.get('Models', 'toplayers').strip().split()
            
            for layer_name in names:
                print('TopLayers, parsing layer:', layer_name)
                toplayers.append(getLayer(parameters, layer_name, os.path.dirname(parameters_file)))
            
            
        models = []
        i=1
        while parameters.has_option('Models', 'model'+str(i)):
            models.append(parameters.get('Models', 'model'+str(i)).strip().split())
            i += 1
        
        layers = []
        
        for i, model in enumerate(models):
            current_layers = []
            
            for m in model:
                print('Model' + str(i) +', parsing layer:', m)

                current_layers.append(getLayer(parameters, m, os.path.dirname(parameters_file)))
            
            layers.append(current_layers)
        
        print(len(models), 'models with:')
        for l in layers:
            print('\t', len(l), 'layers')
        
        return toplayers, layers, oracle

def softMax(x):
    y = np.exp(x - np.max(x))
    y /= np.sum(y)
    return y
