import json
import os
from configparser import ConfigParser
from pathlib import Path
from flask import redirect, url_for
from flask import Blueprint, render_template, request
from github import Github
from requests import get
from slugify import slugify

from minibuilder.builder.node import read_node_link_json
from minibuilder.config import configpath
from minibuilder.file_config.parts import load_json
from minibuilder.forms.home import ChooseBuilderForm, EditConfForm, make_AddBuilderForm, get_data_folder, \
    dynamic_selectcategory
from minibuilder.utils.dict import update

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/', methods=['GET', 'POST'])
def choose_builder():
    if not Path(configpath).is_dir():
        return redirect(url_for("home_bp.make_folder"))

    r = get('https://raw.githubusercontent.com/LeoGrosjean/miniBuilder-Configuration/main/configs.json')

    with open(f'{configpath}/config.json', 'w') as fp:
        json.dump(json.loads(r.content), fp)

    form = ChooseBuilderForm()
    if not Path(get_data_folder()).is_dir():
        return redirect(url_for("home_bp.make_folder"))
    builders = [folder for folder in os.listdir(get_data_folder()) if not folder.startswith('.')]
    form.builder.choices = builders

    if request.method == 'POST':
        results = request.form.to_dict()
        if results.get('submit'):
            return redirect(f"/builder/{results.get('builder')}")
        elif results.get('add_files'):
            return redirect(f"/builder/{results.get('builder')}/configure")
        elif results.get('add_designers'):
            return redirect(f"/builder/{results.get('builder')}/designers")

    return render_template("about.html", form_header=form, builder=builders[0] if builders else None)


@home_bp.route("/make_data_folder", methods=['GET', 'POST'])
def make_folder():
    form_header = ChooseBuilderForm()
    try:
        builders = [folder for folder in os.listdir(get_data_folder()) if not folder.startswith('.')]
        form_header.builder.choices = builders
    except Exception as e:
        print(e)
    form = EditConfForm()
    try:
        config = ConfigParser()
        config.read(configpath + "/mbconfig.ini")
        form.user_data_path.data = config['FOLDER']['data_path']
        form.port.data = config['SERVER']['port']
    except Exception:
        pass
    message = ""
    if request.method == 'POST':
        form_result = request.form.to_dict()
        config = ConfigParser()
        config['FOLDER'] = {
            "data_path": form_result.get('user_data_path')
        }
        config['SERVER'] = {
            "port": form_result.get('port')
        }
        Path(configpath).mkdir(parents=True, exist_ok=True)
        with open(f'{configpath}/mbconfig.ini', 'w') as configfile:
            config.write(configfile)
        Path(form_result.get('user_data_path')).mkdir(parents=True, exist_ok=True)
        message="Relaunch miniBuilder to validate change !"
        builders = os.listdir(get_data_folder())
        form_header.builder.choices = builders

    return render_template("make_folder_data.html", form=form, form_header=form_header, message=message)


@home_bp.route("/add_builder", methods=['GET'])
def list_builder_config():
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    form_header = ChooseBuilderForm()
    if not Path(get_data_folder()).is_dir():
        return redirect(url_for("home_bp.make_folder"))
    builders = [folder for folder in os.listdir(get_data_folder()) if not folder.startswith('.')]
    form_header.builder.choices = builders
    try:
        builder = builders[0]
    except:
        builder = None

    with open(f'{configpath}/config.json') as json_file:
        conf = json.load(json_file)

    #form = make_AddBuilderForm(data_path=data_folder, config=conf)()

    dl = {}
    update = {}

    for builder, file_categories in conf.items():
        if Path(f"{data_folder}/{builder}").exists():
            curr = update
        else:
            curr = dl
        curr[builder] = {
            "dl": {},
            "update": {}
        }
        for category, files in file_categories.items():
            if Path(f"{data_folder}/{builder}/configuration/{category}").exists():
                curr[builder]['update'][category] = files
            else:
                curr[builder]['dl'][category] = files

    return render_template("git_config/add_files.html", dl=dl, update=update, slugify=slugify, form_header=form_header, builder=builder)


@home_bp.route("/dl_builder/<builder>", methods=['GET'])
def dl_builder(builder):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']

    conf = get(f"https://raw.githubusercontent.com/LeoGrosjean/minibuilder/main/data/{builder}/configuration/conf.json")
    conf = json.loads(conf.content)

    if Path(f"{data_folder}/{builder}/configuration/conf.json").exists():
        conf_old = load_json(f"{data_folder}/{builder}/configuration/conf.json", occurence=0)
        if conf['graph'].get('bitz_files'):
            conf['graph']['bitz_files'] = list(set(conf['graph']['bitz_files'] + conf_old['graph'].get('bitz_files', [])))
            conf_old['graph']['bitz_files'] = conf['graph']['bitz_files']
        for node in conf['nodes']:
            for node_old in conf_old["nodes"]:
                if node_old['id'] == node['id']:
                    break
            node['files'] = list(set(node['files'] + node_old['files']))
            node_old['files'] = node['files']
        conf = update(conf, conf_old)

    Path(f"{data_folder}/{builder}/configuration/").mkdir(parents=True, exist_ok=True)
    with open(f"{data_folder}/{builder}/configuration/conf.json", "w") as outfile:
        json.dump(conf, outfile, indent=4)

    for designer in conf['graph'].get('designer_files'):
        designer_ = get(
            f"https://raw.githubusercontent.com/LeoGrosjean/minibuilder/main/data/{builder}/configuration/{designer}")
        designer_ = json.loads(designer_.content)

        if Path(f"{data_folder}/{builder}/configuration/{designer}").exists():
            designer_old = load_json(f"{data_folder}/{builder}/configuration/{designer}", occurence=0)
            designer_ = update(designer_, designer_old)

        Path(f"{data_folder}/{builder}/configuration/").mkdir(parents=True, exist_ok=True)
        with open(f"{data_folder}/{builder}/configuration/{designer}", "w") as outfile:
            json.dump(designer_, outfile, indent=4)

    empty = get(f"https://raw.githubusercontent.com/LeoGrosjean/minibuilder/main/data/{builder}/configuration/empty.json")
    empty = json.loads(empty.content)

    with open(f"{data_folder}/{builder}/configuration/empty.json", "w") as outfile:
        json.dump(empty, outfile, indent=4)

    return redirect(url_for('home_bp.list_builder_config'))


