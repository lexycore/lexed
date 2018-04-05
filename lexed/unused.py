


def tab_key():
    """program specific function that handles 'tab'"""
    char = " "
    global current_line, continue_down, continue_up
    continue_down = 0
    continue_up = 0
    for i in range(0, 4):
        old_number_of_rows = current_line.number_of_rows
        old_x = current_line.x
        templist = current_line.listing
        if current_line.y == 0 and current_line.x == current_line.end_x:
            templist.append(char)
        else:
            position = ROWSIZE * (current_line.number_of_rows - 1 - abs(current_line.y)) + current_line.x - 6
            templist.insert(position, char)
        tempstring = ""
        for item in templist:
            tempstring += item
        current_line.text = tempstring
        current_line.x += 1

        if old_number_of_rows != current_line.number_of_rows:
            if current_line.y != 0: current_line.y -= 1
            if current_line.y == 0:
                current_line.y -= 1
                current_line.x = old_x + 1


def prev():
    """Goto previous line"""
    global program_message, prev_line, current_num
    reset_line()
    try:
        current = current_num
        current_num = prev_line
        prev_line = current
        self.lines.db[current_num].x = self.lines.db[current_num].end_x  # update cursor position
        program_message = " Moved from line %i to %i " % (prev_line, current_num)
        if self.config["syntax_highlighting"]:
            syntax_visible()
    except:
        program_message = " Prev failed! "


def replace_marked(mytext):
    """Replace items in marked lines only"""
    global program_message, saved_since_edit
    count = 0
    mark_total = 0
    reset_line()
    for i in range(1, len(self.lines.db) + 1):  # count number of marked lines
        if self.lines.db[i].marked: mark_total += 1
    if mark_total == 0:
        get_confirmation("No lines are marked!", True)
        program_message = " Replace operation failed! "
        return
    if not get_confirmation("Do replace operation on %i marked lines? (y/n)" % mark_total):
        program_message = " Replace operation aborted! "
        return
    try:
        if "replace marked" in mytext: mytext = mytext.replace("replace marked", "replacemarked")
        if "|" in mytext:
            (oldtext, newtext) = get_args(mytext, " ", "|", False)
        else:
            (oldtext, newtext) = get_args(mytext, " ", " with ", False)
    except:
        get_confirmation("Error occurred, replace operation failed!", True)
        return

    update_que("REPLACE operation")
    update_undo()

    for i in range(1, len(self.lines.db) + 1):
        item = self.lines.db[i]
        if item.marked and oldtext in item.text:
            item.text = item.text.replace(oldtext, newtext)
            count += 1
            if self.config["syntax_highlighting"]: item.add_syntax()  # adjust syntax
            if self.config["debug"] and i > 1:
                item.error = False
                error_test(item.number)  # test for code errors

    program_message = " Replaced %i items " % count
    if count == 0:
        get_confirmation("   Item not found.    ", True)
    else:
        saved_since_edit = False


def replace_selected(mytext, message=True):
    """Replace items in selected lines only"""
    global program_message, saved_since_edit
    count = 0
    select_total = 0
    reset_line()
    for i in range(1, len(self.lines.db) + 1):  # count number of selected lines
        if self.lines.db[i].selected: select_total += 1
    if select_total == 0:
        get_confirmation("No lines are selected!", True)
        program_message = " Replace operation failed! "
        return
    if message and not get_confirmation("Do replace on %i selected lines? (y/n)" % select_total):
        program_message = " Replace operation aborted! "
        return
    try:
        if "replace selected" in mytext: mytext = mytext.replace("replace selected", "replaceselected")
        if "|" in mytext:
            (oldtext, newtext) = get_args(mytext, " ", "|", False)
        else:
            (oldtext, newtext) = get_args(mytext, " ", " with ", False)
    except:
        get_confirmation("Error occurred, replace operation failed!", True)
        return

    update_que("REPLACE operation")
    update_undo()

    for i in range(1, len(self.lines.db) + 1):
        item = self.lines.db[i]
        if item.selected and oldtext in item.text:
            item.text = item.text.replace(oldtext, newtext)
            count += 1
            if self.config["syntax_highlighting"]: item.add_syntax()  # adjust syntax
            if self.config["debug"] and i > 1:
                item.error = False
                error_test(item.number)  # test for code errors

    program_message = " Replaced %i items " % count
    if count == 0:
        get_confirmation("   Item not found.    ", True)
    else:
        saved_since_edit = False


