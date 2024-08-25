# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

# http://chase-seibert.github.io/blog/2014/01/12/python-unicode-console-output.html
#import datetime
import json
import logging
import os
import re
import sys
import roman
import xmltodict
from unidecode import unidecode
from datetime import date, datetime, timedelta
from six import string_types
from zerrphix.util.numbers import is_even
import locale
import pprint

import zerrphix.constants

# print(locale.getdefaultlocale()[1])

log = logging.getLogger(__name__)

caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Lt)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
digits = "([0-9])"

# Taken from https://github.com/Flexget
# Determine the encoding for io
io_encoding = None
if hasattr(sys.stdout, 'encoding'):
    io_encoding = sys.stdout.encoding
if not io_encoding:
    try:
        io_encoding = locale.getpreferredencoding()
    except Exception:
        pass
if not io_encoding:
    # Default to utf8 if nothing can be determined
    io_encoding = 'utf8'
else:
    # Normalize the encoding
    io_encoding = io_encoding.lower()
    if io_encoding == 'cp65001':
        io_encoding = 'utf8'
    elif io_encoding in ['us-ascii', '646', 'ansi_x3.4-1968']:
        io_encoding = 'ascii'

def all_keys_in_dict(dict, keys):
    for key in keys:
        if key not in dict:
            return False
    return True

def xml_to_dict(xml_path):
    """Read and convert template xml file to dict

        Args:
            template_xml_path (str): path to xml template

        Returns:
            dict: template xml converted to dict

        Raises:
            Exception: if template_xml_path is not a file or does not exist

    """
    if os.path.isfile(xml_path):
        with open(xml_path) as fd:
            template_dict = json.loads(json.dumps(xmltodict.parse(fd.read())))
        if isinstance(template_dict, dict):
            return template_dict
    else:
        log.critical('xml_path: {0} is not a file or does not exist'.format(
            xml_path))
        raise Exception('xml_path: {0} is not a file or does not exist'.format(
            xml_path))
    return None

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def split_into_sentences(text):
    # http://stackoverflow.com/questions/4576077/python-split-text-on-sentences
    original_text = text
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    if "Ph.D" in text: text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] ", " \\1<prd> ", text)
    text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)
    text = re.sub(caps + "[.]" + caps + "[.]", "\\1<prd>\\2<prd>", text)
    text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", text)
    text = re.sub(" " + suffixes + "[.]", " \\1<prd>", text)
    text = re.sub(" " + caps + "[.]", " \\1<prd>", text)
    if "”" in text: text = text.replace(".”", "”.")
    if "\"" in text: text = text.replace(".\"", "\".")
    if "!" in text: text = text.replace("!\"", "\"!")
    if "?" in text: text = text.replace("?\"", "\"?")
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", text)
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    if not sentences:
        if text:
            return [text.strip()]
        else:
            return [original_text]
    return sentences


def conform_track_lang(track_lang):
    return re.sub(r'''(?:un|undefined)(?:[\s]+)?\/(?:[\s]+)?([a-z]+)''', r'\1', track_lang)


def remove_non_alpha_numeric(string):
    return re.sub(r""""[^\w\d]+""", " ", string, flags=re.UNICODE)


def consolidate_spaces(string):
    return re.sub(r"""\s+""", " ", string).strip()


def string_to_list(string, seperator, count=None):
    if isinstance(count, int) and count > 0:
        return string.split(seperator, count)
    return string.split(seperator)


