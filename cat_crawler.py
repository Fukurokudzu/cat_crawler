import wmi
import os
import sys
import pickle
# to show time by perf_counter()
from time import perf_counter

AVAILABLE_COMMANDS = {
    "--scan": "scan volume",
    "-l": "print local system drives",
    "-s": "search string in file or folder names in database",
    "-p": "print indexed drives",
    "-r": "remove volume from index database",
    "--purge": "remove database and index files"
}

LOCAL_DB = os.path.dirname(__file__) + "\\local.db"

DRIVE_TYPES = {
        0: "Unknown",
        1: "No Root Directory",
        2: "Removable Disk",
        3: "Local Disk",
        4: "Network Drive",
        5: "Compact Disc",
        6: "RAM Disk"
        }

IDENT = "    "

class Indexed_Volume:
    """
    class for dealing with already indexed volumes
    """

    def __init__(self):
        self.caption = ""
        self.volume_name = ""
        self.file_system = ""
        self.drive_type = DRIVE_TYPES[0]
        self.size = 0
        self.free_size = 0
        self.serial = 0

class Volume:
    """
    class for dealing with system volumes
    """

    def __init__(self, drive):
        self.caption = drive.Caption + "\\"
        self.volume_name = drive.VolumeName
        self.file_system = drive.FileSystem
        self.drive_type = DRIVE_TYPES[drive.DriveType]
        self.size = drive.Size
        self.free_size = drive.FreeSpace
        self.serial = drive.VolumeSerialNumber


def init_drives():
    """
    initialize OS local_drives
    """

    local_drives = []
    c = wmi.WMI()
    for drive in c.Win32_LogicalDisk():
        NewVolume = Volume(drive)
        local_drives.append(NewVolume)
    return local_drives


def show_drives(drives):
    """
    prints all the drives details, including name, type and size (in Gbs)
    """
    for i in range(len(drives)):
        show_drive = drives[i]

        print(f"\n[#{i}] Disk", show_drive.caption)
        print(IDENT + "Name:", show_drive.volume_name)
        print(IDENT + "Size: {0:.2f}".format(
            int(show_drive.size)/1024**3), "Gb")
        print(IDENT + "Free size: {0:.2f}".format(
            int(show_drive.free_size)/1024**3), "Gb")
        print(IDENT + "File system:",show_drive.file_system)
        print(IDENT + "Type:", show_drive.drive_type)
        print(IDENT + "Volume serial:", show_drive.serial)    

def scan_volume(path):
    """
    Creates list of indxfiles for selected path
    """
    list_of_files = []
    list_of_folders = []

    # os.walk returns dirpath, dirnames, filenames
    for root, dirs, indx_files in os.walk(path):
        for folder in dirs:
            list_of_folders.append(os.path.join(root, folder) + "\n")
        for file in indx_files:
            list_of_files.append(os.path.join(root, file) + "\n")

    print(f"\nDisk {path} scanned")
    print(
        f"    {len(list_of_files)} files and {len(list_of_folders)} folders found\n")

    # amount of files and folders found
    return list_of_files, list_of_folders, len(list_of_files), len(list_of_folders)


def write_indexes_to_file(indexes, serial):
    """
    writes list of indexed volume indx_files to .indx file next to the script
    uses volume serial as filename
    """
    index_file_path = os.path.dirname(__file__) + "\\"+serial+".indx"

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

    if (len(sys.argv) == 1):
        print_help(AVAILABLE_COMMANDS)
        return None
    else:
        if sys.argv[1].lower() not in AVAILABLE_COMMANDS.keys():
            print_help(AVAILABLE_COMMANDS)
            quit()

    return sys.argv


def print_help(AVAILABLE_COMMANDS):
    print("Available arguments are:")
    for key, val in AVAILABLE_COMMANDS.items():
        print("    ", key, val)


def search_string(search_query):
    """
    Crawling throughout .indx files in search of user search query
    """
    indx_files = [file for file in os.listdir(
        os.path.dirname(__file__)) if file.endswith('.indx')]
    for indx_file in indx_files:
        file_realpath = os.path.dirname(__file__)+"\\"+indx_file
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
                    len(files_found), "files in", indx_file, "\n")
            elif folders_found:
                print("Found \""+search_query.strip()+"\" in",
                    len(folders_found), "folders in", indx_file, "\n")
            else:
                pass
                # print("Nothing found in", indx_file, "\n")

        # some debugging data in here
        # output_limit = 5  # limits how many search results we print
        # search_results = files_found + folders_found
        # if len(search_results) <= output_limit:
        #     for i in range(len(search_results)):
        #         print(search_results[i])
        # else:
        #     for i in range(output_limit):
        #         print(search_results[i])
        #     # this part is not working for now
        #     print("Too many entries to show here, full output in results.txt\n")

