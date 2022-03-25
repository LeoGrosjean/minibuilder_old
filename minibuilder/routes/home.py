from pathlib import Path
from flask import redirect, url_for
from flask import Blueprint, render_template, request

from minibuilder.forms.home import ChooseBuilderForm

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/', methods=['GET', 'POST'])
def choose_builder():
    from minibuilder.config import Config
    c = Config()

    data_dir = Path(c.data_folder)
    if not data_dir.is_dir():
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


@home_bp.route("/make_data_folder")
def make_folder():
    return render_template("make_folder_data.html")