def enter_commands():
    """Enter commands in 'Entry Window'"""
    global reset_needed, program_message

    program_message = ""
    if self.lines.db[current_num].text and current_num == self.lines.total:  # create empty line if position is last line
        l = Line()  # create emtpy line

    reset_needed = False
    mytext = prompt_user()
    if command_match(mytext, "load", "read", False):
        load_command(mytext)
    elif command_match(mytext, "find", "<@>_foobar_", False):
        find(mytext)
    elif command_match(mytext, "save", "<@>_foobar_", False):
        save(savepath)
    elif command_match(mytext, "new", "<@>_foobar_", False):
        new_doc()

    # Action on marked lines
    elif command_match(mytext, "expand marked", "expandmarked", False):
        expand(mark_items("expand"))
    elif command_match(mytext, "collapse marked", "collapsemarked", False):
        collapse(mark_items("collapse"))
    elif command_match(mytext, "comment marked", "commentmarked", False):
        comment(mark_items("comment"))
    elif command_match(mytext, "uncomment marked", "uncommentmarked", False):
        uncomment(mark_items("uncomment"))
    elif command_match(mytext, "indent marked", "indentmarked", False):
        indent(mark_items("indent"))
    elif command_match(mytext, "unindent marked", "unindentmarked", False):
        unindent(mark_items("unindent"))
    elif command_match(mytext, "replacemarked", "<@>_foobar_", False):
        replace_marked(current_line.text)
    elif command_match(mytext, "copy marked", "copymarked", False):
        copy(mark_items("copy"))
    elif command_match(mytext, "delete marked", "deletemarked", False):
        delete_lines(mark_items("delete"))
    elif command_match(mytext, "cut marked", "cutmarked", False):
        cut(mark_items("cut"))

    # Action on selected lines
    elif command_match(mytext, "expand selected", "expand selection", False):
        expand(select_items("expand"))
    elif command_match(mytext, "collapse selected", "collapse selection", False):
        collapse(select_items("collapse"))
    elif command_match(mytext, "comment selected", "comment selection", False):
        comment(select_items("comment"))
    elif command_match(mytext, "uncomment selected", "uncomment selection", False):
        uncomment(select_items("uncomment"))
    elif command_match(mytext, "indent selected", "indent selection", False):
        indent(select_items("indent"))
    elif command_match(mytext, "unindent selected", "unindent selection", False):
        unindent(select_items("unindent"))
    elif command_match(mytext, "copy selected", "copy selection", False):
        copy(select_items("copy"), True)
    elif command_match(mytext, "delete selected", "delete selection", False):
        delete_lines(select_items("delete"))
    elif command_match(mytext, "cut selected", "cut selection", False):
        cut(select_items("cut"))
    elif command_match(mytext, "select reverse", "select invert", False):
        invert_selection()
    elif command_match(mytext, "invert", "invert selection", False):
        invert_selection()

    elif mytext == "indent":
        indent("indent %s" % str(current_line.number))
    elif command_match(mytext, "indent", "<@>_foobar_", False):
        indent(mytext)
    elif mytext == "unindent":
        unindent("unindent %s" % str(current_line.number))
    elif command_match(mytext, "unindent", "<@>_foobar_", False):
        unindent(mytext)
    elif command_match(mytext, "replace", "<@>_foobar_", False):
        replace_text(mytext)
    elif mytext == "copy":
        copy("copy %s" % str(current_line.number))
    elif command_match(mytext, "copy", "<@>_foobar_", False):
        copy(mytext)
    elif mytext == "paste" and len(clipboard) > 1:
        get_confirmation("Error, multiple lines in memory. Specify line number.", True)
    elif command_match(mytext, "paste", "<@>_foobar_", False):
        paste(mytext)
    elif mytext == "cut":
        cut("cut %i" % current_line.number)  # if no args, cut current line
    elif command_match(mytext, "cut", "<@>_foobar_", False):
        cut(mytext)
    elif command_match(mytext, "mark", "<@>_foobar_", False):
        mark(mytext)
    elif mytext in ("unmark all", "unmark off"):
        unmark_all()
    elif command_match(mytext, "unmark", "<@>_foobar_", False):
        unmark(mytext)

    # Selecting/deselecting
    elif mytext in ("deselect", "unselect"):
        deselect("deselect %s" % str(current_line.number))
    elif command_match(mytext, "deselect all", "unselect all", False):
        deselect_all()  # deselects all lines
    elif command_match(mytext, "select off", "select none", False):
        deselect_all()  # deselects all lines
    elif command_match(mytext, "deselect", "unselect", False):
        deselect(mytext)
    elif command_match(mytext, "select up", False):
        select_up(mytext)
    elif command_match(mytext, "select down", False):
        select_down(mytext)
    elif command_match(mytext, "select", False):
        select(mytext)

    elif command_match(mytext, "goto", "<@>_foobar_", False):
        goto(mytext)
    elif mytext == "delete":
        delete_lines("delete %i" % current_num)  # delete current line if no argument
    elif command_match(mytext, "delete", "<@>_foobar_", False):
        delete_lines(mytext)
    elif command_match(mytext, "quit", "<@>_foobar_", False):
        quit()
    elif command_match(mytext, "show", "hide", False):
        show_hide(mytext)
    elif mytext == "collapse":
        collapse("collapse %s" % str(current_line.number))
    elif mytext == "collapse":
        collapse("collapse %s" % str(current_line.number))
    elif mytext == "collapse all":
        collapse("collapse 1 - %s" % str(len(self.lines.db)))
    elif command_match(mytext, "collapse", "<@>_foobar_", False):
        collapse(mytext)
    elif mytext == "expand":
        expand("expand %s" % str(current_line.number))
    elif mytext == "expand":
        expand("expand %s" % str(current_line.number))
    elif mytext == "expand all":
        expand_all()
    elif command_match(mytext, "expand", "<@>_foobar_", False):
        expand(mytext)
    elif command_match(mytext, "undo", "<@>_foobar_", False):
        undo()
    elif mytext == "comment":
        comment("comment %s" % str(current_line.number))
    elif command_match(mytext, "comment", "<@>_foobar_", False):
        comment(mytext)
    elif mytext == "uncomment":
        uncomment("uncomment %s" % str(current_line.number))
    elif command_match(mytext, "uncomment", "<@>_foobar_", False):
        uncomment(mytext)
    elif command_match(mytext, "run", "<@>_foobar_", False):
        run()
    elif command_match(mytext, "debug", "<@>_foobar_", False):
        toggle_debug(mytext)
    elif command_match(mytext, "syntax", "<@>_foobar_", False):
        toggle_syntax(mytext)

    elif command_match(mytext, "whitespace", "<@>_foobar_", False):
        toggle_whitespace(mytext)
    elif command_match(mytext, "show whitespace", "hide whitespace", False):
        toggle_whitespace(mytext)
    elif command_match(mytext, "guide", "pageguide", False):
        toggle_page_guide(mytext)
    elif mytext == "color on":
        color_on()

    elif command_match(mytext, "split", "splitscreen"):
        toggle_split_screen(mytext)  # toggle splitscreen
    elif command_match(mytext, "commands off", "<@>_foobar_", False):
        self.config["inline_commands"] = False
        program_message = " Inline commands turned off! "
    elif command_match(mytext, "commands on", "<@>_foobar_", False):
        self.config["inline_commands"] = True
        program_message = " Inline commands turned on! "
    elif command_match(mytext, "commands protected", "<@>_foobar_", False):
        self.config["inline_commands"] = "protected"
        program_message = " Inline commands protected with '%s' " % self.config["protect_string"]
    elif command_match(mytext, "protect", "<@>_foobar_", False):
        toggle_protection(mytext)
    elif command_match(mytext, "timestamp", "<@>_foobar_", False):
        time_stamp()
    elif mytext == "help":
        if get_confirmation("Load HELP GUIDE? Current doc will be purged! (y/n)"):
            show_help()
    elif command_match(mytext, "help", "<@>_foobar_", False):
        function_help(mytext)

    # New commands (should be last round)
    elif command_match(mytext, "entry", "<@>_foobar_", False):
        toggle_entry(mytext)
    elif command_match(mytext, "live", "<@>_foobar_", False):
        toggle_live(mytext)
    elif command_match(mytext, "strip", "<@>_foobar_", False):
        if get_confirmation("Strip extra spaces from lines? (y/n)"): strip_spaces(mytext)
    elif command_match(mytext, "savesettings", "saveprefs", False):
        if get_confirmation("Save current settings? (y/n)"): save_settings()
    elif command_match(mytext, "setcolors", "setcolor", False):
        set_colors()
    elif command_match(mytext, "isave", "<@>_foobar_", False):
        isave()
    elif command_match(mytext, "auto", "<@>_foobar_", False):
        toggle_auto(mytext)
    elif command_match(mytext, "formatting", "<@>_foobar_", False):
        toggle_comment_formatting(mytext)
    elif command_match(mytext, "tabs", "tab", False):
        toggle_tabs(mytext)
    elif command_match(mytext, "prev", "previous", False):
        prev()
    elif command_match(mytext, "acceleration", "accelerate", False):
        toggle_acceleration(mytext)
    elif command_match(mytext, "revert", "<@>_foobar_", False):
        revert()
    elif command_match(mytext, "saveas", "<@>_foobar_", False):
        if len(mytext) > 7:
            temp_path = mytext[7:]
        elif not savepath:
            temp_path = False
        else:
            (fullpath, filename) = os.path.split(savepath)
            temp_path = filename
        if not temp_path: temp_path = ""
        if savepath:
            part1 = os.path.split(savepath)[0]
            part2 = temp_path
            temp_path = part1 + "/" + part2
        if "/" not in temp_path: temp_path = (os.getcwd() + "/" + temp_path)
        saveas_path = prompt_user("SAVE FILE AS:", temp_path, "(press 'enter' to proceed, UP arrow to cancel)", True)
        if saveas_path:
            save(saveas_path)
        else:
            program_message = " Save aborted! "

    else:
        if mytext:
            program_message = " Command not found! "
        else:
            program_message = " Aborted entry "


def bug_hunt():
    """If bugs found, moves you to that part of the program"""
    global program_message, current_num
    program_message = ""
    collapsed_bugs = False
    # Debug current line before moving to next
    self.lines.db[current_num].error = False
    error_test(current_num)

    if current_num != len(self.lines.db):
        for i in range(current_num + 1, len(self.lines.db) + 1):
            item = self.lines.db[i]
            if item.error and item.collapsed:
                collapsed_bugs = True
            elif item.error:
                current_num = item.number
                return

    for i in range(1, len(self.lines.db) + 1):
        item = self.lines.db[i]
        if item.error and item.collapsed:
            collapsed_bugs = True
        elif item.error:
            current_num = item.number
            return

    if collapsed_bugs:
        program_message = " Bugs found in collapsed sections "
    else:
        program_message = " No bugs found! "


def status_message(mytext, number, update_lines=False):
    """Displays status message"""
    if update_lines:  # clears entire header and updates number of lines
        stdscr.addstr(0, 0, " " * (WIDTH), self.config["color_header"])
        temp_text = "%i" % self.lines.total
        lines_text = temp_text.rjust(11)
        if self.config["inline_commands"] == "protected":
            protect_string = str(self.config["protect_string"])
            stdscr.addstr(0, WIDTH - 12 - len(protect_string) - 1, lines_text, self.config["color_header"])
            stdscr.addstr(0, WIDTH - len(protect_string) - 1, protect_string, self.config["color_message"])
        else:
            stdscr.addstr(0, WIDTH - 12, lines_text, self.config["color_header"])
    else:  # clears space for statusMessage only
        stdscr.addstr(0, 0, " " * (WIDTH - 13), self.config["color_header"])
    number = int(number)  # Convert to integer
    message = " %s%i" % (mytext, number) + "% "
    stdscr.addstr(0, 0, message, self.config["color_warning"])
    stdscr.refresh()


