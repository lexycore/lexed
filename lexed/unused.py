

def split_screen():
    """Display splitscreen"""
    if not settings["splitscreen"]: return

    number = settings["splitscreen"]
    maxrow = int(HEIGHT / 2 + 1)
    print_row = HEADER
    text = " " * (WIDTH)

    for j in range(2, maxrow):
        stdscr.addstr(j, 0, text, settings["color_normal"])  # Clears screen
        stdscr.addstr(j, 0, "     ", settings["color_line_numbers"])  # draws line number background

    if settings["page_guide"]:
        draw_page_guide(end_pos=maxrow, hline_pos=maxrow)  # Draws page guide

    for z in range(number, number + maxrow):

        if z <= 0 or z > Line.total: break
        if print_row > maxrow - 1: break

        stdscr.addstr(print_row, 0, "     ", settings["color_line_numbers"])  # Prints block
        stdscr.addstr(print_row, 0, str(Line.db[z].number), settings["color_line_numbers"])  # Prints next line numbers

        if Line.db[z].marked and Line.db[z].error and settings["debug"]:
            stdscr.hline(print_row, 5, curses.ACS_DIAMOND, 1, settings["color_warning"])  # MARKED & ERROR

        elif Line.db[z].error and settings["debug"]:
            stdscr.addstr(print_row, 4, "!", settings["color_warning"])  # Prints ERROR

        elif Line.db[z].marked and not Line.locked:
            stdscr.hline(print_row, 5, curses.ACS_DIAMOND, 1, settings["color_quote_double"])  # MARKED & ERROR

        for i in range(0, len(Line.db[z].row)):
            if i != 0 and Line.db[z].number_of_rows > HEIGHT - 4:
                break
            if print_row > maxrow - 1:
                try:
                    stdscr.addstr(print_row - 1, WIDTH - 4, " -->", settings["color_quote_double"])
                except:
                    pass
                break

            next_line = Line.db[z].row[i]

            if Line.db[z].selected:
                stdscr.addstr(print_row, 6, (" " * (WIDTH - 6)), settings["color_selection"])  # Prints selected
                stdscr.addstr(print_row, WIDTH, "<", settings["color_quote_double"])  # Prints selected
                stdscr.addstr(print_row, 6, next_line, settings["color_selection"])  # Prints Selected Text
            elif settings["syntax_highlighting"]:
                if not Line.db[z].syntax: Line.db[z].add_syntax()
                templist = Line.db[z].syntax[i]
                printSyntax(templist, 6, print_row)
            else:
                stdscr.addstr(print_row, 6, next_line, settings["color_normal"])  # Prints next line
            if i == 0 and Line.db[z].number_of_rows > HEIGHT - 4:
                stdscr.addstr(print_row, WIDTH - 4, " -->", settings["color_quote_triple"])
            print_row += 1

    stdscr.hline(maxrow, 0, curses.ACS_HLINE, WIDTH, settings["color_bar"])


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


def return_key():
    """Function that handles return/enter key"""
    global current_num, text_entered, program_message, saved_since_edit

    program_message = ""
    saved_since_edit = False

    # new section to deal with undo
    if text_entered:
        update_undo()
        update_que("text entry")

    if settings["syntax_highlighting"]: syntax_visible()

    if current_line.number == Line.total and current_line.x != 6:
        l = Line("")
        current_num += 1

    elif current_line.text and current_line.number_of_rows == 1 and current_line.x > 6 and current_line.x < current_line.end_x:  # split line in two
        part1 = current_line.text[:current_line.x - 6]
        part2 = current_line.text[current_line.x - 6:]
        split_line(current_num, part1, part2)


    elif current_line.text and current_line.number_of_rows > 1 and current_line.y > -(
            current_line.number_of_rows - 1) or current_line.x > 6:  # split line in two
        prevPart = ""
        afterPart = ""

        currentLine1 = current_line.row[current_line.y + current_line.number_of_rows - 1][:current_line.x - 6]
        currentLine2 = current_line.row[current_line.y + current_line.number_of_rows - 1][current_line.x - 6:]

        for i in range(0, -(current_line.number_of_rows), -1):
            r = i + current_line.number_of_rows - 1

            if current_line.y > i:
                prevPart = current_line.row[r] + prevPart
            elif current_line.y < i:
                afterPart = current_line.row[r] + afterPart

        part1 = prevPart + currentLine1
        part2 = currentLine2 + afterPart

        split_line(current_num, part1, part2)

    elif not current_line.text:
        insert(current_line.number)  # new bit, inserts line
        current_num += 1
    elif current_line.x == current_line.end_x:
        current_num += 1
        Line.db[current_num].x = 6
        Line.db[current_num].y = Line.db[current_num].end_y
    elif current_line.x == 6:
        insert(current_line.number)  # new bit, inserts line
        current_num += 1
    else:
        pass
    debug_visible()


def find(mytext):
    """Search feature
            'find keyword' moves to first instance of 'keyword'
            'find' moves to next match"""
    global current_num, last_search, program_message, prev_line
    prev_line = current_num  # set previous line to current line
    collapsed_lines = False
    count = 0
    findthis = "$!*_foobar"
    show_message = False

    reset_line()

    if len(mytext) > 5 and last_search != findthis:
        findthis = mytext[5:]
        last_search = findthis
        for i in range(1, len(Line.db) + 1):
            item = Line.db[i]
            if findthis in item.text or findthis == item.text: count += item.text.count(findthis)
        show_message = True
    else:
        findthis = last_search

    if current_num != len(Line.db):
        for i in range(current_num + 1, len(Line.db) + 1):
            item = Line.db[i]
            if item.collapsed:  # skip lines that are collapsed (don't search in collapsed lines)
                collapsed_lines = True
                continue
            if findthis in item.text or findthis == item.text:
                current_num = i
                Line.db[current_num].x = Line.db[current_num].end_x  # update cursor position
                if show_message: program_message = " %i matches found " % count
                syntax_visible()
                return

    for i in range(1, len(Line.db) + 1):
        item = Line.db[i]
        if item.collapsed:  # skip lines that are collapsed (don't search in collapsed lines)
            collapsed_lines = True
            continue
        if findthis in item.text or findthis == item.text:
            current_num = i
            Line.db[current_num].x = Line.db[current_num].end_x  # update cursor position
            if show_message: program_message = " %i matches found " % count
            syntax_visible()
            return

    if collapsed_lines:
        program_message = " Item not found; collapsed lines not searched! "
    else:
        program_message = " Item not found! "


def select_up(mytext):
    """Function that selects lines upward till blank line reached"""
    global program_message
    selectTotal = 0
    reset_line()
    for i in range(1, len(Line.db) + 1):  # Deselect all
        Line.db[i].selected = False
    if current_num == 1:
        program_message = " Error, no lines to select! "
        return
    for i in range(current_num - 1, 0, -1):
        if not Line.db[i].text.strip(): break
        selectTotal += 1
    for i in range(current_num - 1, 0, -1):
        if not Line.db[i].text.strip(): break
        Line.db[i].selected = True
    program_message = " Selected %i lines " % selectTotal


def select_down(mytext):
    """Function that selects lines downward till blank line reached"""
    global program_message
    selectTotal = 0
    reset_line()
    for i in range(1, len(Line.db) + 1):  # Deselect all
        Line.db[i].selected = False
    if current_num == Line.total:
        program_message = " Error, no lines to select! "
        return
    for i in range(current_num + 1, Line.total + 1):
        if not Line.db[i].text.strip(): break
        selectTotal += 1
    for i in range(current_num + 1, Line.total + 1):
        if not Line.db[i].text.strip(): break
        Line.db[i].selected = True
    program_message = " Selected %i lines " % selectTotal


def mark(mytext):
    """Function that flags lines as 'marked'.

    Can mark line numbers or lines containing text string

        ex: mark myFunction()
            mark 1-10
            mark 16,33"""

    global program_message, current_num
    isNumber = False
    markTotal = 0
    lineTotal = 0

    reset_line()

    if len(mytext) <= 5:  # if no arguments, mark current line and return
        Line.db[current_num].marked = True
        program_message = " Marked line number %i " % current_num
        return

    temptext = mytext[5:]

    try:
        if temptext.replace(" ", "").replace("-", "").replace(",", "").isdigit(): isNumber = True
    except:
        isNumber = False

    try:
        if isNumber:
            if "," in mytext:
                argList = get_args(mytext, " ", ",")
                for i in range(len(argList) - 1, -1, -1):
                    num = int(argList[i])
                    Line.db[num].marked = True
                    if settings["syntax_highlighting"]: Line.db[num].add_syntax()
                    lineTotal += 1
                    if len(argList) > 200 and Line.total > 500 and num / 10.0 == int(num / 10.0): status_message(
                        "Processing: ", (100 / ((len(argList) + 1) * 1.0 / (num + 1))))
            elif "-" in mytext:
                argList = get_args(mytext, " ", "-")
                start = max(1, int(argList[0]))
                end = min(len(Line.db), int(argList[1]))
                for i in range(end, start - 1, - 1):
                    Line.db[i].marked = True
                    if settings["syntax_highlighting"]: Line.db[i].add_syntax()
                    lineTotal += 1

                    if (end - start) > 200 and Line.total > 500 and i / 10.0 == int(i / 10.0):
                        status_message("Processing: ", (100 / ((end - start) * 1.0 / lineTotal)))

            else:
                argList = get_args(mytext)
                if 'str' in str(type(argList)):
                    num = int(argList)
                else:
                    num = int(argList[0])
                Line.db[num].marked = True
                if settings["syntax_highlighting"]: Line.db[num].add_syntax()
                program_message = " Marked line number %i " % num
                lineTotal += 1

        else:  # if not number, search for text
            findthis = temptext
            for i in range(1, len(Line.db) + 1):
                item = Line.db[i]
                if Line.total > 500 and i / 10.0 == int(i / 10.0): status_message("Processing: ", (
                        100 / ((len(Line.db) + 1) * 1.0 / (i + 1))))
                if findthis in item.text or findthis == item.text:
                    item.marked = findthis
                    markTotal += item.text.count(findthis)
                    lineTotal += 1
                    if settings["syntax_highlighting"]: item.add_syntax()

        if markTotal > 1:
            program_message = " Marked %i lines (%i items) " % (lineTotal, markTotal)
        elif lineTotal > 1 and not program_message:
            program_message = " Marked %i lines " % lineTotal
        elif lineTotal == 1 and not program_message:
            program_message = " Marked 1 line "
        elif not program_message:
            program_message = " No items found! "
    except:
        program_message = " Error, mark failed! "


