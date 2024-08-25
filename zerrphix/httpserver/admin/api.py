import imghdr
# from PIL import Image
import logging
import os
import re
import uuid

from flask import Blueprint
from flask import Response
from flask import abort
from flask import current_app
from flask import escape
from flask import render_template
from flask import request
from flask import send_file
from flask import redirect
from flask_login import current_user
from flask_login import login_required

from zerrphix.util.filesystem import get_file_extension
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import resize_and_crop

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json
import mimetypes
import random

api = Blueprint('api', __name__)

log = logging.getLogger(__name__)


@api.route('/api/1/films_awating_data_count')
@login_required
def films_awatting_data_aquasition():
    count = current_app.config["AdminHTTPApiFuncs"].films_awatting_data_aquasition(current_user.user_langs[1])
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/films_awating_images_count')
@login_required
def films_awating_images_count():
    count = current_app.config["AdminHTTPApiFuncs"].films_awating_images_count(current_user.user_langs[1])
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/films_awating_icon_artwork_count')
@login_required
def films_awating_icon_artwork_count():
    #user_template_id = current_app.config["AdminHTTPGenFuncs"].get_user_template_id(current_user.id)
    count = current_app.config["AdminHTTPApiFuncs"].films_awating_artwork_count(current_user.id, 1, 1, 1)
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/films_awating_synopsis_artwork_count')
@login_required
def films_awating_synopsis_artwork_count():
    count = current_app.config["AdminHTTPApiFuncs"].films_awating_artwork_count(current_user.id, 2, 1, 1)
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_awating_data_count')
def shows_awatting_data_aquasition():
    count = current_app.config["AdminHTTPApiFuncs"].shows_awatting_data_aquasition(current_user.user_langs[2])
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_awating_images_count')
def shows_awating_images_count():
    count = current_app.config["AdminHTTPApiFuncs"].shows_awating_images_count(current_user.user_langs[2])
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_awating_icon_artwork_count')
@login_required
def shows_awating_icon_artwork_count():
    count = current_app.config["AdminHTTPApiFuncs"].shows_awating_artwork_count(current_user.id, 1,
                                                                                'default',
                                                                                '1.0', 1, 1)
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_awating_synopsis_artwork_count')
@login_required
def shows_awating_synopsis_artwork_count():
    count = current_app.config["AdminHTTPApiFuncs"].shows_awating_artwork_count(current_user.id, 2,
                                                                                'default',
                                                                                '1.0', 1, 1)
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/films_unidentified_no_retry_count')
def films_unidentified_no_retry():
    count = current_app.config["AdminHTTPApiFuncs"].films_unidentified_no_retry()
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/films_unidentified_retry_count')
def films_unidentified_retry():
    count = current_app.config["AdminHTTPApiFuncs"].films_unidentified_retry()
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_unidentified_no_retry_count')
def shows_unidentified_no_retry():
    count = current_app.config["AdminHTTPApiFuncs"].shows_unidentified_no_retry()
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_unidentified_retry_count')
def shows_unidentified_retry():
    count = current_app.config["AdminHTTPApiFuncs"].shows_unidentified_retry()
    return_dict = {'status':'success',
                   'data':{'count': count}}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/film_current_library_process_running')
def film_current_library_process_running():
    processing_state_dict = current_app.config["AdminHTTPApiFuncs"].current_library_process_running_state(1)
    return_dict = {'status':'success',
                   'data':processing_state_dict}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/show_current_library_process_running')
def show_current_library_process_running():
    processing_state_dict = current_app.config["AdminHTTPApiFuncs"].current_library_process_running_state(2)
    return_dict = {'status':'success',
                   'data':processing_state_dict}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/films_invalid_count')
def films_invalid_count():
    films_invalid_count_dict = current_app.config["AdminHTTPApiFuncs"].films_invalid_count(1)
    return_dict = {'status':'success',
                   'data':films_invalid_count_dict}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/shows_invalid_count')
def shows_invalid_count():
    films_invalid_count_dict = current_app.config["AdminHTTPApiFuncs"].films_invalid_count(2)
    return_dict = {'status':'success',
                   'data':films_invalid_count_dict}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/issue_count')
def thread_restarts():
    issue_count_dict = current_app.config["AdminHTTPApiFuncs"].get_issue_count_dict()
    return_dict = {'status':'success',
                   'data':issue_count_dict}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')


@api.route('/api/1/free_space')
def free_space():
    issue_count_dict = current_app.config["AdminHTTPApiFuncs"].free_space()
    return_dict = {'status':'success',
                   'data':issue_count_dict}
    return Response(json.dumps(return_dict),
                    mimetype='text/plain')

