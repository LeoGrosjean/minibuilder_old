import webbrowser
import os
from configparser import ConfigParser

from flask import Flask

from minibuilder.config import configpath
from minibuilder.routes.configure import configure_bp
from minibuilder.routes.designers import designer_bp
from minibuilder.routes.edit_file import edit_file_bp
from minibuilder.routes.home import home_bp
from minibuilder.routes.make import make_bp as make_blueprint
from minibuilder.routes.thingidl import thingidl_bp

# blueprint for make parts of app

app = Flask(__name__, template_folder='minibuilder/templates', static_folder='minibuilder/static')
app.register_blueprint(make_blueprint)
app.register_blueprint(thingidl_bp)
app.register_blueprint(configure_bp)
app.register_blueprint(designer_bp)
app.register_blueprint(edit_file_bp)
app.register_blueprint(home_bp)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY_FLASK') or 'coucou_c_moi_leo'
app.config["TEMPLATES_AUTO_RELOAD"] = True


def main():
    # The reloader has not yet run - open the browser
    try:
        config = ConfigParser()
        config.read(f"{configpath}/mbconfig.ini")
        port = config['SERVER']['port']
    except Exception:
        port = 32000

    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new(f'http://127.0.0.1:{port}/')

    # Otherwise, continue as normal
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == '__main__':
    main()
