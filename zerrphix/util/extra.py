#!/usr/bin/env python
#  -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function
"""
   The MIT License (MIT)

   Copyright (C) 2016 Andris Raugulis (moo@arthepsy.eu)

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in
   all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   THE SOFTWARE.
"""
import sys, itertools, base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

WEBSTORM_KEY = b'\xdf\xaa'
WEBSTORM_ENC = 'utf-16-be'

def uord(v):
    return ord(v) if sys.version_info[0] == 2 else v


def str2hex(s):
    return base64.b16encode(s).lower()


def hex2str(s):
    return base64.b16decode(s.upper())


def xor_str(s, k):
    return bytearray(uord(a) ^ uord(b) for a, b in zip(s, itertools.cycle(k)))


def x(s):
    x = xor_str(s.encode(WEBSTORM_ENC), WEBSTORM_KEY)
    x = str2hex(x).decode('ascii')
    return x


def z(s):
    x = xor_str(hex2str(s), WEBSTORM_KEY)
    x = x.decode(WEBSTORM_ENC)
    return x

class AESCipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def v(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def q(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
