# -*- coding: utf-8 
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import asc

from zerrphix.db.tables import TABLES

log = logging.getLogger(__name__)


def check_for_missing_eapi_eid(eapi_dict_got):
    for eapi in eapi_dict_got:
        if eapi_dict_got[eapi] is None:
            return True
    return False


def check_exhausted_eapi_lookup(eapi_dict, eapi_access_list):
    # eapi_dict_to_get_hash = md5(str(eapi_dict['to_get'])).hexdigest()
    for eapi in eapi_access_list:
        for eapi_to_get in eapi_dict['to_get']:
            # print('eapi_to_get %s' % eapi_to_get)
            if eapi_dict['to_get'][eapi_to_get] is None:
                for eapi_checked in eapi_dict['checked']:
                    # print('eapi_checked %s' % eapi_checked)
                    if eapi_to_get != eapi_checked:
                        # print(eapi, eapi_dict['checked'][eapi_to_get])
                        if eapi not in eapi_dict['checked'][eapi_to_get]:
                            # print('''eapi %s not in eapi_dict['checked'][eapi_to_get] %s''' % (eapi, eapi_dict['checked'][eapi_to_get]))
                            return False
                            # elif eapi_dict_to_get_hash not in eapi_dict['checked'][eapi_to_get][eapi]:
                        #	print('''eapi_dict_to_get_hash %s not in eapi_dict['checked'][eapi_to_get][eapi] %s''' % (eapi_dict_to_get_hash, eapi_dict['checked'][eapi_to_get][eapi]))
                        #	return False
                    else:
                        pass
                        # print('eapi_to_get %s = eapi_checked %s' % (eapi_to_get, eapi_checked))
    return True


def get_eapi_eid(eapi_dict, library, eapi_init):
    log.debug('eapi_init %s', eapi_init)
    eapi_to_lookup_list = []
    log.debug('eapi_to_lookup_list %s', eapi_to_lookup_list)
    processing_complete = False
    for eapi_to_get in eapi_dict['to_get']:
        # print('eapi_to_get %s' % eapi_to_get)
        if eapi_dict['to_get'][eapi_to_get] is None:
            log.debug('''eapi_dict['to_get'][eapi_to_get] %s is None (eapi_to_get %s)''',
                      eapi_dict['to_get'][eapi_to_get], eapi_to_get)
            # print('''eapi_dict['to_get'][eapi_to_get] %s is None''' % eapi_dict['to_get'][eapi_to_get])
            # print(eapi_init.eapi_name, eapi_dict['checked'][eapi_init.eapi_name])
            if eapi_to_get not in eapi_dict['checked'][eapi_init.eapi_name]:
                log.debug('''eapi_to_get %s not in eapi_dict['checked'][eapi_init.eapi_name] %s''',
                          eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name])
                # print('eapi_to_get %s not in checked %s' % (eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name]))
                if eapi_to_get in eapi_init._supported_source_eapi_[library]['want']:
                    log.debug('''eapi_to_get %s in eapi_init._supported_source_eapi_[library]['want'] %s''',
                              eapi_to_get, eapi_init._supported_source_eapi_[library]['want'])
                    # print('eapi_to_get %s in want %s' % (eapi_to_get, eapi_init._supported_source_eapi_[library]['want']))
                    for eapi_have in eapi_dict['to_get']:
                        log.debug('''eapi_have %s in eapi_dict['to_get'] %s''', eapi_have, eapi_dict['to_get'])
                        if eapi_dict['to_get'][eapi_have] is not None:
                            log.debug('''eapi_dict['to_get'][eapi_have] %s is not None (eapi_have %s)''',
                                      eapi_dict['to_get'][eapi_have], eapi_have)
                            if eapi_have in eapi_init._supported_source_eapi_[library]['have'] and eapi_have not in \
                                eapi_dict['looked_up'][eapi_init.eapi_name]:
                                log.debug(
                                    '''eapi_have %s in eapi_init._supported_source_eapi_[library]['have'] %s and'''
                                    ''' eapi_have %s not in eapi_dict['looked_up'][eapi_init.eapi_name] %s''',
                                    eapi_have, eapi_init._supported_source_eapi_[library]['have'],
                                    eapi_have, eapi_dict['looked_up'][eapi_init.eapi_name])
                                # print(eapi_dict['checked'])
                                eapi_to_lookup_list.append({'eapi': eapi_have, 'eid': eapi_dict['to_get'][eapi_have]})
                                # if eapi
                                # print('adding eapi_to_get %s to checked for eapi_have %s %s' % (eapi_to_get, eapi_have, eapi_dict['to_get']))
                                log.debug(
                                    '''adding eapi_to_get %s to eapi_dict['checked'][eapi_init.eapi_name] %s (eapi_init.eapi_name %s)''',
                                    eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name], eapi_init.eapi_name)
                                eapi_dict['checked'][eapi_init.eapi_name].append(eapi_to_get)
                                # if eapi_have not in eapi_dict['looked_up'][eapi_init.eapi_name]:
                                log.debug(
                                    '''adding eapi_have %s to eapi_dict['looked_up'][eapi_init.eapi_name] %s (eapi_init.eapi_name %s)''')
                                eapi_dict['looked_up'][eapi_init.eapi_name].append(eapi_have)
                            else:
                                log.debug(
                                    '''eapi_have %s not in eapi_init._supported_source_eapi_[library]['have'] %s and/or'''
                                    ''' eapi_have %s in eapi_dict['looked_up'][eapi_init.eapi_name] %s''',
                                    eapi_have, eapi_init._supported_source_eapi_[library]['have'],
                                    eapi_have, eapi_dict['looked_up'][eapi_init.eapi_name])
                                if eapi_to_get not in eapi_dict['checked'][eapi_init.eapi_name]:
                                    log.debug(
                                        '''adding eapi_to_get %s to eapi_dict['checked'][eapi_init.eapi_name] %s (eapi_init.eapi_name %s)''',
                                        eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name], eapi_init.eapi_name)
                                    eapi_dict['checked'][eapi_init.eapi_name].append(eapi_to_get)
                        else:
                            log.debug('''eapi_dict['to_get'][eapi_have] %s is None (eapi_have %s)''',
                                      eapi_dict['to_get'][eapi_have], eapi_have)
                else:
                    log.debug('''eapi_to_get %s not in eapi_init._supported_source_eapi_[library]['want'] %s''',
                              eapi_to_get, eapi_init._supported_source_eapi_[library]['want'])
            else:
                log.debug('''eapi_to_get %s in eapi_dict['checked'][eapi_init.eapi_name] %s (eapi_init.eapi_name %s)''',
                          eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name], eapi_init.eapi_name)
        else:
            log.debug('''eapi_dict['to_get'][eapi_to_get] %s is not None (eapi_to_get %s)''',
                      eapi_dict['to_get'][eapi_to_get], eapi_to_get)

    return process_eapi_dict(eapi_to_lookup_list, eapi_dict, library, eapi_init)


