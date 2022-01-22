'''
Based on:
  Gravity Turn Maneuver with direct multiple shooting using CVodes
  (c) Mirko Hahn
  https://mintoc.de/index.php/Gravity_Turn_Maneuver_(Casadi)
  https://github.com/zegkljan/kos-stuff/tree/master/non-kos-tools/gturn
----------------------------------------------------------------
'''
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from rocket_input import read_rocket_config

rad_degrees = 180.0 / 3.141592653589793

def plot(result_df, rocket, display):
    FIGSIZE = (6, 8)
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=FIGSIZE)
    ax_vel, ax_beta = axes[0]
    ax_alt, ax_theta = axes[1]
    ax_throttle, ax_mass = axes[2]

    time_series = result_df['time'].to_numpy()

    vel_series = result_df['vel'].to_numpy()
    ax_vel.set_xlim(0, display.flight_duration)
    ax_vel.set_ylim(display.vel_min_max[0], display.vel_min_max[1])
    vel_plot, = ax_vel.plot(time_series, vel_series, color='black', linewidth=1)

    beta_series = result_df['ver_angle'].to_numpy() * rad_degrees
    ax_beta.set_xlim(0, display.flight_duration)
    ax_beta.set_ylim(display.beta_min_max[0], display.beta_min_max[1])
    beta_plot, = ax_beta.plot(time_series, beta_series, color='black', linewidth=1)

    alt_series = result_df['alt'].to_numpy()
    ax_alt.set_xlim(0, display.flight_duration)
    ax_alt.set_ylim(0, display.alt_min_max[1])
    alt_plot, = ax_alt.plot(time_series, alt_series, color='black', linewidth=1)

    theta_series = result_df['hor_angle'].to_numpy() * rad_degrees
    ax_theta.set_xlim(0, display.flight_duration)
    ax_theta.set_ylim(display.theta_min_max[0], display.theta_min_max[1])
    theta_plot, = ax_theta.plot(time_series, theta_series, color='black', linewidth=1)

    # ax_acc.set_xlim(0, display.flight_duration)
    # ax_acc.set_ylim(display.acc_min_max[0], display.acc_min_max[1])
    # acc_plot, = ax_acc.plot([0], [0], color='black', linewidth=1)

    mass_series = result_df['mass'].to_numpy()
    ax_mass.set_xlim(0, display.flight_duration)
    ax_mass.set_ylim(0, rocket.dry_mass + rocket.fuel_mass)
    mass_plot, = ax_mass.plot(time_series, mass_series, color='red', linewidth=3)

    throttle_series = result_df['control'].to_numpy()
    ax_throttle.set_xlim(0, display.flight_duration)
    ax_throttle.set_ylim(0, 1.2)
    throttle_plot, = ax_throttle.plot(time_series, throttle_series, color='red', linewidth=3)

    plt.show()

def main(config_file_name):
    rocket_params, _, model_params, display_params = read_rocket_config(config_file_name)
    result_df = pd.read_excel(model_params.model_file)
    plot(result_df, rocket_params, display_params)



if __name__ == '__main__':
    config_file_name = 'None'
    if len(sys.argv) == 2:
        config_file_name = sys.argv[1]

    config_file_name = Path(config_file_name)
    if not config_file_name.is_file():
        print(f'incorrect config file: {config_file_name}')
        exit()

    main(config_file_name)
