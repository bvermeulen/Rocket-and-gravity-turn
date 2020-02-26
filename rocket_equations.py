''' test some basic rocket equations
'''
import matplotlib.pyplot as plt
import numpy as np
import time

class RocketPhysics():

    G = 6.674 * 10**-11
    MASS_EARTH = 5.972 * 10**24
    RADIUS_EARTH = 6.371 * 10**6  # m
    STANDARD_GRAVITY = 9.80665    # m / s^2

    def __init__(self, motor_isp, mass_flow, dry_mass, fuel_mass, drag_coefficient, rocket_area):
        self.motor_isp = motor_isp
        self.mass_flow = mass_flow
        self.dry_mass = dry_mass
        self.fuel_mass = fuel_mass
        self.drag_coefficient = drag_coefficient
        self.rocket_area = rocket_area

    @classmethod
    def gravity(cls, altitude):
        return (cls.G * cls.MASS_EARTH /
                (cls.RADIUS_EARTH + altitude)**2)

    @classmethod
    def atmosheric_density(cls, altitude):
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

        _common_term = 1 + cls.STANDARD_GRAVITY * M
        if altitude < hb[1]:
            return (pb[0] * (Tb[0] / (Tb[0] + Lb[0] * (altitude - hb[0])))**_common_term /
                    (R * Lb[0]))

        elif altitude < hb[2]:
            return (pb[1] * np.exp(-cls.STANDARD_GRAVITY * M * (altitude - hb[1])) /
                    (R * Tb[1]))

        elif altitude < hb[3]:
            return (pb[2] * (Tb[2] / (Tb[2] + Lb[2] * (altitude - hb[2])))**_common_term /
                    (R * Lb[2]))

        elif altitude < hb[4]:
            return (pb[3] * (Tb[3] / (Tb[3] + Lb[3] * (altitude - hb[3])))**_common_term /
                    (R * Lb[3]))

        elif altitude < hb[5]:
            return (pb[4] * np.exp(-cls.STANDARD_GRAVITY * M * (altitude - hb[4])) /
                    (R * Tb[4]))

        elif altitude < hb[6]:
            return (pb[5] * (Tb[5] / (Tb[5] + Lb[5] * (altitude - hb[5])))**_common_term /
                    (R * Lb[5]))

        elif altitude < hb[7]:
            return (pb[6] * (Tb[6] / (Tb[6] + Lb[6] * (altitude - hb[6])))**_common_term /
                    (R * Lb[6]))

        else:
            return 0

    def thrust(self):
        return (self.motor_isp * self.STANDARD_GRAVITY * self.mass_flow)

    def drag(self, altitude, velocity):
        return (0.5 * self.drag_coefficient * self.rocket_area *
                self.atmosheric_density(altitude) * velocity**2)


def main():
    motor_isp = 335
    mass_flow = 160               # kg / s
    dry_mass = 17_000
    fuel_mass = 40_000
    drag_coefficient = 0.75
    rocket_area = np.pi * 3**2

    dt = 0.5                  # time interval (s)
    v_rocket = 0              # initial speed rocket (m / s)
    flight_duration = 600     # flight duration (s)
    altitude = 0              # altitude (m)
    delta_v = 0               # difference in speed (m / s)

    fig, ((ax_speed, ax_delta_v), (ax_altitude, ax_fuel)) = plt.subplots(nrows=2, ncols=2, figsize=(8, 5))
    plt.ion()
    fig.show()

    ax_speed.set_xlim(0, flight_duration)
    ax_speed.set_ylim(-1500, 3000)
    speed_plot, = ax_speed.plot([0], [0], color='black', linewidth=1)

    ax_delta_v.set_xlim(0, flight_duration)
    ax_delta_v.set_ylim(-50, 50)
    delta_v_plot, = ax_delta_v.plot([0], [0], color='black', linewidth=1)

    ax_altitude.set_xlim(0, flight_duration)
    ax_altitude.set_ylim(0, 200_000)
    altitude_plot, = ax_altitude.plot([0], [0], color='black', linewidth=1)

    ax_fuel.set_xlim(0, flight_duration)
    ax_fuel.set_ylim(0, 100)
    fuel_plot, = ax_fuel.plot([0], [0], color='black', linewidth=1)

    time_series = np.arange(0, flight_duration + dt, dt)
    speed_series = []
    delta_v_series = []
    altitude_series = []
    fuel_series = []

    rocket = RocketPhysics(motor_isp, mass_flow, dry_mass, fuel_mass, drag_coefficient, rocket_area)
    input('press enter to start ...')

    print(altitude)
    step = 1
    for elapsed_time in time_series:
        if altitude < -100:
            break

        speed_series.append(v_rocket)
        delta_v_series.append(delta_v / dt)
        altitude_series.append(altitude)
        fuel_series.append(fuel_mass)

        speed_plot.set_data(time_series[:step], speed_series)
        delta_v_plot.set_data(time_series[:step], delta_v_series)
        altitude_plot.set_data(time_series[:step], altitude_series)
        fuel_plot.set_data(time_series[:step], fuel_series)
        fig.canvas.draw()
        fig.canvas.flush_events()

        # time.sleep(dt*0.01)
        print(f'time: {elapsed_time:.1f}\n'
            f'delta_speed: {delta_v:.1f}\n'
            f'rocket speed: {v_rocket:.0f}\n'
            f'mass fuel: {fuel_mass:.1f}\n'
            f'height: {altitude:.0f}')


        if fuel_mass > 0:
            fuel_mass -= mass_flow * dt
            delta_v = (rocket.thrust() / (dry_mass + fuel_mass) -
                    rocket.gravity(altitude) * dt -
                    rocket.drag(altitude, v_rocket) * dt)

        else:
            if v_rocket < 0:
                delta_v = (-rocket.gravity(altitude) * dt -
                        rocket.drag(altitude, v_rocket) * dt)
            else:
                delta_v = (-rocket.gravity(altitude) * dt +
                        rocket.drag(altitude, v_rocket) * dt)

        v_rocket += delta_v
        altitude += v_rocket * dt
        step += 1


if __name__ == "__main__":
    main()
    input('press enter to stop program ...')
