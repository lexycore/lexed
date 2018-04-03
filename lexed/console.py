import threading


class Curses:
    __singleton_lock = threading.Lock()
    __singleton_instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = super().__new__(cls)
        return cls.__singleton_instance

    def __init__(self):
        temp = __import__('curses')
        self._screen = temp.initscr()
        # self.noecho = temp.noecho
        # self.cbreak = temp.cbreak
        # self.newwin = temp.newwin
        for key in temp.__dict__:
            # if key == key.upper():
            if key != 'initscr' and not key.startswith('_'):
                setattr(self, key, getattr(temp, key, None))
        # self.ACS_HLINE = temp.ACS_HLINE
        # self.ACS_ULCORNER = temp.ACS_ULCORNER
        # self.ACS_URCORNER = temp.ACS_URCORNER
        # self.ACS_VLINE = temp.ACS_VLINE
        # self.ACS_LLCORNER = temp.ACS_LLCORNER
        # self.ACS_LRCORNER = temp.ACS_LRCORNER
        # self.ACS_DIAMOND = temp.ACS_DIAMOND
        # self.A_BOLD = temp.A_BOLD
        # self.A_REVERSE = temp.A_REVERSE
        # self.A_UNDERLINE = temp.A_UNDERLINE

    def initscr(self):
        return self._screen


curses = Curses()
