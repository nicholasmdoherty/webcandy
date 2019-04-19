import util

from flask import (
    g, Blueprint, render_template, jsonify, request, make_response, redirect,
    url_for
)
from werkzeug.exceptions import NotFound
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    SignatureExpired,
    BadSignature
)
from config import Config
from .models import User
from .extensions import auth, controller

views = Blueprint('views', __name__, static_folder='../../static/dist',
                  template_folder='../../static')
api = Blueprint('api', __name__)


# -------------------------------
# Login methods
# -------------------------------


@auth.verify_token
def verify_auth_token(token: str) -> bool:
    """
    Verify an authentication token.

    :param token: the token to verify
    :return: ``True`` if a valid token was provided; ``False`` otherwise
    """
    s = Serializer(Config.SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False  # valid token, but expired
    except BadSignature:
        return False  # invalid token
    g.user = User.query.get(data['id'])
    return True


# -------------------------------
# React routes
# -------------------------------
# TODO: Allow loading of favicon.ico


@views.route('/', defaults={'path': ''}, methods=['GET'])
@views.route('/<path:path>')
def react_catch_all(path: str):
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


@api.route('/token', methods=['POST'])
def get_auth_token():
    req_json = request.get_json()

    user = User.query.filter_by(username=req_json["username"]).first()
    if not user or not user.check_password(req_json["password"]):
        return jsonify({
            'error': '401: Unauthorized',
            'error_description': 'Invalid username and password combination'
        })

    g.user = user
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@api.route('/submit', methods=['POST'])
@auth.login_required
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


@api.route('/patterns', methods=['GET'])
@auth.login_required
def patterns():
    """
    Get a list of valid lighting pattern names.
    """
    return jsonify(util.get_config_names())


@api.route('/colors', methods=['GET'])
@auth.login_required
def colors():
    """
    Get a mapping from name to hex value of saved colors.
    """
    return jsonify(util.load_asset('colors.json'))


@api.route('/color_lists', methods=['GET'])
@auth.login_required
def color_lists():
    """
    Get a mapping from name to list of hex value of saved color lists.
    """
    return jsonify(util.load_asset('color_lists.json'))


# -------------------------------
# Error handlers
# -------------------------------


def unauthorized(_):
    return redirect(url_for('views.login'))


def not_found(error):
    return make_response(jsonify(util.format_error(error)), 404)
