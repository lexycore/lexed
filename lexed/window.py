import os
import threading

from lexed.editor import Editor
from .const import CHAR_DICT
from .console import curses


class Window:
    __singleton_lock = threading.Lock()
    __singleton_instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = super().__new__(cls)
        return cls.__singleton_instance

    def __init__(self, app):
        self.app = app
        self.config = app.config
        self.colors = {}
        self.c = ''

        # Initialize curses window
        self.screen = curses.initscr()

        curses.noecho()  # turns off echoing of keys to the screen
        curses.cbreak()  # read keys without requiring Enter key

        self.screen.keypad(1)  # Enable keypad mode (read special keys)

        self.height, self.width = self.screen.getmaxyx()  # GRABS SIZE of CURRENT TERMINAL WINDOW
        # (self.height, self.width) = windowSize  # split into height and width

        self.height -= 1
        self.width -= 1

        self._win = curses.newwin(self.height, self.width, 0, 0)  # 0,0 is start position
        self.editor = Editor(self)

    def print_header(self, save_info='', message='', save_path='', total=0):
        """Prints header to curses screen"""
        if message:
            # Print info message
            self.screen.addstr(0, 0, (' ' * self.width),
                               self.config['color_header'])  # this was commented out, not sure why
            self.screen.addstr(0, 0, message, self.config['color_message'])
        else:
            self.screen.addstr(0, 0, (' ' * self.width), self.config['color_header'])  # print empty line
            if not save_path:
                self.screen.addstr(0, 0, 'file/not/saved', self.config['color_header'])  # print file/not/saved
            elif len(save_path) > self.width - 14:
                temp_text = os.path.split(save_path)[1]
                self.screen.addstr(0, 0, '%s%s' % (temp_text, save_info),
                                   self.config['color_header'])  # print filename only
            else:
                self.screen.addstr(0, 0, '%s%s' % (save_path, save_info),
                                   self.config['color_header'])  # print directory and filename

        temp_text = '%i' % total
        lines_text = temp_text.rjust(11)
        if self.config['inline_commands'] == 'protected':
            protect_string = str(self.config['protect_string'])
            self.screen.addstr(0, self.width - 12 - len(protect_string) - 1, lines_text, self.config['color_header'])
            self.screen.addstr(0, self.width - len(protect_string) - 1, protect_string, self.config['color_message'])
        else:
            self.screen.addstr(0, self.width - 12, lines_text, self.config['color_header'])

        self.screen.hline(1, 0, curses.ACS_HLINE, self.width, self.config['color_bar'])

    def addstr(self, *args, **kwargs):
        self.screen.addstr(*args, **kwargs)

    def hline(self, *args, **kwargs):
        self.screen.hline(*args, **kwargs)

    def getch(self, *args, **kwargs):
        self.c = self.screen.getch(*args, **kwargs)
        return self.c

    def vline(self, *args, **kwargs):
        self.screen.vline(*args, **kwargs)

    def refresh(self, *args, **kwargs):
        self.screen.refresh(*args, **kwargs)

    def clear(self, *args, **kwargs):
        self.screen.clear(*args, **kwargs)

    def status_message(self, text, number, total, update_lines=False):
        """Displays status message"""
        if update_lines:  # clears entire header and updates number of lines
            self.addstr(0, 0, ' ' * self.width, self.config['color_header'])
            temp_text = '%i' % total
            lines_text = temp_text.rjust(11)
            if self.config['inline_commands'] == 'protected':
                protect_string = str(self.config['protect_string'])
                self.addstr(0, self.width - 12 - len(protect_string) - 1, lines_text, self.config['color_header'])
                self.addstr(0, self.width - len(protect_string) - 1, protect_string, self.config['color_message'])
            else:
                self.addstr(0, self.width - 12, lines_text, self.config['color_header'])
        else:  # clears space for statusMessage only
            self.addstr(0, 0, ' ' * (self.width - 13), self.config['color_header'])
        number = int(number)  # Convert to integer
        message = ' %s%i' % (text, number) + '% '
        self.addstr(0, 0, message, self.config['color_warning'])
        self.refresh()

    def get_confirmation(self, text=' Are you sure? (y/n) ', any_key=False, x=0, y=0):
        """Confirm selection in new (centered) window. Returns 'True' if 'y' pressed."""
        if not any_key and self.config['skip_confirmation'] and text != ' File exists, overwrite? (y/n) ':
            return True
        side = '   '
        if len(text) < 15:
            diff = 15 - len(text)
            spacer = ' ' * int(diff / 2)
            text = spacer + text + spacer
        line = (len(text) + (len(side) * 2)) * ' '

        half_height = int(self.height / 2)
        self.hline(half_height - 1, int(self.width / 2) - int(len(text) / 2) - len(side),
                   curses.ACS_HLINE, (len(text) + 6), self.config["color_message"])
        # print corners
        self.hline(half_height - 1, int(self.width / 2) - int(len(text) / 2) - len(side),
                   curses.ACS_ULCORNER, 1, self.config["color_message"])
        self.hline(half_height - 1, int(self.width / 2) - int(len(text) / 2) + len(text) + 2,
                   curses.ACS_URCORNER, 1, self.config["color_message"])

        self.addstr(half_height + 1, int(self.width / 2) - int(len(text) / 2) - len(side),
                    line, self.config["color_message"])  # Prints blank line
        self.addstr(half_height, int(self.width / 2) - int(len(text) / 2) - len(side),
                    side, self.config["color_message"])  # Prints left side
        self.vline(half_height, int(self.width / 2) - int(len(text) / 2) - len(side),
                   curses.ACS_VLINE, 3, self.config["color_message"])  # prints left side

        self.addstr(half_height, int(self.width / 2) - int(len(text) / 2),
                    text, self.config["color_message"])  # Prints text message

        self.addstr(half_height, int(self.width / 2) - int(len(text) / 2) + len(text),
                    side, self.config["color_message"])  # Prints right side
        self.vline(half_height, int(self.width / 2) - int(len(text) / 2) + len(text) + 2,
                   curses.ACS_VLINE, 3, self.config["color_message"])  # prints right side

        if any_key:
            self.addstr(half_height + 1, int(self.width / 2) - int(len("(press any key)") / 2),
                        "(press any key)", self.config["color_message"])
        self.hline(half_height + 2, int(self.width / 2) - int(len(text) / 2) - len(side),
                   curses.ACS_HLINE, (len(text) + 6), self.config["color_message"])
        # print bottom corners
        self.hline(half_height + 2, int(self.width / 2) - int(len(text) / 2) - len(side),
                   curses.ACS_LLCORNER, 1, self.config["color_message"])
        self.hline(half_height + 2, int(self.width / 2) - int(len(text) / 2) + len(text) + 2,
                   curses.ACS_LRCORNER, 1, self.config["color_message"])

        # Prints text message
        try:
            self.addstr(y + self.height - 2, x, "",
                        self.config["color_normal"])  # Moves cursor to previous position
        except:
            pass

        self.refresh()
        self.c = ''
        while True:
            self.c = self.getch()
            if any_key and self.c:
                return True
            if self.c == ord('y') or self.c == ord('Y'):
                pos = text.find("y")
                self.addstr(half_height, (int(self.width / 2) - int(len(text) / 2) + pos), 'y',
                            self.config["color_quote_double"])  # Prints text message
                self.refresh()
                return True
            if self.c == ord('n') or self.c == ord('N'):
                return False

    def prompt_user(self, title='ENTER COMMAND:', default_answer='',
                    footer="(press 'enter' to proceed, UP arrow to cancel)", adjust_pos=False):
        """
        Displays window and prompts user to enter command
        Used for 'Entry', 'Find', and 'Save' windows
        """

        self.c = ''
        if adjust_pos and '.' in default_answer and default_answer.rfind('.') == len(default_answer) - 4:
            position = len(default_answer) - 4
        elif adjust_pos and '.' in default_answer and default_answer.rfind('.') == len(default_answer) - 3:
            position = len(default_answer) - 3
        else:
            position = len(default_answer)
        text = default_answer
        side = '   '
        line = int(self.width - 16) * ' '
        if self.width < 70 and footer == "(press 'enter' to proceed, UP arrow to cancel)":
            footer = '(press UP arrow to cancel)'
        footer = footer.center(int(self.width - 16) - 6)
        empty_line = (int(self.width - 16) - 6) * ' '
        if len(text) > len(empty_line) * 2:
            text = text[0:(len(empty_line) * 2)]

        half_height = int(self.height / 2)
        while self.c != 10:
            for i in range(0, 6):
                self.addstr(half_height - 2 + i, 8, line, self.config['color_message'])
            self.addstr(half_height - 1, 11, title, self.config['color_message'])
            self.addstr(half_height + 2, 11, footer, self.config['color_message'])
            self.addstr(half_height, 11, empty_line, self.config['color_normal'])
            self.addstr(half_height + 1, 11, empty_line, self.config['color_normal'])

            # print border
            self.hline(half_height - 2, 9, curses.ACS_HLINE, (len(empty_line) + 4), self.config['color_message'])
            self.hline(half_height + 3, 9, curses.ACS_HLINE, (len(empty_line) + 4), self.config['color_message'])
            self.vline(half_height - 2, 8, curses.ACS_VLINE, (6), self.config['color_message'])
            self.vline(half_height - 2, (len(empty_line) + 13), curses.ACS_VLINE, (6), self.config['color_message'])
            self.hline(half_height - 2, 8, curses.ACS_ULCORNER, 1, self.config['color_message'])
            self.hline(half_height + 3, 8, curses.ACS_LLCORNER, 1, self.config['color_message'])
            self.hline(half_height - 2, (len(empty_line) + 13), curses.ACS_URCORNER, 1, self.config['color_message'])
            self.hline(half_height + 3, (len(empty_line) + 13), curses.ACS_LRCORNER, 1, self.config['color_message'])

            if len(text) > len(empty_line):
                self.addstr(half_height, 11, text[0:len(empty_line)], self.config['color_normal'])
                self.addstr(half_height + 1, 11, text[len(empty_line):], self.config['color_normal'])
            else:
                self.addstr(half_height, 11, text, self.config['color_normal'])

                if len(text) == len(empty_line) and position == len(empty_line):
                    self.addstr(half_height + 1, 11, '', self.config['color_normal'])  # Moves cursor to second line

            # Move cursor
            if position < len(empty_line):
                self.addstr(half_height, position + 11, '', self.config['color_normal'])
            else:
                self.addstr(half_height + 1, position + 11 - len(empty_line), '', self.config['color_normal'])

            self.refresh()
            c = self.getch()

            part1 = text[0:position]
            part2 = text[position:]

            if c in (curses.KEY_UP, self.config['key_find'],
                     self.config['key_entry_window'], self.config['key_save_as']):
                return False
            if c == curses.KEY_LEFT:
                position -= 1
            if c == curses.KEY_RIGHT:
                position += 1
            position = max(0, min(position, len(text)))

            if c == curses.KEY_BACKSPACE or c == 127:
                try:
                    text = part1[0:-1] + part2
                except:
                    pass
                position -= 1

            elif c in CHAR_DICT:
                text = (part1 + CHAR_DICT[c] + part2)
                position += 1
        # attempt to hide encrypt password during load/save
        self.addstr(half_height, 11, empty_line, self.config['color_normal'])
        self.addstr(half_height + 1, 11, empty_line, self.config['color_normal'])
        self.refresh()

        return text

    def print_background(self):
        """Displays background color"""
        for i in range(0, self.height + 2):
            try:
                self.addstr(i, 0, (' ' * self.width), self.config['color_background'])
            except:
                return

    def draw_line_number_background(self):
        """Draws background for line numbers"""
        for y in range(2, self.height + 1):
            self.addstr(y, 0, '     ', self.config['color_line_numbers'])  # Prints blank line number block

    def draw_page_guide(self, end_pos=0):  # , hline_pos=1):
        """Draws page guide"""
        end_pos = end_pos or self.height + 1
        if self.width <= (self.config['page_guide'] + 6):
            return

        for i in range(2, end_pos):
            self.vline(i, (self.config['page_guide'] + 6), curses.ACS_VLINE, 1,
                       self.config['color_bar'])  # prints vertical line
        self.hline(1, (self.config['page_guide'] + 6), curses.ACS_TTEE, 1, self.config['color_bar'])

    def color_on(self, default_colors=False):
        """Turn on curses color and handle color assignments"""
        # global program_message
        self.editor.reset_line()

        if curses.has_colors():
            curses.start_color()
        else:
            if self.config.os == 'Macintosh':
                self.editor.get_confirmation('Color not supported on the OSX terminal!', True)
            else:
                self.editor.get_confirmation('Color not supported on your terminal!', True)
            self.config.set_default_settings(True, True)
            self.config['display_color'] = False
            self.editor.program_message = ' Monochrome display '
            return

        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_BLUE)
        curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(13, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_MAGENTA)

        curses.init_pair(15, curses.COLOR_BLUE, curses.COLOR_WHITE)
        curses.init_pair(16, curses.COLOR_GREEN, curses.COLOR_WHITE)
        curses.init_pair(17, curses.COLOR_RED, curses.COLOR_WHITE)

        curses.init_pair(18, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(19, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(20, curses.COLOR_WHITE, curses.COLOR_RED)

        curses.init_pair(21, curses.COLOR_RED, curses.COLOR_BLUE)
        curses.init_pair(22, curses.COLOR_BLUE, curses.COLOR_RED)

        curses.init_pair(23, curses.COLOR_MAGENTA, curses.COLOR_GREEN)
        curses.init_pair(24, curses.COLOR_GREEN, curses.COLOR_MAGENTA)

        curses.init_pair(25, curses.COLOR_YELLOW, curses.COLOR_GREEN)
        curses.init_pair(26, curses.COLOR_GREEN, curses.COLOR_YELLOW)

        curses.init_pair(27, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        curses.init_pair(28, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(29, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        curses.init_pair(30, curses.COLOR_GREEN, curses.COLOR_BLUE)
        curses.init_pair(31, curses.COLOR_MAGENTA, curses.COLOR_BLUE)
        curses.init_pair(32, curses.COLOR_CYAN, curses.COLOR_BLUE)

        curses.init_pair(33, curses.COLOR_CYAN, curses.COLOR_WHITE)
        curses.init_pair(34, curses.COLOR_YELLOW, curses.COLOR_WHITE)
        curses.init_pair(35, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
        curses.init_pair(36, curses.COLOR_WHITE, curses.COLOR_WHITE)
        curses.init_pair(37, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
        curses.init_pair(38, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(39, curses.COLOR_GREEN, curses.COLOR_RED)
        curses.init_pair(40, curses.COLOR_YELLOW, curses.COLOR_RED)
        curses.init_pair(41, curses.COLOR_CYAN, curses.COLOR_RED)
        curses.init_pair(42, curses.COLOR_MAGENTA, curses.COLOR_RED)
        curses.init_pair(43, curses.COLOR_BLUE, curses.COLOR_GREEN)
        curses.init_pair(44, curses.COLOR_CYAN, curses.COLOR_GREEN)
        curses.init_pair(45, curses.COLOR_RED, curses.COLOR_GREEN)
        curses.init_pair(46, curses.COLOR_RED, curses.COLOR_YELLOW)
        curses.init_pair(47, curses.COLOR_WHITE, curses.COLOR_CYAN)
        curses.init_pair(48, curses.COLOR_BLUE, curses.COLOR_CYAN)
        curses.init_pair(49, curses.COLOR_RED, curses.COLOR_CYAN)
        curses.init_pair(50, curses.COLOR_YELLOW, curses.COLOR_CYAN)
        curses.init_pair(51, curses.COLOR_MAGENTA, curses.COLOR_CYAN)

        curses.init_pair(52, curses.COLOR_BLUE, curses.COLOR_YELLOW)

        self.colors.update({
            "white_on_black": curses.color_pair(1),
            "cyan_on_black": curses.color_pair(2),
            "blue_on_black": curses.color_pair(3),
            "green_on_black": curses.color_pair(4),
            "yellow_on_black": curses.color_pair(5),
            "red_on_black": curses.color_pair(6),
            "magenta_on_black": curses.color_pair(7),

            "black_on_white": curses.color_pair(8),
            "black_on_cyan": curses.color_pair(9),
            "black_on_blue": curses.color_pair(10),
            "black_on_green": curses.color_pair(11),
            "black_on_yellow": curses.color_pair(12),
            "black_on_red": curses.color_pair(13),
            "black_on_magenta": curses.color_pair(14),

            "blue_on_white": curses.color_pair(15),
            "green_on_white": curses.color_pair(16),
            "red_on_white": curses.color_pair(17),

            "white_on_blue": curses.color_pair(18),
            "white_on_green": curses.color_pair(19),
            "white_on_red": curses.color_pair(20),

            "red_on_blue": curses.color_pair(21),
            "blue_on_red": curses.color_pair(22),

            "magenta_on_green": curses.color_pair(23),
            "green_on_magenta": curses.color_pair(24),

            "yellow_on_green": curses.color_pair(25),
            "green_on_yellow": curses.color_pair(26),

            "white_on_yellow": curses.color_pair(27),
            "white_on_magenta": curses.color_pair(28),

            "yellow_on_blue": curses.color_pair(29),
            "green_on_blue": curses.color_pair(30),
            "magenta_on_blue": curses.color_pair(31),
            "cyan_on_blue": curses.color_pair(32),

            "cyan_on_white": curses.color_pair(33),
            "yellow_on_white": curses.color_pair(34),
            "magenta_on_white": curses.color_pair(35),
            "white_on_white": curses.color_pair(36),
            "yellow_on_yellow": curses.color_pair(37),
            "black_on_black": curses.color_pair(38),
            "green_on_red": curses.color_pair(39),
            "yellow_on_red": curses.color_pair(40),
            "cyan_on_red": curses.color_pair(41),
            "magenta_on_red": curses.color_pair(42),
            "blue_on_green": curses.color_pair(43),
            "cyan_on_green": curses.color_pair(44),
            "red_on_green": curses.color_pair(45),
            "red_on_yellow": curses.color_pair(46),
            "white_on_cyan": curses.color_pair(47),
            "blue_on_cyan": curses.color_pair(48),
            "red_on_cyan": curses.color_pair(49),
            "yellow_on_cyan": curses.color_pair(50),
            "magenta_on_cyan": curses.color_pair(51),

            "blue_on_yellow": curses.color_pair(52),
        })

        if self.config.no_bold:
            BOLD = 0
        else:
            BOLD = curses.A_BOLD
        UNDERLINE = curses.A_UNDERLINE

        # default colors

        if default_colors or self.config["default_colors"]:
            self.config.settings.update({
                "color_dim": self.colors["white_on_black"],
                "color_line_numbers": self.colors["black_on_yellow"],
                "color_line_num_reversed": self.colors["white_on_blue"] + BOLD,
                "color_warning": self.colors["white_on_red"] + BOLD,
                "color_normal": self.colors["white_on_black"] + BOLD,
                "color_background": self.colors["white_on_black"] + BOLD,
                "color_message": self.colors["white_on_magenta"] + BOLD,
                "color_reversed": self.colors["white_on_magenta"] + BOLD,
                "color_underline": self.colors["white_on_black"] + UNDERLINE + BOLD,
                "color_commands": self.colors["green_on_black"] + BOLD,
                "color_commands_reversed": self.colors["white_on_green"] + BOLD,
                "color_quote_double": self.colors["yellow_on_black"] + BOLD,
                "color_comment": self.colors["yellow_on_black"],
                "color_comment_block": self.colors["black_on_yellow"],
                "color_comment_separator": self.colors["black_on_red"],
                "color_comment_leftjust": self.colors["white_on_magenta"] + BOLD,
                "color_comment_rightjust": self.colors["white_on_red"] + BOLD,
                "color_comment_centered": self.colors["yellow_on_green"] + BOLD,
                "color_number": self.colors["cyan_on_black"],
                "color_entry": self.colors["white_on_blue"] + BOLD,

                "color_entry_command": self.colors["green_on_blue"] + BOLD,
                "color_entry_quote": self.colors["yellow_on_blue"] + BOLD,
                "color_entry_quote_triple": self.colors["red_on_blue"] + BOLD,
                "color_entry_comment": self.colors["red_on_blue"] + BOLD,
                "color_entry_functions": self.colors["magenta_on_blue"] + BOLD,
                "color_entry_class": self.colors["cyan_on_blue"] + BOLD,
                "color_entry_number": self.colors["cyan_on_blue"] + BOLD,
                "color_entry_dim": self.colors["white_on_blue"],

                "color_operator": self.colors["white_on_black"],
                "color_functions": self.colors["magenta_on_black"] + BOLD,
                "color_functions_reversed": self.colors["white_on_magenta"] + BOLD,
                "color_class": self.colors["blue_on_black"] + BOLD,
                "color_class_reversed": self.colors["white_on_blue"] + BOLD,
                "color_quote_triple": self.colors["red_on_black"],
                "color_mark": self.colors["yellow_on_blue"] + BOLD + UNDERLINE,
                "color_negative": self.colors["red_on_black"] + BOLD,
                "color_entry_negative": self.colors["red_on_blue"] + BOLD,
                "color_positive": self.colors["cyan_on_black"] + BOLD,
                "color_entry_positive": self.colors["cyan_on_blue"] + BOLD,
                "color_tab_odd": self.colors["white_on_black"],
                "color_tab_even": self.colors["yellow_on_black"],
                "color_whitespace": self.colors["black_on_white"] + UNDERLINE,
                "color_header": self.colors["white_on_black"] + BOLD,
                "color_bar": self.colors["white_on_black"],
                "color_constant": self.colors["white_on_black"] + UNDERLINE,
                "color_entry_constant": self.colors["white_on_blue"] + BOLD,
                "color_quote_single": self.colors["yellow_on_black"] + BOLD,
                "color_selection": self.colors["black_on_white"] + UNDERLINE,
                "color_selection_reversed": self.colors["black_on_cyan"] + UNDERLINE,
            })
        self.config["display_color"] = True
