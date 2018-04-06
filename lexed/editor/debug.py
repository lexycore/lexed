import os

from lexed.editor.meta import EditorMeta  # , BareException


class EditorDebug(EditorMeta):
    def __init__(self):
        super().__init__()

    def debug_visible(self):
        """Debugs lines visible on screen only"""  # Added to speed up program
        start = min(self.lines.total, self.current_num + 2)
        end = max(1, self.current_num - self.window.height)

        for i in range(start, end, -1):
            self.lines.db[i].error = False
            self.error_test(self.lines.db[i].number)

    def run(self):
        """Run command executes python code in a separate window"""
        path = os.path.expanduser('~')
        temp_file = os.path.join(path, '.TEMP_lexed_runfile.tmp')

        with open(temp_file, 'w') as text_file:
            text_file.write('try:\n')
            for key in self.lines.db:
                this_text = ('    ' + self.lines.db[key].text + '\n')
                text_file.write(this_text)
            text_file.write(
                'except (NameError, IOError, IndexError, KeyError, SyntaxError, TypeError, ValueError, ZeroDivisionError, IndentationError) as e:\n')
            text_file.write('    print("ERROR: {}".format(e))\n')
            text_file.write('else:\n')
            text_file.write('    print("Run complete.")\n')
            hold_message = """raw_input("Press 'enter' to end")"""
            text_file.write(hold_message)

        # entry_list = []
        # _string = ""
        os.system('%s python %s' % (self.config['terminal_command'], temp_file))  # Run program
        os.system('sleep 1')
        os.system('rm %s' % temp_file)  # Delete tempFile

    def toggle_debug(self, text):
        """Turn debug mode on or off"""
        # global program_message
        arg = self.get_args(text)
        self.reset_line()
        if arg not in ('on', 'off') and self.config['debug']:
            arg = 'off'
        elif arg not in ('on', 'off') and not self.config['debug']:
            arg = 'on'
        if arg == 'on':
            self.config['debug'] = True
            self.program_message = ' Debug on '
        elif arg == 'off':
            self.config['debug'] = False
            self.program_message = ' Debug off '

    def bug_hunt(self):
        """If bugs found, moves you to that part of the program"""
        # global program_message, current_num
        self.program_message = ''
        collapsed_bugs = False
        # Debug current line before moving to next
        self.lines.db[self.current_num].error = False
        self.error_test(self.current_num)

        if self.current_num != len(self.lines.db):
            for i in range(self.current_num + 1, len(self.lines.db) + 1):
                item = self.lines.db[i]
                if item.error and item.collapsed:
                    collapsed_bugs = True
                elif item.error:
                    self.current_num = item.number
                    return

        for i in range(1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if item.error and item.collapsed:
                collapsed_bugs = True
            elif item.error:
                self.current_num = item.number
                return

        if collapsed_bugs:
            self.program_message = ' Bugs found in collapsed sections '
        else:
            self.program_message = ' No bugs found! '

    def function_help(self, text):
        """Get info about classes, functions, and Modules

                Works with both external modules and
                functions/classes defined within program"""
        # global program_message
        self.reset_line()
        if self.window.width < 79:
            self.get_confirmation('Help truncated to fit screen', True)
        find_def = f'def {text[5:]}'
        find_class = f'class {text[5:]}'
        search_string = text[5:]
        if '.' in search_string:
            _name = '.' + search_string.split('.', 1)[1]
        else:
            _name = 'foobar_zyx123'
        count = 0
        # function_num = 0
        doc_string = []
        # _type = ""
        # c = 0
        item_text = ''
        for i in range(1, len(self.lines.db) + 1):
            item_text = self.lines.db[i].text[self.lines.db[i].indentation:]
            if item_text.startswith(find_def + '(') or item_text.startswith(find_def + ' (') or \
                    item_text.startswith(find_class + '(') or item_text.startswith(find_class + ' ('):
                # function_num = i
                _type = item_text[0:4]
                if _type == 'def ':
                    _type = 'FUNCTION'
                if _type == 'clas':
                    _type = 'CLASS'
                # definition = self.lines.db[i].text
                _name = item_text.split(' ', 1)[1]
                if '(' in _name:
                    _name = _name.split('(')[0]
                temp = self.lines.db[i].text.replace(':', '')
                if _type == 'FUNCTION':
                    temp = temp.replace('def ', '')

                doc_string.append(temp)
                if self.lines.db[i + 1].text.strip().startswith('"""'):
                    start = i + 1
                    for n in range(start, len(self.lines.db) + 1):
                        temp = self.lines.db[n].text.replace('"""', '')
                        doc_string.append(temp)
                        if self.lines.db[n].text.endswith('"""'):
                            break

            elif search_string in item_text or _name in item_text:
                if not item_text.startswith('import') and not item_text.startswith('from'):
                    count += 1
        if not doc_string:
            # _type = "MODULE"
            if item_text:
                _name = item_text.split(' ', 1)[1]
            else:
                _name = search_string

            # short_name = _name
            temp_list = self.get_info(search_string, self.get_modules())
            for item in temp_list:
                doc_string.append(item)

        if doc_string:
            if doc_string[-1].strip() == '':
                del doc_string[-1]  # delete last item if blank
            self.window.addstr(0, 0, (' ' * self.window.width), self.config['color_header'])
            self.window.addstr(0, 0, f' {_name} ', self.config['color_message'])
            self.window.addstr(0, self.window.width - 11, f'Used: {count:d}'.rjust(10), self.config['color_header'])
            self.window.hline(1, 0, self.window.curses.ACS_HLINE, self.window.width, self.config['color_bar'])

            start = 0
            while True:
                y = 1
                end = min((start + (self.window.height - 3)), len(doc_string))
                if end < 1:
                    end = 1
                for l in range(start, end):
                    doc_string[l] = doc_string[l].rstrip()
                    y += 1
                    self.window.addstr(y, 0, (' ' * self.window.width), self.config['color_background'])
                    if len(doc_string[l]) > self.window.width:
                        self.window.addstr(y, 0, doc_string[l][0:self.window.width], self.config['color_quote_double'])
                    else:
                        self.window.addstr(y, 0, doc_string[l], self.config['color_quote_double'])
                if len(doc_string) < (self.window.height - 2):
                    self.window.hline(end + 2, 0, self.window.curses.ACS_HLINE, self.window.width, self.config[
                        'color_bar'])
                    self.window.addstr(end + 2, self.window.width, '')  # move cursor

                else:
                    self.window.hline(self.window.height - 1, 0, self.window.curses.ACS_HLINE,
                                      self.window.width, self.config['color_bar'])
                    string = ' _Start | _End | Navigate with ARROW keys'
                    self.window.addstr(self.window.height, 0, (' ' * self.window.width),
                                       self.config['color_header'])  # footer
                    self.window.print_formatted_text(self.window.height, string)
                    self.window.print_formatted_text(self.window.height, '| _Quit ', 'rjust', self.window.width)
                self.window.refresh()
                c = self.window.getch()
                if c == ord('q'):
                    break
                elif len(doc_string) < (self.window.height - 4) and c != 0:
                    # Exit on key press if help is less than a page
                    break

                elif c in (ord('s'), ord('S')):
                    start = 0
                elif c in (ord('e'), ord('E')):
                    start = len(doc_string) - (self.window.height - 3)
                elif c == self.window.curses.KEY_DOWN:
                    start += 1
                elif c == self.window.curses.KEY_UP:
                    start -= 1
                elif c == self.window.curses.KEY_LEFT or c == ord('b'):
                    start -= (self.window.height - 3)
                elif c == self.window.curses.KEY_RIGHT or c == 32:
                    start += (self.window.height - 3)

                start = min(start, len(doc_string) - (self.window.height - 3))
                if len(doc_string) < (self.window.height - 3):
                    start = 0
                if start < 0:
                    start = 0

        if not doc_string:
            self.program_message = f" Help for '{search_string}' not available! "

    @staticmethod
    def get_info(this_item, module_list=None):
        """Get info about python modules"""
        module_list = module_list or ['os', 'sys', 'random']
        import_string = ''
        for item in module_list:
            import_string += str(f'import {item}; ')

        p = os.popen(f"python -c '{import_string} help({this_item})'")

        help_list = p.readlines()
        p.close()
        return help_list

    def get_modules(self):
        """Finds modules in current document"""
        module_list = []
        for i in range(1, len(self.lines.db) + 1):
            text = self.lines.db[i].text
            text = text.strip()
            if text.startswith('import ') or text.startswith('from '):
                text = text.replace('import ', '')
                text = text.replace('from ', '')
                if ';' in text:
                    for item in text.split(';'):
                        if ' ' in item and item.startswith(' '):
                            module = item.split(' ')[1]
                        elif ' ' in item:
                            module = item.split(' ')[0]
                        else:
                            module = item.replace(' ', '')
                        module_list.append(module)
                elif ',' in text:
                    for item in text.split(','):
                        if ' ' in item and item.startswith(' '):
                            module = item.split(' ')[1]
                        elif ' ' in item:
                            module = item.split(' ')[0]
                        else:
                            module = item.replace(' ', '')
                        module_list.append(module)
                elif ' ' in text:
                    module = text.split(' ')[0]
                    module_list.append(module)
                else:
                    module = text
                    module_list.append(module)
        if not module_list:
            module_list = ['__builtin__']
        return module_list
