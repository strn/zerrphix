# from PIL import Image
import logging

from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import request
from flask_login import login_required
import tempfile
import os.path
import shutil
import re
from zerrphix.util.filesystem import make_dir
import zipfile
import shutil
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

template = Blueprint('template', __name__)

log = logging.getLogger(__name__)


@template.route('/template', methods=['GET', 'POST'])
@login_required
def template_index():
    if request.method == 'POST':
        post_data = request.form
        process_zip = False
        process_zip_dict = None
        if post_data['type'] == 'add':
            if post_data['ref_name']:
                save_temaplte_name = re.sub(r'''[\s]+''', '_', post_data['ref_name'])
                db_template_name = re.sub(r'''[\s]+''', ' ', post_data['ref_name'])
                name_is_free = current_app.config["AdminHTTPTemplateFuncs"].check_template_name_free(db_template_name)
                if name_is_free is True:
                    process_zip_dict = {0:{'type': 'add',
                                           'template_folder': os.path.join(
                                               current_app.config["global_config_dict"]['template_store_path']
                                                                           , save_temaplte_name),
                                           'db_template_name': db_template_name,
                                           'zip_file_key': 'zip_file'}}
        elif post_data['type'] == 'edit':
            for zip_file_key in request.files:
                log.debug('zip_file_key %s', zip_file_key)
                if request.files[zip_file_key].filename != '':
                    match = re.match(r'''^(?P<zp_template_id>\d+)_zip_file$''', zip_file_key)
                    if match:
                        zp_template_id = match.groupdict()['zp_template_id']
                        template_dict = current_app.config["AdminHTTPGenFuncs"].get_template_dict(zp_template_id)
                        if os.path.isdir(template_dict['path']):
                            if process_zip_dict is None:
                                process_zip_dict = {}
                            process_zip_dict[zp_template_id] = {'type': 'update',
                                                                    'template_folder': template_dict['path'],
                                                                    'db_template_name': template_dict['ref_name'],
                                                                    'zip_file_key': zip_file_key
                                                                    }
                    #log.error('zip_file %s', zip_file)

        log.debug('process_zip_dict %s', process_zip_dict)
        if process_zip_dict:
            for zp_template_id in process_zip_dict:
                zip_file = request.files[process_zip_dict[zp_template_id]['zip_file_key']]
                max_content_length = 200 * 1024 * 1024 * len(process_zip_dict)
                if request.content_length <= max_content_length:
                    temp_save_folder = tempfile.mkdtemp()
                    zip_file_save_path = os.path.join(temp_save_folder, 'template.zip')
                    zip_file.save(zip_file_save_path)
                    template_store_path = current_app.config["global_config_dict"]['template_store_path']
                    if make_dir(template_store_path):
                        if make_dir(process_zip_dict[zp_template_id]['template_folder']):
                            try:
                                zip_ref = zipfile.ZipFile(zip_file_save_path, 'r')
                            except OSError as e:
                                log.error('OSerror %s', str(e))
                            else:
                                shutil.rmtree(process_zip_dict[zp_template_id]['template_folder'])
                                zip_ref.extractall(process_zip_dict[zp_template_id]['template_folder'])
                                log.debug('extracting %s to %s',
                                          zip_file_save_path,
                                          process_zip_dict[zp_template_id]['template_folder'])
                                if process_zip_dict[zp_template_id]['type'] == 'add':
                                    current_app.config["AdminHTTPTemplateFuncs"].add_template(
                                        process_zip_dict[zp_template_id]['db_template_name'],
                                        process_zip_dict[zp_template_id]['template_folder']
                                        )
                                else:
                                    current_app.config["AdminHTTPTemplateFuncs"].update_template(
                                        zp_template_id
                                    )
                                    #current_app.config["AdminHTTPGenFuncs"].clear_template_renders(
                                    #    zp_template_id
                                    #)
                                    current_app.config["AdminHTTPGenFuncs"].set_process_force_run(7)
                                    current_app.config["AdminHTTPGenFuncs"].set_process_force_run(17)
                        else:
                            log.error('cannot make dir %s', process_zip_dict[zp_template_id]['template_folder'])
                    shutil.rmtree(temp_save_folder)


                        #log.debug('making foldernew_film_image_folder %s if does not exist.', new_film_image_folder)
                        #if make_dir(new_film_image_folder):
                        #    log.debug('new_film_image_folder %s exists', new_film_image_folder)
                        #    new_film_poster_image_folder = os.path.join(
                        #        current_app.config["AdminHTTPFilmFuncs"].global_config_dict
                        #        ['downloaded_images_root_path'], 'film',
                        #        zp_film_id)
                        #    new_image_uuid = uuid.uuid4()
                        #    new_film_image_filename = '%s.%s' % (new_image_uuid, get_file_extension(file.filename))
                        #    new_film_image_path = os.path.join(new_film_poster_image_folder, new_film_image_filename)
                        #    log.debug(new_film_image_path)
                        #    file.save(new_film_image_path)
                        #    current_app.config["AdminHTTPFilmFuncs"].add_new_film_raw_image(zp_film_id,
                        #                                                                    str(current_user.id),
                        #                                                                    current_app.config[
                        #                                                                        "AdminHTTPFilmFuncs"].image_type_id_dict[
                        #                                                                        image_type],
                        #                                                                    new_film_image_filename,
                        #                                                                    file.filename)
                        #else:
                        #    log.error('failed to make dir %s', new_film_image_folder)
                        #    raise_alter_message = escape('failed to make dir %s' % new_film_image_folder)
                else:
                    log.error('content-length %d is over %s', request.content_length, max_content_length)
                    zip_file.save('/dev/null')
    template_dict = current_app.config["AdminHTTPGenFuncs"].get_templates_info_dict()
    template_keys = ['ref_name',
                     'path_type',
                     'zip_file']
    template_title_dict = {'ref_name': 'Name',
                           'path_type': 'Type',
                           'zip_file': 'Upload Update'}
    template_add_dict = {'ref_name': 'text',
                         'zip_file': 'file'}
    template_edit_dict = {'ref_name': 'text',
                          'path_type': 'lookup',
                      'zip_file': 'file'}
    template_lookup_dict = {'path_type': {
         1: 'SYSTEM', 2: 'User'
    }}
    log.debug('template_dict %s', template_dict)
    return render_template('template/index.html',
                           template_keys=template_keys,
                           template_title_dict=template_title_dict,
                           template_add_dict=template_add_dict,
                           template_edit_dict=template_edit_dict,
                           template_lookup_dict=template_lookup_dict,
                           template_dict=template_dict)
