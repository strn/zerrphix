# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
from sqlalchemy import orm, and_
import logging
import re
from zerrphix.db.tables import TABLES
from zerrphix.db import commit, flush
from flask import Flask
from flask import render_template
from flask import request
from flask import abort
from werkzeug.routing import BaseConverter
from zerrphix.util.plugin import create_eapi_dict
from zerrphix.httpserver.admin.film import film
from zerrphix.httpserver.admin.film_collection import film_collection
from zerrphix.httpserver.admin.tv import tv
from zerrphix.httpserver.admin.process import process
from zerrphix.httpserver.admin.scan_paths import scan_paths
from zerrphix.httpserver.admin.dunes import dunes
from zerrphix.httpserver.admin.settings import settings
from zerrphix.httpserver.admin.api import api
from zerrphix.httpserver.admin.report import report
from zerrphix.httpserver.admin.template import template
from flask import send_file
from zerrphix.httpserver.admin.funcs.admin_http_gen_funcs import AdminHTTPGenFuncs
from zerrphix.httpserver.admin.funcs.admin_http_film_funcs import AdminHTTPFilmFuncs
from zerrphix.httpserver.admin.funcs.admin_http_film_collection_funcs import AdminHTTPFilmCollectionFuncs
from zerrphix.httpserver.admin.funcs.admin_http_tv_funcs import AdminHTTPTVFuncs
from zerrphix.httpserver.admin.funcs.admin_http_process_funcs import AdminHTTPProcessFuncs
from zerrphix.httpserver.admin.funcs.admin_http_dunes_path_funcs import AdminHTTPDuneFuncs
from zerrphix.httpserver.admin.funcs.admin_http_scan_path_funcs import AdminHTTPScanPathFuncs
from zerrphix.httpserver.admin.funcs.admin_http_api_funcs import AdminHTTPApiFuncs
from zerrphix.httpserver.admin.funcs.admin_http_report_funcs import AdminHTTPReportFuncs
from zerrphix.httpserver.admin.funcs.admin_http_template_funcs import AdminHTTPTemplateFuncs
from zerrphix.httpserver.admin.film_artwork import Artwork as FilmArtwork
from zerrphix.httpserver.admin.film_collection_artwork import Artwork as FilmCollectionArtwork
from zerrphix.httpserver.admin.tv_artwork import Artwork as TVArtwork
from zerrphix.httpserver.admin.tv_episode_artwork import Artwork as TVEpisodeArtwork
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask import current_app
from flask import flash
from flask import redirect
from flask import url_for
from copy import deepcopy
from zerrphix.constants import logo_b64
import base64
import math
import bcrypt
import  pkg_resources
from io import BytesIO
import mimetypes
import os
from zerrphix._version import __version__
#https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
#https://stackoverflow.com/questions/10946795/render-multiple-templates-at-once-in-flask
#https://www.w3schools.com/w3css/tryw3css_templates_analytics.htm
#http://fontawesome.io/cheatsheet/
#https://github.com/jpercent/flask-control
#http://code.nabla.net/doc/jinja2/api/jinja2/jinja2.filters.html
log = logging.getLogger(__name__)

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

