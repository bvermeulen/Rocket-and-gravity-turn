''' test some basic rocket equations
'''
import threading
import time  #pylint: disable=unused-import
import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import ode
from rocket_input import read_rocket_config
from rocket_output import Console


FIGSIZE = (8, 10)

class RocketPhysics():

    G = 6.674 * 10**-11
    MASS_EARTH = 5.972 * 10**24   # kg
    RADIUS_EARTH = 6.371 * 10**6  # m
    STANDARD_GRAVITY = 9.80665    # m / s^2

    def __init__(self, motor_isp, mass_flow, dry_mass, fuel_mass,
                 drag_coefficient, rocket_area):
        self.motor_isp = motor_isp
        self.mass_flow = mass_flow
        self.dry_mass = dry_mass
        self.fuel_mass = fuel_mass
        self.drag_coefficient = drag_coefficient
        self.rocket_area = rocket_area
        self.v_dot = 0
        self.angle_0 = 0
        self._throttle = 0

    @classmethod
    def gravity(cls, altitude):
        return cls.G * cls.MASS_EARTH / (cls.RADIUS_EARTH + altitude)**2

    @classmethod
    def atmospheric_density(cls, altitude):
        '''The altitude model used below is based on the standard atmospheric model used
           in modern meteorology. It takes into accout the different regression rates and
           properties of the thermoclines.
        '''

        R = 8.31432   # ideal gas constant J/(mol*K)
        M = .0289644  # molar mass of dry air, kg/mol
        hb = [0, 11_000, 20_000, 32_000, 47_000, 51_000, 71_000, 86_000]
        pb = [1.2250, 0.36391, 0.08803, 0.01322, 0.00143, 0.00086, 0.000064]
        Tb = [288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65]
        Lb = [-0.0065, 0.0, 0.001, 0.0028, 0.0, -0.0028, -0.002]

        if altitude < hb[1]:
            return (pb[0] * (Tb[0] / (Tb[0] + Lb[0] * (altitude - hb[0])))**
                    (1 + cls.STANDARD_GRAVITY * M / (R * Lb[0])))

        elif altitude < hb[2]:
            return (pb[1] * np.exp(-cls.STANDARD_GRAVITY * M * (altitude - hb[1]) /
                                   (R * Tb[1])))

        elif altitude < hb[3]:
            return (pb[2] * (Tb[2] / (Tb[2] + Lb[2] * (altitude - hb[2])))**
                    (1 + cls.STANDARD_GRAVITY * M / (R * Lb[2])))

        elif altitude < hb[4]:
            return (pb[3] * (Tb[3] / (Tb[3] + Lb[3] * (altitude - hb[3])))**
                    (1 + cls.STANDARD_GRAVITY * M / (R * Lb[3])))

        elif altitude < hb[5]:
            return (pb[4] * np.exp(-cls.STANDARD_GRAVITY * M * (altitude - hb[4]) /
                                   (R * Tb[4])))

        elif altitude < hb[6]:
            return (pb[5] * (Tb[5] / (Tb[5] + Lb[5] * (altitude - hb[5])))**
                    (1 + cls.STANDARD_GRAVITY * M / (R * Lb[5])))

        elif altitude < hb[7]:
            return (pb[6] * (Tb[6] / (Tb[6] + Lb[6] * (altitude - hb[6])))**
                    (1 + cls.STANDARD_GRAVITY * M / (R * Lb[6])))

        else:
            return 0

    def thrust(self):
        if self.fuel_mass > 1:
            return self.motor_isp * self.STANDARD_GRAVITY * self.mass_flow * self.throttle

        return 0

    @property
    def mass(self):
        return self.dry_mass + self.fuel_mass

    @property
    def acceleration(self):
        return self.v_dot

    @property
    def initial_flight_angle(self):
        return self.angle_0

    @initial_flight_angle.setter
    def initial_flight_angle(self, value):
        self.angle_0 = value

    @property
    def throttle(self):
        return  self._throttle

    @throttle.setter
    def throttle(self, value):
        self._throttle = value

    def drag(self, altitude, velocity):
        return (0.5 * self.drag_coefficient * self.rocket_area *
                self.atmospheric_density(altitude) * velocity**2)

    def derivatives_gravity_turn(self, t, state):
        ''' calculation of derivatives (annotated with _dot) for a rocket gravity
            turn equations. This function is input to the scipy integrate ode function
            arguments:
                t: time (s) [notice not used in the derivatives but required for ode]
                state: numpy array of variables, whose derivatives are determined
                    vel: rocket velocity (m/s)
                    flight_angle: angle with horizontal reference (radians)
                    alt: altitude (m)
                    h_range: horizontal range (m)
                    fuel_mass: mass of fuel (kg)
            returns:
                state_dot: numpy array of derivatative of above variables

            Assumptions:
                - effects of wind and solar radiation on rocket are zero
                - trajectory is considered two dimensional
                - non-rotational spherical Earth
                - angle of attack is zero, therefore pitch angle is same
                  as flight angle and lift is neglected
        '''
        vel, flight_angle, alt, h_range, fuel_mass = state  #pylint: disable=unused-variable

        cos_flight_angle = np.cos(flight_angle)
        sin_flight_angle = np.sin(flight_angle)

        self.v_dot = (
            self.thrust() / self.mass -
            vel / abs(vel) * self.drag(alt, vel) / self.mass -
            self.gravity(alt) * cos_flight_angle
            )

        flight_angle_dot = (
            (self.gravity(alt) / vel -
             vel / (self.RADIUS_EARTH + alt)) * sin_flight_angle -
            self.initial_flight_angle / vel
            )

        alt_dot = vel * cos_flight_angle
        h_range_dot = vel * sin_flight_angle

        if fuel_mass > 0:
            mass_fuel_dot = -self.mass_flow * self.throttle
            self.fuel_mass = fuel_mass

        else:
            mass_fuel_dot = 0

        return np.array(
            [self.v_dot, flight_angle_dot, alt_dot, h_range_dot, mass_fuel_dot])

