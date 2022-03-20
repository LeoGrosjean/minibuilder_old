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
    normal, vertice = get_normal_vertice(mesh, mesh_info[on])

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
        dest_normal, dest_vertice = get_normal_vertice(dest_mesh, dest_mesh_info[on][dextral])
    except Exception as e:
        print(e)
        dest_normal, dest_vertice = get_normal_vertice(dest_mesh, dest_mesh_info[on])

    normal, vertice = get_normal_vertice(mesh, mesh_info[on])

    """if on == 'leg' and not base:
        normal = [0, 0, 1]
        dest_normal = np.array([0, 0, -1])"""
    mesh.apply_transform(tm.geometry.align_vectors(normal, dest_normal * -base_coef))

    normal, vertice = get_normal_vertice(mesh, mesh_info[on])

    mesh.apply_translation(dest_vertice - vertice)

    normal, vertice = get_normal_vertice(mesh, mesh_info[on])

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


def get_mesh_normal_position(mesh, marker, inverse_norm=False):
    # TODO support dextral if a node with child and parent have two symmetric childrens
    normal, vertice = get_normal_vertice(mesh, marker)

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
        normal, vertice = get_normal_vertice(mesh, info[on][dextral])
    else:
        normal, vertice = get_normal_vertice(mesh, info[on])

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


def get_normal_vertice(mesh, marker):
    if "vertex" in marker:
        normal = mesh.vertex_normals[marker["vertex"]]
        vertice = mesh.vertices[marker["vertex"]]

    elif "facet" in marker:
        normal = mesh.facets_normal[marker["facet"]]
        vertice = get_center_facet_index(mesh, marker["facet"])

    elif "face" in marker:
        normal = mesh.face_normals[marker["face"]]
        vertice = np.mean(mesh.vertices[mesh.faces[marker["face"]]], axis=0)

    elif "vertex_list" in marker:
        normal = get_mean_vertex_normal_list(mesh, marker["vertex_list"])
        vertice = get_mean_vertex_list(mesh, marker["vertex_list"])

    try:
        if np.abs(sum(normal)) != 1:
            normal /= np.abs(sum(normal))
    except Exception as e:
        print(e)

    return normal, vertice