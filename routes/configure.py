import json
import os
import pathlib
import shutil
from ast import literal_eval
from io import BytesIO
import hashlib
from uuid import uuid4

import patoolib
from flask import Blueprint, render_template, request, url_for, redirect, jsonify, flash, send_file, make_response
import trimesh as tm
from werkzeug.utils import secure_filename

from builder.node import read_node_link_json
from builder.scene import SceneGraphInfo
from file_config.parts import load_json
from forms.configure import DynamicFormMakeMeshConf, FormUploadFile
from forms.home import ChooseBuilderForm
from utils.compressed import extract_nested_compress
from utils.mesh_config import find_vertices
from utils.render import scene_to_html

configure_bp = Blueprint('configure_bp', __name__)


@configure_bp.route('/builder/<builder_name>/configure', methods=['GET'])
def builder(builder_name):
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    if not os.path.exists(f'data/{builder_name}/uploaded/'):
        pathlib.Path(f'data/{builder_name}/uploaded/').mkdir(parents=True)
    form_header = ChooseBuilderForm()
    form_header.builder.data = builder_name
    form = DynamicFormMakeMeshConf(graph)

    form_upload = FormUploadFile()

    return render_template("configure.html",
                           form=form,
                           nodes=list(graph.nodes),
                           form_upload=form_upload,
                           builder=builder_name,
                           form_header=form_header)


