import json
import os
from functools import reduce
from math import radians
from operator import add
from pprint import pprint
from urllib.parse import urlparse

import numpy as np
from flask import Blueprint, render_template, request, url_for, redirect, jsonify, flash, send_file, make_response, \
    render_template_string
from markupsafe import Markup
from networkx import topological_sort, dfs_edges
from trimesh import load
from trimesh.geometry import align_vectors
from trimesh.transformations import euler_matrix

#from utils.cgtrader import download_cgt_file
#from utils.cults import download_cults_file
from wtforms import FieldList, FormField
from wtforms.validators import InputRequired

from utils.graph import get_successors
from utils.render import scene_to_html

from builder.node import read_node_link_json
from file_config.parts import load_json
from forms.home import ChooseBuilderForm
from forms.make import generateminidynamic_func, dynamic_BitzDisplay, dynamic_FieldBitz
from utils.dict import deep_get
from utils.mesh import connect_mesh, get_mesh_normal_position, rotate_mesh, scale_mesh, get_normal_vertice
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
    if request.method == 'POST':
        results = request.form.to_dict()
        if results.get('submit'):
            return redirect(f"/builder/{results.get('builder')}")
        elif results.get('add_files'):
            return redirect(f"/builder/{results.get('builder')}/configure")
        elif results.get('add_designers'):
            return redirect(f"/builder/{results.get('builder')}/designers")

    return render_template("choose_builder.html", form_header=form)


