import os

import wtforms
from flask_wtf import FlaskForm
from werkzeug.datastructures import FileStorage
from wtforms import SubmitField, SelectField, StringField
from wtforms.validators import InputRequired, URL

from minibuilder.file_config.parts import load_json
from wtforms import MultipleFileField


def DynamicFormMakeMeshConf(graph, *args, **kwargs):
    class FormMakeMeshConf(FlaskForm):
        add = SubmitField('add mesh !')
        mesh_file = SelectField(label='Mesh File', choices=os.listdir(f"data/{graph.name}/uploaded/"),
                                validators=[InputRequired()], render_kw={'hidden': False, 'style': 'width: 181'})
        file_name = StringField(label='File Name', validators=[InputRequired()], render_kw={'hidden': False})
        support = SelectField(label='Support File (optionnal)', choices=[''] + os.listdir(f"data/{graph.name}/uploaded/"),
                                validators=[], render_kw={'hidden': False, 'style': 'width: 181'})
        url = StringField(label='Url to download/buy', validators=[InputRequired(), URL()], render_kw={'hidden': False})
        node = SelectField(label=f'Node', validators=[InputRequired()], render_kw={'hidden': False})
        file = StringField(label=f'Json File', validators=[InputRequired()], render_kw={'hidden': False,
                                                                                        "list": "id_list_file"})
        category = StringField(label=f'Category', validators=[InputRequired()], render_kw={'hidden': False,
                                                                                           "list": "id_list_category"})
        designer = SelectField(label=f'Designer', validators=[InputRequired()], render_kw={'hidden': False})

        def __init__(self, graph, *args, **kwargs):
            super(FormMakeMeshConf, self).__init__(*args, **kwargs)
            self.graph = graph

            is_bitz = ['bitz'] if self.graph.graph.get('bitz_files') else []
            self.node.choices = list(self.graph.nodes) + is_bitz
            self.node.default = kwargs.get('node', self.node.choices[0])

            self.file.choices = self.get_file_from_node(self.node.default)
            self.file.default = kwargs.get('file', self.file.choices[0])

            self.category.choices = self.get_category_from_file(self.file.default)
            self.category.default = kwargs.get('category', self.category.choices[0])

            self.designer.choices = self.get_designer_from_file()
            self.designer.default = kwargs.get('designer', self.designer.choices[0] if self.designer.choices else [])

        def get_node_choices(self):
            nodes = set()
            for node, attr in self.graph.nodes.items():
                nodes.add(attr.get('folder'))

            if self.graph.graph.get('bitz_files'):
                nodes.add('bitz')

            return list(nodes)

        def get_file_from_node(self, node):
            if node == "bitz":
                return self.graph.graph.get('bitz_files')
            return self.graph.nodes[node].get('files')

        def get_category_from_file(self, file):
            return list(load_json(f"data/{self.graph.name}/{file}").keys())

        def get_designer_from_file(self, file="designer.json"):
            try:
                designers = list(load_json(f"data/{self.graph.name}/{file}").keys())
            except Exception as e:
                print(e)
                designers = []
            return designers

    node = kwargs.get('node', list(graph.nodes)[0])

    connectors = []
    # TODO maybe issue with bitz

    if "bitz_files" in graph.graph:
        setattr(FormMakeMeshConf, "marker_bitz",
                StringField(f"Bitz Marker", render_kw={'readonly': True, 'hidden': True}))

    if node == "bitz":
        connectors = ['bitz']
        setattr(FormMakeMeshConf, "marker_bitz",
                StringField(f"Bitz Marker", render_kw={'readonly': True, 'hidden': False}))
    else:
        connectors.extend(list(graph.successors(node)))
        connectors.extend(list(graph.predecessors(node)))

    for field in set(graph.nodes) - set(connectors):
        setattr(FormMakeMeshConf, f"marker_{field}",
                StringField(f"{graph.nodes[field].get('label')} Marker", render_kw={'readonly': True, 'hidden': True}))

    if node != "bitz":
        for field in set(connectors):
            setattr(FormMakeMeshConf, f"marker_{field}",
                    StringField(f"{graph.nodes[field].get('label')} Marker", render_kw={'readonly': True}))
    setattr(FormMakeMeshConf, "connectors", connectors)

    return FormMakeMeshConf(graph, *args, **kwargs)


class FormCreateJson(FlaskForm):
    x = StringField("Marker", render_kw={'readonly': True})


class FilesRequired(wtforms.validators.DataRequired):
    """Validates that all entries are Werkzeug
    :class:`~werkzeug.datastructures.FileStorage` objects.
    :param message: error message
    """

    def __call__(self, form, field):
        if not (
            field.data and all(
                (isinstance(entry, FileStorage) and entry)
                for entry in field.data
            )
        ):
            raise wtforms.validators.StopValidation(
                self.message or field.gettext('This field is required.'),
            )


class FormUploadFile(FlaskForm):
    files = MultipleFileField('File(s) Upload', validators=[FilesRequired()])
    submit_upload = SubmitField('Upload files !')


