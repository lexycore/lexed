from copy import deepcopy

from .meta import EditorMeta, BareException


class EditorClipboard(EditorMeta):
    def __init__(self):
        self.clipboard = []
        super().__init__()

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

    def copy(self, text, select_only=False):
        """Copy lines to internal 'clipboard'"""
        # global clipboard, program_message
        self.reset_line()
        if text == 'copy' or select_only:
            selection, item_count = self.get_selected()
            if selection:
                text = f'copy {selection}'
                if self.config['deselect_on_copy']:
                    selection, item_count = self.get_selected()
                    line_list = selection.split(',')
                    for item in line_list:
                        line_num = int(item)
                        self.lines.db[line_num].selected = False
                select_only = True
        length = 1
        try:
            self.clipboard = []
            temp_text = text
            if ',' in temp_text:
                arg_list = self.get_args(temp_text, ' ', ',')
                length = len(arg_list)
                for i in range(len(arg_list) - 1, -1, -1):
                    num = int(arg_list[i])
                    self.clipboard.append(self.lines.db[num].text)

            elif '-' in temp_text:
                arg_list = self.get_args(temp_text, ' ', '-')
                start = int(arg_list[0])
                end = int(arg_list[1])
                length = (end - start) + 1
                if length > 25000:  # Stop copy operations that are too big
                    self.get_confirmation('Copy operation limited to 25000 lines!', True)
                    self.program_message = ' Copy canceled, limit exceeded! '
                    return
                for i in range(end, start - 1, -1):
                    self.clipboard.append(self.lines.db[i].text)
            else:
                arg_list = self.get_args(temp_text)
                if 'str' in str(type(arg_list)):
                    num = int(arg_list)
                else:
                    num = int(arg_list[0])
                self.clipboard.append(self.lines.db[num].text)
                self.program_message = f' Copied line number {num} '
            if select_only:
                self.program_message = f' Selection copied ({length} lines) '
            elif not self.program_message:
                self.program_message = f' {length} lines copied '
        except BareException:
            self.reset_line()
            self.get_confirmation('Error occurred, nothing copied!', True)

    def paste(self, text):
        """Paste lines from 'clipboard'"""
        # global current_num, program_message, saved_since_edit
        original_num = self.current_num
        if not self.clipboard:
            self.get_confirmation('Nothing pasted, clipboard is empty.', True)
            self.reset_line()
            return
        if self.config['select_on_paste']:
            self.deselect_all()
        self.saved_since_edit = False

        length = len(self.clipboard)

        try:
            if self.get_args(text) == 'paste':  # Pastes on current line

                # temp_text = text
                self.reset_line()
                self.update_que('PASTE operation')
                self.update_undo()

                if length > 100 and self.lines.total > 2000:  # New bit to improve performance of BIG paste operations
                    self.program_message = ' Paste aborted! '
                    if self.window.width >= 69:
                        if self.get_confirmation('This operation will expand & unmark lines. Continue? (y/n)'):
                            self.new_paste(self.clipboard, self.current_num)
                        return
                    else:
                        if self.get_confirmation('Lines will be unmarked. Continue? (y/n)'):
                            self.new_paste(self.clipboard, self.current_num)
                        return

                self.current_line.text += self.clipboard[0]
                if self.config['select_on_paste']:
                    self.current_line.selected = True

                if length > 1:
                    for i in range(1, length):
                        self.insert(self.current_num, self.clipboard[i], True)
                        if self.lines.total > 2000 and length > 40 and i / 5.0 == int(i / 5.0):
                            self.status_message('Processing: ', (100 / (length * 1.0 / (i + 1))))

                    self.program_message = f' Pasted {len(self.clipboard):d} lines at line number {original_num:d} '
                else:
                    self.program_message = f' Pasted text at line {self.current_num:d} '
                self.current_num += len(self.clipboard) - 1
                self.lines.db[self.current_num].x = self.lines.db[self.current_num].end_x

            else:
                arg = self.get_args(text)
                num = int(arg)

                self.reset_line()
                if num > len(self.lines.db):  # Stop paste operation
                    self.program_message = f' Error, line {num:d} does not exist! '
                    return
                self.update_que('PASTE operation')
                self.update_undo()

                if length > 100 and self.lines.total > 2000:  # New bit to improve performance of BIG paste operations
                    self.program_message = ' Paste aborted! '
                    if self.window.width >= 69:
                        if self.get_confirmation('This operation will expand & unmark lines. Continue? (y/n)'):
                            self.new_paste(self.clipboard, num)
                        return
                    else:
                        if self.get_confirmation('Lines will be unmarked. Continue? (y/n)'):
                            self.new_paste(self.clipboard, num)
                        return

                for i in range(0, length):
                    self.insert(num, self.clipboard[i], True)
                    if self.lines.total > 2000 and length > 40 and i / 5.0 == int(i / 5.0):
                        self.status_message('Processing: ', (100 / (length * 1.0 / (i + 1))))

                if num <= self.current_num:
                    self.current_num += len(self.clipboard)
                if num > self.lines.total:
                    num = self.lines.total - 1  # fix message bug
                if len(self.clipboard) > 1:
                    self.program_message = f' Pasted (inserted) {(len(self.clipboard)):d} lines at line number {num:d} '
                else:
                    self.program_message = f' Pasted (inserted) text at line {num:d} '
        except BareException:
            self.reset_line()
            self.get_confirmation('Error occurred, nothing pasted!', True)

    def cut(self, text):
        """Combines copy and delete into one operation"""
        # global program_message
        self.reset_line()
        if text.endswith('cut'):
            if self.get_confirmation('Cut selection? (y/n)'):
                self.cut(self.select_items('cut'))
                return
            else:
                self.program_message = ' Cut aborted! '
                return
        temp_text = text.replace('cut', 'copy')
        self.copy(temp_text)
        self.print_header()
        self.delete_lines(temp_text.replace('copy', 'delete'))
