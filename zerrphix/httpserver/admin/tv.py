import imghdr
import json
# from PIL import Image
import logging
import mimetypes
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

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

tv = Blueprint('tv', __name__)

log = logging.getLogger(__name__)


@tv.route('/tv')
#@tv.route('/tv/<regex("[1-9]([0-9]+)?"):page>/<regex("[1-9]([0-9]+)?"):limit>')
@login_required
def tv_index(page=1, limit=50):
    log.debug('tv index request args %s', request.args)
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
    log.debug('tv index limit %s, page %s', limit, page)
    links = 5
    total_shows = current_app.config["AdminHTTPTVFuncs"].get_total_num_shows()
    offset, last_page = current_app.config["AdminHTTPGenFuncs"].process_pagiation(
        page, limit, total_shows
    )
    tv_list = current_app.config["AdminHTTPTVFuncs"].tv_list(limit=limit, offset=offset, sort_type=sort_type)
    return render_template('tv/index.html',
                           tvs=tv_list,
                           last_page=last_page, links=links,
                           sort_type=sort_type,
                           limit=limit, page=page, base_link='/tv')


@tv.route('/tv/searchTVShows')
@login_required
def tv_searchTVShows():
    # todo more sanitizeation of user input
    search = request.args.get('search_text')
    if search is None:
        return Response('{"success":false,"error":"name canot be empty}', mimetype='text/plain')
    else:
        search = re.sub(r'''[^\w\-_\s]''', '', search, flags=re.I | re.U)
        tvs = current_app.config["AdminHTTPTVFuncs"].tv_list(search=search)
    return Response('{"success":true,"error":null,"tvs": %s}' % json.dumps(tvs),
                    mimetype='text/plain')


@tv.route('/tv/unIdentified')
@login_required
def tv_unidentified():
    # todo more sanitizeation of user input
    unidentified = current_app.config["AdminHTTPTVFuncs"].get_unidentified_shows()
    return render_template('tv/unidentified.html', unidentified=unidentified)


@tv.route('/tv/<regex("[0-9]+"):zp_filefolder_id>/identify', methods=['GET', 'POST'])
@login_required
def tv_identify(zp_filefolder_id):
    # todo add unidentified to bottom for easier 'goto next' unidentified
    error_message = ''
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
        # pass
        log.debug(request.form.keys())
        data = request.form
        # verify_tmdbid = False
        log.debug('data %s', data)
        if 'eapi_id' in data and 'eapi_eid' in data:
            eapi_eid = data['eapi_eid']
            eapi_id = data['eapi_id']
            if eapi_id.isdigit() and eapi_eid:
                current_app.config["AdminHTTPTVFuncs"].set_filefolder_eapieid(eapi_id, eapi_eid, zp_filefolder_id)
                current_app.config["AdminHTTPGenFuncs"].set_process_force_run(11)
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
        check_zp_filefolder_id_exists = current_app.config["AdminHTTPTVFuncs"].check_zp_filefolder_id_exists(
            zp_filefolder_id)
        log.debug('check_zp_filefolder_id_exists %s', check_zp_filefolder_id_exists)
        if check_zp_filefolder_id_exists is True:
            identified = True
            exists = True
            check_unidentified = current_app.config["AdminHTTPTVFuncs"].check_unidentified(zp_filefolder_id)
            log.debug('check_unidentified %s', check_unidentified)
            if check_unidentified['unidentified'] is True:
                identified = False
        else:
            exists = False
    else:
        log.warning('zp_filefolder_id %s is not a digit', zp_filefolder_id)
    if identified != True and exists == True:
        eapi_list = current_app.config["AdminHTTPGenFuncs"].get_eapi_list(2)
        tv_path = current_app.config["AdminHTTPTVFuncs"].tv_path(zp_filefolder_id)
        log.debug('eapi_list %s', eapi_list)

        return render_template('tv/identify.html', exists=exists, identified=identified,
                               title=check_unidentified['title'], id=zp_filefolder_id,
                               error_message=escape(error_message),
                               eapi_list=eapi_list, tv_path=tv_path)
    else:
        # if adding the eapi_eid was sucessfull redirect to unIdentified page
        #log.error('adasd')
        return redirect('/tv/unIdentified')

@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/reIdentify', methods=['GET', 'POST'])
@login_required
def tv_re_identify(zp_tv_id):
    # todo add unidentified to bottom for easier 'goto next' unidentified
    error_message = ''
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
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
                current_app.config["AdminHTTPTVFuncs"].reset_tv_filefolder(eapi_id, eapi_eid, zp_tv_id)
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
    if zp_tv_id.isdigit():
        check_zp_tv_id_exists = current_app.config["AdminHTTPTVFuncs"].check_zp_tv_id_exists(
            zp_tv_id)
        if check_zp_tv_id_exists is True:
            zp_tv_filefolder_id = current_app.config["AdminHTTPTVFuncs"].get_tv_filefolder_id(
                    zp_tv_id)
            if zp_tv_filefolder_id > 0:
                eapi_list = current_app.config["AdminHTTPGenFuncs"].get_eapi_list(1)
                log.debug('eapi_list %s', eapi_list)

                tv_path = current_app.config["AdminHTTPTVFuncs"].tv_path(zp_tv_filefolder_id)
                return render_template('tv/re_identify.html',
                                        id=zp_tv_filefolder_id,
                                        error_message=escape(error_message),
                                        eapi_list=eapi_list, tv_path=tv_path)
        # if adding the eapi_eid was sucessfull redirect to unIdentified page
    return redirect('/tv')


