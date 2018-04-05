import os

from lexed.editor.meta import EditorMeta, BareException


class EditorFiles(EditorMeta):
    def __init__(self):
        super().__init__()

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
        except BareException:
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
        except BareException:
            self.get_confirmation('Error - file/path does not exist!', True)
            self.program_message = ' Load failed! '
            return
        try:
            if self.lines.db:
                del self.lines.db
                self.lines.db = {}
        except BareException:
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
            string = string.replace('\f', '')  # form feed character, apparently used as separator?

            line = self.lines.add(string)

            if count in (1, 2, 3, 10, 100):  # check to see if encoding understood
                try:
                    self.window.screen.addstr(0, 0, line.text[0:self.window.width])  # Tests output
                    self.window.screen.addstr(0, 0, (' ' * self.window.width))  # clears line
                except BareException:
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

        self.prev_line = self.current_num

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
            if '~' in file_path:
                file_path = file_path.replace('~', os.path.expanduser('~'))  # changes tilde to full pathname
            if '/' not in file_path and self.save_path and '/' in self.save_path:
                part1 = os.path.split(self.save_path)[0]
                part2 = file_path
                temp_path = part1 + '/' + part2
                file_path = self.window.prompt_user('Save this file?', temp_path)
                if not file_path:
                    self.program_message = ' Save aborted! '
                    return

            elif '/' not in file_path:
                file_path = os.path.abspath(file_path)
            elif '../' in file_path:
                (full_path, filename) = os.path.split(self.save_path)
                file_path = os.path.abspath((full_path + '/' + file_path))

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

        except BareException:
            self.get_confirmation('ERROR - check path, file not saved', True)
            self.program_message = ' Save failed! '
            self.save_path = old_path

    def save_as(self, the_path):
        """Forces open 'save_as' dialog and then saves file"""
        # global program_message
        self.reset_line()
        if not the_path:
            the_path = ''
        if self.save_path:
            part1 = os.path.split(self.save_path)[0]
            part2 = the_path
            the_path = part1 + '/' + part2
        if '/' not in the_path:
            the_path = (os.getcwd() + '/' + the_path)
        save_as_path = self.window.prompt_user('SAVE FILE AS:', the_path,
                                               "(press 'enter' to proceed, UP arrow to cancel)", True)
        if save_as_path:
            self.save(save_as_path)
        else:
            self.program_message = ' Save aborted! '
