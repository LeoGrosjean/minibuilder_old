import json
import os
import pathlib
import shutil
from ast import literal_eval
from configparser import ConfigParser
from urllib.parse import urlparse

import trimesh as tm
from flask import Blueprint, render_template, request, jsonify, url_for, redirect

from minibuilder.builder.node import read_node_link_json
from minibuilder.config import configpath
from minibuilder.file_config.parts import load_json
from minibuilder.forms.edit_file import DynamicFormEditMeshConf, BitzsForm
from minibuilder.forms.home import ChooseBuilderForm, get_data_folder

from minibuilder.utils.mesh import get_mesh_normal_position_edit
from minibuilder.utils.mesh_config import find_vertices

edit_file_bp = Blueprint('edit_file_bp', __name__)


@edit_file_bp.route('/edit/<builder>/<node>/<category>/<file>/', methods=['GET'])
def edit(builder, node, category, file):

    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    graph = read_node_link_json(f'{configuration_folder}/conf.json')

    if not os.path.exists(f'{data_folder}/{builder}/uploaded/'):
        pathlib.Path(f'{data_folder}/{builder}/uploaded/').mkdir(parents=True)

    form_header = ChooseBuilderForm()
    builders = [folder for folder in os.listdir(get_data_folder()) if not folder.startswith('.')]
    if not builders:
        return redirect(url_for('home_bp.list_builder_config'))
    form_header.builder.choices = builders
    form_header.builder.data = builder

    infos = {}
    for json_path in graph.nodes.get(node).get('files'):
        infos.update(load_json(f"{configuration_folder}/{json_path}"))

    form = DynamicFormEditMeshConf(graph, node)
    form.file_name.data = file
    form.hidden_file_name.data = file

    if not infos.get(category).get('stl').get(file):
        return "you can close this page"

    try:
        if graph.nodes[node].get('dextral'):
            form.dextral.data = infos.get(category).get('stl').get(file).get("dextral")
    except Exception as e:
        print(e)

    try:
        form.support.choices = form.support.choices + [infos.get(category).get('stl').get(file).get("support", {}).get('file', '')]
        form.support.data = infos.get(category).get('stl').get(file).get("support", {}).get('file', '')
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
        mesh = tm.load(f"{data_folder}/{builder}/{graph.nodes[node].get('folder')}/{category}/{file_name}")

    except Exception as e:
        print(e)
        message = ''
        for url in infos.get(category).get('stl').get(file).get('urls', []):
            message += f'<a href="{url}" target="_blank">{urlparse(url).netloc} </a><br>'

        return f"{infos.get(category).get('stl').get(file).get('file')} can be downloaded/buy there : <br>{message}<br>Then add them compressed or not !"

    di_normal = {}
    for node_ in form.connectors:
        folder = graph.nodes[node_].get('folder')
        dextral = graph.nodes[node_].get('dextral')
        if hasattr(form, f"{node_}_marker"):
            if graph.nodes[node_].get('dextral'):
                try:
                    vertice_info = infos.get(category).get('stl').get(file).get(folder)[dextral]
                except Exception as e:
                    print(e)
                    vertice_info = infos.get(category).get('stl').get(file).get(folder, {})
            else:
                vertice_info = infos.get(category).get('stl').get(file).get(folder, {})

            getattr(form, f"{node_}_marker").data = str(vertice_info if vertice_info else "")
            # TODO MOVE MARKER XY
            #getattr(form, f"marker_{node_}_movex").data = vertice_info.get('x', 0)
            #getattr(form, f"marker_{node_}_movey").data = vertice_info.get('y', 0)

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
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    graph = read_node_link_json(f'{configuration_folder}/conf.json')

    form_result = request.form.to_dict()
    for json_path in graph.nodes.get(node).get('files'):
        json_file = load_json(f"{configuration_folder}/{json_path}")
        if category in json_file.keys():
            break

    file_name_before = form_result.pop('hidden_file_name')
    file_name_new = form_result.pop('file_name')

    mesh_info = json_file[category]['stl'][file_name_before]

    conf = {
        "urls": [form_result.pop("url")],
        "designer": form_result.pop("designer"),
    }
    if form_result.get("dextral"):
        conf['dextral'] = form_result.pop("dextral")

    support = form_result.pop("support")
    support_file_old = mesh_info.get('support', {}).get('file')
    if support and support != support_file_old:
        conf["support"] = {
            "file": support,
            "md5": tm.load(f"{data_folder}/{builder}/uploaded/{support}").identifier_md5
        }
    folder = graph.nodes[node].get('folder')

    mesh = tm.load(f"{data_folder}/{builder}/{folder}/{category}/{mesh_info['file']}")

    for k, v in form_result.items():
        if k.endswith('marker') and form_result.get(k):
            node_ = k.replace('_marker', '')
            folder_ = graph.nodes[node_].get('folder')
            marker = find_vertices(mesh, *literal_eval(f"[[{form_result.get(k)}]]"))
            dextral = graph.nodes[node_].get('dextral')
            dex_type = graph.nodes[node_].get('dex_type')
            if dex_type and node_ in list(graph.successors(node)):
                if conf.get(folder_):
                    conf[dex_type][dextral] = marker
                    # TODO MOVE MARKER XY
                    #conf[dex_type][dextral]['x'] = float(form_result.get(f"marker_{node_}_movex"))
                    #conf[dex_type][dextral]['y'] = float(form_result.get(f"marker_{node_}_movey"))
                else:
                    conf[dex_type] = {dextral: marker}
                    #conf[dex_type][dextral]['x'] = float(form_result.get(f"marker_{node_}_movex"))
                    #conf[dex_type][dextral]['y'] = float(form_result.get(f"marker_{node_}_movey"))
            else:
                conf[folder_] = marker
                #conf[folder_]['x'] = float(form_result.get(f"marker_{node_}_movex"))
                #conf[folder_]['y'] = float(form_result.get(f"marker_{node_}_movey"))

    mesh_info.update(conf)
    new_conf = mesh_info.copy()

    if file_name_before != file_name_new:
        json_file[category]['stl'][file_name_new] = new_conf
        del json_file[category]['stl'][file_name_before]

    folder = graph.nodes[node].get('folder')

    if support and support != support_file_old:
        try:
            if not os.path.exists(f"{data_folder}/{builder}/{folder}/{category}/support/"):
                pathlib.Path(f"{data_folder}/{builder}/{folder}/{category}/support/").mkdir(parents=True)

            if form_result.get('support') in os.listdir(f"{data_folder}/{builder}/{folder}/{category}/support/"):
                return f"""
                There is an issue with the support file, he gots the same name than another file in "data/{builder}/{folder}/{category}/support/"
                """
            else:
                shutil.move(
                    f"{data_folder}/{builder}/uploaded/{support}",
                    f"{data_folder}/{builder}/{folder}/{category}/support/")
                print(f"{data_folder}/{builder}/uploaded/{support} moved to "
                      f"{data_folder}/{builder}/{folder}/{category}/support !")
        except Exception as e:
            print(e)
    conf_path = f"{data_folder}/{builder}/configuration/{json_path.replace('.', '/', json_path.count('.') - 1)}"
    with open(conf_path, "w") as outfile:
        json.dump(json_file, outfile, indent=4)

    return redirect(url_for("edit_file_bp.edit", builder=builder, node=node, category=category, file=file))


