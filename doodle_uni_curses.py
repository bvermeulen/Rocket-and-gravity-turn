from unicurses import *


class Monitor:
    def __init__(self):
        stdscr = initscr()
        start_color()
        noecho()

    def write(self, message):
        init_pair(1, COLOR_CYAN, COLOR_BLACK)
        addstr(message)
        mvchgat(0, 0, -1, A_BOLD, 1, None)
        mvchgat()
        refresh()
        getch()

    def close(self):
        endwin()


if __name__ == "__main__":
    monitor = Monitor()
    monitor.write("dit is een test ....")
    monitor.write("... en ja het lijkt te werken!")
    monitor.close()
