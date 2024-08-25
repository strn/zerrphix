# -*- coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

path_get_regex_dict = {'film': r'''/film/(?P<zp_film_id>\d+)$''',
                   'film_poster': r'''/film/\d+/poster$''',
                   'film_poster_eapi_eapieid': r'''/d/film/poster/(?P<eapi>[\da-z]+)/(?P<eapi_eid>[\da-z]+)/(?P<filename>[\d+a-z\+_\-\.]+)$'''
                   }