''' various output methods '''
import os
import time


class Console:
    ''' print the status_dict to the console every 0.5 second
        after the system has cleared the console
        updates to the self.status are provided to the class
        Console by the main program
        the method print_status should be started as a seperate
        thread
    '''

    def __init__(self):
        self.status_dict = {
            'time': 0,
            'rocket speed': 0,
            'flight angle': 0,
            'altitude': 0,
            'horizontal range': 0,
            'acceleration': 0,
            'mass rocket': 0,
            'thrust': 0,
            'drag': 0,
            'gravity': 0
        }

        os.system('clear')

    @property
    def status(self):
        return self.status_dict

    @status.setter
    def status(self, value):
        self.status_dict = value

    def print_status(self):
        while True:
            os.system('clear')
            status_message = (
                f'time: {self.status.get("time"):.0f}\n'
                f'rocket speed: {self.status.get("rocket speed"):.0f}\n'
                f'flight angle: {self.status.get("flight angle"):.3f}\n'
                f'altitude: {self.status.get("altitude"):.0f}\n'
                f'horizontal range: {self.status.get("horizontal range"):.0f}\n'
                f'acceleration: {self.status.get("acceleration"):.0f}\n'
                f'mass rocket: {self.status.get("mass rocket"):.0f}\n'
                f'thrust: {self.status.get("thrust"):.3f}\n'
                f'drag: {self.status.get("drag"):.3f}\n'
                f'gravity: {self.status.get("gravity"):.3f}\n'
            )
            print(status_message)
            time.sleep(0.5)
