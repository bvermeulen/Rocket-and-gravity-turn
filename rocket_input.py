''' input rocket configuration
'''
import sys
import re
from dataclasses import dataclass
from pathlib import Path
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
class ModelParams:
    N: int
    h_obj: float
    v_obj: float
    q_obj: float
    model_file: str


@dataclass
class DisplayParams:
    time_interval: float
    flight_duration: float
    vel_min_max: tuple[float, float]
    beta_min_max: tuple[float, float]
    alt_min_max: tuple[float, float]
    theta_min_max: tuple[float, float]
    acc_min_max: tuple[float, float]


def construct_control_array(file_name, delta_t, t_max):
    if not file_name.is_file():
        return np.array([])

    rocket_control_df = pd.read_excel(file_name)
    t = rocket_control_df['time']
    u = rocket_control_df['control']

    t_resampled = np.arange(0, t_max + 2 * delta_t, delta_t)
    u_resampled = np.interp(t_resampled, t, u)
    pd.DataFrame({'time': t_resampled, 'control': u_resampled}).to_excel('control.xlsx')
    return u_resampled


def read_rocket_config(config_file_name):
    with open(config_file_name, mode='rt') as config:
        values = []
        for line in config:
            try:
                values.append(
                    re.match(r'^.*:(.*)$', line).group(1))

            except AttributeError:
                pass

    rocket_params = RocketParams(*[None]*10)
    environment_params = EnvironmentParams(*[None]*5)
    model_params = ModelParams(*[None]*5)
    display_params = DisplayParams(*[None]*7)

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

    model_params.N = int(values[14])
    model_params.h_obj = float(values[15])
    model_params.v_obj = float(values[16])
    model_params.q_obj = float(values[17])
    model_params.model_file = values[25].strip()

    display_params.time_interval = float(values[18])
    display_params.flight_duration = float(values[19])
    display_params.vel_min_max = tuple([float(v) for v in values[20].split(',')])
    display_params.beta_min_max = tuple([float(v) for v in values[21].split(',')])
    display_params.alt_min_max = tuple([float(v) for v in values[22].split(',')])
    display_params.theta_min_max = tuple([float(v) for v in values[23].split(',')])
    display_params.acc_min_max = tuple([float(v) for v in values[24].split(',')])

    rocket_params.thrust_control = construct_control_array(
        Path(model_params.model_file),
        display_params.time_interval,
        display_params.flight_duration
    )

    return rocket_params, environment_params, model_params, display_params

if __name__ == '__main__':
    config_file_name = 'None'
    if len(sys.argv) == 2:
        config_file_name = sys.argv[1]

    config_file_name = Path(config_file_name)
    if not config_file_name.is_file():
        print(f'incorrect config file: {config_file_name}')
        exit()

    a, b, c, d = read_rocket_config(config_file_name)
    pprint(a)
    print('-'*80)
    pprint(b)
    print('-'*80)
    pprint(c)
    print('-'*80)
    pprint(d)
