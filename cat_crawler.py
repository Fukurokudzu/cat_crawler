import os
import sys
import pickle
# to show time by perf_counter()
from time import perf_counter
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

IDENT = "\t"


class Volume:
    """
    class to deal with volumes
    """

    def __init__(self, drive):
        self.caption = drive.Caption + os.sep
        self.volume_name = drive.VolumeName
        self.file_system = drive.FileSystem
        self.drive_type = DRIVE_TYPES[drive.DriveType]
        self.size = drive.Size
        self.free_size = drive.FreeSpace
        self.serial = drive.VolumeSerialNumber
        self.description = ""


def get_volume_num_by_serial(serial):
    """
    Finding volume index in database by some serial number
    """
    i = [count for count, volume in enumerate(database)
                            if serial == volume.serial]
    if i:
        return i[0]
    return None


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
    exceptions = ['$RECYCLE.BIN']
    file_realpath = os.path.dirname(__file__) + os.sep \
                                + volume.serial + ".indx"
    with open(file_realpath, "r", encoding="utf-8") as indx_file:
        for line in indx_file.readlines():
            line_type = line.split("*")[0]
            path = line.split("*")[1].split(os.sep)
            if line_type == "d" and len(path) == 3:
                root_folder = path[1]
                if root_folder not in root_folders and \
                        root_folder not in exceptions:
                    root_folders.append(root_folder)
    if root_folders:
        print("Root folders of", volume.volume_name, volume.serial+":")
        for folder in root_folders:
            print(IDENT, folder)


def show_drives(drives):
    """
    prints all the drives details, including name, type and size (in Gbs)
    """
    for count, drive in enumerate(drives):

        print(f"\n[#{count}] Volume {drive.caption}")
        print(IDENT + "Name:", drive.volume_name)
        print(IDENT + "Size: {0:.2f}".format(
            int(drive.size)/1024**3), "Gb")
        print(IDENT + "Free size: {0:.2f}".format(
            int(drive.free_size)/1024**3), "Gb")
        print(IDENT + "File system:", drive.file_system)
        print(IDENT + "Type:", drive.drive_type)
        print(IDENT + "Volume serial:", drive.serial)
        if drive.description:
            print(IDENT + "Description:", drive.description)


def scan_volume(path):
    """
    Creates list of indxfiles for selected path
    """
    list_of_files = []
    list_of_folders = []

    # os.walk returns dirpath, dirnames, filenames
    for root, dirs, indx_files in os.walk(path):
        for folder in dirs:
            list_of_folders.append("d*" + os.path.join(root, folder) + "\n")
        for file in indx_files:
            list_of_files.append("f*" + os.path.join(root, file) + "\n")

    print(f"\nDisk {path} scanned")
    print(
        f"    {len(list_of_files)} files and {len(list_of_folders)} \
        folders found\n")

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
        quit()

    print("File", index_file_path, "created")

    return 0


def parse_args():
    """
    Cheking CLI arguments for available comments we can handle
    """

    parser = argparse.ArgumentParser()
 
    subparsers = parser.add_subparsers(help="Commands")

    parser_1 = subparsers.add_parser("print", help="print indexed volumes")
    parser_1.set_defaults(func=print_drives)

    parser2 = subparsers.add_parser("local", help="print local system drives")
    parser2.set_defaults(func=show_local)

    parser3 = subparsers.add_parser("scan",
        help="indexing files and folder for selected volume")
    parser3.set_defaults(func=scan)

    parser4 = subparsers.add_parser("search",
        help="search string in file or folder names in database",)
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
                        choices=range(0, len(database))
                        )
    parser6.set_defaults(func=remove_indexed_volume)

    return parser.parse_args()


def search_string(args):
    """
    Crawling throughout .indx files in search of user search query
    """
    search_query = " ".join(args.search_string)
    for volume in database:
        file_realpath = os.path.join(os.path.dirname(__file__),
                        volume.serial + '.indx')
        with open(file_realpath, "r", encoding="utf-8") as search_list:
            files_found = []
            folders_found = []
            current_dir = ""
            for line in search_list.readlines():
                if search_query.strip() in line:
                    folder_found, file_found = os.path.split(line)
                    if search_query.strip() in file_found:
                        files_found.append(line)
                    if search_query.strip() in folder_found:
                        if folder_found != current_dir:
                            current_dir = folder_found
                            folders_found.append(folder_found)
            if files_found:
                print("Found \""+search_query.strip()+"\" in",
                      len(files_found), "files in", volume.serial, "\n")
            elif folders_found:
                print("Found \""+search_query.strip()+"\" in",
                      len(folders_found), "folders in", volume.serial, "\n")

        if len(folders_found) or len(files_found):
            show_root_folders(volume)
        else:
            print("Nothing found in volume", volume.serial)


# cat_crawler functions to work with local database
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
            quit()
        print("Volume", volume.serial, "removed")
    


def update_db():
    with open(LOCAL_DB, 'wb') as db:
        pickle.dump(database, db)


def print_drives(args):
    if (len(database)):
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
                f"Choose drive you want to index"
                f"(should be a number between 0"
                f"and {local_drives_amount - 1}, q to quit): "
            )
            local_drive_num = input(message)
            if local_drive_num == 'q':
                print("Let's quit then!")
                quit()
            elif int(local_drive_num) in range(local_drives_amount):
                local_drive_num = int(local_drive_num)
                break
        except ValueError:
            print(f"Drive index shoud be a number"
                    f"between 0 and {local_drives_amount - 1}")

    t1_start = perf_counter()
    volume_to_index = local_drives[local_drive_num]

    if get_volume_num_by_serial(volume_to_index.serial) != None:
        answer = input("This volume was already indexed. Update? (y/n) ")
        if answer.lower() not in ['y', 'yes', 'sure']:
            print("Ok, quitting")
            quit()
        remove_from_db(volume_to_index)

    print("\nScanning drive", volume_to_index.caption.rstrip(
        os.sep)+"...\nthis might take a few minutes")

    list_of_files, list_of_folders = scan_volume(
        volume_to_index.caption)

    write_indexes_to_file(
        list_of_folders + list_of_files, volume_to_index.serial)
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
        update_db()
    else:
        print("Ok, quitting")


def purge(args):
    question = "Are you sure you want to remove "\
            "database and index files?\nThis "\
            "action will only affect this software database, "\
            "your files and volumes won't be affected\n(y/n) "
    answer = input(question)
    if answer.lower() in ['y', 'yes', 'sure']:
        for volume_to_remove in database:
            remove_from_db(volume_to_remove)
        try:
            os.remove(LOCAL_DB)
        except:
            print("Could'nt remove local.db file, quitting")

def remove_indexed_volume(args):

    #     print("Please insert volume # after -r (use -p to to get volumes list)")
    #     print("Volume number is incorrect, use -p to get volumes list")
    volume_to_remove = database[args.volume_num]
    question = "Are you sure you want to remove volume " + \
        volume_to_remove.volume_name+" " + \
        volume_to_remove.serial+"? (y/n) "
    answer = input(question)
    if answer.lower() in ['y', 'yes', 'sure']:
        remove_from_db(volume_to_remove)


if __name__ == "__main__":

    database = init_local_db()
    args = parse_args()
    args.func(args)
