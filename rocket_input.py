''' input rocket configuration
'''
import re

def read_rocket_config(config_file_name):
    with open(config_file_name, mode='rt') as config:
        values = []
        for line in config:
            try:
                values.append(
                    re.match(r'^.*:(\d*.*\d).*$', line).group(1))
            except AttributeError:
                pass


    keys = ['dry_mass', 'fuel_mass', 'motor_isp',
            'mass_flow', 'drag_coefficient', 'rocket_area',
            'v_rocket', 'flight_angle', 'altitude',
            'time_interval', 'flight_duration',
            'speed_min_max', 'flight_angle_min_max', 'altitude_min_max',
            'h_range_min_max', 'acceleration_min_max']
    rocket_config_dict = {}
    for i in range(11):
        rocket_config_dict[keys[i]] = float(values[i])

    for i in range(11, 16):
        min_max = []
        for val in values[i].split(','):
            min_max.append(float(val))
        rocket_config_dict[keys[i]] = tuple(min_max)

    return rocket_config_dict
