import wmi
import os


class Volume:
    # class for dealing with system volumes
    def __init__(self, settings):
        self.caption = settings['caption']

def init_drives():
    # initialize OS local_drives

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
        this_drive['volume_serial'] = drive.VolumeSerialNumber
        local_drives.append(this_drive)
        # print(drive)
    return local_drives


def show_drives(local_drives):
    # prints all the local_drives details including name, type and size
    # TODO Volume Size in Gb
    print("\nConnected local_drives:")
    for i in range(len(local_drives)):
        print(f"\n[#{i}] Disk", local_drives[i]['caption'])
        for key, value in local_drives[i].items():
            if key == 'size':
                    print("    ", key, ":", "{0:.2f}".format(int(value)/1024**3), "Gb")
                    continue
            if key == 'free_size':
                    print("    ", key, ":", "{0:.2f}".format(int(value)/1024**3), "Gb")
                    continue
            if key != 'caption':
                print("    ", key, ":", value)
                

def scan_folder(path):
    list_of_files = []
    list_of_folders = []
    
    for root, dirs, files in os.walk(path):
        for folder in dirs:
            list_of_folders.append(os.path.join(root, folder))
        for file in files:
            list_of_files.append(os.path.join(root,file))
    
    print(f"\nDisk {path} scanned")
    print(f"    {len(list_of_files)} files in {len(list_of_folders)} folders found\n")

    return len(list_of_files), len(list_of_folders) #amount of files found

if __name__ == "__main__":
    local_drives = init_drives()
    show_drives(local_drives)
    local_drives_amount = len(local_drives)

    while True:
        try:
            local_drive_num = input(f"Choose drive you want to index (should be a number between 0 and {local_drives_amount - 1}, q to quit): ")
            if local_drive_num == 'q':
                print("Let's quit then!")
                quit()
            elif int(local_drive_num) in range(local_drives_amount):
                local_drive_num = int(local_drive_num)
                break
        except ValueError:
            print(f"Drive index shoud be a number between 0 and {local_drives_amount - 1}")

    volume_to_index = Volume(local_drives[local_drive_num])
    print("\nScanning drive", volume_to_index.caption,"...")
    scan_folder(volume_to_index.caption)
    
