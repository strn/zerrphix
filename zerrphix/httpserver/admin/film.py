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

film = Blueprint('film', __name__)

log = logging.getLogger(__name__)


@film.route('/film')
#@film.route('/film/<regex("[1-9]([0-9]+)?"):page>/<regex("[1-9]([0-9]+)?"):limit>')
@login_required
def film_index():
    log.debug('film index request args %s', request.args)
    sort_type = 'alpha_asc'
    if 'sort_type' in request.args:
        if request.args.get('sort_type') in {'added_desc', 'added_asc', 'alpha_desc'}:
            sort_type = request.args.get('sort_type')
    page = 1
    if 'page' in request.args:
        if request.args.get('page').isdigit():
            page = int(request.args.get('page'))
    limit = 50
    if 'limit' in request.args:
        if request.args.get('limit').isdigit():
            limit = int(request.args.get('limit'))
    log.debug('film index limit %s, page %s', limit, page)
    #request_args = request.args
    links=5
    total_films = current_app.config["AdminHTTPFilmFuncs"].get_total_num_films()
    #log.error(total_films)
    # deal with div 0
    offset, last_page = current_app.config["AdminHTTPGenFuncs"].process_pagiation(
        page, limit, total_films
    )
    film_list = current_app.config["AdminHTTPFilmFuncs"].film_list(limit=limit, offset=offset, sort_type=sort_type)
    return render_template('film/index.html',
                           films=film_list,
                           last_page=last_page, links=links,
                           sort_type=sort_type,
                           limit=limit, page=page, base_link='/film')


# @film.route('/film/<regex("[0-9]+^"):uid>')
# https://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing
@film.route('/film/<regex("[0-9]+"):zp_film_id>')
@login_required
def film_choose_section(zp_film_id):
    # match = re.match(r'''^/film/([0-9]+)$''', request.path)
    return render_template('film_choose_section_index.html',
                           zp_film_id=zp_film_id)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/<regex("poster|backdrop"):image_type>', methods=['GET', 'POST'])
@login_required
# if request.method == 'POST':
def film_image(zp_film_id, image_type):
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
                        new_film_image_folder = os.path.join(current_app.config["AdminHTTPFilmFuncs"].global_config_dict
                                                             ['downloaded_images_root_path'], 'film',
                                                             zp_film_id)
                        log.debug('making foldernew_film_image_folder %s if does not exist.', new_film_image_folder)
                        if make_dir(new_film_image_folder):
                            log.debug('new_film_image_folder %s exists', new_film_image_folder)
                            new_film_poster_image_folder = os.path.join(
                                current_app.config["AdminHTTPFilmFuncs"].global_config_dict
                                ['downloaded_images_root_path'], 'film',
                                zp_film_id)
                            new_image_uuid = uuid.uuid4()
                            new_film_image_filename = '%s.%s' % (new_image_uuid, get_file_extension(file.filename))
                            new_film_image_path = os.path.join(new_film_poster_image_folder, new_film_image_filename)
                            log.debug(new_film_image_path)
                            file.save(new_film_image_path)
                            current_app.config["AdminHTTPFilmFuncs"].add_new_film_raw_image(zp_film_id,
                                                                                            str(current_user.id),
                                                                                            current_app.config[
                                                                                                "AdminHTTPFilmFuncs"].image_type_id_dict[
                                                                                                image_type],
                                                                                            new_film_image_filename,
                                                                                            file.filename)
                        else:
                            log.error('failed to make dir %s', new_film_image_folder)
                            raise_alter_message = escape('failed to make dir %s' % new_film_image_folder)
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
    raw_images_list = current_app.config["AdminHTTPFilmFuncs"].film_raw_image_list(zp_film_id,
                                                                                   current_app.config[
                                                                                       "AdminHTTPFilmFuncs"].image_type_id_dict[
                                                                                       image_type])
    user_raw_image_id = current_app.config["AdminHTTPFilmFuncs"].get_user_film_raw_image_id(zp_film_id,
                                                                                            current_app.config[
                                                                                                "AdminHTTPFilmFuncs"].image_film_entity_type_id_dict[
                                                                                                image_type],
                                                                                            int(current_user.id))
    log.debug('user_raw_image_id %s', user_raw_image_id)
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
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
    return render_template('film/image.html',
                           raw_image_group_list=raw_image_group_list, film_title=film_title,
                           render_type=render_type_dict[image_type],
                           raise_user_alert=raise_user_alert, raise_alter_message=raise_alter_message,
                           image_type=image_type, zp_film_id=zp_film_id, user_raw_image_id=user_raw_image_id)