@tv.route('/tv/monitored', methods=['GET', 'POST'])
@login_required
def tv_monitored():
    if request.method == 'POST':
        post_data = request.form
        log.debug(post_data)
        if 'tv_running_list' in post_data:
            tv_running_post_list = []
            try:
                tv_running_json = json.loads(request.form['tv_running_list'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
            except ValueError as e:
                log.warning('ValueError %s', e)
            else:
                current_app.config["AdminHTTPTVFuncs"].clear_tv_monitored()
                for tv_id in tv_running_json:
                    log.debug(tv_id)
                    if tv_id.isdigit():
                        current_app.config["AdminHTTPTVFuncs"].add_tv_monitored(tv_id)

    # todo more sanitizeation of user input
    tv_running_list = current_app.config["AdminHTTPTVFuncs"].tv_monitored()
    return render_template('tv/running.html',
                           tv_running_list=tv_running_list)


@tv.route('/tv/invalidFileFolder')
@tv.route('/tv/invalidFileFolder/<regex("[1-9]([0-9]+)?"):page>/<regex("[1-9]([0-9]+)?"):limit>')
@login_required
def tv_invalid_file_folder(page=1, limit=5):
    page = int(page)
    limit = int(limit)
    links = 5
    # todo more sanitizeation of user input
    # https://code.tutsplus.com/tutorials/how-to-paginate-data-with-php--net-2928
    total_invalid_filefolders = current_app.config["AdminHTTPGenFuncs"].get_total_invalid_filefolders(2)
    # deal with div 0
    offset, last_page = current_app.config["AdminHTTPGenFuncs"].process_pagiation(
        page, limit, total_invalid_filefolders
    )
    log.debug('total_invalid_filefolders %s, page %s, offset %s, limit %s', total_invalid_filefolders,
              page, offset, limit)
    invalid_filefolder_list = current_app.config["AdminHTTPGenFuncs"].get_invalid_filefolders(2, limit=limit,
                                                                                              offset=offset)
    # invalid_filefolder_keys = ['path', 'reason', 'last_ocurrance', 'source', 'scan_path_json', 'added', 'path_extra']
    invalid_filefolder_keys = ['path', 'reason', 'last_ocurrance']
    return render_template('tv/invalid.html', invalid_filefolder_list=invalid_filefolder_list,
                           invalid_filefolder_keys=invalid_filefolder_keys,
                           last_page=last_page, links=links,
                           limit=limit, page=page, base_link='/tv/invalidFileFolder')


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/summary', methods=['GET', 'POST'])
@login_required
def tv_summary(zp_tv_id):
    genre_dict = current_app.config["AdminHTTPGenFuncs"].genre_by_id()
    log.debug('genre_dict %s', genre_dict)
    tv_genres = current_app.config["AdminHTTPTVFuncs"].tv_genres(zp_tv_id)
    log.debug('tv_genres %s', tv_genres)
    tv_genre_name_list = ''
    for tv_genre in tv_genres:
        tv_genre_name_list += "%s, " % genre_dict[tv_genre]
    tv_genre_name_list = tv_genre_name_list.rstrip(', ')
    log.debug('tv_genre_name_list %s', tv_genre_name_list)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    log.debug('tv_title %s', tv_title)
    tv_overview = current_app.config["AdminHTTPTVFuncs"].tv_overview(zp_tv_id, int(current_user.id))
    log.debug('tv_overview %s', tv_overview)
    tv_rating = current_app.config["AdminHTTPTVFuncs"].tv_rating(zp_tv_id)
    log.debug('tv_rating %s', tv_rating)
    tv_cast = current_app.config["AdminHTTPTVFuncs"].tv_cast(zp_tv_id)
    log.debug('tv_cast %s', tv_cast)
    tv_path = current_app.config["AdminHTTPTVFuncs"].tv_path_list(current_app.config[
                                                "AdminHTTPTVFuncs"].get_tv_filefolder_id_list(zp_tv_id))
    log.debug('tv_path %s', tv_path)
    tv_cast_name_list = ''
    for person in tv_cast:
        tv_cast_name_list += "%s, " % person['name']
    tv_cast_name_list = tv_cast_name_list.rstrip(', ')
    log.debug('tv_cast_name_list %s', tv_cast_name_list)
    tv_poster_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_raw_image_id(zp_tv_id, 3,
                                                                                             int(current_user.id))
    log.debug('tv_poster_raw_image_id %s', tv_poster_raw_image_id)
    tv_backdrop_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_raw_image_id(zp_tv_id, 4,
                                                                                               int(
                                                                                                   current_user.id))
    log.debug('tv_poster_raw_image_id %s', tv_poster_raw_image_id)
    tv_banner_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_raw_image_id(zp_tv_id, 5,
                                                                                             int(
                                                                                                 current_user.id))
    log.debug('tv_backdrop_raw_image_id %s', tv_backdrop_raw_image_id)
    tv_rendered_icon_id = 1
    log.debug('tv_rendered_icon %s', tv_rendered_icon_id)
    tv_rendered_synopsis_id = 1
    log.debug('tv_rendered_synopsis %s', tv_rendered_synopsis_id)
    render_templates_display_dict = \
        current_app.config["AdminHTTPGenFuncs"].get_library_render_templates_display_dict(
            current_user.id, 'tv', ['icon', 'synopsis', 'poster', 'backdrop']
        )
    log.debug('render_templates_display_dict %s', pprint.pformat(render_templates_display_dict))
    for image_type_id in render_templates_display_dict:
        for icon_sub_type_id in render_templates_display_dict[image_type_id]['icon_sub_type_list']:
            render_templates_display_dict[image_type_id]['icon_sub_type_list'][icon_sub_type_id]['render_hash_id'] = \
                current_app.config["AdminHTTPTVFuncs"].tv_rendered_image(zp_tv_id, image_type_id,
                                                                             icon_sub_type_id,
                                                                             int(current_user.id))
    return render_template('tv/summary.html', tv_title=tv_title, zp_tv_id=zp_tv_id,
                           tv_genre_name_list=tv_genre_name_list, tv_overview=tv_overview,
                           tv_rating=tv_rating, tv_cast_name_list=tv_cast_name_list,
                           tv_poster_raw_image_id=tv_poster_raw_image_id,
                           tv_backdrop_raw_image_id=tv_backdrop_raw_image_id,
                           tv_banner_raw_image_id=tv_banner_raw_image_id,
                           tv_rendered_icon_id=tv_rendered_icon_id,
                           tv_rendered_synopsis_id=tv_rendered_synopsis_id,
                           tv_path=tv_path,
                           render_templates_display_dict=render_templates_display_dict)


@tv.route('/i/raw/tv/<regex("[0-9]+"):zp_tv_raw_image_id>')
# @login_required
def get_tv_raw_image(zp_tv_raw_image_id):
    image_filename, zp_tv_id = current_app.config["AdminHTTPTVFuncs"].get_tv_raw_image_filename(
        zp_tv_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'tv', str(zp_tv_id), image_filename)
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
        log.warning('zp_tv_raw_image_id %s does not exist in ZP_TV_RAW_IMAGE', zp_tv_raw_image_id)
        return abort(404)


@tv.route('/i/raw/tv/season/<regex("[0-9]+"):zp_tv_raw_image_id>')
# @login_required
def get_tv_season_raw_image(zp_tv_raw_image_id):
    image_filename, zp_tv_id, season = current_app.config["AdminHTTPTVFuncs"].get_tv_season_raw_image_filename(
        zp_tv_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'tv', str(zp_tv_id), str(season), image_filename)
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
        log.warning('zp_tv_raw_image_id %s does not exist in ZP_TV_RAW_IMAGE', zp_tv_raw_image_id)
        return abort(404)


@tv.route('/i/raw/tv/episode/<regex("[0-9]+"):zp_tv_raw_image_id>')
# @login_required
def get_tv_episode_raw_image(zp_tv_raw_image_id):
    image_filename, zp_tv_id, season = current_app.config["AdminHTTPTVFuncs"].get_tv_episode_raw_image_filename(
        zp_tv_raw_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict[
                                      'downloaded_images_root_path'],
                                  'tv', str(zp_tv_id), str(season), image_filename)
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
        log.warning('zp_tv_raw_image_id %s does not exist in ZP_TV_RAW_IMAGE', zp_tv_raw_image_id)
        return abort(404)


@tv.route('/i/rendered/tv/<regex("[0-9]+"):zp_tv_rendered_image_id>')
# @login_required
def get_tv_rendered_image(zp_tv_rendered_image_id):
    image_filename, template_name, zp_tv_id = current_app.config[
        "AdminHTTPTVFuncs"].get_tv_rendered_image_filename(zp_tv_rendered_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict[
                                      'rendered_image_root_path'],
                                  'tv', template_name, str(zp_tv_id), image_filename)
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
        log.error('zp_tv_rendered_image_id %s does not exist in ZP_TV_RENDER_HASH', zp_tv_rendered_image_id)
        return abort(404)

@tv.route('/i/rendered/tv/episode/<regex("[0-9]+"):zp_tv_rendered_image_id>')
# @login_required
def get_tv_episode_rendered_image(zp_tv_rendered_image_id):
    image_filename, template_name, zp_tv_id = current_app.config[
        "AdminHTTPTVFuncs"].get_tv_episode_rendered_image_filename(zp_tv_rendered_image_id)
    if image_filename:
        image_path = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict[
                                      'rendered_image_root_path'],
                                  'tv', template_name, str(zp_tv_id), image_filename)
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
        log.error('zp_tv_rendered_image_id %s does not exist in ZP_TV_RENDER_HASH', zp_tv_rendered_image_id)
        return abort(404)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/overview', methods=['GET', 'POST'])
@login_required
def tv_overview(zp_tv_id):
    if request.method == 'POST':
        if 'zp_overview_ident' in request.form and 'zp_overview_overview' in request.form:
            zp_overview_ident = request.form['zp_overview_ident']
            overview = request.form['zp_overview_overview']
            log.debug('zp_overview_ident %s', zp_overview_ident)
            log.debug('zp_overview_overview %s', overview)
            current_app.config["AdminHTTPTVFuncs"].update_tv_overview(zp_tv_id,
                                                                      int(current_user.id), zp_overview_ident,
                                                                      overview)
    # todo get this from function
    lang_name_dict = current_app.config["AdminHTTPGenFuncs"].get_lang_name_dict(1)
    eapi_name_dict = current_app.config["AdminHTTPGenFuncs"].get_eapi_dict(1)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    tv_overview_list = current_app.config["AdminHTTPTVFuncs"].tv_overview_list(zp_tv_id, int(current_user.id))
    log.debug('tv_overview_list %s', tv_overview_list)
    user_tv_overview_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_overview_id(zp_tv_id,
                                                                                         int(current_user.id))
    log.debug('user_tv_overview_id %s', user_tv_overview_id)
    return render_template('tv/overview.html', tv_title=tv_title, tv_overview_list=tv_overview_list,
                           zp_tv_id=zp_tv_id, user_tv_overview_id=user_tv_overview_id,
                           lang_name_dict=lang_name_dict, eapi_name_dict=eapi_name_dict)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/title', methods=['GET', 'POST'])
@login_required
def tv_title(zp_tv_id):
    if request.method == 'POST':
        if 'zp_title_ident' in request.form and 'zp_title_title' in request.form:
            zp_title_ident = request.form['zp_title_ident']
            title = request.form['zp_title_title']
            log.debug('zp_title_ident %s', zp_title_ident)
            log.debug('zp_title_title %s', title)
            current_app.config["AdminHTTPTVFuncs"].update_tv_title(zp_tv_id,
                                                                   int(current_user.id), zp_title_ident,
                                                                   title)
    # todo get this from function
    lang_name_dict = current_app.config["AdminHTTPGenFuncs"].get_lang_name_dict(1)
    eapi_name_dict = current_app.config["AdminHTTPGenFuncs"].get_eapi_dict(1)
    tile_type_name_dict = {1: 'Normal', 2: 'Origional Title'}
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    tv_title_list = current_app.config["AdminHTTPTVFuncs"].tv_title_list(zp_tv_id, int(current_user.id))
    user_tv_title_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_title_id(zp_tv_id,
                                                                                   int(current_user.id))
    return render_template('tv/title.html', tv_title=tv_title, tv_title_list=tv_title_list,
                           zp_tv_id=zp_tv_id, user_tv_title_id=user_tv_title_id, lang_name_dict=lang_name_dict,
                           eapi_name_dict=eapi_name_dict, tile_type_name_dict=tile_type_name_dict)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/rating', methods=['GET', 'POST'])
@login_required
def tv_rating(zp_tv_id):
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
        # pass
        log.warning(request.form.keys())
        if 'rating' in request.form:
            log.warning(request.form['rating'])
            rating = request.form['rating']
            if rating.isdigit():
                rating = int(rating)
                if rating >= 1 and rating <= 10:
                    current_app.config["AdminHTTPTVFuncs"].update_rating(zp_tv_id, rating)
    # todo add role order
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    rating = current_app.config["AdminHTTPTVFuncs"].tv_rating(zp_tv_id)
    tv_ratings = []
    for i in range(1, 11):
        if i == rating:
            tv_ratings.append({'rating': i, 'selected': True})
        else:
            tv_ratings.append({'rating': i, 'selected': False})
    # log.warning(tv_title_id, tv_title_text)
    return render_template('tv/rating.html', tv_title=tv_title, tv_ratings=tv_ratings,
                           zp_tv_id=zp_tv_id)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/genre', methods=['GET', 'POST'])
@login_required
def tv_genre(zp_tv_id):
    # todo change to using genre by id
    genre_dict = current_app.config["AdminHTTPGenFuncs"].genre_by_name()
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
        # pass
        # log.warning(dir(request.form))
        tv_genre_post_list = []
        if 'tv_genre_list' in request.form:
            log.debug(request.form['tv_genre_list'])
            try:
                tv_genre_json = json.loads(request.form['tv_genre_list'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
            except ValueError as e:
                log.warning('ValueError %s', e)
            else:
                for tv_genre_id in tv_genre_json:
                    log.debug(tv_genre_id)
                    if tv_genre_id.isdigit():
                        tv_genre_post_list.append(int(tv_genre_id))
        tv_genre_to_set_list = []
        if len(tv_genre_post_list) > 0:
            for genre in genre_dict:
                if genre_dict[genre] in tv_genre_post_list:
                    tv_genre_to_set_list.append(genre_dict[genre])
        if len(tv_genre_to_set_list) > 0:
            current_app.config["AdminHTTPTVFuncs"].clear_genres(zp_tv_id)
            for genre in tv_genre_to_set_list:
                current_app.config["AdminHTTPTVFuncs"].add_genre(zp_tv_id, genre)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    tv_genre_list = current_app.config["AdminHTTPTVFuncs"].tv_genres(zp_tv_id)
    log.debug(genre_dict)
    log.debug(tv_genre_list)
    genre_option_list = []
    tv_genre_option_list = []
    for genre in sorted(genre_dict):
        if genre_dict[genre] in tv_genre_list:
            tv_genre_option_list.append({'name': genre, 'id': genre_dict[genre]})
        else:
            genre_option_list.append({'name': genre, 'id': genre_dict[genre]})
    log.debug(tv_genre_option_list)
    log.debug(genre_option_list)
    return render_template('tv/genre.html', tv_title=tv_title,
                           genres=genre_option_list, tv_genres=tv_genre_option_list, zp_tv_id=zp_tv_id)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/cast', methods=['GET', 'POST'])
@login_required
def tv_cast(zp_tv_id):
    if request.method == 'POST':
        # log.warning(request.form['tv_genre_list'])
        # pass
        # log.warning(dir(request.form))
        tv_cast_post_list = []
        if 'tv_actor_json' in request.form:
            log.debug(request.form['tv_actor_json'])
            try:
                post_json = json.loads(request.form['tv_actor_json'])
            except AttributeError as e:
                log.warning('AttributeError %s', e)
            except ValueError as e:
                log.warning('ValueError %s', e)
            else:
                for people_id in post_json:
                    log.debug(people_id)
                    if people_id.isdigit():
                        tv_cast_post_list.append(int(people_id))
        log.debug('tv_cast_post_list %s', tv_cast_post_list)
        if len(tv_cast_post_list) > 0:
            current_app.config["AdminHTTPTVFuncs"].clear_cast(zp_tv_id)
            for people_id in tv_cast_post_list:
                current_app.config["AdminHTTPTVFuncs"].add_cast(zp_tv_id, people_id)
    # todo add role order
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    tv_cast_list = current_app.config["AdminHTTPTVFuncs"].tv_cast(zp_tv_id)
    return render_template('tv/cast.html', tv_title=tv_title, tv_cast=tv_cast_list,
                           zp_tv_id=zp_tv_id)


@tv.route('/tv/searchActors')
@login_required
def tv_searchActors():
    # todo more sanitizeation of user input
    name = request.args.get('name')
    if name is None:
        return Response('{"success":false,"error":"name canot be empty}', mimetype='text/plain')
    else:
        name = re.sub(r'''[^\w\-_\s]''', '', name, flags=re.I | re.U)
        actors = current_app.config["AdminHTTPTVFuncs"].get_actors(name)
    return Response('{"success":true,"error":null,"actors": %s}' % json.dumps(actors),
                    mimetype='text/plain')


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("poster|backdrop|banner"):image_type>/set/'
          '<regex("[0-9]+"):zp_tv_raw_image_id>')
@login_required
def tv_image_update(zp_tv_id, image_type, zp_tv_raw_image_id):
    if current_app.config["AdminHTTPTVFuncs"].set_user_tv_raw_image(zp_tv_id, image_type,
                                                                    zp_tv_raw_image_id, current_user.id) is True:
        current_app.config["AdminHTTPGenFuncs"].set_process_force_run(17)
        return Response('{"success": true, "error": "null"}', mimetype='text/plain')
    else:
        return Response('{"success": false, "error": "unkown"}', mimetype='text/plain')


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("poster|backdrop|banner"):image_type>', methods=['GET', 'POST'])
@login_required
# if request.method == 'POST':
def tv_image(zp_tv_id, image_type):
    log.debug(image_type)
    filename_regex = r'''^[\w\-\_\.\(\)\s]+\.(?:jpg|jpeg|png|bmp|gif)$'''
    # TODO: error message when filesize is too big
    raw_image_group_max_count_dict = {'poster': 4, 'backdrop': 2, 'banner': 2}
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
                        new_tv_image_folder = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict
                                                           ['downloaded_images_root_path'], 'tv',
                                                           zp_tv_id)
                        log.debug('making foldernew_tv_image_folder %s if does not exist.', new_tv_image_folder)
                        if make_dir(new_tv_image_folder):
                            log.debug('new_tv_image_folder %s exists', new_tv_image_folder)
                            new_tv_poster_image_folder = os.path.join(
                                current_app.config["AdminHTTPTVFuncs"].global_config_dict
                                ['downloaded_images_root_path'], 'tv',
                                zp_tv_id)
                            new_image_uuid = uuid.uuid4()
                            new_tv_image_filename = '%s.%s' % (new_image_uuid, get_file_extension(file.filename))
                            new_tv_image_path = os.path.join(new_tv_poster_image_folder, new_tv_image_filename)
                            log.debug(new_tv_image_path)
                            file.save(new_tv_image_path)
                            current_app.config["AdminHTTPTVFuncs"].add_new_tv_raw_image(zp_tv_id,
                                                                                        str(current_user.id),
                                                                                        current_app.config[
                                                                                            "AdminHTTPTVFuncs"].image_type_id_dict[
                                                                                            image_type],
                                                                                        new_tv_image_filename,
                                                                                        file.filename)
                        else:
                            log.error('failed to make dir %s', new_tv_image_folder)
                            raise_alter_message = escape('failed to make dir %s' % new_tv_image_folder)
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
    render_type_dict = {'poster': 'quarter', 'backdrop': 'half', 'banner': 'half'}

    raw_images_list = current_app.config["AdminHTTPTVFuncs"].tv_raw_image_list(zp_tv_id,
                                                                               current_app.config[
                                                                                   "AdminHTTPTVFuncs"].image_type_id_dict[
                                                                                   image_type])
    user_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_raw_image_id(zp_tv_id,
                                                                                        current_app.config[
                                                                                            "AdminHTTPTVFuncs"].image_tv_entity_type_id_dict[
                                                                                            image_type],
                                                                                        int(current_user.id))
    log.debug('user_raw_image_id %s', user_raw_image_id)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
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
    return render_template('tv/image.html',
                           raw_image_group_list=raw_image_group_list, tv_title=tv_title,
                           render_type=render_type_dict[image_type],
                           raise_user_alert=raise_user_alert, raise_alter_message=raise_alter_message,
                           image_type=image_type, zp_tv_id=zp_tv_id, user_raw_image_id=user_raw_image_id)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[a-zA-Z0-9_]+"):image_type>/<regex("[0-9]+"):zp_icon_sub_type_id>/render')
@login_required
# if request.method == 'POST':
def tv_render_image(zp_tv_id, image_type, zp_icon_sub_type_id):
    return_image = current_app.config["AdminHTTPTVArtwork"].render(zp_tv_id, current_user.id, image_type, zp_icon_sub_type_id)
    cimage = StringIO()
    return_image.save(cimage, 'png')
    return_image.close()
    cimage.seek(0)
    # mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
    mimetype = '.png'
    # except:
    # mimetype = 'image'
    return send_file(cimage, mimetype)

@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):season>/<regex("[0-9]+"):episode>/<regex("[a-zA-Z0-9_]+"):image_type>/<regex("[0-9]+"):zp_icon_sub_type_id>/render')
@login_required
# if request.method == 'POST':
def tv_episode_render_image(zp_tv_id, season, episode, image_type, zp_icon_sub_type_id):
    return_image = current_app.config["AdminHTTPTVEpisodeArtwork"].render(zp_tv_id, current_user.id,
                                                                   season, episode,
                                                                   image_type, zp_icon_sub_type_id)
    cimage = StringIO()
    return_image.save(cimage, 'png')
    return_image.close()
    cimage.seek(0)
    # mimetype = mimetypes.types_map['.{0}'.format(imghdr.what(image_path))]
    mimetype = '.png'
    # except:
    # mimetype = 'image'
    return send_file(cimage, mimetype)

