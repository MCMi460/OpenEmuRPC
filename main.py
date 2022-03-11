from sys import platform, exit # This gives us our current OS' information

# Make sure platform is MacOS
if platform.startswith("darwin") != True:
    exit(f"There is not currently a {platform} version supported, please use a different application.")
else:
    from rumps import App, clicked, alert, notification, quit_application # This module adds menu bar support
    from threading import Thread # This allows us to run multiple blocking processes at once
    from time import sleep, time # This lets us get the exact time stamp as well as wait time
    from pypresence import Presence # This is what connects us to Discord and lets us change our status
    from AppKit import NSWorkspace # Allows us to check if OpenEmu is running
    import Quartz # Very important for us in order to get windows running with OpenEmu
    import sqlite3 # Useful for receiving artwork data
    import os # Arguably one of the most useful default Python libraries

# Set default appname
appName = "OpenEmu"

# Set Discord Rich Presence ID
rpc = Presence('901628121214779412')

from os.path import expanduser, exists # Get home directory path
from datetime import datetime # Lets us get current time and date

path = expanduser("~/Library/Application Support/OpenEmuRPC")

emupath = expanduser("~/Library/Application Support/OpenEmu/Game Library")

# Set default function for logging errors
def log_error(error):
    print(error)
    while True:
        try:
            with open(f'{path}/error.txt',"a") as append:
                append.write(f'[{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}] {error}\n')
            break
        except:
            from os import mkdir # Create the directory
            mkdir(path)
            continue

# Checks for screen recording permissions
def check_permissions():
    return Quartz.CGPreflightScreenCaptureAccess()

# Requests screen recording permissions
def request_permissions():
    Quartz.CGRequestScreenCaptureAccess()

# Check first run
def check_run():
    return exists(f'{path}/error.txt')

# Connect to Discord Rich Presence via function
def connect():
    # Set fails variable to 0
    fails = 0

    while True:
        # Attempt to connect to Discord. Will wait until it connects
        try:
            rpc.connect()
            break
        except Exception as e:
            sleep(0.1)
            fails += 1
            if fails > 500:
                # If program fails 500 consecutive times in a row to connect, then send a notification with the exception
                notification("Error in OpenEmuRPC", "Make an issue if error persists", f"\"{e}\"")
                log_error(e)
                exit(f"Error, failed after 500 attempts\n\"{e}\"")
            continue

# Run function
connect()

try:
    # Sometimes PyPresence returns a Client ID error even if we already connected, so this will try to connect again
    rpc.connect()
except:
    exit("Failed to connect")

# Get screen recording permissions
if not check_run():
    if not check_permissions():
        request_permissions()
        error = 'Failed to receive Screen Recording Permissions.'
        log_error(error)
        notification('Launch Error','',error)

# Checks if OpenEmu is running
def is_running():
    apps = NSWorkspace.sharedWorkspace().launchedApplications()
    for app in apps:
        if app['NSApplicationName'] == appName:
            return True
    return False

# Returns all windows for applications named "OpenEmu"
def get_windows():
    response = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements|Quartz.kCGWindowListOptionOnScreenOnly,Quartz.kCGNullWindowID)
    windows = []
    for window in response:
        if window[Quartz.kCGWindowOwnerName] == appName:
            windows.append(window.get(Quartz.kCGWindowName, '<no name>'))
    while '' in windows:
        windows.remove('')
    return windows

