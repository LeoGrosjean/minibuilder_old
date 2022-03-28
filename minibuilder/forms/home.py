import os
from configparser import ConfigParser
from pathlib import Path

from flask_wtf import FlaskForm
from github import Github
from slugify import slugify
from wtforms import SelectField, SubmitField, IntegerField, StringField, HiddenField, FieldList, FormField
from wtforms.widgets import NumberInput

from minibuilder.config import configpath


def get_data_folder():
    config = ConfigParser()
    config.read(configpath + "/mbconfig.ini")
    data_folder = config['FOLDER']['data_path']
    return data_folder


class ChooseBuilderForm(FlaskForm):
    builder = SelectField(label="Builder", choices=os.listdir(get_data_folder()))
    submit = SubmitField("Let's build !")
    add_files = SubmitField('Add files !')
    add_designers = SubmitField('Add designers !')


class EditConfForm(FlaskForm):
    user_data_path = StringField(label="Folder to store files", default=os.getcwd() + '\\data', render_kw={'style': 'width: 100%'} )
    port = IntegerField(label="Port to run miniBuilder (reboot to validate change)", widget=NumberInput(min=-1024, max=65535), default=32000)
    submit = SubmitField('save configuration')


def make_AddBuilderForm(data_path, config, *args, **kwargs):
    class AddBuilderForm(FlaskForm):
        hide = HiddenField()

    for builder, file_categories in config.items():
        builder_id = slugify(builder, separator='_')

        if not Path(f'{data_path}/{builder}').exists:
            setattr(AddBuilderForm, f"{builder_id}_install", SubmitField('Install', name=builder))
        else:
            setattr(AddBuilderForm, f"{builder_id}_update", SubmitField('Update', name=builder))

        setattr(AddBuilderForm, f"{builder_id}_category",
                FieldList(FormField(CategoryForm)),
                )

    del AddBuilderForm.hide

    return AddBuilderForm


class FileForm(FlaskForm):
    file = StringField(render_kw={'hidden': True})
    dl = SubmitField(label=f'DL')


class CategoryForm(FlaskForm):
    category = FieldList(FormField(FileForm))