@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/season', methods=['GET', 'POST'])
@login_required
def tv_season_main(zp_tv_id):
    # todo get this from function
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id)
    return render_template('tv/season_index.html', tv_title=tv_title,
                           season_list=season_list,
                           zp_tv_id=zp_tv_id)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):selected_season>/summary', methods=['GET', 'POST'])
@login_required
def tv_season_summary(zp_tv_id, selected_season):
    # todo get this from function
    selected_season = int(selected_season)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    sidebar_season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id, selected_season)
    log.debug('sidebar_season_list %s', sidebar_season_list)
    tv_season_poster_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_season_raw_image_id(zp_tv_id,
                                                                                                           selected_season,
                                                                                                           1,
                                                                                                           int(
                                                                                                               current_user.id))
    log.debug('tv_season_poster_raw_image_id %s', tv_season_poster_raw_image_id)
    episode_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_list(zp_tv_id, selected_season)
    return render_template('tv/season_summary.html', tv_title=tv_title,
                           episode_list=episode_list,
                           season_list=sidebar_season_list,
                           selected_season=selected_season,
                           tv_season_poster_raw_image_id=tv_season_poster_raw_image_id,
                           zp_tv_id=zp_tv_id)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):selected_season>/<regex("[0-9]+"):selected_episode>/summary',
          methods=['GET', 'POST'])