# Gets artwork for a particular game using OpenEmu's Library database
def get_artwork(gametitle:str):
    try:
        # Connect to OpenEmu's library database
        con = sqlite3.connect(os.path.join(emupath, "Library.storedata"))
        cursor = con.cursor()

        # Get sources from image db
        cursor.execute("SELECT ZSOURCE FROM ZIMAGE")
        art = [ i[0] for i in cursor.fetchall() ]
        cursor.execute("SELECT Z_PK FROM ZIMAGE")
        zsource = [ i[0] for i in cursor.fetchall() ]
        art = [ (zsource[i],art[i]) for i in range(len(art)) ]
        cursor.execute("SELECT ZGAMETITLE FROM ZGAME")
        games = [ i[0] for i in cursor.fetchall() ]
        cursor.execute("SELECT Z_PK FROM ZROM")
        zpk = [ i[0] for i in cursor.fetchall() ]
        games = [ [zpk[i],games[i]] for i in range(len(games)) ]
        con.close()

        # Reorganize list in case of irregular OpenEmu shennanigans
        i = 0
        for e in games:
            if not e[1]:
                games.remove(e)
                h = i
                for n in range(i,len(games)):
                    h += 1
                    games[n][0] = h
                i -= 1
            i += 1

        # Find game in sources
        for i in games:
            if not i[1]: # Prevent irregular games from prematurely ending the recursion
                continue
            if gametitle in i[1]:
                url = next(n[1] for n in art if n[0] == i[0])
                return url
        return None
    except: # On possible failure, just return None
        return None

# Contains logic code that calls functions to grab data using Apple Script and updates the RPC controller with the data
def update():
    if not is_running():
        rpc.clear()
        return
    # Grab windows
    windows = get_windows()
    menus = False
    image = 'main'
    for i in ('Library','Gameplay','Controls','Cores','System Files','Shader Parameters'):
        if i in windows:
            menus = i
            windows.remove(i)
    for i in ('File','Edit','View','Window','Help'):
        if i in windows:
            windows.remove(i)
    if windows == [f'{appName}'] or windows == []:
        status = 0
        details = 'Idly in menus...'
    else:
        status = 1
        try: windows.remove(f'{appName}')
        except: pass
        details = f'Playing {windows[0]}'
        if len(windows) > 1:
            status = 2
            details = f'Playing {", ".join(windows)}'
        else:
            art = get_artwork(windows[0])
            if art:
                image = art
    buttons = [{"label": f"See {appName}", "url": "https://openemu.org/"},]
    if status > 0:
        global games
        if games != windows:
            global start
            start = round(time())
            games = windows
    if menus and status > 0:
        details = f'In {menus} of ' + details[8:]
    if status == 0:
        rpc.update(details=details,large_image=image,large_text=appName,buttons=buttons)
    elif status == 1:
        rpc.update(details=details,large_image=image,large_text=appName,start=start,buttons=buttons)
    elif status == 2:
        rpc.update(details=details,large_image=image,large_text=appName,start=start,buttons=buttons)

# Run update loop on a separate thread so the menu bar app can run on the main thread
class BackgroundUpdate(Thread):
    def run(self,*args,**kwargs):
        global call_update
        # Set fails variable to 0
        fails = 0
        # Loop for the rest of the runtime
        while True:
            # Only run when app is activated
            if activated:
                # Call update function
                try:
                    update()
                    fails = 0
                except Exception as e:
                    notification("Error in OpenEmuRPC", "Make an issue if error persists", f"\"{e}\"")
                    log_error(e)
                    fails += 1
                    if fails > 5:
                        print(f"Error, failed after 5 attempts\n\"{e}\"")
                        quit_application()
                        exit()
                        # Here, we just use everything we can to get the application to stop running!

                # Wait one second
                sleep(1)

# Make sure it runs on start
activated = True
# Set variables
games = []
start = 0

# Grab class and start it
background_update = BackgroundUpdate()
background_update.start()

# Define menu bar object and run it
class RPCApp(App):
    def __init__(self):
        super(RPCApp, self).__init__("OpenEmuRPC",title="🎮")
        self.menu = ["Disable", "Reconnect"]
    # Make an activate button
    @clicked("Disable")
    def button(self, sender):
        global activated
        activated = not activated
        global call_update
        if sender.title == "Disable":
            sender.title = "Enable"
            rpc.clear()
        else:
            sender.title = "Disable"
    # Make a reconnect button
    @clicked("Reconnect")
    def reconnect(self, _):
        # Attempt to connect to Discord, and if failed, it will output an alert with the exception
        try:
            rpc.clear()
        except:
            pass
        try:
            connect()
            alert("Connected to Discord!\n(You may have to restart Discord)")
        except Exception as e:
            alert(f"Failed to connect:\n\"{e}\"")
            log_error(e)

# Make sure process is the main script and run status bar app
if __name__ == "__main__":
    RPCApp().run()
