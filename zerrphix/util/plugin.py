# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import orm

from zerrphix.db.tables import TABLES

log = logging.getLogger(__name__)


def create_eapi_plugins_list(library_type, sys_modules, loaded_plugins, self_):
    eapi_film_plugins_access_list = []
    for loaded_plugin in loaded_plugins:
        if sys_modules.has_key(loaded_plugin):
            log.debug('loaded plugin: {0} in sys.modules'.format(loaded_plugin))
            if hasattr(sys_modules[loaded_plugin], '_types_'):
                log.debug('loaded plugin: {0} has attribute types'.format(loaded_plugin))
                if getattr(sys_modules[loaded_plugin], '_types_').has_key('eapi'):
                    log.debug('loaded plugin: {0}._types_ has key eapi'.format(loaded_plugin))
                    if getattr(sys_modules[loaded_plugin], '_types_')['eapi'].has_key(library_type):
                        log.debug(
                            '''loaded plugin: {0}._types_['eapi'] has key film. Adding to eapi_film_plugins_list'''.format(
                                loaded_plugin))
                        setattr(self_, sys_modules[loaded_plugin]._eapi_name_, getattr(
                            sys_modules[loaded_plugin],
                            sys_modules[loaded_plugin]._types_['eapi'][library_type]['class'])()
                                )
                        eapi_film_plugins_access_list.append(sys_modules[loaded_plugin]._eapi_name_)
                    else:
                        log.debug(
                            '''loaded plugin: {0}._types_['eapi'] does NOT have key film. NOT adding to eapi_film_plugins_list'''.format(
                                loaded_plugin))
                else:
                    log.debug('loaded plugin: {0}._types_ does NOT have key eapi'.format(loaded_plugin))
            else:
                log.debug('loaded plugin: {0} does NOT have attribute types'.format(loaded_plugin))
        else:
            log.debug('loaded plugin: {0} NOT in sys.modules'.format(loaded_plugin))
    return self_, eapi_film_plugins_access_list, loaded_plugins


def create_eapi_dict(session):
    # type: (object) -> object
    eapi_dict = {}
    eapi_dict['id'] = {}
    eapi_dict['name'] = {}
    try:
        eapi_s = session.query(TABLES.ZP_EAPI).all()
    except orm.exc.NoResultFound as e:
        log.debug(('No rows found in TABLES.ZP_EAPI'))
    else:
        for eapi in eapi_s:
            # TODO use eapi_dict['name'][eapi.NAME] = eapi.ID and eapi_dict['id'][eapi.ID] = eapi.NAME
            eapi_dict[eapi.NAME] = eapi.ID
            eapi_dict['name'][eapi.NAME] = eapi.ID
            eapi_dict['id'][eapi.ID] = eapi.NAME
    return eapi_dict