def conform_title(title, option):
    """
    TO DO:

    Convert roman numerlas to digit

    """
    # (?:BluRay|BDRip|BRRip|BD|HDTV|WEBRip|Web-?dl|1080|720|480|576|unrated)

    optional_word_list = ["in(?:[^\w]|_)+the", "the(?:[^\w]|_)+movie", "part", "LIMITED"]

    # new option to remove genre names from title

    if option == 'replace_symbols_with_words':
        # if 'replace_symbols_with_words' in options:
        title = replace_symbols_with_words(title)

    if option == 'replace_release_words_with_spaces':
        # if 'replace_invalid_words_with_spaces' in options:
        title = replace_release_words_with_spaces(title)

    if option == 'replace_optional_words_with_spaces':
        # if 'replace_optional_words_with_spaces' in options:
        title = replace_words_with_spaces(title, optional_word_list)

    if option == 'replace_int_with_roman_numerals':
        # if 'replace_int_with_roman_numerals' in options:
        title = int_in_string_to_roman(title)

    if option == 'replace_roman_numerals_with_int':
        # if 'replace_roman_numerals_with_int':
        title = roman_int_text_to_int(title)

    if option == 'replace_roman_numerals_with_space':
        title = roman_int_text_to_space(title)

    if option == 'replace_int_with_space':
        title = int_in_string_to_space(title)

    if option == 'accent_to_asscii':
        title = unidecode(title)

    if option == 'remove_non_alnum_near_alnum':
        title = remove_non_alnum_near_alnum(title)

    if option == 'non_alnum_dash_to_spaces':
        title = non_alnum_dash_to_spaces(title)

    if option == 'non_alnum_to_spaces':
        title = non_alnum_to_spaces(title)

    if option == 'remove_underscore':
        title = remove_underscore(title)

    if option == 'non_word_chars_to_spaces':
        title = non_word_chars_to_spaces(title)
        title = remove_spaces_between_uppercase_letters(title)

    if option == 'remove_spaces_between_uppercase_letters':
        title = remove_spaces_between_uppercase_letters(title)

    if option == 'remove_spaces':
        title = remove_spaces(title)

    if option == 'replace_space_with_dot':
        title = replace_space_with_dot(title)

    if option == 'replace_non_alnum_with_spaces':
        title = non_alnum_to_spaces(title)

    if option == 'remove_non_alnum':
        title = remove_non_alnum(title)

    if option == 'remove_country_identifier':
        title = remove_country_identifier(title)

    if option == 'extract_year_from_bracket_contents':
        bracket_dict = {0: {'bracket_open': '[', 'bracket_close': ']'},
                        1: {'bracket_open': '(', 'bracket_close': ')'},
                        2: {'bracket_open': '{', 'bracket_close': '}'},
                        }
        for bracket in bracket_dict:
            title = extract_year_from_bracket_contents(title, bracket_dict[bracket]['bracket_open'],
                                                       bracket_dict[bracket]['bracket_close'])

    if option == 'remove_year':
        title = remove_year(title)

    title = consolidate_spaces(title)

    return title


def remove_year(title):
    return re.sub(r"""(\b\d{4}\b)[^\w]*$""", ' ', title)


def replace_space_with_dot(title):
    return '{0}.'.format(re.sub(r'\s+', '.', title))


def remove_spaces(title):
    return re.sub(r'\s+', '', title)


def replace_release_words_with_spaces(string):
    pattern_list = ['pattern_video_source',
                    'pattern_video_tags',
                    'pattern_video_s3d',
                    'pattern_video_repack',
                    'pattern_subtitle_tags',
                    'pattern_video_format']

    for pattern in pattern_list:
        log.debug('string: {0} before re.sub {1}'.format(string, getattr(zerrphix.constants, pattern)))

        string = re.sub(getattr(zerrphix.constants, pattern), ' ', string, flags=re.IGNORECASE | re.UNICODE)

        log.debug('string: {0} after re.sub {1}'.format(string, getattr(zerrphix.constants, pattern)))

    return string


def replace_symbols_with_words(string):
    reaplce_synbols_dict = {}
    reaplce_synbols_dict[0] = {}
    reaplce_synbols_dict[0]['regex'] = r'&'
    reaplce_synbols_dict[0]['replace_with'] = ' and '

    if isinstance(string, basestring):

        for replace in reaplce_synbols_dict:
            string = re.sub(reaplce_synbols_dict[replace]['regex'], reaplce_synbols_dict[replace]['replace_with'],
                            string, flags=re.I | re.UNICODE)

    return string


def replace_words_with_spaces(string, _list, case_insensitive=True):
    for pattern in _list:
        string = re.sub(r"""\b{0}\b""".format(pattern), ' ', string, flags=re.UNICODE | re.IGNORECASE)

        # print(string, pattern)

    return string


