import os

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, HiddenField, StringField, FloatField, validators, FieldList, FormField
from wtforms.validators import InputRequired, DataRequired
from wtforms.widgets import NumberInput
from file_config.parts import load_json


def DynamicFormEditMeshConf(graph, node, *args, **kwargs):
    class FormMakeMeshConf(FlaskForm):
        add = SubmitField('Validate change !')
        file_name = StringField(label='File Name', validators=[InputRequired()], render_kw={'hidden': False})
        support = SelectField(label='Support File (optionnal)', choices=[''] + os.listdir(f"data/{graph.name}/uploaded/"),
                                validators=[], render_kw={'hidden': False, 'style': 'width: 181'})
        url = StringField(label='Url to download/buy', validators=[InputRequired()], render_kw={'hidden': False})

        designer = SelectField(label=f'Designer', validators=[InputRequired()], render_kw={'hidden': False})

        def __init__(self, graph, *args, **kwargs):
            super(FormMakeMeshConf, self).__init__(*args, **kwargs)
            self.graph = graph

            self.designer.choices = self.get_designer_from_file()

        def get_designer_from_file(self, file="designer.json"):
            try:
                designers = list(load_json(f"data/{self.graph.name}/{file}").keys())
            except Exception as e:
                print(e)
                designers = []
            return designers

    if list(graph.successors(node)):
        connectors = []
        connectors.extend(list(graph.successors(node)))
        if list(graph.predecessors(node)):
            connectors.append(node)

        for field in set(connectors):
            setattr(FormMakeMeshConf, f"{field}_marker",
                    StringField(f"{graph.nodes[field].get('label')} Marker", render_kw={'readonly': True}))
            setattr(FormMakeMeshConf, "connectors", connectors)

            setattr(FormMakeMeshConf, f"marker_{field}_movex",
                    FloatField(f"{graph.nodes[field].get('label')} MoveX", default=0, widget=NumberInput(min=-4, max=4, step=0.01),
                               validators=[InputRequired()], render_kw={'type': "range"}))
            setattr(FormMakeMeshConf, f"marker_{field}_movey",
                    FloatField(f"{graph.nodes[field].get('label')} MoveY", default=0, widget=NumberInput(min=-4, max=4, step=0.01),
                               validators=[InputRequired()], render_kw={'type': "range"}))
    else:
        connectors = [node]
        setattr(FormMakeMeshConf, f"{node}_marker",
                StringField(f"{graph.nodes[node].get('label')} Marker", render_kw={'readonly': True}))
        setattr(FormMakeMeshConf, "connectors", connectors)

        setattr(FormMakeMeshConf, f"marker_{node}_movex",
                FloatField(f"{graph.nodes[node].get('label')} MoveX", default=0,
                           widget=NumberInput(min=-4, max=4, step=0.01),
                           validators=[InputRequired()], render_kw={'type': "range"}))
        setattr(FormMakeMeshConf, f"marker_{node}_movey",
                FloatField(f"{graph.nodes[node].get('label')} MoveY", default=0,
                           widget=NumberInput(min=-4, max=4, step=0.01),
                           validators=[InputRequired()], render_kw={'type': "range"}))

    return FormMakeMeshConf(graph, *args, **kwargs)


class ResidenceForm(FlaskForm):
    place = StringField()
    zipcode = StringField()


class MyForm(FlaskForm):
    residence = FieldList(FormField(ResidenceForm), min_entries=1)


class BitzForm(FlaskForm):
    """Subform.
    CSRF is disabled for this subform (using `Form` as parent class) because
    it is never used by itself.
    """
    name = StringField(
        'Label',
        validators=[InputRequired(), validators.Length(max=100)]
    )
    marker = StringField(f"Marker", render_kw={'readonly': False}, validators=[InputRequired()])


class BitzsForm(FlaskForm):
    bitzs = FieldList(
        FormField(BitzForm),
        min_entries=0,
        max_entries=8, validators=[InputRequired()]
    )