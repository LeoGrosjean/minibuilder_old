import json
import os
import pathlib
import shutil
from configparser import ConfigParser
from uuid import uuid4

from flask import Blueprint, render_template, request, url_for, redirect, make_response
import trimesh as tm
from trimesh.exchange.load import mesh_formats
from werkzeug.utils import secure_filename

from minibuilder.builder.node import read_node_link_json
from minibuilder.config import configpath
from minibuilder.forms.configure import DynamicFormMakeMeshConf, FormUploadFile
from minibuilder.forms.home import ChooseBuilderForm, get_data_folder

from minibuilder.utils.compressed import extract_nested_compress
from minibuilder.utils.mesh_config import find_mesh_connector, save_file_config_json

mesh_suffixes = mesh_formats()

configure_bp = Blueprint('configure_bp', __name__)


@configure_bp.route('/builder/<builder>/configure', methods=['GET'])
def builder_configure(builder):
    form_header = ChooseBuilderForm()
    builders = os.listdir(get_data_folder())
    if not builders:
        return redirect(url_for('home_bp.list_builder_config'))
    form_header.builder.choices = builders
    form_header.builder.data = builder

    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    graph = read_node_link_json(f'{configuration_folder}/conf.json')

    if not os.path.exists(f'{data_folder}/{builder}/uploaded/'):
        pathlib.Path(f'{data_folder}/{builder}/uploaded/').mkdir(parents=True)

    try:
        form = DynamicFormMakeMeshConf(graph)
    except Exception as e:
        print(e)
        print('You should download configuration files')
        return redirect(url_for('home_bp.list_builder_config'))

    form_upload = FormUploadFile()
    is_bitz = ['bitz'] if graph.graph.get('bitz_files') else []
    return render_template("configure.html",
                           form=form,
                           nodes=list(graph.nodes) + is_bitz,
                           form_upload=form_upload,
                           builder=builder,
                           form_header=form_header)