def directory_attributes(file_list, directory, sort_by=self.config["default_load_sort"],
                         reverse=self.config["default_load_reverse"], show_hidden=self.config["default_load_invisibles"]):
    """Takes list of filenames and the parent directory, and returns a sorted list of files, paths, and attributes"""
    mylist = []
    readable_extensions = (".txt", ".py", ".pwe", ".cpp", ".c", ".sh", ".js")

    for i in range(0, len(file_list)):
        if not show_hidden and not file_list[i].startswith(".") and not file_list[i].endswith(
                "~"):  # doesn't show hidden files or backup files
            if os.path.isdir((directory + file_list[i])):
                mylist.append(file_list[i])
            else:
                for item in readable_extensions:  # trims to list to 'readable' files
                    if file_list[i].endswith(item): mylist.append(file_list[i])

        elif show_hidden:
            if os.path.isdir((directory + file_list[i])):
                mylist.append(file_list[i])
            else:
                mylist.append(file_list[i])

    if directory.endswith("/"):
        temp_dir = directory[0:-1]
    else:
        temp_dir = directory
    if "/" in temp_dir:
        prev_path = temp_dir.rpartition("/")[0]  # assign ParentDir
    else:
        prev_path = "/"

    prev_dir = ("", "../", prev_path, "", "", "parent", "")

    directory_contents = []

    for i in range(0, len(mylist)):  # cycles thru items in trimmed down list and calculates attributes
        file_name = mylist[i]

        if os.path.isdir((directory + file_name)):
            file_type = "DIR"  # determines if item is directory
        elif file_name.endswith(".txt"):
            file_type = "text"  # could replace with loop!?
        elif file_name.endswith(".py"):
            file_type = "python"
        elif file_name.endswith(".pwe"):
            file_type = "encryp"
        elif file_name.endswith(".cpp"):
            file_type = "c++"
        elif file_name.endswith(".c"):
            file_type = "c"
        elif file_name.endswith(".sh"):
            file_type = "shell"
        elif file_name.endswith(".js"):
            file_type = "jscrpt"
        else:
            file_type = "***"
        try:
            rawsize = os.path.getsize((directory + file_name)) / 1024.00  # get size and convert to kilobytes
        except:
            rawsize = 0
        file_size = "%.2f" % rawsize  # limit to two decimal places (f for float)
        file_size = file_size.rjust(8)
        try:
            mod_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime((directory + file_name))))
        except:
            mod_date = "????-??-?? ??:??"
        path_to_file = directory + file_name

        # Determine file access
        if not os.access(path_to_file, os.R_OK):
            file_access = "NO ACCESS!"
        elif os.access(path_to_file, os.X_OK):
            file_access = "executable"
        elif os.access(path_to_file, os.R_OK) and not os.access(path_to_file, os.W_OK):
            file_access = "READ ONLY "
        elif os.access(path_to_file, os.R_OK) and os.access(path_to_file, os.W_OK):
            file_access = "read/write"
        else:
            file_access = "UNKNOWN!!!"

        if sort_by == "type":
            sort_me = file_type + file_name.lower()  # sort by file_type, then file_name (case insensitive)
        elif sort_by == "date":
            sort_me = mod_date + file_name.lower()
        elif sort_by == "size":
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