@make_bp.route('/builder/<builder_name>', methods=['GET', 'POST'])
def builder(builder_name):
    form_header = ChooseBuilderForm()
    form_header.builder.data = builder_name
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

    bitzs = {}
    for file in graph.graph.get('bitz_files', []):
        bitzs.update(load_json(f"data/{builder_name}/{file}"))

    di_form = {}
    li_position = []
    for node_name, v in graph.nodes.data():
        choices_values = list(infos[node_name].keys())

        di_form[node_name] = {
            'label': v.get('label'),
            'select':  infos[node_name].keys(),
            'choices': infos[node_name][form_result.get(f"{node_name}_select") or choices_values[0]]['stl'].keys(),
            'bitz_select': bitzs.keys(),
            'bitz_choices': bitzs[list(bitzs.keys())[0]]['stl'].keys()
        }

        li_position.append(v.get('position'))

    config_live_edit = {}

    position_matrix = []

    form = generateminidynamic_func(**di_form)

    if request.method == 'GET':
        for node_name, v in graph.nodes.data():
            choices_values = list(infos[node_name].keys())
            cur_cat = choices_values[0]
            curr_file_label = list(infos[node_name][cur_cat]['stl'].keys())[0]
            curr_file = infos[node_name][cur_cat]['stl'][curr_file_label]
            if curr_file.get('bitzs'):
                for bitz_name in curr_file.get('bitzs'):
                    bitz_form = getattr(form, f"{node_name}_bitz")
                    bitz_form.append_entry()
                    bitz_form.entries[-1].bitz_label.data = bitz_name

    for node in topological_sort(graph):
        di_permission = {}
        for permission in graph.nodes[node].get('permissions'):
            di_permission[permission] = getattr(form, f"{node}_{permission}")

        di_permission['builder_name'] = builder_name
        position_matrix.append(di_permission)

    if request.method == 'POST' and ('submit_preview' in form_result or 'dl_zip' in form_result or 'live_edit' in form_result):
        li_removed = []
        di_file = {}
        for node in topological_sort(graph):
            select = form_result.get(f'{node}_select')
            list_select = form_result.get(f'{node}_list')
            folder = graph.nodes.data()[node].get('folder')

            if select == 'Empty':
                li_removed.append(node)
                continue

            di_file[node] = {
                'info': infos.get(node).get(select).get('stl').get(list_select),
                'on': folder,
                'dextral': graph.nodes.data()[node].get('dextral'),
                'rotate': form_result.get(f'{node}_rotate'),
                'shake': form_result.get(f'{node}_shake'),
                'scale': form_result.get(f'{node}_scale'),
                'merge': form_result.get(f'{node}_merge'),
                'anklex': form_result.get(f'{node}_anklex'),
                'ankley': form_result.get(f'{node}_ankley'),
                'movex': form_result.get(f'{node}_movex'),
                'movey': form_result.get(f'{node}_movey'),
            }

            i = 0
            di_file[node]['bitzs'] = []
            while True:
                if f"{node}_bitz-{i}-bitz_label" in form_result:
                    category = form_result.get(f"{node}_bitz-{i}-bitz_select")
                    bitz_file_name = form_result.get(f"{node}_bitz-{i}-bitz_list")
                    if bitz_file_name == 'Empty':
                        i += 1
                        continue
                    bitz_name = form_result.get(f"{node}_bitz-{i}-bitz_label")

                    category_path = bitzs.get(category).get('desc').get('path')
                    file_path = bitzs.get(category).get('stl').get(bitz_file_name).get('file')

                    bitz_marker = bitzs.get(category).get('stl').get(bitz_file_name).get('bitz')

                    bitz_urls = bitzs.get(category).get('stl').get(bitz_file_name).get('urls')

                    bitz_designer = bitzs.get(category).get('stl').get(bitz_file_name).get('designer')

                    di_file[node]['bitzs'].append(
                        {
                            "path": category_path + file_path,
                            "label": bitz_name,
                            "mesh_marker": di_file[node]['info']['bitzs'].get(bitz_name),
                            "bitz_marker": bitz_marker,
                            "urls": bitz_urls,
                            "designer": bitz_designer,
                            "bitz_name": bitz_file_name,
                            "bitz_category": category
                        }
                    )
                    i += 1
                else:
                    break
            di_file[node]['info']['mesh_path'] = \
                f"data/{builder_name}/{folder}/{select}/{infos.get(node).get(select).get('stl').get(list_select).get('file')}"

        for k, v in di_file.items():
            if v.get('bitzs'):
                for i, bitz in enumerate(v.get('bitzs')):
                    bitz_form = getattr(form, f"{k}_bitz")
                    for entrie in bitz_form.entries:
                        if bitz.get('label') == entrie.bitz_label.data:
                            entrie.bitz_list.data = bitz.get('bitz_name')
                            entrie.bitz_list.choices = list(bitzs.get(bitz.get('bitz_category'))['stl'].keys())

        # remove mesh that has no parent connector

        for node_rotate in [k for k, v in graph.nodes.data()]:
            successors = list(graph.successors(node_rotate))
            predecessor = list(graph.predecessors(node_rotate))[0] if list(graph.predecessors(node_rotate)) else None

            if not di_file.get(node_rotate):
                continue

            if predecessor in li_removed:
                flash(
                    f"{node_rotate} wont be display because predecessor {predecessor} is set to Empty !")
                di_file.pop(node_rotate)
                li_removed.append(node_rotate)
                continue

            if di_file.get(predecessor):
                if not di_file.get(predecessor).get('info').get(di_file.get(node_rotate).get('on')):
                    flash(
                        f"{node_rotate} wont be display because {predecessor} don't have {di_file.get(node_rotate).get('on')} in his configuration, set it to Empty !")
                    di_file.pop(node_rotate)
                    li_removed.append(node_rotate)
                    continue
            elif predecessor in li_removed:
                flash(
                    f"{node_rotate} wont be display because {predecessor} don't have {di_file.get(node_rotate).get('on')} in his configuration, set it to Empty !")
                di_file.pop(node_rotate)
                li_removed.append(node_rotate)
                continue

        # CHECK MISSING FILES
        li_to_dl = []
        for node, mesh_infos_node in di_file.items():
            mesh_path = mesh_infos_node.get('info').get('mesh_path')
            if not os.path.isfile(mesh_path):
                li_to_dl.append(mesh_infos_node.get('info'))

            for bitz in mesh_infos_node.get('bitzs'):
                if not os.path.isfile(bitz.get("path")):
                    li_to_dl.append(bitz)

        check_dl_li = []
        if li_to_dl: #and form_result.get('download_missing_file'):
            for to_dl in li_to_dl:
                if to_dl.get('urls'):
                    message = ""
                    for url in to_dl.get('urls'):
                        message += f'<a href="{url}" target="_blank">{urlparse(url).netloc} </a><br>'
                    # TODO add proper file name for Bitz
                    flash(Markup(f"{to_dl.get('mesh_path', 'Bitz')} can be downloaded/buy there : <br>{message}<br>Then add them compressed or not !"))
                #if "thingiverse" in to_dl:
                #    dl_good = download_object(to_dl.get('thingiverse'), to_dl.get('mesh_path'))
                #    if dl_good:
                #        flash(f"{to_dl.get('mesh_path')} has been download in Thingiverse !")
                #    else:
                #        flash(f"{to_dl.get('mesh_path')} has not been download in Thingiverse ! (something went wrong)")
                #    check_dl_li.append(dl_good)
                #elif "cults3d" in to_dl:
                #    dl_good = download_cults_file(to_dl.get('cults3d'), to_dl.get('mesh_path'))
                #elif "cgtrader" in to_dl:
                #    dl_good = download_cgt_file(product_id=to_dl.get('cgtrader').get('product_id'),
                #                                product_name=to_dl.get('cgtrader').get('product_name'),
                #                                file_id=to_dl.get('cgtrader').get('file_id'),
                #                                dest_file=to_dl.get('mesh_path')
                #        , )"""
                else:
                    flash(f"{to_dl.get('mesh_path')} don't exist and have no web references !")
                    check_dl_li.append(False)
        if all(check_dl_li) and check_dl_li:
            return render_template("display.html",
                                    grid=position_matrix,
                                    submit=form.submit_preview,
                                    dl_missing=form.download_missing_file,
                                    dl_zip=form.dl_zip,
                                    live_edit=form.live_edit,
                                    form_header=form_header)

        elif li_to_dl and not form_result.get('download_missing_file'):
            #flash("Check field : <Download missing file> !")
            return render_template("display.html",
                                   grid=position_matrix,
                                   submit=form.submit_preview,
                                   dl_missing=form.download_missing_file,
                                   dl_zip=form.dl_zip,
                                   live_edit=form.live_edit,
                                   form_header=form_header)
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

            for i, bitz in enumerate(di_file[k].get('bitzs')):
                mesh = load(bitz.get('path'))
                mesh.metadata['file_name'] = f"{k}_bitz_{bitz.get('label')}"
                di_file[k]['bitzs'][i]['mesh'] = mesh
                li_designer.append(bitz.get('designer'))

        for designer_id in set(li_designer):
            designer_display[designer_id] = designers.get(designer_id, {"name": f"@{designer_id}"})

        # TODO scale bitz
        for node in di_file.keys():
            scale_mesh(di_file.get(node).get('mesh'),
                       (di_file.get(node).get('info').get('scale') or 1) * (float(di_file.get(node).get('scale') or 1)))

        for edge in dfs_edges(graph):
            dest, source = edge
            try:
                if not (di_file.get(dest) and di_file.get(source)):
                    continue

                if di_file.get(dest).get('info').get(graph.nodes[source].get('folder')):

                    if 'submit_preview' in form_result or 'dl_zip' in form_result:
                        connect_mesh(di_file.get(source).get('mesh'),
                                     di_file.get(dest).get('mesh'),
                                     di_file.get(source).get('info'),
                                     di_file.get(dest).get('info'),
                                     on=di_file.get(source).get('on'),
                                     dextral=di_file.get(source).get('dextral'),
                                     rotate=int(di_file.get(source).get('rotate') or 0),
                                     coef_merge=float(di_file.get(source).get('merge') or 0),
                                     monkey_rotate_child_fix=-int(di_file.get(dest).get('rotate') or 0),
                                     shake_rotate=int(di_file.get(source).get('shake') or 0),
                                     scale=di_file.get(source).get('info').get('scale'),
                                     move_x=float(di_file.get(source).get('movex') or 0),
                                     move_y=float(di_file.get(source).get('movey') or 0),)

                    elif 'live_edit' in form_result:
                        connect_mesh(di_file.get(source).get('mesh'),
                                     di_file.get(dest).get('mesh'),
                                     di_file.get(source).get('info'),
                                     di_file.get(dest).get('info'),
                                     on=di_file.get(source).get('on'),
                                     dextral=di_file.get(source).get('dextral'),
                                     rotate=0,
                                     coef_merge=0,
                                     scale=di_file.get(source).get('info').get('scale'),
                                     move_x=0,
                                     move_y=0)

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
                                       form_header=form_header
                                       )
        for node, info in di_file.items():
            for bitz in info.get('bitzs'):
                mesh_normal, mesh_vertice = get_normal_vertice(info.get('mesh'), bitz.get('mesh_marker'))
                bitz_normal, bitz_vertice = get_normal_vertice(bitz.get('mesh'), bitz.get('bitz_marker'))
                bitz.get('mesh').apply_transform(align_vectors(bitz_normal, mesh_normal * -1))
                mesh_normal, mesh_vertice = get_normal_vertice(info.get('mesh'), bitz.get('mesh_marker'))
                bitz_normal, bitz_vertice = get_normal_vertice(bitz.get('mesh'), bitz.get('bitz_marker'))
                bitz.get('mesh').apply_translation(mesh_vertice - bitz_vertice)
                print()
        #get_normal_vertice(mesh, marker)

        # MERGE

        for edge in list(dfs_edges(graph))[::-1]:
            dest, source = edge
            child_to_rotate = []
            if not di_file.get(source):
                continue
            for child in get_successors(graph, source):
                if not di_file.get(child):
                    continue
                child_to_rotate.append(child)

            if 'submit_preview' in form_result or 'dl_zip' in form_result:
                rotate_mesh(di_file.get(source).get('mesh'),
                            di_file.get(source).get('info'),
                            on=di_file.get(source).get('on'),
                            #monkey_rotate_child_fix=-int(di_file.get(dest).get('rotate') or 0),
                            #shake_rotate=int(di_file.get(source).get('shake') or 0),
                            rotate=float(di_file.get(source).get('rotate') or 0),
                            child_rotate=child_to_rotate,
                            info=di_file,
                            anklex=float(di_file.get(source).get('anklex') or 0),
                            ankley=float(di_file.get(source).get('ankley') or 0),
                            )
            elif 'live_edit' in form_result:
                config_live_edit[source] = {
                    "rotate": int(di_file.get(source).get('rotate') or 0),
                    "merge": float(di_file.get(source).get('merge') or 0),
                    "move_x": float(di_file.get(source).get('movex') or 0),
                    "move_y": float(di_file.get(source).get('movey') or 0),
                    "anklex": float(di_file.get(source).get('anklex') or 0),
                    "ankley": float(di_file.get(source).get('ankley') or 0)
                }

            if 'dl_zip' in form_result:
                for k, v in graph.get_edge_data(dest, source).items():
                    if v.get('merge'):
                        di_file[dest]['mesh'] = di_file[dest]['mesh'] + di_file[source]['mesh']
                        tmp_path = f'tmp/dl/merged_{dest}_{source}.' + str((di_file[dest]['mesh']._kwargs.get('file_type') or 'stl'))
                        di_file[dest]['mesh'].export(tmp_path)
                        di_file[dest]['info']['mesh_path'] = tmp_path
                        del di_file[source]

        for k, v in di_file.items():
            v.get('mesh').apply_transform(euler_matrix(radians(-90), 0, 0))
            for bitz in v.get('bitzs'):
                bitz.get('mesh').apply_transform(euler_matrix(radians(-90), 0, 0))

        if 'live_edit' in form_result:
            node_dict_rotate = {}
            for node_rotate in [k for k, v in graph.nodes.data()]:
                successors = list(graph.successors(node_rotate))
                predecessor = list(graph.predecessors(node_rotate))[0] if list(graph.predecessors(node_rotate)) else None

                if not di_file.get(node_rotate):
                    continue

                if successors and predecessor:
                    normal, vertice, normal_x, normal_y = get_mesh_normal_position(
                        di_file.get(node_rotate).get('mesh'),
                        di_file.get(node_rotate).get('info'),
                        di_file.get(node_rotate).get('on'))

                elif predecessor:
                    normal, vertice, normal_x, normal_y = get_mesh_normal_position(
                        di_file.get(predecessor).get('mesh'),
                        di_file.get(predecessor).get('info'),
                        di_file.get(node_rotate).get('on'), inverse_norm=True)

                if successors:
                    for successor in successors:
                        if not di_file.get(successor):
                            successors.remove(successor)
                if predecessor:
                    node_dict_rotate[node_rotate] = {
                        'child_nodes': successors,
                        'normal': normal,
                        'vertice': vertice,
                        "normal_x": normal_x,
                        "normal_y": normal_y
                    }
                else:
                    node_dict_rotate[node_rotate] = {
                        'child_nodes': successors,
                    }

            #scene = reduce(add, [v.get('mesh').scene() for k, v in di_file.items()])
            from trimesh import Scene

            scene = Scene()
            for k, v in di_file.items():
                if list(graph.predecessors(k)):
                    parent_node = list(graph.predecessors(k))[0]
                else:
                    parent_node = None

                for bitz in v.get('bitzs'):
                    scene.add_geometry(bitz.get('mesh'), bitz.get('label'), parent_node_name=k)

                scene.add_geometry(v.get('mesh'), k, parent_node_name=parent_node)

            #from trimesh.scene.scene import append_scenes
            #scene = append_scenes(scene)
            return render_template("display.html",
                                   grid=position_matrix,
                                   submit=form.submit_preview,
                                   dl_missing=form.download_missing_file,
                                   dl_zip=form.dl_zip,
                                   live_edit=form.live_edit,
                                   designers=designer_display,
                                   scene=scene_to_html(scene, node_dict_rotate, config_live_edit),
                                   node_list=node_dict_rotate,
                                   form_header=form_header,
                                   )

        merge_mesh = [v.get('mesh') for k, v in di_file.items()]

        for k, v in di_file.items():
            for bitz in v.get('bitzs'):
                merge_mesh.append([bitz.get('mesh')])

        scene = reduce(add, merge_mesh)

        if 'dl_zip' in form_result:
            li_file_path = [(v.get('info').get('mesh_path'), k) for k, v in di_file.items()]
            for k, v in di_file.items():
                # TODO what if merged, dont add merged files ? because we remove node from di_file when merge True
                if v.get('info').get('support'):
                    li_file_path.append(
                        (
                            v.get('info').get('mesh_path').replace(v.get('info').get('file'), f"support/{v.get('info').get('support').get('file')}"),
                            k + "_support"
                        )
                    )
            scene.export("tmp/dl/merged.stl")
            li_file_path.append(('tmp/dl/merged.stl', 'merged'))
            data = write_zip(li_file_path)

            # CLEAN
            for file in os.listdir('tmp/dl'):
                os.remove(f"tmp/dl/{file}")
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
                               scene=scene_to_html(scene.scene()),
                               form_header=form_header
                               )

    return render_template("display.html",
                           grid=position_matrix,
                           submit=form.submit_preview,
                           dl_missing=form.download_missing_file,
                           dl_zip=form.dl_zip,
                           live_edit=form.live_edit,
                           form_header=form_header)


