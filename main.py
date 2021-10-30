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

# Set default appname
appName = "OpenEmu"

# Set Discord Rich Presence ID
rpc = Presence('901628121214779412')

from os.path import expanduser # Get home directory path
from datetime import datetime # Lets us get current time and date

path = expanduser("~/Library/Application Support/OpenEmuRPC")

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

connect()

try:
    # Sometimes PyPresence returns a Client ID error even if we already connected, so this will try to connect again
    rpc.connect()
except:
    exit("Failed to connect")

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

# Contains logic code that calls functions to grab data using Apple Script and updates the RPC controller with the data
def update():
    if not is_running():
        rpc.clear()
        return
    # Grab windows
    windows = get_windows()
    if windows == [f'{appName}'] or windows == []:
        status = 0
    else:
        status = 1
        try: windows.remove(f'{appName}')
        except: pass
        if len(windows) > 1:
            status = 2
    buttons = []
    buttons.append({"label": "See OpenEmu", "url": "https://openemu.org/"})
    if status > 0:
        global games
        if games != windows:
            global start
            start = round(time())
            games = windows
    if status == 1:
        rpc.update(details=f'Playing {windows[0]}',large_image='main',large_text='OpenEmu',start=start,buttons=buttons)
    elif status == 2:
        rpc.update(details=f'Playing {", ".join(windows)}',large_image='main',large_text='OpenEmu',start=start,buttons=buttons)
    elif status == 0:
        rpc.update(details=f'Idly in menus...',large_image='main',large_text='OpenEmu',buttons=buttons)

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
