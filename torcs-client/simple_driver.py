from pytocl.driver import Driver
from pytocl.car import State, Command
import math
import time as tm
import sys
import os.path
import numpy as np
import pickle

sys.path.insert(0, '../')






class SimpleDriver(Driver):
    def __init__(self, out_file=None):
        super(SimpleDriver, self).__init__(logdata=False)

        self.out_file = out_file
        
        
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

        command = Command()
        
        command.accelerator = 1
        command.gear = 1
        command.brake = 0
        command.steering = 0#-1 * carstate.angle * np.pi / (180.0 * 0.785398)

        if carstate.speed_x > 1 and command.gear >= 0 and command.brake < 0.1 and carstate.rpm > 8000:
            command.gear = min(6, command.gear + 1)

        if carstate.rpm < 2500 and command.gear > 1:
            command.gear = command.gear - 1

        if not command.gear:
            command.gear = carstate.gear or 1
        
        
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