@film.route('/film/<regex("[0-9]+"):zp_film_id>/<regex("[a-zA-Z0-9_]+"):image_type>/<regex("[0-9]+"):zp_icon_sub_type_id>/render')
@login_required
# if request.method == 'POST':
def film_render_image(zp_film_id, image_type, zp_icon_sub_type_id):
    return_image = current_app.config["AdminHTTPFilmArtwork"].render(zp_film_id, current_user.id, image_type, zp_icon_sub_type_id)
    cimage = StringIO()
    return_image.save(cimage, 'png')
    return_image.close()
    cimage.seek(0)
    # mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
    mimetype = '.png'
    # except:
    # mimetype = 'image'
    return send_file(cimage, mimetype)
# @film.route('/film/<regex("[0-9]+"):zp_film_id>/<regex("poster|backdrop"):image_type>/'
#            'update/<regex("[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.[a-z]{3,4}|clear"):image_filename>')
@film.route('/film/<regex("[0-9]+"):zp_film_id>/<regex("poster|backdrop"):image_type>/set/'
            '<regex("[0-9]+"):zp_film_raw_image_id>')
@login_required
def film_image_update(zp_film_id, image_type, zp_film_raw_image_id):
    if current_app.config["AdminHTTPFilmFuncs"].set_user_film_raw_image(zp_film_id, image_type,
                                                                        zp_film_raw_image_id, current_user.id) is True:
        current_app.config["AdminHTTPGenFuncs"].set_process_force_run(7)
        return Response('{"success": true, "error": "null"}', mimetype='text/plain')
    else:
        return Response('{"success": false, "error": "unkown"}', mimetype='text/plain')


@film.route('/i/raw/film/<regex("[0-9]+"):zp_film_raw_image_id>')
# @login_required
def get_film_raw_image(zp_film_raw_image_id):
    image_filename, zp_film_id = current_app.config["AdminHTTPFilmFuncs"].get_film_raw_image_filename(
        zp_film_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPFilmFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'film', str(zp_film_id), image_filename)
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
        log.warning('zp_film_raw_image_id %s does not exist in ZP_FILM_RAW_IMAGE', zp_film_raw_image_id)
        return abort(404)


@film.route('/i/rendered/film/<regex("[0-9]+"):zp_film_rendered_image_id>')
# @login_required
def get_film_rendered_image(zp_film_rendered_image_id):
    image_filename, template_name, zp_film_id = current_app.config[
        "AdminHTTPFilmFuncs"].get_film_rendered_image_filename(zp_film_rendered_image_id)

    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPFilmFuncs"].global_config_dict[
                                      'rendered_image_root_path'],
                                  'film', str(template_name), str(zp_film_id), image_filename)
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
        log.error('zp_film_rendered_image_id %s does not exist in ZP_FILM_RENDER_HASH', zp_film_rendered_image_id)
        return abort(404)


@film.route('/i/raw/film/<regex("[0-9]+"):zp_film_raw_image_id>/'
            'resize/<regex("[0-9]+"):width>/<regex("[0-9]+"):height>/<regex("top|bottom|middle"):crop_type>/'
            '<regex("[0-9]+"):asptect_ratio_change_threshold>')