def process_eapi_dict(eapi_to_lookup_list, eapi_dict, library, eapi_init):
    log.debug('eapi_to_lookup_list %s, eapi_init.eapi_name %s', eapi_to_lookup_list, eapi_init.eapi_name)
    if eapi_to_lookup_list:
        log.debug(eapi_to_lookup_list)
        # raise SystemExit
    for eapi_to_lookup in eapi_to_lookup_list:
        if None in eapi_dict['to_get'].viewvalues():
            # if eapi_init.eapi_name not in eapi_dict['used']:
            # eapi_dict['used'].append(eapi_init.eapi_name)
            log.debug('eapi_to_lookup %s, eapi_init.eapi_name %s', eapi_to_lookup, eapi_init.eapi_name)
            eapi_acquired_dict = eapi_init.acquire_external_eid(eapi_to_lookup['eapi'], eapi_to_lookup['eid'], library)
            # print(eapi_acquired_dict)
            for eapi_acquired in eapi_acquired_dict:
                # print(eapi_acquired)
                if eapi_dict['to_get'][eapi_acquired] is None:
                    eapi_dict['to_get'][eapi_acquired] = eapi_acquired_dict[eapi_acquired]
    return eapi_dict


def combination_check(eapi_dict, library):
    keep_looking = check_for_missing_eapi_eid(eapi_dict['to_get'])
    if keep_looking is False:
        new_conbination_tried = True
    else:
        new_conbination_tried = False
    while new_conbination_tried is False:
        for eapi_to_get in eapi_dict['to_get']:
            # print('main', eapi_to_get)
            if eapi_dict['to_get'][eapi_to_get] is None:
                # print('''eapi_dict['to_get'][eapi_to_get] %s is None''' % eapi_dict['to_get'][eapi_to_get])
                for eapi in eapi_dict['init']:
                    # print('now using eapi %s' % eapi)
                    combination = '%s|%s' % (eapi, eapi_to_get)
                    if eapi == eapi_to_get and combination not in eapi_dict['cominations_tried']:
                        eapi_dict['cominations_tried'].append(combination)
                        # print(eapi, eapi_dict['checked'][eapi_to_get], eapi_dict['cominations_tried'])
                        # print(combination)
                    if eapi not in eapi_dict['checked'][eapi_to_get] and combination not in eapi_dict[
                        'cominations_tried']:
                        if isinstance(eapi_dict['init'][eapi], object):
                            if hasattr(eapi_dict['init'][eapi], '_supported_source_eapi_') and hasattr(
                                eapi_dict['init'][eapi], 'acquire_external_eid'):
                                # print('calling get_eapi_eid')
                                eapi_dict = get_eapi_eid(eapi_dict, library, eapi_dict['init'][eapi])
                        eapi_dict['cominations_tried'].append(combination)
                        new_conbination_tried = True
        keep_looking = False
        new_conbination_tried = True
    return eapi_dict, keep_looking


def gather_eids(eapi_dict, library):
    eapi_dict['cominations_tried'] = []
    keep_looking = True

    while keep_looking is True:
        log.debug('keep_looking')
        eapi_dict, keep_looking = combination_check(eapi_dict, library)

    if check_for_missing_eapi_eid(eapi_dict['to_get']) is True:
        log.debug('no combination left to try')
    return eapi_dict
