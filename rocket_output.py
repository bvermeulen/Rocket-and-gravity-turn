''' output module for rocket_launch.py
        - Console output
            time, velocity, flight angle, altitude, horizontal range,
            mass rocket, thrust, drag, gravity, acceleration
        - Log output to excel
            time, mass, velocity, beta, h, theta, throttle
        - Plot output
            velocity, pitch angle, altitude, azimuth, throtte, mass,
            trajectory
'''
import curses
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.gridspec import GridSpec
from PIL import Image

deg_rad = np.pi / 180.0
rad_deg = 180.0 / np.pi

class Console:
    ''' print the status_dict to the console every 0.5 second
        after the system has cleared the console
        updates to the self.status are provided to the class
        Console by the main program
        the method print_status should be started as a seperate
        thread
    '''
    def __init__(self):
        self.window = curses.initscr()

    def display_status_message(self, status):
        self.window.clear()
        status_message = (
            f'time: {status.get("time"):.0f}\n'
            f'rocket speed: {status.get("vel"):.3f}\n'
            f'flight angle: {status.get("beta"):.3f}\n'
            f'altitude: {status.get("alt"):.3f}\n'
            f'horizontal range: {status.get("theta"):.3f}\n'
            f'mass rocket: {status.get("mass"):.3f}\n'
            f'thrust: {status.get("thrust"):.3f}\n'
            f'drag: {status.get("drag"):.3f}\n'
            f'gravity: {status.get("gravity"):.3f}\n'
            f'acceleration: {status.get("acc"):.3f}\n'
        )
        self.window.addstr(status_message)
        self.window.refresh()

    def stop_window(self):
        curses.napms(6_000)
        self.window.refresh()
        curses.endwin()
        input('press enter to stop program ...')


class OutputLog:

    def __init__(self):
        self.outputlog_name = 'rocket_output_log.xlsx'
        self.log_df = pd.DataFrame(
            columns=['t', 'm', 'v', 'beta', 'h', 'theta', 'u'])
        self.index = 0

    def log_status(self, status):
        self.log_df.loc[self.index] = [
            status.get('time'),
            status.get('mass'),
            status.get('vel'),
            status.get('beta'),
            status.get('alt'),
            status.get('theta'),
            status.get('throttle_control'),
        ]
        self.index += 1

    def write_logger(self):
        self.log_df.to_excel(self.outputlog_name)


