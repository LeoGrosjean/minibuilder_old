from math import radians
import numpy as np
import trimesh as tm


def get_center_facet_index(mesh_, index_):
    li = []
    for iface in mesh_.facets[index_]:
        # min_face = np.min(mesh_.vertices[mesh_.faces[iface]], axis=0)
        # max_face = np.max(mesh_.vertices[mesh_.faces[iface]], axis=0)
        li.extend(mesh_.vertices[mesh_.faces[iface]])
    return np.mean(li, axis=0)


def get_mean_vertex_list(mesh_, list_index):
    return np.mean(mesh_.vertices[list_index], axis=0)


def get_mean_vertex_normal_list(mesh_, list_index):
    return np.mean(mesh_.vertex_normals[list_index], axis=0) / np.linalg.norm(np.mean(mesh_.vertex_normals[list_index], axis=0))


def rotate_mesh(mesh, mesh_info, on, monkey_rotate_child_fix=0, shake_rotate=None, rotate=None, child_rotate=[],
                info=None, anklex=None, ankley=None):
    if "vertex" in mesh_info[on]:
        normal = mesh.vertex_normals[mesh_info[on]["vertex"]]
        vertice = mesh.vertices[mesh_info[on]["vertex"]]
    elif "facet" in mesh_info[on]:
        normal = mesh.facets_normal[mesh_info[on]["facet"]]
        vertice = get_center_facet_index(mesh, mesh_info[on]["facet"])
    elif "vertex_list" in mesh_info[on]:
        normal = get_mean_vertex_normal_list(mesh, mesh_info[on]["vertex_list"])
        vertice = get_mean_vertex_list(mesh, mesh_info[on]["vertex_list"])

    if rotate:
        mesh.apply_transform(tm.transformations.rotation_matrix(radians(rotate), normal, vertice))
        for child in child_rotate:
            info.get(child).get('mesh').apply_transform(tm.transformations.rotation_matrix(radians(rotate), normal, vertice))

    normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
    if np.isnan(normal_x[0]):
        normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))
    normal_x = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))
    normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))

    if anklex:
        mesh.apply_transform(tm.transformations.rotation_matrix(radians(anklex), normal_x, vertice))
        for child in child_rotate:
            info.get(child).get('mesh').apply_transform(tm.transformations.rotation_matrix(radians(anklex), normal_x, vertice))

    if ankley:

        mesh.apply_transform(tm.transformations.rotation_matrix(radians(ankley), normal_y, vertice))
        for child in child_rotate:
            info.get(child).get('mesh').apply_transform(tm.transformations.rotation_matrix(radians(ankley), normal_y, vertice))


def scale_mesh(mesh, scale):
    if scale:
        mesh.apply_scale(scale)


def connect_mesh(mesh, dest_mesh, mesh_info, dest_mesh_info, on, coef_merge=0, dextral=None, rotate=None, base_coef=1,
                 base=False, monkey_rotate_child_fix=0, shake_rotate=None, scale=None, move_x=0, move_y=0):
    rotate_neg = 1
    if dextral:
        if mesh_info['dextral'] != dextral:
            rotate_neg = -1
            mesh.apply_transform(tm.transformations.reflection_matrix([0, 0, 0], [0, 0, 1]))

    if scale:
        mesh.apply_scale(scale)

    try:
        if "vertex" in dest_mesh_info[on][dextral]:
            dest_normal = dest_mesh.vertex_normals[dest_mesh_info[on][dextral]["vertex"]]
            dest_vertice = dest_mesh.vertices[dest_mesh_info[on][dextral]["vertex"]]
        elif "facet" in dest_mesh_info[on][dextral]:
            dest_normal = dest_mesh.facets_normal[dest_mesh_info[on][dextral]["facet"]]
            dest_vertice = get_center_facet_index(dest_mesh, dest_mesh_info[on][dextral]["facet"])
        elif "vertex_list" in dest_mesh_info[on][dextral]:
            dest_normal = get_mean_vertex_normal_list(dest_mesh, dest_mesh_info[on][dextral]["vertex_list"])
            dest_vertice = get_mean_vertex_list(dest_mesh, dest_mesh_info[on][dextral]["vertex_list"])
    except Exception as e:
        print(e)
        if "vertex" in dest_mesh_info[on]:
            dest_normal = dest_mesh.vertex_normals[dest_mesh_info[on]["vertex"]]
            dest_vertice = dest_mesh.vertices[dest_mesh_info[on]["vertex"]]
        elif "facet" in dest_mesh_info[on]:
            dest_normal = dest_mesh.facets_normal[dest_mesh_info[on]["facet"]]
            dest_vertice = get_center_facet_index(dest_mesh, dest_mesh_info[on]["facet"])
        elif "vertex_list" in dest_mesh_info[on]:
            dest_normal = get_mean_vertex_normal_list(dest_mesh, dest_mesh_info[on]["vertex_list"])
            dest_vertice = get_mean_vertex_list(dest_mesh, dest_mesh_info[on]["vertex_list"])

    if "vertex" in mesh_info[on]:
        normal = mesh.vertex_normals[mesh_info[on]["vertex"]]
    elif "facet" in mesh_info[on]:
        normal = mesh.facets_normal[mesh_info[on]["facet"]]
    elif "vertex_list" in mesh_info[on]:
        normal = get_mean_vertex_normal_list(mesh, mesh_info[on]["vertex_list"])

    """if on == 'leg' and not base:
        normal = [0, 0, 1]
        dest_normal = np.array([0, 0, -1])"""
    mesh.apply_transform(tm.geometry.align_vectors(normal, dest_normal * -base_coef))

    if "vertex" in mesh_info[on]:
        vertice = mesh.vertices[mesh_info[on]["vertex"]]
    elif "facet" in mesh_info[on]:
        vertice = get_center_facet_index(mesh, mesh_info[on]["facet"])
    elif "vertex_list" in mesh_info[on]:
        vertice = get_mean_vertex_list(mesh, mesh_info[on]["vertex_list"])

    mesh.apply_translation(dest_vertice - vertice)

    if "vertex" in mesh_info[on]:
        normal = mesh.vertex_normals[mesh_info[on]["vertex"]]
        vertice = mesh.vertices[mesh_info[on]["vertex"]]
    elif "facet" in mesh_info[on]:
        normal = mesh.facets_normal[mesh_info[on]["facet"]]
        vertice = get_center_facet_index(mesh, mesh_info[on]["facet"])
    elif "vertex_list" in mesh_info[on]:
        normal = get_mean_vertex_normal_list(mesh, mesh_info[on]["vertex_list"])
        vertice = get_mean_vertex_list(mesh, mesh_info[on]["vertex_list"])

    mesh.apply_translation(normal * mesh_info.get('coef_merge', 0) + normal * coef_merge)

    if "rotate" in mesh_info:
        mesh.apply_transform(
            tm.transformations.rotation_matrix(radians(mesh_info['rotate'] * rotate_neg), normal, vertice))

    """if shake_rotate:
        normal_vec = [normal[0], normal[2], normal[1]]
        mesh.apply_transform(tm.transformations.rotation_matrix(radians(shake_rotate),
                                                                    normal_vec,
                                                                    vertice))

    if rotate:
        mesh.apply_transform(tm.transformations.rotation_matrix(radians(rotate), normal, vertice))

    mesh.apply_transform(tm.transformations.rotation_matrix(radians(-monkey_rotate_child_fix), normal, vertice))"""
    normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
    if np.isnan(normal_x[0]):
        print('x is nan')
        normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))
    normal_x = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))
    normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))

    mesh.apply_translation(normal_x * mesh_info.get('movex', 0) + normal_x * move_x +
                           normal_y * mesh_info.get('movey', 0) + normal_y * move_y)