def display_list(directory, page=1, position=0):
    """Displays scrolling list of files for user to choose from"""
    c = 0
    num = 0
    view = 5
    if os.path.isdir(directory) == False and "/" in directory:
        directory = directory.rpartition("/")[0] + "/"  # removes filename (this bit edited)

    templist = os.listdir(directory)
    mylist = []
    sort_type = self.config["default_load_sort"]
    reverse_sort = self.config["default_load_reverse"]
    show_hidden = self.config["default_load_invisibles"]

    directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort,
                                              show_hidden)  # get file attributes from function

    while True:  # User can explore menus until they make a selection or cancel out
        total_pages = int(len(directory_contents) / (HEIGHT - 3))
        if len(directory_contents) % (HEIGHT - 3) != 0: total_pages += 1

        stdscr.clear()
        # print empty lines
        if self.config["color_background"]: print_background()
        stdscr.addstr(0, 0, (" " * WIDTH), self.config["color_header"])  # Print header
        stdscr.addstr(HEIGHT, 0, (" " * WIDTH), self.config["color_header"])  # Print header

        if len(directory) > WIDTH - 14:
            tempstring = "... %s" % directory[(len(directory) - WIDTH) + 14:]  # s[len(s)-WIDTH:]
            stdscr.addstr(0, 0, tempstring, self.config["color_header"])  # Print header
        else:
            stdscr.addstr(0, 0, directory, self.config["color_header"])  # Print header
        stdscr.addstr(0, (WIDTH - 10), ("page " + str(page) + "/" + str(total_pages)).rjust(10),
                      self.config["color_header"])
        stdscr.hline(1, 0, curses.ACS_HLINE, WIDTH, self.config["color_bar"])  # print solid line

        stdscr.hline(HEIGHT - 1, 0, curses.ACS_HLINE, WIDTH, self.config["color_bar"])  # print solid line

        if sort_type == "size":  # change footer based on SortType
            footer_string = "_Home | sort by _Name / *S*i*z*e / _Date / _Type"
        elif sort_type == "date":
            footer_string = "_Home | sort by _Name / _Size / *D*a*t*e / _Type"
        elif sort_type == "type":
            footer_string = "_Home | sort by _Name / _Size / _Date / *T*y*p*e"
        else:
            footer_string = "_Home | sort by *N*a*m*e / _Size / _Date / _Type"

        print_formatted_text(HEIGHT, footer_string)
        if not show_hidden:
            print_formatted_text(HEIGHT, "| show _. | _-/_+ info | _Quit", "rjust", WIDTH)
        else:
            print_formatted_text(HEIGHT, "| hide _. | _-/_+ info | _Quit", "rjust", WIDTH)

        adjust = (page - 1) * (HEIGHT - 3)
        for i in range(0, HEIGHT - 3):
            num = (page - 1) * (HEIGHT - 3) + i
            try:
                name = directory_contents[num][1]
                fullpath = directory_contents[num][2]
                filesize = directory_contents[num][3]
                filemodDate = directory_contents[num][4]
                filetype = directory_contents[num][5]
                if len(directory_contents[num]) > 6:
                    access = directory_contents[num][6]
                else:
                    access = ""

            except:
                break
            # try:
            if position == num:
                # print empty line
                stdscr.addstr(i + 2, 0, (" " * WIDTH), self.config["color_entry"])
                # print name
                if name == "../" or name == os.path.expanduser("~"):
                    stdscr.addstr(i + 2, 0, name, self.config["color_entry_quote"])
                else:
                    stdscr.addstr(i + 2, 0, name, self.config["color_entry"])
                # clear second part of screen
                if view == 6: stdscr.addstr(i + 2, (WIDTH - 54), (" " * (WIDTH - (WIDTH - 54))),
                                            self.config["color_entry"])
                if view == 5: stdscr.addstr(i + 2, (WIDTH - 41), (" " * (WIDTH - (WIDTH - 41))),
                                            self.config["color_entry"])
                if view == 4: stdscr.addstr(i + 2, (WIDTH - 33), (" " * (WIDTH - (WIDTH - 33))),
                                            self.config["color_entry"])
                if view == 3: stdscr.addstr(i + 2, (WIDTH - 21), (" " * (WIDTH - (WIDTH - 21))),
                                            self.config["color_entry"])
                if view == 2: stdscr.addstr(i + 2, (WIDTH - 11), (" " * (WIDTH - (WIDTH - 11))),
                                            self.config["color_entry"])
                # print file_access
                if view == 6 and num != 0:
                    if access == "NO ACCESS!":
                        stdscr.addstr(i + 2, WIDTH - 51, access, self.config["color_warning"])
                    elif access == "READ ONLY ":
                        stdscr.addstr(i + 2, WIDTH - 51, access, self.config["color_entry_quote"])
                    elif access == "read/write":
                        stdscr.addstr(i + 2, WIDTH - 51, access, self.config["color_entry_command"])
                    else:
                        stdscr.addstr(i + 2, WIDTH - 51, access, self.config["color_entry_functions"])

                # print filesize
                if view >= 5 and num != 0: stdscr.addstr(i + 2, WIDTH - 39, (str(filesize) + " KB"),
                                                         self.config["color_entry"])
                if view == 4 and num != 0: stdscr.addstr(i + 2, WIDTH - 31, (str(filesize) + " KB"),
                                                         self.config["color_entry"])
                if view == 3 and num != 0: stdscr.addstr(i + 2, WIDTH - 19, (str(filesize) + " KB"),
                                                         self.config["color_entry"])
                # print mod date
                if view >= 5: stdscr.addstr(i + 2, WIDTH - 25, filemodDate, self.config["color_entry"])
                if view == 4: stdscr.addstr(i + 2, WIDTH - 18, (filemodDate.split(" ")[0]), self.config["color_entry"])
                # print type
                if view > 1:
                    if filetype == "parent":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_entry_quote"])
                    elif filetype == "DIR":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_entry_number"])
                    elif filetype == "text":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_entry_functions"])
                    elif filetype == "python":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_entry_command"])
                    elif filetype == "encryp":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_entry_comment"])
                    else:
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_entry"])
            else:
                stdscr.addstr(i + 2, 0, (" " * WIDTH), self.config["color_background"])
                # print name
                if name == "../" or name == os.path.expanduser("~"):
                    stdscr.addstr(i + 2, 0, name, self.config["color_quote_double"])
                else:
                    stdscr.addstr(i + 2, 0, name, self.config["color_normal"])
                # clear second part of screen
                if view == 6: stdscr.addstr(i + 2, (WIDTH - 54), (" " * (WIDTH - (WIDTH - 54))),
                                            self.config["color_normal"])
                if view == 5: stdscr.addstr(i + 2, (WIDTH - 41), (" " * (WIDTH - (WIDTH - 41))),
                                            self.config["color_normal"])
                if view == 4: stdscr.addstr(i + 2, (WIDTH - 33), (" " * (WIDTH - (WIDTH - 33))),
                                            self.config["color_normal"])
                if view == 3: stdscr.addstr(i + 2, (WIDTH - 21), (" " * (WIDTH - (WIDTH - 21))),
                                            self.config["color_normal"])
                if view == 2: stdscr.addstr(i + 2, (WIDTH - 11), (" " * (WIDTH - (WIDTH - 11))),
                                            self.config["color_normal"])

                # print file_access
                if view == 6 and num != 0: stdscr.addstr(i + 2, WIDTH - 51, access, self.config["color_dim"])
                # print filesize
                if view >= 5 and num != 0: stdscr.addstr(i + 2, WIDTH - 39, (str(filesize) + " KB"),
                                                         self.config["color_dim"])
                if view == 4 and num != 0: stdscr.addstr(i + 2, WIDTH - 31, (str(filesize) + " KB"),
                                                         self.config["color_dim"])
                if view == 3 and num != 0: stdscr.addstr(i + 2, WIDTH - 19, (str(filesize) + " KB"),
                                                         self.config["color_dim"])
                # print mod date
                if view >= 5: stdscr.addstr(i + 2, WIDTH - 25, filemodDate, self.config["color_dim"])
                if view == 4: stdscr.addstr(i + 2, WIDTH - 18, (filemodDate.split(" ")[0]), self.config["color_dim"])
                # print type
                if view > 1:
                    if filetype == "parent":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_quote_double"])
                    elif filetype == "DIR":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_number"])
                    elif filetype == "text":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_functions"])
                    elif filetype == "python":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_commands"])
                    elif filetype == "encryp":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_warning"])
                    else:
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, self.config["color_normal"])

            if len(directory) < WIDTH: stdscr.addstr(0, len(directory), "")  # Move cursor
            # except:
            # pass
        stdscr.refresh()

        c = stdscr.getch()

        if c == curses.KEY_UP:
            position -= 1
        elif c == curses.KEY_DOWN:
            position += 1
        elif c == curses.KEY_RIGHT and page < total_pages:
            page += 1
            position += HEIGHT - 3
        elif c == curses.KEY_RIGHT:
            position += HEIGHT - 3
        elif c == curses.KEY_LEFT:
            page -= 1
            position -= HEIGHT - 3

        elif c == ord('r') and not reverse_sort:  # reverse
            reverse_sort = True
        elif c == ord('r'):
            reverse_sort = False
        elif c == ord('t') and sort_type == "type" and not reverse_sort:
            reverse_sort = True
        elif c == ord('k') and sort_type == "type" and not reverse_sort:
            reverse_sort = True
        elif c == ord('t') or c == ord('k'):
            sort_type = "type"
            reverse_sort = False
        elif c == ord('d') and sort_type == "date" and reverse_sort:
            reverse_sort = False
        elif c == ord('d'):
            sort_type = "date"
            reverse_sort = True
        elif c == ord('s') and sort_type == "size" and reverse_sort:
            reverse_sort = False
        elif c == ord('s'):
            sort_type = 'size'
            reverse_sort = True
        elif c == ord('n') and sort_type == "name" and not reverse_sort:
            reverse_sort = True
        elif c == ord('n'):
            sort_type = "name"
            reverse_sort = False
        elif c in (ord('-'), ord("_")):
            view = max(1, view - 1)
        elif c in (ord('='), ord("+")):
            view = min(6, view + 1)

        if WIDTH < 60 and view > 5:
            view = 5

        elif c == ord('.'):
            if show_hidden:
                show_hidden = False
            else:
                show_hidden = True

            templist = os.listdir(directory)
            directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort, show_hidden)
            position = 0
            page = 1

        elif c in (ord('q'), ord('Q'), ord('c'), ord('C')):  # c for cancel
            reset_line()
            return False

        elif c in (ord('h'), ord('H')):
            directory = (os.path.expanduser("~") + "/")
            templist = os.listdir(directory)
            directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort, show_hidden)
            position = 0
            page = 1

        elif c == 10 and directory_contents[position][1] == "../" and directory_contents[position][3] == "":
            directory = (directory_contents[position][2] + "/")
            if directory == "//": directory = "/"
            templist = os.listdir(directory)
            directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort, show_hidden)
            position = 0
            page = 1

        elif c == 10 and directory_contents[position][1] == os.path.expanduser("~") and directory_contents[position][
            3] == "":
            directory = (directory_contents[position][2] + "/")
            templist = os.listdir(directory)
            directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort, show_hidden)
            position = 0
            page = 1

        elif c == 10 and directory_contents[position][5] == "DIR" and os.access(directory_contents[position][2],
                                                                                os.R_OK):
            directory = (directory_contents[position][2] + "/")
            templist = os.listdir(directory)
            directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort, show_hidden)
            position = 0
            page = 1

        elif c == 10 and encoding_readable(directory_contents[position][2]):
            return (directory_contents[position][2])

        if c in (ord('r'), ord('t'), ord('d'), ord('s'), ord('n'), ord('k')):  # update directoryContents
            directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort, show_hidden)
            position = 0
            page = 1

        if position + 1 > (HEIGHT - 3) * page and page < total_pages:
            page += 1
        elif position < (HEIGHT - 3) * (page - 1):
            page -= 1
        page = max(1, page)
        page = min(page, int(len(directory_contents) / (HEIGHT - 3)) + 1)
        position = max(0, position)
        position = min(position, len(directory_contents) - 1)


