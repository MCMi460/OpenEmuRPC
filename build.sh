curl https://api.github.com/repos/MCMi460/OpenEmuRPC/zipball/main -o OERPC.zip -L
unzip OERPC.zip -d ./OERPC
rm OERPC.zip
cd ./OERPC/*/
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt py2app
python setup.py py2app
open ./dist
rm ../../build.sh
