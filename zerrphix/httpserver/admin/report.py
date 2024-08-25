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

report = Blueprint('report', __name__)

log = logging.getLogger(__name__)


@report.route('/report')
@login_required
def film_index():
    issue_count_dict = current_app.config["AdminHTTPReportFuncs"].get_issue_count_dict()
    recent_fatal_exceptions = current_app.config["AdminHTTPReportFuncs"].recent_fatal_exceptions(20)
    recent_exceptions = current_app.config["AdminHTTPReportFuncs"].recent_exceptions(20)
    recent_errors = current_app.config["AdminHTTPReportFuncs"].recent_errors(20)
    recent_warnings = current_app.config["AdminHTTPReportFuncs"].recent_warnings(20)
    return render_template('report/index.html',
                           issue_count_dict=issue_count_dict,
                           fatal_exception_list=recent_fatal_exceptions,
                           exception_list=recent_exceptions,
                           error_list=recent_errors,
                           warning_list=recent_warnings)


@report.route('/report/<regex("[0-9.]+"):epoch>/<regex("[0-9]+"):source_id>/')
@login_required
def db_log_entry(epoch, source_id):
    db_log_dict = current_app.config["AdminHTTPReportFuncs"].get_db_log_entry(epoch, source_id)
    return render_template('report/db_log_entry.html',
                           db_log_dict=db_log_dict)