def select(mytext):
    """Function that flags lines as 'selected'.

    Can select function name, line numbers, or marked items

        ex: select myFunction()
            select 1-10
            select 16,33"""

    global program_message, current_num
    is_number = False
    select_total = 0
    line_total = 0

    reset_line()

    for i in range(1, len(Line.db) + 1):  # Deselect all
        Line.db[i].selected = False

    if len(mytext) <= 7:  # if no arguments, select current line and return
        Line.db[current_num].selected = True
        program_message = " Selected line number %i " % current_num
        return

    if mytext == "select all":
        mytext = "select 1-%i" % (Line.total)  # handle 'select all'
    temptext = mytext[7:]

    try:
        if temptext.replace(" ", "").replace("-", "").replace(",", "").isdigit():
            is_number = True
    except:
        is_number = False

    try:
        if is_number:
            if "," in mytext:
                arg_list = get_args(mytext, " ", ",")
                for i in range(len(arg_list) - 1, -1, -1):
                    num = int(arg_list[i])
                    Line.db[num].selected = True
                    line_total += 1
            elif "-" in mytext:
                arg_list = get_args(mytext, " ", "-")
                start = max(1, int(arg_list[0]))
                end = min(len(Line.db), int(arg_list[1]))
                for i in range(end, start - 1, - 1):
                    Line.db[i].selected = True
                    line_total += 1
            else:
                arg_list = get_args(mytext)
                if 'str' in str(type(arg_list)):
                    num = int(arg_list)
                else:
                    num = int(arg_list[0])
                Line.db[num].selected = True
                program_message = " Selected line number %i " % num
                line_total += 1

        else:
            if mytext == "select marked":
                for i in range(1, len(Line.db) + 1):
                    if Line.db[i].marked:
                        Line.db[i].selected = True
                        line_total += 1
                if line_total < 1: program_message = " Nothing selected, no lines marked! "

            else:  # Search for function or class
                findfunction = "def " + temptext + "("
                findclass = "class " + temptext + "("
                for i in range(1, len(Line.db) + 1):
                    item = Line.db[i]
                    if item.text.strip().startswith(findfunction) or item.text.strip().startswith(findclass):
                        if item.text.strip().startswith("def"):
                            item_found = "function"
                        elif item.text.strip().startswith("class"):
                            item_found = "class"
                        item.selected = True
                        line_total = 1
                        indent_needed = item.indentation
                        start_num = i + 1
                        break
                if not line_total:
                    program_message = " Specified function/class not found! "
                    return

                for i in range(start_num, Line.total):
                    if Line.db[i].text and Line.db[i].indentation <= indent_needed: break
                    Line.db[i].selected = True
                    line_total += 1
                program_message = " Selected %s '%s' (%i lines) " % (item_found, temptext, line_total)

        if settings["syntax_highlighting"]: syntax_visible()
        if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()

        if line_total > 1 and not program_message:
            program_message = " Selected %i lines " % line_total
        elif line_total == 1 and not program_message:
            program_message = " Selected 1 line "
        elif not program_message:
            program_message = " No items found! "
    except:
        program_message = " Error, select failed! "


def unmark(mytext):
    """Function that flags lines as 'unmarked'."""
    global program_message
    is_number = False
    mark_total = 0

    reset_line()

    if len(mytext) <= 7:  # if no arguments, unmark current line and return
        Line.db[current_num].marked = False
        if settings["syntax_highlighting"]: Line.db[current_num].add_syntax()
        program_message = " Unmarked line number %i " % current_num
        return

    temptext = mytext[7:]

    try:
        if temptext.replace(" ", "").replace("-", "").replace(",", "").isdigit(): is_number = True
    except:
        is_number = False

    try:
        if is_number:
            if "," in mytext:
                arg_list = get_args(mytext, " ", ",")
                for i in range(len(arg_list) - 1, -1, -1):
                    num = int(arg_list[i])
                    Line.db[num].marked = False
                    if settings["syntax_highlighting"]: Line.db[num].add_syntax()
                    mark_total += 1
                    if len(arg_list) > 200 and Line.total > 500 and i / 10.0 == int(i / 10.0): status_message(
                        "Processing: ", (100 / ((len(arg_list) + 1) * 1.0 / (i + 1))))
            elif "-" in mytext:
                arg_list = get_args(mytext, " ", "-")
                start = max(1, int(arg_list[0]))
                end = min(len(Line.db), int(arg_list[1]))
                for i in range(end, start - 1, - 1):
                    was_marked = False
                    if Line.db[i].marked: was_marked = True
                    Line.db[i].marked = False
                    if settings["syntax_highlighting"] and was_marked: Line.db[i].add_syntax()
                    mark_total += 1
                    status_message("Processing: ", (100 / ((end - start) * 1.0 / mark_total)))

            else:
                arg_list = get_args(mytext)
                if 'str' in str(type(arg_list)):
                    num = int(arg_list)
                else:
                    num = int(arg_list[0])
                Line.db[num].marked = False
                if settings["syntax_highlighting"]: Line.db[num].add_syntax()
                program_message = " Unmarked line number %i " % num
                mark_total += 1

        else:  # if not number, search for text
            findthis = temptext
            for i in range(1, len(Line.db) + 1):
                item = Line.db[i]
                if Line.total > 500 and i / 10.0 == int(i / 10.0): status_message("Processing: ", (
                        100 / ((len(Line.db) + 1) * 1.0 / (i + 1))))
                if findthis in item.text or findthis == item.text:
                    item.marked = False
                    if settings["syntax_highlighting"]: Line.db[i].add_syntax()
                    mark_total += 1
        if mark_total > 1:
            program_message = " Unmarked %i lines " % mark_total
        elif mark_total == 1 and not program_message:
            program_message = " Unmarked 1 line "
        elif not program_message:
            program_message = " No items found! "
    except:
        program_message = " Error, mark failed! "


def deselect(mytext):
    """Function that flags lines as 'deselected'."""
    global program_message
    is_number = False
    select_total = 0
    line_total = 0

    reset_line()

    if len(mytext) <= 9:  # if no arguments, deselect all
        program_message = " All lines deselected "
        deselect_all()
        return

    temptext = mytext[9:]

    try:
        if temptext.replace(" ", "").replace("-", "").replace(",", "").isdigit():
            is_number = True
    except:
        is_number = False

    try:
        if is_number:
            if "," in mytext:
                arg_list = get_args(mytext, " ", ",")
                for i in range(len(arg_list) - 1, -1, -1):
                    num = int(arg_list[i])
                    Line.db[num].selected = False
                    select_total += 1
            elif "-" in mytext:
                arg_list = get_args(mytext, " ", "-")
                start = max(1, int(arg_list[0]))
                end = min(len(Line.db), int(arg_list[1]))
                for i in range(end, start - 1, - 1):
                    Line.db[i].selected = False
                    select_total += 1
            else:
                arg_list = get_args(mytext)
                if 'str' in str(type(arg_list)):
                    num = int(arg_list)
                else:
                    num = int(arg_list[0])
                Line.db[num].selected = False
                program_message = " Deselected line number %i " % num
                select_total += 1

        else:
            if mytext in ("deselect marked", "unselect marked"):
                for i in range(1, len(Line.db) + 1):
                    if Line.db[i].marked:
                        Line.db[i].selected = False
                        line_total += 1
                if line_total < 1:
                    program_message = " Nothing selected, no lines marked! "
                else:
                    program_message = " Deselected %i lines " % line_total

            else:  # Search for function or class
                findfunction = "def " + temptext + "("
                findclass = "class " + temptext + "("
                for i in range(1, len(Line.db) + 1):
                    item = Line.db[i]
                    if item.text.strip().startswith(findfunction) or item.text.strip().startswith(findclass):
                        if item.text.strip().startswith("def"):
                            item_found = "function"
                        elif item.text.strip().startswith("class"):
                            item_found = "class"
                        item.selected = False
                        line_total = 1
                        indent_needed = item.indentation
                        start_num = i + 1
                        break
                if not line_total:
                    program_message = " Specified function/class not found! "
                    return

                for i in range(start_num, Line.total):
                    if Line.db[i].text and Line.db[i].indentation <= indent_needed: break
                    Line.db[i].selected = False
                    line_total += 1
                program_message = " Delected %s '%s' (%i lines) " % (item_found, temptext, line_total)

        if settings["syntax_highlighting"]:
            syntax_visible()
        if settings["splitscreen"] and settings["syntax_highlighting"]:
            syntax_split_screen()

        if select_total > 1:
            program_message = " Deselected %i lines " % select_total
        elif select_total == 1 and not program_message:
            program_message = " Deselected 1 line "
        elif not program_message:
            program_message = " No items found! "
    except:
        program_message = " Error, select failed! "


