import os

from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField, IntegerField, BooleanField


class ChooseBuilderForm(FlaskForm):
    builder = SelectField(label="Builder", choices=os.listdir('data'))
    submit = SubmitField("Let's build !")
    add_files = SubmitField('Add files !')

