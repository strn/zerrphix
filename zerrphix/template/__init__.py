# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

from zerrphix.util.text import string_to_list


def tempalte_icon_sub_type_list_convert(template_dict):
    # TODO: validate the list
    icon_sub_type_require_list = string_to_list(template_dict['template']['@icon_sub_type_list'], ',')
    icon_sub_type_require_list = [int(i) for i in icon_sub_type_require_list]
    # print(icon_sub_type_require_list)
    # print(type(template_dict['template']['item']))
    item_list_position = 0
    # print(type(template_dict['template']['item']))
    if isinstance(template_dict['template']['item'], list):
        for item in template_dict['template']['item']:
            # print(item)
            # for item_option in item:
            # print(item.keys())
            for item_type in item:
                if '@icon_sub_type_list' in item[item_type].keys():
                    template_dict['template']['item'][item_list_position][item_type]['@icon_sub_type_list'] = \
                        [int(i) for i in string_to_list(item[item_type]['@icon_sub_type_list'], ',')]
                    # print(template_dict['template']['item'][item_list_position][item_type]['@icon_sub_type_list'])
                    # print(item[item_type]['@icon_sub_type_list'])
            item_list_position += 1
    # print(template_dict['template']['item'])
    # raise SystemExit
    else:
        raise TypeError('''template_dict['template']['item'] is not dict or list but %s''' % type(
            template_dict['template']['item']))

    return icon_sub_type_require_list, template_dict