# cat_crawler functions to work with local database
def init_local_db():
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
    database.append(volume)
    with open(LOCAL_DB, 'wb') as db:
       pickle.dump(database, db)
    
    print(f"Volume {volume.serial} added to local database")

def remove_from_db(volume):
    for i in range(len(database)):
        volume_to_remove = database[i]
        if volume_to_remove.serial == volume.serial:
            del_num = i
        else:
            return 1
    
    del database[del_num]
    with open(LOCAL_DB, 'wb') as db:
        pickle.dump(database, db)
        index_file_path = os.path.dirname(__file__) + "\\"+volume_to_remove.serial+".indx"
        try:
            os.remove(index_file_path)
        except:
            print("Can't remove to file",volume_to_remove.serial,".inx quitting")
            quit()
        print("Volume",volume_to_remove.serial,"removed")

def update_db(volume):
    pass


if __name__ == "__main__":

    database = init_local_db()

    if not parse_args():
        quit()
    else:
        command = sys.argv[1].lower()

    local_drives = init_drives()

    if command == "--scan":
        show_drives(local_drives)
        local_drives_amount = len(local_drives)

        while True:
            try:
                local_drive_num = input(
                    f"Choose drive you want to index (should be a number between 0 and {local_drives_amount - 1}, q to quit): ")
                if local_drive_num == 'q':
                    print("Let's quit then!")
                    quit()
                elif int(local_drive_num) in range(local_drives_amount):
                    local_drive_num = int(local_drive_num)
                    break
            except ValueError:
                print(
                    f"Drive index shoud be a number between 0 and {local_drives_amount - 1}")
        
        t1_start = perf_counter()
        volume_to_index = local_drives[local_drive_num]

        for i in range(len(database)):
            tmp_volume = database[i]
            if volume_to_index.serial == tmp_volume.serial:
                answer = input("This volume was already indexed. Update? (y/n) ")
                if answer.lower() not in ['y', 'yes', 'sure']:
                        print("Ok, quitting")
                        quit()
                remove_from_db(volume_to_index)

        print("\nScanning drive", volume_to_index.caption.rstrip("\\")+"...\nthis might take a few minutes")

        list_of_files, list_of_folders, scanned_files_num, scanned_folders_num = scan_volume(volume_to_index.caption)

        write_indexes_to_file(list_of_files, volume_to_index.serial)
        add_to_db(volume_to_index)
        t1_stop = perf_counter()
        print("Scanning finished", "{0:.2f}".format(t1_stop-t1_start), "seconds")

    # printing connected system drives
    elif command == "-l":
        print("\nConnected local_drives:")
        show_drives(local_drives)

    # searching for search string in indexed files and folders
    elif command == "-s":
        if len(sys.argv) <= 2:
            print("Please insert search query after -s")
            quit()
        search_query = ""
        for i in range(2, len(sys.argv)):
            search_query += str(sys.argv[i])+" "
        search_string(search_query)

    elif command == "-p":
        if (len(database)):
            show_drives(database)
        else:
            print("Local database is empty. Scan volumes using --scan")

    elif command == "-r":
        if len(sys.argv) <= 2:
            print("Please insert volume # you want to remove from db after -r")
            quit()
        else: 
            if int(sys.argv[2]) <= len(database):
                volume_to_remove = database[int(sys.argv[2])]
                question = "Are you sure you want to remove volume "+volume_to_remove.volume_name+" "+volume_to_remove.serial+"? (y/n) "
                answer = input(question)
                if answer.lower() in ['y', 'yes', 'sure']:
                    remove_from_db(volume_to_remove)
            else:
                print("Volume number is incorrect, try -p for volumes list")
                quit()
    elif command == "--purge":
        question = "Are you sure you want to remove database and index files?\nThis action will only affect this software database, your files and volumes won't be affected\n(y/n) "
        answer = input(question)
        if answer.lower() in ['y', 'yes', 'sure']:
            for i in range(len(database)):
                remove_from_db(database[i])
            try:
                os.remove(LOCAL_DB)
            except:
                print("Could'nt remove local.db file, quitting")



