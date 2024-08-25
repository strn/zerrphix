# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

import pytvmaze
from zerrphix.util import rate_limited

log = logging.getLogger(__name__)

_version_ = "0.1"
_libraries_ = ['tv']
_types_ = {'eapi':
               {'tv':
                    {'class': 'TVMaze'}
                }
           }
_available_eids_ = {'tv': [{'want': 'thetvdb', 'have': 'imdb'}]}
_eapi_name_ = "tvmaze"
tmdb_image_url = "https://image.tmdb.org/t/p/original/"


def available_eid(have_eapi, want_eapi, library):
    for available_eid in _available_eids_[library]:
        if available_eid['want'] == want_eapi and available_eid['have'] == have_eapi:
            log.debug('available_eid: {0} have_eapi: {1} want_eapi: {2}'.format(
                available_eid,
                have_eapi,
                want_eapi))
            return True
    return False


class TVMaze(object):
    def __init__(self):
        self.tvm = pytvmaze.TVMaze()
        self.available_eid = available_eid
        self.eapi_name = 'tvmaze'
        self._supported_source_eapi_ = {'film': {'want': 'imdb', 'have': 'tmdb'},
                                        'tv': {'want': ['imdb', 'thetvdb', 'tvmaze', 'tvrage'],
                                               'have': ['imdb', 'thetvdb', 'tvmaze', 'tvrage']}}

    @rate_limited(10, 1.0)
    def acquire_external_eid(self, eapi_have, eapi_have_eid, library):
        # print('acquire_external_eid called')
        kwargs = None
        return_dict = {}
        if library == 'tv':
            if eapi_have == 'imdb':
                # self.get_thetvdb_id_from_imdbid(have_eapi_eid)
                kwargs = {'imdb_id': eapi_have_eid}
            elif eapi_have == 'thetvdb':
                kwargs = {'tvdb_id': eapi_have_eid}
            elif eapi_have == 'tvmaze':
                kwargs = {'maze_id': eapi_have_eid}
            elif eapi_have == 'tvrage':
                kwargs = {'tvrage_id': eapi_have_eid}
                # print(have_eapi_eid)
            try:
                show = self.tvm.get_show(**kwargs)
            except pytvmaze.ShowNotFound as e:
                log.warning(('Show not found. Exception: \n\n{0}\n\noccured').format(e), exc_info=True)
            except pytvmaze.MissingParameters as e:
                log.warning(('Missing Parameters. Exception: \n\n{0}\n\noccured').format(e), exc_info=True)
            else:
                if hasattr(show, 'externals'):
                    log.debug('externals %s', show.externals)
                    if 'thetvdb' in show.externals.keys():
                        # print(show.externals['thetvdb'])
                        for eapi in show.externals:
                            if show.externals[eapi] is not None:
                                return_dict[eapi] = show.externals[eapi]
                    else:
                        log.debug('thetvdb not in externals: {0}'.format(show.externals.keys()))
                if hasattr(show, 'id'):
                    return_dict['tvmaze'] = show.id
                else:
                    log.debug('externals not in show: {0}'.format(dir(show)))

        # return_dict['thetvdb'] = 548
        # return_dict['thetvdb'] = 333
        return return_dict

    def get_eapi_eid(self, have_eapi, have_eapi_eid, want_eapi, library):
        if library == 'tv':
            if have_eapi == 'imdb' and want_eapi == 'thetvdb':
                return self.get_thetvdb_id_from_imdbid(have_eapi_eid)
        return None

    @rate_limited(10, 1.0)
    def get_thetvdb_id_from_imdbid(self, have_eapi_eid):
        # print(have_eapi_eid)
        try:
            show = self.tvm.get_show(imdb_id=have_eapi_eid)
        except pytvmaze.ShowNotFound as e:
            log.warning(('Show not found. Exception: \n\n{0}\n\noccured').format(e), exc_info=True)
        except pytvmaze.MissingParameters as e:
            log.warning(('Missing Parameters. Exception: \n\n{0}\n\noccured').format(e), exc_info=True)
        else:
            if hasattr(show, 'externals'):
                if 'thetvdb' in show.externals.keys():
                    # print(show.externals['thetvdb'])
                    return show.externals['thetvdb']
                else:
                    log.debug('thetvdb not in externals: {0}'.format(show.externals.keys()))
            else:
                log.debug('externals not in show: {0}'.format(dir(show)))
        return None
