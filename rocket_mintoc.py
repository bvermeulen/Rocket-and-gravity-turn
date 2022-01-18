''' test some basic rocket equations
'''
import sys
from dataclasses import dataclass, asdict
import numpy as np
from scipy.integrate import ode
from rocket_input import read_rocket_config
from rocket_output import Console, OutputLog, MapPlot


rad_deg = 180 / np.pi


@dataclass
class State:
    vel: float
    beta: float
    alt: float
    theta: float
    fuel_mass: float


class RocketPhysics():

    RADIUS_EARTH = 6e2
    STANDARD_GRAVITY = 9.81e-3
    H = 5.6
    RHO_0 = (1 * 1.2230948554874)

    def __init__(self, rocket_params):
        self.rocket = rocket_params
        self.v_dot = 0
        self.beta_0 = self.rocket.beta
        self._throttle = 0
        self.fuel_mass = self.rocket.fuel_mass

    @classmethod
    def gravity(cls, altitude):
        return (
            cls.STANDARD_GRAVITY * (cls.RADIUS_EARTH / (cls.RADIUS_EARTH + altitude))**2)

    @property
    def thrust(self):
        return  self.rocket.max_thrust * self.throttle

    @property
    def mass(self):
        return self.rocket.dry_mass + self.fuel_mass

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
        k = (0.5e3 * self.RHO_0 * self.rocket.rocket_area *
             self.rocket.drag_coefficient
            )
        return k * np.exp(-altitude / self.H) * velocity * velocity

    def derivatives_gravity_turn(self, t, state):  #pylint: disable=unused-argument
        ''' Rocket differential equations
            Calculation of derivatives (annotated with _dot) for a rocket gravity
            turn. This function is input to the scipy integrate ode function
            arguments:
                t: time (s) [notice not used in the derivatives but required for ode]
                state: numpy array of variables, whose derivatives are determined
                    vel: rocket velocity (km/s)
                    beta: angle with horizontal reference (radians)
                    alt: altitude (km)
                    theta: horizontal range in degrees (radians)
                    fuel_mass: mass of fuel (kg)
            returns:
                numpy array of derivatative of above variables

            Assumptions:
                - effects of wind and solar radiation on rocket are zero
                - trajectory is considered two dimensional
                - non-rotational spherical Earth
                - angle of attack is zero, therefore pitch angle is same
                  as flight angle and lift are neglected
        '''
        vel, beta, alt, theta, fuel_mass = state  #pylint: disable=unused-variable

        cos_beta = np.cos(beta)
        sin_beta = np.sin(beta)

        self.v_dot = (
            self.thrust / self.mass -
            self.drag(alt, vel) / self.mass -
            self.gravity(alt) * cos_beta
            )

        alt_dot = vel * cos_beta
        theta_dot = vel * sin_beta / (self.RADIUS_EARTH + alt)

        beta_dot = (
            self.gravity(alt) * sin_beta / vel -
            theta_dot
            )

        mass_fuel_dot = -self.thrust / self.rocket.motor_isp / self.STANDARD_GRAVITY
        self.fuel_mass = fuel_mass

        return np.array(
            [self.v_dot, beta_dot, alt_dot, theta_dot, mass_fuel_dot])

def launch(rocket_params, display_params):
    console = Console()
    logger = OutputLog()
    mapper = MapPlot(rocket_params, display_params)
    rocket = RocketPhysics(rocket_params)

    rocket_gravity_turn_integrator = ode(
        rocket.derivatives_gravity_turn).set_integrator('vode')

    # initial values
    flight_state = State(
        vel=rocket_params.vel,
        beta=rocket_params.beta,
        alt=rocket_params.alt,
        theta=0,
        fuel_mass=rocket_params.fuel_mass)

    rocket.throttle = rocket_params.thrust_control[0]
    theta = 0
    _time = 0
    rocket_gravity_turn_integrator.set_initial_value(
        np.array(list(asdict(flight_state).values())), _time
    )
    # launch until rocket is back at earth, explodes or is lost to space
    index = 0
    while (rocket_gravity_turn_integrator.successful() and flight_state.alt > -100 and
           _time <= display_params.flight_duration):

        rocket.throttle = rocket_params.thrust_control[index]

        state = {
            'time': _time,
            'vel': flight_state.vel,
            'beta': flight_state.beta * rad_deg,
            'alt': flight_state.alt,
            'theta': flight_state.theta * rad_deg,
            'acc': rocket.acceleration,
            'mass': rocket.mass,
            'thrust': rocket.thrust / rocket.mass,
            'drag': rocket.drag(flight_state.alt, flight_state.vel) / rocket.mass,
            'gravity': rocket.gravity(flight_state.alt),
            'control': rocket_params.thrust_control[index],
            'index': index,
        }
        mapper.plot(state)
        console.display_status_message(state)
        logger.log_status(state)

        _time += display_params.time_interval
        index += 1

        flight_state.vel, flight_state.beta, flight_state.alt, flight_state.theta, flight_state.fuel_mass = (
            rocket_gravity_turn_integrator.integrate(_time))

    console.stop_window()
    logger.write_logger()

if __name__ == "__main__":
    config_file_name = 'rocket.cfg'
    if len(sys.argv) == 2:
        config_file_name = sys.argv[1]

    launch(*read_rocket_config(config_file_name))