@login_required
def tv_episode_summary(zp_tv_id, selected_season, selected_episode):
    # todo get this from function
    selected_season = int(selected_season)
    selected_episode = int(selected_episode)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    episode_title = current_app.config["AdminHTTPTVFuncs"].tv_episode_title(zp_tv_id, selected_season,
                                                                            selected_episode, int(current_user.id))
    log.debug('tv_title %s', tv_title)
    episode_overview = current_app.config["AdminHTTPTVFuncs"].tv_episode_overview(zp_tv_id, selected_season,
                                                                                  selected_episode,
                                                                                  int(current_user.id))
    log.debug('tv_overview %s', tv_overview)
    sidebar_season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id, selected_season)
    sidebar_episode_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_list(zp_tv_id, selected_season,
                                                                                  selected_episode)
    tv_episode_poster_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_episode_raw_image_id(
        zp_tv_id, selected_season, selected_episode, 3, int(current_user.id))

    render_templates_display_dict = \
        current_app.config["AdminHTTPGenFuncs"].get_library_render_templates_display_dict(
            current_user.id, 'tv', ['episode_icon', 'episode_synopsis', 'episode_screenshot']
        )
    log.debug('render_templates_display_dict %s', pprint.pformat(render_templates_display_dict))
    for image_type_id in render_templates_display_dict:
        for icon_sub_type_id in render_templates_display_dict[image_type_id]['icon_sub_type_list']:
            render_templates_display_dict[image_type_id]['icon_sub_type_list'][icon_sub_type_id]['render_hash_id'] = \
                current_app.config["AdminHTTPTVFuncs"].tv_episode_rendered_image(zp_tv_id,
                    selected_season, selected_episode, image_type_id, icon_sub_type_id, int(current_user.id))
    log.debug('render_templates_display_dict %s', pprint.pformat(render_templates_display_dict))
    return render_template('tv/episode_summary.html', tv_title=tv_title,
                           episode_title=episode_title,
                           episode_overview=episode_overview,
                           episode_list=sidebar_episode_list,
                           season_list=sidebar_season_list,
                           selected_season=selected_season,
                           selected_episode=selected_episode,
                           tv_episode_poster_raw_image_id=tv_episode_poster_raw_image_id,
                           zp_tv_id=zp_tv_id,
                           render_templates_display_dict=render_templates_display_dict)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):selected_season>/<regex("poster"):image_type>',
          methods=['GET', 'POST'])
