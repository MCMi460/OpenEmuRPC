cd ..
python3 -m pip install -r requirements.txt py2app
python3 build.py py2app -O2
open ./dist
