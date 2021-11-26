import webbrowser
from threading import Timer
import os
from flask import Flask
from routes.make import make_bp as make_blueprint
from routes.thingidl import thingidl_bp

# blueprint for make parts of app
app = Flask(__name__)
app.register_blueprint(make_blueprint)
app.register_blueprint(thingidl_bp)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY_FLASK') or 'coucou_c_moi_leo'


def main():
    # The reloader has not yet run - open the browser
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:2000/')

    # Otherwise, continue as normal
    app.run(host="127.0.0.1", port=2000, debug=True)


if __name__ == '__main__':
    main()