from flask import Blueprint, render_template


thingidl_bp = Blueprint('thingidl_bp', __name__)


@thingidl_bp.route('/thingiverse')
def lol():
    return render_template('thingiverse_downloader_tab.jinja2.html')


@thingidl_bp.route('/admin')
def admin():
    return render_template('thingiverse_downloader_settings.jinja2.html', _='lol')