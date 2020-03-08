''' input rocket configuration
'''
from pprint import pprint
import re
from recordtype import recordtype
import numpy as np
import pandas as pd

RocketParams = recordtype(
    'RocketParams',
    'dry_mass, fuel_mass, motor_isp, max_thrust, drag_coefficient, '
    'rocket_area, vel, beta, alt, thrust_control'
)

DisplayParams = recordtype(
    'DisplayParams',
    'time_interval, flight_duration, vel_min_max, beta_min_max, '
    'alt_min_max, theta_min_max, acc_min_max'
)


def construct_control_array(file_name, delta_t, t_max):
    rocket_control_df = pd.read_excel(file_name)
    t = rocket_control_df['t']
    u = rocket_control_df['u']

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
    display_params = DisplayParams(*[None]*7)

    rocket_params.dry_mass = float(values[0])
    rocket_params.fuel_mass = float(values[1])
    rocket_params.motor_isp = float(values[2])
    rocket_params.max_thrust = float(values[3])
    rocket_params.drag_coefficient = float(values[4])
    rocket_params.rocket_area = float(values[5])
    rocket_params.vel = float(values[6])
    rocket_params.beta = float(values[7])
    rocket_params.alt = float(values[8])

    display_params.time_interval = float(values[9])
    display_params.flight_duration = float(values[10])
    display_params.vel_min_max = tuple([float(v) for v in values[11].split(',')])
    display_params.beta_min_max = tuple([float(v) for v in values[12].split(',')])
    display_params.alt_min_max = tuple([float(v) for v in values[13].split(',')])
    display_params.theta_min_max = tuple([float(v) for v in values[14].split(',')])
    display_params.acc_min_max = tuple([float(v) for v in values[15].split(',')])

    rocket_params.thrust_control = construct_control_array(
        values[16].strip(),
        display_params.time_interval,
        display_params.flight_duration)

    return rocket_params, display_params

if __name__ == '__main__':
    a, b = read_rocket_config('mintoc.cfg')
    pprint(a)
    print('-'*80)
    pprint(b)
