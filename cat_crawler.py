import win32api

def init_drives():
    # initialize OS drives
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]
    
    for i in range(len(drives)):
        drives[i] = drives[i].strip('\\')
    return drives

def show_drives():
    drives = init_drives()
    for count, drive in enumerate(drives, start=1):
        print (count, drive)

if __name__ == "__main__":
    
    show_drives()

   