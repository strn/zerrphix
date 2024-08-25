# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import netifaces
import IPy
import socket
import struct

SELF_ASSIGNED_RANGE_START = 2851995648
SELF_ASSIGNED_RANGE_END = 2852061183

def ip2long(ip):
    """
    Convert an IP string to long
    """
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

def private_listen_address_list():
    return_list = []
    for interface in netifaces.interfaces():
        interface_addresses = netifaces.ifaddresses(interface)
        #print(interface)
        #print(interface_addresses)
        #print(interface_addresses)
        for af_net_type in interface_addresses:
            if af_net_type == netifaces.AF_INET:
                for address in interface_addresses[af_net_type]:
                    if 'addr' in address:
                        #print(address['addr'])
                        if IPy.IP(address['addr']).iptype() == 'PRIVATE':
                            address_as_int = ip2long(address['addr'])
                            if address_as_int not in range(SELF_ASSIGNED_RANGE_START, SELF_ASSIGNED_RANGE_END):
                                #print(address['addr'])
                                if address['addr'] != '0.0.0.0' and not address['addr'].startswith('127.0.0'):
                                    if address['addr'] not in return_list:
                                        return_list.append(address['addr'])
    return return_list