@configure_bp.route('/builder/<builder_name>/configure', methods=['POST'])
def builder_post(builder_name):
    form_upload = FormUploadFile()
    form_header = ChooseBuilderForm()
    form_header.builder.data = builder_name
    if form_upload.validate_on_submit():
        files_filenames = []
        for file in form_upload.files.data:
            file_filename = secure_filename(file.filename)
            file.save(f"data/{builder_name}/uploaded/{file_filename}")
            # TODO check if compress and flatten them in uploaded
            extract_nested_compress(builder_name, file_filename)
        return redirect(url_for("configure_bp.builder", builder_name=builder_name))

    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    form_result = request.form.to_dict()

    conf_json = form_result.get('file')
    mesh = tm.load(f"data/{builder_name}/uploaded/{form_result.get('mesh_file')}")

    mesh_info = {
        form_result.get('file_name'): {
            "file": form_result.get("mesh_file"),
            "designer": form_result.get('designer'),
            "md5": tm.load(f"data/{builder_name}/uploaded/{form_result.get('mesh_file')}").identifier_md5,
            "urls": [form_result.get('url')]
        }
    }
    if form_result.get('support'):
        mesh_info[form_result.get('file_name')]['support'] = {
            "file": form_result.get('support'),
            "md5": tm.load(f"data/{builder_name}/uploaded/{form_result.get('support')}").identifier_md5
        }

    for k, v in form_result.items():
        if k.startswith('marker_') and v:
            node = graph.nodes[k.replace('marker_', '')]
            if k.replace('marker_', '') in list(graph.predecessors(form_result.get('node'))):
                node = graph.nodes[form_result.get('node')]
                folder = node['folder']
                if node.get('dextral'):
                    mesh_info[form_result.get('file_name')]['dextral'] = node.get('dextral')
                mesh_info[form_result.get('file_name')][folder] = find_vertices(mesh, *literal_eval(f"[[{form_result.get(k)}]]"))
            else:
                folder = node['folder']
                if node.get('dextral'):
                    if not mesh_info[form_result.get('file_name')].get(folder):
                        mesh_info[form_result.get('file_name')][folder] = {}
                    mesh_info[form_result.get('file_name')][folder].update({ node.get('dextral'): find_vertices(mesh, *literal_eval(f"[[{form_result.get(k)}]]")) })
                else:
                    mesh_info[form_result.get('file_name')][folder] = find_vertices(mesh, *literal_eval(f"[[{form_result.get(k)}]]"))
    del mesh
    try:
        conf = load_json(f"data/{builder_name}/{conf_json}")
        if conf.get(form_result.get('category')):
            if conf[form_result.get('category')]['stl'].get(form_result.get('file_name')):
                conf[form_result.get('category')]['stl'][form_result.get('file_name')].update(mesh_info[form_result.get('file_name')])
            else:
                conf[form_result.get('category')]['stl'].update(mesh_info)
            print(f"data/{builder_name}/{conf_json} has been updated !")
        else:
            conf[form_result.get('category')] = {
                "desc": {
                    "display": form_result.get('category'),
                    "path": f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/"
                },
                "stl": mesh_info
                }
            print(f"data/{builder_name}/{conf_json} has been updated with {form_result.get('category')}!")

    except Exception as e:
        print(e)
        conf = {
            form_result.get('category'): {
                "desc": {
                    "display": form_result.get('category'),
                    "path": f"data/{builder_name}/{graph.nodes[form_result.get('node')].get('folder')}/{form_result.get('category')}/"
                },
                "stl": mesh_info
                }
            }
        print(f"data/{builder_name}/{conf_json} has been created with {form_result.get('category')}!")

        with open(f"data/{builder_name}/conf.json", "r+") as node_file:
            data = json.load(node_file)
            for i, node in enumerate(data['nodes']):
                if node.get('id') == form_result.get('node'):
                    folder = node.get('folder')
                    break

            for i, node in enumerate(data['nodes']):
                if node.get('folder') == folder:
                    data['nodes'][i]['files'].append(conf_json)
                    print(f"{conf_json} added to files of {form_result.get('node')}!")

            node_file.seek(0)
            json.dump(data, node_file, indent=4)

    with open(f"data/{builder_name}/{conf_json}", "w") as outfile:
        json.dump(conf, outfile, indent=4)

    # file:
    # TODO if file_name already exist (and is different assuming check md5 has been done) it will add uuid in file_name not in conf
    try:
        if not os.path.exists(f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/"):
            pathlib.Path(f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/").mkdir(
                parents=True)
        if form_result.get('mesh_file') in os.listdir(
                f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/"):
            shutil.move(
                f"data/{builder_name}/uploaded/{form_result.get('mesh_file')}",
                f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/"
                f"{uuid4()}_{form_result.get('mesh_file')}")
            print(f"data/{builder_name}/uploaded/{form_result.get('mesh_file')} moved to "
                  f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')} !")
        else:
            shutil.move(
                f"data/{builder_name}/uploaded/{form_result.get('mesh_file')}",
                f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/")
            print(f"data/{builder_name}/uploaded/{form_result.get('mesh_file')} moved to "
                  f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')} !")
    except FileExistsError as e:
        print(e)
    # support
    if form_result.get('support'):
        try:
            if not os.path.exists(f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support/"):
                pathlib.Path(f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support/").mkdir(parents=True)
            if form_result.get('support') in os.listdir(
                    f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support/"):
                shutil.move(
                    f"data/{builder_name}/uploaded/{form_result.get('support')}",
                    f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support/"
                    f"{uuid4()}_{form_result.get('support')}")
                print(f"data/{builder_name}/uploaded/{form_result.get('support')} moved to "
                      f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support !")
            else:
                shutil.move(
                    f"data/{builder_name}/uploaded/{form_result.get('support')}",
                    f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support/")
                print(f"data/{builder_name}/uploaded/{form_result.get('support')} moved to "
                      f"data/{builder_name}/{graph.nodes[form_result.get('node')]['folder']}/{form_result.get('category')}/support !")
        except Exception as e:
            print(e)


    form = DynamicFormMakeMeshConf(graph, **form_result)

    return render_template("configure.html",
                           form=form,
                           nodes=list(graph.nodes),
                           form_upload=form_upload,
                           builder=builder_name,
                           form_header=form_header
                           )


@configure_bp.route('/send/<builder>/<file>/', methods=['GET', 'POST'])
def send(builder, file):
    try:
        mesh = tm.load(f"data/{builder}/uploaded/{file}")
    except Exception as e:
        print(e)
        return ""
    return mesh.export(file_type='stl')


@configure_bp.route('/configureformnode/<builder>/<node>/')
def update_configure_node(builder, node):
    graph = read_node_link_json(f'data/{builder}/conf.json')
    form = DynamicFormMakeMeshConf(graph, node=node)

    choices = {
        "file": list(zip(form.file.choices, form.file.choices)),
        "category": list(zip(form.category.choices, form.category.choices)),
        "all_connections": list(graph.nodes),
        "connection": list(form.connectors)
    }

    response = make_response(json.dumps(choices))
    response.content_type = 'application/jsons'
    return response


@configure_bp.route('/configureformfile/<builder>/<node>/<file>')
def update_configure_file(builder, node, file):
    try:
        graph = read_node_link_json(f'data/{builder}/conf.json')
        form = DynamicFormMakeMeshConf(graph, node=node, file=file)

        choices = {
            "file": list(zip(form.file.choices, form.file.choices)),
            "category": list(zip(form.category.choices, form.category.choices))
        }

        response = make_response(json.dumps(choices))
    except Exception as e:
        print(e)
        response = make_response(json.dumps({}))
    response.content_type = 'application/jsons'
    return response


@configure_bp.route('/checkmd5/<builder_name>/')
def check_md5(builder_name):
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    monset = set()
    id_folder = {}
    for k, v in graph.nodes.items():
        monset.update(v.get("files"))

    di = {}
    for json_file in list(monset):
        with open(f"data/{builder_name}/{json_file}", "r") as f:
            json_file = json.load(f)
            for v in json_file.values():
                for mesh in v['stl'].values():
                    try:
                        di[mesh.get('md5')] = v.get('desc').get('path') + mesh.get('file')
                    except Exception as e:
                        pass
                    if mesh.get('support'):
                        di[mesh.get('support').get('md5')] = v.get('desc').get('path') + 'support/' + mesh.get('support').get('file')

    # TODO file has md5 in conf, but name of file added is from another file

    for file in os.listdir(f'data/{builder_name}/uploaded'):
        try:
            hash = tm.load(f"data/{builder_name}/uploaded/{file}").identifier_md5
        except Exception as e:
            print(e)
            continue
        if di.get(hash):
            if not os.path.exists(pathlib.Path(di.get(hash)).parent):
                pathlib.Path(di.get(hash)).parent.mkdir(parents=True)
            print(f"{file} already have a configuration ! {hash}")
            try:
                shutil.move(
                    f"data/{builder_name}/uploaded/{file}", di.get(hash))
                print(f"data/{builder_name}/uploaded/{file} moved to {di.get(hash)} !")
            except Exception as e:
                print(e)
                os.remove(f"data/{builder_name}/uploaded/{file}")
                print(f'data/{builder_name}/uploaded/{file} has been removed')

    response = make_response(json.dumps({}))
    response.content_type = 'application/jsons'
    return response
