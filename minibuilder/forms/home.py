import os

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, StringField
from wtforms.widgets import NumberInput


class ChooseBuilderForm(FlaskForm):
    builder = SelectField(label="Builder", choices=os.listdir('data'))
    submit = SubmitField("Let's build !")
    add_files = SubmitField('Add files !')
    add_designers = SubmitField('Add designers !')


class EditConfForm(FlaskForm):
    user_data_path = StringField(label="Folder to store files", default=os.getcwd() + '\\data', render_kw={'style': 'width: 100%'} )
    port = IntegerField(label="Port to run miniBuilder (reboot to validate change)", widget=NumberInput(min=-1024, max=65535), default=32000)
    submit = SubmitField('save configuration')

