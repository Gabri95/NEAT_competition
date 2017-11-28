import logging
import math
from collections import Iterable
from functools import partialmethod
import numpy as np

_logger = logging.getLogger(__name__)

DEGREE_PER_RADIANS = 180 / math.pi
MPS_PER_KMH = 1000 / 3600


class Value:
    """Base class for value objects."""

    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(k, v) for k, v in self.__dict__.items()
        )

    def chain(self, *attributes):
        """Attribute iterator, unpacking iterable attributes."""
        for name in attributes:
            value = getattr(self, name)
            if isinstance(value, Iterable):
                yield from value
            else:
                yield value


class State(Value):
    """State of car and environment, sent periodically by racing server.

    Update the state's dictionary and use properties to access the various
    sensor values. Value ``None`` means the sensor value is invalid or unset.

    Attributes:
        sensor_dict: Dictionary of sensor key value pairs in string form.
        angle: Angle between car direction and track axis, [-180;180], deg.
        current_lap_time: Time spent in current lap, [0;inf[, s.
        damage: Damage points, 0 means no damage, [0;inf[, points.
        distance_from_start:
            Distance of car from start line along track center, [0;inf[, m.
        distance_raced:
            Distance car traveled since beginning of race, [0;inf[, m.
        fuel: Current fuel level, [0;inf[, l.
        gear: Current gear. -1: reverse, 0: neutral,
            [1;6]: corresponding forward gear.
        last_lap_time: Time it took to complete last lap, [0;inf[, s.
        opponents: Distances to nearest opponents in 10 deg slices in
            [-180;180] deg. [0;200], m.
        race_position: Position in race with respect to other cars, [1;N].
        rpm: Engine's revolutions per minute, [0;inf[.
        speed_x: Speed in X (forward) direction, ]-inf;inf[, m/s.
        speed_y: Speed in Y (left) direction, ]-inf;inf[, m/s.
        speed_z: Speed in Z (up) direction, ]-inf;inf[, m/s.
        distances_from_edge: Distances to track edge along configured driver
            range finders, [0;200], m.
        focused_distances_from_edge: Distances to track edge, five values in
            five degree range along driver focus, [0;200], m. Can be used only
            once per second and while on track, otherwise values set to -1.
            See ``focused_distances_from_edge_valid``.
        distance_from_center: Normalized distance from track center,
            -1: right edge, 0: center, 1: left edge, [0;1].
        wheel_velocities: Four wheels' velocity, [0;inf[, deg/s.
        z: Distance of car center of mass to track surface, ]-inf;inf[, m.
    """

    def __init__(self, sensor_dict):
        """Creates decoded car state from sensor value dictionary."""
        self.angle = self.float_value(sensor_dict, 'angle') * \
            DEGREE_PER_RADIANS
        self.current_lap_time = self.float_value(sensor_dict, 'curLapTime')
        self.damage = self.int_value(sensor_dict, 'damage')
        self.distance_from_start = self.float_value(
            sensor_dict,
            'distFromStart'
        )
        self.distance_raced = self.float_value(sensor_dict, 'distRaced')
        self.fuel = self.float_value(sensor_dict, 'fuel')
        self.gear = self.int_value(sensor_dict, 'gear')
        self.last_lap_time = self.float_value(sensor_dict, 'lastLapTime')
        self.opponents = self.floats_value(sensor_dict, 'opponents')
        self.race_position = self.int_value(sensor_dict, 'racePos')
        self.rpm = self.float_value(sensor_dict, 'rpm')
        self.speed_x = self.float_value(sensor_dict, 'speedX') * MPS_PER_KMH
        self.speed_y = self.float_value(sensor_dict, 'speedY') * MPS_PER_KMH
        self.speed_z = self.float_value(sensor_dict, 'speedZ') * MPS_PER_KMH
        self.distances_from_edge = self.floats_value(sensor_dict, 'track')
        self.distance_from_center = self.float_value(sensor_dict, 'trackPos')
        self.wheel_velocities = tuple(
            v * DEGREE_PER_RADIANS for v in self.floats_value(
                sensor_dict,
                'wheelSpinVel'
            )
        )
        self.z = self.float_value(sensor_dict, 'z')

        self.focused_distances_from_edge = self.floats_value(
            sensor_dict,
            'focus'
        )

        self.distFromLeader = self.float_value(sensor_dict, 'distFromLeader')

    @property
    def distances_from_egde_valid(self):
        """Flag whether regular distances are currently valid."""
        return -1 not in self.distances_from_edge

    @property
    def focused_distances_from_egde_valid(self):
        """Flag whether focus distances are currently valid."""
        return -1 not in self.focused_distances_from_edge

    # def to_input_array(self):
    #
    #     array = []
    #
    #     array.append(self.speed_x)
    #
    #     array.append(self.distance_from_center)
    #
    #     array.append(self.angle)
    #
    #     for j in range(19):
    #         array.append(self.distances_from_edge[j])
    #
    #     return np.array(array)/200
    
    def to_input_array(self, smaller=False, opponents=False):

        array = []

        # self.current_lap_time
        # array.append(self.distance_from_start)
        # array.append(self.distance_raced)
        # array.append(self.fuel)
        # gear = np.sign(self.gear)
        # for g in range(-1, 2):
        #     if g == gear:
        #         array.append(1)
        #     else:
        #         array.append(0)
        # array.append(np.sign(self.gear))
        # self.last_lap_time
        # self.race_position
        # array.append((self.rpm - 2000.0)/5000.0)

        array.append(self.angle / 180.0)

        # TODO - TO ADD BACK IF USING THE CIRCUIT MODEL
        # array.append(self.damage/10000.0)

        array.append(self.speed_x / 50.0)
        array.append(self.speed_y / 40.0)
        
        if smaller:
            for idxs in [[0], [2], [4], [7, 9, 11], [14], [16], [18]]:
                d = min([self.distances_from_edge[j] for j in idxs])
                if math.fabs(self.distance_from_center) > 1 or d < 0:
                    array.append(-1)
                else:
                    array.append(d / 200.0)
        else:
            for j in range(19):
                if math.fabs(self.distance_from_center) > 1 or self.distances_from_edge[j] < 0:
                    array.append(-1)
                else:
                    array.append(self.distances_from_edge[j] / 200.0)

        array.append(self.distance_from_center)

        if opponents:
            #for idxs in [[1, 0, -1, -2], range(2, 9), range(9, 15), range(16, 20), range(20, 27), range(27, 34)]:
            for idxs in [range(0, 9), range(9, 11), range(13, 15), range(16, 18), range(18, 20), range(21, 23), range(25, 27), range(27, 36)]:
                d = min([self.opponents[j] for j in idxs])
                array.append(d/200.0)
        
        # for j in range(4):
        #     array.append(self.wheel_velocities[j] / 3000.0)  # /150.0
        # array.append(self.z-0.36)
        # array.append(self.speed_z / 10.0)

        return np.array(array)
        
    
    
    @staticmethod
    def converted_value(sensor_dict, key, converter):
        try:
            return converter(sensor_dict[key])
        except (ValueError, KeyError):
            _logger.warning(
                'Expected sensor value {!r} not found.'.format(key)
            )
            return None

    float_value = partialmethod(converted_value, converter=float)
    floats_value = partialmethod(
        converted_value,
        converter=lambda l: tuple(float(v) for v in l)
    )
    int_value = partialmethod(converted_value, converter=int)


class Command(Value):
    """Command to drive car during next control cycle.

    Attributes:
        accelerator: Accelerator, 0: no gas, 1: full gas, [0;1].
        brake:  Brake pedal, [0;1].
        gear: Next gear. -1: reverse, 0: neutral,
            [1;6]: corresponding forward gear.
        steering: Rotation of steering wheel, -1: full right, 0: straight,
            1: full left, [-1;1]. Full turn results in an approximate wheel
            rotation of 21 degrees.
        focus: Direction of driver's focus, resulting in corresponding
            ``State.focused_distances_from_edge``, [-90;90], deg.
    """

    def __init__(self):
        self.accelerator = 0.0
        self.brake = 0.0
        self.gear = 0
        self.steering = 0.0
        self.focus = 0.0

    @property
    def actuator_dict(self):
        return dict(
            accel=[self.accelerator],
            brake=[self.brake],
            gear=[self.gear],
            steer=[self.steering],
            clutch=[0],  # server car does not need clutch control?
            focus=[self.focus],
            meta=[0]  # no support for server restart via meta=1
        )