@edit_file_bp.route('/send/<builder>/<folder>/<category>/<file_name>/', methods=['GET', 'POST'])
def send(builder, folder, category, file_name):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"
    try:
        mesh = tm.load(f"{data_folder}/{builder}/{folder}/{category}/{file_name}")
    except Exception as e:
        print(e)
        return ""
    return mesh.export(file_type='stl')


@edit_file_bp.route('/addbitz/<builder>/<node>/<category>/<file>/', methods=["POST"])
def addbitz(builder, node, category, file):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    graph = read_node_link_json(f'{configuration_folder}/conf.json')

    for conf_json in graph.nodes.get(node).get('files'):
        path_conf = f"{data_folder}/{builder}/configuration/{conf_json}"
        files_conf = load_json(path_conf)

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
            mesh = tm.load(f"{data_folder}/{builder}/{folder}/{category}/{file_name}")

            files_conf.get(category).get('stl').get(file)['bitzs'] = {}
            for bitz in li:
                files_conf.get(category).get('stl').get(file)['bitzs'][bitz.get('name')] = find_vertices(mesh, *literal_eval(f"[[{bitz.get('marker')}]]"))

            conf_json = conf_json.replace('.', '/', conf_json.count('.') - 1)
            with open(f"{configuration_folder}/{conf_json}", "w") as outfile:
                json.dump(files_conf, outfile, indent=4)

        # server-side validation
        if li:
            # data is valid, so at this point save data to database
            return jsonify({'success': f'File configuration has been updated ! {", ".join([x.get("name") for x in li])}'})

        else:
            # errors occured during validation
            return (jsonify({'errors': "Can't update configuration. Add a marker or a name to the bitz."}))
