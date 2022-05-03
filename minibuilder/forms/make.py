from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField, IntegerField, BooleanField, FloatField, FieldList, \
    FormField, HiddenField, StringField
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
                SelectField(label=f'{v.get("label")}', default=list(v.get('select'))[0],
                            choices=v.get('select'), validators=[InputRequired()], render_kw={'hidden': False, 'style': 'max-width: 181'}))
        setattr(GenerateMiniDynamic, f"{k}_list",
                SelectField(label=v.get("label"), default=list(v.get('choices'))[0], choices=list(zip(v.get('choices'), v.get('choices'))), validators=[InputRequired()],
                render_kw={'hidden': False, 'style': 'max-width: 181'}))
        setattr(GenerateMiniDynamic, f"{k}_rotate",
                IntegerField(f'{v.get("label")} Rotation', default=0, widget=NumberInput(min=-180, max=180, step=1), validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_anklex",
                FloatField(f'{v.get("label")} Rotation AnkleX', default=0, widget=NumberInput(min=-45, max=45, step=0.1),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_ankley",
                FloatField(f'{v.get("label")} Rotation AnkleY', default=0,
                             widget=NumberInput(min=-45, max=45, step=0.1),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_shake",
                IntegerField(f'{v.get("label")} Shake', default=0, widget=NumberInput(min=-180, max=180, step=1),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_scale",
                FloatField(f'{v.get("label")} Scale', default=1, widget=NumberInput(min=0.5, max=1.5, step=0.01),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_merge",
                FloatField(f'{v.get("label")} Merge', default=0, widget=NumberInput(min=-4, max=3, step=0.01),
                             validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_movex",
                FloatField(f'{v.get("label")} MoveX', default=0, widget=NumberInput(min=-4, max=4, step=0.01),
                           validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_movey",
                FloatField(f'{v.get("label")} MoveY', default=0, widget=NumberInput(min=-4, max=4, step=0.01),
                           validators=[InputRequired()]))
        setattr(GenerateMiniDynamic, f"{k}_bitz",
                FieldList(
                    FormField(dynamic_BitzDisplay(**v)),
                    min_entries=0,
                    max_entries=8, validators=[InputRequired()]
                )
                )
    return GenerateMiniDynamic()


class MissingFiles(FlaskForm):
    missing_list = SelectMultipleField(label='Missing Files')
    yes = SubmitField('Yay, download them !')
    no = SubmitField("I don't want to download them.")


def dynamic_BitzDisplay(*args, **kwargs):

    class BitzDisplay(FlaskForm):
        bitz_label = StringField(label='placeholder_bitzname', render_kw={'hidden': True})
        bitz_fusion = BooleanField(label='Fusion', default=False)
        bitz_select = SelectField(label=f'Category', validators=[InputRequired()], choices=kwargs.get('bitz_select'), render_kw={'hidden': False})
        bitz_list = SelectField(label='File', validators=[InputRequired()], choices=kwargs.get('bitz_choices'), render_kw={'hidden': False})
        bitz_rotate = IntegerField('Rotation', default=0, widget=NumberInput(min=-180, max=180, step=1),
                     validators=[InputRequired()])
        bitz_scale = FloatField('Scale', default=1, widget=NumberInput(min=0.5, max=1.5, step=0.01),
                             validators=[InputRequired()])
        bitz_merge = FloatField('Merge', default=0, widget=NumberInput(min=-4, max=3, step=0.01),
                   validators=[InputRequired()])

        bitz_anklex = FloatField('AnkleX', default=0,
                           widget=NumberInput(min=-45, max=45, step=0.1),
                           validators=[InputRequired()])
        bitz_ankley = FloatField('AnkleY', default=0,
                           widget=NumberInput(min=-45, max=45, step=0.1),
                           validators=[InputRequired()])
        bitz_movex = FloatField('MoveX', default=0, widget=NumberInput(min=-4, max=4, step=0.01),
                           validators=[InputRequired()])
        bitz_movey = FloatField('MoveY', default=0, widget=NumberInput(min=-4, max=4, step=0.01),
                           validators=[InputRequired()])
    return BitzDisplay


def dynamic_FieldBitz(*args, **kwargs):
    class FieldBitz(FlaskForm):
        hide = HiddenField()

    if kwargs.get('bitzs'):
        bitz_select = kwargs.get('bitzs').keys()
        bitz_choices = kwargs.get('bitzs')[list(kwargs.get('bitzs').keys())[0]]['stl'].keys()
    else:
        bitz_select = []
        bitz_choices = None

    if 'Empty' in kwargs.get('bitzs'):
        bitz_select = list(kwargs.get('bitzs').keys())
        bitz_select.insert(0, bitz_select.pop(bitz_select.index('Empty')))
        bitz_choices = kwargs.get('bitzs')[list(kwargs.get('bitzs').keys())[0]]['stl'].keys()

    setattr(FieldBitz, f"{kwargs.get('node')}_bitz",
            FieldList(
                FormField(dynamic_BitzDisplay(
                    bitz_select=bitz_select,
                    bitz_choices=bitz_choices)
                ),
                min_entries=0,
                max_entries=8,
                validators=[InputRequired()]
            ))
    return FieldBitz