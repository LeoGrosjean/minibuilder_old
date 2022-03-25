from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import InputRequired


class FormAddDesigner(FlaskForm):
    add = SubmitField('add designer !')

    designer_name = StringField(label=f'Name', validators=[InputRequired()])
    donation_url = StringField(label=f'Donation url', validators=[InputRequired()])

    # TODO add web