@configure_bp.route('/builder/<builder>/configure', methods=['POST'])
def builder_post(builder):

    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    form_upload = FormUploadFile()
    form_header = ChooseBuilderForm()
    builders = os.listdir(get_data_folder())
    if not builders:
        return redirect(url_for('home_bp.list_builder_config'))
    form_header.builder.choices = builders

    form_header.builder.data = builder
    if form_upload.validate_on_submit():
        files_filenames = []
        for file in form_upload.files.data:
            file_filename = secure_filename(file.filename)
            file.save(f"{data_folder}/{builder}/uploaded/{file_filename}")
            # TODO check if compress and flatten them in uploaded
            extract_nested_compress(builder, file_filename)
            for file in os.listdir(f"{data_folder}/{builder}/uploaded/"):
                try:
                    if not pathlib.Path(file).suffix[1:].lower() in mesh_suffixes:
                        os.remove(f"{data_folder}/{builder}/uploaded/{file}")
                except Exception as e:
                    print(e)
        return redirect(url_for("configure_bp.builder_post", builder=builder))

    graph = read_node_link_json(f'{configuration_folder}/conf.json')
    form_result = request.form.to_dict()

    conf_json = form_result.get('file')
    mesh = tm.load(f"{data_folder}/{builder}/uploaded/{form_result.get('mesh_file')}")

    if form_result.get('url').startswith('http'):
        url = form_result.get('url')
    else:
        url = "https://" + form_result.get('url')

    mesh_info = {
        form_result.get('file_name'): {
            "file": form_result.get("mesh_file"),
            "designer": form_result.get('designer'),
            "md5": tm.load(f"{data_folder}/{builder}/uploaded/{form_result.get('mesh_file')}").identifier_md5,
            "urls": [url]
        }
    }
    if form_result.get('support'):
        mesh_info[form_result.get('file_name')]['support'] = {
            "file": form_result.get('support'),
            "md5": tm.load(f"{data_folder}/{builder}/uploaded/{form_result.get('support')}").identifier_md5
        }

    mesh_info = find_mesh_connector(mesh, graph, form_result, mesh_info)
    del mesh

    save_file_config_json(graph, data_folder, builder, conf_json, form_result, mesh_info)

    # file:
    # TODO if file_name already exist (and is different assuming check md5 has been done) it will add uuid in file_name not in file conf

    if form_result.get('marker_bitz'):
        folder = 'bitz'
    else:
        folder = graph.nodes[form_result.get('node')]['folder']

    try:
        if not os.path.exists(f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/"):
            pathlib.Path(f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/").mkdir(
                parents=True)
        if form_result.get('mesh_file') in os.listdir(
                f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/"):
            shutil.move(
                f"{data_folder}/{builder}/uploaded/{form_result.get('mesh_file')}",
                f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/"
                f"{uuid4()}_{form_result.get('mesh_file')}")
            print(f"{data_folder}/{builder}/uploaded/{form_result.get('mesh_file')} moved to "
                  f"{data_folder}/{builder}/{folder}/{form_result.get('category')} !")
        else:
            shutil.move(
                f"{data_folder}/{builder}/uploaded/{form_result.get('mesh_file')}",
                f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/")
            print(f"{data_folder}/{builder}/uploaded/{form_result.get('mesh_file')} moved to "
                  f"{data_folder}/{builder}/{folder}/{form_result.get('category')} !")
    except FileExistsError as e:
        print(e)
    # support
    if form_result.get('support'):
        try:
            if not os.path.exists(f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support/"):
                pathlib.Path(f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support/").mkdir(parents=True)
            if form_result.get('support') in os.listdir(
                    f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support/"):
                shutil.move(
                    f"{data_folder}/{builder}/uploaded/{form_result.get('support')}",
                    f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support/"
                    f"{uuid4()}_{form_result.get('support')}")
                print(f"{data_folder}/{builder}/uploaded/{form_result.get('support')} moved to "
                      f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support !")
            else:
                shutil.move(
                    f"{data_folder}/{builder}/uploaded/{form_result.get('support')}",
                    f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support/")
                print(f"{data_folder}/{builder}/uploaded/{form_result.get('support')} moved to "
                      f"{data_folder}/{builder}/{folder}/{form_result.get('category')}/support !")
        except Exception as e:
            print(e)

    form = DynamicFormMakeMeshConf(graph, **form_result)
    is_bitz = ['bitz'] if graph.graph.get('bitz_files') else []
    return render_template("configure.html",
                           form=form,
                           nodes=list(graph.nodes) + is_bitz,
                           form_upload=form_upload,
                           builder=builder,
                           form_header=form_header
                           )


@configure_bp.route('/send/<builder>/<file>/', methods=['GET', 'POST'])
def send(builder, file):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"
    try:
        mesh = tm.load(f"{data_folder}/{builder}/uploaded/{file}")
    except Exception as e:
        print(e)
        return ""
    return mesh.export(file_type='stl')


@configure_bp.route('/configureformnode/<builder>/<node>/')
def update_configure_node(builder, node):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    graph = read_node_link_json(f'{configuration_folder}/conf.json')

    form = DynamicFormMakeMeshConf(graph, node=node)
    is_bitz = ['bitz'] if graph.graph.get('bitz_files') else []
    choices = {
        "file": list(zip(form.file.choices, form.file.choices)),
        "category": list(zip(form.category.choices, form.category.choices)),
        "all_connections": list(graph.nodes) + is_bitz,
        "connection": list(form.connectors)
    }

    response = make_response(json.dumps(choices))
    response.content_type = 'application/jsons'
    return response


@configure_bp.route('/configureformfile/<builder>/<node>/<file>')
def update_configure_file(builder, node, file):
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    try:
        graph = read_node_link_json(f'{configuration_folder}/conf.json')
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


@configure_bp.route('/checkmd5/<builder>/')
def check_md5(builder):
    print('starting MD5 check')
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    configuration_folder = f"{data_folder}/{builder}/configuration"

    graph = read_node_link_json(f'{configuration_folder}/conf.json')
    monset = set()
    id_folder = {}
    for k, v in graph.nodes.items():
        monset.update(v.get("files"))

    monset.update(graph.graph.get('bitz_files', []))

    di = {}
    for json_file in list(monset):
        json_file = json_file.replace('.', '/', json_file.count('.') - 1)
        with open(f"{configuration_folder}/{json_file}", "r") as f:
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

    for file in os.listdir(f'{data_folder}/{builder}/uploaded'):
        try:
            hash = tm.load(f"{data_folder}/{builder}/uploaded/{file}").identifier_md5
        except Exception as e:
            print(e)
            continue
        if di.get(hash):
            if not os.path.exists(pathlib.Path(di.get(hash)).parent):
                pathlib.Path(f"{data_folder}/{di.get(hash)}").parent.mkdir(parents=True, exist_ok=True)
            print(f"{file} already have a configuration ! {hash}")
            try:

                shutil.move(
                    f"{data_folder}/{builder}/uploaded/{file}", f"{data_folder}/{di.get(hash)}")
                print(f"{data_folder}/{builder}/uploaded/{file} moved to {data_folder}/{di.get(hash)} !")
            except Exception as e:
                print(e)
                os.remove(f"{data_folder}/{builder}/uploaded/{file}")
                print(f'{data_folder}/{builder}/uploaded/{file} has been removed')

    response = make_response(json.dumps({}))
    response.content_type = 'application/jsons'
    print('ending MD5 check')
    return response
