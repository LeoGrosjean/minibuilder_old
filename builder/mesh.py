import os
from math import radians
import numpy as np
import trimesh as tm

from utils.mesh import get_center_facet_index, get_mean_vertex_normal_list, get_mean_vertex_list

DL_WEBSITES = [
    'thingiverse',
    'cults3d',
    'cgtrader'
]

PERMISSIONS_MODIF = [
    "rotate",
    "scale",
    "merge",
    "anklex",
    "ankley",
    "movex",
    "movey"
]


class MeshNode:
    def __init__(self, mesh_path, node, info, on, dextral=None, permissions=[], **kwargs):
        self.mesh_path = mesh_path
        self.mesh = None
        self.node = node
        self.dextral = dextral
        self.permissions = permissions
        self.info = info

        for k, v in kwargs.items():
            if k.split("_")[1] in PERMISSIONS_MODIF:
                setattr(self, k.split("_")[1], v)

        if self.file_exist():
            self.mesh = tm.load(mesh_path)
            self.mesh.metadata['file_name'] = node

    def file_exist(self):
        return os.path.isfile(self.mesh_path)

    def permission_check(self, permission):
        return permission in self.permissions

    def get_normal(self, on):
        """
        get the related normal of this mesh for a predecessor/successor node name
        :param on: name of a node
        :return: normal linked to the parent mesh
        """
        if "vertex" in self.info[on]:
            normal = self.mesh.vertex_normals[self.info[on]["vertex"]]
        elif "facet" in self.info[on]:
            normal = self.mesh.facets_normal[self.info[on]["facet"]]
        elif "vertex_list" in self.info[on]:
            normal = get_mean_vertex_normal_list(self.mesh, self.info[on]["vertex_list"])
        return normal

    def get_vertice(self, on):
        """
        get the related vertice of this mesh for a predecessor/successor node name
        :param on: name of a node
        :return: vertice linked to the parent mesh
        """
        if "vertex" in self.info[on]:
            vertice = self.mesh.vertices[self.info[on]["vertex"]]
        elif "facet" in self.info[on]:
            vertice = get_center_facet_index(self.mesh, self.info[on]["facet"])
        elif "vertex_list" in self.info[on]:
            vertice = get_mean_vertex_list(self.mesh, self.info[on]["vertex_list"])
        return vertice

    def apply_rotation(self, on, rotate, ankle_x=None, ankle_y=None):
        """
        apply rotation to mesh from 3 axis on one vertice
        :param on: name of a node
        :param rotate: value for rotate
        :param ankle_x: value for anklex
        :param ankle_y: value for ankley
        :return: apply modification to self.mesh
        """
        normal = self.get_normal(on)
        vertice = self.get_vertice(on)
        transform_matrice = tm.transformations.rotation_matrix(radians(rotate), normal, vertice)
        self.mesh.apply_transform(transform_matrice)

        if ankle_x:
            normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
            if np.isnan(normal_x[0]):
                normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))
            transform_matrice = tm.transformations.rotation_matrix(radians(ankle_x), normal_x, vertice)
            self.mesh.apply_transform(transform_matrice)

        if ankle_y:
            normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))
            transform_matrice = tm.transformations.rotation_matrix(radians(ankle_y), normal_y, vertice)
            self.mesh.apply_transform(transform_matrice)

    def allign_mesh_normal(self, on, dest_normal):
        normal = self.get_normal(on)
        self.mesh.apply_transform(tm.geometry.align_vectors(normal, dest_normal))

    def translate_to_vertice(self, on, dest_vertice):
        vertice = self.get_vertice(on)
        self.mesh.apply_translation(dest_vertice - vertice)

    def translate_from_normal(self, on, merge, move_x=None, move_y=None):
        normal = self.get_normal(on)
        self.mesh.apply_translation(normal * merge)
        if move_x:
            normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
            if np.isnan(normal_x[0]):
                normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))
            self.mesh.apply_translation(normal_x * move_x)

        if move_y:
            normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))
            self.mesh.apply_translation(normal_y * move_y)

    def scale_mesh(self, scale):
        self.mesh.apply_scale(scale)

    def stringify_normals_vertice(self, on):
        normal = self.get_normal(on)
        vertice = self.get_vertice(on)

        normal_x = np.cross(normal, [1, 0, 0]) / np.linalg.norm(np.cross(normal, [1, 0, 0]))
        if np.isnan(normal_x[0]):
            normal_x = np.cross(normal, [0, 0, 1]) / np.linalg.norm(np.cross(normal, [0, 0, 1]))

        normal_y = np.cross(normal, normal_x) / np.linalg.norm(np.cross(normal, normal_x))

        normal = ','.join([str(x) for x in normal.tolist()])
        vertice = ','.join([str(x) for x in vertice.tolist()])
        normal_x = ','.join([str(x) for x in normal_x.tolist()])
        normal_y = ','.join([str(x) for x in normal_y.tolist()])

        return normal, vertice, normal_x, normal_y