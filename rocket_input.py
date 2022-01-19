''' input rocket configuration
'''
from dataclasses import dataclass
import re
import numpy as np
import pandas as pd
from pprint import pprint


@dataclass
class RocketParams:
    dry_mass: float
    fuel_mass: float
    motor_isp0: float
    motor_isp1: float
    max_thrust: float
    rocket_area: float
    vel: float
    beta: float
    alt: float
    thrust_control: float


@dataclass
class EnvironmentParams:
    gravity: float
    radius: float
    drag_coefficient: float
    scale_height: float
    density: float


@dataclass
class DisplayParams:
    time_interval: float
    flight_duration: float
    vel_min_max: tuple[float, float]
    beta_min_max: tuple[float, float]
    alt_min_max: tuple[float, float]
    theta_min_max: tuple[float, float]
    acc_min_max: tuple[float, float]
    model_file: str


def construct_control_array(file_name, delta_t, t_max):
    rocket_control_df = pd.read_excel(file_name)
    t = rocket_control_df['time']
    u = rocket_control_df['control']

    t_resampled = np.arange(0, t_max + 2 * delta_t, delta_t)
    return np.interp(t_resampled, t, u)


def read_rocket_config(config_file_name):
    with open(config_file_name, mode='rt') as config:
        values = []
        for line in config:
            try:
                values.append(
                    re.match(r'^.*:(\d*.*\d).*$', line).group(1))
                continue

            except AttributeError:
                pass

            try:
                values.append(
                    re.match(r'^.*:(.*)$', line).group(1))

            except AttributeError:
                pass

    rocket_params = RocketParams(*[None]*10)
    environment_params = EnvironmentParams(*[None]*5)
    display_params = DisplayParams(*[None]*8)

    rocket_params.dry_mass = float(values[0])
    rocket_params.fuel_mass = float(values[1])
    rocket_params.motor_isp0 = float(values[2])
    rocket_params.motor_isp1 = float(values[3])
    rocket_params.max_thrust = float(values[4])
    rocket_params.rocket_area = float(values[5])
    rocket_params.vel = float(values[6])
    rocket_params.beta = float(values[7])
    rocket_params.alt = float(values[8])

    environment_params.gravity = float(values[9])
    environment_params.radius = float(values[10])
    environment_params.drag_coefficient = float(values[11])
    environment_params.scale_height = float(values[12])
    environment_params.density = float(values[13])

    display_params.time_interval = float(values[14])
    display_params.flight_duration = float(values[15])
    display_params.vel_min_max = tuple([float(v) for v in values[16].split(',')])
    display_params.beta_min_max = tuple([float(v) for v in values[17].split(',')])
    display_params.alt_min_max = tuple([float(v) for v in values[18].split(',')])
    display_params.theta_min_max = tuple([float(v) for v in values[19].split(',')])
    display_params.acc_min_max = tuple([float(v) for v in values[20].split(',')])
    display_params.model_file = values[21].strip()

    rocket_params.thrust_control = construct_control_array(
        display_params.model_file,
        display_params.time_interval,
        display_params.flight_duration)

    return rocket_params, environment_params, display_params

if __name__ == '__main__':
    a, b, c = read_rocket_config('mintoc_new.cfg')
    pprint(a)
    print('-'*80)
    pprint(b)
    print('-'*80)
    pprint(c)
