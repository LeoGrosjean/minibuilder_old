import os
from pathlib import Path

from flask_wtf import FlaskForm
from github import Github
from slugify import slugify
from wtforms import SelectField, SubmitField, IntegerField, StringField, HiddenField, FieldList, FormField
from wtforms.widgets import NumberInput

from minibuilder.config import git_public_token


class ChooseBuilderForm(FlaskForm):
    builder = SelectField(label="Builder", choices=os.listdir('data'))
    submit = SubmitField("Let's build !")
    add_files = SubmitField('Add files !')
    add_designers = SubmitField('Add designers !')


class EditConfForm(FlaskForm):
    user_data_path = StringField(label="Folder to store files", default=os.getcwd() + '\\data', render_kw={'style': 'width: 100%'} )
    port = IntegerField(label="Port to run miniBuilder (reboot to validate change)", widget=NumberInput(min=-1024, max=65535), default=32000)
    submit = SubmitField('save configuration')


def make_AddBuilderForm(data_path, *args, **kwargs):
    class AddBuilderForm(FlaskForm):
        hide = HiddenField()

    g = Github(git_public_token)
    repo = g.get_repo("LeoGrosjean/minibuilder")

    try:
        builders = repo.get_contents(f"data")
    except Exception as e:
        print(e)
        builders = []

    for builder in builders:
        builder_id = slugify(builder.name, separator='_')
        if not Path(f'{data_path}/{builder}').exists:
            setattr(AddBuilderForm, f"{builder_id}_install", SubmitField('Install', name=builder.name))
        else:
            setattr(AddBuilderForm, f"{builder_id}_update", SubmitField('Update', name=builder.name))

    del AddBuilderForm.hide

    return AddBuilderForm


def make_AddCategoryForm(data_path, builder, *args, **kwargs):
    class AddCategoryForm(FlaskForm):
        hide = HiddenField()

    g = Github(git_public_token)
    repo = g.get_repo("LeoGrosjean/minibuilder")

    try:
        categories = [x.name for x in repo.get_contents(f"data/{builder}/configuration") if x.type == 'dir']
    except Exception as e:
        print(e)
        categories = []

    for category in categories:
        category_id = slugify(category.name, separator='_')
        if not Path(f'{data_path}/{builder}').exists:
            setattr(AddCategoryForm, f"{category_id}_install", SubmitField('Install', name=category.name))
        else:
            setattr(AddCategoryForm, f"{category_id}_update", SubmitField('Update', name=category.name))

    del AddCategoryForm.hide

    return AddCategoryForm
