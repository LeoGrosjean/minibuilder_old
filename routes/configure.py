from io import BytesIO

from flask import Blueprint, render_template, request, url_for, redirect, jsonify, flash, send_file, make_response
import trimesh as tm
from builder.node import read_node_link_json
from utils.render import scene_to_html

configure_bp = Blueprint('configure_bp', __name__)


@configure_bp.route('/builder/<builder_name>/configure', methods=['GET', 'POST'])
def builder(builder_name):
    form_result = request.form.to_dict()
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    mesh = tm.load_remote("https://cdn.thingiverse.com/assets/0a/a4/28/c9/c1/torso.stl")
    mesh.metadata['file_name'] = 'body'

    #return scene_to_html(mesh.scene(), mode="make_conf")
    return render_template("makeconf.html")


@configure_bp.route('/send', methods=['GET', 'POST'])
def send():
    mesh = tm.load("data/Wargame Humanoid/arm/Space Warrior/heavy_weapons_-_arms.stl")
    return mesh.export(file_type='stl')