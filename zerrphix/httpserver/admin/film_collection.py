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
import pprint
from zerrphix.util.filesystem import get_file_extension
from zerrphix.util.filesystem import make_dir
from zerrphix.util.image import resize_and_crop

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json
import mimetypes
import json

film_collection = Blueprint('film_collection', __name__)

log = logging.getLogger(__name__)


@film_collection.route('/film_collection')
#@film_collection.route('/film_collection/<regex("[1-9]([0-9]+)?"):page>/<regex("[1-9]([0-9]+)?"):limit>')
@login_required
def film_collection_index(page=1, limit=50):
    log.debug('film_collection_index request args %s', request.args)
    sort_type = 'alpha_asc'
    if 'sort_type' in request.args:
        if request.args.get('sort_type') in {'alpha_desc'}:
            sort_type = request.args.get('sort_type')
    page = 1
    if 'page' in request.args:
        if request.args.get('page').isdigit():
            page = int(request.args.get('page'))
    limit = 50
    if 'limit' in request.args:
        if request.args.get('limit').isdigit():
            limit = int(request.args.get('limit'))
    log.debug('film_collection_index limit %s, page %s', limit, page)
    links=5
    total_film_collections = current_app.config["AdminHTTPFilmCollectionFuncs"].get_total_num_collections()
    #log.error(total_films)
    # deal with div 0
    offset, last_page = current_app.config["AdminHTTPGenFuncs"].process_pagiation(
        page, limit, total_film_collections
    )
    film_collection_list = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_list(
        limit=limit, offset=offset, sort_type=sort_type)
    return render_template('film_collection/index.html',
                           films=film_collection_list,
                           last_page=last_page, links=links,
                           sort_type=sort_type,
                           limit=limit, page=page, base_link='/film_collection')


@film_collection.route('/film_collection/searchFilmCollections')
@login_required
def film_collection_searchFilmCollections():
    # todo more sanitizeation of user input
    search = request.args.get('search_text')
    if search is None:
        return Response('{"success":false,"error":"name canot be empty}', mimetype='text/plain')
    else:
        search = re.sub(r'''[^\w\-_\s]''', '', search, flags=re.I | re.U)
        films = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_list(search=search)
        if films:
            warning = json.dumps('')
        else:
            warning = json.dumps(escape('No results from search with %s' % search))
    return Response('{"success":true,"error":null,"films": %s,"warning": %s}' % (json.dumps(films),
                                                                                 warning),
                    mimetype='text/plain')

@film_collection.route('/film_collection/searchFilms')
@login_required
def film_collection_searchFilms():
    # todo more sanitizeation of user input
    search = request.args.get('search_text')
    if search is None:
        return Response('{"success":false,"error":"name canot be empty}', mimetype='text/plain')
    else:
        search = re.sub(r'''[^\w\-_\s]''', '', search, flags=re.I | re.U)
        films = current_app.config["AdminHTTPFilmCollectionFuncs"].film_list(search)
        if films:
            warning = json.dumps('')
        else:
            warning = json.dumps(escape('No results from search with %s' % search))
    return Response('{"success":true,"error":null,"films": %s,"warning": %s}' % (json.dumps(films),
                                                                                 warning),
                    mimetype='text/plain')


@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/summary', methods=['GET', 'POST'])
@login_required
def film_collection_summary(zp_film_collection_id):
    film_collection_title = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_title(
        zp_film_collection_id,
        int(current_user.id))
    log.debug('film_collection_title %s', film_collection_title)
    film_collection_overview = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_overview(
        zp_film_collection_id,
        int(current_user.id))
    log.debug('film_collection_overview %s', film_collection_overview)
    film_collection_poster_raw_image_id = current_app.config[
        "AdminHTTPFilmCollectionFuncs"].get_user_film_collection_raw_image_id(
        zp_film_collection_id, 3,
        int(current_user.id))
    log.debug('film_collection_poster_raw_image_id %s', film_collection_poster_raw_image_id)
    film_collection_backdrop_raw_image_id = current_app.config[
        "AdminHTTPFilmCollectionFuncs"].get_user_film_collection_raw_image_id(
        zp_film_collection_id, 4,
        int(current_user.id))
    log.debug('film_collection_backdrop_raw_image_id %s', film_collection_backdrop_raw_image_id)
    render_templates_display_dict = \
        current_app.config["AdminHTTPGenFuncs"].get_library_render_templates_display_dict(
            current_user.id, 'film_collection', ['icon', 'synopsis', 'poster', 'backdrop']
        )
    log.debug('render_templates_display_dict %s', pprint.pformat(render_templates_display_dict))
    for image_type_id in render_templates_display_dict:
        for icon_sub_type_id in render_templates_display_dict[image_type_id]['icon_sub_type_list']:
            render_templates_display_dict[image_type_id]['icon_sub_type_list'][icon_sub_type_id]['render_hash_id'] = \
                current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_rendered_image(
                    zp_film_collection_id,
                    image_type_id,
                    icon_sub_type_id,
                    int(current_user.id))
    return render_template('film_collection/summary.html', film_collection_title=film_collection_title,
                           zp_film_collection_id=zp_film_collection_id,
                           film_collection_overview=film_collection_overview,
                           film_collection_poster_raw_image_id=film_collection_poster_raw_image_id,
                           film_collection_backdrop_raw_image_id=film_collection_backdrop_raw_image_id,
                           render_templates_display_dict=render_templates_display_dict)


