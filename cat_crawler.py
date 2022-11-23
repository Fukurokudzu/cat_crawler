import os
import sys
import pickle
from time import perf_counter, sleep
from datetime import datetime
import argparse
import wmi

LOCAL_DB = os.path.dirname(__file__) + os.sep + "local.db"

DRIVE_TYPES = {
    0: "Unknown",
    1: "No Root Directory",
    2: "Removable Disk",
    3: "Local Disk",
    4: "Network Drive",
    5: "Compact Disc",
    6: "RAM Disk"
}

INDENT = "\t"
SHORT_SEARCH_RESULTS_LIMIT = 5
LONG_SEARCH_RESULTS_LIMIT = 50
EXCEPTIONS = ['$RECYCLE.BIN']


class Volume:
    """
    class to deal with volumes
    """

    def __init__(self, drive):
        self.caption = drive.Caption + os.sep
        self.name = drive.VolumeName
        self.file_system = drive.FileSystem
        self.drive_type = DRIVE_TYPES[drive.DriveType]
        self.size = drive.Size
        self.free_size = drive.FreeSpace
        self.serial = drive.VolumeSerialNumber
        self.description = ""
        self.indexed = ""


def get_volume_num_by_serial(serial):
    """
    Finding volume index in database by some serial number
    """
    i = [count for count, volume in enumerate(database)
         if serial == volume.serial]
    return i[0] if i else None


def init_drives():
    """
    initialize OS local_drives
    """

    local_volumes = wmi.WMI()
    return [Volume(drive) for drive in local_volumes.Win32_LogicalDisk()]


def show_root_folders(volume):
    """
    Showing root folders for selected volume
    """
    root_folders = []
    file_realpath = os.path.dirname(__file__) + os.sep \
        + volume.serial + ".indx"
    with open(file_realpath, "r", encoding="utf-8") as indx_file:
        for line in indx_file.readlines():
            if find_root_folders(line, root_folders) is not None:
                root_folders.append(find_root_folders(line, root_folders))

    if root_folders:
        print("\nRoot folders of", volume.name, volume.serial + ":")
        for folder in root_folders:
            print(INDENT, folder)


def find_root_folders(line, root_folders):
    line_type, path = parse_indx_line(line)
    path_segments = path.split(os.sep)
    if line_type == "d" and len(path_segments) == 2:
        if path not in root_folders and \
                path not in EXCEPTIONS:
            return path


def show_drives(drives):
    """
    prints all the drives details, including name, type and size (in Gbs)
    """
    for count, drive in enumerate(drives):
        print(f"\n[#{count}] Volume {drive.caption}")
        if drive.indexed:
            print(INDENT + "Indexed on:", drive.indexed)
        print(INDENT + "Name:", drive.name)
        print(INDENT + "Size: {0:.2f}".format(
            int(drive.size) / 1024**3), "Gb")
        print(INDENT + "Free size: {0:.2f}".format(
            int(drive.free_size) / 1024**3), "Gb")
        print(INDENT + "File system:", drive.file_system)
        print(INDENT + "Type:", drive.drive_type)
        print(INDENT + "Volume serial:", drive.serial)
        if drive.description:
            print(INDENT + "Description:", drive.description)


def show_volume(volume):
    """
    prints volume details, including name, type and size (in Gbs)
    """
    print(f"\nVolume {volume.caption}")
    if volume.indexed:
        print(INDENT + "Indexed on:", volume.indexed)
    print(INDENT + "Name:", volume.name)
    print(INDENT + "Size: {0:.2f}".format(
        int(volume.size) / 1024**3), "Gb")
    print(INDENT + "Free size: {0:.2f}".format(
        int(volume.free_size) / 1024**3), "Gb")
    print(INDENT + "File system:", volume.file_system)
    print(INDENT + "Type:", volume.drive_type)
    print(INDENT + "Volume serial:", volume.serial)
    if volume.description:
        print(INDENT + "Description:", volume.description)

    show_root_folders(volume)


