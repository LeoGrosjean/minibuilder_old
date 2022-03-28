from networkx import topological_sort


def make_info(graph, builder, form_result, infos, bitzs, li_removed, data_folder):
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
        is_bitz = True
        while is_bitz:
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
                        "path": data_folder + '/' + category_path + file_path,
                        "label": bitz_name,
                        "mesh_marker": di_file[node]['info']['bitzs'].get(bitz_name),
                        "bitz_marker": bitz_marker,
                        "urls": bitz_urls,
                        "designer": bitz_designer,
                        "bitz_name": bitz_file_name,
                        "bitz_category": category,
                        "id_web": f"{node}_bitz-{i}",

                        "scale": float(form_result.get(f"{node}_bitz-{i}-bitz_scale", 1)),
                        "rotate": float(form_result.get(f"{node}_bitz-{i}-bitz_rotate", 0)),
                        "merge": float(form_result.get(f"{node}_bitz-{i}-bitz_merge", 0)),
                        "anklex": float(form_result.get(f"{node}_bitz-{i}-bitz_anklex", 0)),
                        "ankley": float(form_result.get(f"{node}_bitz-{i}-bitz_ankley", 0)),
                        "movex": float(form_result.get(f"{node}_bitz-{i}-bitz_movex", 0)),
                        "movey": float(form_result.get(f"{node}_bitz-{i}-bitz_movey", 0)),

                        "fusion": bool(form_result.get(f"{node}_bitz-{i}-bitz_fusion")),

                    }
                )
                i += 1
            else:
                is_bitz = False
        di_file[node]['info']['mesh_path'] = \
            f"{data_folder}/{builder}/{folder}/{select}/{infos.get(node).get(select).get('stl').get(list_select).get('file')}"

    return di_file