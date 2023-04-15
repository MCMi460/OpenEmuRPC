cd ..
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt py2app
python build.py py2app
open ./dist