@login_required
# if request.method == 'POST':
def tv_season_image(zp_tv_id, selected_season, image_type):
    log.debug('image_type %s', image_type)
    filename_regex = r'''^[\w\-\_\.\(\)\s]+\.(?:jpg|jpeg|png|bmp|gif)$'''
    # TODO: error message when filesize is too big
    raw_image_group_max_count_dict = {'poster': 4, 'backdrop': 2, 'banner': 2}
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
                        new_tv_image_folder = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict
                                                           ['downloaded_images_root_path'], 'tv',
                                                           zp_tv_id)
                        log.debug('making foldernew_tv_image_folder %s if does not exist.', new_tv_image_folder)
                        if make_dir(new_tv_image_folder):
                            log.debug('new_tv_image_folder %s exists', new_tv_image_folder)
                            new_tv_season_image_folder = os.path.join(
                                current_app.config["AdminHTTPTVFuncs"].global_config_dict
                                ['downloaded_images_root_path'], 'tv',
                                zp_tv_id, selected_season)
                            if make_dir(new_tv_season_image_folder):
                                log.debug('new_tv_season_image_folder %s exists', new_tv_season_image_folder)
                                new_image_uuid = uuid.uuid4()
                                new_tv_image_filename = '%s.%s' % (new_image_uuid, get_file_extension(file.filename))
                                new_tv_image_path = os.path.join(new_tv_season_image_folder, new_tv_image_filename)
                                log.debug('new_tv_image_path %s', new_tv_image_path)
                                file.save(new_tv_image_path)
                                current_app.config["AdminHTTPTVFuncs"].add_new_tv_season_raw_image(zp_tv_id,
                                                                                                   selected_season,
                                                                                                   str(current_user.id),
                                                                                                   current_app.config[
                                                                                                       "AdminHTTPTVFuncs"].image_season_type_id_dict[
                                                                                                       image_type],
                                                                                                   new_tv_image_filename,
                                                                                                   file.filename)
                            else:
                                log.error('failed to make dir %s', new_tv_season_image_folder)
                                raise_alter_message = escape('failed to make dir %s' % new_tv_season_image_folder)
                        else:
                            log.error('failed to make dir %s', new_tv_image_folder)
                            raise_alter_message = escape('failed to make dir %s' % new_tv_image_folder)
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
    selected_season = int(selected_season)
    sidebar_season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id, selected_season)
    sidebar_episode_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_list(zp_tv_id, selected_season)
    render_type_dict = {'poster': 'quarter', 'backdrop': 'half', 'banner': 'half'}
    raw_images_list = current_app.config["AdminHTTPTVFuncs"].tv_season_raw_image_list(zp_tv_id,
                                                                                      selected_season,
                                                                                      current_app.config[
                                                                                          "AdminHTTPTVFuncs"].image_season_type_id_dict[
                                                                                          image_type])
    log.debug('raw_images_list %s', raw_images_list)
    user_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_season_raw_image_id(
        zp_tv_id,
        selected_season,
        current_app.config["AdminHTTPTVFuncs"].image_tv_season_user_entity_type_id_dict[image_type],
        int(current_user.id))
    log.debug('user_raw_image_id %s', user_raw_image_id)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
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
    return render_template('tv/season_image.html',
                           raw_image_group_list=raw_image_group_list, tv_title=tv_title,
                           render_type=render_type_dict[image_type],
                           episode_list=sidebar_episode_list,
                           season_list=sidebar_season_list,
                           selected_season=selected_season,
                           raise_user_alert=raise_user_alert, raise_alter_message=raise_alter_message,
                           image_type=image_type, zp_tv_id=zp_tv_id, user_raw_image_id=user_raw_image_id,
                           )


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):season>/<regex("[0-9]+"):episode>/'
          '<regex("screenshot"):image_type>/set/'
          '<regex("[0-9]+"):zp_tv_raw_image_id>')