def unmark_all():
    """Unmark all lines"""
    global program_message
    program_message = " All lines unmarked "
    for i in range(1, len(Line.db) + 1):
        was_marked = False
        if Line.db[i].marked:
            was_marked = True
        Line.db[i].marked = False
        if settings["syntax_highlighting"] and was_marked:
            Line.db[i].add_syntax()
        if Line.total > 500 and i / 20.0 == int(i / 20.0):
            status_message("Processing: ", (100 / ((len(Line.db) + 1) * 1.0 / (i + 1))))
    reset_line()


def deselect_all():
    """Deselect all lines"""
    global program_message
    program_message = " All lines deselected "
    for i in range(1, len(Line.db) + 1):
        Line.db[i].selected = False
    syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]:
        syntax_split_screen()


def goto(mytext):
    """program specific function which moves to given line number"""
    global current_num, program_message, prev_line
    prev_line = current_num
    tempstring = mytext[5:]
    item_found = ""
    reset_line()
    try:
        if not tempstring.isdigit():  # Find function or class
            findfunction = "def " + tempstring + "("
            findclass = "class " + tempstring + "("
            for i in range(1, len(Line.db) + 1):
                item = Line.db[i]
                if item.text.strip().startswith(findfunction) or item.text.strip().startswith(findclass):
                    if item.text.strip().startswith("def"):
                        item_found = "function"
                    elif item.text.strip().startswith("class"):
                        item_found = "class"
                    tempstring = i
                    break
            if tempstring == mytext[5:]:
                if tempstring == "start":
                    tempstring = 1
                elif tempstring == "end":
                    tempstring = Line.total
                else:
                    for i in range(1, len(Line.db) + 1):
                        item = Line.db[i]
                        if item.text.strip().startswith("def %s" % tempstring) or item.text.strip().startswith(
                                "class %s" % tempstring):
                            if item.text.strip().startswith("def"):
                                item_found = "function"
                            elif item.text.strip().startswith("class"):
                                item_found = "class"
                            tempstring = i
                            break

            if tempstring == mytext[5:]:
                program_message = " Specified function/class not found! "
                return

        current_num = max(min(int(tempstring), Line.total), 1)
        Line.db[current_num].x = Line.db[current_num].end_x  # update cursor position
        if Line.db[current_num].collapsed:
            program_message = " Moved to line %i (collapsed) " % (current_num)
        else:
            program_message = " Moved from line %i to %i " % (prev_line, current_num)
        if settings["syntax_highlighting"]: syntax_visible()
    except:
        program_message = " Goto failed! "


def prev():
    """Goto previous line"""
    global program_message, prev_line, current_num
    reset_line()
    try:
        current = current_num
        current_num = prev_line
        prev_line = current
        Line.db[current_num].x = Line.db[current_num].end_x  # update cursor position
        program_message = " Moved from line %i to %i " % (prev_line, current_num)
        if settings["syntax_highlighting"]:
            syntax_visible()
    except:
        program_message = " Prev failed! "


def comment(mytext):
    """New comment function that uses returnArgs"""
    global saved_since_edit, program_message
    reset_line()
    selection = False
    if mytext == "comment":
        selection, item_count = get_selected()
        if selection:
            mytext = "comment %s" % selection
    try:
        mylist = return_args(mytext)
        count = len(mylist)
        update_que("COMMENT operation")
        update_undo()
        loop_num = 0
        for i in mylist:
            loop_num += 1
            if Line.db[i].text:
                Line.db[i].text = "#" + Line.db[i].text
                if settings["debug"] and i > 1:  # update error status
                    Line.db[i].error = False
                    error_test(Line.db[i].number)  # test for code errors
                if len(mylist) > 200 and i / 10.0 == int(i / 10.0) and settings["syntax_highlighting"]:
                    status_message("Processing: ", (100 / ((len(mylist) + 1.0) / (loop_num))))
            else:
                count -= 1
            if i == current_num: Line.db[current_num].x = Line.db[current_num].end_x
        if selection:
            program_message = " Selection commented (%i lines) " % count
        elif len(mylist) == 1 and count == 1:
            program_message = " Commented line number %i " % mylist[0]
        else:
            program_message = " Commented %i lines " % count
    except:
        program_message = " Error, Comment Failed! "
    if settings["syntax_highlighting"]: syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()
    saved_since_edit = False


def uncomment(mytext):
    """New uncomment function that uses returnArgs"""
    global saved_since_edit, program_message
    reset_line()
    selection = False
    if mytext == "uncomment":
        selection, item_count = get_selected()
        if selection:
            mytext = "Uncomment %s" % selection
    try:
        mylist = return_args(mytext)
        count = len(mylist)
        update_que("UNCOMMENT operation")
        update_undo()
        loop_num = 0
        for num in mylist:
            loop_num += 1
            if Line.db[num].text and Line.db[num].text[0] == "#":
                Line.db[num].text = Line.db[num].text[1:]
                if settings["debug"] and num > 1:  # update error status
                    Line.db[num].error = False
                    error_test(Line.db[num].number)  # test for code errors
                if len(mylist) > 200 and num / 10.0 == int(num / 10.0) and settings["syntax_highlighting"]:
                    status_message("Processing: ", (100 / ((len(mylist) + 1.0) / (loop_num))))
            else:
                count -= 1
            if num == current_num: Line.db[current_num].x = Line.db[current_num].end_x  # reset cursor if current line
        if selection:
            program_message = " Selection uncommented (%i lines) " % count
        elif len(mylist) == 1 and count == 1:
            program_message = " Uncommented line number %i " % mylist[0]
        else:
            program_message = " Uncommented %i lines " % count
    except:
        program_message = " Error, Uncomment Failed! "
    if settings["syntax_highlighting"]: syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()
    saved_since_edit = False


def indent(mytext):
    """New indent function that uses returnArgs"""
    global saved_since_edit, program_message
    reset_line()
    selection = False
    if mytext == "indent":
        selection, item_count = get_selected()
        if selection:
            mytext = "Indent %s" % selection
    reset_line()
    try:
        mylist = return_args(mytext)
        count = len(mylist)
        update_que("INDENT operation")
        update_undo()
        loop_num = 0
        for num in mylist:
            loop_num += 1
            if Line.db[num].text:
                Line.db[num].text = "    " + Line.db[num].text
                if settings["debug"] and num > 1:  # update error status
                    Line.db[num].error = False
                    error_test(Line.db[num].number)  # test for code errors
                if len(mylist) > 200 and num / 10.0 == int(num / 10.0) and settings["syntax_highlighting"]:
                    status_message("Processing: ", (100 / ((len(mylist) + 1.0) / (loop_num))))
            else:
                count -= 1
            if num == current_num: Line.db[current_num].x = Line.db[current_num].end_x  # reset cursor if current line
        if selection:
            program_message = " Selection indented (%i lines) " % count
        elif len(mylist) == 1 and count == 1:
            program_message = " Indented line number %i " % mylist[0]
        else:
            program_message = " Indented %i lines " % count
    except:
        program_message = " Error, Indent Failed! "
    if settings["syntax_highlighting"]: syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()

    saved_since_edit = False


def unindent(mytext):
    """New unindent function that uses returnArgs"""
    global saved_since_edit, program_message
    reset_line()
    selection = False
    if mytext == "unindent":
        selection, item_count = get_selected()
        if selection:
            mytext = "unindent %s" % selection
    try:
        mylist = return_args(mytext)
        count = len(mylist)
        update_que("UNINDENT operation")
        update_undo()
        loop_num = 0
        for num in mylist:
            loop_num += 1
            if Line.db[num].text and Line.db[num].text[0:4] == "    ":
                Line.db[num].text = Line.db[num].text[4:]
                if settings["debug"] and num > 1:  # update error status
                    Line.db[num].error = False
                    error_test(Line.db[num].number)  # test for code errors
                if len(mylist) > 200 and num / 10.0 == int(num / 10.0) and settings["syntax_highlighting"]:
                    status_message("Processing: ", (100 / ((len(mylist) + 1.0) / (loop_num))))
            else:
                count -= 1
            if num == current_num: Line.db[current_num].x = Line.db[current_num].end_x  # reset cursor if current line
        if selection:
            program_message = " Selection unindented (%i lines) " % count
        elif len(mylist) == 1 and count == 1:
            program_message = " Unindented line number %i " % mylist[0]
        else:
            program_message = " Unindented %i lines " % count
    except:
        program_message = " Error, Unindent Failed! "
    if settings["syntax_highlighting"]: syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()
    saved_since_edit = False


def run():
    """Run command executes python code in a separate window"""
    mypath = os.path.expanduser("~")
    temp_file = os.path.join(mypath, ".TEMP_lexed_runfile.tmp")

    text_file = open(temp_file, "w")
    text_file.write("try:\n")
    for key in Line.db:
        this_text = ("    " + Line.db[key].text + "\n")
        text_file.write(this_text)
    text_file.write(
        "except(NameError, IOError, IndexError, KeyError, SyntaxError, TypeError, ValueError, ZeroDivisionError, IndentationError),e:\n")
    text_file.write("    print 'ERROR:',e\n")
    text_file.write("else:\n")
    text_file.write("    print 'Run complete.'\n")
    hold_message = """raw_input("Press 'enter' to end")"""
    text_file.write(hold_message)
    text_file.close()
    entry_list = []
    mystring = ""
    os.system("%s python %s" % (settings["terminal_command"], temp_file))  # Run program
    os.system("sleep 1")
    os.system("rm %s" % temp_file)  # Delete tempFile


