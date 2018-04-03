import os
import time
from copy import deepcopy

from .const import COMMANDS, CHAR_DICT
from .line import Lines
from .console import curses


class Editor:
    def __init__(self, window):
        self.window = window
        self.config = window.config
        self.app = window.app
        self.reset_needed = False
        self.text_entered = False
        self.header = 2
        self.row_size = window.width - 6
        self.print_at_row = window.height - 2
        self.lines = Lines(self)
        self.current_num = 1
        self.save_path = ''
        self.saved_since_edit = True
        self.undo_type = None
        self.undo_list = []
        self.undo_text_que = []
        self.undo_state_que = []
        self.undo_state = []
        self.undo_mark_que = []
        self.undo_mark = []
        self.undo_select = []
        self.undo_select_que = []
        self.program_message = ''
        self.continue_up = 0
        self.continue_down = 0
        self.continue_left = 0
        self.continue_right = 0
        self.last_search = ''
        self.time = time
        self.old_time = time.time()
        self.current_line = self.lines.db.get(1) or self.lines.add()
        self.status = {}

    def print_current_line(self):
        """Prints current line"""
        # global print_at_row, currentNum, current_line, c, startRow
        self.print_at_row = self.window.height - 2

        # collapse_number = 0
        while True:  # This part handles collapsed lines
            try:
                if not self.current_line.collapsed:
                    break  # leave while loop if line not collapsed
                if self.window.c == curses.KEY_DOWN:
                    self.current_num += 1
                else:
                    self.current_num -= 1
                self.current_line = self.lines.db[self.current_num]
            except:
                if self.current_num < 1:
                    self.current_num = 1
                elif self.current_num > self.lines.total:
                    self.current_num = self.lines.total
                break

        try:
            if self.current_line.number_of_rows < self.window.height - 4:
                if self.lines.locked:
                    self.window.addstr((self.print_at_row + 1 - self.current_line.number_of_rows), 0,
                                       str(self.current_line.number),
                                       self.config['color_line_numbers'])  # Prints current line number
                else:
                    self.window.addstr((self.print_at_row + 1 - self.current_line.number_of_rows), 0,
                                       '     ',
                                       self.config['color_line_num_reversed'])  # Prints blank line number block
                    self.window.addstr((self.print_at_row + 1 - self.current_line.number_of_rows), 0,
                                       str(self.current_line.number),
                                       self.config['color_line_num_reversed'])  # Prints current line number

                if self.current_line.selected:
                    self.window.addstr((self.print_at_row + 1 - self.current_line.number_of_rows), 6,
                                       (' ' * (self.window.width - 6)),
                                       self.config['color_selection'])  # Prints selected
                    self.window.addstr((self.print_at_row + 1 - self.current_line.number_of_rows), self.window.width,
                                       '<', self.config['color_quote_double'])  # Prints selected

                if self.current_line.marked and self.current_line.error and self.config['debug']:
                    self.window.hline((self.print_at_row + 1 - self.current_line.number_of_rows), 5, curses.ACS_DIAMOND,
                                      1,
                                      self.config['color_warning'])
                elif self.current_line.error and self.config['debug']:
                    self.window.addstr((self.print_at_row + 1 - self.current_line.number_of_rows), 5, '!',
                                       self.config['color_warning'])  # Prints ERROR

                elif self.current_line.marked and not self.lines.locked:
                    self.window.hline((self.print_at_row + 1 - self.current_line.number_of_rows), 5, curses.ACS_DIAMOND,
                                      1,
                                      self.config['color_quote_double'])
        except:
            pass

        if self.config['live_syntax'] and self.current_line.number_of_rows < (self.window.height - 4):
            self.current_line.add_syntax()

        if len(self.current_line.row) > self.window.height - 4:
            start = len(self.current_line.row) - 1 + self.current_line.y
            end = max(-1, start - (self.window.height - 4))
        else:
            start = len(self.current_line.row) - 1
            end = - 1
        for i in range(start, end, -1):
            if self.config['entry_highlighting']:
                if self.config['page_guide'] and self.config['page_guide'] > 20 and not self.current_line.selected:
                    self.window.addstr(self.print_at_row, 6, ' ' * self.config['page_guide'],
                                       self.config['color_entry'])  # prints blank line
                else:
                    if self.current_line.selected:
                        self.window.addstr(self.print_at_row, 6, ' ' * self.row_size,
                                           self.config['color_selection_reversed'])  # prints blank line
                    else:
                        self.window.addstr(self.print_at_row, 6, ' ' * self.row_size,
                                           self.config['color_entry'])  # prints blank line

                if self.config['page_guide'] and self.config['page_guide'] <= 20:
                    self.window.vline(self.print_at_row, (self.config['page_guide'] + 6), curses.ACS_VLINE, 1,
                                      self.config['color_entry'])  # prints vertical line
            else:
                if self.config['page_guide']:
                    self.window.vline(self.print_at_row, (self.config['page_guide'] + 6), curses.ACS_VLINE, 1,
                                      self.config['color_bar'])  # prints vertical line

            if self.current_line.selected:
                self.window.addstr(self.print_at_row, 6, self.current_line.row[i],
                                   self.config['color_selection_reversed'])  # Prints current line
                self.window.addstr(self.print_at_row, self.window.width, '<',
                                   self.config['color_quote_double'])  # Prints selected
            elif self.config['syntax_highlighting'] and self.config['live_syntax'] and \
                    self.current_line.number_of_rows < (self.window.height - 4):
                temp_list = self.current_line.syntax[i]
                self.print_syntax(temp_list, 6, self.print_at_row, False, True)
            elif self.config['entry_highlighting']:
                self.window.addstr(self.print_at_row, 6, self.current_line.row[i],
                                   self.config['color_entry'])  # Added to fix bug
            else:
                self.window.addstr(self.print_at_row, 6, self.current_line.row[i],
                                   self.config['color_normal'])  # Prints current line

            self.print_at_row -= 1

            if self.print_at_row < 2:
                self.print_at_row = 2
        if len(self.current_line.row) > self.window.height - 4 and start > (self.window.height - 5):
            for r in range(3, self.window.height - 2):  # print vertical line
                self.window.hline(r, 2, curses.ACS_VLINE, 1, self.config['color_quote_triple'])
            self.window.hline(4, 2, curses.ACS_UARROW, 1, self.config['color_quote_triple'])
            if self.current_line.y != 0:
                self.window.hline(self.window.height - 2, 2, curses.ACS_DARROW, 1, self.config['color_quote_triple'])
            else:
                self.window.hline(self.window.height - 2, 2, curses.ACS_DIAMOND, 1, self.config['color_commands'])
            self.window.addstr(3, 0, '    ', self.config['color_entry'])  # Prints blank line number block
            self.window.addstr(3, 0, str(self.current_line.number),
                               self.config['color_line_num_reversed'])  # Prints current line number
            self.window.addstr(3, 6, '. . . ', self.config['color_line_num_reversed'])
        elif len(self.current_line.row) > self.window.height - 4:  # print vertical line
            for r in range(self.print_at_row + 1, self.window.height - 2):
                self.window.hline(r, 2, curses.ACS_VLINE, 1, self.config['color_quote_triple'])
            self.window.hline(self.window.height - 2, 2, curses.ACS_DARROW, 1, self.config['color_quote_triple'])
            self.window.addstr(self.print_at_row + 1, 0, '    ',
                               self.config['color_line_num_reversed'])  # Prints blank line number block
            self.window.addstr(self.print_at_row + 1, 0, str(self.current_line.number),
                               self.config['color_line_num_reversed'])  # Prints current line number

    def formatted_comments(self, text):
        """Returns formatted text based on comment type"""
        if not text or len(text) > self.row_size + 1 or text[0].strip() != '#':
            return False
        stripped_text = text.strip('#')
        if self.config['page_guide'] and self.config['page_guide'] > 20:
            comment_width = self.config['page_guide']
        else:
            comment_width = self.row_size  # changed from ROWSIZE - 1

        if stripped_text == '':
            temp_text = ' ' * comment_width
            return temp_text
        elif len(stripped_text) == 1:
            temp_text = stripped_text * comment_width
            return temp_text
        elif stripped_text.upper() == 'DEBUG':
            text = '**DEBUG**'
            temp_text = text.rjust(comment_width)
            return temp_text
        else:
            try:
                if text[2] != '#' and text[-1] != '#':
                    comment_type = 'LEFT'
                elif text[-1] != '#':
                    comment_type = 'RIGHT'
                elif text[-1] == '#':
                    comment_type = 'CENTER'
                else:
                    comment_type = 'LEFT'
            except:
                comment_type = 'LEFT'
            # New formatting options
            if comment_type == 'LEFT':
                temp_text = stripped_text.ljust(comment_width)
                return temp_text
            elif comment_type == 'CENTER':
                temp_text = stripped_text.center(comment_width)
                return temp_text
            elif comment_type == 'RIGHT':
                temp_text = stripped_text.rjust(comment_width)
                return temp_text

    def print_syntax(self, temp_list, x=6, y=0, collapsed=False, entry_line=False):
        """Prints a line of code with syntax highlighting"""
        y = y or self.window.height - 2
        # global print_at_row
        command = False
        comment = False
        double_quote = False
        single_quote = False
        triple_quote = False
        space = False
        indent = False
        number_char = False
        operator = False
        func = False
        separator = False
        marked = False
        first_printed = False
        my_class = False
        negative = False
        positive = False
        constant = False
        indent_num = 0
        if self.config['live_syntax'] and entry_line and not self.lines.locked:
            real_time = True
            complete_string = ''
            for txt in temp_list:
                complete_string += txt

        else:
            real_time = False

        # if self.config['inline_commands'] == 'protected':
        #     p_string = self.config['protect_string']
        #     p_len = len(p_string)
        # else:
        #     p_string = ''
        #     p_len = 0

        item_string = ''

        for item in temp_list:
            item_string += item
            # Highlighting commands is now handled by different part of program!
            # try:
            if self.config['format_comments'] and item == '_!SEP!_' and not real_time:
                comment_string = ''
                for t in temp_list:
                    comment_string += t
                comment_string = comment_string.replace('_!SEP!_', '')
                comment_string = comment_string.replace('_!SPA!_', '')
                comment_string = comment_string.replace('_!MAR!_', '')
                comment_string = comment_string.replace('_!MOF!_', '')
                comment_string = comment_string.replace('_!IND!_', '')
                if comment_string[0:2] == '##' and self.formatted_comments(comment_string):
                    formatted_text = self.formatted_comments(comment_string)
                    if formatted_text.strip() == '**DEBUG**':
                        self.window.addstr(y, x, formatted_text, self.config['color_warning'])
                    elif comment_string[-1] == '#':  # centered
                        self.window.addstr(y, x, formatted_text, self.config['color_comment_centered'])
                    elif comment_string[0:3] == '###' and len(comment_string.replace('#', '')) > 1:  # right justified
                        self.window.addstr(y, x, formatted_text, self.config['color_comment_rightjust'])
                    elif len(comment_string.replace('#', '')) == 1:  # separator
                        self.window.addstr(y, x, formatted_text, self.config['color_comment_separator'])
                    else:
                        self.window.addstr(y, x, formatted_text, self.config['color_comment_leftjust'])
                    return

                else:
                    if '##' in comment_string:
                        comment_text = comment_string[comment_string.find('##') + 2:]
                    else:
                        comment_text = comment_string
                    self.window.addstr(y, x, comment_text, self.config['color_comment_block'])
                    return

            # except:
            # pass

            if item == '_!MAR!_':
                marked = True
            elif item == '_!SPA!_':
                space = True
            elif item == '_!MOF!_':
                marked = False
            elif item == '_!IND!_':
                indent = True
                indent_num += 1
            elif item == '_!FUN!_':
                func = True
            elif item == '_!CLA!_':
                my_class = True
            elif item == '_!FOF!_':
                func = False
                my_class = False
            elif item == '_!CMD!_':
                command = True
            elif item == '_!NOC!_':
                command = False
                first_printed = True
            elif item == '_!SEP!_':
                separator = True
            elif item == '_!CMT!_':
                comment = True
            elif item == '_!NUM!_':
                number_char = True
            elif item == '_!NEG!_':
                negative = True
            elif item == '_!NEO!_':
                negative = False
            elif item == '_!POS!_':
                positive = True
            elif item == '_!POO!_':
                positive = False
            elif item == '_!CON!_':
                constant = True
            elif item == '_!COO!_':
                constant = False
            elif item == '_!OPE!_':
                operator = True
            elif item == '_!NOF!_':
                number_char = False
            elif item == '_!OOF!_':
                operator = False
            elif item == '_!TQT!_':
                triple_quote = True
            elif item == '_!DQT!_':
                double_quote = True
            elif item == '_!SQT!_':
                single_quote = True
            elif item == '_!OFF!_':
                double_quote = False
                single_quote = False
                triple_quote = False

            elif marked:
                self.window.addstr(y, x, item, self.config['color_mark'])
                x += len(item)

            elif self.lines.locked:
                self.window.addstr(y, x, item, self.config['color_normal'])
                x += len(item)

            elif separator:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_comment'])
                    x += len(item)
                elif entry_line:
                    self.window.addstr(y, x, item, self.config['color_comment'])
                    x += len(item)
                else:
                    if self.config['format_comments']:  # fixed this so comment block could be turned off
                        comment_text = item.replace('#', '')
                        self.window.addstr(y, x, comment_text, self.config['color_comment_block'])
                        if item != '#':
                            x += len(item)
                    else:
                        self.window.addstr(y, x, item, self.config['color_comment'])
                        x += len(item)

            elif self.config['showSpaces'] and space:
                self.window.addstr(y, x, self.config.space_char, self.config['color_whitespace'])
                x += len(self.config.space_char)
            elif self.config['showSpaces'] and self.config['show_indent'] and indent:
                self.window.addstr(y, x, '.', self.config['color_whitespace'])
                x += 1
            elif self.config['show_indent'] and indent:
                if real_time and self.config['entry_highlighting']:
                    if self.config.os == 'Linux':
                        self.window.hline(y, x, curses.ACS_BULLET, 1, self.config['color_entry_dim'])
                    else:
                        self.window.addstr(y, x, '.', self.config['color_entry_dim'])
                else:
                    if indent_num > 8:
                        indent_num = 1
                    if indent_num > 4:
                        if self.config.os == 'Linux':
                            self.window.hline(y, x, curses.ACS_BULLET, 1, self.config['color_tab_even'])
                        else:
                            self.window.addstr(y, x, '.', self.config['color_tab_even'])  # Prints 'tab
                    else:
                        if self.config.os == 'Linux':
                            self.window.hline(y, x, curses.ACS_BULLET, 1, self.config['color_tab_odd'])
                        else:
                            self.window.addstr(y, x, '.', self.config['color_tab_odd'])  # Prints 'tab'
                x += 1

            elif func and collapsed:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_functions'])
                else:
                    self.window.addstr(y, x, item, self.config['color_functions_reversed'])
                x += len(item)
            elif func:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_functions'])
                else:
                    self.window.addstr(y, x, item, self.config['color_functions'])
                x += len(item)

            elif my_class and collapsed:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_class'])
                else:
                    self.window.addstr(y, x, item, self.config['color_class_reversed'])
                x += len(item)
            elif my_class:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_class'])
                else:
                    self.window.addstr(y, x, item, self.config['color_class'])
                x += len(item)

            elif command and collapsed and not first_printed:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_command'])
                else:
                    self.window.addstr(y, x, item, self.config['color_commands_reversed'])
                x += len(item)

            elif command:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_command'])
                else:
                    self.window.addstr(y, x, item, self.config['color_commands'])
                x += len(item)

            elif negative:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_negative'])
                else:
                    self.window.addstr(y, x, item, self.config['color_negative'])
                x += len(item)

            elif positive:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_positive'])
                else:
                    self.window.addstr(y, x, item, self.config['color_positive'])
                x += len(item)

            elif constant:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_constant'])
                else:
                    self.window.addstr(y, x, item, self.config['color_constant'])
                x += len(item)

            elif number_char:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_number'])
                else:
                    self.window.addstr(y, x, item, self.config['color_number'])
                x += len(item)
            elif operator:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_dim'])
                else:
                    self.window.addstr(y, x, item, self.config['color_operator'])
                x += len(item)

            elif comment:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_comment'])
                else:
                    self.window.addstr(y, x, item, self.config['color_comment'])
                x += len(item)
            elif triple_quote:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_quote_triple'])
                else:
                    self.window.addstr(y, x, item, self.config['color_quote_triple'])
                x += len(item)
            elif double_quote:
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_quote'])
                else:
                    self.window.addstr(y, x, item, self.config['color_quote_double'])
                x += len(item)

            elif single_quote:  # new bit that separates single and double quotes
                if real_time and self.config['entry_highlighting']:
                    self.window.addstr(y, x, item, self.config['color_entry_quote'])
                else:
                    self.window.addstr(y, x, item, self.config['color_quote_single'])
                x += len(item)

            elif entry_line and self.config['entry_highlighting']:  # Was 'real_time', changed to fix bug
                self.window.addstr(y, x, item, self.config['color_entry'])
                x += len(item)
            else:
                self.window.addstr(y, x, item, self.config['color_normal'])
                x += len(item)

            if item != '_!SPA!_':
                space = False
            if item != '_!IND!_':
                indent = False

    def new_paste(self, clipboard, pos):
        """A new paste algorithm meant to speed up LARGE paste operations. Based on 'load'"""
        # global current_num, program_message
        clipboard_length = len(clipboard)
        count = 0
        part1 = []
        part2 = deepcopy(clipboard)
        part2.reverse()
        part3 = []

        for i in range(1, pos):
            part1.append(self.lines.db[i].text)
        for i in range(pos, len(self.lines.db) + 1):
            part3.append(self.lines.db[i].text)

        temp_lines = part1 + part2 + part3

        del self.lines.db
        self.lines.db = {}

        length = len(temp_lines)

        for string in temp_lines:
            count += 1
            line = self.lines.add(string)
            if self.config['select_on_paste'] and pos - 1 < count < pos + clipboard_length:
                line.selected = True
            if length > 500 and count / 100.0 == int(count / 100.0):
                self.status_message('Rebuilding Document: ', (100 / (length * 1.0 / count)))
            if self.config['syntax_highlighting']:
                line.add_syntax()
            if self.config['debug']:
                self.error_test(line.number)

        if pos <= self.current_num:
            self.current_num = self.current_num + clipboard_length
        if pos > self.lines.total:
            self.current_num = self.lines.total - 1  # fix message bug
        self.program_message = ' Pasted (inserted) %i lines at line %i ' % (clipboard_length, pos)

    def new_delete(self, start, end):
        """A new delete algorithm meant to speed up LARGE delete operations. Based on 'load'"""
        # global current_num
        count = 0
        part1 = []
        part3 = []

        for i in range(1, start):
            part1.append(self.lines.db[i].text)
        for i in range(end + 1, len(self.lines.db) + 1):
            part3.append(self.lines.db[i].text)

        temp_lines = part1 + part3

        del self.lines.db
        self.lines.db = {}

        length = len(temp_lines)
        if length == 0:
            temp_lines = ['']  # Fix bug that occurred when deleting entire selection

        for string in temp_lines:
            count += 1
            line = self.lines.add(string)

            if length > 500 and count / 100.0 == int(count / 100.0):
                self.status_message('Rebuilding Document: ', (100 / (length * 1.0 / count)))

            if self.config['syntax_highlighting']:
                line.add_syntax()
            if self.config['debug']:
                self.error_test(line.number)

        if end < self.current_num:
            self.current_num -= (end - start) + 1
        elif start > self.current_num:
            pass
        else:
            self.current_num = self.lines.total
        if self.current_num > self.lines.total:
            self.current_num = self.lines.total  # fix bug

    @staticmethod
    def item_member(_list, _string):
        """Checks items in list to see if they are in string"""
        for item in _list:
            if item in _string:
                return True
        return False

    def error_test(self, number_of_line):
        """looks for errors in string"""
        # This is version 2. Version 1 worked, but the code was much, much, uglier.
        item = self.lines.db[number_of_line]

        item.equal_continues = False
        item.if_continues = False

        if not item.text:
            return  # don't process if line is empty
        if item.text.strip().startswith('exec '):
            item.error = False
            return

        try:
            if item.text.isspace():
                return  # don't process if line whitespace
            if item.text[item.indentation] == '#':
                return  # don't process if line is commented
            if item.text[item.indentation:].startswith('from'):
                return  # don't process if line begins with from
            if item.text[item.indentation:].startswith('import'):
                return  # don't process if line begins with import
            if item.text[item.indentation:].startswith('return'):
                return  # don't process if line begins with return
            if item.text[item.indentation:].startswith('raise'):
                return  # don't process if line begins with raise
            if item.text[item.indentation:].startswith('except') and item.text.endswith(':'):
                return  # don't process if line begins with except
            if not item.text[item.indentation].isalpha():
                return  # don't process if line begins with '(', '[', '{'
        except:
            pass

        # initialize flags & other variables
        if_status = False
        def_status = False
        class_status = False
        while_status = False
        double_quote = False
        single_quote = False
        triple_quote = False
        equal_status = False
        # return_status = False
        print_status = False
        for_status = False
        # print_num = 0
        paren_num = 0
        bracket_num = 0
        # curly_status = False
        else_status = False
        try_status = False
        except_status = False
        global_status = False
        dual_equality = False
        prev_comma = False

        if item.number > 1 and self.lines.db[item.number - 1].continue_quoting:
            triple_quote = True

        addendum = ('else:', 'try:', 'except:', 'in')
        op_list = ('=', '==', '>=', '<=', '+=', '-=', '(', ')', '()', '[', ']', '{', '}', ':')
        over_list = '+-/*%^<>=:'
        old_word = ''
        old_char = ''

        prev_item = False
        previous_ending = ''

        # Check indentation levels
        try:
            if number_of_line > 1:
                prev_item = self.lines.db[number_of_line - 1]
                if prev_item.text[prev_item.indentation] != '#' and \
                        not prev_item.text.endswith(',') and \
                        not prev_item.text.endswith('\\') and \
                        self.lines.end_colon(prev_item.text) and not triple_quote:
                    if prev_item.indentation >= item.indentation:
                        item.error = 'need additional indentation'
                        return
                elif item.text[item.indentation] != '#' and \
                        prev_item.text[-1] not in (':', '{', ',', '#') and \
                        prev_item.text[prev_item.indentation:prev_item.indentation + 3] not in (
                        'if ', 'def', 'try', 'for') and \
                        prev_item.text[prev_item.indentation:prev_item.indentation + 4] not in (
                        'elif', 'else') and \
                        prev_item.text[prev_item.indentation:prev_item.indentation + 6] not in (
                        'while ', 'except', 'class ') and \
                        not prev_item.text.endswith(',') and not prev_item.text.endswith('\\'):
                    if prev_item.indentation < item.indentation and \
                            not prev_item.text.strip().startswith('#') and not triple_quote:
                        item.error = 'need less indentation'
                        return
                if prev_item.text:
                    previous_ending = prev_item.text[-1]
        except:
            pass

        # check for syntax errors

        if prev_item and prev_item.equal_continues:
            equal_status = True  # This bit allows multi-line equality operations

        if prev_item and prev_item.if_continues:
            if_status = True
        if prev_item and prev_item.text.endswith(','):
            prev_comma = True
        elif prev_item and prev_item.text.endswith('\\'):
            prev_comma = True

        if len(item.text.split()) == 1 and not equal_status:
            temp_word = item.text.split()[0]
            if temp_word and temp_word not in COMMANDS and temp_word not in addendum and \
                    not self.item_member(temp_word, op_list) and \
                    not self.item_member(over_list, temp_word) and \
                    '"""' not in temp_word and not triple_quote and previous_ending != '\\':
                item.error = "check syntax for '%s'" % item.text[0:int(self.window.width / 2) - 2]

        if ', ' in item.text and ' = ' in item.text:  # attempt to stop false error: a, b = c, d
            dual_equality = True

        for word in item.text.split():
            if '"""' in word and "'\"\"\"'" not in word:
                if not triple_quote and word.count('"""') != 2:
                    triple_quote = True
                    continue
                else:
                    triple_quote = False
                    if word[-1] == ':':  # Added this section to fix minor bug
                        if bracket_num < 1:
                            if_status = False
                        def_status = False
                        class_status = False
                        while_status = False
                        for_status = False
                        else_status = False
                        try_status = False
                        except_status = False
                    continue
            elif not single_quote and not double_quote and not triple_quote:
                if word == '#' or word[0] == '#':
                    break
                if word == 'if' or word == 'elif':
                    if_status = True
                elif word == 'def':
                    def_status = True
                elif word == 'class':
                    class_status = True
                elif word == 'while':
                    while_status = True
                elif word == 'print':
                    print_status = True
                # elif word == 'return':
                #     return_status = True
                elif word == 'for':
                    for_status = True
                elif word == 'else' or word == 'else:':
                    else_status = True
                elif word == 'try' or word == 'try:':
                    try_status = True
                elif word == 'except' or word == 'except:':
                    except_status = True
                elif word == 'global':
                    global_status = True

                elif not if_status and not def_status and not class_status and \
                        not while_status and not for_status and not print_status and \
                        not equal_status and old_word and old_word not in COMMANDS and \
                        old_word not in addendum and old_word not in op_list and \
                        word not in op_list and '(' not in word and word != ':' and \
                        ':' not in old_word and ';' not in old_word and paren_num == 0 and \
                        not global_status and '=' not in word and not item.equal_continues and \
                        word[word.count(' ')] != '{' and item.text[-1] != ',' and \
                        not dual_equality and not prev_comma:
                    if ';' in old_word or old_char == ';':
                        item.error = "check syntax for '%s'" % word[0:int(self.window.width / 2) - 2]
                    else:
                        item.error = "check syntax for '%s'" % old_word[0:int(self.window.width / 2) - 2]
            char_so_far = ''
            for char in word:
                char_so_far += char
                if not single_quote and not double_quote and not triple_quote:

                    if if_status and char == '=' and '==' not in word and '!=' not in word and \
                            '>=' not in word and '<=' not in word:
                        item.error = "missing comparison operator, '=='"
                    elif while_status and char == '=' and '==' not in word and '!=' not in word and \
                            '>=' not in word and '<=' not in word:
                        item.error = "missing comparison operator, '=='"
                    elif not if_status and not while_status and char == '=' and '==' in word and \
                            '"=="' not in word and "'=='" not in word and word.count('=') != 3:
                        if prev_item and prev_item.text and prev_item.text[-1] == '\\':
                            pass  # may need to set if_status here (or maybe not... seems to be working)
                        else:
                            item.error = "improper use of comparison operator, '=='"

                    if char == '#':
                        return  # new bit to stop false syntax errors when there isn't a space before comment character
                    if char == "'" and old_char != '\\':
                        single_quote = True
                    elif char == '"' and old_char != '\\':
                        double_quote = True
                    elif char == '(':
                        paren_num += 1
                    elif char == ')':
                        paren_num -= 1

                    elif char == '[':
                        bracket_num += 1
                    elif char == ']':
                        bracket_num -= 1
                    # elif char == '{':
                    #     curly_status = True
                    # elif char == "}":
                    #   equal_status = False  # ????? Looks like an error!

                    elif not if_status and char == '=':
                        equal_status = True
                    elif char == ':':
                        if bracket_num < 1:
                            if_status = False
                        def_status = False
                        class_status = False
                        while_status = False
                        for_status = False
                        else_status = False
                        try_status = False
                        except_status = False
                        # comp_continues = False
                    elif char == ";":
                        print_status = False
                        equal_status = False
                        global_status = False
                else:  # (if quote status)
                    if single_quote and char == "'" and old_char != '\\':
                        single_quote = False
                    elif single_quote and char == "'" and char_so_far.endswith("\\\\'"):
                        single_quote = False
                    elif double_quote and char == '"' and old_char != '\\':
                        double_quote = False
                    elif double_quote and char == '"' and char_so_far.endswith('\\\\"'):
                        double_quote = False
                    # new bits (testing)

                old_char = char
            old_word = word

        if double_quote and not item.text.endswith('\\') and previous_ending != '\\':
            item.error = 'missing double quote'
        elif single_quote and not item.text.endswith('\\') and previous_ending != '\\':
            item.error = 'missing single quote'
        elif if_status or def_status or class_status or while_status or for_status or \
                else_status or try_status or except_status:
            if not item.text.endswith('\\'):
                item.error = "missing end colon, ':'"
            else:
                item.if_continues = True

        elif equal_status and bracket_num >= 0 and item.text[-1] in (',', '\\'):  # equal continues to next line
            item.equal_continues = True
        elif equal_status and paren_num >= 0 and item.text[-1] in (',', '\\'):  # equal continues to next line
            item.equal_continues = True

        elif bracket_num < 0:
            if prev_item and prev_item.text and prev_item.text[-1] in (',', '\\'):
                pass  # No error if prev_item equals ","
            else:
                item.error = "missing lead bracket, '['"
        elif bracket_num > 0:
            if item.text and item.text[-1] in (',', '\\', '['):
                pass  # No error if item ends with ","
            else:
                item.error = "missing end bracket, ']'"
        elif paren_num < 0:
            if prev_item and prev_item.text and prev_item.text[-1] in (',', '\\'):
                pass  # No error if prev_item equals ","
            else:
                item.error = "missing lead parenthesis, '('"
        elif paren_num > 0:
            if item.text and item.text[-1] in (',', '\\', '('):
                pass  # No error if item ends with ","
            else:
                item.error = "missing end parenthesis, ')'"

    def syntax_visible(self):
        """Adds syntax for lines visible on screen only"""  # Added to speed up program
        start = min(self.lines.total, self.current_num + 2)
        end = max(0, self.current_num - self.window.height)

        for i in range(start, end, -1):
            try:
                if self.lines.db[i].number_of_rows < self.window.height - 4:
                    self.lines.db[i].add_syntax()  # changed to further speed up program
            except:
                return

    def syntax_split_screen(self):
        """Adds syntax for lines visible on splitscreen"""  # Added to improve split functionality
        max_row = int(self.window.height / 2 + 1)
        if not self.config['splitscreen']:
            return
        start = max(1, self.config['splitscreen'])
        end = min(self.lines.total, self.config['splitscreen'] + max_row)
        for i in range(start, end + 1):
            try:
                if self.lines.db[i].number_of_rows < self.window.height - 4:
                    self.lines.db[i].add_syntax()  # changed to further speed up program
            except:
                return

    def update_que(self, the_type='UNKNOWN operation'):
        """Updates undo queues"""
        # global undo_list, undo_type, undo_text_que, undo_state_que, undo_mark_que, text_entered, undo_select_que

        self.undo_type = the_type

        self.undo_text_que = []
        self.undo_state_que = []
        self.undo_mark_que = []
        self.undo_select_que = []

        for i in range(1, len(self.lines.db) + 1):
            self.undo_text_que.append(self.lines.db[i].text)
            self.undo_state_que.append(self.lines.db[i].collapsed)
            self.undo_mark_que.append(self.lines.db[i].marked)
            self.undo_select_que.append(self.lines.db[i].selected)
        self.text_entered = False  # reset flag

    def update_undo(self):
        """Updates global undo variables, sets them to undo queues"""
        # global undo_list, undo_type, undo_text_que, undo_state_que, undo_mark_que, undo_mark, undo_state, undo_select_que, undo_select
        self.undo_list = self.undo_text_que
        self.undo_state = self.undo_state_que
        self.undo_mark = self.undo_mark_que
        self.undo_select = self.undo_select_que
        self.undo_text_que = []
        self.undo_state_que = []
        self.undo_mark_que = []
        self.undo_select_que = []

    def get_selected(self):
        """Returns lines selected as text string, and the count

                ex: "4, 10, 20"
        """
        selected_lines = ''
        count = 0
        for i in range(1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if item.selected:
                if selected_lines != '':
                    selected_lines += ','
                selected_lines += str(i)
                count += 1
        if selected_lines:
            return selected_lines, count
        else:
            return False, 0

    def reset_line(self, force=False):
        """Resets/clears line after command execution"""
        if self.reset_needed or force:
            self.current_line.text = ''
            if self.config.get('debug'):
                self.current_line.error = False
            self.current_line.add_syntax()
            self.current_line.x = 6
            self.reset_needed = False
            self.text_entered = ''

    def delete(self, pos, syntax_needed=True):
        """Delete Line"""
        # global current_num, program_message

        if pos < 1:
            pos = 1
        if pos >= self.lines.total:
            self.program_message = ' Last line can not be deleted! '
            return  # Can't delete last item

        temp = self.lines.db[self.lines.total]

        for i in range(pos, self.lines.total - 1):
            _next = i + 1
            mark_status = self.lines.db[_next].marked  # attempt to fix bug where line deletion removes 'marked' status
            self.lines.db[i] = self.lines.db[_next]
            self.lines.db[i].number = i
            self.lines.db[i].marked = mark_status
        del self.lines.db[len(self.lines.db)]
        self.lines.total -= 1
        if pos <= self.current_num:
            self.current_num -= 1  # slight change
        if self.current_num < 1:
            self.current_num = 1

        self.lines.db[self.lines.total] = temp
        self.lines.db[self.lines.total].number = self.lines.total

        # new bit to fix bug, cursor should be at line end, not beginning
        self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x

        if self.config['syntax_highlighting'] and syntax_needed:
            self.syntax_visible()
        if self.config['splitscreen'] and syntax_needed:
            self.syntax_split_screen()
        if self.config['splitscreen'] and self.config['splitscreen'] > 1:
            self.config['splitscreen'] -= 1  # stop bottom half of screen from 'eating' top half after line deletion

    def get_confirmation(self, text=' Are you sure? (y/n) ', any_key=False):
        return self.window.get_confirmation(text, any_key, self.current_line.x, self.current_line.y)

    @staticmethod
    def get_args(text_string, break_char=" ", separator=" ", strip_spaces=True):
        """Function to separate arguments from text string

                Optional arguments:
                    breakChar - character that separates 'command' from arguments
                                default is " "
                    separator - character that separates arguments from one another
                                default is " "
                    stripSpaces - strips spaces from arguments
                                default is True"""
        try:
            text_string = text_string[(text_string.find(break_char) + 1):]  # removes leading "command" at breakpoint

            if separator != ' ' and strip_spaces:
                text_string = text_string.replace(' ', '')  # strips spaces

            if separator:
                arg_list = text_string.split(separator)  # separates arguments
            else:
                arg_list = []
                for item in text_string:
                    arg_list.append(item)  # separates individual characters, if not separator

            if len(arg_list) == 1:
                return arg_list[0]  # if single argument, return argument
            else:
                return arg_list  # if multiple arguments, return list of arguments
        except:
            return False  # return False if error occurs

    def status_message(self, text, number, update_lines=False):
        self.window.status_message(text, number, self.lines.total, update_lines)

    def delete_lines(self, my_text):
        """Function that deletes lines"""
        # global program_message, current_num, saved_since_edit
        self.program_message = ''
        temp_text = my_text
        self.reset_line()
        self.update_que('Delete operation')
        self.update_undo()
        count = 0
        stat_count = 0  # For use with processing/status message
        delete_selection = False

        if temp_text == 'delete':
            selection, item_count = self.get_selected()
            if selection:
                if self.get_confirmation('Delete selection - %s lines? (y/n)' % item_count):
                    temp_text = 'delete %s' % selection
                    delete_selection = True
                else:
                    self.program_message = ' Delete aborted! '
                    return

        try:
            if ',' in temp_text:
                arg_list = self.get_args(temp_text, ' ', ',')
                line_num_list = []
                for t in arg_list:  # count args between 1 and length of line database
                    if 1 <= int(t) <= self.lines.total:
                        count += 1
                        line_num_list.append(int(t))
                if count < 0:
                    count = 0
                if not delete_selection and \
                        not self.get_confirmation('Delete %i lines? (y/n)' % count):  # Print confirmation message
                    self.program_message = ' Delete aborted! '
                    return

                if count > 100 and self.lines.total > 1000 and \
                        self.consecutive_numbers(line_num_list):  # Use new delete (speed optimization)
                    if self.window.width >= 69:
                        temp_message = 'This operation will expand & unmark lines. Continue? (y/n)'
                    else:
                        temp_message = 'Lines will be unmarked. Continue? (y/n)'
                    if self.get_confirmation(temp_message):
                        start = min(line_num_list)
                        end = max(line_num_list)
                        self.new_delete(start, end)
                        if delete_selection:
                            self.program_message = ' Selection deleted (%i lines) ' % count
                        else:
                            self.program_message = ' Deleted %i lines ' % count
                        return
                    else:
                        self.program_message = ' Delete aborted! '
                        return

                for i in range(len(arg_list) - 1, -1, -1):
                    num = int(arg_list[i])
                    stat_count += 1
                    if self.lines.total > 2000 and count >= 49 and \
                            stat_count / 10.0 == int(stat_count / 10.0):  # display processing message
                        self.status_message('Processing: ', (100 / (count * 1.0 / stat_count)))
                    self.delete(num, False)
                self.program_message = ' Deleted %i lines ' % count

            elif '-' in temp_text:
                arg_list = self.get_args(temp_text, ' ', '-')
                start = max(1, int(arg_list[0]))
                end = min(self.lines.total, int(arg_list[1]))
                length = (end - start)
                if start > end:
                    length = -1
                for i in range(end, start - 1, - 1):
                    count += 1
                if not self.get_confirmation('Delete %i lines? (y/n)' % count):
                    self.program_message = ' Delete aborted! '
                    return

                if length > 100 and self.lines.total > 1000:  # Use new delete (speed optimization)
                    if self.window.width >= 69:
                        temp_message = 'This operation will expand & unmark lines. Continue? (y/n)'
                    else:
                        temp_message = 'Lines will be unmarked. Continue? (y/n)'
                    if self.get_confirmation(temp_message):
                        self.new_delete(start, end)
                        self.program_message = ' Deleted %i lines ' % (length + 1)

                        return
                    else:
                        self.program_message = ' Delete aborted! '
                        return

                for i in range(end, start - 1, - 1):
                    stat_count += 1
                    if length > 500 and stat_count / 10.0 == int(stat_count / 10.0):  # display processing message
                        self.status_message('Processing: ', (100 / (length * 1.0 / stat_count)))
                    elif self.lines.total > 2000 and length >= 49 and \
                            stat_count / 10.0 == int(stat_count / 10.0):  # display processing message
                        self.status_message('Processing: ', (100 / (length * 1.0 / stat_count)))
                    self.delete(i, False)
                self.program_message = ' Deleted %i lines ' % (length + 1)
            else:
                arg_list = self.get_args(temp_text)
                if 'str' in str(type(arg_list)):
                    num = int(arg_list)
                else:
                    num = int(arg_list[0])
                if num < 1 or num > self.lines.total:
                    self.program_message = ' Line does not exist, delete failed! '
                    return
                elif num == self.lines.total:
                    self.program_message = ' Last line can not be deleted! '
                    return

                if not delete_selection and not self.get_confirmation('Delete line number %i? (y/n)' % num):
                    self.program_message = ' Delete aborted! '
                    return
                self.delete(num, False)
                self.program_message = ' Deleted line number %i ' % num
            if not self.program_message:
                self.program_message = ' Delete successful '
            self.saved_since_edit = False
            if self.config['syntax_highlighting']:
                self.syntax_visible()
            if self.config['splitscreen'] and self.config['syntax_highlighting']:
                self.syntax_split_screen()

        except:
            self.get_confirmation('Error occurred, nothing deleted!', True)

    @staticmethod
    def consecutive_numbers(num_list):  # Fixes delete bug with non-consecutive selection over 100 lines!
        """Returns true if list of numbers is consecutive"""
        num_list.sort()
        if len(num_list) == 1:
            return True
        for i in range(0, len(num_list)):
            if i != 0 and num_list[i] - num_list[i - 1] != 1:
                return False
        return True

    def insert(self, pos, text='', paste_operation=False):
        """ Insert line"""
        # global saved_since_edit
        self.saved_since_edit = False

        if pos < 1:
            pos = 1
        if pos > self.lines.total:
            pos = self.lines.total

        temp = self.lines.db[self.lines.total]
        a = self.lines.add(text)
        a.check_executable()

        if paste_operation and self.config['select_on_paste']:
            a.selected = True

        if self.config['syntax_highlighting']:
            a.add_syntax()  # changed/added to try to increase operation speed
        if self.config['debug']:
            self.error_test(a.number)

        for i in range(self.lines.total - 1, pos, -1):
            prev = i - 1
            self.lines.db[i] = self.lines.db[prev]
            self.lines.db[i].number = i
        self.lines.db[pos] = a
        self.lines.db[pos].number = pos

        self.lines.db[self.lines.total] = temp
        self.lines.db[self.lines.total].number = self.lines.total

    def split_line(self, pos, first_part, second_part):
        """Splits lines at position"""
        # global current_num, current_line, saved_since_edit
        self.saved_since_edit = False

        mark_status = self.lines.db[pos].marked  # attempt to fix 'mark' bug
        select_status = self.lines.db[pos].selected  # attempt to fix 'select' bug
        self.insert(pos)
        self.lines.db[pos].text = first_part
        self.lines.db[pos + 1].text = second_part
        self.lines.db[pos].marked = mark_status  # attempt to fix 'mark' bug
        self.lines.db[pos + 1].marked = False  # attempt to fix 'mark' bug

        self.lines.db[pos].selected = select_status  # attempt to fix 'select' bug
        self.lines.db[pos + 1].selected = False  # attempt to fix 'select' bug

        self.lines.db[pos].calc_cursor()  # This added to fix bug where cursor position (end_x) was incorrect
        self.lines.db[pos + 1].calc_cursor()

        self.current_num += 1
        self.lines.db[pos + 1].y = self.lines.db[pos + 1].end_y
        self.lines.db[pos + 1].x = 6

        if self.config['syntax_highlighting']:
            self.syntax_visible()

    def combine_lines(self, pos, first_part, second_part):
        """Combines lines at position"""
        # global current_num, current_line

        if self.lines.db[pos].marked or self.lines.db[pos - 1].marked:
            mark_status = True  # attempt to fix 'mark' bug
        else:
            mark_status = False

        part1rows = self.lines.db[pos - 1].number_of_rows
        temp_x = self.lines.db[pos - 1].end_x
        self.lines.db[pos - 1].text = first_part + second_part
        self.delete(pos)
        temp_y = self.lines.db[self.current_num].end_y + (part1rows - 1)
        self.lines.db[self.current_num].y = temp_y
        self.lines.db[self.current_num].x = temp_x

        self.lines.db[self.current_num].marked = mark_status  # attempt to fix 'mark' bug

        if self.config['syntax_highlighting']:
            self.syntax_visible()

    def new_doc(self):
        """Deletes current doc from memory and creates empty one"""
        # global program_message, current_num, save_path, saved_since_edit
        # global undo_list, undo_text_que, undo_state_que, undo_state, undo_mark_que, undo_mark
        self.reset_line()
        if not self.saved_since_edit and not self.get_confirmation('Create new file without saving old? (y/n)'):
            return
        if self.config['splitscreen']:
            self.config['splitscreen'] = 1
        try:
            if self.lines.db:
                self.lines.locked = False
                del self.lines.db
                self.lines.db = {}
        except:
            pass
        self.lines.add('')
        self.program_message = ' New file created '
        self.current_num = 1
        self.save_path = ''
        self.saved_since_edit = True
        self.undo_list = []
        self.undo_text_que = []
        self.undo_state_que = []
        self.undo_state = []
        self.undo_mark_que = []
        self.undo_mark = []

    def load(self, file_path, read_only=False):
        """Loads file and creates line objects for each line"""
        # global current_num, program_message, save_path, saved_since_edit, text_edited, prev_line
        # global undo_list, undo_text_que, undo_state_que, undo_state, undo_mark_que, undo_mark
        extension = ''

        if "'" in file_path:
            file_path = file_path.replace("'", '')
        if '"' in file_path:
            file_path = file_path.replace('"', '')
        if '~' in file_path:
            file_path = file_path.replace('~', os.path.expanduser('~'))

        self.reset_line()

        try:
            if os.path.exists(file_path):  # if path exists, attempt to load file
                if not os.access(file_path, os.R_OK):  # Display error message if you don't have read access
                    if self.window.width >= 69:
                        self.get_confirmation("You don't have permission to access this file!", True)
                    else:
                        self.get_confirmation('Access not allowed!', True)
                    self.program_message = ' Load failed! '
                    return
                raw_size = os.path.getsize(file_path) / 1024.00  # get size and convert to kilobytes
                if raw_size > 8000 and not self.get_confirmation('  Excessive file size! Continue? (y/n)  '):
                    self.program_message = ' Load aborted '
                    return

                with open(file_path) as code_file:
                    temp_lines = code_file.readlines()

                encrypted = False
                if not temp_lines:  # stop loading if file is empty
                    self.get_confirmation('Load failed, file empty!', True)
                    self.program_message = ' Load failed! '
                    return
            else:  # Display message if path doesn't exist
                self.get_confirmation('Error - file/path does not exist!', True)
                self.program_message = ' Load failed! '
                return
        except:
            self.get_confirmation('Error - file/path does not exist!', True)
            self.program_message = ' Load failed! '
            return
        try:
            if self.lines.db:
                del self.lines.db
                self.lines.db = {}
        except:
            pass

        if temp_lines[-1] not in ('\n', '\r', ''):
            temp_lines.append('')  # edited to stop multiple empty lines at end of file
        # Set lines to line class
        count = 0
        length = len(temp_lines)

        if read_only:  # adjust settings if read Only
            self.config.copy_settings()

            self.config.settings.update({
                'debug': False,
                'show_indent': False,
                'entry_highlighting': False,
                'syntax_highlighting': True,
                'format_comments': True,
                'live_syntax': True,
                'showSpaces': False,
                'splitscreen': False,
            })

        if self.config['auto'] and not read_only:  # Auto adjust settings based on file format
            if file_path.endswith('.py') or extension == '.py':
                self.config.settings.update({
                    'syntax_highlighting': True,
                    'entry_highlighting': True,
                    'live_syntax': True,
                    'debug': True,
                    'format_comments': True,
                    'show_indent': True,
                    'inline_commands': True,
                })
            else:
                self.config.settings.update({
                    'syntax_highlighting': False,
                    'live_syntax': False,
                    'debug': False,
                    'format_comments': False,
                    'show_indent': False,
                    'show_whitespace': False,
                    'inline_commands': 'protected',  # protect commands with protect string
                })

        if length > 9999:  # Turn off special features if document is huge (speed optimization)
            self.config.settings.update({
                'syntax_highlighting': False,
                'live_syntax': False,
                'debug': False,
            })

        if length > 500:  # Show status message
            self.window.screen.addstr(0, 0, ' ' * (self.window.width - 13), self.config['color_header'])
            self.window.screen.addstr(0, 0, 'Loading...', self.config['color_warning'])
            # new bit to stop random character from appearing
            self.window.screen.addstr(0, self.window.width, ' ', self.config['color_header'])
            self.window.screen.refresh()

        self.current_num = 0
        total_rows = 0
        for string in temp_lines:
            count += 1
            string = string.replace('\t', '    ')
            string = string.replace('    ', '    ')
            string = string.replace('\n', '')
            string = string.replace('\r', '')
            string = string.replace('\f', '')  # form feed character, apparently used as seperator?

            line = self.lines.add(string)

            if count in (1, 2, 3, 10, 100):  # check to see if encoding understood
                try:
                    self.window.screen.addstr(0, 0, line.text[0:self.window.width])  # Tests output
                    self.window.screen.addstr(0, 0, (' ' * self.window.width))  # clears line
                except:
                    self.get_confirmation("Error, can't read file encoding!", True)
                    self.new_doc()
                    return

            if length > 500 and count / 100.0 == int(count / 100.0):
                self.status_message('Loading: ', (100 / (length * 1.0 / count)), True)

            if self.config['syntax_highlighting'] or self.config['debug']:
                line.add_syntax()
                self.error_test(line.number)

            # This part checks number of rows so doc is opened properly in 'read' mode
            total_rows += (line.number_of_rows - 1)
            if line.number <= (self.window.height - 2) and self.current_num + total_rows < (self.window.height - 2):
                self.current_num += 1

        self.current_num -= 1  # adjustment to fix bug
        if self.current_num > (self.window.height - 2):
            self.current_num = (self.window.height - 2)
        if self.current_num < 1:
            self.current_num = 1

        # prev_line = self.current_num

        if self.config['collapse_functions']:
            self.lines.collapse_functions()
        if not encrypted:
            self.program_message = ' File loaded successfully '
            self.save_path = file_path
        else:
            if extension and extension != '.???':
                self.save_path = file_path.replace('.pwe', '') + extension
            else:
                self.save_path = file_path.replace('.pwe', '')
        if "/" not in self.save_path:
            self.save_path = os.path.abspath(self.save_path)
        self.saved_since_edit = True
        if read_only:
            self.lines.locked = True
        else:
            self.current_num = self.lines.total  # goto end of line if not readOnly mode
        self.undo_list = []
        self.undo_text_que = []
        self.undo_state_que = []
        self.undo_state = []
        self.undo_mark_que = []
        self.undo_mark = []

    def save(self, file_path=''):
        """Saves file"""
        # global save_path, program_message, saved_since_edit
        old_path = self.save_path
        try:

            if not file_path:
                file_path = self.window.prompt_user('ENTER FILENAME:', (os.getcwd() + '/'))
                if not file_path:
                    self.program_message = ' Save aborted! '
                    return
            if '~' in file_path: file_path = file_path.replace('~', os.path.expanduser(
                '~'))  # changes tilde to full pathname
            if '/' not in file_path and self.save_path and '/' in self.save_path:
                part1 = os.path.split(self.save_path)[0]
                part2 = file_path
                tempPath = part1 + '/' + part2
                file_path = self.window.prompt_user('Save this file?', tempPath)
                if not file_path:
                    self.program_message = ' Save aborted! '
                    return

            elif '/' not in file_path:
                file_path = os.path.abspath(file_path)
            elif '../' in file_path:
                (fullpath, filename) = os.path.split(self.save_path)
                file_path = os.path.abspath((fullpath + '/' + file_path))

            if os.path.isdir(file_path):  # stop save process if path is directory
                self.get_confirmation(" You can't overwrite a directory! ", True)
                self.program_message = ' Save failed! '
                return

            if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
                self.get_confirmation("Error, file is READ only. Use 'saveas'", True)
                self.program_message = ' Save failed! '
                return

            if file_path != self.save_path and os.path.exists(file_path) and \
                    not self.get_confirmation(' File exists, overwrite? (y/n) '):
                self.program_message = ' Save aborted! '
                return

            self.save_path = file_path
            with open(self.save_path, 'w') as text_file:
                for key in self.lines.db:
                    this_text = (self.lines.db[key].text + '\n')
                    text_file.write(this_text)
            self.program_message = ' File saved successfully '
            self.saved_since_edit = True

        except:
            self.get_confirmation('ERROR - check path, file not saved', True)
            self.program_message = ' Save failed! '
            self.save_path = old_path

    def print_previous_lines(self):
        """Prints previous lines"""
        # global current_num, print_at_row
        collapse_number = 0
        marked = False
        error = False
        # master_indent = 0
        for z in range(self.current_num - 1, 0, -1):
            if self.print_at_row < self.header:
                break

            if self.lines.db[z].number_of_rows > (self.window.height - 4):  # If terminal too small to display line
                self.window.addstr(self.print_at_row, 0, str(self.lines.db[z].number),
                                   self.config['color_line_numbers'])  # Prints line number
                if self.lines.db[z].selected:
                    self.window.addstr(self.print_at_row, self.window.width, '<',
                                       self.config['color_quote_double'])  # Prints selected
                if self.lines.db[z].marked and not self.lines.locked:
                    self.window.hline(self.print_at_row, 5, curses.ACS_DIAMOND, 1,
                                      self.config['color_quote_double'])  # Prints Marked
                if self.lines.db[z].selected:
                    self.window.addstr(self.print_at_row, 6, self.lines.db[z].row[0][0:self.row_size - 4],
                                       self.config['color_selection'])  # Prints Selected Text
                if self.lines.db[z].selected:
                    self.window.addstr(self.print_at_row, 6, self.lines.db[z].row[0][0:self.row_size - 4],
                                       self.config['color_selection'])
                elif self.config['syntax_highlighting']:
                    if not self.lines.db[z].syntax:
                        self.lines.db[z].add_syntax()
                    temp_list = self.lines.db[z].syntax[0]
                    self.print_syntax(temp_list, 6, self.print_at_row, False)
                else:
                    self.window.addstr(self.print_at_row, 6, self.lines.db[z].row[0][0:self.row_size - 4],
                                       self.config['color_normal'])
                self.window.hline(self.print_at_row, self.window.width - 1, curses.ACS_RARROW, 1,
                                  self.config['color_quote_triple'])
                self.window.hline(self.print_at_row, self.window.width - 3, curses.ACS_HLINE, 2,
                                  self.config['color_quote_triple'])
                self.window.addstr(self.print_at_row, self.window.width - 4, ' ', self.config['color_normal'])
                self.print_at_row -= 1
                continue

            if self.lines.db[z].collapsed:
                master_indent = self.lines.db[z].indent_required
                if self.lines.db[z].error:
                    error = True
                if self.lines.db[z].marked:
                    marked = True
                # if self.lines.db[z].selected:
                #     selected = True
                if collapse_number == 0:
                    self.window.hline(self.print_at_row, 7 + master_indent, curses.ACS_LLCORNER, 1,
                                      self.config['color_bar'])
                    self.window.hline(self.print_at_row, 8 + master_indent, curses.ACS_HLINE,
                                      (self.row_size - 14 - master_indent), self.config['color_bar'])
                    self.print_at_row -= 1
                collapse_number += 1

                if self.lines.db[z].selected:
                    self.window.addstr((self.print_at_row + 1), 6, (' ' * (self.window.width - 6)),
                                       self.config['color_selection'])  # Prints selected
                    self.window.addstr((self.print_at_row + 1), self.window.width, '<',
                                       self.config['color_quote_double'])  # Prints selected

                if marked and error and self.config['debug']:
                    self.window.hline((self.print_at_row + 1), 5, curses.ACS_DIAMOND, 1,
                                      self.config['color_warning'])  # Prints both
                elif marked and not self.lines.locked:
                    self.window.hline((self.print_at_row + 1), 5, curses.ACS_DIAMOND, 1,
                                      self.config['color_quote_double'])  # Prints Marked
                elif error and self.config['debug']:
                    self.window.addstr((self.print_at_row + 1), 5, '!', self.config['color_warning'])  # Prints ERROR

                self.window.addstr(self.print_at_row + 1, self.window.width - 10, '%i lines' % collapse_number,
                                   self.config['color_dim'])
                continue
            collapse_number = 0
            marked = False
            error = False

            if self.print_at_row - self.lines.db[z].number_of_rows >= self.header - 1:
                self.window.addstr((self.print_at_row - self.lines.db[z].number_of_rows + 1), 0,
                                   str(self.lines.db[z].number),
                                   self.config['color_line_numbers'])  # Prints line number

                if self.lines.db[z].selected:
                    self.window.addstr((self.print_at_row - self.lines.db[z].number_of_rows + 1), 6,
                                       (' ' * (self.window.width - 6)),
                                       self.config['color_selection'])  # Prints selected
                    self.window.addstr((self.print_at_row - self.lines.db[z].number_of_rows + 1), self.window.width,
                                       '<', self.config['color_quote_double'])  # Prints selected
                if self.lines.db[z].marked and self.lines.db[z].error and self.config['debug']:
                    self.window.hline((self.print_at_row - self.lines.db[z].number_of_rows + 1), 5, curses.ACS_DIAMOND,
                                      1, self.config['color_warning'])

                elif self.lines.db[z].error and self.config['debug']:
                    self.window.addstr((self.print_at_row - self.lines.db[z].number_of_rows + 1), 5, '!',
                                       self.config['color_warning'])  # Prints ERROR

                elif self.lines.db[z].marked and not self.lines.locked:
                    self.window.hline((self.print_at_row - self.lines.db[z].number_of_rows + 1), 5, curses.ACS_DIAMOND,
                                      1, self.config['color_quote_double'])
            else:
                self.window.addstr(2, 0, str(self.lines.db[z].number),
                                   self.config['color_line_numbers'])  # Prints line number

            for i in range(len(self.lines.db[z].row) - 1, -1, -1):
                if self.print_at_row < 2:
                    self.window.hline(2, 5, curses.ACS_LARROW, 1, self.config['color_quote_double'])
                    self.window.hline(2, 6, curses.ACS_HLINE, 2, self.config['color_quote_double'])
                    self.window.addstr(2, 8, ' ', self.config['color_normal'])

                    break  # break out of loop if line is in Header
                if self.lines.db[z].selected:
                    self.window.addstr(self.print_at_row, 6, (' ' * (self.window.width - 6)),
                                       self.config['color_selection'])  # Prints selected
                    self.window.addstr(self.print_at_row, 6, self.lines.db[z].row[i],
                                       self.config['color_selection'])  # Prints Selected Text
                    self.window.addstr(self.print_at_row, self.window.width, '<',
                                       self.config['color_quote_double'])  # Prints selected
                elif self.config['syntax_highlighting']:
                    if not self.lines.db[z].syntax:
                        self.lines.db[z].add_syntax()
                    temp_list = self.lines.db[z].syntax[i]
                    try:
                        status = self.lines.db[z + 1].collapsed
                    except:
                        status = False
                    self.print_syntax(temp_list, 6, self.print_at_row, status)
                else:
                    self.window.addstr(self.print_at_row, 6, self.lines.db[z].row[i], self.config['color_normal'])

                self.print_at_row -= 1

    def print_next_line(self):
        """Prints line after current line, if applicable"""
        if self.current_num == self.lines.total:
            return

        try:
            if self.lines.db[self.current_num + 1].selected:
                self.window.addstr((self.window.height - 1), 6,
                                   (' ' * (self.window.width - 6)), self.config['color_selection'])  # Prints selected
                self.window.addstr((self.window.height - 1), self.window.width,
                                   '<', self.config['color_quote_double'])  # Prints selected
                next_line = self.lines.db[self.current_num + 1].row[0]
                self.window.addstr(self.window.height - 1, 6,
                                   next_line, self.config['color_selection'])  # Prints next line
            elif self.config['syntax_highlighting']:
                if not self.lines.db[self.current_num + 1].syntax:
                    self.lines.db[self.current_num + 1].add_syntax()
                temp_list = self.lines.db[self.current_num + 1].syntax[0]
                self.print_syntax(temp_list, 6, self.window.height - 1)
            else:
                next_line = self.lines.db[self.current_num + 1].row[0]
                self.window.addstr(self.window.height - 1, 6,
                                   next_line, self.config['color_normal'])  # Prints next line
            if self.lines.db[self.current_num + 1].length > self.row_size and \
                    self.lines.db[self.current_num + 1].number_of_rows > (self.window.height - 4):
                self.window.addstr(self.window.height - 1, self.window.width - 4, ' ', self.config['color_normal'])
                self.window.hline(self.window.height - 1, self.window.width - 3,
                                  curses.ACS_HLINE, 2, self.config['color_quote_triple'])
                self.window.hline(self.window.height - 1, self.window.width - 1,
                                  curses.ACS_RARROW, 1, self.config['color_quote_triple'])
            elif self.lines.db[self.current_num + 1].length > self.row_size:
                self.window.addstr(self.window.height - 1, self.window.width - 4, ' ', self.config['color_normal'])
                self.window.hline(self.window.height - 1, self.window.width - 3,
                                  curses.ACS_HLINE, 2, self.config['color_quote_double'])
                self.window.hline(self.window.height - 1, self.window.width - 1,
                                  curses.ACS_RARROW, 1, self.config['color_quote_double'])

            self.window.addstr(self.window.height - 1, 0, str(self.lines.db[self.current_num + 1].number),
                               self.config['color_line_numbers'])  # Prints next line numbers

            if self.lines.db[self.current_num + 1].marked and \
                    self.lines.db[self.current_num + 1].error and self.config['debug']:
                self.window.hline(self.window.height - 1, 5,
                                  curses.ACS_DIAMOND, 1, self.config['color_warning'])  # MARKED

            elif self.lines.db[self.current_num + 1].error and self.config['debug']:
                self.window.addstr(self.window.height - 1, 5, '!', self.config['color_warning'])  # Prints ERROR

            elif self.lines.db[self.current_num + 1].marked and not self.lines.locked:
                self.window.hline(self.window.height - 1, 5, curses.ACS_DIAMOND, 1,
                                  self.config['color_quote_double'])  # MARKED
        except:
            pass

        if self.current_num > self.lines.total - 2:
            return  # This is a temp line, for debug purposes

        try:
            if self.lines.db[self.current_num + 2].selected:
                self.window.addstr(self.window.height, 6, (' ' * (self.window.width - 6)),
                                   self.config['color_selection'])  # Prints selected
                self.window.vline(self.window.height, self.window.width, '<', 1,
                                  self.config['color_quote_double'])  # prints vertical line
                next_line = self.lines.db[self.current_num + 2].row[0]
                self.window.addstr(self.window.height, 6, next_line, self.config['color_selection'])  # Prints next line
            elif self.config['syntax_highlighting']:
                if not self.lines.db[self.current_num + 2].syntax:
                    self.lines.db[self.current_num + 2].add_syntax()
                temp_list = self.lines.db[self.current_num + 2].syntax[0]
                self.print_syntax(temp_list, 6, self.window.height)
            else:
                next_line = self.lines.db[self.current_num + 2].row[0]
                self.window.addstr(self.window.height, 6, next_line, self.config['color_normal'])  # Prints next line
            if self.lines.db[self.current_num + 2].length > self.row_size and \
                    self.lines.db[self.current_num + 2].number_of_rows > (self.window.height - 4):
                self.window.addstr(self.window.height, self.window.width - 4, ' ', self.config['color_normal'])
                self.window.hline(self.window.height, self.window.width - 3, curses.ACS_HLINE, 2,
                                  self.config['color_quote_triple'])
                self.window.hline(self.window.height, self.window.width - 1, curses.ACS_RARROW, 1,
                                  self.config['color_quote_triple'])
            elif self.lines.db[self.current_num + 2].length > self.row_size:
                self.window.addstr(self.window.height, self.window.width - 4, ' ', self.config['color_normal'])
                self.window.hline(self.window.height, self.window.width - 3, curses.ACS_HLINE, 2,
                                  self.config['color_quote_double'])
                self.window.hline(self.window.height, self.window.width - 1, curses.ACS_RARROW, 1,
                                  self.config['color_quote_double'])

            self.window.addstr(self.window.height, 0, str(self.lines.db[self.current_num + 2].number),
                               self.config['color_line_numbers'])  # Prints next line numbers
            if self.lines.db[self.current_num + 2].marked and \
                    self.lines.db[self.current_num + 2].error and self.config['debug']:
                self.window.hline(self.window.height, 5, curses.ACS_DIAMOND, 1,
                                  self.config['color_warning'])  # MARKED and ERROR
            elif self.lines.db[self.current_num + 2].error and self.config['debug']:
                self.window.addstr(self.window.height, 5, '!', self.config['color_warning'])  # Prints ERROR
            elif self.lines.db[self.current_num + 2].marked and not self.lines.locked:
                self.window.hline(self.window.height, 5, curses.ACS_DIAMOND, 1,
                                  self.config['color_quote_double'])  # MARKED
        except:
            pass

    def move_up(self):
        """program specific function that moves up one line"""
        # global current_num, program_message, saved_since_edit, continue_down, continue_up

        self.program_message = ''
        self.continue_down = 0
        self.continue_left = 0
        self.continue_right = 0

        if self.config['syntax_highlighting']:
            self.lines.db[self.current_num].add_syntax()  # update syntax BEFORE leaving line

        if self.current_line.text and self.current_line.number == self.lines.total:
            self.lines.add()  # create emtpy line

        if self.text_entered:
            self.update_undo()
            self.update_que('text entry')
            self.saved_since_edit = False

        if self.current_line.number_of_rows > 1 and self.current_line.y == 0 and \
                self.current_line.x == self.current_line.end_x and not self.lines.locked:
            self.current_num -= 1
            if self.current_num < 1:
                self.current_num = 1
            self.lines.db[self.current_num].y = 0
            self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
        elif self.current_line.number_of_rows > 1 and \
                self.current_line.y > self.current_line.end_y:  # deal with large lines
            prev_y = self.current_line.y
            if self.current_line.x >= 6:
                self.current_line.y -= 1
            if prev_y == 0 and self.current_line.x == self.current_line.end_x:
                self.current_line.x = self.window.width - 1
        else:  # deal with normal lines
            if self.config['cursor_acceleration']:
                move_rate = min(self.config['cursor_max_vertical_speed'], int(self.continue_up / 10.0) + 1)
            else:
                move_rate = 1
            self.current_num -= move_rate
            self.continue_up += 1

            if self.current_num < 1:
                self.current_num = 1

            self.lines.db[self.current_num].y = 0
            self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x

        if self.config['syntax_highlighting']:
            self.lines.db[self.current_num].add_syntax()  # added to speed up program
        if self.config['debug']:
            self.debug_visible()

    def move_down(self):
        """program specific function that moves down one line"""
        # global current_num, program_message, saved_since_edit, continue_down, continue_up
        self.program_message = ''
        self.continue_up = 0
        self.continue_left = 0
        self.continue_right = 0
        if self.config['syntax_highlighting']:
            self.lines.db[self.current_num].add_syntax()  # update syntax BEFORE leaving line

        if self.current_line.text and self.current_line.number == self.lines.total:
            self.lines.add()  # create emtpy line

        if self.text_entered:
            self.update_undo()
            self.update_que('text entry')
            self.saved_since_edit = False

        if self.current_line.number_of_rows > 1 and self.current_line.y != 0:  # deal with large lines
            prev_y = self.current_line.y
            prev_x = self.current_line.x
            self.current_line.y += 1
            if self.current_line.y == 0 and prev_x == self.window.height - 1:
                self.current_line.x = self.current_line.end_x
            elif self.current_line.y == 0 and prev_x > self.current_line.end_x:
                self.current_line.x = self.current_line.end_x
            elif prev_y == self.current_line.end_y and self.current_line.x == self.window.width - 1:
                self.current_line.x = self.window.width - 1

        else:  # deal with normal lines
            if self.config['cursor_acceleration']:
                move_rate = min(self.config['cursor_max_vertical_speed'], int(self.continue_down / 10.0) + 1)
            else:
                move_rate = 1
            self.current_num += move_rate
            self.continue_down += 1

            if self.current_num > self.lines.total:
                self.current_num = self.lines.total

            if self.lines.db[self.current_num].number_of_rows > (self.window.height - 4) and self.lines.locked:
                self.lines.db[self.current_num].y = self.lines.db[self.current_num].end_y + (self.window.height - 5)
            elif self.current_line.y != 0:
                self.lines.db[self.current_num].y = self.lines.db[self.current_num].end_y  # changed
                self.lines.db[self.current_num].x = self.window.width - 1
            else:
                self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
                self.lines.db[self.current_num].y = 0

        if self.config['syntax_highlighting']:
            self.lines.db[self.current_num].add_syntax()  # added to speed up program
        if self.config['debug']:
            self.debug_visible()

    def move_left(self):
        """program specific function that moves left one space"""
        # global continue_up, continue_down, continue_right, continue_left
        self.continue_up = 0
        self.continue_down = 0
        self.continue_right = 0
        if self.current_line.text and self.current_line.number == self.lines.total:
            self.lines.add()  # create emtpy line

        try:  # if tab, move 4 spaces
            if self.current_line.x - 6 <= self.current_line.indentation and \
                    self.current_line.text[self.current_line.x - 6 - 4:self.current_line.x - 6] == '    ' and \
                    self.current_line.y == self.current_line.end_y:
                self.current_line.x -= 4
                return
        except:
            pass
        if self.config['cursor_acceleration']:
            move_rate = min(self.config['cursor_max_horizontal_speed'], int(self.continue_left / 10.0) + 1)
        else:
            move_rate = 1
        self.continue_left += 1
        self.current_line.x -= move_rate

    def move_right(self):
        """program specific function that moves right one space"""
        # global continue_up, continue_down, continue_right, continue_left
        self.continue_up = 0
        self.continue_down = 0
        self.continue_left = 0
        if self.current_line.text and self.current_line.number == self.lines.total:
            self.lines.add()  # create emtpy line

        try:  # if tab, move 4 spaces
            if self.current_line.x - 6 < self.current_line.indentation and \
                    self.current_line.text[self.current_line.x - 6:self.current_line.x - 6 + 4] == '    ' and \
                    self.current_line.y == self.current_line.end_y:
                self.current_line.x += 4
                return
        except:
            pass

        if self.config['cursor_acceleration']:
            move_rate = min(self.config['cursor_max_horizontal_speed'], int(self.continue_right / 10.0) + 1)
        else:
            move_rate = 1
        self.continue_right += 1
        self.current_line.x += move_rate

    def page_up(self):
        """program specific function that moves up one page"""
        # global current_num, program_message, saved_since_edit, continue_down, continue_up, continue_left, continue_right

        self.program_message = ''
        self.continue_down = 0
        self.continue_left = 0
        self.continue_right = 0
        self.continue_up = 0

        if self.config['syntax_highlighting']:
            self.lines.db[self.current_num].add_syntax()  # update syntax BEFORE leaving line
        self.current_num = max((self.current_num - (self.window.height - 1)), 1)

    def page_down(self):
        """program specific function that moves down one page"""
        # global current_num, program_message, saved_since_edit, continue_down, continue_up, continue_left, continue_right

        self.program_message = ''
        self.continue_down = 0
        self.continue_left = 0
        self.continue_right = 0
        self.continue_up = 0

        if self.config['syntax_highlighting']:
            self.lines.db[self.current_num].add_syntax()  # update syntax BEFORE leaving line
        self.current_num = min((self.current_num + (self.window.height - 1)), self.lines.total)

    def print_header(self):
        self.window.print_header(
            save_info=self.saved_since_edit and '*' or '',
            message=self.program_message,
            save_path=self.save_path,
            total=self.lines.total,
        )

    def debug_visible(self):
        """Debugs lines visible on screen only"""  # Added to speed up program
        start = min(self.lines.total, self.current_num + 2)
        end = max(1, self.current_num - self.window.height)

        for i in range(start, end, -1):
            self.lines.db[i].error = False
            self.error_test(self.lines.db[i].number)

    def add_character(self, char):
        """program specific function that adds character to line"""
        # global current_line, text_entered, program_message, saved_since_edit, continue_down, continue_up
        self.continue_down = 0
        self.continue_up = 0
        # if len(current_line.text) > 4: saved_since_edit = False # Updated so 'new', 'run', 'save', or 'load' won't count as an edit.
        self.program_message = ""

        if not self.text_entered:
            self.text_entered = True

        old_number_of_rows = self.current_line.number_of_rows
        old_x = self.current_line.x
        temp_list = self.current_line.listing
        if self.current_line.y == 0 and self.current_line.x == self.current_line.end_x:
            temp_list.append(char)
        else:
            position = self.row_size * (
                    self.current_line.number_of_rows - 1 - abs(self.current_line.y)) + self.current_line.x - 6
            temp_list.insert(position, char)
        temp_string = ""
        for item in temp_list:
            temp_string += item
        self.current_line.text = temp_string
        self.current_line.x += 1

        if self.config["live_syntax"] and \
                self.current_line.number_of_rows < (self.window.height - 4):
            self.current_line.add_syntax()  # added 'live' check to speed up program
        if old_number_of_rows != self.current_line.number_of_rows:
            if self.current_line.y != 0: self.current_line.y -= 1
            if self.current_line.y == 0:
                self.current_line.y -= 1
                self.current_line.x = old_x + 1

    def key_backspace(self):
        """This function determines what happens when delete/backspace key pressed"""
        # global current_line, current_num, saved_since_edit, text_entered, continue_up, continue_down
        self.continue_down = 0
        self.continue_up = 0
        self.saved_since_edit = False
        if not self.text_entered and len(self.current_line.text) > 4:
            self.text_entered = True

        if not self.current_line.text and self.current_line.number == self.lines.total:
            self.lines.add()  # create emtpy line

        if not self.lines.db[self.current_num].text:  # delete line if empty
            self.delete(self.current_num)
            self.text_entered = True
            return

        if (self.current_num - 1) in self.lines.db and \
                self.lines.db[self.current_num].text and self.current_line.x == 6 and \
                self.current_line.y == self.current_line.end_y:  # end_y added to fix bug
            part1 = self.lines.db[self.current_num - 1].text
            part2 = self.lines.db[self.current_num].text
            self.combine_lines(self.current_num, part1, part2)
            self.text_entered = True
            return

        old_number_of_rows = self.current_line.number_of_rows
        temp_list = self.current_line.listing

        if self.current_line.y == 0 and self.current_line.x == self.current_line.end_x:  # delete last character on line
            del temp_list[-1]
        else:
            position = self.row_size * (self.current_line.number_of_rows - 1 - abs(self.current_line.y)) + self.current_line.x - 6
            try:
                if position <= self.current_line.indentation and \
                        self.current_line.text[position - 3:position + 1] and \
                        self.current_line.indentation / 4.0 == int(self.current_line.indentation / 4.0):  # delete tab
                    del temp_list[position - 4:position]
                    self.current_line.x -= 3  # move cursor position 3 spaces, final one below
                else:
                    del temp_list[position - 1]  # delete position
            except:
                del temp_list[position - 1]  # delete position

        temp_string = ""
        for item in temp_list:
            temp_string += item
        self.current_line.text = temp_string
        self.current_line.x -= 1
        if self.config["syntax_highlighting"]:
            self.current_line.add_syntax()
        if old_number_of_rows != self.current_line.number_of_rows:
            self.current_line.y += 1
            if self.current_line.number_of_rows == 1 and self.current_line.x == 6:
                self.current_line.x = self.current_line.end_x

    def run_editor(self):
        while True:
            # try:
            if self.app.break_now:
                break  # exit main loop, exit program
            self.current_line = self.lines.db[self.current_num]
            self.window.clear()
            if self.config['color_background']:
                self.window.print_background()
            if self.config['color_line_numbers']:
                self.window.draw_line_number_background()
            if self.lines.locked:
                self.program_message = " READ ONLY MODE. Press 'q' to quit. "
            self.print_header()
            if self.config['page_guide'] and self.window.width > (self.config['page_guide'] + 6):
                self.window.draw_page_guide()
            self.print_current_line()
            self.print_previous_lines()
            self.print_next_line()
            if self.config['inline_commands'] and self.config['highlight_commands'] and self.current_line.executable:
                print_command()

            if self.config['inline_commands'] == 'protected':  # set protect variables
                pr_str = str(self.config['protect_string'])
                pr_len = len(pr_str)
            else:
                pr_str = ''
                pr_len = 0

            if self.config['splitscreen']:
                split_screen()

            if self.config['debug'] and self.current_line.error and not self.program_message:  # Print error messages
                self.window.addstr(0, 0, ' ' * (self.window.width - 13), self.config['color_header'])
                self.window.addstr(0, 0, ' ERROR: %s ' % self.current_line.error, self.config['color_warning'])

            # Debugging
            # stdscr.addstr(0, 0, " KEYPRESS: %i              " %(c), settings["color_warning"])
            # if c == ord("\\"): print non_existent_variable ##force program to crash

            # Moves cursor to correct location
            if self.lines.locked:
                self.window.addstr(self.window.height, self.window.width, '',
                                   self.config['color_normal'])  # moves cursor
            elif self.current_line.number_of_rows > self.window.height - 4:
                self.window.addstr(self.window.height - 2, self.current_line.x, '',
                                   self.config['color_normal'])  # moves cursor
            else:
                self.window.addstr(self.current_line.y + self.window.height - 2, self.current_line.x, '',
                                   self.config['color_normal'])  # moves cursor

            self.window.refresh()

            # Get key presses
            c = self.window.getch()

            if self.lines.locked and c == 10:
                c = self.window.c = curses.KEY_DOWN  # Convert 'enter' to down arrow if document is 'locked'
            elif self.lines.locked and c in (ord('q'), ord('Q')) and \
                    self.get_confirmation('Close current document? (y/n)'):
                self.config.copy_settings(True)
                self.new_doc()
                continue
            elif self.lines.locked and c == ord('s'):
                self.current_num = 1
            elif self.lines.locked and c == ord('e'):
                self.current_num = self.lines.total

            self.reset_needed = True  # Trying to fix bug where commands aren't properly cleared
            if c == 10 and command_match(self.current_line.text, 'collapse off', 'expand all'):
                self.current_line.text = ''
                self.current_line.add_syntax()
                # settings['collapse_functions'] = False
                self.lines.expand_all()
                self.reset_line()

            elif c == 10 and command_match(self.current_line.text, 'expand marked'):
                self.lines.expand(mark_items('expand'))
            elif c == 10 and command_match(self.current_line.text, 'expand selected', 'expand selection'):
                self.lines.expand(select_items('expand'))
            elif c == 10 and command_match(self.current_line.text, 'expand'):
                self.lines.expand(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'collapse marked'):
                self.lines.collapse(mark_items('collapse'))
            elif c == 10 and command_match(self.current_line.text, 'collapse selected', 'collapse selection'):
                self.lines.collapse(select_items('collapse'))
            elif c == 10 and command_match(self.current_line.text, 'collapse all'):
                self.lines.collapse('collapse 1 - %s' % str(len(self.lines.db)))
            elif c == 10 and command_match(self.current_line.text, 'collapse'):
                self.lines.collapse(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'quit'):
                self.reset_line()
                if not self.saved_since_edit and self.get_confirmation(' Quit without saving? (y/n) '):
                    quit(False)
                elif self.saved_since_edit:
                    quit(False)
            elif c == 10 and self.current_line.length - pr_len > 5 and \
                    command_match(self.current_line.text, 'save'):  # save w/ new name
                temp_path = self.current_line.text[5:]
                self.reset_line()
                self.save(temp_path)
            elif c == 10 and command_match(self.current_line.text, 'save'):  # save (write over) current file
                self.reset_line()
                self.save(self.save_path)
            elif c == 10 and command_match(self.current_line.text, 'saveas'):
                if self.current_line.length - pr_len > 7:
                    temp_path = self.current_line.text[7:]
                elif not self.save_path:
                    temp_path = False
                else:
                    (fullpath, filename) = os.path.split(self.save_path)
                    temp_path = filename
                self.save_as(temp_path)

            elif c == 10 and command_match(self.current_line.text, 'split', 'splitscreen'):
                toggle_split_screen(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'show', 'hide'):
                show_hide(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, 'syntax'):
                toggle_syntax(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'show syntax', 'hide syntax'):
                toggle_syntax(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'whitespace'):
                toggle_whitespace(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'show whitespace', 'hide whitespace'):
                toggle_whitespace(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, 'tabs', 'tab'):
                toggle_tabs(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, 'find'):
                self.reset_needed = True  # Trying to fix intermittant bug where find doesn't clear line
                find(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, 'mark'):
                mark(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "unmark all", "unmark off"):
                unmark_all()  # unmarks all lines
            elif c == 10 and command_match(self.current_line.text, "unmark"):
                unmark(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, "deselect all", "unselect all"):
                self.reset_line()
                self.deselect_all()  # deselects all lines
            elif c == 10 and command_match(self.current_line.text, "select off", "select none"):
                self.deselect_all()  # deselects all lines
                self.reset_line()
            elif c == 10 and command_match(self.current_line.text, "deselect"):
                self.deselect(self.current_line.text)
                self.reset_line()
            elif c == 10 and command_match(self.current_line.text, "select reverse", "select invert"):
                self.invert_selection()
            elif c == 10 and command_match(self.current_line.text, "invert", "invert selection"):
                self.invert_selection()
            elif c == 10 and command_match(self.current_line.text, "select up"):
                self.select_up(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "select down"):
                self.select_down(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "select"):
                self.select(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, "goto"):
                self.goto(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "comment marked"):
                self.comment(mark_items("comment"))
            elif c == 10 and command_match(self.current_line.text, "comment selected", "comment selection"):
                self.comment(select_items("comment"))
            elif c == 10 and command_match(self.current_line.text, "comment"):
                self.comment(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "uncomment marked"):
                self.uncomment(mark_items("uncomment"))
            elif c == 10 and command_match(self.current_line.text, "uncomment selected", "uncomment selection"):
                self.uncomment(select_items("uncomment"))
            elif c == 10 and command_match(self.current_line.text, "uncomment"):
                self.uncomment(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "indent marked"):
                self.indent(mark_items("indent"))
            elif c == 10 and command_match(self.current_line.text, "indent selected", "indent selection"):
                self.indent(select_items("indent"))
            elif c == 10 and command_match(self.current_line.text, "indent"):
                self.indent(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "unindent marked"):
                self.unindent(mark_items("unindent"))
            elif c == 10 and command_match(self.current_line.text, "unindent selected", "unindent selection"):
                self.unindent(select_items("unindent"))
            elif c == 10 and command_match(self.current_line.text, "unindent"):
                self.unindent(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, "load", "read"):
                self.load_command(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, "run"):
                self.reset_line()
                self.run()

            elif c == 10 and command_match(self.current_line.text, "color on"):
                color_on()
            elif c == 10 and command_match(self.current_line.text, "color default", "color defaults"):
                default_colors()

            elif c == 10 and command_match(self.current_line.text, "replace"):
                replace_text(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "copy marked"):
                copy(mark_items("copy"))
            elif c == 10 and command_match(self.current_line.text, "copy selected", "copy selection"):
                copy(select_items("copy"), True)
            elif c == 10 and command_match(self.current_line.text, "copy"):
                copy(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "paste"):
                paste(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "undo"):
                undo()
            elif c == 10 and command_match(self.current_line.text, "delete marked"):
                delete_lines(mark_items("delete"))
            elif c == 10 and command_match(self.current_line.text, "delete selected", "delete selection"):
                delete_lines(select_items("delete"))
            elif c == 10 and command_match(self.current_line.text, "delete"):
                delete_lines(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "revert"):
                revert()
            elif c == 10 and command_match(self.current_line.text, "new"):
                self.new_doc()
            elif c == 10 and command_match(self.current_line.text, "cut selected", "cut selection"):
                cut(select_items("cut"))
            elif c == 10 and command_match(self.current_line.text, "cut"):
                cut(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, "protect"):
                toggle_protection(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "commands off"):
                self.reset_line()
                if self.get_confirmation("Turn off inline commands? (y/n)"):
                    self.config["inline_commands"] = False
                    self.get_confirmation("Command window still accessible with ctrl 'e'", True)
                    self.program_message = " Inline commands turned off! "

            elif c == 10 and command_match(self.current_line.text, "debug"):
                self.toggle_debug(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "prev", "previous"):
                prev()
            elif c == 10 and command_match(self.current_line.text, "strip") and \
                    self.get_confirmation("Strip extra spaces from lines? (y/n)"):
                strip_spaces(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "savesettings", "saveprefs") and \
                    self.get_confirmation("Save current settings? (y/n)"):
                self.config.save_settings()
            elif c == 10 and command_match(self.current_line.text, "setcolors", "setcolor"):
                set_colors()
            elif c == 10 and command_match(self.current_line.text, "isave"):
                isave()
            elif c == 10 and command_match(self.current_line.text, "entry"):
                toggle_entry(self.current_line.text)

            elif c == 10 and command_match(self.current_line.text, "live"):
                toggle_live(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "timestamp"):
                time_stamp()
            elif c == 10 and current_line.text.endswith("help") and command_match(current_line.text, "help"):
                self.reset_line()
                if self.window.width > 60 and \
                        self.get_confirmation("Load HELP GUIDE? Current doc will be purged! (y/n)"):
                    show_help()
                elif self.window.width <= 60 and \
                        self.get_confirmation("Load HELP & purge current doc? (y/n)"):
                    show_help()
            elif c == 10 and command_match(self.current_line.text, "auto"):
                toggle_auto(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "formatting"):
                toggle_comment_formatting(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "help"):
                function_help(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "guide", "pageguide"):
                toggle_page_guide(self.current_line.text)
            elif c == 10 and command_match(self.current_line.text, "acceleration", "accelerate"):
                toggle_acceleration(self.current_line.text)

            # Return Key pressed
            elif c == 10:
                return_key()
            # Key up
            elif c == curses.KEY_UP:
                new_time = time.time()
                if new_time - self.old_time > .2:
                    self.continue_down = 0
                    self.continue_up = 0
                    self.continue_left = 0
                    self.continue_right = 0
                self.old_time = new_time
                self.move_up()
            # Key down
            elif c == curses.KEY_DOWN:
                new_time = time.time()
                if new_time - self.old_time > .2:
                    self.continue_down = 0
                    self.continue_up = 0
                    self.continue_left = 0
                    self.continue_right = 0
                self.old_time = new_time
                self.move_down()
            # Key left
            elif c == curses.KEY_LEFT:
                if self.lines.locked:
                    self.current_num = max(1, self.current_num - (self.window.height - 1))
                else:
                    new_time = time.time()
                    if new_time - self.old_time > .2:
                        self.continue_down = 0
                        self.continue_up = 0
                        self.continue_left = 0
                        self.continue_right = 0
                    self.old_time = new_time
                    self.move_left()
            # Key right
            elif c == curses.KEY_RIGHT:
                if self.lines.locked:
                    self.current_num = min(self.lines.total, self.current_num + (self.window.height - 1))
                else:
                    new_time = time.time()
                    if new_time - self.old_time > .2:
                        self.continue_down = 0
                        self.continue_up = 0
                        self.continue_left = 0
                        self.continue_right = 0
                    self.old_time = new_time
                    self.move_right()

            # If read only mode, 'b' and 'space' should act as in terminal.
            elif self.lines.locked and c in (ord('b'), ord('B')):
                self.move_up()
            elif self.lines.locked and c == ord(' '):
                self.move_down()

            elif c == self.config["key_save_as"]:
                self.reset_needed = False
                if not self.save_path:
                    temp_path = False
                else:
                    (fullpath, filename) = os.path.split(self.save_path)
                    temp_path = filename
                self.save_as(temp_path)

            elif self.config["splitscreen"] and c in (339, self.config["key_page_up"]):  # PAGE UP
                self.program_message = ""
                if self.config["splitscreen"] > 1:
                    self.config["splitscreen"] -= 1
                    if self.config["syntax_highlighting"]:
                        syntax_split_screen()

            elif self.config["splitscreen"] and c in (338, self.config["key_page_down"]):  # PAGE DOWN
                self.program_message = ""
                if self.config["splitscreen"] < self.lines.total - 1:
                    self.config["splitscreen"] += 1
                    if self.config["syntax_highlighting"]:
                        syntax_split_screen()

            elif c == self.config["key_page_up"]:
                self.page_up()
            elif c == self.config["key_page_down"]:
                self.page_down()

            elif c == self.config["key_entry_window"]:
                if self.lines.locked:
                    read_mode_entry_window()
                else:
                    enter_commands()  # Control E pulls up dialog box

            elif c == self.config["key_find"]:
                self.reset_needed = False
                find_window()

            elif c == self.config["key_find_again"] and not self.last_search:
                self.reset_needed = False
                find_window()
            elif c == self.config["key_find_again"] and self.last_search:
                self.reset_needed = False  # fix bug that was deleting lines
                self.program_message = ""
                # find("find %s" %last_search) #Press control-g to find again
                find("find")  # Press control -g to find again
            elif c == self.config["key_deselect_all"] and self.lines.locked:  # In read only mode, deselects selection
                self.last_search = ''
                unmark_all()
            elif c == self.config["key_deselect_all"]:
                deselect_all()  # Press control-a to deselect lines
            elif self.config["debug"] and c == self.config["key_next_bug"]:
                bug_hunt()  # Press control-d to move to line with 'bug'
            elif not self.config["debug"] and c == self.config["key_next_bug"] and \
                    self.get_confirmation("Turn on debug mode? (y/n)"):
                self.reset_needed = False
                self.toggle_debug("debug on")
            elif c == self.config["key_next_marked"]:
                goto_marked()  # goto next marked line if control-n is pressed
            elif c == self.config["key_previous_marked"]:
                prev_marked()  # goto prev marked line if control-b is pressed

            # Key backspace (delete)
            elif c == curses.KEY_BACKSPACE or c == 127:
                if self.lines.locked:
                    self.move_up()  # If document is locked, convert backspace/delete to ARROW UP
                else:
                    self.key_backspace()
            # Tab pressed (insert 4 spaces)
            elif c == 9:
                self.tab_key()
            # Other key presses (alphanumeric)
            elif not self.lines.locked and c in CHAR_DICT:
                self.add_character(CHAR_DICT[c])