@login_required
def tv_episode_image_update(zp_tv_id, season, episode, image_type, zp_tv_raw_image_id):
    if current_app.config["AdminHTTPTVFuncs"].set_user_tv_episode_raw_image(zp_tv_id, season, episode, image_type,
                                                                            zp_tv_raw_image_id,
                                                                            current_user.id) is True:
        current_app.config["AdminHTTPGenFuncs"].set_process_force_run(17)
        return Response('{"success": true, "error": "null"}', mimetype='text/plain')
    else:
        return Response('{"success": false, "error": "unkown"}', mimetype='text/plain')


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):selected_season>/<regex("[0-9]+"):selected_episode>/'
          '<regex("screenshot"):image_type>', methods=['GET', 'POST'])
@login_required
# if request.method == 'POST':
def tv_episode_image(zp_tv_id, selected_season, selected_episode, image_type):
    log.debug('image_type %s', image_type)
    filename_regex = r'''^[\w\-\_\.\(\)\s]+\.(?:jpg|jpeg|png|bmp|gif)$'''
    # TODO: error message when filesize is too big
    raw_image_group_max_count_dict = {'poster': 4, 'backdrop': 2, 'banner': 2, 'screenshot': 2}
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
                        new_tv_image_folder = os.path.join(current_app.config["AdminHTTPTVFuncs"].global_config_dict
                                                           ['downloaded_images_root_path'], 'tv',
                                                           zp_tv_id)
                        log.debug('making foldernew_tv_image_folder %s if does not exist.', new_tv_image_folder)
                        if make_dir(new_tv_image_folder):
                            log.debug('new_tv_image_folder %s exists', new_tv_image_folder)
                            new_tv_season_image_folder = os.path.join(
                                current_app.config["AdminHTTPTVFuncs"].global_config_dict
                                ['downloaded_images_root_path'], 'tv',
                                zp_tv_id, selected_season)
                            if make_dir(new_tv_season_image_folder):
                                log.debug('new_tv_season_image_folder %s exists', new_tv_season_image_folder)
                                new_image_uuid = uuid.uuid4()
                                new_tv_image_filename = '%s.%s' % (new_image_uuid, get_file_extension(file.filename))
                                new_tv_image_path = os.path.join(new_tv_season_image_folder, new_tv_image_filename)
                                log.debug('new_tv_image_path %s', new_tv_image_path)
                                file.save(new_tv_image_path)
                                current_app.config["AdminHTTPTVFuncs"].add_new_tv_episode_raw_image(zp_tv_id,
                                                                                                    selected_season,
                                                                                                    selected_episode,
                                                                                                    str(
                                                                                                        current_user.id),
                                                                                                    current_app.config[
                                                                                                        "AdminHTTPTVFuncs"].image_episode_type_id_dict[
                                                                                                        image_type],
                                                                                                    new_tv_image_filename,
                                                                                                    file.filename)
                            else:
                                log.error('failed to make dir %s', new_tv_season_image_folder)
                                raise_alter_message = escape('failed to make dir %s' % new_tv_season_image_folder)
                        else:
                            log.error('failed to make dir %s', new_tv_image_folder)
                            raise_alter_message = escape('failed to make dir %s' % new_tv_image_folder)
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
    selected_season = int(selected_season)
    selected_episode = int(selected_episode)
    episode_title = current_app.config["AdminHTTPTVFuncs"].tv_episode_title(zp_tv_id, selected_season,
                                                                            selected_episode, int(current_user.id))
    sidebar_season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id, selected_season)
    sidebar_episode_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_list(zp_tv_id, selected_season,
                                                                                  selected_episode)
    render_type_dict = {'poster': 'quarter', 'backdrop': 'half', 'banner': 'half', 'screenshot': 'half'}
    raw_images_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_raw_image_list(zp_tv_id,
                                                                                       selected_season,
                                                                                       selected_episode,
                                                                                       current_app.config[
                                                                                           "AdminHTTPTVFuncs"].image_episode_type_id_dict[
                                                                                           image_type])
    log.debug('raw_images_list %s', raw_images_list)
    user_raw_image_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_episode_raw_image_id(zp_tv_id,
                                                                                                selected_season,
                                                                                                selected_episode,
                                                                                                current_app.config[
                                                                                                    "AdminHTTPTVFuncs"].image_tv_episode_user_entity_type_id_dict[
                                                                                                    image_type],
                                                                                                int(current_user.id))
    log.debug('user_raw_image_id %s', user_raw_image_id)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
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
    return render_template('tv/episode_image.html',
                           raw_image_group_list=raw_image_group_list, tv_title=tv_title,
                           render_type=render_type_dict[image_type],
                           episode_list=sidebar_episode_list,
                           season_list=sidebar_season_list,
                           selected_season=selected_season,
                           selected_episode=selected_episode,
                           raise_user_alert=raise_user_alert, raise_alter_message=raise_alter_message,
                           image_type=image_type, zp_tv_id=zp_tv_id, user_raw_image_id=user_raw_image_id,
                           episode_title=episode_title
                           )


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):season>/<regex("poster"):image_type>/set/'
          '<regex("[0-9]+"):zp_tv_raw_image_id>')
