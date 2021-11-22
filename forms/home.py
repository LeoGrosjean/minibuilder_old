from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField, IntegerField, BooleanField


class ChooseBuilderForm(FlaskForm):
    builder = SelectField(label="Builder")
    submit = SubmitField("Let's build !")
