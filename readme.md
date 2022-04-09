## Create Virtual Env
You need a [python](https://www.python.org/downloads/) version installed locally.

### 1. With [virtualenv](https://github.com/pypa/virtualenv)

Upgrade PIP 
    
```shell script
pip install -U pip 
pip install virtualenv
```
Create your virtual environment

```shell script
cd <DESTINATION_FOLDER>
virtualenv <ENVIRONMENT_NAME>
```

````shell
pip install -r requirements.txt
````

## Launch App
Within your virtual environment

```
python app.py
```
A web browser managed from selenium will launch, it will be used to automatically download files from website that need authentification :
1. Cults3d required to be connected to your account to download file
2. paid files can't be acquired for free, you need to be connected to the website hosting  paid files

It uses selenium webbrowser to get the cookies and automatized the connection, the user just need to login to the service he wants to download files !

Thingiverse has an API and user dont need to be authentificated

## Configuration file
Each mesh is a node

Each node has different rules (rotate, merge, scale...)

Configuration file allow user to make a miniBuilder about everything !

check ````data/<builder>/conf.json```` file
WIP

## Technical Stack

Back (python):
- Flask (framework web)
- Trimesh (edit mesh)
- networkx (graph)
Software Back:
- blender (optional, for boolean dif, not used in prod but works in dev ex: hole for magnet)

Front :
- native JS
- bootstrap
- THREE.JS (live edit)
   
## License

Working on it, but in the futur I want to monetize my work on the project. However dunno how yet !

So you can't copy my work without asking me, the code of miniBuilder is the propriety of Leopold Grosjean (lol) !

The configuration files can be shared and are not included in the license (all the data folder)

pyinstaller --name miniBuilder --add-data "minibuilder;minibuilder/" app.py