# @login_required
def get_film_raw_image_resized(zp_film_raw_image_id, width, height, crop_type,
                               asptect_ratio_change_threshold):
    image_filename, zp_film_id = current_app.config["AdminHTTPFilmFuncs"].get_film_raw_image_filename(
        zp_film_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPFilmFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'film', str(zp_film_id), image_filename)
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
        log.error('zp_film_raw_image_id %s does not exist in ZP_FILM_RAW_IMAGE', zp_film_raw_image_id)
        return abort(404)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/summary', methods=['GET', 'POST'])
@login_required
def film_summary(zp_film_id):
    genre_dict = current_app.config["AdminHTTPGenFuncs"].genre_by_id()
    log.debug('genre_dict %s', genre_dict)
    film_genres = current_app.config["AdminHTTPFilmFuncs"].film_genres(zp_film_id)
    log.debug('film_genres %s', film_genres)
    film_genre_name_list = ''
    for film_genre in film_genres:
        film_genre_name_list += "%s, " % genre_dict[film_genre]
    film_genre_name_list = film_genre_name_list.rstrip(', ')
    log.debug('film_genre_name_list %s', film_genre_name_list)
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
    log.debug('film_title %s', film_title)
    film_overview = current_app.config["AdminHTTPFilmFuncs"].film_overview(zp_film_id, int(current_user.id))
    log.debug('film_overview %s', film_overview)
    film_rating = current_app.config["AdminHTTPFilmFuncs"].film_rating(zp_film_id)
    log.debug('film_rating %s', film_rating)
    film_cast = current_app.config["AdminHTTPFilmFuncs"].film_cast(zp_film_id)
    log.debug('film_cast %s', film_cast)
    film_path = current_app.config["AdminHTTPFilmFuncs"].film_path(current_app.config[
                                                "AdminHTTPFilmFuncs"].get_film_filefolder_id(zp_film_id))
    film_cast_name_list = ''
    for person in film_cast:
        film_cast_name_list += "%s, " % person['name']
    film_cast_name_list = film_cast_name_list.rstrip(', ')
    log.debug('film_cast_name_list %s', film_cast_name_list)
    film_poster_raw_image_id = current_app.config["AdminHTTPFilmFuncs"].get_user_film_raw_image_id(zp_film_id, 3,
                                                                                                   int(current_user.id))
    log.debug('film_poster_raw_image_id %s', film_poster_raw_image_id)
    film_backdrop_raw_image_id = current_app.config["AdminHTTPFilmFuncs"].get_user_film_raw_image_id(zp_film_id, 4,
                                                                                                     int(
                                                                                                         current_user.id))
    log.debug('film_backdrop_raw_image_id %s', film_backdrop_raw_image_id)
    film_rendered_icon_id = 1
    log.debug('film_rendered_icon %s', film_rendered_icon_id)
    film_rendered_synopsis_id = 1
    log.debug('film_rendered_synopsis %s', film_rendered_synopsis_id)
    render_templates_display_dict = \
        current_app.config["AdminHTTPGenFuncs"].get_library_render_templates_display_dict(
            current_user.id, 'film', ['icon', 'synopsis', 'poster', 'backdrop']
        )
    log.debug('render_templates_display_dict %s', pprint.pformat(render_templates_display_dict))
    for image_type_id in render_templates_display_dict:
        for icon_sub_type_id in render_templates_display_dict[image_type_id]['icon_sub_type_list']:
            render_templates_display_dict[image_type_id]['icon_sub_type_list'][icon_sub_type_id]['render_hash_id'] = \
                current_app.config["AdminHTTPFilmFuncs"].film_rendered_image(zp_film_id, image_type_id,
                                                                             icon_sub_type_id,
                                                                             int(current_user.id))
    log.debug('render_templates_display_dict %s', pprint.pformat(render_templates_display_dict))
    return render_template('film/summary.html', film_title=film_title, zp_film_id=zp_film_id,
                           film_genre_name_list=film_genre_name_list, film_overview=film_overview,
                           film_rating=film_rating, film_cast_name_list=film_cast_name_list,
                           film_poster_raw_image_id=film_poster_raw_image_id,
                           film_backdrop_raw_image_id=film_backdrop_raw_image_id,
                           film_rendered_icon_id=film_rendered_icon_id,
                           film_rendered_synopsis_id=film_rendered_synopsis_id,
                           film_path=film_path,
                           render_templates_display_dict=render_templates_display_dict)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/genre', methods=['GET', 'POST'])
