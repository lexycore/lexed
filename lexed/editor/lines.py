from lexed.editor.meta import EditorMeta, BareException


class EditorLines(EditorMeta):
    def __init__(self):
        super().__init__()

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

        except BareException:
            self.get_confirmation('Error occurred, nothing deleted!', True)

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

    def strip_spaces(self):  # , text):
        """Strips extra/trailing spaces from line"""
        # global program_message, saved_since_edit
        self.reset_line()
        self.update_que('STRIP WHITESPACE operation')
        self.update_undo()
        count = 0
        for num in range(1, self.lines.total + 1):
            item = self.lines.db[num]
            if item.text and item.text.count(' ') == len(item.text):
                item.text = ''
                if self.config['syntax_highlighting']:
                    item.add_syntax()
                if self.config['debug']:
                    self.error_test(item.number)
                count += 1
            else:
                for i in range(64, 0, -1):
                    search = (i * ' ')
                    if item.text.endswith(search):
                        item.text = item.text[:-i]
                        if self.config['syntax_highlighting']:
                            item.add_syntax()
                        if self.config['debug']:
                            self.error_test(item.number)
                        count += 1
        if not count:
            self.program_message = ' No extra whitespace found! '
        else:
            self.program_message = f' {count:d} lines stripped '
            self.saved_since_edit = False