def scan_volume(path):
    """
    Creates list of indxfiles for selected path
    """
    list_of_files = []
    list_of_folders = []

    # os.walk returns dirpath, dirnames, filenames
    for root, dirs, indx_files in os.walk(path):
        for file in indx_files:
            if file not in EXCEPTIONS:
                list_of_files.append("f*" + os.path.join(root, file) + "\n")

        for folder in dirs:
            if folder not in EXCEPTIONS:
                list_of_folders.append("d*"
                                       + os.path.join(root, folder) + "\n")

    print(f"\nDisk {path} scanned")
    print(f"{INDENT}{len(list_of_files)} files and "
          f"{len(list_of_folders)} folders found\n")

    # amount of files and folders found
    return list_of_files, list_of_folders


def write_indexes_to_file(indexes, serial):
    """
    writes list of indexed volume indx_files to .indx file next to the script
    uses volume serial as filename
    """
    index_file_path = os.path.dirname(__file__) + os.sep + serial + ".indx"

    try:
        with open(index_file_path, "w", encoding="utf-8") as export_file:
            export_file.writelines(indexes)
    except:
        print("Can't write to file, quitting")
        sys.exit()

    print("File", index_file_path, "created")

    return 0


def parse_args():
    """
    Cheking CLI arguments for available comments we can handle
    """

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Commands")

    parser1 = subparsers.add_parser("print", help="print indexed volumes")
    parser1.set_defaults(func=print_drives)

    choice = range(0, len(database)) if len(database) > 1 else ['0']

    parser1.add_argument("indexed_volume_num",
                         help="number of indexed volume",
                         type=int,
                         choices=choice,
                         nargs='?'
                         )

    parser2 = subparsers.add_parser("local", help="print local system drives")
    parser2.set_defaults(func=show_local)

    parser3 = subparsers.add_parser("scan",
                                    help="indexing files and folder for \
                                    selected volume")
    parser3.set_defaults(func=scan)

    parser4 = subparsers.add_parser("search",
                                    help="search string in file or folder \
                                    names in database",)
    parser4.add_argument("search_string", help="search request", nargs="+")
    parser4.set_defaults(func=search_string)

    parser5 = subparsers.add_parser("purge",
                                    help="remove database and index files",)
    parser5.set_defaults(func=purge)

    parser6 = subparsers.add_parser("remove",
                                    help="removes volume from index database",)
    parser6.add_argument("volume_num",
                         help="number of indexed volume",
                         type=int,
                         choices=range(0, len(database)),
                         nargs="?",
                         )
    parser6.set_defaults(func=remove_indexed_volume)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()

    return parser.parse_args()


def parse_indx_line(line):
    path = line.split("*")[1].strip()
    line_type = line.split("*")[0]
    return line_type, path


def parse_results_line(line):
    path = line.split("*")[1].strip()
    serial = line.split("*")[0]
    return serial, path


