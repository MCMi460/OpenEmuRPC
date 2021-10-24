from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'iconfile': 'build/AppIcon.icns',
    'plist': {
        'CFBundleName': 'OpenEmuRPC',
        'CFBundleShortVersionString': '1.0',
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
