from flask import Flask
from flask import jsonify

from blueprints.dashboard import dashboard_bp
from blueprints.attendance import attendance_bp
from blueprints.major_project_submission import major_project_bp
from blueprints.intro_evals import intro_evals_bp
from blueprints.intro_evals_form import intro_evals_form_bp
from blueprints.housing_evals import housing_evals_bp
from blueprints.housing_evals_form import housing_evals_form_bp

from blueprints.spring_evals import spring_evals_bp
from blueprints.spring_evals_form import spring_evals_form_bp
import os

import json
import sys

base_dir = os.getcwd()


def app_path(*args):
    return os.path.join(base_dir, *args)

app = Flask(__name__)

app.templates_folder = app_path("templates")

app.register_blueprint(dashboard_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(major_project_bp)
app.register_blueprint(intro_evals_bp)
app.register_blueprint(intro_evals_form_bp)
app.register_blueprint(housing_evals_bp)
app.register_blueprint(housing_evals_form_bp)
app.register_blueprint(spring_evals_bp)
app.register_blueprint(spring_evals_form_bp)


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)

def web_main():
    json_config = None

    with open(sys.argv[1]) as config_file:
        json_config = json.load(config_file)

    app.run(**json_config['flask'])

if __name__ == '__main__':
    web_main()