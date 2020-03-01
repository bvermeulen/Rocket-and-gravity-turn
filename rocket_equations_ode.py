''' test some basic rocket equations
'''
import time  #pylint: disable=unused-import
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import ode

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
            return self.motor_isp * self.STANDARD_GRAVITY * self.mass_flow

        else:
            return 0

    @property
    def mass(self):
        return self.dry_mass + self.fuel_mass

    @property
    def acceleration(self):
        return self.v_dot

    def drag(self, altitude, velocity):
        return (0.5 * self.drag_coefficient * self.rocket_area *
                self.atmospheric_density(altitude) * velocity**2)

    def derivatives_gravity_turn(self, t, state):
        vel, alt, fuel_mass = state

        self.v_dot = (
            self.thrust() / self.mass -
            vel / abs(vel) * self.drag(alt, vel) / self.mass -
            self.gravity(alt)
            )

        h_dot = vel

        if fuel_mass > 0:
            mass_fuel_dot = -self.mass_flow
            self.fuel_mass = fuel_mass

        else:
            mass_fuel_dot = 0

        state_dot = np.zeros(3)
        state_dot[0] = self.v_dot
        state_dot[1] = h_dot
        state_dot[2] = mass_fuel_dot

        return state_dot

def main():
    motor_isp = 335
    mass_flow = 149               # kg / s
    dry_mass = 10_000             # kg
    fuel_mass = 40_000            # kg
    drag_coefficient = 0.75       #
    rocket_area = np.pi * 3**2    # m^2

    time_interval = 5.0           # time interval (s)
    v_rocket = 0.05               # initial speed rocket (m / s) - needs to be small positive     pylint: disable=line-too-long
    flight_duration = 900         # flight duration (s)
    altitude = 0                  # altitude (m)

    # display min-max tuples y-axis
    speed_min_max = (-2500, 2500)
    acceleration_min_max = (-20, 170)
    altitude_min_max = (0, 400_000)

    rocket = RocketPhysics(
        motor_isp, mass_flow, dry_mass, fuel_mass, drag_coefficient, rocket_area)

    fig, ((ax_speed, ax_acceleration), (ax_altitude, ax_mass)) = plt.subplots(
        nrows=2, ncols=2, figsize=(8, 5))
    plt.ion()
    fig.show()

    ax_speed.set_xlim(0, flight_duration)
    ax_speed.set_ylim(speed_min_max[0], speed_min_max[1])
    speed_plot, = ax_speed.plot([0], [0], color='black', linewidth=1)

    ax_acceleration.set_xlim(0, flight_duration)
    ax_acceleration.set_ylim(acceleration_min_max[0], acceleration_min_max[1])
    acceleration_plot, = ax_acceleration.plot([0], [0], color='black', linewidth=1)

    ax_altitude.set_xlim(0, flight_duration)
    ax_altitude.set_ylim(altitude_min_max[0], altitude_min_max[1])
    altitude_plot, = ax_altitude.plot([0], [0], color='black', linewidth=1)

    ax_mass.set_xlim(0, flight_duration)
    ax_mass.set_ylim(0, rocket.mass)
    mass_plot, = ax_mass.plot([0], [0], color='black', linewidth=1)

    time_series = np.arange(0, flight_duration + time_interval, time_interval)
    speed_series = []
    acceleration_series = []
    altitude_series = []
    mass_series = []

    rocket_gravity_turn_integrator = ode(
        rocket.derivatives_gravity_turn).set_integrator('vode')

    # zero state
    state = np.array([v_rocket, 0, rocket.fuel_mass])
    _time = 0
    rocket_gravity_turn_integrator.set_initial_value(state, _time)

    # launch until rocket is back at earth
    index = 1
    while rocket_gravity_turn_integrator.successful() and altitude > -100:

        v_rocket, altitude, fuel_mass = state

        speed_series.append(v_rocket)
        acceleration_series.append(rocket.acceleration)
        altitude_series.append(altitude)
        mass_series.append(rocket.mass)

        speed_plot.set_data(time_series[:index], speed_series)
        acceleration_plot.set_data(time_series[:index], acceleration_series)
        altitude_plot.set_data(time_series[:index], altitude_series)
        mass_plot.set_data(time_series[:index], mass_series)
        fig.canvas.draw()
        # fig.canvas.flush_events()

        print(f'time: {_time:.1f}\n'
              f'acceleration: {rocket.acceleration:.1f}\n'
              f'rocket speed: {v_rocket:.0f}\n'
              f'mass rocket: {rocket.mass:.1f}\n'
              f'altitude: {altitude:.0f}\n'
              f'thrust: {rocket.thrust() / rocket.mass:.0f}\n'
              f'drag: {rocket.drag(altitude, v_rocket) / rocket.mass:.3f}\n'
              f'gravity: {rocket.gravity(altitude):.3f}\n'
             )

        _time += time_interval
        state = rocket_gravity_turn_integrator.integrate(
            _time)

            # rocket_gravity_turn_integrator.t + time_interval)
        index += 1

if __name__ == "__main__":
    main()
    input('press enter to stop program ...')
