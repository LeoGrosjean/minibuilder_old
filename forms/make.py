import json
from math import radians

import numpy as np
import trimesh as tm
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField, IntegerField, BooleanField, StringField, FieldList, \
    FormField
from wtforms.validators import InputRequired

from wtforms.widgets import NumberInput

from file_config.parts import backpacks, heads, arms, bodies, hands, legs


class GenerateMini(FlaskForm):
    backpack_ = SelectField(label='Backpack Type', choices=backpacks.keys(), validators=[InputRequired()])
    backpack = SelectMultipleField(label='Backpack', choices=list(zip(backpacks['SM']['stl'], backpacks['SM']['stl'])), validators=[InputRequired()])

    head_ = SelectField(label='Head Type', choices=heads.keys())
    head = SelectMultipleField(label='Head', choices=list(zip(heads['SM']['stl'], heads['SM']['stl'])), validators=[InputRequired()])

    rarm_ = SelectField(label='Right Arm Type', choices=arms.keys(), validators=[InputRequired()])
    rarm = SelectMultipleField(label='Right Arm', choices=list(zip(arms['SM']['stl'], arms['SM']['stl'])), validators=[InputRequired()])
    rarm_rotation = IntegerField('Right Arm Rotation', default=0, widget=NumberInput(min=-90, max=90, step=1), validators=[InputRequired()])

    larm_ = SelectField(label='Left Arm Type', choices=arms.keys(), validators=[InputRequired()])
    larm = SelectMultipleField(label='Left Arm', choices=list(zip(arms['SM']['stl'], arms['SM']['stl'])), validators=[InputRequired()])
    larm_rotation = IntegerField('Left Arm Rotation', default=0, widget=NumberInput(min=-90, max=90, step=1), validators=[InputRequired()])

    body_ = SelectField(label='Body Type', choices=bodies.keys(), validators=[InputRequired()])
    body = SelectMultipleField(label='Body', choices=list(zip(bodies['SM']['stl'], bodies['SM']['stl'])), validators=[InputRequired()])

    rhand_ = SelectField(label='Right Hand Type', choices=hands.keys(), validators=[InputRequired()])
    rhand = SelectMultipleField(label='Right Hand', choices=list(zip(hands['SM']['stl'], hands['SM']['stl'])), validators=[InputRequired()])
    rhand_rotation = IntegerField('Right Hand Rotation', default=0, widget=NumberInput(min=-90, max=90, step=1), validators=[InputRequired()])

    lhand_ = SelectField(label='Left Hand Type', choices=hands.keys(), validators=[InputRequired()])
    lhand = SelectMultipleField(label='Left Hand', choices=list(zip(hands['SM']['stl'], hands['SM']['stl'])), validators=[InputRequired()])
    lhand_rotation = IntegerField('Left Hand Rotation', default=0, widget=NumberInput(min=-90, max=90, step=1), validators=[InputRequired()])

    leg_ = SelectField(label='Leg Type', choices=legs.keys(), validators=[InputRequired()])
    leg = SelectMultipleField(label='Leg', choices=list(zip(legs['SM']['stl'], legs['SM']['stl'])), validators=[InputRequired()])

    download_missing_file = BooleanField('Download missing file')

    submit_preview = SubmitField('Get a Preview !')


def generateminidynamic_func(*args, **kwargs):

    class GenerateMiniDynamic(FlaskForm):
        download_missing_file = BooleanField('Download missing file')
        submit_preview = SubmitField('Get a Preview !')

    for k, v in kwargs.items():
        setattr(GenerateMiniDynamic, f"{k}_select",
                SelectField(label=f'{v.get("label")}', choices=v.get('select'), validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_list",
                SelectMultipleField(label=v.get("label"), choices=list(zip(v.get('choices'), v.get('choices'))), validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_rotate",
                IntegerField(f'{v.get("label")} Rotation', default=0, widget=NumberInput(min=-180, max=180, step=1), validators=[InputRequired()]))

    return GenerateMiniDynamic()


class MissingFiles(FlaskForm):
    missing_list = SelectMultipleField(label='Missing Files')
    yes = SubmitField('Yay, download them !')
    no = SubmitField("I don't want to download them.")