def print_formatted_text(y, string, type=False, width=79):
    """Formats curses text by looking for 'special' characters.

        Type can be "rjust" for right justification, "center" for centered.
        Width should be passed when using Type.

        Text formatting
        ---------------
        '_' = UNDERLINE
        '^' = BOLD
        '*' = REVERSE

        String Replacement
        ------------------
        '$' = DIAMOND
        '|" = Vertical Line"""

    underline = False
    bold = False
    reverse = False
    tempstring = string.replace("*", "")  # REVERSE
    tempstring = tempstring.replace("_", "")  # UNDERLINE
    tempstring = tempstring.replace("^", "")  # BOLD

    if type == "rjust":
        x = width - len(tempstring)
    elif type == "center":
        x = int((width - len(tempstring)) / 2)
    else:
        x = 0

    for z in range(0, len(string)):  # easy way to make first letter of each word standout
        item = string[z]
        if item == "_":
            underline = True
        elif item == "^":
            bold = True
        elif item == "*":
            reverse = True
        elif item == "$":
            stdscr.hline(y, x, curses.ACS_DIAMOND, (1), self.config["color_normal"])  # print diamond
            x += 1
        elif item == "|" and reverse == True:
            stdscr.vline(y, x, curses.ACS_VLINE, (1), self.config["color_reversed"])  # prints vertical line
            reverse = False
            x += 1
        elif item == "|" and bold == True:
            stdscr.vline(y, x, curses.ACS_VLINE, (1), bold_TEXT)  # prints vertical line
            reverse = False
            x += 1
        elif item == "|":
            stdscr.vline(y, x, curses.ACS_VLINE, (1), self.config["color_bar"])  # prints vertical line
            stdscr.hline(y - 1, x, curses.ACS_TTEE, (1), self.config["color_bar"])  # Format previous line

            underline = False
            x += 1
        elif underline:
            underline = False
            stdscr.addstr(y, x, item, self.config["color_underline"])
            x += 1
        elif bold:
            stdscr.addstr(y, x, item, BOLD_TEXT)
            bold = False
            x += 1
        elif reverse:
            stdscr.addstr(y, x, item, self.config["color_reversed"])
            reverse = False
            x += 1
        else:
            stdscr.addstr(y, x, item, self.config["color_header"])
            x += 1


def goto_marked():
    """Move to next 'marked' line"""
    global current_num, program_message, prev_line
    if current_num < self.lines.total:
        for i in range(current_num + 1, len(self.lines.db) + 1):
            if self.lines.db[i].marked:
                prev_line = current_num
                current_num = self.lines.db[i].number
                if self.config["syntax_highlighting"]: syntax_visible()
                return
    for i in range(1, current_num):
        if self.lines.db[i].marked:
            prev_line = current_num
            current_num = self.lines.db[i].number
            if self.config["syntax_highlighting"]: syntax_visible()
            return
    if self.lines.db[current_num].marked:
        program_message = " No other lines marked! "
    else:
        program_message = " No lines marked! "


def prev_marked():
    """Move to previous 'marked' line"""
    global current_num, program_message, prev_line
    if current_num > 1:
        for i in range(current_num - 1, 0, -1):
            if self.lines.db[i].marked:
                prev_line = current_num
                current_num = self.lines.db[i].number
                if self.config["syntax_highlighting"]: syntax_visible()
                return
    for i in range(self.lines.total, current_num, -1):
        if self.lines.db[i].marked:
            prev_line = current_num
            current_num = self.lines.db[i].number
            if self.config["syntax_highlighting"]: syntax_visible()
            return
    if self.lines.db[current_num].marked:
        program_message = " No other lines marked! "
    else:
        program_message = " No lines marked! "


def revert():
    """Revert file to last saved"""
    reset_line()
    if get_confirmation("Revert to original file? (y/n)"):
        update_que("REVERT operation")
        update_undo()
        load(savepath)


def toggle_debug(mytext):
    """Turn debug mode on or off"""
    global program_message
    arg = get_args(mytext)
    reset_line()
    if arg not in ("on", "off") and self.config["debug"] == True:
        arg = "off"
    elif arg not in ("on", "off") and self.config["debug"] == False:
        arg = "on"
    if arg == "on":
        self.config["debug"] = True
        program_message = " Debug on "
    elif arg == "off":
        self.config["debug"] = False
        program_message = " Debug off "


def toggle_acceleration(mytext):
    """Turn acceleration on or off"""
    global program_message
    arg = get_args(mytext)
    reset_line()
    if arg not in ("on", "off") and self.config["cursor_acceleration"] == True:
        arg = "off"
    elif arg not in ("on", "off") and self.config["cursor_acceleration"] == False:
        arg = "on"
    if arg == "on":
        self.config["cursor_acceleration"] = True
        program_message = " Cursor acceleration on "
    elif arg == "off":
        self.config["cursor_acceleration"] = False
        program_message = " Cursor acceleration off "


def strip_spaces(mytext):
    """Strips extra/trailing spaces from line"""
    global program_message, saved_since_edit
    reset_line()
    update_que("STRIP WHITESPACE operation")
    update_undo()
    count = 0
    for num in range(1, self.lines.total + 1):
        item = self.lines.db[num]
        if item.text and item.text.count(" ") == len(item.text):
            item.text = ""
            if self.config["syntax_highlighting"]: item.add_syntax()
            if self.config["debug"]: error_test(item.number)
            count += 1
        else:
            for i in range(64, 0, -1):
                search = (i * " ")
                if item.text.endswith(search):
                    item.text = item.text[:-i]
                    if self.config["syntax_highlighting"]: item.add_syntax()
                    if self.config["debug"]: error_test(item.number)
                    count += 1
    if not count:
        program_message = " No extra whitespace found! "
    else:
        program_message = " %i lines stripped " % count
        saved_since_edit = False