def old_replace_words_with_spaces(string, _list, case_insensitive=True):
    if isinstance(_list, list):

        if _list:

            _words = r""""""

            for item in _list:
                _words += r"""((?:^|(?:[^\w]|_))' + item + r'(?:(?:[^\w]|_)|$))|"""

                print(_words)

            if _words[-1:] == r'|':
                _words = _words[:-1]

            if case_insensitive:

                _pattern = re.compile(_words, re.IGNORECASE | re.UNICODE)

            else:

                _pattern = re.compile(_words)

            return _pattern.sub(' ', string)

        else:

            return string
    else:

        return string


def regex_match_int_to_roman(match):
    group_1 = match.group(1)

    return '{0}'.format(roman.toRoman(int(group_1)))


def int_in_string_to_space(string):
    return re.sub(r"""\b([1-9]|0[1-9]|1[0-9]|20)\b""", regex_match_int_to_roman, string)


def int_in_string_to_roman(string):
    return re.sub(r"""\b([1-9]|0[1-9]|1[0-9]|20)\b""", regex_match_int_to_roman, string)


def regex_match_roman_to_int(match):
    group = match.group(1)

    if len(group) >= 1:

        return str(roman.fromRoman(group)).decode("utf-8")

    else:

        return match.group(1)


def regex_match_roman_to_space(match):
    group = match.group(1)

    if len(group) >= 1:

        return ' '

    else:

        return match.group(1)


def roman_int_text_to_space(string):
    # return re.sub(r"""(?:^|\s)(IX|IV|V?I{0,3})(?:\s|$)""", regex_match_roman_to_space, string)

    return re.sub(r"""(?<!^)\b(IX|IV|V?I{0,3})\b""", regex_match_roman_to_space, string)


def roman_int_text_to_int(string):
    # return re.sub(r"""(?:^|\s)(IX|IV|V?I{0,3})(?:\s|$)""", regex_match_roman_to_int, string)

    return re.sub(r"""(?<!^)\b(IX|IV|V?I{0,3})\b""", regex_match_roman_to_int, string)


def remove_brackets_and_contents(string, bracket_open, bracket_close):
    return re.sub(r"""(\{0}.+?\{1})""".format(bracket_open, bracket_close), " ", string)


def re_match_re_search_year(match):
    group = match.group(1)

    log.debug('groups {0}'.format(match.groups()))

    log.debug('match.group(1) {0}'.format(group))

    year_pattern = r"""\b(?P<year>[1-2][0-9]{3})\b"""

    log.debug("trying to match match.group(1) {0} against year_pattern {1}".format(
        group,
        year_pattern))

    regex_search = re.search(year_pattern, group)

    if regex_search:
        return ' {0} '.format(regex_search.groupdict()['year'])

    return ' '


def extract_year_from_bracket_contents(string, bracket_open, bracket_close):
    pattern = r"""(\{0}.+?\{1})""".format(bracket_open, bracket_close)

    log.debug('pattern {0} with bracket_open {1} and bracket_close {2} on string {3}'.format(
        pattern,
        bracket_open,
        bracket_close,
        string))

    return re.sub(pattern, re_match_re_search_year, string)


def dots_to_spaces(string):
    return re.sub(r"""\.+""", " ", string)


def remove_non_alpha_num_punct(string):
    # why neg lookahead for underscore. should realy comment as I gp. DOH.
    # I think is because titles are not generally speareted by _
    # but _ can be used to deonte the end of the title

    return re.sub(r"""(?!_)[^\d\w'`\-\s]""", ' ', string, flags=re.UNICODE | re.IGNORECASE)


def remove_underscore(string):
    # for when _ is in the title. This is needed due to remove_non_alpha_num_punct
    return re.sub(r"""_""", ' ', string, flags=re.UNICODE | re.IGNORECASE)


def remove_url_from_string(string):
    return re.sub(r"""((?:https?:\/\/)(?:www\.)?[-\w\d@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-\w\d@:%_\+.~#?&//=]*))""",
                  ' ', string, flags=re.UNICODE | re.IGNORECASE)


