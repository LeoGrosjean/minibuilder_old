from trimesh import load


def load_meshes_find_designer(di_file, designers):
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
            mesh.metadata['file_name'] = bitz.get('id_web')
            di_file[k]['bitzs'][i]['mesh'] = mesh
            li_designer.append(bitz.get('designer'))

    for designer_id in set(li_designer):
        designer_display[designer_id] = designers.get(designer_id, {"name": f"@{designer_id}"})

    return designer_display