from lexed.editor.meta import EditorMeta, BareException


class EditorSelect(EditorMeta):
    def __init__(self):
        super().__init__()

    def deselect(self, text):
        """Function that flags lines as 'deselected'."""
        # global program_message
        is_number = False
        select_total = 0
        line_total = 0

        self.reset_line()

        if len(text) <= 9:  # if no arguments, deselect all
            self.program_message = ' All lines deselected '
            self.deselect_all()
            return

        temp_text = text[9:]

        try:
            if temp_text.replace(' ', '').replace('-', '').replace(',', '').isdigit():
                is_number = True
        except BareException:
            is_number = False

        try:
            if is_number:
                if "," in text:
                    arg_list = self.get_args(text, ' ', ',')
                    for i in range(len(arg_list) - 1, -1, -1):
                        num = int(arg_list[i])
                        self.lines.db[num].selected = False
                        select_total += 1
                elif "-" in text:
                    arg_list = self.get_args(text, ' ', '-')
                    start = max(1, int(arg_list[0]))
                    end = min(len(self.lines.db), int(arg_list[1]))
                    for i in range(end, start - 1, - 1):
                        self.lines.db[i].selected = False
                        select_total += 1
                else:
                    arg_list = self.get_args(text)
                    if 'str' in str(type(arg_list)):
                        num = int(arg_list)
                    else:
                        num = int(arg_list[0])
                    self.lines.db[num].selected = False
                    self.program_message = f' Deselected line number {num} '
                    select_total += 1

            else:
                start_num = 0
                indent_needed = 0
                if text in ('deselect marked', 'unselect marked'):
                    for i in range(1, len(self.lines.db) + 1):
                        if self.lines.db[i].marked:
                            self.lines.db[i].selected = False
                            line_total += 1
                    if line_total < 1:
                        self.program_message = ' Nothing selected, no lines marked! '
                    else:
                        self.program_message = f' Deselected {line_total} lines '

                else:  # Search for function or class
                    find_function = 'def ' + temp_text + '('
                    find_class = 'class ' + temp_text + '('
                    for i in range(1, len(self.lines.db) + 1):
                        item = self.lines.db[i]
                        if item.text.strip().startswith(find_function) or item.text.strip().startswith(find_class):
                            if item.text.strip().startswith('def'):
                                item_found = 'function'
                            elif item.text.strip().startswith('class'):
                                item_found = 'class'
                            item.selected = False
                            line_total = 1
                            indent_needed = item.indentation
                            start_num = i + 1
                            break
                    if not line_total:
                        self.program_message = ' Specified function/class not found! '
                        return

                    for i in range(start_num, self.lines.total):
                        if self.lines.db[i].text and self.lines.db[i].indentation <= indent_needed:
                            break
                        self.lines.db[i].selected = False
                        line_total += 1
                    self.program_message = f" Deselected {item_found} '{temp_text}' ({line_total} lines) "

            if self.config['syntax_highlighting']:
                self.syntax_visible()
            if self.config['splitscreen'] and self.config['syntax_highlighting']:
                self.syntax_split_screen()

            if select_total > 1:
                self.program_message = f' Deselected {select_total} lines '
            elif select_total == 1 and not self.program_message:
                self.program_message = ' Deselected 1 line '
            elif not self.program_message:
                self.program_message = ' No items found! '
        except BareException:
            self.program_message = ' Error, select failed! '

    def deselect_all(self):
        """Deselect all lines"""
        # global program_message
        self.program_message = ' All lines deselected '
        for i in range(1, len(self.lines.db) + 1):
            self.lines.db[i].selected = False
            self.syntax_visible()
        if self.config['splitscreen'] and self.config['syntax_highlighting']:
            self.syntax_split_screen()

    def select_up(self, text):
        """Function that selects lines upward till blank line reached"""
        # global program_message
        select_total = 0
        self.reset_line()
        for i in range(1, len(self.lines.db) + 1):  # Deselect all
            self.lines.db[i].selected = False
        if self.current_num == 1:
            self.program_message = ' Error, no lines to select! '
            return
        for i in range(self.current_num - 1, 0, -1):
            if not self.lines.db[i].text.strip():
                break
            select_total += 1
        for i in range(self.current_num - 1, 0, -1):
            if not self.lines.db[i].text.strip():
                break
            self.lines.db[i].selected = True
        self.program_message = f' Selected {select_total} lines '

    def select_down(self, text):
        """Function that selects lines downward till blank line reached"""
        # global program_message
        select_total = 0
        self.reset_line()
        for i in range(1, len(self.lines.db) + 1):  # Deselect all
            self.lines.db[i].selected = False
        if self.current_num == self.lines.total:
            self.program_message = ' Error, no lines to select! '
            return
        for i in range(self.current_num + 1, self.lines.total + 1):
            if not self.lines.db[i].text.strip():
                break
            select_total += 1
        for i in range(self.current_num + 1, self.lines.total + 1):
            if not self.lines.db[i].text.strip():
                break
            self.lines.db[i].selected = True
        self.program_message = f' Selected {select_total} lines '

    def select(self, text):
        """Function that flags lines as 'selected'.

        Can select function name, line numbers, or marked items

            ex: select myFunction()
                select 1-10
                select 16,33"""

        # global program_message, current_num
        is_number = False
        # select_total = 0
        line_total = 0

        self.reset_line()

        for i in range(1, len(self.lines.db) + 1):  # Deselect all
            self.lines.db[i].selected = False

        if len(text) <= 7:  # if no arguments, select current line and return
            self.lines.db[self.current_num].selected = True
            self.program_message = f' Selected line number {self.current_num} '
            return

        if text == 'select all':
            text = f'select 1-{self.lines.total}'  # handle 'select all'
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
                        self.lines.db[num].selected = True
                        line_total += 1
                elif '-' in text:
                    arg_list = self.get_args(text, ' ', '-')
                    start = max(1, int(arg_list[0]))
                    end = min(len(self.lines.db), int(arg_list[1]))
                    for i in range(end, start - 1, - 1):
                        self.lines.db[i].selected = True
                        line_total += 1
                else:
                    arg_list = self.get_args(text)
                    if 'str' in str(type(arg_list)):
                        num = int(arg_list)
                    else:
                        num = int(arg_list[0])
                    self.lines.db[num].selected = True
                    self.program_message = f' Selected line number {num} '
                    line_total += 1

            else:
                if text == 'select marked':
                    for i in range(1, len(self.lines.db) + 1):
                        if self.lines.db[i].marked:
                            self.lines.db[i].selected = True
                            line_total += 1
                    if line_total < 1:
                        self.program_message = ' Nothing selected, no lines marked! '

                else:  # Search for function or class
                    start_num = 0
                    indent_needed = 0
                    find_function = 'def ' + temp_text + '('
                    find_class = 'class ' + temp_text + '('
                    item_found = ''
                    for i in range(1, len(self.lines.db) + 1):
                        item = self.lines.db[i]
                        if item.text.strip().startswith(find_function) or item.text.strip().startswith(find_class):
                            if item.text.strip().startswith('def'):
                                item_found = 'function'
                            elif item.text.strip().startswith('class'):
                                item_found = 'class'
                            item.selected = True
                            line_total = 1
                            indent_needed = item.indentation
                            start_num = i + 1
                            break
                    if not line_total:
                        self.program_message = ' Specified function/class not found! '
                        return

                    for i in range(start_num, self.lines.total):
                        if self.lines.db[i].text and self.lines.db[i].indentation <= indent_needed:
                            break
                        self.lines.db[i].selected = True
                        line_total += 1
                    self.program_message = f" Selected {item_found} '{temp_text}' ({line_total} lines) "

            if self.config['syntax_highlighting']:
                self.syntax_visible()
            if self.config['splitscreen'] and self.config['syntax_highlighting']:
                self.syntax_split_screen()

            if line_total > 1 and not self.program_message:
                self.program_message = f' Selected {line_total} lines '
            elif line_total == 1 and not self.program_message:
                self.program_message = ' Selected 1 line '
            elif not self.program_message:
                self.program_message = ' No items found! '
        except BareException:
            self.program_message = ' Error, select failed! '

    def invert_selection(self):
        """Inverts/reverses current selection"""
        self.reset_line()
        count = 0
        selected_lines = ''
        for i in range(1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if item.selected:
                count += 1
            else:
                if selected_lines != '':
                    selected_lines += ', '
                selected_lines += str(i)
        if count == self.lines.total:
            self.deselect_all()
        elif count == 0:
            self.select('select all')
        else:
            self.select(f'select {selected_lines}')

    def select_items(self, _type):
        """Returns string of selected lines.
                Type of command to be executed must be passed

                example: selectItems("copy")
        """
        select_string = ''
        # word1 = _type.capitalize()
        for i in range(1, len(self.lines.db) + 1):
            if self.lines.db[i].selected:
                num = self.lines.db[i].number
                select_string += '%i,' % num
        if select_string.endswith(','):
            select_string = select_string[0:-1]
        return f'{_type} {select_string}'

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
