import wmi

def init_drives():
    # initialize OS drives

    drive_types = {
        0 : "Unknown",
        1 : "No Root Directory",
        2 : "Removable Disk",
        3 : "Local Disk",
        4 : "Network Drive",
        5 : "Compact Disc",
        6 : "RAM Disk"
        }
    drives = []
    c = wmi.WMI()
    for drive in c.Win32_LogicalDisk():
        this_drive = {}
        this_drive['cation'] = drive.Caption
        this_drive['volume_name'] = drive.VolumeName
        this_drive['file_system'] = drive.FileSystem
        this_drive['drive_type'] = drive_types[drive.DriveType]
        this_drive['volume_serial'] = drive.VolumeSerialNumber
        drives.append(this_drive)
    return drives

def show_drives(drives):
    # prints all the drives details including name, type and size
    # TO DO - some nice formating here
    for i in range(len(drives)):
        print(drives[i], sep = "\n")

if __name__ == "__main__":
    drives = init_drives()
    show_drives(drives)