def command_match(text_string, command, alt="<@>_foobar_", protect_needed=True):
    """Gets 'command' from string, returns False if next character is '='."""
    if text_string == "<@>_foobar_":
        return False
    text_list = ""
    orig_text = text_string
    try:
        if not text_string or text_string[0] == " ":
            return False

        if not settings["inline_commands"] and protect_needed:
            return False

        if " " in text_string and " " not in command:
            text_list = text_string.split()
            if len(text_list) > 1:
                if text_list[1] and text_list[1][0] in ("=", "+", "-", "*", "/", "%", "(", "[", "{"):
                    if command in ("replace", "protect") and " with " in text_string:
                        pass
                    elif command in ("save", "saveas", "load") and text_list[1][0] == "/":
                        pass
                    else:
                        return False
                if command in ("replace", "protect") and text_string.count(
                        " ") > 3 and " with " not in text_string and "|" not in text_string:
                    return False
                text_string = text_list[0]

        if settings["inline_commands"] == "protected" and protect_needed:
            command = settings["protect_string"] + command
            alt = settings["protect_string"] + alt
            temp_text = text_string.replace(settings["protect_string"], "")
        else:
            temp_text = text_string

        if command in (
                "syntax", "entry", "live", "formatting", "tab", "tabs", "whitespace", "show", "hide", "goto", "color",
                "help",
                "debug", "split", "guide", "pageguide") and len(text_list) > 2:
            return False

        if alt in (
                "syntax", "entry", "live", "formatting", "tab", "tabs", "whitespace", "show", "hide", "goto", "color",
                "help",
                "debug", "split", "guide", "pageguide") and len(text_list) > 2:
            return False

        if temp_text not in ("replace", "protect", "find", "save", "saveas", "load", "mark") and orig_text.count(
                " ") - 1 > orig_text.count(",") + (2 * orig_text.count("-")):
            return False
        if temp_text not in ("replace", "protect", "find", "save", "saveas", "load", "mark") and orig_text.count(
                "-") > 1:
            return False
        if temp_text not in (
                "replace", "protect", "find", "save", "saveas", "load",
                "mark") and "-" in orig_text and "," in orig_text:
            return False

        if text_string == command or text_string == alt:
            if settings["inline_commands"] == "protected" and protect_needed:
                current_line.text = current_line.text[len(settings["protect_string"]):]
            return True
        else:
            return False
    except:
        return False


def replace_text(mytext):
    """Function to replace old text with new"""
    global program_message, saved_since_edit
    selection, item_count = get_selected()
    if "replace marked" in mytext:
        replace_marked(mytext)
        return
    elif "replace selected" in mytext:
        replace_selected(mytext)
        return
    elif selection and get_confirmation("Act on %i selected lines only? (y/n)" % item_count):
        replace_selected(mytext, False)
        return
    try:
        if "|" in mytext:
            (oldtext, newtext) = get_args(mytext, " ", "|", False)
        else:
            (oldtext, newtext) = get_args(mytext, " ", " with ", False)
    except:
        get_confirmation("Error occurred, replace operation failed!", True)
        return
    reset_line()
    replace_num = 0

    # calculate number of replacements
    for i in range(1, len(Line.db) + 1):
        item = Line.db[i]
        if oldtext in item.text: replace_num += item.text.count(oldtext)
    if replace_num:  # Confirm replacement
        if replace_num > 1:
            message_text = "Replace %i items? (y/n)" % replace_num
        else:
            message_text = "Replace 1 item? (y/n)"

        if not get_confirmation(message_text):
            program_message = " Replace aborted! "
            return
        else:  # replace items

            update_que("REPLACE operation")
            update_undo()

            for i in range(1, len(Line.db) + 1):
                item = Line.db[i]
                if oldtext in item.text:
                    if replace_num > 200 and i / 10.0 == int(i / 10.0):  # display processing message
                        status_message("Processing: ", (100 / ((len(Line.db) + 1) * 1.0 / (i + 1))))
                    temptext = item.text
                    temptext = temptext.replace(oldtext, newtext)
                    item.text = temptext
                    if settings["syntax_highlighting"]: item.add_syntax()  # adjust syntax
                    if settings["debug"] and i > 1:
                        Line.db[i].error = False
                        error_test(Line.db[i].number)  # test for code errors
            program_message = " Replaced %i items " % replace_num
        saved_since_edit = False
    else:
        get_confirmation("   Item not found!    ", True)


def replace_marked(mytext):
    """Replace items in marked lines only"""
    global program_message, saved_since_edit
    count = 0
    mark_total = 0
    reset_line()
    for i in range(1, len(Line.db) + 1):  # count number of marked lines
        if Line.db[i].marked: mark_total += 1
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

    for i in range(1, len(Line.db) + 1):
        item = Line.db[i]
        if item.marked and oldtext in item.text:
            item.text = item.text.replace(oldtext, newtext)
            count += 1
            if settings["syntax_highlighting"]: item.add_syntax()  # adjust syntax
            if settings["debug"] and i > 1:
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
    for i in range(1, len(Line.db) + 1):  # count number of selected lines
        if Line.db[i].selected: select_total += 1
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

    for i in range(1, len(Line.db) + 1):
        item = Line.db[i]
        if item.selected and oldtext in item.text:
            item.text = item.text.replace(oldtext, newtext)
            count += 1
            if settings["syntax_highlighting"]: item.add_syntax()  # adjust syntax
            if settings["debug"] and i > 1:
                item.error = False
                error_test(item.number)  # test for code errors

    program_message = " Replaced %i items " % count
    if count == 0:
        get_confirmation("   Item not found.    ", True)
    else:
        saved_since_edit = False


def copy(mytext, select_only=False):
    """Copy lines to internal 'clipboard'"""
    global clipboard, program_message
    reset_line()
    if mytext == "copy" or select_only:
        selection, item_count = get_selected()
        if selection:
            mytext = "copy %s" % selection
            if settings["deselect_on_copy"]:
                selection, item_count = get_selected()
                line_list = selection.split(",")
                for item in line_list:
                    linenum = int(item)
                    Line.db[linenum].selected = False
            select_only = True
    length = 1
    try:
        clipboard = []
        temptext = mytext
        if "," in temptext:
            argList = get_args(temptext, " ", ",")
            length = len(argList)
            for i in range(len(argList) - 1, -1, -1):
                num = int(argList[i])
                clipboard.append(Line.db[num].text)

        elif "-" in temptext:
            argList = get_args(temptext, " ", "-")
            start = int(argList[0])
            end = int(argList[1])
            length = (end - start) + 1
            if length > 25000:  # Stop copy operations that are too big
                get_confirmation("Copy operation limited to 25000 lines!", True)
                program_message = " Copy canceled, limit exceeded! "
                return
            for i in range(end, start - 1, -1):
                clipboard.append(Line.db[i].text)
        else:
            argList = get_args(temptext)
            if 'str' in str(type(argList)):
                num = int(argList)
            else:
                num = int(argList[0])
            clipboard.append(Line.db[num].text)
            program_message = " Copied line number %i " % num
        if select_only:
            program_message = " Selection copied (%i lines) " % length
        elif not program_message:
            program_message = " %i lines copied " % length
    except:
        reset_line()
        get_confirmation("Error occurred, nothing copied!", True)


def paste(mytext):
    """Paste lines from 'clipboard'"""
    global current_num, program_message, saved_since_edit
    original_num = current_num
    if not clipboard:
        get_confirmation("Nothing pasted, clipboard is empty.", True)
        reset_line()
        return
    if settings["select_on_paste"]: deselect_all()
    saved_since_edit = False

    length = len(clipboard)

    try:
        if get_args(mytext) == "paste":  # Pastes on current line

            temptext = mytext
            reset_line()
            update_que("PASTE operation")
            update_undo()

            if length > 100 and Line.total > 2000:  # New bit to improve performance of BIG paste operations
                program_message = " Paste aborted! "
                if WIDTH >= 69:
                    if get_confirmation("This operation will expand & unmark lines. Continue? (y/n)"): new_paste(
                        clipboard, current_num)
                    return
                else:
                    if get_confirmation("Lines will be unmarked. Continue? (y/n)"): new_paste(clipboard, current_num)
                    return

            current_line.text += clipboard[0]
            if settings["select_on_paste"]: current_line.selected = True

            if length > 1:
                for i in range(1, length):
                    insert(current_num, clipboard[i], True)
                    if Line.total > 2000 and length > 40 and i / 5.0 == int(i / 5.0):
                        status_message("Processing: ", (100 / (length * 1.0 / (i + 1))))

                program_message = " Pasted %i lines at line number %i " % ((len(clipboard)), original_num)
            else:
                program_message = " Pasted text at line %i " % (current_num)
            current_num += len(clipboard) - 1
            Line.db[current_num].x = Line.db[current_num].end_x

        else:
            arg = get_args(mytext)
            num = int(arg)

            reset_line()
            if num > len(Line.db):  # Stop paste operation
                program_message = " Error, line %i does not exist! " % (num)
                return
            update_que("PASTE operation")
            update_undo()

            if length > 100 and Line.total > 2000:  # New bit to improve performance of BIG paste operations
                program_message = " Paste aborted! "
                if WIDTH >= 69:
                    if get_confirmation("This operation will expand & unmark lines. Continue? (y/n)"): new_paste(
                        clipboard, num)
                    return
                else:
                    if get_confirmation("Lines will be unmarked. Continue? (y/n)"): new_paste(clipboard, num)
                    return

            for i in range(0, length):
                insert(num, clipboard[i], True)
                if Line.total > 2000 and length > 40 and i / 5.0 == int(i / 5.0):
                    status_message("Processing: ", (100 / (length * 1.0 / (i + 1))))

            if num <= current_num: current_num += len(clipboard)
            if num > Line.total: num = Line.total - 1  # fix message bug
            if len(clipboard) > 1:
                program_message = " Pasted (inserted) %i lines at line number %i " % ((len(clipboard)), num)
            else:
                program_message = " Pasted (inserted) text at line %i " % (num)
    except:
        reset_line()
        get_confirmation("Error occurred, nothing pasted!", True)


