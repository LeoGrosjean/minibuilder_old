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
from trimesh.viewer import scene_to_html

from builder.node import read_node_link_json
from file_config.parts import load_json
from forms.home import ChooseBuilderForm
from forms.make import generateminidynamic_func
from utils.dict import deep_get
from utils.mesh import connect_mesh
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
        return redirect(f"/{results.get('builder')}")

    return render_template("choose_builder.html", form=form)


@make_bp.route('/<builder_name>', methods=['GET', 'POST'])
def builder(builder_name):
    form_result = request.form.to_dict()
    graph = read_node_link_json(f'data/{builder_name}/conf.json')
    infos = {}
    for node_name in graph.nbunch_iter():
        infos[node_name] = {}
        for json_path in graph.nodes.get(node_name).get('files'):
            infos[node_name].update(load_json(f"data/{builder_name}/{json_path}"))
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
    if request.method == 'POST' and ('submit_preview' in form_result or 'dl_zip' in form_result):
        di_file = {}
        for node in topological_sort(graph):
            select = form_result.get(f'{node}_select')
            list_select = form_result.get(f'{node}_list')
            folder = graph.nodes.data()[node].get('folder')

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

        cant_dl = False
        if li_to_dl and form_result.get('download_missing_file'):
            for to_dl in li_to_dl:
                if "thingiverse" in to_dl:
                    download_object(to_dl.get('thingiverse'), to_dl.get('mesh_path'))
                    flash(f"{to_dl.get('mesh_path')} has been download in Thingiverse !")
                else:
                    flash(f"{to_dl.get('mesh_path')} don't exist and have no web references !")
                    cant_dl = True
        if cant_dl:
            return render_template("display.html",
                                    grid=position_matrix,
                                    submit=form.submit_preview,
                                    dl_missing=form.download_missing_file,
                                    dl_zip=form.dl_zip)

        elif li_to_dl:
            flash("Check field : <Download missing file> !")
            return render_template("display.html",
                                   grid=position_matrix,
                                   submit=form.submit_preview,
                                   dl_missing=form.download_missing_file,
                                   dl_zip=form.dl_zip)
        # MESH PROCESSING
        for k, v in di_file.items():
            di_file[k]['mesh'] = load(v.get('info').get('mesh_path'))

        for edge in dfs_edges(graph):
            dest, source = edge
            try:
                print(di_file.get(source))
                print(di_file.get(dest))
                connect_mesh(di_file.get(source).get('mesh'),
                             di_file.get(dest).get('mesh'),
                             di_file.get(source).get('info'),
                             di_file.get(dest).get('info'),
                             on=di_file.get(source).get('on'),
                             dextral=di_file.get(source).get('dextral'),
                             rotate=int(di_file.get(source).get('rotate') or 0),
                             coef_merge=int(di_file.get(source).get('coef_merge') or 0))
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
                               scene=scene_to_html(scene.scene())
                               )
        #scene = [v.get('mesh').scene() for k, v in di_file.items()]
        #scene = reduce(add, [v.get('mesh').scene() for k, v in di_file.items()])
        #from trimesh.scene.scene import append_scenes
        #scene = append_scenes(scene)
        #return render_template("display.html",
        #                       grid=position_matrix,
        #                       submit=form.submit_preview,
        #                       dl_missing=form.download_missing_file,
        #                       scene=scene_to_html(scene)
        #                       )

    return render_template("display.html",
                           grid=position_matrix,
                           submit=form.submit_preview,
                           dl_missing=form.download_missing_file,
                           dl_zip=form.dl_zip)