def get_mesh_normal_position(mesh, info, on, inverse_norm=False):
    dextral = info.get('dextral')
    if dextral:
        if "vertex" in info[on]:
            normal = mesh.vertex_normals[info[on]["vertex"]]
            vertice = mesh.vertices[info[on]["vertex"]]
        elif "facet" in info[on]:
            normal = mesh.facets_normal[info[on]["facet"]]
            vertice = get_center_facet_index(mesh, info[on]["facet"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)
        elif "vertex_list" in info[on]:
            normal = get_mean_vertex_normal_list(mesh, info[on]["vertex_list"])
            vertice = get_mean_vertex_list(mesh, info[on]["vertex_list"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)
    else:
        if "vertex" in info[on]:
            normal = mesh.vertex_normals[info[on]["vertex"]]
            vertice = mesh.vertices[info[on]["vertex"]]
        elif "facet" in info[on]:
            normal = mesh.facets_normal[info[on]["facet"]]
            vertice = get_center_facet_index(mesh, info[on]["facet"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)
        elif "vertex_list" in info[on]:
            normal = get_mean_vertex_normal_list(mesh, info[on]["vertex_list"])
            vertice = get_mean_vertex_list(mesh, info[on]["vertex_list"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)

    if inverse_norm:
        normal = normal * -1

    normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
    if np.isnan(normal_x[0]):
        normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))
    normal_x = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))
    normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))

    normal = ','.join([str(x) for x in normal.tolist()])
    vertice = ','.join([str(x) for x in vertice.tolist()])
    normal_x = ','.join([str(x) for x in normal_x.tolist()])
    normal_y = ','.join([str(x) for x in normal_y.tolist()])

    return normal, vertice, normal_x, normal_y


def get_mesh_normal_position_edit(mesh, info, on, dextral=None, inverse_norm=False):
    if dextral:
        if "vertex" in info[on][dextral]:
            normal = mesh.vertex_normals[info[on][dextral]["vertex"]]
            vertice = mesh.vertices[info[on][dextral]["vertex"]]
        elif "facet" in info[on][dextral]:
            normal = mesh.facets_normal[info[on][dextral]["facet"]]
            vertice = get_center_facet_index(mesh, info[on][dextral]["facet"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)
        elif "vertex_list" in info[on][dextral]:
            normal = get_mean_vertex_normal_list(mesh, info[on][dextral]["vertex_list"])
            vertice = get_mean_vertex_list(mesh, info[on][dextral]["vertex_list"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)
    else:
        if "vertex" in info[on]:
            normal = mesh.vertex_normals[info[on]["vertex"]]
            vertice = mesh.vertices[info[on]["vertex"]]
        elif "facet" in info[on]:
            normal = mesh.facets_normal[info[on]["facet"]]
            vertice = get_center_facet_index(mesh, info[on]["facet"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)
        elif "vertex_list" in info[on]:
            normal = get_mean_vertex_normal_list(mesh, info[on]["vertex_list"])
            vertice = get_mean_vertex_list(mesh, info[on]["vertex_list"])
            try:
                if np.abs(sum(normal)) != 1:
                    normal /= np.abs(sum(normal))
            except Exception as e:
                print(e)

    if inverse_norm:
        normal = normal * -1

    normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
    if np.isnan(normal_x[0]):
        normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))
    normal_x = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))
    normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))

    normal = ','.join([str(x) for x in normal.tolist()])
    vertice = ','.join([str(x) for x in vertice.tolist()])
    normal_x = ','.join([str(x) for x in normal_x.tolist()])
    normal_y = ','.join([str(x) for x in normal_y.tolist()])

    return normal, vertice, normal_x, normal_y