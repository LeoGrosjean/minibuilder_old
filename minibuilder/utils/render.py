import base64
from trimesh import util, resources
import codecs


def scene_to_html(scene, node_dict_rotate={}, config_live_edit={}, mode='live_edit'):
    """
    Return HTML that will render the scene using
    GLTF/GLB encoded to base64 loaded by three.js

    Parameters
    --------------
    scene : trimesh.Scene
      Source geometry

    Returns
    --------------
    html : str
      HTML containing embedded geometry
    """
    # fetch HTML template from ZIP archive
    # it is bundling all of three.js so compression is nice
    from jinja2 import Template
    if mode == 'live_edit':
        with open('minibuilder/templates/template_mesh_render_v2.jinja2') as file_:
            base = Template(file_.read())
    elif mode == 'make_conf':
        with open('minibuilder/templates/template_mesh_render.jinja2') as file_:
            base = Template(file_.read())
    base = base.render(node_dict_rotate=node_dict_rotate, config_live_edit=config_live_edit)
    scene.camera
    # get export as bytes
    data = scene.export(file_type='glb')
    # encode as base64 string
    encoded = base64.b64encode(data).decode('utf-8')
    # replace keyword with our scene data
    result = base.replace('$B64GLTF', encoded)

    return result