def set_colors():
    """Function that allows user to set colors used with syntax highlighting"""
    global program_message
    reset_line()
    if not self.config["display_color"] or not curses.has_colors():
        get_confirmation("You can't set colors in monochrome mode!", True)
        return
    if WIDTH < 79 or HEIGHT < 19:
        get_confirmation("Increase termnal size to set colors!", True)
        return

    self.config["default_colors"] = False
    win = curses.newwin(HEIGHT, WIDTH, 0, 0)  # 0,0 is start position
    x = int((WIDTH - 49) / 2)
    c = 0
    i_num = 0
    item_list = []
    c_num = 0
    color_list = []
    temp_list = []
    empty = ("").center(49)
    seperator = ("").center(49, "@")
    style = 0
    style_change = False

    for key in settings.keys():
        if "color_" in key: item_list.append(key)
    for key in colors.keys():
        (item1, item2) = key.split("_on_")
        temp_list.append((item2 + item1, key))  # change "white_on_blue" to ("bluewhite", "white_on_blue")
    temp_list.sort()

    for value in temp_list:
        color_list.append(value[1])

    item_list.sort()
    color_list.insert(0, "[CURRENT]")

    for i in range(0, HEIGHT + 1):
        stdscr.addstr(i, 0, (" " * WIDTH), self.config["color_normal"])
        if i <= 8: stdscr.addstr(i, x, empty, curses.A_NORMAL)  # redundant?
    title = ("SETCOLORS").center(49)
    header = " ITEM (up/down)               COLOR (left/right)"
    divider = ("").center(49, "-")
    footer = ("*N*o*r*m*a*l $ _Bold $ _Underline $ b_Oth")

    sample_header = ("SAMPLE LAYOUT").center(49)
    sample_left = ("Left justified").ljust(49)
    sample_right = ("Right justified").rjust(49)

    while c != 10:  # continue until 'enter' is pressed
        item = item_list[i_num]
        color = color_list[c_num]
        stdscr.addstr(1, x, title, curses.A_REVERSE)
        stdscr.addstr(2, x, header, curses.A_BOLD)
        stdscr.hline(3, x, curses.ACS_HLINE, 49, self.config["color_bar"])
        if color == "[CURRENT]":
            for key, value in colors.items():
                if self.config[item] == value:
                    search = key
                    style = 0
                elif self.config[item] == value + curses.A_BOLD:
                    search = key
                    style = curses.A_BOLD
                elif self.config[item] == value + curses.A_UNDERLINE:
                    search = key
                    style = curses.A_UNDERLINE
                elif self.config[item] == value + curses.A_BOLD + curses.A_UNDERLINE:
                    search = key
                    style = curses.A_BOLD + curses.A_UNDERLINE
            index = color_list.index(search, 1)
            c_num = index
            color = color_list[c_num]

        stdscr.addstr(4, x + 23, (color.replace("_", " ").rjust(25)), colors[color] + style)  # testing
        stdscr.addstr(4, x + 1, ((item.replace("color", "").replace("_", " "))).ljust(23),
                      colors["white_on_blue"] + curses.A_BOLD)  # testing
        stdscr.hline(5, x, curses.ACS_HLINE, 49, self.config["color_bar"])
        # print vertical lines
        stdscr.hline(4, x, curses.ACS_VLINE, 1, self.config["color_bar"])
        stdscr.hline(4, x + 48, curses.ACS_VLINE, 1, self.config["color_bar"])
        # print corners
        stdscr.hline(3, x, curses.ACS_ULCORNER, 1, self.config["color_bar"])
        stdscr.hline(3, x + 48, curses.ACS_URCORNER, 1, self.config["color_bar"])
        stdscr.hline(5, x, curses.ACS_LLCORNER, 1, self.config["color_bar"])
        stdscr.hline(5, x + 48, curses.ACS_LRCORNER, 1, self.config["color_bar"])

        if style == curses.A_BOLD + curses.A_UNDERLINE:
            footer = ("_Normal $ _Bold $ _Underline $ *b*O*t*h")
        elif style == curses.A_BOLD:
            footer = ("_Normal $ *B*o*l*d $ _Underline $ b_Oth")
        elif style == curses.A_UNDERLINE:
            footer = ("_Normal $ _Bold $ *U*n*d*e*r*l*i*n*e $ b_Oth")
        else:
            footer = ("*N*o*r*m*a*l $ _Bold $ _Underline $ b_Oth")
        print_formatted_text(6, footer, "center", WIDTH)
        stdscr.addstr(8, x, sample_header, self.config["color_comment_centered"])  # Text types need to be changed?
        stdscr.addstr(9, x, seperator, self.config["color_comment_separator"])
        stdscr.addstr(10, x, sample_left, self.config["color_comment_leftjust"])
        stdscr.addstr(11, x, sample_right, self.config["color_comment_rightjust"])

        stdscr.addstr(12, x, "class", self.config["color_class"])
        stdscr.addstr(12, x + 12, "collapsed", self.config["color_class_reversed"])
        stdscr.addstr(12, x + 28, "print", self.config["color_commands"])
        stdscr.addstr(12, x + 40, "#comment", self.config["color_comment"])

        stdscr.addstr(13, x, "def", self.config["color_functions"])
        stdscr.addstr(13, x + 12, "collapsed", self.config["color_functions_reversed"])
        stdscr.addstr(13, x + 28, "True", self.config["color_positive"])
        stdscr.addstr(13, x + 40, "False", self.config["color_negative"])

        stdscr.addstr(14, x, "'quote'", self.config["color_quote_single"])
        stdscr.addstr(14, x + 12, '"double"', self.config["color_quote_double"])
        stdscr.addstr(14, x + 28, '"""doc"""', self.config["color_quote_triple"])

        stdscr.addstr(14, x + 40, 'CONSTANT', self.config["color_constant"])

        stdscr.addstr(15, x, "()!=[]+-", self.config["color_operator"])
        stdscr.addstr(15, x + 12, "normal text", self.config["color_normal"])
        stdscr.addstr(15, x + 28, '0123456789', self.config["color_number"])
        stdscr.addstr(15, x + 40, " C.BLOCK", self.config["color_comment_block"])

        stdscr.addstr(16, x, "print ", self.config["color_entry_command"])
        stdscr.addstr(16, x + 6, '"Entry line"', self.config["color_entry_quote"])
        stdscr.addstr(16, x + 18, "; ", self.config["color_entry_dim"])
        stdscr.addstr(16, x + 20, "number ", self.config["color_entry"])
        stdscr.addstr(16, x + 27, "= ", self.config["color_entry_dim"])
        stdscr.addstr(16, x + 29, "100", self.config["color_entry_number"])
        stdscr.addstr(16, x + 32, "; ", self.config["color_entry_dim"])
        stdscr.addstr(16, x + 34, "def ", self.config["color_entry_functions"])
        stdscr.addstr(16, x + 38, "#comment  ", self.config["color_entry_comment"])

        stdscr.addstr(17, x, "class", self.config["color_entry_class"])
        stdscr.addstr(17, x + 5, ": ", self.config["color_entry_dim"])
        stdscr.addstr(17, x + 7, "False", self.config["color_entry_negative"])
        stdscr.addstr(17, x + 12, ", ", self.config["color_entry_dim"])
        stdscr.addstr(17, x + 14, "True", self.config["color_entry_positive"])
        stdscr.addstr(17, x + 18, "; ", self.config["color_entry_dim"])
        stdscr.addstr(17, x + 20, "CONSTANT", self.config["color_entry_constant"])
        stdscr.addstr(17, x + 28, "; ", self.config["color_entry_dim"])
        stdscr.addstr(17, x + 30, '"""Triple Quote"""', self.config["color_entry_quote_triple"])

        stdscr.addstr(18, x, "999 ", self.config["color_line_numbers"])
        stdscr.addstr(18, x + 6, "....", self.config["color_tab_odd"])
        stdscr.addstr(18, x + 10, "....", self.config["color_tab_even"])
        stdscr.addstr(18, x + 14, "                                  ", self.config["color_background"])

        stdscr.addstr(19, x + 12, ("Press [RETURN] when done!"), self.config["color_warning"])
        stdscr.refresh()
        c = stdscr.getch()

        if c == curses.KEY_UP:
            i_num -= 1
            if i_num < 0: i_num = 0
            c_num = 0
            style_change = False
        elif c == curses.KEY_DOWN:
            i_num += 1
            if i_num > len(item_list) - 1:
                i_num = len(item_list) - 1
            c_num = 0
            style_change = False
        elif c == curses.KEY_LEFT:
            c_num -= 1
            if c_num < 1: c_num = 1
            style_change = False
            self.config[item_list[i_num]] = colors[color_list[c_num]] + style

        elif c == curses.KEY_RIGHT:
            c_num += 1
            if c_num > len(color_list) - 1:
                c_num = len(color_list) - 1
            style_change = False
            self.config[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("b"), ord("B")):
            style = curses.A_BOLD
            style_change = True
            self.config[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("u"), ord("U")):
            style = curses.A_UNDERLINE
            style_change = True
            self.config[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("n"), ord("N")):  # set style to normal
            style = 0
            style_change = True  # no longer needed?
            self.config[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("o"), ord("O")):
            style = curses.A_BOLD + curses.A_UNDERLINE
            style_change = True
            self.config[item_list[i_num]] = colors[color_list[c_num]] + style


def toggle_protection(mytext):
    """Turns protection on/off for inline commands"""
    global program_message
    if "protect with " in mytext:
        args = get_args(mytext, "_foobar", "protect with ", False)
        if args[1].endswith(" "): args[1] = args[1].rstrip()
        if len(args[1]) > 4: args[1] = args[1][0:4]
        if get_confirmation("Protect commands with '%s'? (y/n)" % args[1]):
            self.config["protect_string"] = args[1]
            self.config["inline_commands"] = "protected"
            program_message = " Commands now protected with '%s' " % args[1]
    else:
        program_message = " Commands protected with '%s' " % self.config["protect_string"]
        arg = get_args(mytext)
        if arg == "on":
            self.config["inline_commands"] = "protected"
        elif arg == "off":
            self.config["inline_commands"] = True
            program_message = " Command protection off! "
        else:
            program_message = " Error, protection not changed "
    reset_line()


def isave():
    """Incremental save - increments last number in filename
            useful for saving versions"""
    global savepath, program_message
    reset_line()
    if not savepath:  # stop incremental save if file has not yet been saved
        get_confirmation("Save file before using incremental save!", True)
        program_message = " Save failed! "
        return
    (directory, filename) = os.path.split(savepath)
    (shortname, ext) = os.path.splitext(filename)
    if filename.startswith('.'):
        shortname = filename
        ext = ""
    else:
        (shortname, ext) = os.path.splitext(filename)

    number = ""
    for i in range(1, len(shortname) + 1):  # determine if name ends with number
        item = shortname[-i]
        if item.isdigit():
            number = item + number
        else:
            break
    if number:  # increment number at end of filename
        newNum = int(number) + 1
        end = len(shortname) - len(number)
        newName = shortname[0:end] + str(newNum)
    else:  # add 2 to end of filename
        newName = shortname + "2"
    newpath = os.path.join(directory, newName) + ext
    save(newpath)