def remove_standalone_non_alpha_num(string):
    return re.sub(r"""\s[^\w\d]\s""", ' ', string, flags=re.UNICODE | re.IGNORECASE)


def remove_non_alnum_near_alnum(string):
    return re.sub(r"""(^|\w|\d)[^\w\d\s]+(\w|\d|\s|$)""", r'\1\2', string, flags=re.UNICODE | re.IGNORECASE)


def remove_dots_near_alnum(string):
    return re.sub(r"""(^|\w|\d|\s)\.+(\w|\d)""", r'\1 \2', string, flags=re.UNICODE | re.IGNORECASE)


def remove_spaces_between_uppercase_letters(string):
    return re.sub(r"""([A-Z])\s(?=[A-Z](?:\s|$))""", r'\1', string)


def non_word_chars_to_spaces(string):
    return re.sub(r"""\b[^\w]+\b""", r' ', string, flags=re.IGNORECASE)


def check_year_in_string(string):
    if re.search(r"""\b(?P<year>(?:19|20)\d{2})\b""", string):
        return True
    return False


def non_alnum_dash_to_spaces(string):
    return re.sub(r"""[^\w-]""", r' ', string, flags=re.UNICODE | re.IGNORECASE)


def non_alnum_to_spaces(string):
    return re.sub(r"""[^\w ]""", r' ', string, flags=re.UNICODE | re.IGNORECASE)


def remove_non_alnum(string):
    return re.sub(r"""[^\w ]""", r'', string, flags=re.UNICODE | re.IGNORECASE)


def remove_country_identifier(string):
    return re.sub(r"""\[?\(?\bu(?:k|s)\b\)?\]?""", r'', string, flags=re.UNICODE | re.IGNORECASE)


def sanitise_film_filename(string):
    bracket_dict = {0: {'bracket_open': '[', 'bracket_close': ']'},
                    1: {'bracket_open': '(', 'bracket_close': ')'},
                    2: {'bracket_open': '{', 'bracket_close': '}'},
                    }

    for bracket in bracket_dict:
        log.debug('string: {0} before extract_year_from_bracket_contents(string, {1}, {2})'.format(
            string,
            bracket_dict[bracket]['bracket_open'],
            bracket_dict[bracket]['bracket_close']))

        string = extract_year_from_bracket_contents(string, bracket_dict[bracket]['bracket_open'],
                                                    bracket_dict[bracket]['bracket_close'])

        log.debug('string: {0} after extract_year_from_bracket_contents(string, {1}, {2})'.format(
            string,
            bracket_dict[bracket]['bracket_open'],
            bracket_dict[bracket]['bracket_close']))

    log.debug('string: {0} before remove_url_from_string(string)'.format(string))

    string = remove_url_from_string(string)

    log.debug('string: {0} after remove_url_from_string(string)'.format(string))

    if check_year_in_string(string) == True:

        log.debug('string: {0} before remove_standalone_non_alpha_num(string)'.format(string))

        string = remove_standalone_non_alpha_num(string)

        log.debug('string: {0} after remove_standalone_non_alpha_num(string)'.format(string))

        log.debug('string: {0} before remove_non_alpha_num_punct(string)'.format(string))

        string = remove_non_alpha_num_punct(string)

        log.debug('string: {0} after remove_non_alpha_num_punct(string)'.format(string))

        log.debug('string: {0} before replace_release_words_with_spaces(string)'.format(string))

        string = replace_release_words_with_spaces(string)

        log.debug('string: {0} after replace_release_words_with_spaces(string)'.format(string))

    else:

        log.debug('string: {0} before remove_url_from_string(string)'.format(string))

        string = remove_dots_near_alnum(string)

        log.debug('string: {0} after remove_url_from_string(string)'.format(string))

    log.debug('string: {0} before consolidate_spaces(string)'.format(string))

    string = consolidate_spaces(string)

    log.debug('string: {0} after consolidate_spaces(string)'.format(string))

    return string


