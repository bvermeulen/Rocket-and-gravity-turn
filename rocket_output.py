''' various output methods '''
import curses
import pandas as pd


class Console:
    ''' print the status_dict to the console every 0.5 second
        after the system has cleared the console
        updates to the self.status are provided to the class
        Console by the main program
        the method print_status should be started as a seperate
        thread
    '''

    def __init__(self):
        # self.window = curses.initscr()
        pass

    def display_status_message(self, status):
        # self.window.clear()
        status_message = (
            f'time: {status.get("time"):.0f}\n'
            f'rocket speed: {status.get("rocket speed"):.0f}\n'
            f'flight angle: {status.get("flight angle"):.3f}\n'
            f'altitude: {status.get("altitude"):.3f}\n'
            f'horizontal range: {status.get("horizontal range"):.3f}\n'
            f'acceleration: {status.get("acceleration"):.0f}\n'
            f'mass rocket: {status.get("mass rocket"):.3f}\n'
            f'thrust: {status.get("thrust"):.3f}\n'
            f'drag: {status.get("drag"):.3f}\n'
            f'gravity: {status.get("gravity"):.3f}\n'
        )
        # self.window.addstr(status_message)
        # self.window.refresh()
        print(status_message)

    def stop_window(self):
        # curses.napms(10_000)
        # self.window.refresh()
        # curses.endwin()
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
            status.get('mass rocket'),
            status.get('rocket speed'),
            status.get('flight angle'),
            status.get('altitude'),
            status.get('horizontal range'),
            status.get('u'),
        ]
        self.index += 1

    def write_logger(self):
        self.log_df.to_excel(self.outputlog_name)
