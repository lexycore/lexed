import os
import time

from lexed.const import COMMANDS, CHAR_DICT
from lexed.line import Lines
from lexed.console import curses

from .clipboard import EditorClipboard
from .select import EditorSelect
from .mark import EditorMark
from .files import EditorFiles
from .lines import EditorLines
from .moves import EditorMoves
from .debug import EditorDebug
from .meta import BareException


class Editor(EditorClipboard, EditorSelect, EditorMark, EditorFiles, EditorLines, EditorMoves, EditorDebug):
    def __init__(self, window):
        super(EditorClipboard, self).__init__()
        super(EditorSelect, self).__init__()
        super(EditorMark, self).__init__()
        super(EditorFiles, self).__init__()
        super(EditorLines, self).__init__()
        super(EditorMoves, self).__init__()
        super(EditorDebug, self).__init__()
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
        self.prev_line = 0
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
            except BareException:
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
        except BareException:
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
            except BareException:
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
                    if self.config.os_name == 'Linux':
                        self.window.hline(y, x, curses.ACS_BULLET, 1, self.config['color_entry_dim'])
                    else:
                        self.window.addstr(y, x, '.', self.config['color_entry_dim'])
                else:
                    if indent_num > 8:
                        indent_num = 1
                    if indent_num > 4:
                        if self.config.os_name == 'Linux':
                            self.window.hline(y, x, curses.ACS_BULLET, 1, self.config['color_tab_even'])
                        else:
                            self.window.addstr(y, x, '.', self.config['color_tab_even'])  # Prints 'tab
                    else:
                        if self.config.os_name == 'Linux':
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
        except BareException:
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
        except BareException:
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
            except BareException:
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
            except BareException:
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
        except BareException:
            return False  # return False if error occurs

    def status_message(self, text, number, update_lines=False):
        self.window.status_message(text, number, self.lines.total, update_lines)

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
                    except BareException:
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
        except BareException:
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
        except BareException:
            pass

    def print_header(self):
        self.window.print_header(
            save_info=self.saved_since_edit and '*' or '',
            message=self.program_message,
            save_path=self.save_path,
            total=self.lines.total,
        )

    def command_match(self, text_string, command, alt='<@>_foobar_', protect_needed=True):
        """Gets 'command' from string, returns False if next character is '='."""
        if text_string == '<@>_foobar_':
            return False
        text_list = ''
        orig_text = text_string
        try:
            if not text_string or text_string[0] == ' ':
                return False

            if not self.config['inline_commands'] and protect_needed:
                return False

            if ' ' in text_string and ' ' not in command:
                text_list = text_string.split()
                if len(text_list) > 1:
                    if text_list[1] and text_list[1][0] in ('=', '+', '-', '*', '/', '%', '(', '[', '{'):
                        if command in ('replace', 'protect') and ' with ' in text_string:
                            pass
                        elif command in ('save', 'saveas', 'load') and text_list[1][0] == '/':
                            pass
                        else:
                            return False
                    if command in ('replace', 'protect') and text_string.count(
                            ' ') > 3 and ' with ' not in text_string and '|' not in text_string:
                        return False
                    text_string = text_list[0]

            if self.config['inline_commands'] == 'protected' and protect_needed:
                command = self.config['protect_string'] + command
                alt = self.config['protect_string'] + alt
                temp_text = text_string.replace(self.config['protect_string'], '')
            else:
                temp_text = text_string

            if command in (
                    'syntax', 'entry', 'live', 'formatting', 'tab', 'tabs', 'whitespace', 'show', 'hide', 'goto',
                    'color',
                    'help',
                    'debug', 'split', 'guide', 'pageguide') and len(text_list) > 2:
                return False

            if alt in (
                    'syntax', 'entry', 'live', 'formatting', 'tab', 'tabs', 'whitespace', 'show', 'hide', 'goto',
                    'color',
                    'help',
                    'debug', 'split', 'guide', 'pageguide') and len(text_list) > 2:
                return False

            if temp_text not in ('replace', 'protect', 'find', 'save', 'saveas', 'load', 'mark') and \
                    orig_text.count(' ') - 1 > orig_text.count(',') + (2 * orig_text.count('-')):
                return False
            if temp_text not in ('replace', 'protect', 'find', 'save', 'saveas', 'load', 'mark') and \
                    orig_text.count('-') > 1:
                return False
            if temp_text not in (
                    'replace', 'protect', 'find', 'save', 'saveas', 'load',
                    'mark') and '-' in orig_text and ',' in orig_text:
                return False

            if text_string == command or text_string == alt:
                if self.config['inline_commands'] == 'protected' and protect_needed:
                    self.current_line.text = self.current_line.text[len(self.config['protect_string']):]
                return True
            else:
                return False
        except BareException:
            return False

    def print_command(self):
        """New method to print executable commands"""
        if not self.lines.db[self.current_num].executable:
            return
        if len(self.lines.db[self.current_num].text) >= self.window.width - 6:
            self.window.addstr((self.window.height - 2) - self.lines.db[self.current_num].number_of_rows + 1, 6,
                               self.lines.db[self.current_num].text.split()[0],
                               self.config['color_warning'])  # Prints command only if line oversized
        else:
            self.window.addstr(self.window.height - 2, 6, self.lines.db[self.current_num].text,
                               self.config['color_warning'])  # Prints entire line

    def split_screen(self):
        """Display splitscreen"""
        if not self.config['splitscreen']:
            return

        number = self.config['splitscreen']
        max_row = int(self.window.height / 2 + 1)
        print_row = self.header
        text = ' ' * self.window.width

        for j in range(2, max_row):
            self.window.addstr(j, 0, text, self.config['color_normal'])  # Clears screen
            self.window.addstr(j, 0, '     ', self.config['color_line_numbers'])  # draws line number background

        if self.config['page_guide']:
            self.window.draw_page_guide(end_pos=max_row, hline_pos=max_row)  # Draws page guide

        for z in range(number, number + max_row):

            if z <= 0 or z > self.lines.total:
                break
            if print_row > max_row - 1:
                break

            self.window.addstr(print_row, 0, '     ', self.config['color_line_numbers'])  # Prints block
            self.window.addstr(print_row, 0, str(self.lines.db[z].number),
                               self.config['color_line_numbers'])  # Prints next line numbers

            if self.lines.db[z].marked and self.lines.db[z].error and self.config['debug']:
                self.window.hline(print_row, 5, curses.ACS_DIAMOND, 1, self.config['color_warning'])  # MARKED & ERROR

            elif self.lines.db[z].error and self.config['debug']:
                self.window.addstr(print_row, 4, '!', self.config['color_warning'])  # Prints ERROR

            elif self.lines.db[z].marked and not self.lines.locked:
                self.window.hline(print_row, 5, curses.ACS_DIAMOND, 1,
                                  self.config['color_quote_double'])  # MARKED & ERROR

            for i in range(0, len(self.lines.db[z].row)):
                if i != 0 and self.lines.db[z].number_of_rows > self.window.height - 4:
                    break
                if print_row > max_row - 1:
                    try:
                        self.window.addstr(print_row - 1, self.window.width - 4,
                                           ' -->', self.config['color_quote_double'])
                    except BareException:
                        pass
                    break

                next_line = self.lines.db[z].row[i]

                if self.lines.db[z].selected:
                    self.window.addstr(print_row, 6, (' ' * (self.window.width - 6)),
                                       self.config['color_selection'])  # Prints selected
                    self.window.addstr(print_row, self.window.width, '<',
                                       self.config['color_quote_double'])  # Prints selected
                    self.window.addstr(print_row, 6, next_line,
                                       self.config['color_selection'])  # Prints Selected Text
                elif self.config['syntax_highlighting']:
                    if not self.lines.db[z].syntax:
                        self.lines.db[z].add_syntax()
                    temp_list = self.lines.db[z].syntax[i]
                    self.print_syntax(temp_list, 6, print_row)
                else:
                    self.window.addstr(print_row, 6, next_line, self.config['color_normal'])  # Prints next line
                if i == 0 and self.lines.db[z].number_of_rows > self.window.height - 4:
                    self.window.addstr(print_row, self.window.width - 4, ' -->', self.config['color_quote_triple'])
                print_row += 1

        self.window.hline(max_row, 0, curses.ACS_HLINE, self.window.width, self.config['color_bar'])

    def toggle_split_screen(self, text):
        """Turn splitscreen on or off"""
        # global program_message
        arg = self.get_args(text)
        self.reset_line()
        self.program_message = ' Splitscreen on '
        if arg == 'on':
            self.config['splitscreen'] = 1
        elif arg == 'off':
            self.config['splitscreen'] = False
            self.program_message = ' Splitscreen off '
        elif arg in ('', 'split', 'splitscreen') and self.config['splitscreen']:
            self.config['splitscreen'] = False
            self.program_message = ' Splitscreen off '
        elif arg in ('', 'split', 'splitscreen') and not self.config['splitscreen']:
            self.config['splitscreen'] = 1
        else:
            try:
                if arg == 'end':
                    arg = max(1, self.lines.total - 1)
                if arg == 'start':
                    arg = 1
                line_number = int(arg)
                # max_row = int(self.window.height / 2 + 1)
                if line_number > self.lines.total - 1:
                    line_number = self.lines.total - 1
                if line_number < 1:
                    line_number = 1
                if line_number > self.lines.total:
                    line_number = self.lines.total
                self.config['splitscreen'] = line_number
                self.program_message = f' Splitscreen @ line {line_number} '
            except BareException:
                self.program_message = ' Error, splitscreen failed! '
                return

    def show_hide(self, text):
        """Allows show and hide commands to change settings"""
        # global program_message
        flag = 'show' in text
        item = text.split(' ', 1)[1]
        if item == 'syntax':
            self.config['syntax_highlighting'] = flag
            temp_text = 'Syntax highlighting'
        elif item in ('spaces', 'whitespace'):
            self.config['showSpaces'] = flag
            temp_text = 'Whitespace'
        elif item in ('tabs', 'tab stops', 'indent', 'indentation'):
            self.config['show_indent'] = flag
            temp_text = 'Visible tabs'
        elif item in ('entry', 'entry line'):
            self.config['entry_highlighting'] = flag
            temp_text = 'Entry line highlighting'
        elif item in ('live', 'live syntax'):
            self.config['live_syntax'] = flag
            temp_text = 'Live syntax'
        elif item in ('debug', 'bugs', 'debug mode'):
            self.config['debug'] = flag
            temp_text = 'Debug mode'
        elif item in ('formatting', 'comment formatting'):
            self.config['format_comments'] = flag
            temp_text = 'Comment formatting'
        elif item in ('split', 'splitscreen', 'split screen'):
            self.config['splitscreen'] = flag
            temp_text = 'Splitscreen'
        elif item in ('guide', 'pageguide'):
            self.config['page_guide'] = 80 if flag else flag

            if self.config['page_guide'] > self.window.width - 7:
                self.config['page_guide'] = False
                if self.window.width > 59:
                    self.program_message = ' Error, terminal too small for 80 character page guide! '
                else:
                    self.program_message = ' Error, page guide not displayed '
                self.reset_line()
                return
            else:
                temp_text = 'Page guide'
        else:
            temp_text = 'Error, nothing'

        self.program_message = f' {temp_text} turned {"on" if flag else "off"}'

        self.reset_line()
        if self.config['syntax_highlighting']:
            self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()
        if self.config['debug']:
            self.debug_visible()

    def toggle_syntax(self, text):
        """Toggle syntax highlighting"""
        # global program_message
        self.program_message = ' Syntax highlighting turned off '
        if 'off' in text or 'hide' in text:
            self.config['syntax_highlighting'] = False
        elif text == 'syntax' and self.config['syntax_highlighting']:
            self.config['syntax_highlighting'] = False
        else:
            self.config['syntax_highlighting'] = True
            for line_num in self.lines.db.values():
                line_num.add_syntax()
                i = line_num.number
                if len(self.lines.db) + 1 > 800 and i / 10.0 == int(i / 10.0):  # display status message
                    self.status_message('Adding syntax: ', (100 / ((len(self.lines.db) + 1) * 1.0 / (i + 1))))
            self.program_message = ' Syntax highlighting turned on '
        self.reset_line()

    def toggle_whitespace(self, text):
        """Toggle visible whitespace"""
        # global program_message
        self.program_message = ' Visible whitespace turned off '
        if 'off' in text or 'hide' in text:
            self.config['showSpaces'] = False
        elif text == 'whitespace' and self.config['showSpaces']:
            self.config['showSpaces'] = False
        else:
            self.config['showSpaces'] = True
            self.toggle_syntax('syntax on')  # update syntax to include whitespace
            self.program_message = ' Visible whitespace turned on '
        self.reset_line()

    def toggle_tabs(self, text):
        """Toggle visible tabs"""
        # global program_message
        self.program_message = ' Visible tabs turned off '
        if 'off' in text or 'hide' in text:
            self.config['show_indent'] = False
        elif text in ['tab', 'tabs'] and self.config['show_indent']:
            self.config['show_indent'] = False
        else:
            self.config['show_indent'] = True
            self.toggle_syntax('syntax on')  # update syntax to include tabs
            self.program_message = ' Visible tabs turned on '
        self.reset_line()

    def find(self, text):
        """Search feature
                'find keyword' moves to first instance of 'keyword'
                'find' moves to next match"""
        # global current_num, last_search, program_message, prev_line
        self.prev_line = self.current_num  # set previous line to current line
        collapsed_lines = False
        count = 0
        find_this = '$!*_foobar'
        show_message = False

        self.reset_line()

        if len(text) > 5 and self.last_search != find_this:
            find_this = text[5:]
            self.last_search = find_this
            for i in range(1, len(self.lines.db) + 1):
                item = self.lines.db[i]
                if find_this in item.text or find_this == item.text:
                    count += item.text.count(find_this)
            show_message = True
        else:
            find_this = self.last_search

        if self.current_num != len(self.lines.db):
            for i in range(self.current_num + 1, len(self.lines.db) + 1):
                item = self.lines.db[i]
                if item.collapsed:  # skip lines that are collapsed (don't search in collapsed lines)
                    collapsed_lines = True
                    continue
                if find_this in item.text or find_this == item.text:
                    self.current_num = i
                    self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x  # update cursor position
                    if show_message:
                        self.program_message = ' %i matches found ' % count
                    self.syntax_visible()
                    return

        for i in range(1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if item.collapsed:  # skip lines that are collapsed (don't search in collapsed lines)
                collapsed_lines = True
                continue
            if find_this in item.text or find_this == item.text:
                current_num = i
                self.lines.db[current_num].x = self.lines.db[current_num].end_x  # update cursor position
                if show_message:
                    self.program_message = f' {count} matches found '
                self.syntax_visible()
                return

        if collapsed_lines:
            self.program_message = ' Item not found{}'.format(
                '; collapsed lines not searched! ' if collapsed_lines else '! ')

    def comment(self, text):
        """New comment function that uses returnArgs"""
        # global saved_since_edit, program_message
        self.reset_line()
        selection = False
        if text == 'comment':
            selection, item_count = self.get_selected()
            if selection:
                text = f'comment {selection}'
        try:
            _list = self.return_args(text)
            count = len(_list)
            self.update_que('COMMENT operation')
            self.update_undo()
            loop_num = 0
            for i in _list:
                loop_num += 1
                if self.lines.db[i].text:
                    self.lines.db[i].text = '#' + self.lines.db[i].text
                    if self.config['debug'] and i > 1:  # update error status
                        self.lines.db[i].error = False
                        self.error_test(self.lines.db[i].number)  # test for code errors
                    if len(_list) > 200 and i / 10.0 == int(i / 10.0) and self.config['syntax_highlighting']:
                        self.status_message('Processing: ', (100 / ((len(_list) + 1.0) / loop_num)))
                else:
                    count -= 1
                if i == self.current_num:
                    self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
            if selection:
                self.program_message = f' Selection commented ({count} lines) '
            elif len(_list) == 1 and count == 1:
                self.program_message = f' Commented line number {_list[0]} '
            else:
                self.program_message = f' Commented {count} lines '
        except BareException:
            self.program_message = ' Error, Comment Failed! '
        if self.config['syntax_highlighting']:
            self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()
        self.saved_since_edit = False

    def uncomment(self, text):
        """New uncomment function that uses returnArgs"""
        # global saved_since_edit, program_message
        self.reset_line()
        selection = False
        if text == 'uncomment':
            selection, item_count = self.get_selected()
            if selection:
                text = f'Uncomment {selection}'
        try:
            _list = self.return_args(text)
            count = len(_list)
            self.update_que('UNCOMMENT operation')
            self.update_undo()
            loop_num = 0
            for num in _list:
                loop_num += 1
                if self.lines.db[num].text and self.lines.db[num].text[0] == '#':
                    self.lines.db[num].text = self.lines.db[num].text[1:]
                    if self.config['debug'] and num > 1:  # update error status
                        self.lines.db[num].error = False
                        self.error_test(self.lines.db[num].number)  # test for code errors
                    if len(_list) > 200 and num / 10.0 == int(num / 10.0) and self.config['syntax_highlighting']:
                        self.status_message('Processing: ', (100 / ((len(_list) + 1.0) / loop_num)))
                else:
                    count -= 1
                if num == self.current_num:
                    # reset cursor if current line
                    self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
            if selection:
                self.program_message = f' Selection uncommented ({count} lines) '
            elif len(_list) == 1 and count == 1:
                self.program_message = f' Uncommented line number {_list[0]} '
            else:
                self.program_message = f' Uncommented {count} lines '
        except BareException:
            self.program_message = ' Error, Uncomment Failed! '
        if self.config['syntax_highlighting']:
            self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()
        self.saved_since_edit = False

    def indent(self, text):
        """New indent function that uses returnArgs"""
        # global saved_since_edit, program_message
        self.reset_line()
        selection = False
        if text == 'indent':
            selection, item_count = self.get_selected()
            if selection:
                text = f'Indent {selection}'
        self.reset_line()
        try:
            _list = self.return_args(text)
            count = len(_list)
            self.update_que('INDENT operation')
            self.update_undo()
            loop_num = 0
            for num in _list:
                loop_num += 1
                if self.lines.db[num].text:
                    self.lines.db[num].text = '    ' + self.lines.db[num].text
                    if self.config['debug'] and num > 1:  # update error status
                        self.lines.db[num].error = False
                        self.error_test(self.lines.db[num].number)  # test for code errors
                    if len(_list) > 200 and num / 10.0 == int(num / 10.0) and self.config['syntax_highlighting']:
                        self.status_message('Processing: ', (100 / ((len(_list) + 1.0) / loop_num)))
                else:
                    count -= 1
                if num == self.current_num:
                    # reset cursor if current line
                    self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
            if selection:
                self.program_message = ' Selection indented ({count} lines) '
            elif len(_list) == 1 and count == 1:
                self.program_message = ' Indented line number {_list[0]} '
            else:
                self.program_message = ' Indented {count} lines '
        except BareException:
            self.program_message = ' Error, Indent Failed! '
        if self.config['syntax_highlighting']:
            self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()

        self.saved_since_edit = False

    def unindent(self, text):
        """New unindent function that uses returnArgs"""
        # global saved_since_edit, program_message
        self.reset_line()
        selection = False
        if text == 'unindent':
            selection, item_count = self.get_selected()
            if selection:
                text = f'unindent {selection}'
        try:
            _list = self.return_args(text)
            count = len(_list)
            self.update_que('UNINDENT operation')
            self.update_undo()
            loop_num = 0
            for num in _list:
                loop_num += 1
                if self.lines.db[num].text and self.lines.db[num].text[0:4] == "    ":
                    self.lines.db[num].text = self.lines.db[num].text[4:]
                    if self.config['debug'] and num > 1:  # update error status
                        self.lines.db[num].error = False
                        self.error_test(self.lines.db[num].number)  # test for code errors
                    if len(_list) > 200 and num / 10.0 == int(num / 10.0) and self.config['syntax_highlighting']:
                        self.status_message('Processing: ', (100 / ((len(_list) + 1.0) / loop_num)))
                else:
                    count -= 1
                if num == self.current_num:
                    self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
                    # reset cursor if current line
            if selection:
                self.program_message = f' Selection unindented ({count} lines) '
            elif len(_list) == 1 and count == 1:
                self.program_message = f' Unindented line number {_list[0]} '
            else:
                self.program_message = f' Unindented {count} lines '
        except BareException:
            self.program_message = ' Error, Unindent Failed! '
        if self.config['syntax_highlighting']:
            self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()
        self.saved_since_edit = False

    def load_command(self, text):
        """Pre-processes load command"""
        self.reset_line()
        read_state = text[:4] == 'read'
        if ' ' in text and len(text) > 5:
            self.load(text[5:], read_state)
        else:
            if self.save_path:
                loadfile = self.display_list(self.save_path)
            else:
                temp_path = str(os.getcwd() + '/')
                loadfile = self.display_list(temp_path)
            if loadfile:
                if self.saved_since_edit:
                    self.load(loadfile, read_state)
                elif self.lines.total < 2 and not self.save_path:
                    self.load(loadfile, read_state)
                elif self.get_confirmation('Load file without saving old? (y/n)'):
                    self.load(loadfile, read_state)

    def return_args(self, temp_text):
        """Returns list of args (line numbers, not text)"""
        try:
            the_list = []
            if ',' in temp_text:
                arg_list = self.get_args(temp_text, ' ', ',')
                for i in range(0, len(arg_list)):
                    num = int(arg_list[i])
                    if 1 <= num <= self.lines.total:
                        the_list.append(num)
            elif '-' in temp_text:
                arg_list = self.get_args(temp_text, ' ', '-')
                start = int(arg_list[0])
                end = int(arg_list[1])
                for num in range(start, end + 1):
                    if 1 <= num <= self.lines.total:
                        the_list.append(num)
            else:
                arg_list = self.get_args(temp_text)
                if 'str' in str(type(arg_list)):
                    num = int(arg_list)
                else:
                    num = int(arg_list[0])
                the_list.append(num)
            return the_list
        except BareException:
            return False

    def default_colors(self):
        """set colors to default"""
        # global program_message
        self.program_message = ' Colors set to defaults '
        self.reset_line()
        self.config['default_colors'] = True
        self.window.color_on(True)

    def replace_text(self, text):
        """Function to replace old text with new"""
        # global program_message, saved_since_edit
        selection, item_count = self.get_selected()
        if 'replace marked' in text:
            self.replace_marked(text)
            return
        elif 'replace selected' in text:
            self.replace_selected(text)
            return
        elif selection and self.get_confirmation(f'Act on {item_count} selected lines only? (y/n)'):
            self.replace_selected(text, False)
            return
        try:
            if '|' in text:
                (old_text, new_text) = self.get_args(text, ' ', '|', False)
            else:
                (old_text, new_text) = self.get_args(text, ' ', ' with ', False)
        except BareException:
            self.get_confirmation('Error occurred, replace operation failed!', True)
            return
        self.reset_line()
        replace_num = 0

        # calculate number of replacements
        for i in range(1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if old_text in item.text:
                replace_num += item.text.count(old_text)
        if replace_num:  # Confirm replacement
            if replace_num > 1:
                message_text = f'Replace {replace_num} items? (y/n)'
            else:
                message_text = 'Replace 1 item? (y/n)'

            if not self.get_confirmation(message_text):
                self.program_message = ' Replace aborted! '
                return
            else:  # replace items

                self.update_que('REPLACE operation')
                self.update_undo()

                for i in range(1, len(self.lines.db) + 1):
                    item = self.lines.db[i]
                    if old_text in item.text:
                        if replace_num > 200 and i / 10.0 == int(i / 10.0):  # display processing message
                            self.status_message('Processing: ', (100 / ((len(self.lines.db) + 1) * 1.0 / (i + 1))))
                        temp_text = item.text
                        temp_text = temp_text.replace(old_text, new_text)
                        item.text = temp_text
                        if self.config['syntax_highlighting']:
                            item.add_syntax()  # adjust syntax
                        if self.config['debug'] and i > 1:
                            self.lines.db[i].error = False
                            self.error_test(self.lines.db[i].number)  # test for code errors
                self.program_message = f' Replaced {replace_num} items '
            self.saved_since_edit = False
        else:
            self.get_confirmation('   Item not found!    ', True)

    def undo(self):
        """Function that reverses command/restores state to last edit"""
        # global current_num, undo_list, undo_text_que, undo_state_que, undo_state, undo_mark_que, undo_mark, program_message, reset_needed, undo_select_que, undo_select
        count = 0
        self.reset_line()
        if not self.undo_list:
            self.get_confirmation('There is nothing to undo!', True)
            return
        if not self.get_confirmation(f'Undo last {self.undo_type}? (y/n)'):
            return
        del self.lines.db
        self.lines.db = {}
        length = len(self.undo_list)
        for i in range(0, len(self.undo_list)):
            count += 1
            string = self.undo_list[i]
            line = self.lines.add(string)

            if length > 500 and count / 100.0 == int(count / 100.0):  # display processing message
                self.status_message('Processing: ', (100 / (length * 1.0 / count)))

            if self.undo_state:
                line.collapsed = self.undo_state[i]
            if self.undo_mark:
                line.marked = self.undo_mark[i]
            if self.undo_select:
                line.selected = self.undo_select[i]
            if self.config['syntax_highlighting']:
                line.add_syntax()  # adjust syntax
            if self.config['debug']:
                self.error_test(line.number)  # test for code errors

        if self.current_num > self.lines.total:
            self.current_num = self.lines.total
        self.undo_list = []
        self.undo_text_que = []
        self.undo_state_que = []
        self.undo_state = []
        self.undo_mark_que = []
        self.undo_mark = []
        self.undo_select_que = []
        self.undo_select = []

        self.program_message = " Undo successful "

    def toggle_protection(self, text):
        """Turns protection on/off for inline commands"""
        # global program_message
        if 'protect with ' in text:
            args = self.get_args(text, '_foobar', 'protect with ', False)
            if args[1].endswith(" "):
                args[1] = args[1].rstrip()
            if len(args[1]) > 4:
                args[1] = args[1][0:4]
            if self.get_confirmation(f"Protect commands with '{args[1]}'? (y/n)"):
                self.config['protect_string'] = args[1]
                self.config['inline_commands'] = 'protected'
                self.program_message = f" Commands now protected with '{args[1]}' "
        else:
            self.program_message = f" Commands protected with '{self.config['protect_string']}' "
            arg = self.get_args(text)
            if arg == 'on':
                self.config['inline_commands'] = 'protected'
            elif arg == 'off':
                self.config['inline_commands'] = True
                self.program_message = ' Command protection off! '
            else:
                self.program_message = ' Error, protection not changed '
        self.reset_line()

    def toggle_entry(self, text):
        """Toggle entry highlighting (colorizes entry line)"""
        # global program_message
        self.program_message = ' Entry highlighting turned off '
        if 'off' in text or 'hide' in text:
            self.config['entry_highlighting'] = False
        elif text == 'entry' and self.config['entry_highlighting']:
            self.config['entry_highlighting'] = False
        else:
            self.config['entry_highlighting'] = True
            self.program_message = ' Entry highlighting turned on '
        self.reset_line()

    def toggle_live(self, text):
        """Toggle syntax highlighting on entry line"""
        # global program_message
        self.program_message = ' Live syntax turned off '
        if 'off' in text or 'hide' in text:
            self.config["live_syntax"] = False
        elif text == 'live' and self.config['live_syntax']:
            self.config['live_syntax'] = False
        else:
            self.config['live_syntax'] = True
            self.program_message = ' Live syntax turned on '
        self.reset_line()

    def time_stamp(self):
        """Prints current time & date"""
        # global text_entered, program_message, saved_since_edit
        self.reset_line()
        a_time = time.strftime('%m/%d/%y %r (%A)', time.localtime())

        self.current_line.text = self.current_line.text + a_time
        self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x
        self.text_entered = True
        self.saved_since_edit = False
        self.program_message = " Current time & date printed "

    def toggle_comment_formatting(self, text):
        """Toggle comment formatting (formats/colorizes comments)"""
        # global program_message
        self.program_message = ' Comment formatting turned off '
        if 'off' in text or 'hide' in text:
            self.config['format_comments'] = False
        elif text == 'formatting' and self.config['format_comments']:
            self.config['format_comments'] = False
        else:
            self.config['format_comments'] = True
            self.program_message = ' Comment formatting turned on '
        self.reset_line()
        self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()

    @staticmethod
    def rotate_string(string, rotate_num,
                      characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 {}[]()!@#$%^&*_+=-'\"\\|/<>,.?~`"):
        """Function that 'rotates' string.
               (I suggest you don't reuse this code in other programs... there are
                better ways to do this in Python)"""
        new_text = ''
        for i in range(0, len(string)):
            char = string[i]
            index_num = characters.find(char)
            if index_num == -1:
                new_text += string[i]
            else:
                position = index_num + rotate_num
                while position >= len(characters):
                    position -= len(characters)
                while position < 0:
                    position = len(characters) + position
                new_character = characters[position]
                new_text += new_character
        return new_text

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
                self.print_command()

            if self.config['inline_commands'] == 'protected':  # set protect variables
                pr_str = str(self.config['protect_string'])
                pr_len = len(pr_str)
            else:
                # pr_str = ''
                pr_len = 0

            if self.config['splitscreen']:
                self.split_screen()

            if self.config['debug'] and self.current_line.error and not self.program_message:  # Print error messages
                self.window.addstr(0, 0, ' ' * (self.window.width - 13), self.config['color_header'])
                self.window.addstr(0, 0, f' ERROR: {self.current_line.error} ', self.config['color_warning'])

            # Debugging
            # self.window.addstr(0, 0, " KEYPRESS: %i              " %(c), settings["color_warning"])
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
            if c == 10 and self.command_match(self.current_line.text, 'collapse off', 'expand all'):
                self.current_line.text = ''
                self.current_line.add_syntax()
                # settings['collapse_functions'] = False
                self.lines.expand_all()
                self.reset_line()

            elif c == 10 and self.command_match(self.current_line.text, 'expand marked'):
                self.lines.expand(self.mark_items('expand'))
            elif c == 10 and self.command_match(self.current_line.text, 'expand selected', 'expand selection'):
                self.lines.expand(self.select_items('expand'))
            elif c == 10 and self.command_match(self.current_line.text, 'expand'):
                self.lines.expand(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'collapse marked'):
                self.lines.collapse(self.mark_items('collapse'))
            elif c == 10 and self.command_match(self.current_line.text, 'collapse selected', 'collapse selection'):
                self.lines.collapse(self.select_items('collapse'))
            elif c == 10 and self.command_match(self.current_line.text, 'collapse all'):
                self.lines.collapse('collapse 1 - %s' % str(len(self.lines.db)))
            elif c == 10 and self.command_match(self.current_line.text, 'collapse'):
                self.lines.collapse(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'quit'):
                self.reset_line()
                if not self.saved_since_edit and self.get_confirmation(' Quit without saving? (y/n) '):
                    self.quit(False)
                elif self.saved_since_edit:
                    self.quit(False)
            elif c == 10 and self.current_line.length - pr_len > 5 and \
                    self.command_match(self.current_line.text, 'save'):  # save w/ new name
                temp_path = self.current_line.text[5:]
                self.reset_line()
                self.save(temp_path)
            elif c == 10 and self.command_match(self.current_line.text, 'save'):  # save (write over) current file
                self.reset_line()
                self.save(self.save_path)
            elif c == 10 and self.command_match(self.current_line.text, 'saveas'):
                if self.current_line.length - pr_len > 7:
                    temp_path = self.current_line.text[7:]
                elif not self.save_path:
                    temp_path = False
                else:
                    (full_path, filename) = os.path.split(self.save_path)
                    temp_path = filename
                self.save_as(temp_path)

            elif c == 10 and self.command_match(self.current_line.text, 'split', 'splitscreen'):
                self.toggle_split_screen(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'show', 'hide'):
                self.show_hide(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, 'syntax'):
                self.toggle_syntax(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'show syntax', 'hide syntax'):
                self.toggle_syntax(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'whitespace'):
                self.toggle_whitespace(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'show whitespace', 'hide whitespace'):
                self.toggle_whitespace(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, 'tabs', 'tab'):
                self.toggle_tabs(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, 'find'):
                self.reset_needed = True  # Trying to fix intermittant bug where find doesn't clear line
                self.find(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, 'mark'):
                self.mark(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "unmark all", "unmark off"):
                self.unmark_all()  # unmarks all lines
            elif c == 10 and self.command_match(self.current_line.text, "unmark"):
                self.unmark(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, "deselect all", "unselect all"):
                self.reset_line()
                self.deselect_all()  # deselects all lines
            elif c == 10 and self.command_match(self.current_line.text, "select off", "select none"):
                self.deselect_all()  # deselects all lines
                self.reset_line()
            elif c == 10 and self.command_match(self.current_line.text, "deselect"):
                self.deselect(self.current_line.text)
                self.reset_line()
            elif c == 10 and self.command_match(self.current_line.text, "select reverse", "select invert"):
                self.invert_selection()
            elif c == 10 and self.command_match(self.current_line.text, "invert", "invert selection"):
                self.invert_selection()
            elif c == 10 and self.command_match(self.current_line.text, "select up"):
                self.select_up(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "select down"):
                self.select_down(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "select"):
                self.select(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, "goto"):
                self.goto(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "comment marked"):
                self.comment(self.mark_items("comment"))
            elif c == 10 and self.command_match(self.current_line.text, "comment selected", "comment selection"):
                self.comment(self.select_items("comment"))
            elif c == 10 and self.command_match(self.current_line.text, "comment"):
                self.comment(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "uncomment marked"):
                self.uncomment(self.mark_items("uncomment"))
            elif c == 10 and self.command_match(self.current_line.text, "uncomment selected", "uncomment selection"):
                self.uncomment(self.select_items("uncomment"))
            elif c == 10 and self.command_match(self.current_line.text, "uncomment"):
                self.uncomment(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "indent marked"):
                self.indent(self.mark_items("indent"))
            elif c == 10 and self.command_match(self.current_line.text, "indent selected", "indent selection"):
                self.indent(self.select_items("indent"))
            elif c == 10 and self.command_match(self.current_line.text, "indent"):
                self.indent(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "unindent marked"):
                self.unindent(self.mark_items("unindent"))
            elif c == 10 and self.command_match(self.current_line.text, "unindent selected", "unindent selection"):
                self.unindent(self.select_items("unindent"))
            elif c == 10 and self.command_match(self.current_line.text, "unindent"):
                self.unindent(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, "load", "read"):
                self.load_command(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, "run"):
                self.reset_line()
                self.run()

            elif c == 10 and self.command_match(self.current_line.text, "color on"):
                self.window.color_on()
            elif c == 10 and self.command_match(self.current_line.text, "color default", "color defaults"):
                self.default_colors()

            elif c == 10 and self.command_match(self.current_line.text, "replace"):
                self.replace_text(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "copy marked"):
                self.copy(self.mark_items("copy"))
            elif c == 10 and self.command_match(self.current_line.text, "copy selected", "copy selection"):
                self.copy(self.select_items("copy"), True)
            elif c == 10 and self.command_match(self.current_line.text, "copy"):
                self.copy(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "paste"):
                self.paste(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "undo"):
                self.undo()
            elif c == 10 and self.command_match(self.current_line.text, "delete marked"):
                self.delete_lines(self.mark_items("delete"))
            elif c == 10 and self.command_match(self.current_line.text, "delete selected", "delete selection"):
                self.delete_lines(self.select_items("delete"))
            elif c == 10 and self.command_match(self.current_line.text, "delete"):
                self.delete_lines(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "revert"):
                self.revert()
            elif c == 10 and self.command_match(self.current_line.text, "new"):
                self.new_doc()
            elif c == 10 and self.command_match(self.current_line.text, "cut selected", "cut selection"):
                self.cut(self.select_items("cut"))
            elif c == 10 and self.command_match(self.current_line.text, "cut"):
                self.cut(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, "protect"):
                self.toggle_protection(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "commands off"):
                self.reset_line()
                if self.get_confirmation("Turn off inline commands? (y/n)"):
                    self.config["inline_commands"] = False
                    self.get_confirmation("Command window still accessible with ctrl 'e'", True)
                    self.program_message = " Inline commands turned off! "

            elif c == 10 and self.command_match(self.current_line.text, "debug"):
                self.toggle_debug(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "prev", "previous"):
                self.prev()
            elif c == 10 and self.command_match(self.current_line.text, "strip") and \
                    self.get_confirmation("Strip extra spaces from lines? (y/n)"):
                self.strip_spaces()  # self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "savesettings", "saveprefs") and \
                    self.get_confirmation("Save current settings? (y/n)"):
                self.config.save_settings()
            elif c == 10 and self.command_match(self.current_line.text, "setcolors", "setcolor"):
                self.window.set_colors()
            elif c == 10 and self.command_match(self.current_line.text, "isave"):
                self.isave()
            elif c == 10 and self.command_match(self.current_line.text, "entry"):
                self.toggle_entry(self.current_line.text)

            elif c == 10 and self.command_match(self.current_line.text, "live"):
                self.toggle_live(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "timestamp"):
                self.time_stamp()
            elif c == 10 and self.current_line.text.endswith("help") and \
                    self.command_match(self.current_line.text, "help"):
                self.reset_line()
                if self.window.width > 60 and \
                        self.get_confirmation("Load HELP GUIDE? Current doc will be purged! (y/n)"):
                    self.window.show_help()
                elif self.window.width <= 60 and \
                        self.get_confirmation("Load HELP & purge current doc? (y/n)"):
                    self.window.show_help()
            elif c == 10 and self.command_match(self.current_line.text, "auto"):
                self.toggle_auto(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "formatting"):
                self.toggle_comment_formatting(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "help"):
                self.function_help(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "guide", "pageguide"):
                self.toggle_page_guide(self.current_line.text)
            elif c == 10 and self.command_match(self.current_line.text, "acceleration", "accelerate"):
                self.toggle_acceleration(self.current_line.text)

            # Return Key pressed
            elif c == 10:
                self.return_key()
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
                    (full_path, filename) = os.path.split(self.save_path)
                    temp_path = filename
                self.save_as(temp_path)

            elif self.config["splitscreen"] and c in (339, self.config["key_page_up"]):  # PAGE UP
                self.program_message = ""
                if self.config["splitscreen"] > 1:
                    self.config["splitscreen"] -= 1
                    if self.config["syntax_highlighting"]:
                        self.syntax_split_screen()

            elif self.config["splitscreen"] and c in (338, self.config["key_page_down"]):  # PAGE DOWN
                self.program_message = ""
                if self.config["splitscreen"] < self.lines.total - 1:
                    self.config["splitscreen"] += 1
                    if self.config["syntax_highlighting"]:
                        self.syntax_split_screen()

            elif c == self.config["key_page_up"]:
                self.page_up()
            elif c == self.config["key_page_down"]:
                self.page_down()

            elif c == self.config["key_entry_window"]:
                if self.lines.locked:
                    self.read_mode_entry_window()
                else:
                    self.enter_commands()  # Control E pulls up dialog box

            elif c == self.config["key_find"]:
                self.reset_needed = False
                self.find_window()

            elif c == self.config["key_find_again"] and not self.last_search:
                self.reset_needed = False
                self.find_window()
            elif c == self.config["key_find_again"] and self.last_search:
                self.reset_needed = False  # fix bug that was deleting lines
                self.program_message = ""
                # find("find %s" %last_search) #Press control-g to find again
                self.find("find")  # Press control -g to find again
            elif c == self.config["key_deselect_all"] and self.lines.locked:  # In read only mode, deselects selection
                self.last_search = ''
                self.unmark_all()
            elif c == self.config["key_deselect_all"]:
                self.deselect_all()  # Press control-a to deselect lines
            elif self.config["debug"] and c == self.config["key_next_bug"]:
                self.bug_hunt()  # Press control-d to move to line with 'bug'
            elif not self.config["debug"] and c == self.config["key_next_bug"] and \
                    self.get_confirmation("Turn on debug mode? (y/n)"):
                self.reset_needed = False
                self.toggle_debug('debug on')
            elif c == self.config['key_next_marked']:
                self.goto_marked()  # goto next marked line if control-n is pressed
            elif c == self.config['key_previous_marked']:
                self.prev_marked()  # goto prev marked line if control-b is pressed

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

    def read_mode_entry_window(self):
        """Enter commands in 'Entry Window'"""
        # global reset_needed, program_message
        self.program_message = ''
        self.reset_needed = False
        text = self.window.prompt_user()
        if self.command_match(text, 'load', 'read', False):
            self.lines.locked = False
            self.load_command(text)
        elif self.command_match(text, 'new', '<@>_foobar_', False):
            self.new_doc()

        elif self.command_match(text, 'find', 'mark', False):
            for i in range(1, len(self.lines.db) + 1):
                self.lines.db[i].marked = False
            self.mark(text)
            self.find(text)

        elif text in ('unmark all', 'unmark off'):
            self.unmark_all()
        elif self.command_match(text, 'unmark', '<@>_foobar_', False):
            self.unmark(text)
        elif self.command_match(text, 'goto', '<@>_foobar_', False):
            self.goto(text)
        elif self.command_match(text, 'quit', '<@>_foobar_', False):
            self.quit()
        elif self.command_match(text, 'split', 'splitscreen'):
            self.toggle_split_screen(text)  # toggle splitscreen
        elif self.command_match(text, 'show split', 'hide split'):
            self.toggle_split_screen(text)
        elif self.command_match(text, 'show splitscreen', 'hide splitscreen'):
            self.toggle_split_screen(text)
        elif text == "help":
            if self.get_confirmation('Load HELP GUIDE? Current doc will be purged! (y/n)'):
                self.window.show_help()
        elif self.command_match(text, 'prev', 'previous', False):
            self.prev()
        else:
            self.get_confirmation('That command not allowed in read mode!', True)

    def toggle_acceleration(self, text):
        """Turn acceleration on or off"""
        # global program_message
        arg = self.get_args(text)
        self.reset_line()
        if arg not in ('on', 'off') and self.config['cursor_acceleration']:
            arg = 'off'
        elif arg not in ('on', 'off') and not self.config['cursor_acceleration']:
            arg = 'on'
        if arg == 'on':
            self.config['cursor_acceleration'] = True
            self.program_message = ' Cursor acceleration on '
        elif arg == 'off':
            self.config['cursor_acceleration'] = False
            self.program_message = ' Cursor acceleration off '

    def toggle_page_guide(self, text):
        """Toggle page guide (shows page guide)
            Default width of page is 80 characters."""
        # global program_message
        self.program_message = ' Page guide turned off '
        if 'off' in text or 'hide' in text:
            self.config['page_guide'] = False
        elif text in ['guide', 'pageguide'] and self.config['page_guide']:
            self.config['page_guide'] = False
        elif self.get_args(text) not in ['guide', 'pageguide'] and 'show' not in text and 'on' not in text:
            try:
                num = int(self.get_args(text))
                if num < 1:
                    num = 80
                self.config['page_guide'] = num
                self.program_message = f' Page guide - {num:d} characters '
            except BareException:
                self.program_message = ' Error occurred, nothing changed! '
                self.reset_line()
                return
        else:
            self.config['page_guide'] = 80
            self.program_message = ' Page guide turned on '
        if self.config['page_guide'] > self.window.width - 7:
            if self.window.width > 59:
                self.program_message = \
                    f' Error, terminal too small for {self.config["page_guide"]:d} character page guide! '
            else:
                self.program_message = ' Error, page guide not displayed '
            self.config['page_guide'] = False
        self.reset_line()

    def enter_commands(self):
        """Enter commands in 'Entry Window'"""
        # global reset_needed, program_message

        self.program_message = ''
        if self.lines.db[self.current_num].text and \
                self.current_num == self.lines.total:  # create empty line if position is last line
            self.lines.add()  # create emtpy line

        self.reset_needed = False
        text = self.window.prompt_user()
        if self.command_match(text, 'load', 'read', False):
            self.load_command(text)
        elif self.command_match(text, 'find', '<@>_foobar_', False):
            self.find(text)
        elif self.command_match(text, 'save', '<@>_foobar_', False):
            self.save(self.save_path)
        elif self.command_match(text, 'new', '<@>_foobar_', False):
            self.new_doc()

        # Action on marked lines
        elif self.command_match(text, 'expand marked', 'expandmarked', False):
            self.lines.expand(self.mark_items('expand'))
        elif self.command_match(text, 'collapse marked', 'collapsemarked', False):
            self.lines.collapse(self.mark_items('collapse'))
        elif self.command_match(text, 'comment marked', 'commentmarked', False):
            self.comment(self.mark_items('comment'))
        elif self.command_match(text, 'uncomment marked', 'uncommentmarked', False):
            self.uncomment(self.mark_items('uncomment'))
        elif self.command_match(text, 'indent marked', 'indentmarked', False):
            self.indent(self.mark_items('indent'))
        elif self.command_match(text, 'unindent marked', 'unindentmarked', False):
            self.unindent(self.mark_items('unindent'))
        elif self.command_match(text, 'replacemarked', '<@>_foobar_', False):
            self.replace_marked(self.current_line.text)
        elif self.command_match(text, 'copy marked', 'copymarked', False):
            self.copy(self.mark_items('copy'))
        elif self.command_match(text, 'delete marked', 'deletemarked', False):
            self.delete_lines(self.mark_items('delete'))
        elif self.command_match(text, 'cut marked', 'cutmarked', False):
            self.cut(self.mark_items('cut'))

        # Action on selected lines
        elif self.command_match(text, 'expand selected', 'expand selection', False):
            self.lines.expand(self.select_items('expand'))
        elif self.command_match(text, 'collapse selected', 'collapse selection', False):
            self.lines.collapse(self.select_items('collapse'))
        elif self.command_match(text, 'comment selected', 'comment selection', False):
            self.comment(self.select_items('comment'))
        elif self.command_match(text, 'uncomment selected', 'uncomment selection', False):
            self.uncomment(self.select_items('uncomment'))
        elif self.command_match(text, 'indent selected', 'indent selection', False):
            self.indent(self.select_items('indent'))
        elif self.command_match(text, 'unindent selected', 'unindent selection', False):
            self.unindent(self.select_items('unindent'))
        elif self.command_match(text, 'copy selected', 'copy selection', False):
            self.copy(self.select_items('copy'), True)
        elif self.command_match(text, 'delete selected', 'delete selection', False):
            self.delete_lines(self.select_items('delete'))
        elif self.command_match(text, 'cut selected', 'cut selection', False):
            self.cut(self.select_items('cut'))
        elif self.command_match(text, 'select reverse', 'select invert', False):
            self.invert_selection()
        elif self.command_match(text, 'invert', 'invert selection', False):
            self.invert_selection()

        elif text == 'indent':
            self.indent(f'indent {str(self.current_line.number)}')
        elif self.command_match(text, 'indent', '<@>_foobar_', False):
            self.indent(text)
        elif text == 'unindent':
            self.unindent(f'unindent {str(self.current_line.number)}')
        elif self.command_match(text, 'unindent', '<@>_foobar_', False):
            self.unindent(text)
        elif self.command_match(text, 'replace', '<@>_foobar_', False):
            self.replace_text(text)
        elif text == 'copy':
            self.copy(f'copy {str(self.current_line.number)}')
        elif self.command_match(text, 'copy', '<@>_foobar_', False):
            self.copy(text)
        elif text == 'paste' and len(self.clipboard) > 1:
            self.get_confirmation('Error, multiple lines in memory. Specify line number.', True)
        elif self.command_match(text, 'paste', '<@>_foobar_', False):
            self.paste(text)
        elif text == 'cut':
            self.cut(f'cut {self.current_line.number:d}')  # if no args, cut current line
        elif self.command_match(text, 'cut', '<@>_foobar_', False):
            self.cut(text)
        elif self.command_match(text, 'mark', '<@>_foobar_', False):
            self.mark(text)
        elif text in ('unmark all', 'unmark off'):
            self.unmark_all()
        elif self.command_match(text, 'unmark', '<@>_foobar_', False):
            self.unmark(text)

        # Selecting/deselecting
        elif text in ('deselect', 'unselect'):
            self.deselect('deselect %s' % str(self.current_line.number))
        elif self.command_match(text, 'deselect all', 'unselect all', False):
            self.deselect_all()  # deselects all lines
        elif self.command_match(text, 'select off', 'select none', False):
            self.deselect_all()  # deselects all lines
        elif self.command_match(text, 'deselect', 'unselect', False):
            self.deselect(text)
        elif self.command_match(text, 'select up', 'select up', False):
            self.select_up(text)
        elif self.command_match(text, 'select down', 'select down', False):
            self.select_down(text)
        elif self.command_match(text, 'select', 'select', False):
            self.select(text)

        elif self.command_match(text, 'goto', '<@>_foobar_', False):
            self.goto(text)
        elif text == 'delete':
            self.delete_lines('delete %i' % self.current_num)  # delete current line if no argument
        elif self.command_match(text, 'delete', '<@>_foobar_', False):
            self.delete_lines(text)
        elif self.command_match(text, 'quit', '<@>_foobar_', False):
            self.quit()
        elif self.command_match(text, 'show', 'hide', False):
            self.show_hide(text)
        elif text == 'collapse':
            self.lines.collapse(f'collapse {str(self.current_line.number)}')
        elif text == 'collapse':
            self.lines.collapse(f'collapse {str(self.current_line.number)}')
        elif text == 'collapse all':
            self.lines.collapse(f'collapse 1 - {str(len(self.lines.db))}')
        elif self.command_match(text, 'collapse', '<@>_foobar_', False):
            self.lines.collapse(text)
        elif text == 'expand':
            self.lines.expand(f'expand {str(self.current_line.number)}')
        elif text == 'expand':
            self.lines.expand(f'expand {str(self.current_line.number)}')
        elif text == 'expand all':
            self.lines.expand_all()
        elif self.command_match(text, 'expand', '<@>_foobar_', False):
            self.lines.expand(text)
        elif self.command_match(text, 'undo', '<@>_foobar_', False):
            self.undo()
        elif text == 'comment':
            self.comment(f'comment {str(self.current_line.number)}')
        elif self.command_match(text, 'comment', '<@>_foobar_', False):
            self.comment(text)
        elif text == 'uncomment':
            self.uncomment(f'uncomment {str(self.current_line.number)}')
        elif self.command_match(text, 'uncomment', '<@>_foobar_', False):
            self.uncomment(text)
        elif self.command_match(text, 'run', '<@>_foobar_', False):
            self.run()
        elif self.command_match(text, 'debug', '<@>_foobar_', False):
            self.toggle_debug(text)
        elif self.command_match(text, 'syntax', '<@>_foobar_', False):
            self.toggle_syntax(text)

        elif self.command_match(text, 'whitespace', '<@>_foobar_', False):
            self.toggle_whitespace(text)
        elif self.command_match(text, 'show whitespace', 'hide whitespace', False):
            self.toggle_whitespace(text)
        elif self.command_match(text, 'guide', 'pageguide', False):
            self.window.toggle_page_guide(text)
        elif text == 'color on':
            self.window.color_on()

        elif self.command_match(text, 'split', 'splitscreen'):
            self.toggle_split_screen(text)  # toggle splitscreen
        elif self.command_match(text, 'commands off', '<@>_foobar_', False):
            self.config['inline_commands'] = False
            self.program_message = ' Inline commands turned off! '
        elif self.command_match(text, 'commands on', '<@>_foobar_', False):
            self.config['inline_commands'] = True
            self.program_message = ' Inline commands turned on! '
        elif self.command_match(text, 'commands protected', '<@>_foobar_', False):
            self.config['inline_commands'] = 'protected'
            self.program_message = f" Inline commands protected with '{self.config['protect_string']}' "
        elif self.command_match(text, 'protect', '<@>_foobar_', False):
            self.toggle_protection(text)
        elif self.command_match(text, 'timestamp', '<@>_foobar_', False):
            self.time_stamp()
        elif text == 'help':
            if self.get_confirmation('Load HELP GUIDE? Current doc will be purged! (y/n)'):
                self.window.show_help()
        elif self.command_match(text, 'help', '<@>_foobar_', False):
            self.function_help(text)

        # New commands (should be last round)
        elif self.command_match(text, 'entry', '<@>_foobar_', False):
            self.toggle_entry(text)
        elif self.command_match(text, 'live', '<@>_foobar_', False):
            self.toggle_live(text)
        elif self.command_match(text, 'strip', '<@>_foobar_', False):
            if self.get_confirmation('Strip extra spaces from lines? (y/n)'):
                self.strip_spaces()  # text)
        elif self.command_match(text, 'savesettings', 'saveprefs', False):
            if self.get_confirmation('Save current settings? (y/n)'):
                self.config.save_settings()
        elif self.command_match(text, 'setcolors', 'setcolor', False):
            self.window.set_colors()
        elif self.command_match(text, 'isave', '<@>_foobar_', False):
            self.isave()
        elif self.command_match(text, 'auto', '<@>_foobar_', False):
            self.toggle_auto(text)
        elif self.command_match(text, 'formatting', '<@>_foobar_', False):
            self.toggle_comment_formatting(text)
        elif self.command_match(text, 'tabs', 'tab', False):
            self.toggle_tabs(text)
        elif self.command_match(text, 'prev', 'previous', False):
            self.prev()
        elif self.command_match(text, 'acceleration', 'accelerate', False):
            self.toggle_acceleration(text)
        elif self.command_match(text, 'revert', '<@>_foobar_', False):
            self.revert()
        elif self.command_match(text, 'saveas', '<@>_foobar_', False):
            if len(text) > 7:
                temp_path = text[7:]
            elif not self.save_path:
                temp_path = False
            else:
                (full_path, filename) = os.path.split(self.save_path)
                temp_path = filename
            if not temp_path:
                temp_path = ''
            if self.save_path:
                part1 = os.path.split(self.save_path)[0]
                part2 = temp_path
                temp_path = part1 + '/' + part2
            if '/' not in temp_path:
                temp_path = (os.getcwd() + '/' + temp_path)
            saveas_path = self.window.prompt_user('SAVE FILE AS:', temp_path,
                                                  "(press 'enter' to proceed, UP arrow to cancel)", True)
            if saveas_path:
                self.save(saveas_path)
            else:
                self.program_message = ' Save aborted! '

        else:
            if text:
                self.program_message = ' Command not found! '
            else:
                self.program_message = ' Aborted entry '

    def quit(self, confirm_needed=True, message=''):
        """Gracefully exits program"""
        # global break_now
        self.app.break_now = True
        if not self.saved_since_edit and confirm_needed and not self.get_confirmation(' Quit without saving? (y/n) '):
            return
        curses.nocbreak()
        self.window.keypad(0)
        curses.echo()  # to turn off curses settings
        curses.endwin()  # restore terminal to original condition
        if message:
            print(message)
