from lexed.editor.meta import EditorMeta, BareException


class EditorMoves(EditorMeta):
    def __init__(self):
        super().__init__()

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
            if self.current_line.y != 0:
                self.current_line.y -= 1
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
            position = self.row_size * (
                    self.current_line.number_of_rows - 1 - abs(self.current_line.y)) + self.current_line.x - 6
            try:
                if position <= self.current_line.indentation and \
                        self.current_line.text[position - 3:position + 1] and \
                        self.current_line.indentation / 4.0 == int(self.current_line.indentation / 4.0):  # delete tab
                    del temp_list[position - 4:position]
                    self.current_line.x -= 3  # move cursor position 3 spaces, final one below
                else:
                    del temp_list[position - 1]  # delete position
            except BareException:
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

    def return_key(self):
        """Function that handles return/enter key"""
        # global current_num, text_entered, program_message, saved_since_edit

        self.program_message = ''
        self.saved_since_edit = False

        # new section to deal with undo
        if self.text_entered:
            self.update_undo()
            self.update_que('text entry')

        if self.config['syntax_highlighting']:
            self.syntax_visible()

        if self.current_line.number == self.lines.total and self.current_line.x != 6:
            self.lines.add('')
            self.current_num += 1

        elif self.current_line.text and self.current_line.number_of_rows == 1 and \
                6 < self.current_line.x < self.current_line.end_x:  # split line in two
            part1 = self.current_line.text[:self.current_line.x - 6]
            part2 = self.current_line.text[self.current_line.x - 6:]
            self.split_line(self.current_num, part1, part2)

        elif self.current_line.text and self.current_line.number_of_rows > 1 and \
                self.current_line.y > -(self.current_line.number_of_rows - 1) or \
                self.current_line.x > 6:  # split line in two
            prev_part = ''
            after_part = ''

            current_line1 = self.current_line.row[
                                self.current_line.y + self.current_line.number_of_rows - 1][:self.current_line.x - 6]
            current_line2 = self.current_line.row[
                                self.current_line.y + self.current_line.number_of_rows - 1][self.current_line.x - 6:]

            for i in range(0, -self.current_line.number_of_rows, -1):
                r = i + self.current_line.number_of_rows - 1

                if self.current_line.y > i:
                    prev_part = self.current_line.row[r] + prev_part
                elif self.current_line.y < i:
                    after_part = self.current_line.row[r] + after_part

            part1 = prev_part + current_line1
            part2 = current_line2 + after_part

            self.split_line(self.current_num, part1, part2)

        elif not self.current_line.text:
            self.insert(self.current_line.number)  # new bit, inserts line
            self.current_num += 1
        elif self.current_line.x == self.current_line.end_x:
            self.current_num += 1
            self.lines.db[self.current_num].x = 6
            self.lines.db[self.current_num].y = self.lines.db[self.current_num].end_y
        elif self.current_line.x == 6:
            self.insert(self.current_line.number)  # new bit, inserts line
            self.current_num += 1
        else:
            pass
        self.debug_visible()

    def tab_key(self):
        """program specific function that handles 'tab'"""
        char = ' '
        # global current_line, continue_down, continue_up
        self.continue_down = 0
        self.continue_up = 0
        for i in range(0, 4):
            old_number_of_rows = self.current_line.number_of_rows
            old_x = self.current_line.x
            temp_list = self.current_line.listing
            if self.current_line.y == 0 and self.current_line.x == self.current_line.end_x:
                temp_list.append(char)
            else:
                position = self.row_size * (
                        self.current_line.number_of_rows - 1 - abs(self.current_line.y)) + self.current_line.x - 6
                temp_list.insert(position, char)
            temp_string = ''
            for item in temp_list:
                temp_string += item
            self.current_line.text = temp_string
            self.current_line.x += 1

            if old_number_of_rows != self.current_line.number_of_rows:
                if self.current_line.y != 0:
                    self.current_line.y -= 1
                if self.current_line.y == 0:
                    self.current_line.y -= 1
                    self.current_line.x = old_x + 1

    def prev(self):
        """Goto previous line"""
        # global program_message, prev_line, current_num
        self.reset_line()
        try:
            self.current_num, self.prev_line = self.prev_line, self.current_num
            self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x  # update cursor position
            self.program_message = f' Moved from line {self.prev_line:d} to {self.current_num:d} '
            if self.config['syntax_highlighting']:
                self.syntax_visible()
        except BareException:
            self.program_message = ' Prev failed! '

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
        except BareException:
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
        except BareException:
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

    def goto(self, text):
        """program specific function which moves to given line number"""
        # global current_num, program_message, prev_line
        self.prev_line = self.current_num
        temp_string = text[5:]
        self.reset_line()
        try:
            if not temp_string.isdigit():  # Find function or class
                find_function = 'def ' + temp_string + '('
                find_class = 'class ' + temp_string + '('
                for i in range(1, len(self.lines.db) + 1):
                    item = self.lines.db[i]
                    if item.text.strip().startswith(find_function) or item.text.strip().startswith(find_class):
                        # if item.text.strip().startswith('def'):
                        #     item_found = 'function'
                        # elif item.text.strip().startswith('class'):
                        #     item_found = 'class'
                        temp_string = i
                        break
                if temp_string == text[5:]:
                    if temp_string == 'start':
                        temp_string = 1
                    elif temp_string == 'end':
                        temp_string = self.lines.total
                    else:
                        for i in range(1, len(self.lines.db) + 1):
                            item = self.lines.db[i]
                            if item.text.strip().startswith('def %s' % temp_string) or item.text.strip().startswith(
                                    'class %s' % temp_string):
                                # if item.text.strip().startswith('def'):
                                #     item_found = 'function'
                                # elif item.text.strip().startswith('class'):
                                #     item_found = 'class'
                                temp_string = i
                                break

                if temp_string == text[5:]:
                    self.program_message = ' Specified function/class not found! '
                    return

            self.current_num = max(min(int(temp_string), self.lines.total), 1)
            self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x  # update cursor position
            if self.lines.db[self.current_num].collapsed:
                self.program_message = f' Moved to line {self.current_num} (collapsed) '
            else:
                self.program_message = f' Moved from line {self.prev_line} to {self.current_num} '
            if self.config['syntax_highlighting']:
                self.syntax_visible()
        except BareException:
            self.program_message = ' Goto failed! '