def remove_me_soon():
    form = GenerateMini()
    print(form.larm_)
    print(request.remote_addr)
    if request.method == 'POST':
        results = request.form.to_dict()
        # print(results)
        form.backpack.choices = list(zip(backpacks[results.get('backpack_')]['stl'],
                                         backpacks[results.get('backpack_')]['stl']))
        form.head.choices = list(zip(heads[results.get('head_')]['stl'],
                                     heads[results.get('head_')]['stl']))
        form.rarm.choices = list(zip(arms[results.get('rarm_')]['stl'],
                                     arms[results.get('rarm_')]['stl']))
        form.larm.choices = list(zip(arms[results.get('larm_')]['stl'],
                                     arms[results.get('larm_')]['stl']))
        form.body.choices = list(zip(bodies[results.get('body_')]['stl'],
                                     bodies[results.get('body_')]['stl']))
        form.rhand.choices = list(zip(hands[results.get('rhand_')]['stl'],
                                      hands[results.get('rhand_')]['stl']))
        form.lhand.choices = list(zip(hands[results.get('lhand_')]['stl'],
                                      hands[results.get('lhand_')]['stl']))
        form.leg.choices = list(zip(legs[results.get('leg_')]['stl'],
                                    legs[results.get('leg_')]['stl']))

        if "submit_preview" in results:
            print(results)
            left_hand = deep_get(hands, f"{results.get('lhand_')}|stl|{results.get('lhand')}")
            right_hand = deep_get(hands, f"{results.get('rhand_')}|stl|{results.get('rhand')}")
            head = deep_get(heads, f"{results.get('head_')}|stl|{results.get('head')}")
            body = deep_get(bodies, f"{results.get('body_')}|stl|{results.get('body')}")
            right_arm = deep_get(arms, f"{results.get('rarm_')}|stl|{results.get('rarm')}")
            left_arm = deep_get(arms, f"{results.get('larm_')}|stl|{results.get('larm')}")
            leg = deep_get(legs, f"{results.get('leg_')}|stl|{results.get('leg')}")
            backpack = deep_get(backpacks, f"{results.get('backpack_')}|stl|{results.get('backpack')}")

            lhand_path = deep_get(hands, f"{results.get('lhand_')}|desc|path")
            rhand_path = deep_get(hands, f"{results.get('rhand_')}|desc|path")
            head_path = deep_get(heads, f"{results.get('head_')}|desc|path")
            body_path = deep_get(bodies, f"{results.get('body_')}|desc|path")
            rarm_path = deep_get(arms, f"{results.get('rarm_')}|desc|path")
            larm_path = deep_get(arms, f"{results.get('larm_')}|desc|path")
            leg_path = deep_get(legs, f"{results.get('leg_')}|desc|path")
            backpack_path = deep_get(backpacks, f"{results.get('backpack_')}|desc|path")

            import trimesh as tm

            mleft_hand_path = {"path": f"{lhand_path}{left_hand['file']}", "info": left_hand}
            mright_hand_path = {"path": f"{rhand_path}{right_hand['file']}", "info": right_hand}
            mhead_path = {"path": f"{head_path}{head['file']}", "info": head}
            mbody_path = {"path": f"{body_path}{body['file']}", "info": body}
            mright_arm_path = {"path": f"{rarm_path}{right_arm['file']}", "info": right_arm}
            mleft_arm_path = {"path": f"{larm_path}{left_arm['file']}", "info": left_arm}
            mleg_path = {"path": f"{leg_path}{leg['file']}", "info": leg}
            mbackpack_path = {"path": f"{backpack_path}{backpack['file']}", "info": backpack}

            li_to_dl = []
            for path_info in [mleft_hand_path, mright_hand_path, mhead_path, mbody_path, mright_arm_path, mleft_arm_path, mleg_path, mbackpack_path]:
                if not os.path.isfile(path_info.get('path')):
                    print(f"{path_info.get('path')} is missing")
                    li_to_dl.append((path_info))

            if li_to_dl and results.get('download_missing_file'):
                for to_dl in li_to_dl:
                    if "thingiverse" in to_dl.get('info'):
                        download_object(to_dl.get('info').get('thingiverse'), to_dl.get('path'))
            elif li_to_dl:
                print("Check Download missing file !")
                return render_template('minicreator.html', form=form, designers={})

            mleft_hand = tm.load(mleft_hand_path.get('path'))
            mright_hand = tm.load(mright_hand_path.get('path'))
            mhead = tm.load(mhead_path.get('path'))
            mbody = tm.load(mbody_path.get('path'))
            mright_arm = tm.load(mright_arm_path.get('path'))
            mleft_arm = tm.load(mleft_arm_path.get('path'))
            mleg = tm.load(mleg_path.get('path'))
            mbackpack = tm.load(mbackpack_path.get('path'))

            connect_mesh(mhead, mbody, head, body, on='head', rotate=0, coef_merge=-0.3)
            connect_mesh(mleft_arm, mbody, left_arm, body, on='arm', dextral='left',
                         rotate=int(results.get('larm_rotation')), coef_merge=0)
            connect_mesh(mright_arm, mbody, right_arm, body, on='arm', dextral='right',
                         rotate=int(results.get('rarm_rotation')), coef_merge=0)
            connect_mesh(mleft_hand, mleft_arm, left_hand, left_arm, on='hand', dextral='left',
                         rotate=int(results.get('lhand_rotation')), coef_merge=0)
            connect_mesh(mright_hand, mright_arm, right_hand, right_arm, on='hand', dextral='right',
                         rotate=int(results.get('rhand_rotation')),
                         coef_merge=0)
            connect_mesh(mleg, mbody, leg, body, on='leg', rotate=0, coef_merge=0)
            connect_mesh(mbackpack, mbody, backpack, body, on='backpack', rotate=0, coef_merge=0)

            scene = (mhead + mbody + mleft_arm + mright_arm + mleft_hand + mright_hand + mleg + mbackpack)
            scene.apply_transform(tm.transformations.euler_matrix(radians(-90), 0, 0))

            from trimesh.viewer import scene_to_html

            todo_designer = {
                "name": "designer will be added soon",
                "donation": "TODO",
                "web": {
                }
            }

            designer = {
                "Designer of left_hand": designers.get(left_hand.get('designer', 'Nop'), todo_designer),
                "Designer of right_hand": designers.get(right_hand.get('designer', 'Nop'), todo_designer),
                "Designer of head": designers.get(head.get('designer', 'Nop'), todo_designer),
                "Designer of body": designers.get(body.get('designer', 'Nop'), todo_designer),
                "Designer of right_arm": designers.get(right_arm.get('designer', 'Nop'), todo_designer),
                "Designer of left_arm": designers.get(left_arm.get('designer', 'Nop'), todo_designer),
                "Designer of leg": designers.get(leg.get('designer', 'Nop'), todo_designer),
                "Designer of backpack": designers.get(backpack.get('designer', 'Nop'), todo_designer),
            }
            return render_template('minicreator.html', form=form, test=scene_to_html(scene.scene()),
                                   designers=designer)

    return render_template('minicreator.html', form=form, designers={})