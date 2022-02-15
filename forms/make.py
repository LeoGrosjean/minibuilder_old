from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField, IntegerField, BooleanField
from wtforms.validators import InputRequired

from wtforms.widgets import NumberInput


def generateminidynamic_func(*args, **kwargs):

    class GenerateMiniDynamic(FlaskForm):
        download_missing_file = BooleanField('Download missing file')
        submit_preview = SubmitField('Get a Preview !')
        dl_zip = SubmitField('Download Zip !')
        live_edit = SubmitField('Live edit !')

    for k, v in kwargs.items():
        setattr(GenerateMiniDynamic, f"{k}_select",
                SelectField(label=f'{v.get("label")}', choices=v.get('select'), validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_list",
                SelectField(label=v.get("label"), choices=list(zip(v.get('choices'), v.get('choices'))), validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_rotate",
                IntegerField(f'{v.get("label")} Rotation', default=0, widget=NumberInput(min=-180, max=180, step=1), validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_shake",
                IntegerField(f'{v.get("label")} Shake', default=0, widget=NumberInput(min=-180, max=180, step=1),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_scale",
                IntegerField(f'{v.get("label")} Scale', default=1, widget=NumberInput(min=0.8, max=1.2, step=0.01),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_merge",
                IntegerField(f'{v.get("label")} Merge', default=0, widget=NumberInput(min=-1, max=2, step=0.01),
                             validators=[InputRequired()]))
    return GenerateMiniDynamic()


class MissingFiles(FlaskForm):
    missing_list = SelectMultipleField(label='Missing Files')
    yes = SubmitField('Yay, download them !')
    no = SubmitField("I don't want to download them.")
