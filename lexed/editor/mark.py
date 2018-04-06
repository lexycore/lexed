from lexed.editor.meta import EditorMeta, BareException


class EditorMark(EditorMeta):
    def __init__(self):
        super().__init__()

    def mark(self, text):
        """Function that flags lines as 'marked'.

        Can mark line numbers or lines containing text string

            ex: mark myFunction()
                mark 1-10
                mark 16,33"""

        # global program_message, current_num
        is_number = False
        mark_total = 0
        line_total = 0

        self.reset_line()

        if len(text) <= 5:  # if no arguments, mark current line and return
            self.lines.db[self.current_num].marked = True
            self.program_message = ' Marked line number %i ' % self.current_num
            return

        temp_text = text[5:]

        try:
            if temp_text.replace(' ', '').replace('-', '').replace(',', '').isdigit():
                is_number = True
        except BareException:
            is_number = False

        try:
            if is_number:
                if ',' in text:
                    arg_list = self.get_args(text, ' ', ',')
                    for i in range(len(arg_list) - 1, -1, -1):
                        num = int(arg_list[i])
                        self.lines.db[num].marked = True
                        if self.config['syntax_highlighting']:
                            self.lines.db[num].add_syntax()
                        line_total += 1
                        if len(arg_list) > 200 and self.lines.total > 500 and num / 10.0 == int(num / 10.0):
                            self.status_message(
                                'Processing: ', (100 / ((len(arg_list) + 1) * 1.0 / (num + 1))))
                elif '-' in text:
                    arg_list = self.get_args(text, ' ', '-')
                    start = max(1, int(arg_list[0]))
                    end = min(len(self.lines.db), int(arg_list[1]))
                    for i in range(end, start - 1, - 1):
                        self.lines.db[i].marked = True
                        if self.config['syntax_highlighting']:
                            self.lines.db[i].add_syntax()
                        line_total += 1

                        if (end - start) > 200 and self.lines.total > 500 and i / 10.0 == int(i / 10.0):
                            self.status_message('Processing: ', (100 / ((end - start) * 1.0 / line_total)))

                else:
                    arg_list = self.get_args(text)
                    if 'str' in str(type(arg_list)):
                        num = int(arg_list)
                    else:
                        num = int(arg_list[0])
                    self.lines.db[num].marked = True
                    if self.config['syntax_highlighting']:
                        self.lines.db[num].add_syntax()
                    self.program_message = f' Marked line number {num:d} '
                    line_total += 1

            else:  # if not number, search for text
                find_this = temp_text
                for i in range(1, len(self.lines.db) + 1):
                    item = self.lines.db[i]
                    if self.lines.total > 500 and i / 10.0 == int(i / 10.0):
                        self.status_message('Processing: ',
                                            (100 / ((len(self.lines.db) + 1) * 1.0 / (i + 1))))
                    if find_this in item.text or find_this == item.text:
                        item.marked = find_this
                        mark_total += item.text.count(find_this)
                        line_total += 1
                        if self.config['syntax_highlighting']:
                            item.add_syntax()

            if mark_total > 1:
                self.program_message = f' Marked {line_total} lines ({mark_total} items) '
            elif line_total > 1 and not self.program_message:
                self.program_message = f' Marked {line_total} lines '
            elif line_total == 1 and not self.program_message:
                self.program_message = ' Marked 1 line '
            elif not self.program_message:
                self.program_message = ' No items found! '
        except BareException:
            self.program_message = ' Error, mark failed! '

    def mark_items(self, _type):
        """Returns string of marked lines.
                Type of command to be executed must be passed

                example: markItems("copy")
        """
        mark_string = ''
        word1 = _type.capitalize()
        if self.get_confirmation(f'{word1} ALL marked lines? (y/n)'):
            for i in range(1, len(self.lines.db) + 1):
                if self.lines.db[i].marked:
                    num = self.lines.db[i].number
                    mark_string += f'{num},'
            if mark_string.endswith(','):
                mark_string = mark_string[0:-1]
            return f'{_type} {mark_string}'

    def unmark(self, text):
        """Function that flags lines as 'unmarked'."""
        # global program_message
        is_number = False
        mark_total = 0

        self.reset_line()

        if len(text) <= 7:  # if no arguments, unmark current line and return
            self.lines.db[self.current_num].marked = False
            if self.config['syntax_highlighting']:
                self.lines.db[self.current_num].add_syntax()
            self.program_message = ' Unmarked line number %i ' % self.current_num
            return

        temp_text = text[7:]

        try:
            if temp_text.replace(' ', '').replace('-', '').replace(',', '').isdigit():
                is_number = True
        except BareException:
            is_number = False

        try:
            if is_number:
                if ',' in text:
                    arg_list = self.get_args(text, ' ', ',')
                    for i in range(len(arg_list) - 1, -1, -1):
                        num = int(arg_list[i])
                        self.lines.db[num].marked = False
                        if self.config['syntax_highlighting']:
                            self.lines.db[num].add_syntax()
                        mark_total += 1
                        if len(arg_list) > 200 and self.lines.total > 500 and i / 10.0 == int(i / 10.0):
                            self.status_message(
                                'Processing: ', (100 / ((len(arg_list) + 1) * 1.0 / (i + 1))))
                elif '-' in text:
                    arg_list = self.get_args(text, ' ', '-')
                    start = max(1, int(arg_list[0]))
                    end = min(len(self.lines.db), int(arg_list[1]))
                    for i in range(end, start - 1, - 1):
                        was_marked = False
                        if self.lines.db[i].marked:
                            was_marked = True
                        self.lines.db[i].marked = False
                        if self.config['syntax_highlighting'] and was_marked:
                            self.lines.db[i].add_syntax()
                        mark_total += 1
                        self.status_message('Processing: ', (100 / ((end - start) * 1.0 / mark_total)))

                else:
                    arg_list = self.get_args(text)
                    if 'str' in str(type(arg_list)):
                        num = int(arg_list)
                    else:
                        num = int(arg_list[0])
                    self.lines.db[num].marked = False
                    if self.config['syntax_highlighting']:
                        self.lines.db[num].add_syntax()
                    self.program_message = f' Unmarked line number {num} '
                    mark_total += 1

            else:  # if not number, search for text
                find_this = temp_text
                for i in range(1, len(self.lines.db) + 1):
                    item = self.lines.db[i]
                    if self.lines.total > 500 and i / 10.0 == int(i / 10.0):
                        self.status_message('Processing: ', (
                                100 / ((len(self.lines.db) + 1) * 1.0 / (i + 1))))
                    if find_this in item.text or find_this == item.text:
                        item.marked = False
                        if self.config['syntax_highlighting']:
                            self.lines.db[i].add_syntax()
                        mark_total += 1
            if mark_total > 1:
                self.program_message = f' Unmarked {mark_total} lines '
            elif mark_total == 1 and not self.program_message:
                self.program_message = ' Unmarked 1 line '
            elif not self.program_message:
                self.program_message = ' No items found! '
        except BareException:
            self.program_message = ' Error, mark failed! '

    def unmark_all(self):
        """Unmark all lines"""
        # global program_message
        self.program_message = ' All lines unmarked '
        for i in range(1, len(self.lines.db) + 1):
            was_marked = False
            if self.lines.db[i].marked:
                was_marked = True
            self.lines.db[i].marked = False
            if self.config['syntax_highlighting'] and was_marked:
                self.lines.db[i].add_syntax()
            if self.lines.total > 500 and i / 20.0 == int(i / 20.0):
                self.status_message('Processing: ', (100 / ((len(self.lines.db) + 1) * 1.0 / (i + 1))))
        self.reset_line()

    def goto_marked(self):
        """Move to next 'marked' line"""
        # global current_num, program_message, prev_line
        if self.current_num < self.lines.total:
            for i in range(self.current_num + 1, len(self.lines.db) + 1):
                if self.lines.db[i].marked:
                    self.prev_line = self.current_num
                    self.current_num = self.lines.db[i].number
                    if self.config['syntax_highlighting']:
                        self.syntax_visible()
                    return
        for i in range(1, self.current_num):
            if self.lines.db[i].marked:
                self.prev_line = self.current_num
                self.current_num = self.lines.db[i].number
                if self.config['syntax_highlighting']:
                    self.syntax_visible()
                return
        if self.lines.db[self.current_num].marked:
            self.program_message = ' No other lines marked! '
        else:
            self.program_message = ' No lines marked! '

    def prev_marked(self):
        """Move to previous 'marked' line"""
        # global current_num, program_message, prev_line
        if self.current_num > 1:
            for i in range(self.current_num - 1, 0, -1):
                if self.lines.db[i].marked:
                    self.prev_line = self.current_num
                    self.current_num = self.lines.db[i].number
                    if self.config['syntax_highlighting']:
                        self.syntax_visible()
                    return
        for i in range(self.lines.total, self.current_num, -1):
            if self.lines.db[i].marked:
                self.prev_line = self.current_num
                self.current_num = self.lines.db[i].number
                if self.config['syntax_highlighting']:
                    self.syntax_visible()
                return
        if self.lines.db[self.current_num].marked:
            self.program_message = ' No other lines marked! '
        else:
            self.program_message = ' No lines marked! '

    def replace_marked(self, text):
        """Replace items in marked lines only"""
        # global program_message, saved_since_edit
        count = 0
        mark_total = 0
        self.reset_line()
        for i in range(1, len(self.lines.db) + 1):  # count number of marked lines
            if self.lines.db[i].marked:
                mark_total += 1
        if mark_total == 0:
            self.get_confirmation('No lines are marked!', True)
            self.program_message = ' Replace operation failed! '
            return
        if not self.get_confirmation(f'Do replace operation on {mark_total:d} marked lines? (y/n)'):
            self.program_message = ' Replace operation aborted! '
            return
        try:
            if 'replace marked' in text:
                text = text.replace('replace marked', 'replacemarked')
            if '|' in text:
                (old_text, new_text) = self.get_args(text, ' ', '|', False)
            else:
                (old_text, new_text) = self.get_args(text, ' ', ' with ', False)
        except BareException:
            self.get_confirmation('Error occurred, replace operation failed!', True)
            return

        self.update_que('REPLACE operation')
        self.update_undo()

        for i in range(1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if item.marked and old_text in item.text:
                item.text = item.text.replace(old_text, new_text)
                count += 1
                if self.config['syntax_highlighting']:
                    item.add_syntax()  # adjust syntax
                if self.config['debug'] and i > 1:
                    item.error = False
                    self.error_test(item.number)  # test for code errors

        self.program_message = f' Replaced {count:d} items '
        if count == 0:
            self.get_confirmation('   Item not found.    ', True)
        else:
            self.saved_since_edit = False

    def find_window(self):
        """Opens Find window"""
        # global program_message
        find_this = self.window.prompt_user('Find what item?')
        if find_this:
            if self.lines.locked:  # In read only mode, find & mark join forces
                for i in range(1, len(self.lines.db) + 1):
                    self.lines.db[i].marked = False
                self.mark(f'mark {str(find_this)}')
            self.find(f'find {str(find_this)}')
        else:
            self.program_message = ' Aborted search '
