from configparser import ConfigParser
from pathlib import Path
from flask import redirect, url_for
from flask import Blueprint, render_template, request
from github import Github

from minibuilder.config import configpath
from minibuilder.forms.home import ChooseBuilderForm, EditConfForm

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/', methods=['GET', 'POST'])
def choose_builder():
    if not Path(configpath).is_dir():
        return redirect(url_for("home_bp.make_folder"))

    form = ChooseBuilderForm()
    if request.method == 'POST':
        results = request.form.to_dict()
        if results.get('submit'):
            return redirect(f"/builder/{results.get('builder')}")
        elif results.get('add_files'):
            return redirect(f"/builder/{results.get('builder')}/configure")
        elif results.get('add_designers'):
            return redirect(f"/builder/{results.get('builder')}/designers")

    return render_template("about.html", form_header=form)


@home_bp.route("/make_data_folder", methods=['GET', 'POST'])
def make_folder():

    form = EditConfForm()
    try:
        config = ConfigParser()
        config.read(configpath + "/mbconfig.ini")
        form.user_data_path.default = config['FOLDER']['data_path']
        form.port.data = config['SERVER']['port']
    except Exception:
        pass

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

    return render_template("make_folder_data.html", form=form)


@home_bp.route("/list_file_config/<builder>", methods=['GET'])
def list_file_config(builder):
    g = Github()
    repo = g.get_repo("LeoGrosjean/minibuilder")
    conf_category = []
    for content in repo.get_contents(f"data/{builder}/configuration"):
        if content.type == "dir":
            conf_category.append(repo.get_contents(content.path))
        else:
            continue
            print(file_content)

    form = EditConfForm()
    try:
        config = ConfigParser()
        config.read(configpath + "/mbconfig.ini")
        form.user_data_path.default = config['FOLDER']['data_path']
        form.port.data = config['SERVER']['port']
    except Exception:
        pass

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

    return render_template("make_folder_data.html", form=form)