def undo():
    """Function that reverses command/restores state to last edit"""
    global current_num, undo_list, undo_text_que, undo_state_que, undo_state, undo_mark_que, undo_mark, program_message, reset_needed, undo_select_que, undo_select
    count = 0
    reset_line()
    if not undo_list:
        get_confirmation("There is nothing to undo!", True)
        return
    if not get_confirmation("Undo last %s? (y/n)" % undo_type):
        return
    del Line.db
    Line.db = {}
    length = len(undo_list)
    for i in range(0, len(undo_list)):
        count += 1
        string = undo_list[i]
        l = Line(string)

        if length > 500 and count / 100.0 == int(count / 100.0):  # display processing message
            status_message("Processing: ", (100 / (length * 1.0 / count)))

        if undo_state: l.collapsed = undo_state[i]
        if undo_mark: l.marked = undo_mark[i]
        if undo_select: l.selected = undo_select[i]
        if settings["syntax_highlighting"]: l.add_syntax()  # adjust syntax
        if settings["debug"]: error_test(l.number)  # test for code errors

    if current_num > Line.total: current_num = Line.total
    undo_list = []
    undo_text_que = []
    undo_state_que = []
    undo_state = []
    undo_mark_que = []
    undo_mark = []
    undo_select_que = []
    undo_select = []

    program_message = " Undo successful "


def enter_commands():
    """Enter commands in 'Entry Window'"""
    global reset_needed, program_message

    program_message = ""
    if Line.db[current_num].text and current_num == Line.total:  # create empty line if position is last line
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
        collapse("collapse 1 - %s" % str(len(Line.db)))
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
        settings["inline_commands"] = False
        program_message = " Inline commands turned off! "
    elif command_match(mytext, "commands on", "<@>_foobar_", False):
        settings["inline_commands"] = True
        program_message = " Inline commands turned on! "
    elif command_match(mytext, "commands protected", "<@>_foobar_", False):
        settings["inline_commands"] = "protected"
        program_message = " Inline commands protected with '%s' " % settings["protect_string"]
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
    Line.db[current_num].error = False
    error_test(current_num)

    if current_num != len(Line.db):
        for i in range(current_num + 1, len(Line.db) + 1):
            item = Line.db[i]
            if item.error and item.collapsed:
                collapsed_bugs = True
            elif item.error:
                current_num = item.number
                return

    for i in range(1, len(Line.db) + 1):
        item = Line.db[i]
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
        stdscr.addstr(0, 0, " " * (WIDTH), settings["color_header"])
        temp_text = "%i" % Line.total
        lines_text = temp_text.rjust(11)
        if settings["inline_commands"] == "protected":
            protect_string = str(settings["protect_string"])
            stdscr.addstr(0, WIDTH - 12 - len(protect_string) - 1, lines_text, settings["color_header"])
            stdscr.addstr(0, WIDTH - len(protect_string) - 1, protect_string, settings["color_message"])
        else:
            stdscr.addstr(0, WIDTH - 12, lines_text, settings["color_header"])
    else:  # clears space for statusMessage only
        stdscr.addstr(0, 0, " " * (WIDTH - 13), settings["color_header"])
    number = int(number)  # Convert to integer
    message = " %s%i" % (mytext, number) + "% "
    stdscr.addstr(0, 0, message, settings["color_warning"])
    stdscr.refresh()


def directory_attributes(file_list, directory, sort_by=settings["default_load_sort"],
                         reverse=settings["default_load_reverse"], show_hidden=settings["default_load_invisibles"]):
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
    sort_type = settings["default_load_sort"]
    reverse_sort = settings["default_load_reverse"]
    show_hidden = settings["default_load_invisibles"]

    directory_contents = directory_attributes(templist, directory, sort_type, reverse_sort,
                                              show_hidden)  # get file attributes from function

    while True:  # User can explore menus until they make a selection or cancel out
        total_pages = int(len(directory_contents) / (HEIGHT - 3))
        if len(directory_contents) % (HEIGHT - 3) != 0: total_pages += 1

        stdscr.clear()
        # print empty lines
        if settings["color_background"]: print_background()
        stdscr.addstr(0, 0, (" " * WIDTH), settings["color_header"])  # Print header
        stdscr.addstr(HEIGHT, 0, (" " * WIDTH), settings["color_header"])  # Print header

        if len(directory) > WIDTH - 14:
            tempstring = "... %s" % directory[(len(directory) - WIDTH) + 14:]  # s[len(s)-WIDTH:]
            stdscr.addstr(0, 0, tempstring, settings["color_header"])  # Print header
        else:
            stdscr.addstr(0, 0, directory, settings["color_header"])  # Print header
        stdscr.addstr(0, (WIDTH - 10), ("page " + str(page) + "/" + str(total_pages)).rjust(10),
                      settings["color_header"])
        stdscr.hline(1, 0, curses.ACS_HLINE, WIDTH, settings["color_bar"])  # print solid line

        stdscr.hline(HEIGHT - 1, 0, curses.ACS_HLINE, WIDTH, settings["color_bar"])  # print solid line

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
                stdscr.addstr(i + 2, 0, (" " * WIDTH), settings["color_entry"])
                # print name
                if name == "../" or name == os.path.expanduser("~"):
                    stdscr.addstr(i + 2, 0, name, settings["color_entry_quote"])
                else:
                    stdscr.addstr(i + 2, 0, name, settings["color_entry"])
                # clear second part of screen
                if view == 6: stdscr.addstr(i + 2, (WIDTH - 54), (" " * (WIDTH - (WIDTH - 54))),
                                            settings["color_entry"])
                if view == 5: stdscr.addstr(i + 2, (WIDTH - 41), (" " * (WIDTH - (WIDTH - 41))),
                                            settings["color_entry"])
                if view == 4: stdscr.addstr(i + 2, (WIDTH - 33), (" " * (WIDTH - (WIDTH - 33))),
                                            settings["color_entry"])
                if view == 3: stdscr.addstr(i + 2, (WIDTH - 21), (" " * (WIDTH - (WIDTH - 21))),
                                            settings["color_entry"])
                if view == 2: stdscr.addstr(i + 2, (WIDTH - 11), (" " * (WIDTH - (WIDTH - 11))),
                                            settings["color_entry"])
                # print file_access
                if view == 6 and num != 0:
                    if access == "NO ACCESS!":
                        stdscr.addstr(i + 2, WIDTH - 51, access, settings["color_warning"])
                    elif access == "READ ONLY ":
                        stdscr.addstr(i + 2, WIDTH - 51, access, settings["color_entry_quote"])
                    elif access == "read/write":
                        stdscr.addstr(i + 2, WIDTH - 51, access, settings["color_entry_command"])
                    else:
                        stdscr.addstr(i + 2, WIDTH - 51, access, settings["color_entry_functions"])

                # print filesize
                if view >= 5 and num != 0: stdscr.addstr(i + 2, WIDTH - 39, (str(filesize) + " KB"),
                                                         settings["color_entry"])
                if view == 4 and num != 0: stdscr.addstr(i + 2, WIDTH - 31, (str(filesize) + " KB"),
                                                         settings["color_entry"])
                if view == 3 and num != 0: stdscr.addstr(i + 2, WIDTH - 19, (str(filesize) + " KB"),
                                                         settings["color_entry"])
                # print mod date
                if view >= 5: stdscr.addstr(i + 2, WIDTH - 25, filemodDate, settings["color_entry"])
                if view == 4: stdscr.addstr(i + 2, WIDTH - 18, (filemodDate.split(" ")[0]), settings["color_entry"])
                # print type
                if view > 1:
                    if filetype == "parent":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_entry_quote"])
                    elif filetype == "DIR":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_entry_number"])
                    elif filetype == "text":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_entry_functions"])
                    elif filetype == "python":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_entry_command"])
                    elif filetype == "encryp":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_entry_comment"])
                    else:
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_entry"])
            else:
                stdscr.addstr(i + 2, 0, (" " * WIDTH), settings["color_background"])
                # print name
                if name == "../" or name == os.path.expanduser("~"):
                    stdscr.addstr(i + 2, 0, name, settings["color_quote_double"])
                else:
                    stdscr.addstr(i + 2, 0, name, settings["color_normal"])
                # clear second part of screen
                if view == 6: stdscr.addstr(i + 2, (WIDTH - 54), (" " * (WIDTH - (WIDTH - 54))),
                                            settings["color_normal"])
                if view == 5: stdscr.addstr(i + 2, (WIDTH - 41), (" " * (WIDTH - (WIDTH - 41))),
                                            settings["color_normal"])
                if view == 4: stdscr.addstr(i + 2, (WIDTH - 33), (" " * (WIDTH - (WIDTH - 33))),
                                            settings["color_normal"])
                if view == 3: stdscr.addstr(i + 2, (WIDTH - 21), (" " * (WIDTH - (WIDTH - 21))),
                                            settings["color_normal"])
                if view == 2: stdscr.addstr(i + 2, (WIDTH - 11), (" " * (WIDTH - (WIDTH - 11))),
                                            settings["color_normal"])

                # print file_access
                if view == 6 and num != 0: stdscr.addstr(i + 2, WIDTH - 51, access, settings["color_dim"])
                # print filesize
                if view >= 5 and num != 0: stdscr.addstr(i + 2, WIDTH - 39, (str(filesize) + " KB"),
                                                         settings["color_dim"])
                if view == 4 and num != 0: stdscr.addstr(i + 2, WIDTH - 31, (str(filesize) + " KB"),
                                                         settings["color_dim"])
                if view == 3 and num != 0: stdscr.addstr(i + 2, WIDTH - 19, (str(filesize) + " KB"),
                                                         settings["color_dim"])
                # print mod date
                if view >= 5: stdscr.addstr(i + 2, WIDTH - 25, filemodDate, settings["color_dim"])
                if view == 4: stdscr.addstr(i + 2, WIDTH - 18, (filemodDate.split(" ")[0]), settings["color_dim"])
                # print type
                if view > 1:
                    if filetype == "parent":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_quote_double"])
                    elif filetype == "DIR":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_number"])
                    elif filetype == "text":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_functions"])
                    elif filetype == "python":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_commands"])
                    elif filetype == "encryp":
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_warning"])
                    else:
                        stdscr.addstr(i + 2, WIDTH - 6, filetype, settings["color_normal"])

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
            stdscr.hline(y, x, curses.ACS_DIAMOND, (1), settings["color_normal"])  # print diamond
            x += 1
        elif item == "|" and reverse == True:
            stdscr.vline(y, x, curses.ACS_VLINE, (1), settings["color_reversed"])  # prints vertical line
            reverse = False
            x += 1
        elif item == "|" and bold == True:
            stdscr.vline(y, x, curses.ACS_VLINE, (1), bold_TEXT)  # prints vertical line
            reverse = False
            x += 1
        elif item == "|":
            stdscr.vline(y, x, curses.ACS_VLINE, (1), settings["color_bar"])  # prints vertical line
            stdscr.hline(y - 1, x, curses.ACS_TTEE, (1), settings["color_bar"])  # Format previous line

            underline = False
            x += 1
        elif underline:
            underline = False
            stdscr.addstr(y, x, item, settings["color_underline"])
            x += 1
        elif bold:
            stdscr.addstr(y, x, item, BOLD_TEXT)
            bold = False
            x += 1
        elif reverse:
            stdscr.addstr(y, x, item, settings["color_reversed"])
            reverse = False
            x += 1
        else:
            stdscr.addstr(y, x, item, settings["color_header"])
            x += 1