def mk_int(s, F=False):
    if isinstance(s, string_types):
        s = s.strip()
        try:
            return int(float(s))
        except:
            pass
    elif isinstance(s, int) or isinstance(s, long):
        return s
    elif isinstance(s, float):
        return int(s)

    if F == True:
        return False
    else:
        return 0


def date_time(offset=0, type=None):
    # return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime() - offset)
    if not isinstance(offset, timedelta):
        if isinstance(offset, int):
            offset = timedelta(seconds=offset)
        else:
            offset = timedelta(seconds=0)
    if type == 'ymd_hms':
        return (datetime.now() - offset).strftime("%Y%m%d_%H%M%S")
    else:
        return (datetime.now() - offset).strftime("%Y-%m-%d %H:%M:%S")

def construct_dune_ui_entity_return_list(entity_search_results, entity_name, **kwargs):
    return_list = []
    entity_id_order_list = []
    entity_processing_dict = {}
    root_render_image_url_http = kwargs['root_render_image_url_http']
    root_template_image_url_http = kwargs['root_template_image_url_http']
    root_user_url_dhttp = kwargs['root_user_url_dhttp']
    image_type = kwargs['image_type']
    alt_icon = kwargs['alt_icon'] if 'alt_icon' in kwargs else ''
    alt_icon_sel = kwargs['alt_icon_sel'] if 'alt_icon_sel' in kwargs else ''
    if entity_name == 'ZP_FILM_ID':
        library_text = 'film'
    elif entity_name == 'ZP_TV_ID':
        library_text = 'tv'
    for result in entity_search_results:
        TEMPLATE_NAME = result.REF_NAME
        #entity_id = result.ZP_TV_ID
        entity_id = getattr(result, entity_name)
        if entity_id not in entity_id_order_list:
            entity_id_order_list.append(entity_id)
        if entity_id not in entity_processing_dict:
            entity_processing_dict[entity_id] = {'title': result.TITLE}
            entity_processing_dict[entity_id]['args'] = '%s=%s' % (
                    entity_name, entity_id
                )
            entity_processing_dict[entity_id]['menu'] = '%s_synop' % library_text
            if library_text == 'film':
                zp_film_collection_id = getattr(result, 'ZP_FILM_COLLECTION_ID')
                entity_processing_dict[entity_id]['args'] += '&ZP_FILM_COLLECTION_ID=%s' % (
                    zp_film_collection_id if zp_film_collection_id is not None else 0
                )

            # tv_season_dict[zp_tv_id]['ZP_TV_EPISODE_FILEFOLDER_ID'] = result.ZP_TV_EPISODE_FILEFOLDER_ID
        if is_even(result.ZP_IMAGE_SUB_TYPE):
            if (result.ZP_IMAGE_SUB_TYPE == 4 and result.DATETIME is not None) or \
                (result.ZP_IMAGE_SUB_TYPE == 2 and result.DATETIME is None) or \
                (result.ZP_IMAGE_SUB_TYPE == 2 and 'icon_sel' not in entity_processing_dict[entity_id]):
                entity_processing_dict[entity_id]['icon_sel'] = {}
                entity_processing_dict[entity_id]['icon_sel']['hash'] = result.HASH
                entity_processing_dict[entity_id]['icon_sel']['post_image_type_text'] = result.POST_IMAGE_TYPE_TEXT
                entity_processing_dict[entity_id]['icon_sel']['ext'] = result.EXT
        else:
            if (result.ZP_IMAGE_SUB_TYPE == 3 and result.DATETIME is not None) or \
                (result.ZP_IMAGE_SUB_TYPE == 1 and result.DATETIME is None) or \
                (result.ZP_IMAGE_SUB_TYPE == 1 and 'icon' not in entity_processing_dict[entity_id]):
                entity_processing_dict[entity_id]['icon'] = {}
                entity_processing_dict[entity_id]['icon']['hash'] = result.HASH
                entity_processing_dict[entity_id]['icon']['post_image_type_text'] = result.POST_IMAGE_TYPE_TEXT
                entity_processing_dict[entity_id]['icon']['ext'] = result.EXT

    log.debug('entity_processing_dict %s', pprint.pformat(entity_processing_dict))
    for entity_id in entity_id_order_list:
        entity_procseed_dict = {}
        entity_procseed_dict[r'::TITLE::'] = entity_processing_dict[entity_id]['title']
        entity_procseed_dict[r'::%s::' % entity_name] = str(entity_id)
        entity_procseed_dict[r'::menu::'] = entity_processing_dict[entity_id]['menu']
        entity_procseed_dict[r'::args::'] = entity_processing_dict[entity_id]['args']
        if 'icon' in entity_processing_dict[entity_id]:
            entity_procseed_dict[r'::icon_url::'] = '{0}/{1}/{2}/{3}/.{4}{5}.{6}.{7}'.format(
                root_render_image_url_http,
                library_text,
                TEMPLATE_NAME,
                str(entity_id),
                image_type,
                entity_processing_dict[entity_id]['icon']['post_image_type_text'],
                entity_processing_dict[entity_id]['icon']['hash'],
                entity_processing_dict[entity_id]['icon']['ext']
            )
        if 'icon_sel' in entity_processing_dict[entity_id]:
            entity_procseed_dict['::icon_sel_url::'] = '{0}/{1}/{2}/{3}/.{4}{5}.{6}.{7}'.format(
                root_render_image_url_http,
                library_text,
                TEMPLATE_NAME,
                str(entity_id),
                image_type,
                entity_processing_dict[entity_id]['icon_sel']['post_image_type_text'],
                entity_processing_dict[entity_id]['icon_sel']['hash'],
                entity_processing_dict[entity_id]['icon_sel']['ext']
            )
        return_list.append(entity_procseed_dict)
    log.debug('return_list %s', return_list)
    if not return_list and alt_icon:
        return_list=[
            {'::icon_url::': '%s/%s' % (root_template_image_url_http, alt_icon),
             '::icon_sel_url::': '%s/%s' % (root_template_image_url_http, alt_icon_sel),
             '::menu::': root_user_url_dhttp,
             '::args::': '',
             '::TITLE::': 'ALT'}
        ]
    log.debug('return_list %s', pprint.pformat(return_list))
    return return_list

