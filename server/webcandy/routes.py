import util

from flask import (
    g, Blueprint, render_template, jsonify, request, make_response,
)
from werkzeug.exceptions import NotFound
from .models import User
from .extensions import auth, controller

views = Blueprint('views', __name__, static_folder='../../static/dist',
                  template_folder='../../static')
api = Blueprint('api', __name__)


# -------------------------------
# Login methods
# -------------------------------


@auth.verify_password
def verify_password(username_or_token: str, password: str) -> bool:
    # TODO: Requires token to be passed as username. Implement bearer token.
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.check_password(password):
            return False
    g.user = user
    return True


# -------------------------------
# React routes
# -------------------------------


@views.route('/', defaults={'path': ''})
@views.route('/<path:path>')
@auth.login_required
def index(path: str):
    # catch-all to route any non-API calls to React, which then does its own
    # routing to display the correct page
    del path  # just to get rid of IDE warnings
    return render_template('index.html')


# -------------------------------
# API routes
# -------------------------------


@api.route('/', defaults={'path': ''}, methods=['GET'])
@api.route('/<path:path>')
def api_catch_all(path: str):
    del path
    # this will only be reached if a user tries to get /api/<non-existing path>
    # we want to generate a JSON 404 response rather than the React one that
    # would be generated by the index catch-al if this method did not exist
    return not_found(NotFound())


@api.route('/token', methods=['GET'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@api.route('/submit', methods=['POST'])
def submit():
    """
    Handle the submission of a lighting configuration to run.

    POST form fields fields:
    - "pattern": the pattern to run
    - "strobe": whether to add a strobe effect
    - "color": the color to use, if applicable
    - "color_list": the color list to use, if applicable

    :return: JSON indicating if running was successful
    """
    req_json = request.get_json()
    pattern = req_json['pattern']
    del req_json['pattern']

    return jsonify(success=controller.run_script(pattern, **req_json))


# TODO: Loading of favicon.ico (sometimes) blocked for jsonify pages


@api.route('/patterns', methods=['GET'])
def patterns():
    return jsonify(util.get_config_names())


@api.route('/colors', methods=['GET'])
def colors():
    return jsonify(util.load_asset('colors.json'))


@api.route('/color_lists', methods=['GET'])
def color_lists():
    return jsonify(util.load_asset('color_lists.json'))


# -------------------------------
# Error handlers
# -------------------------------


def not_found(error):
    return make_response(jsonify(util.format_error(error)), 404)
