import threading, time, sqlite3, os, sys, datetime
if not sys.platform.startswith('darwin'):
    sys.exit('OpenEmu is a macOS exclusive application.')

import rumps, pypresence, Quartz, AppKit

# Set default appname
appName = 'OpenEmu'

path = os.path.expanduser('~/Library/Application Support/OpenEmuRPC')
emupath = os.path.expanduser('~/Library/Application Support/OpenEmu/Game Library')

# Define menu bar object and run it
class Client(rumps.App):
    def __init__(self):
        if not self.check_permissions():
            self.request_permissions()
            self.handle_error('Failed to receive permissions.', True)
        self.rpc = None
        self.games = None
        self.connect()
        super().__init__('OpenEmuRPC', title = '🎮')
        threading.Thread(target = self.background, daemon = True).start()

    def create_instance(self, clientID:str = '901628121214779412', pipe:int = 0):
        self.rpc = pypresence.Presence(clientID, pipe = pipe)

    def connect(self):
        if not self.rpc:
            self.create_instance()
        try:
            self.rpc.connect()
        except Exception as e:
            self.handle_error(e, True)

    def handle_error(self, error:Exception, quit:bool):
        if not os.path.isdir(path):
            os.mkdir(path)
        with open(f'{path}/error.txt', 'a') as file:
            file.write('[%s] %s\n' % (datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), error))
        print(error)
        if quit:
            rumps.alert('Error in OpenEmuRPC', '"%s"' % error)
            sys.exit()
        rumps.notification('Error in OpenEmuRPC', 'Make an issue if error persists', '"%s"' % error)

    def check_permissions(self):
        return Quartz.CGPreflightScreenCaptureAccess()

    def request_permissions(self):
        Quartz.CGRequestScreenCaptureAccess()

    def is_running(self):
        apps = AppKit.NSWorkspace.sharedWorkspace().launchedApplications()
        for app in apps:
            if app['NSApplicationName'] == appName:
                return True
        return False

    def update(self):
        if not self.is_running():
            self.rpc.clear()
            return
        windows = self.get_windows()
        menus = False
        dict = {
            'large_image': 'main',
            'large_text': appName,
            'buttons': [{'label': 'See %s' % appName, 'url': 'https://openemu.org/'},],
            'details': 'Idly in menus...',
        }
        for i in ('Library', 'Gameplay', 'Controls', 'Cores', 'System Files', 'Shader Parameters'):
            if i in windows:
                menus = i
                windows.remove(i)
        for i in ('', 'Apple', 'About', 'Updating OpenEmu', 'File', 'Edit', 'View', 'Window', 'Help'):
            if i in windows:
                windows.remove(i)
        if windows and windows != [appName]:
            if self.games != windows:
                self.start = round(time.time())
                self.games = windows.copy()
            dict['start'] = self.start
            if appName in windows:
                windows.remove(appName)
            game = windows[0]
            art = self.get_artwork(windows[0])
            if art:
                dict['large_image'] = art
            if len(windows) > 1:
                game = ', '.join(windows)
                art = self.get_artwork(windows[1])
                if art:
                    dict['small_image'] = art
                    dict['small_text'] = windows[1]
            dict['details'] = 'Playing %s' % game
            dict['large_text'] = windows[0]
            if menus:
                dict['details'] = ('In %s of ' + game) % menus
        for key in list(dict):
            if isinstance(dict[key], str):
                if len(dict[key]) < 2:
                    del dict[key]
                elif len(dict[key]) > 128:
                    dict[key] = dict[key][:128]
        self.rpc.update(**dict)

    def get_artwork(self, title:str):
        try:
            # Connect to OpenEmu's library database
            con = sqlite3.connect(os.path.join(emupath, 'Library.storedata'))
            cursor = con.cursor()

            # Get sources from image db
            cursor.execute('SELECT ZSOURCE FROM ZIMAGE')
            art = [ i[0] for i in cursor.fetchall() ]
            cursor.execute('SELECT Z_PK FROM ZIMAGE')
            zsource = [ i[0] for i in cursor.fetchall() ]
            art = [ (zsource[i],art[i]) for i in range(len(art)) ]
            cursor.execute('SELECT ZGAMETITLE FROM ZGAME')
            games = [ i[0] for i in cursor.fetchall() ]
            cursor.execute('SELECT Z_PK FROM ZROM')
            zpk = [ i[0] for i in cursor.fetchall() ]
            games = [ [zpk[i], games[i]] for i in range(len(games)) ]
            con.close()

            # Ahem, Future Delta here.
            # I do not want to mess with past me's stuff.
            # I fear no man.
            # But this?
            # This scares me.

            # Reorganize list in case of irregular OpenEmu shennanigans
            i = 0
            for e in games:
                if not e[1]:
                    games.remove(e)
                    h = i
                    for n in range(i, len(games)):
                        h += 1
                        games[n][0] = h
                    i -= 1
                i += 1

            # Find game in sources
            for i in games:
                if not i[1]: # Prevent irregular games from prematurely ending the recursion
                    continue
                if title in i[1]:
                    url = next(n[1] for n in art if n[0] == i[0])
                    return url
            return None
        except: # On possible failure, just return None
            return None

    def get_windows(self):
        response = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements|Quartz.kCGWindowListOptionOnScreenOnly,Quartz.kCGNullWindowID)
        windows = []
        for window in response:
            if window[Quartz.kCGWindowOwnerName] == appName:
                windows.append(window.get(Quartz.kCGWindowName, '<no name>'))
        while '' in windows:
            windows.remove('')
        return windows

    def background(self):
        while True:
            self.update()
            time.sleep(1)

if __name__ == '__main__':
    Client().run()
