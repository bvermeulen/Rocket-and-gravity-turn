''' test reprint '''
import time
from reprint import output


class Console:

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

    @property
    def status(self):
        return self.status_dict

    @status.setter
    def status(self, value):
        self.status_dict = value

    def print_status(self):
        ''' print the status_dict to the console with reprint output that
            clears the console before writing
        '''
        with output(output_type='dict') as output_lines:
            while True:
                output_lines[' 1. time'] = (
                    f'{self.status.get("time"):.0f}')
                output_lines[' 2. rocket speed'] = (
                    f'{self.status.get("rocket speed"):.0f}')
                output_lines[' 3. flight angle'] = (
                    f'{self.status.get("flight angle"):.3f}')
                output_lines[' 4. altitude'] = (
                    f'{self.status.get("altitude"):.0f}')
                output_lines[' 5. horizontal range'] = (
                    f'{self.status.get("horizontal range"):.0f}')
                output_lines[' 6. acceleration'] = (
                    f'{self.status.get("acceleration"):.0f}')
                output_lines[' 7. mass rocket'] = (
                    f'{self.status.get("mass rocket"):.0f}')
                output_lines[' 8. thrust'] = (
                    f'{self.status.get("thrust"):.3f}')
                output_lines[' 9. drag'] = (
                    f'{self.status.get("drag"):.3f}')
                output_lines['10. gravity'] = (
                    f'{self.status.get("gravity"):.3f}')
                time.sleep(0.5)