@home_bp.route("/dl_category_config/<builder>/<category>", methods=['GET'])
def dl_category_config(builder, category):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']

    with open(f'{configpath}/config.json') as json_file:
        conf = json.load(json_file)

    conf_ = load_json(f"{data_folder}/{builder}/configuration/conf.json", occurence=0)

    for file in conf[builder][category]:
        file_ = get(f"https://raw.githubusercontent.com/LeoGrosjean/minibuilder/main/data/{builder}/configuration/{category}/{file}")
        file_ = json.loads(file_.content)

        if Path(f"{data_folder}/{builder}/configuration/{category}/{file}").exists():
            file_old = load_json(f"{data_folder}/{builder}/configuration/{category}/{file}", occurence=0)
            file_ = update(file_, file_old)

        folders = []
        got_bitz = False
        for cat in file_.keys():
            folders.extend(file_[cat]['desc'].get("nodes", []))
            if file_[cat]['desc'].get("bitz"):
                got_bitz = True
        folders = list(set(folders))

        for node in conf_.get("nodes", []):
            if node.get('folder') in folders:
                node['files'] = list(set(node['files'] + [f"{category}.{file}"]))

        if got_bitz:
            conf_['graph']['bitz_files'] = list(set(conf_['graph'].get('bitz_files', []) + [f"{category}.{file}"]))

        Path(f"{data_folder}/{builder}/configuration/{category}/").mkdir(parents=True, exist_ok=True)
        with open(f"{data_folder}/{builder}/configuration/{category}/{file}", "w") as outfile:
            json.dump(file_, outfile, indent=4)

    Path(f"{data_folder}/{builder}/configuration/").mkdir(parents=True, exist_ok=True)
    with open(f"{data_folder}/{builder}/configuration/conf.json", "w") as outfile:
        json.dump(conf_, outfile, indent=4)

    return redirect(url_for('home_bp.list_builder_config'))


@home_bp.route("/select_category/", methods=['GET'])
def redirect_empty_category():
    return redirect(url_for('home_bp.list_builder_config'))


@home_bp.route("/select_category/<builder>", methods=['GET', 'POST'])
def select_category(builder):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    form_header = ChooseBuilderForm()
    if not Path(get_data_folder()).is_dir():
        return redirect(url_for("home_bp.make_folder"))
    builders = [folder for folder in os.listdir(get_data_folder()) if not folder.startswith('.')]

    if not builders:
        return redirect(url_for('home_bp.list_builder_config'))

    form_header.builder.choices = builders
    form_header.builder.data = builder

    graph = read_node_link_json(f'{configuration_folder}/conf.json')

    infos = {}
    infos_node = {}
    for node_name in graph.nbunch_iter():
        infos_node[node_name] = {}
        for json_path in graph.nodes.get(node_name).get('files'):
            tmp = load_json(f"{configuration_folder}/{json_path}")
            infos.update(tmp)
            infos_node[node_name].update(tmp)
    bitzs = {}
    for file in graph.graph.get('bitz_files', []):
        bitzs.update(load_json(f"{configuration_folder}/{file}"))

    display_infos = {
        "bitz_category": {},
        "category": {}
    }
    if request.method == 'POST':
        with open(f"{configuration_folder}/{slugify(builder, separator='_')}.json", 'w') as f:
            for k, v in request.form.to_dict().items():
                for cat in list(infos.keys()) + list(bitzs.keys()):
                    if slugify(cat) == k.replace('category_', '', 1):
                        display_infos['category'][cat] = True if v == 'y' else False
                    elif slugify(cat) == k.replace('bitz_', '', 1):
                        display_infos['bitz_category'][cat] = True if v == 'y' else False

            for missing_cat in set(infos.keys()) ^ set(display_infos['category'].keys()):
                display_infos['category'][missing_cat] = False
            for missing_cat in set(bitzs.keys()) ^ set(display_infos['bitz_category'].keys()):
                display_infos['bitz_category'][missing_cat] = False

            json.dump(display_infos, f, indent=4)
    else:
        try:
            display_infos = load_json(f"{configuration_folder}/{slugify(builder, separator='_')}.json")
        except:
            display_infos = {
                "bitz_category": {},
                "category": {}
            }

    display_bitz = {}
    for k in bitzs.keys():
        display_bitz[k] = display_infos['bitz_category'].get(k, True)

    display_cat = {}
    for k in infos.keys():
        display_cat[k] = display_infos['category'].get(k, True)

    display_node = {}
    for k in infos.keys():
        display_node[k] = []
        for node, v2 in infos_node.items():
            if k in v2.keys():
                display_node[k].append(node)

    form = dynamic_selectcategory(
        bitz_category=dict(sorted(display_bitz.items())),
        category=dict(sorted(display_cat.items()))
    )()

    return render_template("configuration/category_select.html", form_header=form_header, form=form, display_node=display_node, builder=builder)