def search_string(args):
    """
    Crawling throughout .indx files in search of user search query
    """
    search_query = " ".join(args.search_string)
    volumes_nums_found = []
    results = []
    results_count = {}
    for count, volume in enumerate(database):
        file_realpath = os.path.join(os.path.dirname(__file__),
                                     volume.serial + '.indx')
        with open(file_realpath, "r", encoding="utf-8") as search_list:
            files_found = []
            dirs_found = []
            for line in search_list.readlines():
                if search_query in line:
                    line_type, path = parse_indx_line(line)
                    tmp_path = path.split(os.sep)
                    time_to_stop = None
                    for p in tmp_path:
                        if p in EXCEPTIONS:
                            time_to_stop = 1
                    if time_to_stop:
                        break
                    if line_type == "f":
                        files_found.append(volume.serial + "*" + path)
                    elif line_type == "d":
                        dirs_found.append(volume.serial + "*" + path)

            if files_found or dirs_found:
                results_count[volume.serial] = [len(files_found),
                                                len(dirs_found)]
                print(f"\nVOLUME #{count}: {volume.name} {volume.serial}")
                volumes_nums_found.append(count)

            if dirs_found:
                results.append(dirs_found)
                print("\n", INDENT, "Found \""+search_query+"\" in",
                      len(dirs_found), "folders")

                for j in dirs_found[:SHORT_SEARCH_RESULTS_LIMIT]:
                    print(INDENT, parse_results_line(j)[1])
                if len(dirs_found) > SHORT_SEARCH_RESULTS_LIMIT:
                    print(INDENT, "... and",
                          len(dirs_found)-SHORT_SEARCH_RESULTS_LIMIT, "more")

            if files_found:
                results.append(files_found)
                print("\n", INDENT, "Found \""+search_query+"\" in",
                      len(files_found), "files")
                for i in files_found[:SHORT_SEARCH_RESULTS_LIMIT]:
                    print(INDENT, parse_results_line(i)[1])
                if len(files_found) > SHORT_SEARCH_RESULTS_LIMIT:
                    print(INDENT, "... and",
                          len(files_found)-SHORT_SEARCH_RESULTS_LIMIT-1,
                          "more")

    if volumes_nums_found:
        while True:
            try:
                message = (
                        f"\nChoose volume to see results "
                        f"(one of {volumes_nums_found}, q to quit): ")
                volume_num = input(message)
                if volume_num == 'q':
                    print("Let's quit then!")
                    sys.exit()
                elif int(volume_num) in volumes_nums_found:
                    volume_num = int(volume_num)
                    break
            except ValueError:
                print(f"Volume index shoud be in {volumes_nums_found}")

        n_results = normalize_search_results(database[volume_num].serial,
                                             results)

        files_found, dirs_found = results_count[database[volume_num].serial]
        if files_found < LONG_SEARCH_RESULTS_LIMIT \
                and dirs_found < LONG_SEARCH_RESULTS_LIMIT:
            print("You were looking for \"", search_query, "\"")
            show_volume(database[volume_num])
            print("\nFiles and folders found on this volume:")
            for line in n_results:
                print(INDENT + line)
        else:
            now = datetime.now()
            dt = now.strftime("%d%m%Y_%H%M%S")
            file_path = "search_" + dt + ".txt"
            file_realpath = os.path.dirname(__file__) + os.sep + \
                "search_" + dt + ".txt"
            old_stdout = sys.stdout
            print("Too many results found")
            sleep(1)
            print(file_realpath, "created")
            sleep(1)
            print("Opening file in text editor...")
            sleep(1)
            try:
                sys.stdout = open(file_path, 'w', encoding="utf-8")
                print("You were looking for \"", search_query, "\"")
                show_volume(database[volume_num])
                print("\nFiles and folders found on this volume:")
                for items in n_results:
                    sys.stdout.writelines(items + "\n")
                sys.stdout.close()
                sys.stdout = old_stdout
                os.system(file_realpath)
            except:
                print("Couln't create search results file")

    if not volumes_nums_found:
        print("Nothing found in local database")


def normalize_search_results(serial, results):
    n_list = []
    for line in results:
        for i in line:
            res_serial, path = parse_results_line(i)
            if res_serial == serial:
                n_list.append(path)
    return n_list


def init_local_db():
    """
    importing database from local file, or creating one if it's missing
    """
    database = []
    if os.path.exists(LOCAL_DB):
        with open(LOCAL_DB, 'rb') as db:
            try:
                db_data = pickle.load(db)
                for obj in db_data:
                    database.append(obj)
            except:
                pass
    else:
        new_file = open(LOCAL_DB, 'x')
        new_file.close()
    return database


def add_to_db(volume):
    """
    adding volume to local database
    """
    database.append(volume)
    with open(LOCAL_DB, 'wb') as db:
        pickle.dump(database, db)

    print(f"Volume {volume.serial} added to local database")