def launch(rocket_config):
    console = Console()
    x = threading.Thread(target=console.print_status)
    x.start()

    motor_isp = rocket_config.get('motor_isp')
    mass_flow = rocket_config.get('mass_flow')
    dry_mass = rocket_config.get('dry_mass')
    fuel_mass = rocket_config.get('fuel_mass')
    drag_coefficient = rocket_config.get('drag_coefficient')
    rocket_area = rocket_config.get('rocket_area')

    time_interval = rocket_config.get('time_interval')
    flight_duration = rocket_config.get('flight_duration')
    v_rocket = rocket_config.get('v_rocket')
    flight_angle = rocket_config.get('flight_angle')
    altitude = rocket_config.get('altitude')
    u = rocket_config.get('u')
    h_range = 0
    rad_deg = 180 / np.pi

    # display min-max tuples y-axis
    speed_min_max = rocket_config.get('speed_min_max')
    flight_angle_min_max = rocket_config.get('flight_angle_min_max')
    altitude_min_max = rocket_config.get('altitude_min_max')
    h_range_min_max = rocket_config.get('h_range_min_max')
    acceleration_min_max = rocket_config.get('acceleration_min_max')

    rocket = RocketPhysics(
        motor_isp, mass_flow, dry_mass, fuel_mass, drag_coefficient, rocket_area)

    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=FIGSIZE)
    ax_speed, ax_flight_angle = axes[0]
    ax_altitude, ax_h_range = axes[1]
    ax_throttle, ax_mass = axes[2]

    plt.ion()
    fig.show()

    ax_speed.set_xlim(0, flight_duration)
    ax_speed.set_ylim(speed_min_max[0], speed_min_max[1])
    speed_plot, = ax_speed.plot([0], [0], color='black', linewidth=1)

    ax_flight_angle.set_xlim(0, flight_duration)
    ax_flight_angle.set_ylim(flight_angle_min_max[0], flight_angle_min_max[1])
    flight_angle_plot, = ax_flight_angle.plot([0], [0], color='black', linewidth=1)

    ax_altitude.set_xlim(0, flight_duration)
    ax_altitude.set_ylim(altitude_min_max[0], altitude_min_max[1])
    altitude_plot, = ax_altitude.plot([0], [0], color='black', linewidth=1)

    ax_h_range.set_xlim(0, flight_duration)
    ax_h_range.set_ylim(h_range_min_max[0], h_range_min_max[1])
    h_range_plot, = ax_h_range.plot([0], [0], color='black', linewidth=1)

    # ax_acceleration.set_xlim(0, flight_duration)
    # ax_acceleration.set_ylim(acceleration_min_max[0], acceleration_min_max[1])
    # acceleration_plot, = ax_acceleration.plot([0], [0], color='black', linewidth=1)

    ax_mass.set_xlim(0, flight_duration)
    ax_mass.set_ylim(0, rocket.mass)
    mass_plot, = ax_mass.plot([0], [0], color='red', linewidth=3)

    ax_throttle.set_xlim(0, flight_duration)
    ax_throttle.set_ylim(0, 1.2)
    throttle_plot, = ax_throttle.plot([0], [0], color='red', linewidth=3)

    time_series = np.arange(0, flight_duration + time_interval, time_interval)
    speed_series = []
    flight_angle_series = []
    altitude_series = []
    h_range_series = []
    acceleration_series = []
    throttle_series = []
    mass_series = []

    rocket_gravity_turn_integrator = ode(
        rocket.derivatives_gravity_turn).set_integrator('vode')

    # zero state
    _time = 0
    rocket_gravity_turn_integrator.set_initial_value(
        np.array([v_rocket, flight_angle, altitude, h_range, rocket.fuel_mass]), _time)

    # launch until rocket is back at earth
    index = 1
    rocket.throttle = u[0]

    while rocket_gravity_turn_integrator.successful() and altitude > -100 and \
          _time <= flight_duration:

        speed_series.append(v_rocket)
        flight_angle_series.append(flight_angle)
        altitude_series.append(altitude)
        h_range_series.append(h_range)
        acceleration_series.append(rocket.acceleration)
        throttle_series.append(rocket.throttle)
        mass_series.append(rocket.mass)

        speed_plot.set_data(time_series[:index], speed_series)
        flight_angle_plot.set_data(time_series[:index], flight_angle_series)
        altitude_plot.set_data(time_series[:index], altitude_series)
        h_range_plot.set_data(time_series[:index], h_range_series)
        # acceleration_plot.set_data(time_series[:index], acceleration_series)
        throttle_plot.set_data(time_series[:index], throttle_series)
        mass_plot.set_data(time_series[:index], mass_series)
        fig.canvas.draw()
        fig.canvas.flush_events()

        # update the status to the console
        console.status = {
            'time': _time,
            'rocket speed': v_rocket,
            'flight angle': flight_angle * rad_deg,
            'altitude': altitude,
            'horizontal range': h_range,
            'acceleration': rocket.acceleration,
            'mass rocket': rocket.mass,
            'thrust': rocket.thrust() / rocket.mass,
            'drag': rocket.drag(altitude, v_rocket) / rocket.mass,
            'gravity': rocket.gravity(altitude)
        }

        _time += time_interval
        index += 1
        rocket.throttle = u[index]

        v_rocket, flight_angle, altitude, h_range, fuel_mass = \
            rocket_gravity_turn_integrator.integrate(_time)

        if not 2000 < altitude < 2300:
            rocket.initial_flight_angle = 0

        else:
            rocket.initial_flight_angle = -0.3


if __name__ == "__main__":
    config_file_name = 'rocket.cfg'
    if len(sys.argv) == 2:
        config_file_name = sys.argv[1]

    launch(read_rocket_config(config_file_name))
    input('press enter to stop program ...')