@login_required
def tv_season_image_update(zp_tv_id, season, image_type, zp_tv_raw_image_id):
    if current_app.config["AdminHTTPTVFuncs"].set_user_tv_season_raw_image(zp_tv_id, season, image_type,
                                                                           zp_tv_raw_image_id, current_user.id) is True:
        current_app.config["AdminHTTPGenFuncs"].set_process_force_run(17)
        return Response('{"success": true, "error": "null"}', mimetype='text/plain')
    else:
        return Response('{"success": false, "error": "unkown"}', mimetype='text/plain')


@tv.route(
    '/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):selected_season>/<regex("[0-9]+"):selected_episode>/overview',
    methods=['GET', 'POST'])
@login_required
def tv_episode_overview(zp_tv_id, selected_season, selected_episode):
    if request.method == 'POST':
        if 'zp_overview_ident' in request.form and 'zp_overview_overview' in request.form:
            zp_overview_ident = request.form['zp_overview_ident']
            overview = request.form['zp_overview_overview']
            log.debug('zp_overview_ident %s', zp_overview_ident)
            log.debug('zp_overview_overview %s', overview)
            current_app.config["AdminHTTPTVFuncs"].update_tv_episode_overview(zp_tv_id,
                                                                              selected_episode,
                                                                              selected_season,
                                                                              int(current_user.id), zp_overview_ident,
                                                                              overview)
        else:
            log.debug('zp_overview_ident and or zp_overview_overview not in request.form %s', request.form)
    # todo get this from function
    lang_name_dict = {1823: 'English'}
    eapi_name_dict = {1: 'TMDB'}
    episode_title = current_app.config["AdminHTTPTVFuncs"].tv_episode_title(zp_tv_id, selected_season,
                                                                            selected_episode, int(current_user.id))
    log.debug('episode_title %s', episode_title)
    selected_season = int(selected_season)
    selected_episode = int(selected_episode)
    sidebar_season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id, selected_season)
    sidebar_episode_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_list(zp_tv_id, selected_season,
                                                                                  selected_episode)
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    log.debug('tv_title %s', tv_title)
    tv_episode_overview_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_overview_list(zp_tv_id,
                                                                                               selected_season,
                                                                                               selected_episode,
                                                                                               int(current_user.id))
    log.debug('tv_episode_overview_list %s', tv_episode_overview_list)
    user_tv_episode_overview_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_episode_overview_id(zp_tv_id,
                                                                                                         selected_season,
                                                                                                         selected_episode,
                                                                                                         int(
                                                                                                             current_user.id))
    log.debug('user_tv_episode_overview_id %s', user_tv_episode_overview_id)
    return render_template('tv/episode_overview.html', tv_title=tv_title,
                           tv_episode_overview_list=tv_episode_overview_list,
                           zp_tv_id=zp_tv_id, user_tv_episode_overview_id=user_tv_episode_overview_id,
                           season_list=sidebar_season_list,
                           episode_list=sidebar_episode_list,
                           selected_season=selected_season,
                           selected_episode=selected_episode,
                           episode_title=episode_title,
                           lang_name_dict=lang_name_dict, eapi_name_dict=eapi_name_dict)


