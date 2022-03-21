import json
import os
import pathlib
from ast import literal_eval
from urllib.parse import urlparse

import trimesh as tm
from flask import Blueprint, render_template, request, jsonify, flash

from builder.node import read_node_link_json
from file_config.parts import load_json
from forms.edit_file import DynamicFormEditMeshConf, BitzsForm
from forms.home import ChooseBuilderForm
from utils.mesh import get_mesh_normal_position_edit
from utils.mesh_config import find_vertices

edit_file_bp = Blueprint('edit_file_bp', __name__)


@edit_file_bp.route('/edit/<builder>/<node>/<category>/<file>/', methods=['GET'])
def edit(builder, node, category, file):
    graph = read_node_link_json(f'data/{builder}/conf.json')
    if not os.path.exists(f'data/{builder}/uploaded/'):
        pathlib.Path(f'data/{builder}/uploaded/').mkdir(parents=True)
    form_header = ChooseBuilderForm()
    form_header.builder.data = builder

    infos = {}
    for json_path in graph.nodes.get(node).get('files'):
        infos.update(load_json(f"data/{builder}/{json_path}"))

    form = DynamicFormEditMeshConf(graph, node)
    form.file_name.data = file

    try:
        form.support.data = infos.get(category).get('stl').get(file).get("support")
    except Exception as e:
        print(e)
    try:
        form.url.data = infos.get(category).get('stl').get(file).get("urls")[0]
    except Exception as e:
        print(e)

    try:
        form.designer.data = infos.get(category).get('stl').get(file).get("designer")
    except Exception as e:
        print(e)

    try:
        file_name = infos.get(category).get('stl').get(file).get('file')
        mesh = tm.load(f"data/{builder}/{graph.nodes[node].get('folder')}/{category}/{file_name}")

    except Exception as e:
        print(e)
        message = ''
        for url in infos.get(category).get('stl').get(file).get('urls', []):
            message += f'<a href="{url}" target="_blank">{urlparse(url).netloc} </a><br>'

        return f"{infos.get(category).get('stl').get(file).get('file')} can be downloaded/buy there : <br>{message}<br>Then add them compressed or not !"

    di_normal = {}
    for node_ in form.connectors:
        print(node_)
        folder = graph.nodes[node_].get('folder')
        dextral = graph.nodes[node_].get('dextral')
        if hasattr(form, f"{node_}_marker"):
            if dextral:
                try:
                    vertice_info = infos.get(category).get('stl').get(file).get(folder)[dextral]
                except Exception as e:
                    print(e)
                    vertice_info = infos.get(category).get('stl').get(file).get(folder, "")
            else:
                vertice_info = infos.get(category).get('stl').get(file).get(folder, "")
            getattr(form, f"{node_}_marker").data = str(vertice_info)

            if folder in infos.get(category).get('stl').get(file):
                try:
                    normal, vertice, normal_x, normal_y = get_mesh_normal_position_edit(mesh,
                                                                infos.get(category).get('stl').get(file),
                                                                folder, dextral)
                except:
                    normal, vertice, normal_x, normal_y = get_mesh_normal_position_edit(mesh,
                                                                                        infos.get(category).get('stl').get(file),
                                                                                        folder)
            else:
                normal = vertice = normal_x = normal_y = ''
            di_normal[node_] = {
                "normal": normal,
                "vertice": vertice,
                "normal_x": normal_x,
                "normal_y": normal_y,
            }
            mesh_info = {
            "builder": builder,
            "folder": graph.nodes[node].get('folder'),
            "category": category,
            "file_name": file_name,
            "file": file,
            "node": node
            }

    form_bitz = BitzsForm()
    for bitz_name, bitz_marker in infos.get(category).get('stl').get(file).get("bitzs", {}).items():
        form_bitz.bitzs.append_entry({"name": bitz_name, "marker": bitz_marker})
    else:
        form_bitz.bitzs.append_entry()

    return render_template("edit_file.html",
                           form=form,
                           form_bitz=form_bitz,
                           nodes=list(graph.nodes),
                           builder=builder,
                           form_header=form_header,
                           mesh_info=mesh_info,
                           di_normal=di_normal,
                           )


@edit_file_bp.route('/edit_post/<builder>/<node>/<category>/<file>/', methods=['POST'])
def edit_post(builder, node, category, file):
    return json.dumps(request.form.to_dict(), indent=4)


@edit_file_bp.route('/send/<builder>/<folder>/<category>/<file_name>/', methods=['GET', 'POST'])
def send(builder, folder, category, file_name):
    try:
        mesh = tm.load(f"data/{builder}/{folder}/{category}/{file_name}")
    except Exception as e:
        print(e)
        return ""
    return mesh.export(file_type='stl')


@edit_file_bp.route('/addbitz/<builder>/<node>/<category>/<file>/', methods=["POST"])
def addbitz(builder, node, category, file):
    graph = read_node_link_json(f'data/{builder}/conf.json')
    for conf_json in graph.nodes.get(node).get('files'):
        files_conf = load_json(f"data/{builder}/{conf_json}")

        if category in files_conf:
            if file in files_conf.get(category).get('stl'):
                break

    if request.method == "POST":
        # get data from ajax request
        form_bitz = BitzsForm(request.form)
        li = []
        for fieldlist in form_bitz:   # check console logs if data was received
            try:
                _ = (entry for entry in fieldlist)
            except TypeError:
                continue
            for entry in fieldlist:
                if isinstance(entry.data, dict):
                    bitz_info = dict(entry.data)
                    bitz_info.pop('csrf_token')
                    if bitz_info.get('name') and bitz_info.get('marker'):
                        li.append(bitz_info)
        if li:
            file_name = files_conf.get(category).get('stl').get(file).get('file')
            folder = graph.nodes[node].get('folder')
            mesh = tm.load(f"data/{builder}/{folder}/{category}/{file_name}")

            files_conf.get(category).get('stl').get(file)['bitzs'] = {}
            for bitz in li:
                files_conf.get(category).get('stl').get(file)['bitzs'][bitz.get('name')] = find_vertices(mesh, *literal_eval(f"[[{bitz.get('marker')}]]"))

            with open(f"data/{builder}/{conf_json}", "w") as outfile:
                json.dump(files_conf, outfile, indent=4)

        # server-side validation
        if li:
            # data is valid, so at this point save data to database
            return jsonify({'success': f'File configuration has been updated ! {", ".join([x.get("name") for x in li])}'})

        else:
            # errors occured during validation
            return (jsonify({'errors': "Can't update configuration. Add a marker or a name to the bitz."}))
