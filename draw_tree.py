#modified code from https://github.com/KirillArtemenko

import os
import sys

class bcolors:
    LINE = '\033[37m'
    FOLDER = '\033[94m'
    FILE = '\033[97m'
    ENDC = '\033[0m'


def show_tree(dir, level=0, spacing_after_last_file=True, compact=False, colors=True):
    ignored_levels_count = str(dir).count('/')

    s = {
        'space': u'\u00A0',
        'v_line': u'\u2502',
        'item': u'\u251C',
        'h_line': u'\u252C',
        'item_line': u'\u2500',
        'last_item': u'\u2514',
    }

    files_count = 0
    folders_count = 0

    for dirpath, folders, files in os.walk(dir):
        # ^ this idiom means "we won't be using this value"
        files_count += len(files)
        folders_count += len(folders)

    # first_level_elements = len()

    folders_left = folders_count

    is_folder_last = None

    for dirpath, dirs, files in os.walk(dir):

        path = dirpath.split('/')
        level = len(path) - ignored_levels_count
        total_files = len(files)
        f_c = total_files

        item_line_width = 1 if compact else 2
        space_width = 1 if compact else 3
        inner_space_width = 1 if compact else 2
        name_line_width = 0 if compact else 2

        folder_name = os.path.basename(dirpath)

        # draw line
        line = u''
        if level > 1:
            if is_folder_last:
                line += (
                    s['space'] * space_width
                    + s['v_line' if folders_left > 0 else 'space']
                    + s['space'] * ((level - 1) * item_line_width)
                    + s['last_item']
                )
            else:
                line += (
                    s['space'] * space_width
                    + s['item' if folders_left > 0 else 'last_item']
                    + s['item_line'] * ((level - 1) * item_line_width - 1)
                    + s['item_line'] * name_line_width
                )
        else:
            line += (
                s['item_line'] * name_line_width
            )

        if colors:
            line = bcolors.LINE + line + bcolors.ENDC
            folder_name = bcolors.FOLDER + folder_name + bcolors.ENDC

        sys.stdout.write(line)
        sys.stdout.write(' ' + folder_name + "\n")

        is_folder_last = total_files < 1

        for f in files:
            f_c -= 1

            # draw line
            line = (
                s['space'] * space_width
                + s['v_line' if folders_left > 0 else 'space']
                + s['space'] * (level * inner_space_width)
                + s['item' if f_c > 0 else 'last_item']
                + s['item_line'] * name_line_width
            )

            if colors:
                line = bcolors.LINE + line + bcolors.ENDC
                f = bcolors.FILE + f + bcolors.ENDC

            sys.stdout.write(line)
            sys.stdout.write(' ' + f + "\n")

            # print empty line after last file in folder
            if spacing_after_last_file and f_c < 1:
                empty_line = (
                    s['space'] * space_width
                    + s['v_line' if folders_left > 0 else 'space']
                )
                if colors:
                    empty_line = bcolors.LINE + empty_line + bcolors.ENDC
                sys.stdout.write(empty_line)
                sys.stdout.write("\n")

        folders_left -= 1

# draw a tree
show_tree('./')