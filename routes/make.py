import os
from functools import reduce
from math import radians
from operator import add
from pprint import pprint
import numpy as np
from flask import Blueprint, render_template, request, url_for, redirect, jsonify, flash, send_file
from markupsafe import Markup
from networkx import topological_sort, dfs_edges
from trimesh import load
from trimesh.transformations import euler_matrix
from utils.render import scene_to_html

from builder.node import read_node_link_json
from file_config.parts import load_json
from forms.home import ChooseBuilderForm
from forms.make import generateminidynamic_func
from utils.dict import deep_get
from utils.mesh import connect_mesh, get_mesh_normal_position
from utils.thingiverse import download_object
from utils.zip import write_zip

make_bp = Blueprint('make_bp', __name__)


@make_bp.context_processor
def utility_functions():
    def print_in_console(message):
        print(str(message))

    return dict(mdebug=print_in_console)


@make_bp.route('/', methods=['GET', 'POST'])
def choose_builder():
    form = ChooseBuilderForm()
    form.builder.choices = os.listdir('data')
    if request.method == 'POST':
        results = request.form.to_dict()
        return redirect(f"/builder/{results.get('builder')}")

    return render_template("choose_builder.html", form=form)


@make_bp.route('/builder/<builder_name>', methods=['GET', 'POST'])
def builder(builder_name):
    form_result = request.form.to_dict()
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    infos = {}
    for node_name in graph.nbunch_iter():
        infos[node_name] = {}
        for json_path in graph.nodes.get(node_name).get('files'):
            infos[node_name].update(load_json(f"data/{builder_name}/{json_path}"))
    designers = {}
    for file in graph.graph.get('designer_files', []):
        designers.update(load_json(f"data/{builder_name}/{file}"))

    di_form = {}
    li_position = []
    for node_name, v in graph.nodes.data():
        choices_values = list(infos[node_name].keys())

        di_form[node_name] = {
            'label': v.get('label'),
            'select':  infos[node_name].keys(),
            'choices': infos[node_name][form_result.get(f"{node_name}_select") or choices_values[0]]['stl'].keys()
        }
        li_position.append(v.get('position'))

    position_matrix = np.zeros(np.max(li_position, axis=0) + 1)
    shape_m = position_matrix.shape
    position_matrix = position_matrix.tolist()
    for i in range(shape_m[0]):
        for j in range(shape_m[1]):
            position_matrix[i][j] = {}

    form = generateminidynamic_func(**di_form)

    for k, v in graph.nodes.data():
        row_index, col_index = v.get('position')
        di_permission = {}
        for permission in v.get('permissions'):
            di_permission[permission] = getattr(form, f"{k}_{permission}")
        position_matrix[row_index][col_index] = di_permission
    if request.method == 'POST' and ('submit_preview' in form_result or 'dl_zip' in form_result or 'live_edit' in form_result):
        di_file = {}
        for node in topological_sort(graph):
            select = form_result.get(f'{node}_select')
            list_select = form_result.get(f'{node}_list')
            folder = graph.nodes.data()[node].get('folder')

            if select == 'Empty':
                continue

            di_file[node] = {
                'info': infos.get(node).get(select).get('stl').get(list_select),
                'on': folder,
                'dextral': graph.nodes.data()[node].get('dextral'),
                'rotate': form_result.get(f'{node}_rotate')
            }
            di_file[node]['info']['mesh_path'] = \
                f"data/{builder_name}/{folder}/{select}/{infos.get(node).get(select).get('stl').get(list_select).get('file')}"


        # DL MISSING FILES THINGIVERSE
        li_to_dl = []
        for node, mesh_infos_node in di_file.items():
            mesh_path = mesh_infos_node.get('info').get('mesh_path')
            if not os.path.isfile(mesh_path):
                flash(f"{mesh_path} is missing")
                li_to_dl.append(mesh_infos_node.get('info'))

        check_dl_li = []
        if li_to_dl and form_result.get('download_missing_file'):
            for to_dl in li_to_dl:
                if "thingiverse" in to_dl:
                    dl_good = download_object(to_dl.get('thingiverse'), to_dl.get('mesh_path'))
                    if dl_good:
                        flash(f"{to_dl.get('mesh_path')} has been download in Thingiverse !")
                    else:
                        flash(f"{to_dl.get('mesh_path')} has not been download in Thingiverse ! (something went wrong)")
                    check_dl_li.append(dl_good)
                else:
                    flash(f"{to_dl.get('mesh_path')} don't exist and have no web references !")
                    check_dl_li.append(False)
        if all(check_dl_li) and check_dl_li:
            return render_template("display.html",
                                    grid=position_matrix,
                                    submit=form.submit_preview,
                                    dl_missing=form.download_missing_file,
                                    dl_zip=form.dl_zip,
                                    live_edit=form.live_edit,)

        elif li_to_dl and not form_result.get('download_missing_file'):
            flash("Check field : <Download missing file> !")
            return render_template("display.html",
                                   grid=position_matrix,
                                   submit=form.submit_preview,
                                   dl_missing=form.download_missing_file,
                                   dl_zip=form.dl_zip,
                                   live_edit=form.live_edit,)
        # MESH PROCESSING
        li_designer = []
        designer_display = {}
        for k, v in di_file.items():
            mesh = load(v.get('info').get('mesh_path'))
            mesh.metadata['file_name'] = k
            di_file[k]['mesh'] = mesh
            if 'designer' in v.get('info'):
                designer_id = v.get('info').get('designer')
                li_designer.append(designer_id)
        for designer_id in set(li_designer):
            designer_display[designer_id] = designers.get(designer_id, {"name": f"@{designer_id}"})

        for edge in dfs_edges(graph):
            dest, source = edge
            try:
                if not (di_file.get(dest) and di_file.get(source)):
                    continue
                print(edge, di_file.get(source).get('rotate'), di_file.get(source)['info'], di_form)
                connect_mesh(di_file.get(source).get('mesh'),
                             di_file.get(dest).get('mesh'),
                             di_file.get(source).get('info'),
                             di_file.get(dest).get('info'),
                             on=di_file.get(source).get('on'),
                             dextral=di_file.get(source).get('dextral'),
                             rotate=int(di_file.get(source).get('rotate') or 0),
                             coef_merge=int(di_file.get(source).get('coef_merge') or 0),
                             monkey_rotate_child_fix=-int(di_file.get(dest).get('rotate') or 0))
            except Exception as e:
                meshconfhelper = Markup('change the vertex/facet/vertex_list file conf ! '
                                        '<a href="https://github.com/LeoGrosjean/MeshConfHelper" class="alert-link" target="_blank">'
                                        'How to fix'
                                        '</a>')
                if "dest" in str(e):
                    flash(f"an error occured on file: {di_file.get(dest).get('info').get('mesh_path')}")
                    flash(e)
                    flash(meshconfhelper)
                else:
                    flash(f"an error occured on file: {di_file.get(source).get('info').get('mesh_path')}")
                    flash(e)
                    flash(meshconfhelper)

                return render_template("display.html",
                                       grid=position_matrix,
                                       submit=form.submit_preview,
                                       dl_missing=form.download_missing_file,
                                       dl_zip=form.dl_zip,
                                       live_edit=form.live_edit,
                                       )
            # MERGE
            if 'dl_zip' in form_result:
                for k, v in graph.get_edge_data(dest, source).items():
                    if v.get('merge'):
                        di_file[dest]['mesh'] = di_file[dest]['mesh'] + di_file[source]['mesh']
                        tmp_path = f'tmp/merged_{dest}_{source}.stl'
                        di_file[dest]['mesh'].export(tmp_path)
                        di_file[dest]['info']['mesh_path'] = tmp_path
                        del di_file[source]

        if 'live_edit' in form_result:
            node_dict_rotate = {}
            for node_rotate in [k for k, v in graph.nodes.data() if 'rotate' in v.get('permissions')]:
                successors = list(graph.successors(node_rotate))
                if successors:
                    normal, vertice = get_mesh_normal_position(
                        di_file.get(node_rotate).get('mesh'),
                        di_file.get(node_rotate).get('info'),
                        di_file.get(node_rotate).get('on'))
                else:
                    predecessor = list(graph.predecessors(node_rotate))[0]
                    normal, vertice = get_mesh_normal_position(
                        di_file.get(predecessor).get('mesh'),
                        di_file.get(predecessor).get('info'),
                        di_file.get(node_rotate).get('on'), inverse_norm=True)
                node_dict_rotate[node_rotate] = {
                    'child_nodes': successors,
                    'normal': normal,
                    'vertice': vertice
                }
                print(vertice)
                print(normal)

            scene = reduce(add, [v.get('mesh').scene() for k, v in di_file.items()])
            from trimesh.scene.scene import append_scenes
            scene = append_scenes(scene)
            return render_template("display.html",
                                   grid=position_matrix,
                                   submit=form.submit_preview,
                                   dl_missing=form.download_missing_file,
                                   dl_zip=form.dl_zip,
                                   live_edit=form.live_edit,
                                   designers=designer_display,
                                   scene=scene_to_html(scene, node_dict_rotate),
                                   node_list=node_dict_rotate
                                   )

        scene = reduce(add, [v.get('mesh') for k, v in di_file.items()])
        scene.apply_transform(euler_matrix(radians(-90), 0, 0))

        if 'dl_zip' in form_result:
            li_file_path = [(v.get('info').get('mesh_path'), k) for k, v in di_file.items()]
            scene.export("tmp/merged.stl")
            li_file_path.append(('tmp/merged.stl', 'merged'))
            data = write_zip(li_file_path)

            # CLEAN
            for file in os.listdir('tmp'):
                os.remove(f"tmp/{file}")
            return send_file(data,
                             mimetype='application/zip',
                             as_attachment=True,
                             attachment_filename='data.zip')
        return render_template("display.html",
                               grid=position_matrix,
                               submit=form.submit_preview,
                               dl_missing=form.download_missing_file,
                               dl_zip=form.dl_zip,
                               live_edit=form.live_edit,
                               designers=designer_display,
                               scene=scene_to_html(scene.scene())
                               )


    return render_template("display.html",
                           grid=position_matrix,
                           submit=form.submit_preview,
                           dl_missing=form.download_missing_file,
                           dl_zip=form.dl_zip,
                           live_edit=form.live_edit)
