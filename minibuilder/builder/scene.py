from networkx import topological_sort

from minibuilder.builder.mesh import MeshNode


class SceneGraphInfo:
    def __init__(self, graph):
        self.graph = graph
        self.scene = {}
        self.meshes = {}

    def form_configure_display(self, form):
        nodes = set()
        fields = {}
        for node, attr in self.graph.nodes.items():
            nodes.add(attr.get('folder'))
        fields['node'] = nodes

        return form

    def form_display(self, form):
        display = []
        for node in topological_sort(self.graph):
            di_permission = {}
            for permission in self.graph.nodes[node].get('permissions'):
                di_permission[permission] = getattr(form, f"{node}_{permission}")
            display.append(di_permission)

        return display

    def init_mesh(self, form_result, infos, builder_name):
        for node in topological_sort(self.graph):
            select = form_result.get(f'{node}_select')
            list_select = form_result.get(f'{node}_list')
            folder = self.graph.nodes.data()[node].get('folder')

            file_name = infos.get(node).get(select).get('stl').get(list_select).get('file')
            mesh_path = f"data/{builder_name}/{folder}/{select}/{file_name}"

            self.meshes[node] = MeshNode(
                mesh_path=mesh_path,
                node=node,
                info=infos.get(node).get(select).get('stl').get(list_select),
                on=folder,
                dextral=None,
                permissions=self.graph.nodes.data()[node].get('permissions'),
                **{k: v for k, v in form_result.items() if k.startswith(node)}
            )

        return self.meshes