# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function
from zerrphix.util.extra import AESCipher
from zerrphix.util.extra import x, z
#from zerrphix.util.extra import decrypt, encrypt
import base64
import uuid


if __name__ == '__main__':

    key = str(uuid.uuid4())
    print('key %s' % key)
    for password in ['aidem99', 'media99']:
        print('password %s' % password)
        key_obs = x(key)
        print('key_obs %s' % key_obs)
        key_obs_dec = z(key_obs)
        print('key_obs_dec %s' % key_obs_dec)
        encrypted_password = AESCipher(z(key_obs)).v(password)
        print('encrypted_password %s' % encrypted_password)
        decrypted_password = AESCipher(z(key_obs)).q(encrypted_password)
        print('decrypted_password %s' % decrypted_password)
        #print('----')
        #key = 'fe7019dc-7a26-49a6-a20d-abcd3ff3d9ac'
        #print('key %s' % key)
        #key_obs = x(key)
        #print('key_obs %s' % key_obs)
        #print('key_obs %s' % 'dfccdfcfdf9ddf9adf9bdf93dfcedfc9df87df9ddfcbdf98df9cdf87df9edf93dfcbdf9cdf87dfcbdf98df9adfcedf87dfcbdfc8dfc9dfcedf99dfccdfccdf99dfcedf93dfcbdfc9')
        #key_obs_dec = z(key_obs)
        #print('key_obs_dec %s' % key_obs_dec)
        #print('key_obs_dec %s' % z('dfccdfcfdf9ddf9adf9bdf93dfcedfc9df87df9ddfcbdf98df9cdf87df9edf93dfcbdf9cdf87dfcbdf98df9adfcedf87dfcbdfc8dfc9dfcedf99dfccdfccdf99dfcedf93dfcbdfc9'))
        #encrypted_password = AESCipher(z(key_obs)).v(password)
        #print('encrypted_password %s' % encrypted_password)
        #encrypted_password = AESCipher(z('dfccdfcfdf9ddf9adf9bdf93dfcedfc9df87df9ddfcbdf98df9cdf87df9edf93dfcbdf9cdf87dfcbdf98df9adfcedf87dfcbdfc8dfc9dfcedf99dfccdfccdf99dfcedf93dfcbdfc9')).v(password)
        #print('encrypted_password man %s' % encrypted_password)
        #decrypted_password = AESCipher(z(key_obs)).q(encrypted_password)
        #print('decrypted_password %s' % decrypted_password)
        #decrypted_password = AESCipher(z('dfccdfcfdf9ddf9adf9bdf93dfcedfc9df87df9ddfcbdf98df9cdf87df9edf93dfcbdf9cdf87dfcbdf98df9adfcedf87dfcbdfc8dfc9dfcedf99dfccdfccdf99dfcedf93dfcbdfc9')).q('2xZuFkBrA+FLb+GQhO0NldoiX3GOltvENuCUKGbROJtJrsaviZjEyNiCwZNpFArV')
        #print('decrypted_password man %s' % decrypted_password)
        #print('----')
        #decrypted_password = AESCipher(z('df99dfcfdf9cdf93dfcedf93dfc8df92df87dfccdfcfdfcbdfc9df87df9edf9fdfccdfcbdf87df92df98df9adf99df87df9cdf9edf93df98df9fdf9edf93df9ddfc8dfccdf9adf9c')).q(encrypted_password)
        #print('decrypted_password %s' % decrypted_password)
        #encrypted_password = AESCipher(z('df99dfcfdf9cdf93dfcedf93dfc8df92df87dfccdfcfdfcbdfc9df87df9edf9fdfccdfcbdf87df92df98df9adf99df87df9cdf9edf93df98df9fdf9edf93df9ddfc8dfccdf9adf9c')).v(password)
        #print('encrypted_password %s' % encrypted_password)
        #decrypted_password = AESCipher(z('df99dfcfdf9cdf93dfcedf93dfc8df92df87dfccdfcfdfcbdfc9df87df9edf9fdfccdfcbdf87df92df98df9adf99df87df9cdf9edf93df98df9fdf9edf93df9ddfc8dfccdf9adf9c')).q(encrypted_password)
        #print('decrypted_password %s' % decrypted_password)
        #decrypted_password = AESCipher(z('df99dfcfdf9cdf93dfcedf93dfc8df92df87dfccdfcfdfcbdfc9df87df9edf9fdfccdfcbdf87df92df98df9adf99df87df9cdf9edf93df98df9fdf9edf93df9ddfc8dfccdf9adf9c')).q('soVfXXwFmIWUyWDvSc/LUcTRpz0ViMwVBnTRRpfzM+ig3GY1I83i6L0m35RbApv2')
        #print('decrypted_password %s' % decrypted_password)