def goto_marked():
    """Move to next 'marked' line"""
    global current_num, program_message, prev_line
    if current_num < Line.total:
        for i in range(current_num + 1, len(Line.db) + 1):
            if Line.db[i].marked:
                prev_line = current_num
                current_num = Line.db[i].number
                if settings["syntax_highlighting"]: syntax_visible()
                return
    for i in range(1, current_num):
        if Line.db[i].marked:
            prev_line = current_num
            current_num = Line.db[i].number
            if settings["syntax_highlighting"]: syntax_visible()
            return
    if Line.db[current_num].marked:
        program_message = " No other lines marked! "
    else:
        program_message = " No lines marked! "


def prev_marked():
    """Move to previous 'marked' line"""
    global current_num, program_message, prev_line
    if current_num > 1:
        for i in range(current_num - 1, 0, -1):
            if Line.db[i].marked:
                prev_line = current_num
                current_num = Line.db[i].number
                if settings["syntax_highlighting"]: syntax_visible()
                return
    for i in range(Line.total, current_num, -1):
        if Line.db[i].marked:
            prev_line = current_num
            current_num = Line.db[i].number
            if settings["syntax_highlighting"]: syntax_visible()
            return
    if Line.db[current_num].marked:
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


def toggle_split_screen(mytext):
    """Turn splitscreen on or off"""
    global program_message
    arg = get_args(mytext)
    reset_line()
    program_message = " Splitscreen on "
    if arg == "on":
        settings["splitscreen"] = 1
    elif arg == "off":
        settings["splitscreen"] = False
        program_message = " Splitscreen off "
    elif arg in ("", "split", "splitscreen") and settings["splitscreen"]:
        settings["splitscreen"] = False
        program_message = " Splitscreen off "
    elif arg in ("", "split", "splitscreen") and not settings["splitscreen"]:
        settings["splitscreen"] = 1
    else:
        try:
            if arg == "end": arg = max(1, Line.total - 1)
            if arg == "start": arg = 1
            lineNumber = int(arg)
            maxrow = int(HEIGHT / 2 + 1)
            if lineNumber > Line.total - 1: lineNumber = Line.total - 1
            if lineNumber < 1: lineNumber = 1
            if lineNumber > Line.total: lineNumber = Line.total
            settings["splitscreen"] = lineNumber
            program_message = " Splitscreen @ line %i " % lineNumber
        except:
            program_message = " Error, splitscreen failed! "
            return


def toggle_debug(mytext):
    """Turn debug mode on or off"""
    global program_message
    arg = get_args(mytext)
    reset_line()
    if arg not in ("on", "off") and settings["debug"] == True:
        arg = "off"
    elif arg not in ("on", "off") and settings["debug"] == False:
        arg = "on"
    if arg == "on":
        settings["debug"] = True
        program_message = " Debug on "
    elif arg == "off":
        settings["debug"] = False
        program_message = " Debug off "


def toggle_acceleration(mytext):
    """Turn acceleration on or off"""
    global program_message
    arg = get_args(mytext)
    reset_line()
    if arg not in ("on", "off") and settings["cursor_acceleration"] == True:
        arg = "off"
    elif arg not in ("on", "off") and settings["cursor_acceleration"] == False:
        arg = "on"
    if arg == "on":
        settings["cursor_acceleration"] = True
        program_message = " Cursor acceleration on "
    elif arg == "off":
        settings["cursor_acceleration"] = False
        program_message = " Cursor acceleration off "


def strip_spaces(mytext):
    """Strips extra/trailing spaces from line"""
    global program_message, saved_since_edit
    reset_line()
    update_que("STRIP WHITESPACE operation")
    update_undo()
    count = 0
    for num in range(1, Line.total + 1):
        item = Line.db[num]
        if item.text and item.text.count(" ") == len(item.text):
            item.text = ""
            if settings["syntax_highlighting"]: item.add_syntax()
            if settings["debug"]: error_test(item.number)
            count += 1
        else:
            for i in range(64, 0, -1):
                search = (i * " ")
                if item.text.endswith(search):
                    item.text = item.text[:-i]
                    if settings["syntax_highlighting"]: item.add_syntax()
                    if settings["debug"]: error_test(item.number)
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
    if not settings["display_color"] or not curses.has_colors():
        get_confirmation("You can't set colors in monochrome mode!", True)
        return
    if WIDTH < 79 or HEIGHT < 19:
        get_confirmation("Increase termnal size to set colors!", True)
        return

    settings["default_colors"] = False
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
        stdscr.addstr(i, 0, (" " * WIDTH), settings["color_normal"])
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
        stdscr.hline(3, x, curses.ACS_HLINE, 49, settings["color_bar"])
        if color == "[CURRENT]":
            for key, value in colors.items():
                if settings[item] == value:
                    search = key
                    style = 0
                elif settings[item] == value + curses.A_BOLD:
                    search = key
                    style = curses.A_BOLD
                elif settings[item] == value + curses.A_UNDERLINE:
                    search = key
                    style = curses.A_UNDERLINE
                elif settings[item] == value + curses.A_BOLD + curses.A_UNDERLINE:
                    search = key
                    style = curses.A_BOLD + curses.A_UNDERLINE
            index = color_list.index(search, 1)
            c_num = index
            color = color_list[c_num]

        stdscr.addstr(4, x + 23, (color.replace("_", " ").rjust(25)), colors[color] + style)  # testing
        stdscr.addstr(4, x + 1, ((item.replace("color", "").replace("_", " "))).ljust(23),
                      colors["white_on_blue"] + curses.A_BOLD)  # testing
        stdscr.hline(5, x, curses.ACS_HLINE, 49, settings["color_bar"])
        # print vertical lines
        stdscr.hline(4, x, curses.ACS_VLINE, 1, settings["color_bar"])
        stdscr.hline(4, x + 48, curses.ACS_VLINE, 1, settings["color_bar"])
        # print corners
        stdscr.hline(3, x, curses.ACS_ULCORNER, 1, settings["color_bar"])
        stdscr.hline(3, x + 48, curses.ACS_URCORNER, 1, settings["color_bar"])
        stdscr.hline(5, x, curses.ACS_LLCORNER, 1, settings["color_bar"])
        stdscr.hline(5, x + 48, curses.ACS_LRCORNER, 1, settings["color_bar"])

        if style == curses.A_BOLD + curses.A_UNDERLINE:
            footer = ("_Normal $ _Bold $ _Underline $ *b*O*t*h")
        elif style == curses.A_BOLD:
            footer = ("_Normal $ *B*o*l*d $ _Underline $ b_Oth")
        elif style == curses.A_UNDERLINE:
            footer = ("_Normal $ _Bold $ *U*n*d*e*r*l*i*n*e $ b_Oth")
        else:
            footer = ("*N*o*r*m*a*l $ _Bold $ _Underline $ b_Oth")
        print_formatted_text(6, footer, "center", WIDTH)
        stdscr.addstr(8, x, sample_header, settings["color_comment_centered"])  # Text types need to be changed?
        stdscr.addstr(9, x, seperator, settings["color_comment_separator"])
        stdscr.addstr(10, x, sample_left, settings["color_comment_leftjust"])
        stdscr.addstr(11, x, sample_right, settings["color_comment_rightjust"])

        stdscr.addstr(12, x, "class", settings["color_class"])
        stdscr.addstr(12, x + 12, "collapsed", settings["color_class_reversed"])
        stdscr.addstr(12, x + 28, "print", settings["color_commands"])
        stdscr.addstr(12, x + 40, "#comment", settings["color_comment"])

        stdscr.addstr(13, x, "def", settings["color_functions"])
        stdscr.addstr(13, x + 12, "collapsed", settings["color_functions_reversed"])
        stdscr.addstr(13, x + 28, "True", settings["color_positive"])
        stdscr.addstr(13, x + 40, "False", settings["color_negative"])

        stdscr.addstr(14, x, "'quote'", settings["color_quote_single"])
        stdscr.addstr(14, x + 12, '"double"', settings["color_quote_double"])
        stdscr.addstr(14, x + 28, '"""doc"""', settings["color_quote_triple"])

        stdscr.addstr(14, x + 40, 'CONSTANT', settings["color_constant"])

        stdscr.addstr(15, x, "()!=[]+-", settings["color_operator"])
        stdscr.addstr(15, x + 12, "normal text", settings["color_normal"])
        stdscr.addstr(15, x + 28, '0123456789', settings["color_number"])
        stdscr.addstr(15, x + 40, " C.BLOCK", settings["color_comment_block"])

        stdscr.addstr(16, x, "print ", settings["color_entry_command"])
        stdscr.addstr(16, x + 6, '"Entry line"', settings["color_entry_quote"])
        stdscr.addstr(16, x + 18, "; ", settings["color_entry_dim"])
        stdscr.addstr(16, x + 20, "number ", settings["color_entry"])
        stdscr.addstr(16, x + 27, "= ", settings["color_entry_dim"])
        stdscr.addstr(16, x + 29, "100", settings["color_entry_number"])
        stdscr.addstr(16, x + 32, "; ", settings["color_entry_dim"])
        stdscr.addstr(16, x + 34, "def ", settings["color_entry_functions"])
        stdscr.addstr(16, x + 38, "#comment  ", settings["color_entry_comment"])

        stdscr.addstr(17, x, "class", settings["color_entry_class"])
        stdscr.addstr(17, x + 5, ": ", settings["color_entry_dim"])
        stdscr.addstr(17, x + 7, "False", settings["color_entry_negative"])
        stdscr.addstr(17, x + 12, ", ", settings["color_entry_dim"])
        stdscr.addstr(17, x + 14, "True", settings["color_entry_positive"])
        stdscr.addstr(17, x + 18, "; ", settings["color_entry_dim"])
        stdscr.addstr(17, x + 20, "CONSTANT", settings["color_entry_constant"])
        stdscr.addstr(17, x + 28, "; ", settings["color_entry_dim"])
        stdscr.addstr(17, x + 30, '"""Triple Quote"""', settings["color_entry_quote_triple"])

        stdscr.addstr(18, x, "999 ", settings["color_line_numbers"])
        stdscr.addstr(18, x + 6, "....", settings["color_tab_odd"])
        stdscr.addstr(18, x + 10, "....", settings["color_tab_even"])
        stdscr.addstr(18, x + 14, "                                  ", settings["color_background"])

        stdscr.addstr(19, x + 12, ("Press [RETURN] when done!"), settings["color_warning"])
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
            settings[item_list[i_num]] = colors[color_list[c_num]] + style

        elif c == curses.KEY_RIGHT:
            c_num += 1
            if c_num > len(color_list) - 1:
                c_num = len(color_list) - 1
            style_change = False
            settings[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("b"), ord("B")):
            style = curses.A_BOLD
            style_change = True
            settings[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("u"), ord("U")):
            style = curses.A_UNDERLINE
            style_change = True
            settings[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("n"), ord("N")):  # set style to normal
            style = 0
            style_change = True  # no longer needed?
            settings[item_list[i_num]] = colors[color_list[c_num]] + style
        elif c in (ord("o"), ord("O")):
            style = curses.A_BOLD + curses.A_UNDERLINE
            style_change = True
            settings[item_list[i_num]] = colors[color_list[c_num]] + style