@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/<regex("[a-zA-Z0-9_]+"):image_type>/<regex("[0-9]+"):zp_icon_sub_type_id>/render')
@login_required
# if request.method == 'POST':
def film_collection_render_image(zp_film_collection_id, image_type, zp_icon_sub_type_id):
    return_image = current_app.config["AdminHTTPFilmCollectionArtwork"].render(zp_film_collection_id,
                                                                     current_user.id, image_type, zp_icon_sub_type_id)
    cimage = StringIO()
    return_image.save(cimage, 'png')
    return_image.close()
    cimage.seek(0)
    # mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
    mimetype = '.png'
    # except:
    # mimetype = 'image'
    return send_file(cimage, mimetype)

@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/overview', methods=['GET', 'POST'])
@login_required
def film_collection_overview(zp_film_collection_id):
    if request.method == 'POST':
        if 'zp_overview_ident' in request.form and 'zp_overview_overview' in request.form:
            zp_overview_ident = request.form['zp_overview_ident']
            overview = request.form['zp_overview_overview']
            log.debug('zp_overview_ident %s', zp_overview_ident)
            log.debug('zp_overview_overview %s', overview)
            current_app.config["AdminHTTPFilmCollectionFuncs"].update_film_collection_overview(zp_film_collection_id,
                                                                                               int(current_user.id),
                                                                                               zp_overview_ident,
                                                                                               overview)
    # todo get this from function
    lang_name_dict = {1823: 'English'}
    eapi_name_dict = {1: 'TMDB'}
    film_collection_title = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_title(
        zp_film_collection_id,
        int(current_user.id))
    film_collection_overview_list = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_overview_list(
        zp_film_collection_id, int(current_user.id))
    log.debug('film_collection_overview_list %s', film_collection_overview_list)
    user_film_collection_overview_id = current_app.config[
        "AdminHTTPFilmCollectionFuncs"].get_user_film_collection_overview_id(
        zp_film_collection_id,
        int(current_user.id))
    log.debug('user_film_collection_overview_id %s', user_film_collection_overview_id)
    return render_template('film_collection/overview.html', film_collection_title=film_collection_title,
                           film_collection_overview_list=film_collection_overview_list,
                           zp_film_collection_id=zp_film_collection_id,
                           user_film_collection_overview_id=user_film_collection_overview_id,
                           lang_name_dict=lang_name_dict, eapi_name_dict=eapi_name_dict)

