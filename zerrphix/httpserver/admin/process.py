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
from flask_login import current_user
from flask_login import login_required

from zerrphix.util.filesystem import get_file_extension
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import resize_and_crop

import json
import mimetypes
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

process = Blueprint('process', __name__)

log = logging.getLogger(__name__)


@process.route('/process', methods=['GET', 'POST'])
@login_required
def process_index():
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
        # pass
        # log.warning(dir(request.form))
        #log.error('request.form %s', request.form)
        valid_entry_regex = r'''^(?P<zp_process_id>\d+)_(?P<section>enabled|run_interval|force_run|run_between|run_between_start|run_between_end)$'''
        post_data = request.form
        #log.error(post_data.keys())
        process_dict = {}
        if post_data:
            for post_data_key in post_data:
                #log.error(post_data_key)
                post_data_key_match = re.match(valid_entry_regex, post_data_key)
                if post_data_key_match:
                    post_data_key_match_group_dict = post_data_key_match.groupdict()
                    if post_data_key_match_group_dict['zp_process_id'] not in process_dict:
                        process_dict[post_data_key_match_group_dict['zp_process_id']] = {}
                    process_dict[post_data_key_match_group_dict['zp_process_id']][
                        post_data_key_match_group_dict['section']] = post_data[post_data_key]

                    #zp_process_id = post_data_key_match_group_dict['zp_process_id']
                    #process_section_value = post_data[post_data_key]
                    #section = post_data_key_match_group_dict['section']
                    #log.debug('post_data_key %s, post_data_key_match_group_dict %s, value %s', post_data_key,
                    #          post_data_key_match_group_dict, post_data[post_data_key])
                    #current_app.config["AdminHTTPProcessFuncs"].set_process_section(zp_process_id, section,
                                                                                        #process_section_value)
                else:
                    log.debug('post_data_key %s failed to match valid_entry_regex %s', post_data_key,
                              valid_entry_regex)
            for zp_process_id in process_dict:
                log.debug('zp_process_id %s, %s', zp_process_id, process_dict[zp_process_id])
                current_app.config["AdminHTTPProcessFuncs"].set_process_section(zp_process_id,
                                                                                process_dict[zp_process_id])
        else:
            log.error('post_data %s empty', post_data)
        #if 'tv_genre_list' in request.form:
    process_list = current_app.config["AdminHTTPProcessFuncs"].process_list()
    process_keys = ['zp_process_id',
                    'name',
                    'zp_library_id',
                    'enabled',
                    'last_run_finish' ,
                    'force_run',
                    'run_interval',
                    'run_between',
                    'run_between_start',
                    'run_between_end']
    process_editable_dict = {'enabled':'bool',
                             'run_interval': 'int',
                             'force_run': 'bool',
                             'run_between': 'bool',
                             'run_between_start': 'int',
                             'run_between_end': 'int',
                             }
    return render_template('process/index.html', process_list=process_list, process_keys=process_keys,
                           process_editable_dict=process_editable_dict)