@make_bp.route('/selectform/<node>/<selection>/<builder>')
def updateselect(node, selection, builder):
    builder_name = builder
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    infos = {}
    for node_name in graph.nbunch_iter():
        infos[node_name] = {}
        for json_path in graph.nodes.get(node_name).get('files'):
            infos[node_name].update(load_json(f"data/{builder_name}/{json_path}"))
    designers = {}
    for file in graph.graph.get('designer_files', []):
        designers.update(load_json(f"data/{builder_name}/{file}"))

    choices = list(infos[node.split('_')[0]][selection]['stl'].keys())
    choices = list(zip(choices, choices))
    response = make_response(json.dumps(choices))
    response.content_type = 'application/jsons'
    return response


@make_bp.route('/selectformbitz/bitz/<selection>/<builder>')
def updateselectbitz(selection, builder):
    builder_name = builder
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    bitz_infos = {}
    for bitz_file in graph.graph.get('bitz_files', []):
        bitz_infos.update(load_json(f"data/{builder_name}/{bitz_file}"))

    choices = list(bitz_infos[selection]['stl'].keys())
    choices = list(zip(choices, choices))
    response = make_response(json.dumps(choices))
    response.content_type = 'application/jsons'
    return response


jinja_string = """
{% macro change_bitz_choice(bitz_field) %}
<script>
    let select_field_{{bitz_field.id.replace('-', '_')}} = document.getElementById("{{bitz_field.id}}")
    let choice_field_{{bitz_field.id.replace('-', '_')}} = document.getElementById("{{bitz_field.id.replace('-bitz_select', '-bitz_list')}}")

    select_field_{{bitz_field.id.replace('-', '_')}}.onchange = function () {
        selection = select_field_{{bitz_field.id.replace('-', '_')}}.value;

        fetch("/selectformbitz/bitz/" + selection + "/" + "{{builder}}").then(function (response) {
            response.json().then(function (data) {
                let optionHTML = '';
                for (choice in data) {
                    optionHTML += '<option value="' + data[choice][0] + '">' + data[choice][1] + '</option>';
                }
                choice_field_{{bitz_field.id.replace('-', '_')}}.innerHTML = optionHTML
            })
        })

    }
</script>

{% endmacro %}
<div id="{{form.id}}">
    {% for bitz_form in form %}
        
        {{ bitz_form.bitz_label }}
        <p class="bg-light" style="z-index:1;">
            {{ bitz_form.bitz_label.data }} {{ bitz_form.bitz_select }} {{ bitz_form.bitz_list }}
            {{change_bitz_choice(bitz_form.bitz_select)}}
        </p>
    {% endfor %}
 </div>
"""


@make_bp.route('/selectformbitz/bitz/<builder>/<node>/<category>/<selection>/')
def updatebitz(builder, node, category, selection):
    builder_name = builder
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    infos = {}
    for json_file in graph.nodes[node].get('files'):
        infos.update(load_json(f"data/{builder_name}/{json_file}"))

    bitzs = {}
    for bitz_json_file in graph.graph.get('bitz_files', []):
        bitzs.update(load_json(f"data/{builder_name}/{bitz_json_file}"))

    form = dynamic_FieldBitz(node=node, bitzs=bitzs)()

    curr_file = infos[category]['stl'][selection]
    if curr_file.get('bitzs'):
        for bitz_name in curr_file.get('bitzs'):
            bitz_form = getattr(form, f"{node}_bitz")
            bitz_form.append_entry()
            bitz_form.entries[-1].bitz_label.data = bitz_name

    return render_template_string(jinja_string, form=getattr(form, f"{node}_bitz"), builder=builder)
