# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
from sqlalchemy import orm, and_
import logging
from zerrphix.db.tables import TABLES
from zerrphix.db import commit, flush
from zerrphix.util.plugin import create_eapi_dict
from sqlalchemy import or_
import os
import base64
import math
import bcrypt
from zerrphix.util.text import date_time

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
# https://stackoverflow.com/questions/10946795/render-multiple-templates-at-once-in-flask
# https://www.w3schools.com/w3css/tryw3css_templates_analytics.htm
# http://fontawesome.io/cheatsheet/
# https://github.com/jpercent/flask-control
# http://code.nabla.net/doc/jinja2/api/jinja2/jinja2.filters.html
log = logging.getLogger(__name__)


class AdminHTTPTemplateFuncs(object):
    def __init__(self, Session, global_config_dict):
        # logging.config.dictConfig(LOG_SETTINGS)
        self.Session = Session
        self.global_config_dict = global_config_dict
        self.eapi_dict = create_eapi_dict(Session)

    def add_template(self, ref_name, path):
        session = self.Session()
        add_zp_template = TABLES.ZP_TEMPLATE(
            REF_NAME = ref_name,
            PATH = path,
            PATH_TYPE = 2,
            LAST_MOD_DATETIME = date_time()
        )
        session.add(add_zp_template)
        commit(session)
        session.close()

    def update_template(self, zp_template_id):
        session = self.Session()
        session.query(TABLES.ZP_TEMPLATE).filter(TABLES.ZP_TEMPLATE.ID == zp_template_id).update(
            {"LAST_MOD_DATETIME": date_time()})
        commit(session)
        session.close()

    def check_template_name_free(self, ref_name):
        session = self.Session()
        try:
            session.query(
                TABLES.ZP_TEMPLATE
            ).filter(
                TABLES.ZP_TEMPLATE.REF_NAME == ref_name
            ).one()
        except orm.exc.NoResultFound:
            name_is_free = True
        else:
            name_is_free = False
        session.close()
        return name_is_free