def remove_from_db(volume):
    del database[get_volume_num_by_serial(volume.serial)]
    with open(LOCAL_DB, 'wb') as db:
        pickle.dump(database, db)
        index_file_path = os.path.dirname(
            __file__) + os.sep + volume.serial+".indx"
        try:
            os.remove(index_file_path)
        except FileNotFoundError:
            print("Can't remove to file",
                  volume.serial, ".inx quitting")
            sys.exit()
        print("Volume", volume.serial, "removed")


def update_db(database):
    with open(LOCAL_DB, 'wb') as db:
        pickle.dump(database, db)


def print_drives(args):
    if (len(database)):
        if args.indexed_volume_num is not None:
            show_volume(database[args.indexed_volume_num])
        else:
            print("Indexed volumes in database:")
            show_drives(database)
    else:
        print("Local database is empty. Scan volumes using \"scan\"")


# printing connected system drives
def show_local(args):
    local_drives = init_drives()
    print("\nConnected local_drives:")
    show_drives(local_drives)


def scan(args):
    """
    scans local drives and creates index file for selected volume
    """
    local_drives = init_drives()
    show_drives(local_drives)
    local_drives_amount = len(local_drives)

    while True:
        try:
            message = (
                f"Choose drive you want to index "
                f"(should be a number between 0 "
                f"and {local_drives_amount - 1}, q to quit): "
            )
            local_drive_num = input(message)
            if local_drive_num == 'q':
                print("Let's quit then!")
                sys.exit()
            elif int(local_drive_num) in range(local_drives_amount):
                local_drive_num = int(local_drive_num)
                break
        except ValueError:
            print(f"Drive index shoud be a number"
                  f"between 0 and {local_drives_amount - 1}")

    t1_start = perf_counter()
    volume_to_index = local_drives[local_drive_num]

    if get_volume_num_by_serial(volume_to_index.serial) is not None:
        answer = input("This volume was already indexed. Update? (y/n) ")
        if answer.lower() not in ['y', 'yes', 'sure']:
            print("Ok, quitting")
            sys.exit()
        remove_from_db(volume_to_index)

    print("\nScanning drive", volume_to_index.caption.rstrip(
        os.sep)+"...\nthis might take a few minutes")

    list_of_files, list_of_folders = scan_volume(
        volume_to_index.caption)

    write_indexes_to_file(
        list_of_folders + list_of_files, volume_to_index.serial)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    volume_to_index.indexed = dt_string
    add_to_db(volume_to_index)
    t1_stop = perf_counter()
    print("Scanning finished", "{0:.2f}".format(
        t1_stop-t1_start), "seconds")

    # refreshing database data
    database = init_local_db()
    answer = input(
        "You can add description for this volume (or q to quit): ")
    if answer and answer.lower() not in "q":
        database[get_volume_num_by_serial(
            volume_to_index.serial)].description = str(answer)
        update_db(database)
    else:
        print("Ok, quitting")


def purge(args):
    question = "Are you sure you want to remove "\
            "database and index files?\nThis "\
            "action will only affect this software database, "\
            "your files and volumes won't be affected\n(y/n) "
    answer = input(question)
    if answer.lower() in ['y', 'yes', 'sure']:
        tmp_database = database.copy()
        for volume_to_remove in tmp_database:
            remove_from_db(volume_to_remove)
        try:
            os.remove(LOCAL_DB)
        except:
            print("Could'nt remove local.db file, quitting")


def remove_indexed_volume(args):
    if args.volume_num is not None:
        volume_to_remove = database[args.volume_num]
        ask_to_remove(volume_to_remove)
    else:
        show_drives(database)
        message = (
                f"Choose volume you want to remove "
                f"(should be a number between 0 "
                f"and {len(database) - 1}, q to quit): ")
        a = input(message)
        ask_to_remove(database[int(a)])


def ask_to_remove(volume):
    question = "Are you sure you want to remove volume " + \
            volume.name+" " + \
            volume.serial+"? (y/n) "
    answer = input(question)
    if answer.lower() in ['y', 'yes', 'sure']:
        remove_from_db(volume)


if __name__ == "__main__":

    database = init_local_db()
    args = parse_args()
    args.func(args)