class MapPlot:
    FIGSIZE = (12, 8)

    def __init__(self, rocket, environment, _, display):
        ''' initial all plot settings
        '''
        self.fig = plt.figure(constrained_layout=True, figsize=self.FIGSIZE)
        gs = GridSpec(3, 4, figure=self.fig)
        ax_vel = self.fig.add_subplot(gs[0, 0])
        ax_beta = self.fig.add_subplot(gs[0, 1])
        ax_alt = self.fig.add_subplot(gs[1, 0])
        ax_theta = self.fig.add_subplot(gs[1, 1])
        ax_throttle = self.fig.add_subplot(gs[2, 0])
        ax_mass = self.fig.add_subplot(gs[2, 1])
        self.ax_traj = self.fig.add_subplot(gs[0:2, 2:])

        ax_vel.set_title('velocity')
        ax_vel.set_xlim(0, display.flight_duration)
        ax_vel.set_ylim(display.vel_min_max[0], display.vel_min_max[1])
        self.vel_plot, = ax_vel.plot([0], [0], color='black', linewidth=1)

        ax_beta.set_title('pitch angle')
        ax_beta.set_xlim(0, display.flight_duration)
        ax_beta.set_ylim(display.beta_min_max[0], display.beta_min_max[1])
        self.beta_plot, = ax_beta.plot([0], [0], color='black', linewidth=1)

        ax_alt.set_title('altitude')
        ax_alt.set_xlim(0, display.flight_duration)
        ax_alt.set_ylim(0, display.alt_min_max[1])
        self.alt_plot, = ax_alt.plot([0], [0], color='black', linewidth=1)

        ax_theta.set_title('azimuth')
        ax_theta.set_xlim(0, display.flight_duration)
        ax_theta.set_ylim(display.theta_min_max[0], display.theta_min_max[1])
        self.theta_plot, = ax_theta.plot([0], [0], color='black', linewidth=1)

        ax_throttle.set_title('engine throttle')
        ax_throttle.set_xlim(0, display.flight_duration)
        ax_throttle.set_ylim(0, 1.2)
        self.throttle_plot, = ax_throttle.plot([0], [0], color='red', linewidth=3)

        ax_mass.set_title('rocket mass')
        ax_mass.set_xlim(0, display.flight_duration)
        ax_mass.set_ylim(0, rocket.dry_mass + rocket.fuel_mass)
        self.mass_plot, = ax_mass.plot([0], [0], color='red', linewidth=3)

        self.earth_radius = environment.radius
        display_radius = self.earth_radius + display.alt_min_max[1]
        y_min = (
            display_radius * np.cos(display.theta_min_max[1] * deg_rad)
            if display.theta_min_max[1] < 180 else -display_radius
        )
        y_max = display_radius
        x_min = (
            display_radius * min(
                np.sin(display.theta_min_max[0] * deg_rad),
                np.sin(display.theta_min_max[1] * deg_rad)
            )
            if display.theta_min_max[1] < 270 else -display_radius
        )
        x_max = (
            display_radius * np.sin(display.theta_min_max[1] * deg_rad)
            if display.theta_min_max[1] < 90 else +display_radius
        )
        self.ax_traj.set_title('rocket trajectory')
        self.ax_traj.set_xlim(x_min, x_max)
        self.ax_traj.set_ylim(y_min, y_max)
        self.ax_traj.set_aspect('equal')
        thetas = np.arange(0, 2*np.pi, 0.01)
        earth_x_vals, earth_y_vals = [], []
        for theta in thetas:
            earth_x_vals.append(self.earth_radius * np.sin(theta))
            earth_y_vals.append(self.earth_radius * np.cos(theta))
        self.ax_traj.plot(earth_x_vals, earth_y_vals, color='blue', linewidth=1.2)
        self.traj_plot, = self.ax_traj.plot([0], [0], color='red', linewidth=1.0)

        self.rocket_sprite = Image.open(display.rocket_sprite_file)
        self.rocket = None
        self.update_sprite(0.0, self.earth_radius, 0.0, 0.0)

        step_ = display.time_interval * display.status_update_step
        self.time_series = np.arange(0, display.flight_duration + step_, step_)
        self.vel_series = []
        self.beta_series = []
        self.alt_series = []
        self.theta_series = []
        self.acc_series = []
        self.throttle_series = []
        self.mass_series = []
        self.traj_series_x = []
        self.traj_series_y = []

        plt.ion()
        self.fig.show()

    def update_sprite(self, x, y, alignment, theta):
        try:
            self.rocket.remove()

        except AttributeError:
            pass

        im = OffsetImage(
            self.rocket_sprite.rotate(-(alignment + theta)), zoom=0.015
        )
        rocket_im = AnnotationBbox(im, (x, y), frameon=False
        )
        self.rocket = self.ax_traj.add_artist(rocket_im)


    def plot_state_generator(self, new_state=None):
        ''' generator to plot the new state
        '''
        index = 0
        while True:
            state = yield new_state
            if state is None:
                yield

            alt = state.get('alt')
            theta = state.get('theta')
            radius = self.earth_radius + alt
            self.traj_series_x.append(radius * np.sin(theta * deg_rad))
            self.traj_series_y.append(radius * np.cos(theta * deg_rad))
            self.traj_plot.set_data(self.traj_series_x, self.traj_series_y)

            self.vel_series.append(state.get('vel'))
            self.beta_series.append(state.get('beta'))
            self.alt_series.append(alt)
            self.theta_series.append(theta)
            self.throttle_series.append(state.get('control'))
            self.mass_series.append(state.get('mass'))

            self.vel_plot.set_data(self.time_series[:index+1], self.vel_series)
            self.beta_plot.set_data(self.time_series[:index+1], self.beta_series)
            self.alt_plot.set_data(self.time_series[:index+1], self.alt_series)
            self.theta_plot.set_data(self.time_series[:index+1], self.theta_series)
            self.throttle_plot.set_data(self.time_series[:index+1], self.throttle_series)
            self.mass_plot.set_data(self.time_series[:index+1], self.mass_series)

            self.update_sprite(
                self.traj_series_x[-1], self.traj_series_y[-1],
                self.beta_series[-1], theta
            )

            self.blit()
            index += 1

    def blit(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
