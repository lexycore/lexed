import os

from lexed.console import curses
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
                    if self.window.self.window.self.window.width >= 69:
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
            self.window.screen.addstr(0, 0, ' ' * (self.window.self.window.self.window.width - 13),
                                      self.config['color_header'])
            self.window.screen.addstr(0, 0, 'Loading...', self.config['color_warning'])
            # new bit to stop random character from appearing
            self.window.screen.addstr(0, self.window.self.window.self.window.width, ' ', self.config['color_header'])
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
                    self.window.screen.addstr(0, 0,
                                              line.text[0:self.window.self.window.self.window.width])  # Tests output
                    self.window.screen.addstr(0, 0, (' ' * self.window.self.window.self.window.width))  # clears line
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
            if line.number <= (self.window.self.window.self.window.height - 2) and self.current_num + total_rows < (
                    self.window.self.window.self.window.height - 2):
                self.current_num += 1

        self.current_num -= 1  # adjustment to fix bug
        if self.current_num > (self.window.self.window.self.window.height - 2):
            self.current_num = (self.window.self.window.self.window.height - 2)
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

    def isave(self):
        """Incremental save - increments last number in filename
                useful for saving versions"""
        # global save_path, program_message
        self.reset_line()
        if not self.save_path:  # stop incremental save if file has not yet been saved
            self.get_confirmation('Save file before using incremental save!', True)
            self.program_message = ' Save failed! '
            return
        (directory, filename) = os.path.split(self.save_path)
        # (short_name, ext) = os.path.splitext(filename)
        if filename.startswith('.'):
            short_name = filename
            ext = ''
        else:
            (short_name, ext) = os.path.splitext(filename)

        number = ''
        for i in range(1, len(short_name) + 1):  # determine if name ends with number
            item = short_name[-i]
            if item.isdigit():
                number = item + number
            else:
                break
        if number:  # increment number at end of filename
            new_num = int(number) + 1
            end = len(short_name) - len(number)
            new_name = short_name[0:end] + str(new_num)
        else:  # add 2 to end of filename
            new_name = short_name + "2"
        new_path = os.path.join(directory, new_name) + ext
        self.save(new_path)

    def directory_attributes(self, file_list, directory, sort_by=None, reverse=None, show_hidden=None):
        """
        Takes list of file names and the parent directory, and returns a sorted list of files, paths, and attributes
        """
        sort_by = sort_by or self.config['default_load_sort']
        reverse = reverse or self.config['default_load_reverse']
        show_hidden = show_hidden or self.config['default_load_invisibles']

        _list = []
        readable_extensions = ('.txt', '.py', '.cpp', '.c', '.sh', '.js')  # , '.pwe'

        for i in range(0, len(file_list)):
            if not show_hidden and not file_list[i].startswith('.') and \
                    not file_list[i].endswith('~'):  # doesn't show hidden files or backup files
                if os.path.isdir((directory + file_list[i])):
                    _list.append(file_list[i])
                else:
                    for item in readable_extensions:  # trims to list to 'readable' files
                        if file_list[i].endswith(item):
                            _list.append(file_list[i])

            elif show_hidden:
                if os.path.isdir((directory + file_list[i])):
                    _list.append(file_list[i])
                else:
                    _list.append(file_list[i])

        if directory.endswith("/"):
            temp_dir = directory[0:-1]
        else:
            temp_dir = directory
        if '/' in temp_dir:
            prev_path = temp_dir.rpartition('/')[0]  # assign ParentDir
        else:
            prev_path = '/'

        prev_dir = ('', '../', prev_path, '', '', 'parent', '')

        directory_contents = []

        for i in range(0, len(_list)):  # cycles through items in trimmed down list and calculates attributes
            file_name = _list[i]

            if os.path.isdir((directory + file_name)):
                file_type = 'DIR'  # determines if item is directory
            elif file_name.endswith('.txt'):
                file_type = 'text'  # could replace with loop!?
            elif file_name.endswith('.py'):
                file_type = 'python'
            # elif file_name.endswith('.pwe'):
            #     file_type = 'encryp'
            elif file_name.endswith('.cpp'):
                file_type = 'c++'
            elif file_name.endswith('.c'):
                file_type = 'c'
            elif file_name.endswith('.sh'):
                file_type = 'shell'
            elif file_name.endswith('.js'):
                file_type = 'jscrpt'
            else:
                file_type = '***'
            try:
                raw_size = os.path.getsize((directory + file_name)) / 1024.00  # get size and convert to kilobytes
            except BareException:
                raw_size = 0
            file_size = "%.2f" % raw_size  # limit to two decimal places (f for float)
            file_size = file_size.rjust(8)
            try:
                mod_date = self.time.strftime('%Y-%m-%d %H:%M',
                                              self.time.localtime(os.path.getmtime((directory + file_name))))
            except BareException:
                mod_date = "????-??-?? ??:??"
            path_to_file = directory + file_name

            # Determine file access
            if not os.access(path_to_file, os.R_OK):
                file_access = 'NO ACCESS!'
            elif os.access(path_to_file, os.X_OK):
                file_access = 'executable'
            elif os.access(path_to_file, os.R_OK) and not os.access(path_to_file, os.W_OK):
                file_access = 'READ ONLY '
            elif os.access(path_to_file, os.R_OK) and os.access(path_to_file, os.W_OK):
                file_access = 'read/write'
            else:
                file_access = 'UNKNOWN!!!'

            if sort_by == 'type':
                sort_me = file_type + file_name.lower()  # sort by file_type, then file_name (case insensitive)
            elif sort_by == 'date':
                sort_me = mod_date + file_name.lower()
            elif sort_by == 'size':
                sort_me = file_size + file_name.lower()
            else:
                sort_me = file_name.lower()
            directory_contents.append((sort_me, file_name, path_to_file, file_size, mod_date, file_type, file_access))

        if not reverse:
            directory_contents.sort()
        else:
            directory_contents.sort(reverse=True)

        directory_contents.insert(0, prev_dir)

        return directory_contents

    def display_list(self, directory, page=1, position=0):
        """Displays scrolling list of files for user to choose from"""
        # c = 0
        # num = 0
        view = 5
        if (not os.path.isdir(directory)) and '/' in directory:
            directory = directory.rpartition('/')[0] + '/'  # removes filename (this bit edited)

        temp_list = os.listdir(directory)
        # _list = []
        sort_type = self.config['default_load_sort']
        reverse_sort = self.config['default_load_reverse']
        show_hidden = self.config['default_load_invisibles']

        directory_contents = self.directory_attributes(temp_list, directory, sort_type, reverse_sort,
                                                       show_hidden)  # get file attributes from function

        while True:  # User can explore menus until they make a selection or cancel out
            total_pages = int(len(directory_contents) / (self.window.self.window.height - 3))
            if len(directory_contents) % (self.window.self.window.height - 3) != 0:
                total_pages += 1

            self.window.clear()
            # print empty lines
            if self.config['color_background']:
                self.window.print_background()
            self.window.addstr(0, 0, (' ' * self.window.self.window.width), self.config['color_header'])  # Print header
            self.window.addstr(self.window.self.window.height, 0, (' ' * self.window.self.window.width),
                               self.config['color_header'])  # Print header

            if len(directory) > self.window.self.window.width - 14:
                temp_string = '... %s' % directory[
                                         (len(
                                             directory) - self.window.self.window.width) + 14:]  # s[len(s)-self.window.self.window.width:]
                self.window.addstr(0, 0, temp_string, self.config['color_header'])  # Print header
            else:
                self.window.addstr(0, 0, directory, self.config['color_header'])  # Print header
            self.window.addstr(0, (self.window.self.window.width - 10),
                               ('page ' + str(page) + '/' + str(total_pages)).rjust(10),
                               self.config['color_header'])
            self.window.hline(1, 0, curses.ACS_HLINE, self.window.self.window.width,
                              self.config['color_bar'])  # print solid line

            self.window.hline(self.window.self.window.height - 1, 0, curses.ACS_HLINE, self.window.self.window.width,
                              self.config['color_bar'])  # print solid line

            if sort_type == 'size':  # change footer based on SortType
                footer_string = '_Home | sort by _Name / *S*i*z*e / _Date / _Type'
            elif sort_type == 'date':
                footer_string = '_Home | sort by _Name / _Size / *D*a*t*e / _Type'
            elif sort_type == 'type':
                footer_string = '_Home | sort by _Name / _Size / _Date / *T*y*p*e'
            else:
                footer_string = '_Home | sort by *N*a*m*e / _Size / _Date / _Type'

            self.window.print_formatted_text(self.window.self.window.height, footer_string)
            if not show_hidden:
                self.window.print_formatted_text(self.window.self.window.height, '| show _. | _-/_+ info | _Quit',
                                                 'rjust', self.window.self.window.width)
            else:
                self.window.print_formatted_text(self.window.self.window.height, '| hide _. | _-/_+ info | _Quit',
                                                 'rjust', self.window.self.window.width)

            # adjust = (page - 1) * (self.window.self.window.height - 3)
            for i in range(0, self.window.self.window.height - 3):
                num = (page - 1) * (self.window.self.window.height - 3) + i
                try:
                    name = directory_contents[num][1]
                    # full_path = directory_contents[num][2]
                    file_size = directory_contents[num][3]
                    file_mod_date = directory_contents[num][4]
                    file_type = directory_contents[num][5]
                    if len(directory_contents[num]) > 6:
                        access = directory_contents[num][6]
                    else:
                        access = ''

                except BareException:
                    break
                # try:
                if position == num:
                    # print empty line
                    self.window.addstr(i + 2, 0, (' ' * self.window.self.window.width), self.config['color_entry'])
                    # print name
                    if name == '../' or name == os.path.expanduser('~'):
                        self.window.addstr(i + 2, 0, name, self.config['color_entry_quote'])
                    else:
                        self.window.addstr(i + 2, 0, name, self.config['color_entry'])
                    # clear second part of screen
                    if view == 6:
                        self.window.addstr(i + 2, (self.window.self.window.width - 54),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 54))),
                                           self.config['color_entry'])
                    if view == 5:
                        self.window.addstr(i + 2, (self.window.self.window.width - 41),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 41))),
                                           self.config['color_entry'])
                    if view == 4:
                        self.window.addstr(i + 2, (self.window.self.window.width - 33),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 33))),
                                           self.config['color_entry'])
                    if view == 3:
                        self.window.addstr(i + 2, (self.window.self.window.width - 21),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 21))),
                                           self.config['color_entry'])
                    if view == 2:
                        self.window.addstr(i + 2, (self.window.self.window.width - 11),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 11))),
                                           self.config['color_entry'])
                    # print file_access
                    if view == 6 and num != 0:
                        if access == 'NO ACCESS!':
                            self.window.addstr(i + 2, self.window.self.window.width - 51, access,
                                               self.config['color_warning'])
                        elif access == 'READ ONLY ':
                            self.window.addstr(i + 2, self.window.self.window.width - 51, access,
                                               self.config['color_entry_quote'])
                        elif access == 'read/write':
                            self.window.addstr(i + 2, self.window.self.window.width - 51, access,
                                               self.config['color_entry_command'])
                        else:
                            self.window.addstr(i + 2, self.window.self.window.width - 51, access,
                                               self.config['color_entry_functions'])

                    # print file_size
                    if view >= 5 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 39, (str(file_size) + ' KB'),
                                           self.config['color_entry'])
                    if view == 4 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 31, (str(file_size) + ' KB'),
                                           self.config['color_entry'])
                    if view == 3 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 19, (str(file_size) + ' KB'),
                                           self.config['color_entry'])
                    # print mod date
                    if view >= 5:
                        self.window.addstr(i + 2, self.window.self.window.width - 25, file_mod_date,
                                           self.config['color_entry'])
                    if view == 4:
                        self.window.addstr(i + 2, self.window.self.window.width - 18, (file_mod_date.split(' ')[0]),
                                           self.config['color_entry'])
                    # print type
                    if view > 1:
                        if file_type == 'parent':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_entry_quote'])
                        elif file_type == 'DIR':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_entry_number'])
                        elif file_type == 'text':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_entry_functions'])
                        elif file_type == 'python':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_entry_command'])
                        elif file_type == 'encryp':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_entry_comment'])
                        else:
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_entry'])
                else:
                    self.window.addstr(i + 2, 0, (' ' * self.window.self.window.width), self.config['color_background'])
                    # print name
                    if name == '../' or name == os.path.expanduser('~'):
                        self.window.addstr(i + 2, 0, name, self.config['color_quote_double'])
                    else:
                        self.window.addstr(i + 2, 0, name, self.config['color_normal'])
                    # clear second part of screen
                    if view == 6:
                        self.window.addstr(i + 2, (self.window.self.window.width - 54),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 54))),
                                           self.config['color_normal'])
                    if view == 5:
                        self.window.addstr(i + 2, (self.window.self.window.width - 41),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 41))),
                                           self.config['color_normal'])
                    if view == 4:
                        self.window.addstr(i + 2, (self.window.self.window.width - 33),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 33))),
                                           self.config['color_normal'])
                    if view == 3:
                        self.window.addstr(i + 2, (self.window.self.window.width - 21),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 21))),
                                           self.config['color_normal'])
                    if view == 2:
                        self.window.addstr(i + 2, (self.window.self.window.width - 11),
                                           (' ' * (self.window.self.window.width - (
                                                   self.window.self.window.width - 11))),
                                           self.config['color_normal'])

                    # print file_access
                    if view == 6 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 51, access, self.config['color_dim'])
                    # print file_size
                    if view >= 5 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 39, (str(file_size) + ' KB'),
                                           self.config['color_dim'])
                    if view == 4 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 31, (str(file_size) + ' KB'),
                                           self.config['color_dim'])
                    if view == 3 and num != 0:
                        self.window.addstr(i + 2, self.window.self.window.width - 19, (str(file_size) + ' KB'),
                                           self.config['color_dim'])
                    # print mod date
                    if view >= 5:
                        self.window.addstr(i + 2, self.window.self.window.width - 25, file_mod_date,
                                           self.config['color_dim'])
                    if view == 4:
                        self.window.addstr(i + 2, self.window.self.window.width - 18, (file_mod_date.split(' ')[0]),
                                           self.config['color_dim'])
                    # print type
                    if view > 1:
                        if file_type == 'parent':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_quote_double'])
                        elif file_type == 'DIR':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_number'])
                        elif file_type == 'text':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_functions'])
                        elif file_type == 'python':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_commands'])
                        elif file_type == 'encryp':
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_warning'])
                        else:
                            self.window.addstr(i + 2, self.window.self.window.width - 6, file_type,
                                               self.config['color_normal'])

                if len(directory) < self.window.self.window.width:
                    self.window.addstr(0, len(directory), "")  # Move cursor
                # except:
                # pass
            self.window.refresh()

            c = self.window.getch()

            if c == curses.KEY_UP:
                position -= 1
            elif c == curses.KEY_DOWN:
                position += 1
            elif c == curses.KEY_RIGHT and page < total_pages:
                page += 1
                position += self.window.self.window.height - 3
            elif c == curses.KEY_RIGHT:
                position += self.window.self.window.height - 3
            elif c == curses.KEY_LEFT:
                page -= 1
                position -= self.window.self.window.height - 3

            elif c == ord('r') and not reverse_sort:  # reverse
                reverse_sort = True
            elif c == ord('r'):
                reverse_sort = False
            elif c == ord('t') and sort_type == 'type' and not reverse_sort:
                reverse_sort = True
            elif c == ord('k') and sort_type == 'type' and not reverse_sort:
                reverse_sort = True
            elif c == ord('t') or c == ord('k'):
                sort_type = 'type'
                reverse_sort = False
            elif c == ord('d') and sort_type == 'date' and reverse_sort:
                reverse_sort = False
            elif c == ord('d'):
                sort_type = 'date'
                reverse_sort = True
            elif c == ord('s') and sort_type == 'size' and reverse_sort:
                reverse_sort = False
            elif c == ord('s'):
                sort_type = 'size'
                reverse_sort = True
            elif c == ord('n') and sort_type == 'name' and not reverse_sort:
                reverse_sort = True
            elif c == ord('n'):
                sort_type = 'name'
                reverse_sort = False
            elif c in (ord('-'), ord('_')):
                view = max(1, view - 1)
            elif c in (ord('='), ord('+')):
                view = min(6, view + 1)

            if self.window.self.window.width < 60 and view > 5:
                view = 5

            elif c == ord('.'):
                if show_hidden:
                    show_hidden = False
                else:
                    show_hidden = True

                temp_list = os.listdir(directory)
                directory_contents = self.directory_attributes(temp_list, directory,
                                                               sort_type, reverse_sort, show_hidden)
                position = 0
                page = 1

            elif c in (ord('q'), ord('Q'), ord('c'), ord('C')):  # c for cancel
                self.reset_line()
                return False

            elif c in (ord('h'), ord('H')):
                directory = (os.path.expanduser('~') + '/')
                temp_list = os.listdir(directory)
                directory_contents = self.directory_attributes(temp_list, directory,
                                                               sort_type, reverse_sort, show_hidden)
                position = 0
                page = 1

            elif c == 10 and directory_contents[position][1] == '../' and directory_contents[position][3] == "":
                directory = (directory_contents[position][2] + '/')
                if directory == '//':
                    directory = '/'
                temp_list = os.listdir(directory)
                directory_contents = self.directory_attributes(temp_list, directory,
                                                               sort_type, reverse_sort, show_hidden)
                position = 0
                page = 1

            elif c == 10 and directory_contents[position][1] == os.path.expanduser('~') and \
                    directory_contents[position][3] == '':
                directory = (directory_contents[position][2] + '/')
                temp_list = os.listdir(directory)
                directory_contents = self.directory_attributes(temp_list, directory,
                                                               sort_type, reverse_sort, show_hidden)
                position = 0
                page = 1

            elif c == 10 and directory_contents[position][5] == 'DIR' and \
                    os.access(directory_contents[position][2], os.R_OK):
                directory = (directory_contents[position][2] + '/')
                temp_list = os.listdir(directory)
                directory_contents = self.directory_attributes(temp_list, directory,
                                                               sort_type, reverse_sort, show_hidden)
                position = 0
                page = 1

            elif c == 10 and self.encoding_readable(directory_contents[position][2]):
                return directory_contents[position][2]

            if c in (ord('r'), ord('t'), ord('d'), ord('s'), ord('n'), ord('k')):  # update directoryContents
                directory_contents = self.directory_attributes(temp_list, directory,
                                                               sort_type, reverse_sort, show_hidden)
                position = 0
                page = 1

            if position + 1 > (self.window.self.window.height - 3) * page and page < total_pages:
                page += 1
            elif position < (self.window.self.window.height - 3) * (page - 1):
                page -= 1
            page = max(1, page)
            page = min(page, int(len(directory_contents) / (self.window.self.window.height - 3)) + 1)
            position = max(0, position)
            position = min(position, len(directory_contents) - 1)

    def encoding_readable(self, the_path):
        """Check file encoding to see if it can be read by program"""
        if not os.access(the_path, os.R_OK):  # return if file not accessible
            self.get_confirmation('Access not allowed!', True)
            return False
        raw_size = os.path.getsize(the_path) / 1024.00  # get size and convert to kilobytes
        if raw_size > 8000:
            if self.get_confirmation('File may not be readable. Continue? (y/n)'):
                return True
            else:
                return False

        _file = open(the_path)
        temp_lines = _file.readlines()
        _file.close()

        try:
            self.window.addstr(0, 0, temp_lines[-1][0:self.window.width], self.config["color_header"])  # Tests output
            if len(temp_lines) > 100:
                self.window.addstr(0, 0, temp_lines[-100][0:self.window.width],
                                   self.config["color_header"])  # Tests output
            self.window.addstr(0, 0, (" " * self.window.width))  # clears line
        except BareException:
            self.get_confirmation("Error, can't read file encoding!", True)
            return False

        skip = int(len(temp_lines) / 10) + 1

        for i in range(0, len(temp_lines), skip):
            string = temp_lines[i]
            string = string.replace("\t", "    ")
            string = string.replace("    ", "    ")
            string = string.replace("\n", "")
            string = string.replace("\r", "")
            string = string.replace("\f", "")  # form feed character, apparently used as separator?

            try:
                self.window.addstr(0, 0, string[0:self.window.width], self.config["color_header"])  # Tests output
                self.window.addstr(0, 0, (" " * self.window.width), self.config["color_header"])  # clears line
            except BareException:
                self.get_confirmation("Error, can't read file encoding!", True)
                return False
        return True

    def revert(self):
        """Revert file to last saved"""
        self.reset_line()
        if self.get_confirmation('Revert to original file? (y/n)'):
            self.update_que('REVERT operation')
            self.update_undo()
            self.load(self.save_path)

    def toggle_auto(self, text):
        """Toggle feature automation (turns on features based on file type)"""
        # global program_message
        self.program_message = ' Auto-settings turned off '
        if 'off' in text:
            self.config['auto'] = False
        elif text == 'auto' and self.config['auto']:
            self.config['auto'] = False
        else:
            self.config['auto'] = True
            self.program_message = ' Auto-settings turned on '
        self.reset_line()
