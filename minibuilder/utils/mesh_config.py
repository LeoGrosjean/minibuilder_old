import json
from ast import literal_eval
from pathlib import Path

import numpy as np

from minibuilder.file_config.parts import load_json


def find_vertices(mesh, *args):
    li = []

    if len(args[0]) == 3:
        for i, (x, y, z) in enumerate(mesh.vertices):
            for value in args:
                check = np.array(value) - np.array([x, y, z])
                if (-10e-04 < check).all() and (check < 10e-04).all():
                    li.append(i)
        if len(li) == 1:
            return {"vertex": li[0]}
        else:
            return {"vertex_list": li}

    elif isinstance(args[0][0], dict):
        return args[0][0]

    elif args[0][0].startswith("'face'"):
        return literal_eval("{" + args[0][0] + "}")

    elif args[0][0].startswith("'plan'"):
        for i, facet in enumerate(mesh.facets):
            if int(args[0][0].split(':')[-1]) in facet:
                return {"facet": i}
        print('Marker is not on face but on facet')
        return literal_eval("{" + args[0][0].replace('plan', 'face') + "}")



def find_mesh_connector(mesh, graph, form_result, mesh_info):
    if form_result.get('marker_bitz'):
        mesh_info[form_result.get('file_name')]['bitz'] = find_vertices(mesh, *literal_eval(f"[[{form_result.get('marker_bitz')}]]"))
    else:
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

    return mesh_info


def save_file_config_json(graph, data_folder, builder_name, conf_json, form_result, mesh_info):
    if form_result.get('marker_bitz'):
        folder = 'bitz'
    else:
        folder = graph.nodes[form_result.get('node')]['folder']

    try:
        conf = load_json(f"{data_folder}/{builder_name}/configuration/{conf_json}")
        if conf.get(form_result.get('category')):
            if conf[form_result.get('category')]['stl'].get(form_result.get('file_name')):
                conf[form_result.get('category')]['stl'][form_result.get('file_name')].update(mesh_info[form_result.get('file_name')])
            else:
                conf[form_result.get('category')]['stl'].update(mesh_info)
            print(f"{data_folder}/{builder_name}/configuration/{conf_json} has been updated !")
        else:
            conf[form_result.get('category')] = {
                "desc": {
                    "display": form_result.get('category'),
                    "path": f"{builder_name}/{folder}/{form_result.get('category')}/"
                },
                "stl": mesh_info
                }

            print(f"{data_folder}/{builder_name}/configuration/{conf_json} has been updated with {form_result.get('category')}!")
            if folder == 'bitz':
                conf[form_result.get('category')]["desc"]['bitz'] = True

    except Exception as e:
        print(e)
        conf = {
            form_result.get('category'): {
                "desc": {
                    "display": form_result.get('category'),
                    "path": f"{builder_name}/{folder}/{form_result.get('category')}/"
                },
                "stl": mesh_info
                }
            }
        if folder == 'bitz':
            conf[form_result.get('category')]["desc"]['bitz'] = True
        print(f"{data_folder}/{builder_name}/configuration/{conf_json} has been created with {form_result.get('category')}!")

        with open(f"{data_folder}/{builder_name}/configuration/conf.json", "r+") as node_file:

            data = json.load(node_file)
            if folder == 'bitz':
                data['graph']['bitz_files'].append(conf_json)
                print(f"{conf_json} added to bitz_files !")
            else:
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
    json_file_path = f"{data_folder}/{builder_name}/configuration/{conf_json}"
    json_file_path = Path(json_file_path.replace('.', '/', json_file_path.count('.') - 1))
    json_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(json_file_path), "w") as outfile:
        json.dump(conf, outfile, indent=4)