def toggle_protection(mytext):
    """Turns protection on/off for inline commands"""
    global program_message
    if "protect with " in mytext:
        args = get_args(mytext, "_foobar", "protect with ", False)
        if args[1].endswith(" "): args[1] = args[1].rstrip()
        if len(args[1]) > 4: args[1] = args[1][0:4]
        if get_confirmation("Protect commands with '%s'? (y/n)" % args[1]):
            settings["protect_string"] = args[1]
            settings["inline_commands"] = "protected"
            program_message = " Commands now protected with '%s' " % args[1]
    else:
        program_message = " Commands protected with '%s' " % settings["protect_string"]
        arg = get_args(mytext)
        if arg == "on":
            settings["inline_commands"] = "protected"
        elif arg == "off":
            settings["inline_commands"] = True
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


def default_colors():
    """set colors to default"""
    global program_message
    program_message = " Colors set to defaults "
    reset_line()
    settings["default_colors"] = True
    color_on(True)


def return_args(temptext):
    """Returns list of args (line numbers, not text)"""
    try:
        the_list = []
        if "," in temptext:
            arg_list = get_args(temptext, " ", ",")
            for i in range(0, len(arg_list)):
                num = int(arg_list[i])
                if num >= 1 and num <= Line.total: the_list.append(num)
        elif "-" in temptext:
            arg_list = get_args(temptext, " ", "-")
            start = int(arg_list[0])
            end = int(arg_list[1])
            for num in range(start, end + 1):
                if num >= 1 and num <= Line.total: the_list.append(num)
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
    Line.db[current_num].x = Line.db[current_num].end_x
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



def toggle_syntax(mytext):
    """Toggle syntax highlighting"""
    global program_message
    program_message = " Syntax highlighting turned off "
    if "off" in mytext or "hide" in mytext:
        settings["syntax_highlighting"] = False
    elif mytext == "syntax" and settings["syntax_highlighting"]:
        settings["syntax_highlighting"] = False
    else:
        settings["syntax_highlighting"] = True
        for lineNum in Line.db.values():
            lineNum.add_syntax()
            i = lineNum.number
            if len(Line.db) + 1 > 800 and i / 10.0 == int(i / 10.0):  # display status message
                status_message("Adding syntax: ", (100 / ((len(Line.db) + 1) * 1.0 / (i + 1))))
        program_message = " Syntax highlighting turned on "
    reset_line()


def toggle_whitespace(mytext):
    """Toggle visible whitespace"""
    global program_message
    program_message = " Visible whitespace turned off "
    if "off" in mytext or "hide" in mytext:
        settings["showSpaces"] = False
    elif mytext == "whitespace" and settings["showSpaces"]:
        settings["showSpaces"] = False
    else:
        settings["showSpaces"] = True
        toggle_syntax("syntax on")  # update syntax to include whitespace
        program_message = " Visible whitespace turned on "
    reset_line()


def toggle_tabs(mytext):
    """Toggle visible tabs"""
    global program_message
    program_message = " Visible tabs turned off "
    if "off" in mytext or "hide" in mytext:
        settings["show_indent"] = False
    elif mytext in ["tab", "tabs"] and settings["show_indent"]:
        settings["show_indent"] = False
    else:
        settings["show_indent"] = True
        toggle_syntax("syntax on")  # update syntax to include tabs
        program_message = " Visible tabs turned on "
    reset_line()


def toggle_live(mytext):
    """Toggle syntax highlighting on entry line"""
    global program_message
    program_message = " Live syntax turned off "
    if "off" in mytext or "hide" in mytext:
        settings["live_syntax"] = False
    elif mytext == "live" and settings["live_syntax"]:
        settings["live_syntax"] = False
    else:
        settings["live_syntax"] = True
        program_message = " Live syntax turned on "
    reset_line()


def toggle_auto(mytext):
    """Toggle feature automation (turns on features based on file type)"""
    global program_message
    program_message = " Auto-settings turned off "
    if "off" in mytext:
        settings["auto"] = False
    elif mytext == "auto" and settings["auto"]:
        settings["auto"] = False
    else:
        settings["auto"] = True
        program_message = " Auto-settings turned on "
    reset_line()


def toggle_entry(mytext):
    """Toggle entry highlighting (colorizes entry line)"""
    global program_message
    program_message = " Entry highlighting turned off "
    if "off" in mytext or "hide" in mytext:
        settings["entry_highlighting"] = False
    elif mytext == "entry" and settings["entry_highlighting"]:
        settings["entry_highlighting"] = False
    else:
        settings["entry_highlighting"] = True
        program_message = " Entry highlighting turned on "
    reset_line()


def toggle_comment_formatting(mytext):
    """Toggle comment formatting (formats/colorizes comments)"""
    global program_message
    program_message = " Comment formatting turned off "
    if "off" in mytext or "hide" in mytext:
        settings["format_comments"] = False
    elif mytext == "formatting" and settings["format_comments"]:
        settings["format_comments"] = False
    else:
        settings["format_comments"] = True
        program_message = " Comment formatting turned on "
    reset_line()
    syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()


def toggle_page_guide(mytext):
    """Toggle page guide (shows page guide)
        Default width of page is 80 characters."""
    global program_message
    program_message = " Page guide turned off "
    if "off" in mytext or "hide" in mytext:
        settings["page_guide"] = False
    elif mytext in ["guide", "pageguide"] and settings["page_guide"]:
        settings["page_guide"] = False
    elif get_args(mytext) not in ["guide", "pageguide"] and "show" not in mytext and "on" not in mytext:
        try:
            num = int(get_args(mytext))
            if num < 1: num = 80
            settings["page_guide"] = num
            program_message = " Page guide - %i characters " % num
        except:
            program_message = " Error occured, nothing changed! "
            reset_line()
            return
    else:
        settings["page_guide"] = 80
        program_message = " Page guide turned on "
    if settings["page_guide"] > WIDTH - 7:
        if WIDTH > 59:
            program_message = " Error, terminal too small for %i character page guide! " % settings["page_guide"]
        else:
            program_message = " Error, page guide not displayed "
        settings["page_guide"] = False
    reset_line()


def show_help():
    """Display help guide"""
    global HELP_GUIDE, current_num, saved_since_edit
    oversized = False

    try:
        if Line.db:
            del Line.db
            Line.db = {}
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
    settings["debug"] = False
    settings["show_indent"] = False
    settings["entry_highlighting"] = False
    settings["syntax_highlighting"] = True
    settings["format_comments"] = True
    settings["live_syntax"] = True
    settings["showSpaces"] = False
    settings["splitscreen"] = False
    Line.locked = True
    status["help"] = True
    saved_since_edit = True
    if WIDTH > 80:
        settings["page_guide"] = 72
    else:
        settings["page_guide"] = False


