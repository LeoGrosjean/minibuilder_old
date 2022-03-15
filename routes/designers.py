import json
import os

from flask import Blueprint, render_template, request

from forms.designers import FormAddDesigner
from forms.home import ChooseBuilderForm

designer_bp = Blueprint('designer_bp', __name__)


@designer_bp.route('/builder/<builder_name>/designers', methods=['GET'])
def form_designer(builder_name):
    form_designer = FormAddDesigner()
    form_header = ChooseBuilderForm()
    form_header.builder.data = builder_name
    return render_template("designers.html",
                           form_designer=form_designer,
                           form_header=form_header,
                           builder_name=builder_name)


@designer_bp.route('/builder/<builder_name>/designers', methods=['POST'])
def add_designer(builder_name):
    form_designer = FormAddDesigner()
    form_header = ChooseBuilderForm()
    form_header.builder.data = builder_name
    form_result = request.form.to_dict()

    if "designer.json" in os.listdir(f"data/{builder_name}/"):
        with open(f"data/{builder_name}/designer.json", "r+") as f:
            designers = json.load(f)
            f.seek(0)
            designers[form_result.get('designer_name')] = {
                "name": f"@{form_result.get('designer_name')}",
                "donation": form_result.get('donation_url')

                # TODO add web []
            }
            json.dump(designers, f, indent=4)
    else:
        with open(f"data/{builder_name}/designer.json", "w") as f:
            designers = {}
            designers[form_result.get('designer_name')] = {
                "name": f"@{form_result.get('designer_name')}",
                "donation": form_result.get('donation_url')

                # TODO add web []
            }
            json.dump(designers, f, indent=4)

    return render_template("designers.html",
                           form_designer=form_designer,
                           form_header=form_header,
                           builder_name=builder_name)