@login_required
def film_genre(zp_film_id):
    # todo change to using genre by id
    genre_dict = current_app.config["AdminHTTPGenFuncs"].genre_by_name()
    if request.method == 'POST':
        # log.warning(request.form['film_genre_list'])
        # pass
        # log.warning(dir(request.form))
        film_genre_post_list = []
        if 'film_genre_list' in request.form:
            log.debug(request.form['film_genre_list'])
            try:
                film_genre_json = json.loads(request.form['film_genre_list'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
            except ValueError as e:
                log.warning('ValueError %s', e)
            else:
                for film_genre_id in film_genre_json:
                    log.debug(film_genre_id)
                    if film_genre_id.isdigit():
                        film_genre_post_list.append(int(film_genre_id))
        film_genre_to_set_list = []
        if len(film_genre_post_list) > 0:
            for genre in genre_dict:
                if genre_dict[genre] in film_genre_post_list:
                    film_genre_to_set_list.append(genre_dict[genre])
        if len(film_genre_to_set_list) > 0:
            current_app.config["AdminHTTPFilmFuncs"].clear_genres(zp_film_id)
            for genre in film_genre_to_set_list:
                current_app.config["AdminHTTPFilmFuncs"].add_genre(zp_film_id, genre)
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
    film_genre_list = current_app.config["AdminHTTPFilmFuncs"].film_genres(zp_film_id)
    log.debug(genre_dict)
    log.debug(film_genre_list)
    genre_option_list = []
    film_genre_option_list = []
    for genre in sorted(genre_dict):
        if genre_dict[genre] in film_genre_list:
            film_genre_option_list.append({'name': genre, 'id': genre_dict[genre]})
        else:
            genre_option_list.append({'name': genre, 'id': genre_dict[genre]})
    log.debug(film_genre_option_list)
    log.debug(genre_option_list)
    return render_template('film/genre.html', film_title=film_title,
                           genres=genre_option_list, film_genres=film_genre_option_list, zp_film_id=zp_film_id)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/cast', methods=['GET', 'POST'])
@login_required
def film_cast(zp_film_id):
    if request.method == 'POST':
        # log.warning(request.form['film_genre_list'])
        # pass
        # log.warning(dir(request.form))
        film_cast_post_list = []
        if 'film_actor_json' in request.form:
            log.debug(request.form['film_actor_json'])
            try:
                post_json = json.loads(request.form['film_actor_json'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
            except ValueError as e:
                log.warning('ValueError %s', e)
            else:
                for people_id in post_json:
                    log.debug(people_id)
                    if people_id.isdigit():
                        film_cast_post_list.append(int(people_id))
        if len(film_cast_post_list) > 0:
            current_app.config["AdminHTTPFilmFuncs"].clear_cast(zp_film_id)
            for people_id in film_cast_post_list:
                current_app.config["AdminHTTPFilmFuncs"].add_cast(zp_film_id, people_id)
    # todo add role order
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
    film_cast_list = current_app.config["AdminHTTPFilmFuncs"].film_cast(zp_film_id)
    return render_template('film/cast.html', film_title=film_title, film_cast=film_cast_list,
                           zp_film_id=zp_film_id)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/overview', methods=['GET', 'POST'])
@login_required
def film_overview(zp_film_id):
    if request.method == 'POST':
        if 'zp_overview_ident' in request.form and 'zp_overview_overview' in request.form:
            zp_overview_ident = request.form['zp_overview_ident']
            zp_overview_ident = request.form['zp_overview_ident']
            overview = request.form['zp_overview_overview']
            log.debug('zp_overview_ident %s', zp_overview_ident)
            log.debug('zp_overview_overview %s', overview)
            current_app.config["AdminHTTPFilmFuncs"].update_film_overview(zp_film_id,
                                                                          int(current_user.id), zp_overview_ident,
                                                                          overview)
    # todo get this from function
    lang_name_dict = current_app.config["AdminHTTPGenFuncs"].get_lang_name_dict(1)
    eapi_name_dict = current_app.config["AdminHTTPGenFuncs"].get_eapi_dict(1)
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
    film_overview_list = current_app.config["AdminHTTPFilmFuncs"].film_overview_list(zp_film_id, int(current_user.id))
    log.debug('film_overview_list %s', film_overview_list)
    user_film_overview_id = current_app.config["AdminHTTPFilmFuncs"].get_user_film_overview_id(zp_film_id,
                                                                                               int(current_user.id))
    log.debug('user_film_overview_id %s', user_film_overview_id)
    return render_template('film/overview.html', film_title=film_title, film_overview_list=film_overview_list,
                           zp_film_id=zp_film_id, user_film_overview_id=user_film_overview_id,
                           lang_name_dict=lang_name_dict, eapi_name_dict=eapi_name_dict)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/title', methods=['GET', 'POST'])
@login_required
def film_title(zp_film_id):
    if request.method == 'POST':
        if 'zp_title_ident' in request.form and 'zp_title_title' in request.form:
            zp_title_ident = request.form['zp_title_ident']
            title = request.form['zp_title_title']
            log.debug('zp_title_ident %s', zp_title_ident)
            log.debug('zp_title_title %s', title)
            current_app.config["AdminHTTPFilmFuncs"].update_film_title(zp_film_id,
                                                                       int(current_user.id), zp_title_ident,
                                                                       title)
    # todo get this from function
    lang_name_dict = current_app.config["AdminHTTPGenFuncs"].get_lang_name_dict(1)
    eapi_name_dict = current_app.config["AdminHTTPGenFuncs"].get_eapi_dict(1)
    tile_type_name_dict = {1: 'Normal', 2: 'Origional Title'}
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
    film_title_list = current_app.config["AdminHTTPFilmFuncs"].film_title_list(zp_film_id, int(current_user.id))
    user_film_title_id = current_app.config["AdminHTTPFilmFuncs"].get_user_film_title_id(zp_film_id,
                                                                                         int(current_user.id))
    return render_template('film/title.html', film_title=film_title, film_title_list=film_title_list,
                           zp_film_id=zp_film_id, user_film_title_id=user_film_title_id, lang_name_dict=lang_name_dict,
                           eapi_name_dict=eapi_name_dict, tile_type_name_dict=tile_type_name_dict)


@film.route('/film/<regex("[0-9]+"):zp_film_id>/rating', methods=['GET', 'POST'])
@login_required
def film_rating(zp_film_id):
    if request.method == 'POST':
        # log.warning(request.form['film_genre_list'])
        # pass
        log.warning(request.form.keys())
        if 'rating' in request.form:
            log.warning(request.form['rating'])
            rating = request.form['rating']
            if rating.isdigit():
                rating = int(rating)
                if rating >= 1 and rating <= 10:
                    current_app.config["AdminHTTPFilmFuncs"].update_rating(zp_film_id, rating)
    # todo add role order
    film_title = current_app.config["AdminHTTPFilmFuncs"].film_title(zp_film_id, int(current_user.id))
    rating = current_app.config["AdminHTTPFilmFuncs"].film_rating(zp_film_id)
    film_ratings = []
    for i in range(1, 11):
        if i == rating:
            film_ratings.append({'rating': i, 'selected': True})
        else:
            film_ratings.append({'rating': i, 'selected': False})
    # log.warning(film_title_id, film_title_text)
    return render_template('film/rating.html', film_title=film_title, film_ratings=film_ratings,
                           zp_film_id=zp_film_id)


@film.route('/film/unIdentified')
@login_required
def film_unidentified():
    # todo more sanitizeation of user input
    unidentified = current_app.config["AdminHTTPFilmFuncs"].get_unidentified_films()
    return render_template('film/unidentified.html', unidentified=unidentified)

@film.route('/film/invalidFileFolder')
@film.route('/film/invalidFileFolder/<regex("[1-9]([0-9]+)?"):page>/<regex("[1-9]([0-9]+)?"):limit>')
@login_required
def film_invalid_file_folder(page=1, limit=10):
    page = int(page)
    limit = int(limit)
    links=5
    # todo more sanitizeation of user input
    # https://code.tutsplus.com/tutorials/how-to-paginate-data-with-php--net-2928
    total_invalid_filefolders = current_app.config["AdminHTTPGenFuncs"].get_total_invalid_filefolders(1)
    # deal with div 0
    offset, last_page = current_app.config["AdminHTTPGenFuncs"].process_pagiation(
        page, limit, total_invalid_filefolders
    )

    invalid_filefolder_list = current_app.config["AdminHTTPGenFuncs"].get_invalid_filefolders(1, limit=limit,
                                                                                              offset=offset)
    log.debug('total_invalid_filefolders %s, page %s, offset %s, limit %s', total_invalid_filefolders,
              page, offset, limit)
    # invalid_filefolder_keys = ['path', 'reason', 'last_ocurrance', 'source', 'scan_path_json', 'added', 'path_extra']
    invalid_filefolder_keys = ['path', 'reason', 'last_ocurrance']
    log.debug(invalid_filefolder_list)
    return render_template('film/invalid.html', invalid_filefolder_list=invalid_filefolder_list,
                           invalid_filefolder_keys=invalid_filefolder_keys,
                           last_page=last_page, links=links,
                           limit=limit, page=page, base_link='/film/invalidFileFolder')


@film.route('/film/<regex("[0-9]+"):zp_filefolder_id>/identify', methods=['GET', 'POST'])
@login_required
def film_identify(zp_filefolder_id):
    # todo add unidentified to bottom for easier 'goto next' unidentified
    error_message = ''
    if request.method == 'POST':
        # log.warning(request.form['film_genre_list'])
        # pass
        log.debug(request.form.keys())
        data = request.form
        #verify_tmdbid = False
        log.debug('data %s', data)
        if 'eapi_id' in data and 'eapi_eid' in data:
            eapi_eid = data['eapi_eid']
            eapi_id = data['eapi_id']
            if eapi_id.isdigit() and eapi_eid:
                current_app.config["AdminHTTPFilmFuncs"].set_filefolder_eapieid(eapi_id, eapi_eid, zp_filefolder_id)
                current_app.config["AdminHTTPGenFuncs"].set_process_force_run(2)
            else:
                error_message = 'eapi_id %s is not a digit or eapi_eid %s is empty' % (eapi_id, eapi_eid)
                log.warning(error_message)
        else:
            error_message = 'eapi_id and or eapi_eid is/are not in %s' % data.keys()
            log.warning(error_message)
    # todo more sanitizeation of user input
    identified = None
    exists = None
    check_unidentified = {'title': ''}
    if zp_filefolder_id.isdigit():
        check_zp_filefolder_id_exists = current_app.config["AdminHTTPFilmFuncs"].check_zp_filefolder_id_exists(
            zp_filefolder_id)
        if check_zp_filefolder_id_exists is True:
            identified = True
            exists = True
            check_unidentified = current_app.config["AdminHTTPFilmFuncs"].check_unidentified(zp_filefolder_id)
            if check_unidentified['unidentified'] is True:
                identified = False
        else:
            exists = False
    if identified != True and exists == True:
        eapi_list = current_app.config["AdminHTTPGenFuncs"].get_eapi_list(1)
        log.debug('eapi_list %s', eapi_list)
        film_path = current_app.config["AdminHTTPFilmFuncs"].film_path(zp_filefolder_id)

        return render_template('film/identify.html', exists=exists, identified=identified,
                           title=check_unidentified['title'], id=zp_filefolder_id, error_message=escape(error_message),
                           eapi_list=eapi_list, film_path=film_path)
    else:
        # if adding the eapi_eid was sucessfull redirect to unIdentified page
        return redirect('/film/unIdentified')

@film.route('/film/<regex("[0-9]+"):zp_film_id>/reIdentify', methods=['GET', 'POST'])
@login_required
def film_re_identify(zp_film_id):
    # todo add unidentified to bottom for easier 'goto next' unidentified
    error_message = ''
    if request.method == 'POST':
        # log.warning(request.form['film_genre_list'])
        # pass
        log.debug(request.form.keys())
        data = request.form
        #verify_tmdbid = False
        log.debug('data %s', data)
        if 'eapi_id' in data and 'eapi_eid' in data:
            eapi_eid = data['eapi_eid']
            eapi_id = data['eapi_id']
            if eapi_id.isdigit() and eapi_eid:
                #current_app.config["AdminHTTPFilmFuncs"].set_filefolder_eapieid(eapi_id, eapi_eid, zp_filefolder_id)
                current_app.config["AdminHTTPFilmFuncs"].reset_film_filefolder(eapi_id, eapi_eid, zp_film_id)
                current_app.config["AdminHTTPGenFuncs"].set_process_force_run(2)
            else:
                error_message = 'eapi_id %s is not a digit or eapi_eid %s is empty' % (eapi_id, eapi_eid)
                log.warning(error_message)
        else:
            error_message = 'eapi_id and or eapi_eid is/are not in %s' % data.keys()
            log.warning(error_message)
    # todo more sanitizeation of user input
    identified = None
    exists = None
    check_unidentified = {'title': ''}
    if zp_film_id.isdigit():
        check_zp_film_id_exists = current_app.config["AdminHTTPFilmFuncs"].check_zp_film_id_exists(
            zp_film_id)
        if check_zp_film_id_exists is True:
            zp_film_filefolder_id = current_app.config["AdminHTTPFilmFuncs"].get_filfolder_from_film(
            zp_film_id)
            if zp_film_filefolder_id > 0:
                eapi_list = current_app.config["AdminHTTPGenFuncs"].get_eapi_list(1)
                log.debug('eapi_list %s', eapi_list)
                film_path = current_app.config["AdminHTTPFilmFuncs"].film_path(zp_film_filefolder_id)
                return render_template('film/re_identify.html',
                                        id=zp_film_filefolder_id,
                                        error_message=escape(error_message),
                                        eapi_list=eapi_list, film_path=film_path)
        # if adding the eapi_eid was sucessfull redirect to unIdentified page
    return redirect('/film')

@film.route('/film/searchActors')
@login_required
def film_searchActors():
    # todo more sanitizeation of user input
    search = request.args.get('name')
    if search is None:
        return Response('{"success":false,"error":"name canot be empty}', mimetype='text/plain')
    else:
        search = re.sub(r'''[^\w\-_\s]''', '', search, flags=re.I | re.U)
        actors = current_app.config["AdminHTTPFilmFuncs"].get_actors(search)
        if actors:
            warning = json.dumps('')
        else:
            warning = json.dumps(escape('No results from search with %s' % search))
    return Response('{"success":true,"error":null,"actors": %s,"warning": %s}' % (json.dumps(actors),
                                                                                 warning),
                    mimetype='text/plain')


@film.route('/film/searchFilms')
@login_required
def film_searchFilms():
    # todo more sanitizeation of user input
    search = request.args.get('search_text')
    if search is None:
        return Response('{"success":false,"error":"name canot be empty}', mimetype='text/plain')
    else:
        search = re.sub(r'''[^\w\-_\s]''', '', search, flags=re.I | re.U)
        films = current_app.config["AdminHTTPFilmFuncs"].film_list(search=search)
        if films:
            warning = json.dumps('')
        else:
            warning = json.dumps(escape('No results from search with %s' % search))
    return Response('{"success":true,"error":null,"films": %s,"warning": %s}' % (json.dumps(films),
                                                                                 warning),
                    mimetype='text/plain')
