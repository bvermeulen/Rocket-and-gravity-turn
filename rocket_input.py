''' input rocket configuration
'''
from pprint import pprint
import re
import numpy as np
import pandas as pd

def construct_control_array(file_name, delta_t, t_max):
    rocket_control_df = pd.read_excel('mintoc_gravity_turn.xlsx')
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

    keys = ['dry_mass', 'fuel_mass', 'motor_isp',
            'max_thrust', 'drag_coefficient', 'rocket_area',
            'v_rocket', 'flight_angle', 'altitude',
            'time_interval', 'flight_duration',
            'speed_min_max', 'flight_angle_min_max', 'altitude_min_max',
            'h_range_min_max', 'acceleration_min_max', 'u']
    rocket_config_dict = {}
    for i in range(11):
        rocket_config_dict[keys[i]] = float(values[i])

    for i in range(11, 16):
        min_max = []
        for val in values[i].split(','):
            min_max.append(float(val))
        rocket_config_dict[keys[i]] = tuple(min_max)

    rocket_config_dict[keys[16]] = construct_control_array(
        values[16].strip(),
        rocket_config_dict.get('time_interval'),
        rocket_config_dict.get('flight_duration'))

    return rocket_config_dict

if __name__ == '__main__':
    pprint(read_rocket_config('mintoc.cfg'))