def return_args(temptext):
    """Returns list of args (line numbers, not text)"""
    try:
        the_list = []
        if "," in temptext:
            arg_list = get_args(temptext, " ", ",")
            for i in range(0, len(arg_list)):
                num = int(arg_list[i])
                if num >= 1 and num <= self.lines.total: the_list.append(num)
        elif "-" in temptext:
            arg_list = get_args(temptext, " ", "-")
            start = int(arg_list[0])
            end = int(arg_list[1])
            for num in range(start, end + 1):
                if num >= 1 and num <= self.lines.total: the_list.append(num)
        else:
            arg_list = get_args(temptext)
            if 'str' in str(type(arg_list)):
                num = int(arg_list)
            else:
                num = int(arg_list[0])
            the_list.append(num)
        return the_list
    except:
        return False


def time_stamp():
    """Prints current time & date"""
    global text_entered, program_message, saved_since_edit
    reset_line()
    atime = time.strftime('%m/%d/%y %r (%A)', time.localtime())

    current_line.text = current_line.text + atime
    self.lines.db[current_num].x = self.lines.db[current_num].end_x
    text_entered = True
    saved_since_edit = False
    program_message = " Current time & date printed "


def rotate_string(string, rotateNum,
                  characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 {}[]()!@#$%^&*_+=-'\"\\|/<>,.?~`"):
    """Function that 'rotates' string.
           (I suggest you don't reuse this code in other programs... there are
            better ways to do this in Python)"""
    newtext = ""
    for i in range(0, len(string)):
        char = string[i]
        index_num = characters.find(char)
        if index_num == -1:
            newtext += string[i]
        else:
            position = index_num + rotateNum
            while position >= len(characters):
                position -= len(characters)
            while position < 0:
                position = len(characters) + position
            new_character = characters[position]
            newtext += new_character
    return newtext


def toggle_live(mytext):
    """Toggle syntax highlighting on entry line"""
    global program_message
    program_message = " Live syntax turned off "
    if "off" in mytext or "hide" in mytext:
        self.config["live_syntax"] = False
    elif mytext == "live" and self.config["live_syntax"]:
        self.config["live_syntax"] = False
    else:
        self.config["live_syntax"] = True
        program_message = " Live syntax turned on "
    reset_line()


def toggle_auto(mytext):
    """Toggle feature automation (turns on features based on file type)"""
    global program_message
    program_message = " Auto-settings turned off "
    if "off" in mytext:
        self.config["auto"] = False
    elif mytext == "auto" and self.config["auto"]:
        self.config["auto"] = False
    else:
        self.config["auto"] = True
        program_message = " Auto-settings turned on "
    reset_line()


def toggle_entry(mytext):
    """Toggle entry highlighting (colorizes entry line)"""
    global program_message
    program_message = " Entry highlighting turned off "
    if "off" in mytext or "hide" in mytext:
        self.config["entry_highlighting"] = False
    elif mytext == "entry" and self.config["entry_highlighting"]:
        self.config["entry_highlighting"] = False
    else:
        self.config["entry_highlighting"] = True
        program_message = " Entry highlighting turned on "
    reset_line()


def toggle_comment_formatting(mytext):
    """Toggle comment formatting (formats/colorizes comments)"""
    global program_message
    program_message = " Comment formatting turned off "
    if "off" in mytext or "hide" in mytext:
        self.config["format_comments"] = False
    elif mytext == "formatting" and self.config["format_comments"]:
        self.config["format_comments"] = False
    else:
        self.config["format_comments"] = True
        program_message = " Comment formatting turned on "
    reset_line()
    syntax_visible()
    if self.config["splitscreen"] and self.config["syntax_highlighting"]: syntax_split_screen()


def toggle_page_guide(mytext):
    """Toggle page guide (shows page guide)
        Default width of page is 80 characters."""
    global program_message
    program_message = " Page guide turned off "
    if "off" in mytext or "hide" in mytext:
        self.config["page_guide"] = False
    elif mytext in ["guide", "pageguide"] and self.config["page_guide"]:
        self.config["page_guide"] = False
    elif get_args(mytext) not in ["guide", "pageguide"] and "show" not in mytext and "on" not in mytext:
        try:
            num = int(get_args(mytext))
            if num < 1: num = 80
            self.config["page_guide"] = num
            program_message = " Page guide - %i characters " % num
        except:
            program_message = " Error occured, nothing changed! "
            reset_line()
            return
    else:
        self.config["page_guide"] = 80
        program_message = " Page guide turned on "
    if self.config["page_guide"] > WIDTH - 7:
        if WIDTH > 59:
            program_message = " Error, terminal too small for %i character page guide! " % self.config["page_guide"]
        else:
            program_message = " Error, page guide not displayed "
        self.config["page_guide"] = False
    reset_line()


def show_help():
    """Display help guide"""
    global HELP_GUIDE, current_num, saved_since_edit
    oversized = False

    try:
        if self.lines.db:
            del self.lines.db
            self.lines.db = {}
    except:
        pass
    current_num = 0
    total_rows = 0
    for i in range(0, len(HELP_GUIDE)):
        mytext = HELP_GUIDE[i]

        l = Line(mytext)

        total_rows += (l.number_of_rows - 1)
        if l.number <= (HEIGHT - 2) and current_num + total_rows < (HEIGHT - 2): current_num += 1

    current_num -= 1
    copy_settings()
    self.config["debug"] = False
    self.config["show_indent"] = False
    self.config["entry_highlighting"] = False
    self.config["syntax_highlighting"] = True
    self.config["format_comments"] = True
    self.config["live_syntax"] = True
    self.config["showSpaces"] = False
    self.config["splitscreen"] = False
    self.lines.locked = True
    status["help"] = True
    saved_since_edit = True
    if WIDTH > 80:
        self.config["page_guide"] = 72
    else:
        self.config["page_guide"] = False


def function_help(mytext):
    """Get info about classes, functions, and Modules

            Works with both external modules and
            functions/classes defined within program"""
    global program_message
    reset_line()
    if WIDTH < 79:
        get_confirmation("Help truncated to fit screen", True)
    find_def = "def " + mytext[5:]
    find_class = "class " + mytext[5:]
    search_string = mytext[5:]
    if '.' in search_string:
        myname = "." + search_string.split('.', 1)[1]
    else:
        myname = "foobar_zyx123"
    count = 0
    function_num = 0
    doc_string = []
    mytype = ""
    c = 0
    for i in range(1, len(self.lines.db) + 1):
        item_text = self.lines.db[i].text[Line.db[i].indentation:]
        if item_text.startswith(find_def + "(") or item_text.startswith(find_def + " (") or item_text.startswith(
                find_class + "(") or item_text.startswith(find_class + " ("):
            function_num = i
            mytype = item_text[0:4]
            if mytype == "def ":
                mytype = "FUNCTION"
            if mytype == "clas":
                mytype = "CLASS"
            definition = self.lines.db[i].text
            myname = item_text.split(" ", 1)[1]
            if "(" in myname:
                myname = myname.split("(")[0]
            temp = self.lines.db[i].text.replace(':', '')
            if mytype == "FUNCTION":
                temp = temp.replace("def ", "")

            doc_string.append(temp)
            if self.lines.db[i + 1].text.strip().startswith('"""'):
                start = i + 1
                for n in range(start, len(self.lines.db) + 1):
                    temp = self.lines.db[n].text.replace('"""', '')
                    doc_string.append(temp)
                    if self.lines.db[n].text.endswith('"""'): break

        elif search_string in item_text or myname in item_text:
            if not item_text.startswith("import") and not item_text.startswith("from"):
                count += 1
    if not doc_string:
        mytype = "MODULE"
        if item_text:
            myname = item_text.split(" ", 1)[1]
        else:
            myname = search_string

        shortname = myname
        temp_list = getInfo(search_string, get_modules())
        for item in temp_list: doc_string.append(item)

    if doc_string:
        if doc_string[-1].strip() == "": del doc_string[-1]  # delete last item if blank
        stdscr.addstr(0, 0, (" " * (WIDTH)), self.config["color_header"])
        stdscr.addstr(0, 0, (" %s " % (myname)), self.config["color_message"])
        stdscr.addstr(0, WIDTH - 11, ("Used: %i" % count).rjust(10), self.config["color_header"])
        stdscr.hline(1, 0, curses.ACS_HLINE, WIDTH, self.config["color_bar"])

        start = 0
        while True:
            y = 1
            end = min((start + (HEIGHT - 3)), len(doc_string))
            if end < 1: end = 1
            for l in range(start, end):
                doc_string[l] = doc_string[l].rstrip()
                y += 1
                stdscr.addstr(y, 0, (" " * (WIDTH)), self.config["color_background"])
                if len(doc_string[l]) > WIDTH:
                    stdscr.addstr(y, 0, doc_string[l][0:WIDTH], self.config["color_quote_double"])
                else:
                    stdscr.addstr(y, 0, doc_string[l], self.config["color_quote_double"])
            if len(doc_string) < (HEIGHT - 2):
                stdscr.hline(end + 2, 0, curses.ACS_HLINE, WIDTH, self.config["color_bar"])
                stdscr.addstr(end + 2, WIDTH, "")  # move cursor

            else:
                stdscr.hline(HEIGHT - 1, 0, curses.ACS_HLINE, WIDTH, self.config["color_bar"])
                string = " _Start | _End | Navigate with ARROW keys"
                stdscr.addstr(HEIGHT, 0, (" " * (WIDTH)), self.config["color_header"])  # footer
                print_formatted_text(HEIGHT, string)
                print_formatted_text(HEIGHT, '| _Quit ', 'rjust', WIDTH)
            stdscr.refresh()
            c = stdscr.getch()
            if c == ord('q'):
                break
            elif len(doc_string) < (HEIGHT - 4) and c != 0:  # Exit on key press if help is less than a page
                break

            elif c in (ord('s'), ord('S')):
                start = 0
            elif c in (ord('e'), ord('E')):
                start = len(doc_string) - (HEIGHT - 3)
            elif c == curses.KEY_DOWN:
                start += 1
            elif c == curses.KEY_UP:
                start -= 1
            elif c == curses.KEY_LEFT or c == ord('b'):
                start -= (HEIGHT - 3)
            elif c == curses.KEY_RIGHT or c == 32:
                start += (HEIGHT - 3)

            start = min(start, len(doc_string) - (HEIGHT - 3))
            if len(doc_string) < (HEIGHT - 3): start = 0
            if start < 0: start = 0

    if not doc_string:
        program_message = " Help for '%s' not available! " % search_string


def getInfo(this_item, module_list=['os', 'sys', 'random']):
    """Get info about python modules"""
    import_string = ""
    for item in module_list:
        import_string += str("import %s; " % item)

    p = os.popen("python -c '%s help(%s)'" % (import_string, this_item))

    help_list = p.readlines()
    p.close()
    return help_list


def get_modules():
    """Finds modules in current document"""
    module_list = []
    for i in range(1, len(self.lines.db) + 1):
        mytext = self.lines.db[i].text
        mytext = mytext.strip()
        if mytext.startswith("import ") or mytext.startswith("from "):
            mytext = mytext.replace("import ", "")
            mytext = mytext.replace("from ", "")
            if ';' in mytext:
                for item in mytext.split(";"):
                    if " " in item and item.startswith(" "):
                        module = item.split(" ")[1]
                    elif " " in item:
                        module = item.split(" ")[0]
                    else:
                        module = item.replace(" ", "")
                    module_list.append(module)
            elif ',' in mytext:
                for item in mytext.split(","):
                    if " " in item and item.startswith(" "):
                        module = item.split(" ")[1]
                    elif " " in item:
                        module = item.split(" ")[0]
                    else:
                        module = item.replace(" ", "")
                    module_list.append(module)
            elif " " in mytext:
                module = mytext.split(" ")[0]
                module_list.append(module)
            else:
                module = mytext
                module_list.append(module)
    if not module_list: module_list = ['__builtin__']
    return module_list


def find_window():
    """Opens Find window"""
    global program_message
    find_this = prompt_user("Find what item?")
    if find_this:
        if self.lines.locked:  # In read only mode, find & mark join forces
            for i in range(1, len(self.lines.db) + 1):
                self.lines.db[i].marked = False
            mark("mark %s" % str(find_this))
        find("find %s" % str(find_this))
    else:
        program_message = " Aborted search "


def quit(confirm_needed=True, message=""):
    """Gracefully exits program"""
    global break_now
    break_now = True
    if not saved_since_edit and confirm_needed and not get_confirmation(" Quit without saving? (y/n) "):
        return
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()  # to turn off curses settings
    curses.endwin()  # restore terminal to original condition
    if message:
        print(message)


def encoding_readable(the_path):
    """Check file encoding to see if it can be read by program"""
    if not os.access(the_path, os.R_OK):  # return if file not accesible
        get_confirmation("Access not allowed!", True)
        return False
    rawsize = os.path.getsize(the_path) / 1024.00  # get size and convert to kilobytes
    if rawsize > 8000:
        if get_confirmation("File may not be readable. Continue? (y/n)"):
            return True
        else:
            return False

    myfile = open(the_path)
    temp_lines = myfile.readlines()
    myfile.close()

    try:
        stdscr.addstr(0, 0, temp_lines[-1][0:WIDTH], self.config["color_header"])  # Tests output
        if len(temp_lines) > 100:
            stdscr.addstr(0, 0, temp_lines[-100][0:WIDTH], self.config["color_header"])  # Tests output
        stdscr.addstr(0, 0, (" " * WIDTH))  # clears line
    except:
        get_confirmation("Error, can't read file encoding!", True)
        return False

    skip = int(len(temp_lines) / 10) + 1

    for i in range(0, len(temp_lines), skip):
        string = temp_lines[i]
        string = string.replace("\t", "    ")
        string = string.replace("    ", "    ")
        string = string.replace("\n", "")
        string = string.replace("\r", "")
        string = string.replace("\f", "")  # form feed character, apparently used as seperator?

        try:
            stdscr.addstr(0, 0, string[0:WIDTH], self.config["color_header"])  # Tests output
            stdscr.addstr(0, 0, (" " * WIDTH), self.config["color_header"])  # clears line
        except:
            get_confirmation("Error, can't read file encoding!", True)
            return False
    return True


def read_mode_entry_window():
    """Enter commands in 'Entry Window'"""
    global reset_needed, program_message
    program_message = ""
    reset_needed = False
    mytext = prompt_user()
    if command_match(mytext, "load", "read", False):
        self.lines.locked = False
        load_command(mytext)
    elif command_match(mytext, "new", "<@>_foobar_", False):
        new_doc()

    elif command_match(mytext, "find", "mark", False):
        for i in range(1, len(self.lines.db) + 1):
            self.lines.db[i].marked = False
        mark(mytext)
        find(mytext)

    elif mytext in ("unmark all", "unmark off"):
        unmark_all()
    elif command_match(mytext, "unmark", "<@>_foobar_", False):
        unmark(mytext)
    elif command_match(mytext, "goto", "<@>_foobar_", False):
        goto(mytext)
    elif command_match(mytext, "quit", "<@>_foobar_", False):
        quit()
    elif command_match(mytext, "split", "splitscreen"):
        toggle_split_screen(mytext)  # toggle splitscreen
    elif command_match(mytext, "show split", "hide split"):
        toggle_split_screen(mytext)
    elif command_match(mytext, "show splitscreen", "hide splitscreen"):
        toggle_split_screen(mytext)
    elif mytext == "help":
        if get_confirmation("Load HELP GUIDE? Current doc will be purged! (y/n)"): show_help()
    elif command_match(mytext, "prev", "previous", False):
        prev()
    else:
        get_confirmation("That command not allowed in read mode!", True)
