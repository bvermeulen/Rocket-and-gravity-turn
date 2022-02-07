''' Rocket launch
      - using thrust profile as calculated by rocket_casadi_solution
        for a gravty turn [rocket_casadi_solution.py]

    based on :
        https://mintoc.de/index.php/Gravity_Turn_Maneuver
        providing the gravity turn differential equations

    Config file:
        parameters for rocket, environment, model and display, see
        mintoc_launch.cfg as example

    Author:
        Bruno Vermeulen
        bruno.vermeulen@hotmail.com
'''
import sys
from pathlib import Path
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

    def __init__(self, rocket_params, environment_params):
        self.rocket = rocket_params
        self.v_dot = 0
        self.beta_0 = self.rocket.beta
        self._throttle = 0
        self._fuel_mass = self.rocket.fuel_mass
        self.env = environment_params

    def gravity(self, altitude):
        return (
            self.env.gravity * (self.env.radius / (self.env.radius + altitude))**2)

    @property
    def thrust(self):
        return  self.rocket.max_thrust * self.throttle

    @property
    def mass(self):
        return self.rocket.dry_mass + self.fuel_mass

    @property
    def fuel_mass(self):
        return self._fuel_mass

    @fuel_mass.setter
    def fuel_mass(self, value):
        self._fuel_mass = value

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
        k = 0.5 * self.env.density * self.rocket.rocket_area * self.env.drag_coefficient
        return k * np.exp(-altitude / self.env.scale_height) * velocity * velocity

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
        theta_dot = vel * sin_beta / (self.env.radius + alt)

        beta_dot = (
            self.gravity(alt) * sin_beta / vel - theta_dot
        )
        mass_fuel_dot = -self.thrust / self.rocket.motor_isp0 / self.env.gravity
        self.fuel_mass = fuel_mass

        return np.array(
            [self.v_dot, beta_dot, alt_dot, theta_dot, mass_fuel_dot]
        )

def launch(rocket_params, environment_params, model_params, display_params):
    console = Console()
    logger = OutputLog()
    mapper = MapPlot(rocket_params, environment_params, model_params, display_params)
    rocket = RocketPhysics(rocket_params, environment_params)

    rocket_gravity_turn_integrator = ode(
        rocket.derivatives_gravity_turn).set_integrator('vode'
    )
    # initial values
    theta = 0
    flight_state = State(
        vel=rocket_params.vel,
        beta=rocket_params.beta,
        alt=rocket_params.alt,
        theta=theta,
        fuel_mass=rocket_params.fuel_mass
    )
    rocket.throttle = rocket_params.thrust_control[0]
    _time = 0
    rocket_gravity_turn_integrator.set_initial_value(
        np.array(list(asdict(flight_state).values())), _time
    )

    # launch until rocket is back at earth, explodes or is lost to space
    index = 0
    plot = mapper.plot_state_generator()
    next(plot)
    while (rocket_gravity_turn_integrator.successful() and flight_state.alt > -100 and
           _time <= display_params.flight_duration):

        rocket.throttle = rocket_params.thrust_control[index]

        if index % display_params.status_update_step == 0:
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
            plot.send(state)
            console.display_status_message(state)
            logger.log_status(state)

        _time += display_params.time_interval
        index += 1

        flight_state.vel, flight_state.beta, flight_state.alt, flight_state.theta, flight_state.fuel_mass = (
            rocket_gravity_turn_integrator.integrate(_time))

    console.stop_window()
    logger.write_logger()

if __name__ == "__main__":
    config_file_name = 'None'
    if len(sys.argv) == 2:
        config_file_name = sys.argv[1]

    config_file_name = Path(config_file_name)
    if not config_file_name.is_file():
        print(f'incorrect config file: {config_file_name}')
        exit()

    launch(*read_rocket_config(config_file_name))