class AdminHTTPSvr(object):
    def __init__(self, args, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.args = args
        self.init_flask()
        self.eapi_dict = create_eapi_dict(Session)

    def init_flask(self):
        """
        A user requests the following URL:
            http://www.example.com/myapplication/page.html?x=y

        In this case the values of the above mentioned attributes would be the following:

            path             /page.html
            script_root      /myapplication
            base_url         http://www.example.com/myapplication/page.html
            url              http://www.example.com/myapplication/page.html?x=y
            url_root         http://www.example.com/myapplication/
        :return:
        """
        self.app = Flask(__name__)
        # todo get this from db which is random on app install
        self.app.secret_key = self.global_config_dict['flask_secret']
        login_manager = LoginManager()
        login_manager.init_app(self.app)
        login_manager.login_view = 'login'
        #self.app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
        self.app.url_map.converters['regex'] = RegexConverter
        #self.app.register_blueprint(film, url_prefix='/film')
        self.app.register_blueprint(film)
        self.app.register_blueprint(film_collection)
        self.app.register_blueprint(tv)
        self.app.register_blueprint(process)
        self.app.register_blueprint(scan_paths)
        self.app.register_blueprint(settings)
        self.app.register_blueprint(dunes)
        self.app.register_blueprint(api)
        self.app.register_blueprint(report)
        self.app.register_blueprint(template)
        self.app.config["global_config_dict"] = self.global_config_dict
        self.app.config["AdminHTTPFilmFuncs"] = AdminHTTPFilmFuncs(self.Session, self.global_config_dict)
        self.app.config._version = __version__
        # todo not to have to deepcopy global config dict
        film_global_config_dict = deepcopy(self.global_config_dict)
        tv_global_config_dict = deepcopy(self.global_config_dict)
        #film_global_config_dict['library'] = 'film'
        #film_global_config_dict['library_id'] = 1
        #film_global_config_dict['downloaded_images_library_root_path'] = os.path.join(
        #    film_global_config_dict['downloaded_images_root_path'],
        #    film_global_config_dict['library'])
        film_library_config_dict = {'name': 'film', 'id': 1, 'downloaded_images_library_root_path':
            os.path.join(
                film_global_config_dict['downloaded_images_root_path'],
                'film')}
        film_collection_library_config_dict = {'name': 'film_collection', 'id': 1,
                                               'downloaded_images_library_root_path':
            os.path.join(
                film_global_config_dict['downloaded_images_root_path'],
                'film_collection')}
        tv_library_config_dict = {'name': 'tv', 'id': 2, 'downloaded_images_library_root_path':
            os.path.join(
                film_global_config_dict['downloaded_images_root_path'],
                'tv')}
        self.app.config["AdminHTTPFilmArtwork"] = FilmArtwork(args=self.args, Session=self.Session,
                                                              global_config_dict=film_global_config_dict,
                                                              library_config_dict=film_library_config_dict)
        self.app.config["AdminHTTPFilmCollectionArtwork"] = FilmCollectionArtwork(args=self.args, Session=self.Session,
                                                              global_config_dict=film_global_config_dict,
                                                              library_config_dict=film_collection_library_config_dict)
        self.app.config["AdminHTTPTVArtwork"] = TVArtwork(args=self.args, Session=self.Session,
                                                              global_config_dict=tv_global_config_dict,
                                                              library_config_dict=tv_library_config_dict)
        self.app.config["AdminHTTPTVEpisodeArtwork"] = TVEpisodeArtwork(args=self.args, Session=self.Session,
                                                              global_config_dict=tv_global_config_dict,
                                                              library_config_dict=tv_library_config_dict)
        self.app.config["AdminHTTPFilmCollectionFuncs"] = AdminHTTPFilmCollectionFuncs(self.Session,
                                                                                       self.global_config_dict)
        self.app.config["AdminHTTPTVFuncs"] = AdminHTTPTVFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPGenFuncs"] = AdminHTTPGenFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPProcessFuncs"] = AdminHTTPProcessFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPScanPathFuncs"] = AdminHTTPScanPathFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPDuneFuncs"] = AdminHTTPDuneFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPApiFuncs"] = AdminHTTPApiFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPReportFuncs"] = AdminHTTPReportFuncs(self.Session, self.global_config_dict)
        self.app.config["AdminHTTPTemplateFuncs"] = AdminHTTPTemplateFuncs(self.Session, self.global_config_dict)
        self.app.config["User"] = User
        @self.app.route('/')
        @self.app.route('/index')
        @login_required
        # Flask defaultly automagically looks for a templates folder in the same dir as this script
        def index():
            #films_awating_data = current_app.config["AdminHTTPGenFuncs"].films_awatting_data_aquasition()
            return render_template('index.html', title='Home')

        #@self.app.route('/resetSecretKey')
        #def resetSecretKey():
        #    self.app.config["AdminHTTPGenFuncs"].resetSecretKey()
        #    return redirect(url_for('index'))

        @self.app.route('/logo.png')
        def zp_icon():
            buffer = BytesIO()
            buffer.write(base64.b64decode(logo_b64))
            buffer.seek(0)
            return send_file(buffer, mimetype='.png')

        @self.app.route('/<regex("[0-9a-zA-Z\.\-]+\.css"):css>')
        def css(css):
            if css in ['w3.css', 'font-awesome.min.css']:
                return send_file(css)
            else:
                return abort(404)

        @self.app.route('/fonts/<regex("[0-9a-zA-Z\.\-]+\.(?:ttf|woff|woff2)(?:\?v=[\d\.]+)?"):font>')
        def font(font):
            log.warning(font)
            font_conformed = re.sub(r"""\?.*""", "", font)
            log.warning(font_conformed)
            if font_conformed in ['fontawesome-webfont.ttf', 'fontawesome-webfont.woff', 'fontawesome-webfont.woff2']:
                log.warning(font_conformed)
                return send_file(font_conformed)
            else:
                return abort(404)

        @self.app.route('/jquery.js')
        def jquery():
            return send_file('jquery.js')

        # used to relogin user from cookie
        @login_manager.user_loader
        def load_user(user_id):
            #log.error('user_id %s', user_id)
            user = current_app.config["User"](str(user_id), self.Session)
            #log.error('user %s', user)
            return user

        # logout page
        @self.app.route('/logout')
        def logout():
            logout_user()
            return redirect(url_for('index'))

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'GET':
                return render_template('login.html')
            username = request.form['username']
            password = request.form['password']
            #registered_user = User.query.filter_by(username=username, password=password).first()
            # todo message for invalid pass and disabled
            user_id = current_app.config["AdminHTTPGenFuncs"].veryify_uanme_pass(username, password)
            if user_id > 0:
                registered_user = current_app.config["User"](str(user_id), self.Session)
                #log.error('registered_user %s', registered_user)
            else:
                registered_user = None
            if registered_user is None:
                flash('Username or Password is invalid', 'error')
                return redirect(url_for('login'))
            # todo optionise remember_me
            login_user(registered_user, remember=True)
            flash('Logged in successfully')
            return redirect(request.args.get('next') or url_for('index'))

