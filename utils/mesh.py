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
    return np.mean(mesh_.vertex_normals[list_index], axis=0)


def connect_mesh(mesh, dest_mesh, mesh_info, dest_mesh_info, on, coef_merge=0, dextral=None, rotate=None, base_coef=1,
                 base=False):
    rotate_neg = 1
    if dextral:
        if mesh_info['dextral'] != dextral:
            rotate_neg = -1
            mesh.apply_transform(tm.transformations.reflection_matrix([0, 0, 0], [0, 0, 1]))

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

    mesh.apply_translation(normal * mesh_info.get('coef_merge', coef_merge))

    if "rotate" in mesh_info:
        mesh.apply_transform(
            tm.transformations.rotation_matrix(radians(mesh_info['rotate'] * rotate_neg), normal, vertice))

    if rotate:
        mesh.apply_transform(tm.transformations.rotation_matrix(radians(rotate), normal, vertice))


def get_mesh_normal_position(mesh, info, on, inverse_norm=False):
    dextral = info.get(on).get('dextral')
    if dextral:
        if "vertex" in info[on][dextral]:
            normal = mesh.vertex_normals[info[on][dextral]["vertex"]]
            vertice = mesh.vertices[info[on][dextral]["vertex"]]
        elif "facet" in info[on][dextral]:
            normal = mesh.facets_normal[info[on][dextral]["facet"]]
            vertice = get_center_facet_index(mesh, info[on][dextral]["facet"])
        elif "vertex_list" in mesh[on][dextral]:
            normal = get_mean_vertex_normal_list(mesh, info[on][dextral]["vertex_list"])
            vertice = get_mean_vertex_list(mesh, info[on][dextral]["vertex_list"])
    else:
        if "vertex" in info[on]:
            normal = mesh.vertex_normals[info[on]["vertex"]]
            vertice = mesh.vertices[info[on]["vertex"]]
        elif "facet" in info[on]:
            normal = mesh.facets_normal[info[on]["facet"]]
            vertice = get_center_facet_index(mesh, info[on]["facet"])
        elif "vertex_list" in info[on]:
            normal = get_mean_vertex_normal_list(mesh, info[on]["vertex_list"])
            vertice = get_mean_vertex_list(mesh, info[on]["vertex_list"])

    if inverse_norm:
        normal = normal * -1

    normal = ','.join([str(x) for x in normal.tolist()])
    vertice = ','.join([str(x) for x in vertice.tolist()])

    return normal, vertice