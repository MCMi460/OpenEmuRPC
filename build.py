from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'iconfile': 'images/AppIcon.icns',
    'plist': {
        'CFBundleName': 'OpenEmuRPC',
        'CFBundleShortVersionString': '1.1',
        'LSUIElement': True,
    },
    'packages': ['rumps'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