@tv.route('/tv/<regex("[0-9]+"):zp_tv_id>/<regex("[0-9]+"):selected_season>/<regex("[0-9]+"):selected_episode>/title',
          methods=['GET', 'POST'])
@login_required
def tv_episode_title(zp_tv_id, selected_season, selected_episode):
    if request.method == 'POST':
        if 'zp_title_ident' in request.form and 'zp_title_title' in request.form:
            zp_title_ident = request.form['zp_title_ident']
            title = request.form['zp_title_title']
            log.debug('zp_title_ident %s', zp_title_ident)
            log.debug('zp_title_title %s', title)
            current_app.config["AdminHTTPTVFuncs"].update_tv_episode_title(zp_tv_id,
                                                                           selected_episode,
                                                                           selected_season,
                                                                           int(current_user.id), zp_title_ident,
                                                                           title)
        else:
            log.error('zp_title_ident and or zp_title_title not in request.form %s', request.form)
    # todo get this from function
    lang_name_dict = {1823: 'English'}
    eapi_name_dict = {1: 'TMDB'}
    tile_type_name_dict = {1: 'Normal', 2: 'Origional Title'}
    episode_title = current_app.config["AdminHTTPTVFuncs"].tv_episode_title(zp_tv_id, selected_season,
                                                                            selected_episode, int(current_user.id))
    tv_title = current_app.config["AdminHTTPTVFuncs"].tv_title(zp_tv_id, int(current_user.id))
    selected_season = int(selected_season)
    selected_episode = int(selected_episode)
    sidebar_season_list = current_app.config["AdminHTTPTVFuncs"].tv_season_list(zp_tv_id, selected_season)
    sidebar_episode_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_list(zp_tv_id, selected_season,
                                                                                  selected_episode)
    tv_episode_title_list = current_app.config["AdminHTTPTVFuncs"].tv_episode_title_list(zp_tv_id,
                                                                                         selected_season,
                                                                                         selected_episode,
                                                                                         int(current_user.id))
    log.debug('tv_episode_title_list %s', tv_episode_title_list)
    user_tv_episode_title_id = current_app.config["AdminHTTPTVFuncs"].get_user_tv_episode_title_id(zp_tv_id,
                                                                                                   selected_season,
                                                                                                   selected_episode,
                                                                                                   int(current_user.id))
    log.debug('user_tv_episode_title_id %s', user_tv_episode_title_id)
    return render_template('tv/episode_title.html', tv_title=tv_title, tv_episode_title_list=tv_episode_title_list,
                           zp_tv_id=zp_tv_id, user_tv_episode_title_id=user_tv_episode_title_id,
                           season_list=sidebar_season_list,
                           episode_list=sidebar_episode_list,
                           selected_season=selected_season,
                           selected_episode=selected_episode,
                           episode_title=episode_title,
                           lang_name_dict=lang_name_dict,
                           eapi_name_dict=eapi_name_dict, tile_type_name_dict=tile_type_name_dict)
