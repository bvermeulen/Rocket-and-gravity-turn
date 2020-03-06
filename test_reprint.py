import curses

window = curses.initscr()
window.addstr('hello there')
window.refresh()
curses.napms(2000)

curses.endwin()