@film_collection.route('/film_collection/create', methods=['GET', 'POST'])
@login_required
def film_collection_create():
    collection_add_result_message = ''
    if request.method == 'POST':
        film_collection_film_list = []
        if 'film_in_collection_json' in request.form and 'film_in_collection_title' in request.form \
            and 'film_in_collection_overview' in request.form:
            log.error(request.form['film_in_collection_json'])
            log.error(request.form['film_in_collection_title'])
            log.error(request.form['film_in_collection_overview'])
            log.error(current_user.privileges)
            log.error(current_user.user_langs)
            #raise TypeError
            try:
                post_json = json.loads(request.form['film_in_collection_json'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
                collection_add_result_message = 'AttributeError on converting film_in_collection_json to json'
            except ValueError as e:
                log.warning('ValueError %s', e)
                collection_add_result_message = 'ValueError on converting film_in_collection_json to json'
            else:
                for film_id in post_json:
                    log.debug('film_id %s', film_id)
                    if film_id.isdigit():
                        film_collection_film_list.append(int(film_id))
            if len(film_collection_film_list) > 0:
                post_title = request.form['film_in_collection_title']
                post_overview = request.form['film_in_collection_overview']
                zp_film_collection_id = current_app.config["AdminHTTPFilmCollectionFuncs"].create_collection(
                    post_title,
                    post_overview,
                    # change to global library id
                    current_user.user_langs[1]
                )
                log.debug('film_collection_film_list %s', film_collection_film_list)
                for film_id in film_collection_film_list:
                    log.debug('adding film_id %s to zp_film_collection_id')
                    current_app.config["AdminHTTPFilmCollectionFuncs"].add_film(zp_film_collection_id, film_id)
                collection_add_result_message = escape('Added file collection %s' %
                                                       request.form['film_in_collection_title'])
            else:
                log.error('len(film_collection_film_list) %s is not > 0', len(film_collection_film_list))
                collection_add_result_message = 'len(film_collection_film_list) %s is not > 0'
        else:
            log.error('film_in_collection_json not in request.form %s', request.form.keys())
    return render_template('film_collection/create.html',
                           collection_add_result_message = collection_add_result_message)


@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/films', methods=['GET', 'POST'])
@login_required
def film_collection_films(zp_film_collection_id):
    if request.method == 'POST':
        film_collection_film_list = []
        if 'film_in_collection_json' in request.form:
            log.debug(request.form['film_in_collection_json'])
            try:
                post_json = json.loads(request.form['film_in_collection_json'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
            except ValueError as e:
                log.warning('ValueError %s', e)
            else:
                for film_id in post_json:
                    log.debug('film_id %s', film_id)
                    if film_id.isdigit():
                        film_collection_film_list.append(int(film_id))
            if len(film_collection_film_list) > 0:
                current_app.config["AdminHTTPFilmCollectionFuncs"].clear_films(zp_film_collection_id)
                log.debug('film_collection_film_list %s', film_collection_film_list)
                for film_id in film_collection_film_list:
                    log.debug('adding film_id %s to zp_film_collection_id')
                    current_app.config["AdminHTTPFilmCollectionFuncs"].add_film(zp_film_collection_id, film_id)
            else:
                log.error('len(film_cast_post_list) %s is not > 0', len(film_collection_film_list))
        else:
            log.error('film_in_collection_json not in request.form %s', request.form.keys())
    # todo add role order
    film_collection_title = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_title(
        zp_film_collection_id, int(current_user.id))
    film_collection_films = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_films(
        zp_film_collection_id, int(current_user.id))
    return render_template('film_collection/films.html', film_collection_title=film_collection_title,
                           film_collection_films=film_collection_films,
                           zp_film_collection_id=zp_film_collection_id)

@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/title', methods=['GET', 'POST'])
@login_required
def film_collection_title(zp_film_collection_id):
    if request.method == 'POST':
        if 'zp_title_ident' in request.form and 'zp_title_title' in request.form:
            zp_title_ident = request.form['zp_title_ident']
            title = request.form['zp_title_title']
            log.debug('zp_title_ident %s', zp_title_ident)
            log.debug('zp_title_title %s', title)
            current_app.config["AdminHTTPFilmCollectionFuncs"].update_film_collection_title(zp_film_collection_id,
                                                                                            int(current_user.id),
                                                                                            zp_title_ident,
                                                                                            title)
    # todo get this from function
    lang_name_dict = {1823: 'English'}
    eapi_name_dict = {1: 'TMDB'}
    tile_type_name_dict = {1: 'Normal', 2: 'Origional Title'}
    film_collection_title = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_title(
        zp_film_collection_id,
        int(current_user.id))
    film_collection_title_list = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_title_list(
        zp_film_collection_id, int(current_user.id))
    user_film_collection_title_id = current_app.config[
        "AdminHTTPFilmCollectionFuncs"].get_user_film_collection_title_id(
        zp_film_collection_id,
        int(current_user.id))
    return render_template('film_collection/title.html', film_collection_title=film_collection_title,
                           film_collection_title_list=film_collection_title_list,
                           zp_film_collection_id=zp_film_collection_id,
                           user_film_collection_title_id=user_film_collection_title_id, lang_name_dict=lang_name_dict,
                           eapi_name_dict=eapi_name_dict, tile_type_name_dict=tile_type_name_dict)


@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/<regex("poster|backdrop"):image_type>',
                       methods=['GET', 'POST'])
@login_required
# if request.method == 'POST':
def film_collection_image(zp_film_collection_id, image_type):
    log.debug(image_type)
    filename_regex = r'''^[\w\-\_\.\(\)\s]+\.(?:jpg|jpeg|png|bmp|gif)$'''
    # TODO: error message when filesize is too big
    raw_image_group_max_count_dict = {'poster': 4, 'backdrop': 2}
    raise_user_alert = False
    raise_alter_message = ''
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename == '':
                if file and re.match(filename_regex, file.filename, flags=re.I | re.U):
                    # todo set/get from max_content_length in db
                    max_content_length = 5 * 1024 * 1024
                    log.debug('content-length %s', request.content_length)
                    if request.content_length <= max_content_length:
                        new_film_collection_image_folder = os.path.join(
                            current_app.config["AdminHTTPFilmCollectionFuncs"].global_config_dict
                            ['downloaded_images_root_path'], 'film_collection',
                            zp_film_collection_id)
                        log.debug('making foldernew_film_collection_image_folder %s if does not exist.',
                                  new_film_collection_image_folder)
                        if make_dir(new_film_collection_image_folder):
                            log.debug('new_film_collection_image_folder %s exists', new_film_collection_image_folder)
                            new_film_collection_poster_image_folder = os.path.join(
                                current_app.config["AdminHTTPFilmCollectionFuncs"].global_config_dict
                                ['downloaded_images_root_path'], 'film_collection',
                                zp_film_collection_id)
                            new_image_uuid = uuid.uuid4()
                            new_film_collection_image_filename = '%s.%s' % (
                            new_image_uuid, get_file_extension(file.filename))
                            new_film_collection_image_path = os.path.join(new_film_collection_poster_image_folder,
                                                                          new_film_collection_image_filename)
                            log.debug(new_film_collection_image_path)
                            file.save(new_film_collection_image_path)
                            current_app.config["AdminHTTPFilmCollectionFuncs"].add_new_film_collection_raw_image(
                                zp_film_collection_id,
                                str(current_user.id),
                                current_app.config[
                                    "AdminHTTPFilmCollectionFuncs"].image_type_id_dict[image_type],
                                new_film_collection_image_filename,
                                file.filename)
                        else:
                            log.error('failed to make dir %s', new_film_collection_image_folder)
                            raise_alter_message = escape('failed to make dir %s' % new_film_collection_image_folder)
                    else:
                        log.error('content-length %d which is over %s', request.content_length, max_content_length)
                        file.save('/dev/null')
                        raise_user_alert = True
                        raise_alter_message = 'content-length %d which is over %s' % (request.content_length,
                                                                                      max_content_length)
                else:
                    log.error('not file or match filed with %s on %s', filename_regex, file.filename)
                    raise_alter_message = escape('not file or match filed with %s on %s' %
                                                 (filename_regex, file.filename))
            else:
                log.error('file.filename is empty %s', file.filename)
                raise_alter_message = escape('file.filename is empty %s' % file.filename)
        else:
            log.error('file not in %s', request.files)
            raise_alter_message = escape('file not in %s' % request.files)
    render_type_dict = {'poster': 'quarter', 'backdrop': 'half'}
    raw_images_list = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_raw_image_list(
        zp_film_collection_id,
        current_app.config[
            "AdminHTTPFilmCollectionFuncs"].image_type_id_dict[image_type])
    user_raw_image_id = current_app.config["AdminHTTPFilmCollectionFuncs"].get_user_film_collection_raw_image_id(
        zp_film_collection_id,
        current_app.config[
            "AdminHTTPFilmCollectionFuncs"].image_film_collection_entity_type_id_dict[image_type],
        int(current_user.id))
    log.debug('user_raw_image_id %s', user_raw_image_id)
    film_collection_title = current_app.config["AdminHTTPFilmCollectionFuncs"].film_collection_title(zp_film_collection_id,
                                                                                           int(current_user.id))
    log.debug(raw_images_list)
    raw_image_group_list = []
    raw_image_group_count = 0
    temp_list = []
    for raw_image in raw_images_list:
        if raw_image_group_count + 1 > raw_image_group_max_count_dict[image_type]:
            raw_image_group_count = 0
            raw_image_group_list.append(temp_list)
            temp_list = []
        temp_list.append(raw_image)
        raw_image_group_count += 1
    if temp_list:
        raw_image_group_list.append(temp_list)
    log.debug('raw_image_group_list %s', raw_image_group_list)
    return render_template('film_collection/image.html',
                           raw_image_group_list=raw_image_group_list, film_collection_title=film_collection_title,
                           render_type=render_type_dict[image_type],
                           raise_user_alert=raise_user_alert, raise_alter_message=raise_alter_message,
                           image_type=image_type, zp_film_collection_id=zp_film_collection_id,
                           user_raw_image_id=user_raw_image_id)


@film_collection.route('/i/raw/film_collection/<regex("[0-9]+"):zp_film_collection_raw_image_id>')
# @login_required
def get_film_collection_raw_image(zp_film_collection_raw_image_id):
    image_filename, zp_film_collection_id = current_app.config["AdminHTTPFilmCollectionFuncs"].get_film_collection_raw_image_filename(
        zp_film_collection_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPFilmCollectionFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'film_collection', str(zp_film_collection_id), image_filename)
        # log.warning(vars())
        log.warning(image_path)
        if os.path.exists(image_path):
            # try:
            mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
            # except:
            # mimetype = 'image'
            return send_file(image_path, mimetype)
        else:
            log.warning('image_path %s does not exist', image_path)
            return abort(404)
    else:
        log.warning('zp_film_collection_raw_image_id %s does not exist in ZP_FILM_RAW_IMAGE', zp_film_collection_raw_image_id)
        return abort(404)


@film_collection.route('/i/rendered/film_collection/<regex("[0-9]+"):zp_film_collection_rendered_image_id>')
# @login_required
def get_film_collection_rendered_image(zp_film_collection_rendered_image_id):
    image_filename, template_name, zp_film_collection_id = current_app.config[
        "AdminHTTPFilmCollectionFuncs"].get_film_collection_rendered_image_filename(zp_film_collection_rendered_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPFilmCollectionFuncs"].global_config_dict[
                                      'rendered_image_root_path'],
                                  'film_collection', template_name, str(zp_film_collection_id), image_filename)
        # log.warning(vars())
        log.warning(image_path)
        if os.path.exists(image_path):
            # try:
            # rimage = Image.open(image_path)
            # mimage = resize_and_crop(image_path, (width, height))
            # cimage = cStringIO.StringIO()
            mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
            # mimetype = '.png'
            # except:
            # mimetype = 'image'
            return send_file(image_path, mimetype)
        else:
            log.error('image_path %s does not exist', image_path)
            return abort(404)
    else:
        log.error('zp_film_collection_rendered_image_id %s does not exist in ZP_FILM_RENDER_HASH', zp_film_collection_rendered_image_id)
        return abort(404)


@film_collection.route('/i/raw/film_collection/<regex("[0-9]+"):zp_film_collection_raw_image_id>/'
            'resize/<regex("[0-9]+"):width>/<regex("[0-9]+"):height>/<regex("top|bottom|middle"):crop_type>/'
            '<regex("[0-9]+"):asptect_ratio_change_threshold>')
# @login_required
def get_film_collection_raw_image_resized(zp_film_collection_raw_image_id, width, height, crop_type,
                               asptect_ratio_change_threshold):
    image_filename, zp_film_collection_id = current_app.config["AdminHTTPFilmCollectionFuncs"].get_film_collection_raw_image_filename(
        zp_film_collection_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPFilmCollectionFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'film_collection', str(zp_film_collection_id), image_filename)
        # log.warning(vars())
        log.warning(image_path)
        if os.path.exists(image_path):
            # try:
            asptect_ratio_change_threshold = int(asptect_ratio_change_threshold)
            if asptect_ratio_change_threshold > 0:
                return_image = resize_and_crop(image_path, (int(width), int(height)), crop_type=crop_type,
                                               asptect_ratio_change_threshold=asptect_ratio_change_threshold)
            else:
                return_image = resize_and_crop(image_path, (int(width), int(height)), crop_type=crop_type)
            cimage = StringIO()
            return_image.save(cimage, 'png')
            cimage.seek(0)
            # mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
            mimetype = '.png'
            # except:
            # mimetype = 'image'
            return send_file(cimage, mimetype)
        else:
            log.error('image_path %s does not exist', image_path)
            return abort(404)
    else:
        log.error('zp_film_collection_raw_image_id %s does not exist in ZP_FILM_RAW_IMAGE', zp_film_collection_raw_image_id)
        return abort(404)

@film_collection.route('/film_collection/<regex("[0-9]+"):zp_film_collection_id>/<regex("poster|backdrop"):image_type>/set/'
            '<regex("[0-9]+"):zp_film_collection_raw_image_id>')
@login_required
def film_collection_image_update(zp_film_collection_id, image_type, zp_film_collection_raw_image_id):
    if current_app.config["AdminHTTPFilmCollectionFuncs"].set_user_film_collection_raw_image(zp_film_collection_id, image_type,
                                                    zp_film_collection_raw_image_id, current_user.id) is True:
        return Response('{"success": true, "error": "null"}', mimetype='text/plain')
    else:
        return Response('{"success": false, "error": "unkown"}', mimetype='text/plain')