def bitrate_text_to_float(bitrate_string):
    bitrate = float(0)
    if isinstance(bitrate_string, string_types):
        bitrate_pattern = r'''[^\d]+(?P<bitrate>\d+(\.\d+)?)(?P<unit>[kmg]?bps)?'''
        bitrate_string_conformed = re.sub('\s+', '', bitrate_string)
        match = re.search(bitrate_pattern, bitrate_string_conformed.lower(), flags=re.I)
        if match:
            match_groupdict = match.groupdict()
            modifier = 0
            if isinstance(match_groupdict['unit'], string_types):
                bitrate_unit = match_groupdict['unit'].lower()
                if bitrate_unit == 'kbps':
                    modifier = 1024
                elif bitrate_unit == 'mbps':
                    modifier = 1024 * 1024
                elif bitrate_unit == 'gbps':
                    modifier = 1024 * 1024 * 1024
            bitrate = float(match_groupdict['bitrate']) * modifier
    return bitrate

def get_higest_number_in_string(string):
    highest_digit = None
    if isinstance(string, string_types):
        for c in string:
            if c.isdigit() is True:
                c_int = int(c)
                if highest_digit is None:
                    highest_digit = c_int
                elif c_int > highest_digit:
                    highest_digit = c_int
    return highest_digit

def frame_rate_text_to_float(string):
    frame_rate = None
    if isinstance(string, string_types):
        frame_rate_pattern = r'''(?P<frame_rate>\d+(?:\.\d+))'''
        match = re.search(frame_rate_pattern, string)
        if match:
            return float(match.groupdict()['frame_rate'])
    return frame_rate

def display_aspect_ratio_from_text(string):
    display_aspect_ratio = None
    if isinstance(string, string_types):
        frame_rate_pattern = r'''(?P<display_aspect_ratio>[.\d]+:\d+)'''
        match = re.search(frame_rate_pattern, string)
        if match:
            return match.groupdict()['display_aspect_ratio']
    return display_aspect_ratio