def show_hide(mytext):
    """Allows show and hide commands to change settings"""
    global program_message
    if "show" in mytext:
        myflag = True
    else:
        myflag = False
    myitem = mytext.split(" ", 1)[1]
    temptext = ""
    if myitem == "syntax":
        settings["syntax_highlighting"] = myflag
        temptext = "Syntax highlighting"
    elif myitem in ("spaces", "whitespace"):
        settings["showSpaces"] = myflag
        temptext = "Whitespace"
    elif myitem in ("tabs", "tab stops", "indent", "indentation"):
        settings["show_indent"] = myflag
        temptext = "Visible tabs"
    elif myitem in ("entry", "entry line"):
        settings["entry_highlighting"] = myflag
        temptext = "Entry line highlighting"
    elif myitem in ("live", "live syntax"):
        settings["live_syntax"] = myflag
        temptext = "Live syntax"
    elif myitem in ("debug", "bugs", "debug mode"):
        settings["debug"] = myflag
        temptext = "Debug mode"
    elif myitem in ("formatting", "comment formatting"):
        settings["format_comments"] = myflag
        temptext = "Comment formatting"
    elif myitem in ("split", "splitscreen", "split screen"):
        settings["splitscreen"] = myflag
        temptext = "Splitscreen"
    elif myitem in ("guide", "pageguide"):
        settings["page_guide"] = myflag
        if settings["page_guide"] == True:
            settings["page_guide"] = 80

        if settings["page_guide"] > WIDTH - 7:
            settings["page_guide"] = False
            if WIDTH > 59:
                program_message = " Error, terminal too small for 80 character page guide! "
            else:
                program_message = " Error, page guide not displayed "
            reset_line()
            return
        else:
            temptext = "Page guide"
    else:
        temptext = "Error, nothing"

    if myflag:
        program_message = " %s turned on " % temptext
    else:
        program_message = " %s turned off " % temptext

    reset_line()
    if settings["syntax_highlighting"]: syntax_visible()
    if settings["splitscreen"] and settings["syntax_highlighting"]: syntax_split_screen()
    if settings["debug"]: debug_visible()


def load_command(mytext):
    """Pre-processes load command"""
    reset_line()
    if " " in mytext and len(mytext) > 5:
        if mytext[:4] == "read":
            read_state = True
        else:
            read_state = False
        load(mytext[5:], read_state)
    else:
        if mytext[:4] == "read":
            read_state = True
        else:
            read_state = False
        if savepath:
            loadfile = display_list(savepath)
        else:
            temp_path = str(os.getcwd() + "/")
            loadfile = display_list(temp_path)
        if loadfile:
            if saved_since_edit:
                load(loadfile, read_state)
            elif Line.total < 2 and not savepath:
                load(loadfile, read_state)
            elif get_confirmation("Load file without saving old? (y/n)"):
                load(loadfile, read_state)


def cut(mytext):
    """Combines copy and delete into one operation"""
    global program_message
    reset_line()
    if mytext.endswith("cut"):
        if get_confirmation("Cut selection? (y/n)"):
            cut(select_items("cut"))
            return
        else:
            program_message = " Cut aborted! "
            return
    temp_text = mytext.replace("cut", "copy")
    copy(temp_text)
    print_header()
    delete_lines(temp_text.replace("copy", "delete"))


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
    for i in range(1, len(Line.db) + 1):
        item_text = Line.db[i].text[Line.db[i].indentation:]
        if item_text.startswith(find_def + "(") or item_text.startswith(find_def + " (") or item_text.startswith(
                find_class + "(") or item_text.startswith(find_class + " ("):
            function_num = i
            mytype = item_text[0:4]
            if mytype == "def ":
                mytype = "FUNCTION"
            if mytype == "clas":
                mytype = "CLASS"
            definition = Line.db[i].text
            myname = item_text.split(" ", 1)[1]
            if "(" in myname:
                myname = myname.split("(")[0]
            temp = Line.db[i].text.replace(':', '')
            if mytype == "FUNCTION":
                temp = temp.replace("def ", "")

            doc_string.append(temp)
            if Line.db[i + 1].text.strip().startswith('"""'):
                start = i + 1
                for n in range(start, len(Line.db) + 1):
                    temp = Line.db[n].text.replace('"""', '')
                    doc_string.append(temp)
                    if Line.db[n].text.endswith('"""'): break

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
        stdscr.addstr(0, 0, (" " * (WIDTH)), settings["color_header"])
        stdscr.addstr(0, 0, (" %s " % (myname)), settings["color_message"])
        stdscr.addstr(0, WIDTH - 11, ("Used: %i" % count).rjust(10), settings["color_header"])
        stdscr.hline(1, 0, curses.ACS_HLINE, WIDTH, settings["color_bar"])

        start = 0
        while True:
            y = 1
            end = min((start + (HEIGHT - 3)), len(doc_string))
            if end < 1: end = 1
            for l in range(start, end):
                doc_string[l] = doc_string[l].rstrip()
                y += 1
                stdscr.addstr(y, 0, (" " * (WIDTH)), settings["color_background"])
                if len(doc_string[l]) > WIDTH:
                    stdscr.addstr(y, 0, doc_string[l][0:WIDTH], settings["color_quote_double"])
                else:
                    stdscr.addstr(y, 0, doc_string[l], settings["color_quote_double"])
            if len(doc_string) < (HEIGHT - 2):
                stdscr.hline(end + 2, 0, curses.ACS_HLINE, WIDTH, settings["color_bar"])
                stdscr.addstr(end + 2, WIDTH, "")  # move cursor

            else:
                stdscr.hline(HEIGHT - 1, 0, curses.ACS_HLINE, WIDTH, settings["color_bar"])
                string = " _Start | _End | Navigate with ARROW keys"
                stdscr.addstr(HEIGHT, 0, (" " * (WIDTH)), settings["color_header"])  # footer
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
    for i in range(1, len(Line.db) + 1):
        mytext = Line.db[i].text
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
        if Line.locked:  # In read only mode, find & mark join forces
            for i in range(1, len(Line.db) + 1):
                Line.db[i].marked = False
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


def mark_items(mytype):
    """Returns string of marked lines.
            Type of command to be executed must be passed

            example: markItems("copy")
    """
    markstring = ""
    word1 = mytype.capitalize()
    if get_confirmation("%s ALL marked lines? (y/n)" % word1):
        for i in range(1, len(Line.db) + 1):
            if Line.db[i].marked:
                num = Line.db[i].number
                markstring += "%i," % num
        if markstring.endswith(","): markstring = markstring[0:-1]
        return ("%s %s" % (mytype, markstring))


def select_items(mytype):
    """Returns string of selected lines.
            Type of command to be executed must be passed

            example: selectItems("copy")
    """
    selectstring = ""
    word1 = mytype.capitalize()
    for i in range(1, len(Line.db) + 1):
        if Line.db[i].selected:
            num = Line.db[i].number
            selectstring += "%i," % num
    if selectstring.endswith(","): selectstring = selectstring[0:-1]
    return ("%s %s" % (mytype, selectstring))


def curses_off():
    """Turns off curses and resets terminal to normal"""
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()  # to turn off curses settings
    curses.endwin()  # restore terminal to original condition


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
        stdscr.addstr(0, 0, temp_lines[-1][0:WIDTH], settings["color_header"])  # Tests output
        if len(temp_lines) > 100:
            stdscr.addstr(0, 0, temp_lines[-100][0:WIDTH], settings["color_header"])  # Tests output
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
            stdscr.addstr(0, 0, string[0:WIDTH], settings["color_header"])  # Tests output
            stdscr.addstr(0, 0, (" " * WIDTH), settings["color_header"])  # clears line
        except:
            get_confirmation("Error, can't read file encoding!", True)
            return False
    return True


def invert_selection():
    """Inverts/reverses current selection"""
    reset_line()
    count = 0
    selected_lines = ""
    for i in range(1, len(Line.db) + 1):
        item = Line.db[i]
        if item.selected:
            count += 1
        else:
            if selected_lines != "": selected_lines += ", "
            selected_lines += str(i)
    if count == Line.total:
        deselect_all()
    elif count == 0:
        select("select all")
    else:
        select("select %s" % selected_lines)


def print_command():
    """New method to print executable commands"""
    if not Line.db[current_num].executable: return
    if len(Line.db[current_num].text) >= WIDTH - 6:
        stdscr.addstr((HEIGHT - 2) - Line.db[current_num].number_of_rows + 1, 6, Line.db[current_num].text.split()[0],
                      settings["color_warning"])  # Prints command only if line oversized
    else:
        stdscr.addstr(HEIGHT - 2, 6, Line.db[current_num].text, settings["color_warning"])  # Prints entire line


def read_mode_entry_window():
    """Enter commands in 'Entry Window'"""
    global reset_needed, program_message
    program_message = ""
    reset_needed = False
    mytext = prompt_user()
    if command_match(mytext, "load", "read", False):
        Line.locked = False
        load_command(mytext)
    elif command_match(mytext, "new", "<@>_foobar_", False):
        new_doc()

    elif command_match(mytext, "find", "mark", False):
        for i in range(1, len(Line.db) + 1):
            Line.db[i].marked = False
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


def save_as(the_path):
    """Forces open 'save_as' dialog and then saves file"""
    global program_message
    reset_line()
    if not the_path:
        the_path = ""
    if savepath:
        part1 = os.path.split(savepath)[0]
        part2 = the_path
        the_path = part1 + "/" + part2
    if "/" not in the_path: the_path = (os.getcwd() + "/" + the_path)
    save_as_path = prompt_user("SAVE FILE AS:", the_path, "(press 'enter' to proceed, UP arrow to cancel)", True)
    if save_as_path:
        save(save_as_path)
    else:
        program_message = " Save aborted! "