class User(UserMixin):
    def __init__(self, user_id, Session):
        self.id = user_id
        self.zp_user_id = int(user_id)
        self.Session = Session
        # todo get this from db
        self.privileges = self.get_privilegs()
        self.user_langs = self.get_library_langs()
        self.username = self.get_username()
        #self.template_dict = self.get_template_dict()

    def get_username(self):
        session = self.Session()
        username = session.query(TABLES.ZP_USER).filter(
            TABLES.ZP_USER.ID == self.zp_user_id
        ).one().USERNAME.capitalize()
        session.close()
        return username

    def get_library_langs(self):
        session = self.Session()
        library_lang_dict = {}
        zp_user_library_lang = session.query(TABLES.ZP_USER_LIBRARY_LANG).filter(
            TABLES.ZP_USER_LIBRARY_LANG.ZP_USER_ID == self.zp_user_id
        ).all()
        for lang in zp_user_library_lang:
            library_lang_dict[lang.ZP_LIBRARY_ID] = lang.ZP_LANG_ID
        session.close()
        return library_lang_dict

    def get_privilegs(self):
        session = self.Session()
        privilege = []
        zp_user_priv = session.query(TABLES.ZP_USER_PRIV).filter(
            TABLES.ZP_USER_PRIV.ZP_USER_ID == self.zp_user_id
        ).all()
        for priv in zp_user_priv:
            privilege.append(priv.ZP_USER_PRIV_ID)
        session.close()
        return privilege

    def get_template_dict(self):
        session = self.Session()
        zp_user = session.query(TABLES.ZP_USER).filter(
            TABLES.ZP_USER.ID == self.zp_user_id
        ).one()
        return_dict = {'template_film_icon': zp_user.template_film_icon,
                       'template_film_synopsis': zp_user.template_film_synopsis,
                       'template_film_dhttp': zp_user.template_film_dhttp,
                       'template_tv_icon': zp_user.template_tv_icon,
                       'template_tv_synopsis': zp_user.template_tv_synopsis,
                       'template_tv_dhttp': zp_user.template_tv_dhttp}
        session.close()
        return return_dict


