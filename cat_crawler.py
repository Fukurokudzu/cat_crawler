import wmi
import os
import sys

available_commands = {
    "--scan": "scan volume",
    "-p": "print system drives",
    "-s": "search string in file or folder names in database",
}


class Volume:
    """
    class for dealing with system volumes
    """

    def __init__(self, settings):
        self.caption = settings['caption']
        self.serial = settings['serial']


def init_drives():
    """
    initialize OS local_drives
    """

    drive_types = {
        0: "Unknown",
        1: "No Root Directory",
        2: "Removable Disk",
        3: "Local Disk",
        4: "Network Drive",
        5: "Compact Disc",
        6: "RAM Disk"
    }

    local_drives = []
    c = wmi.WMI()
    for drive in c.Win32_LogicalDisk():
        this_drive = {}
        this_drive['caption'] = drive.Caption + "\\"
        this_drive['volume_name'] = drive.VolumeName
        this_drive['file_system'] = drive.FileSystem
        this_drive['drive_type'] = drive_types[drive.DriveType]
        this_drive['size'] = drive.Size
        this_drive['free_size'] = drive.FreeSpace
        this_drive['serial'] = drive.VolumeSerialNumber
        local_drives.append(this_drive)
        # print(drive)
    return local_drives


def show_drives(local_drives):
    """
    prints all the local_drives details including name, type and size (in Gbs)
    """
    print("\nConnected local_drives:")
    for i in range(len(local_drives)):
        print(f"\n[#{i}] Disk", local_drives[i]['caption'])
        for key, value in local_drives[i].items():
            if key == 'size':
                print("    ", key, ":", "{0:.2f}".format(
                    int(value)/1024**3), "Gb")
                continue
            if key == 'free_size':
                print("    ", key, ":", "{0:.2f}".format(
                    int(value)/1024**3), "Gb")
                continue
            if key != 'caption':
                print("    ", key, ":", value)


def scan_volume(path):
    """
    Creates list of indxfiles for selected path
    """
    list_of_files = []
    list_of_folders = []

    # os.walk returns dirpath, dirnames, filenames
    for root, dirs, indxfiles in os.walk(path):
        for folder in dirs:
            list_of_folders.append(os.path.join(root, folder) + "\n")
        for file in indx_files:
            list_of_files.append(os.path.join(root, file) + "\n")

    print(f"\nDisk {path} scanned")
    print(
        f"    {len(list_of_files)} files and {len(list_of_folders)} folders found\n")

    # amount of files and folders found
    return list_of_files, list_of_folders, len(list_of_files), len(list_of_folders)


def write_database_to_file(database, serial):
    """
    writes list of indexed volume indxfiles to .indx file next to the script
    uses volume serial as filename
    """
    index_file_path = os.path.dirname(__file__) + "\\"+serial+".indx"

    try:
        with open(index_file_path, "w", encoding="utf-8") as export_file:
            export_file.writelines(database)
    except:
        print("Can't write to file, quitting")
        quit()

    print("File", index_file_path, "created")

    return index_file_path


def parse_args():
    """
    Cheking CLI arguments for available comments we can handle
    """

    if (len(sys.argv) == 1):
        print_help(available_commands)
        return None
    else:
        if sys.argv[1] in available_commands.keys():
            pass
        else:
            print_help(available_commands)
            quit()
    return sys.argv


def print_help(available_commands):
    print("Available arguments are:")
    for key, val in available_commands.items():
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

        print("Found \""+search_query.strip()+"\":",
              len(files_found), "files in", indx_file, "\n")
        print("Found \""+search_query.strip()+"\":",
              len(folders_found), "folders in", indx_file, "\n")

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


if __name__ == "__main__":
    if not parse_args():
        quit()
    else:
        command = sys.argv[1]

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

        volume_to_index = Volume(local_drives[local_drive_num])
        print("\nScanning drive", volume_to_index.caption, "...")

        list_of_files, list_of_folders, scanned_files_num, scanned_folders_num = scan_volume(
            volume_to_index.caption)

        write_database_to_file(list_of_files, volume_to_index.serial)

    # printing connected system drives
    elif command == "-p":
        show_drives(local_drives)
        quit()

    # searching for search string in indexed files and folders
    elif command == "-s":
        if len(sys.argv) <= 2:
            print("Please insert search query after -s")
            quit()
        search_query = ""
        for i in range(2, len(sys.argv)):
            search_query += str(sys.argv[i])+" "
        search_string(search_query)
