from __future__ import unicode_literals, division, absolute_import, print_function
from smb.SMBConnection import SMBConnection
import logging
import logging.handlers
import sys
import codecs
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

class ZerrphixFormatter(logging.Formatter):
    """Custom formatter that can handle both regular log records and those created by FlexGetLogger"""
    # figure out what the -int does
    # zerrphix_fmt = '%(asctime)-15s %(levelname)-8s %(name)-13s %(task)-15s %(message)s'
    zerrphix_fmt = '%(asctime)s [%(threadName)s] %(levelname)8s:%(name)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s'

    def __init__(self):
        logging.Formatter.__init__(self, self.zerrphix_fmt, '%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stdout = sys.stdout
    formatter = ZerrphixFormatter()
    if hasattr(stdout, 'buffer'):
        # On python 3, we need to get the buffer directly to support writing bytes
        stdout = stdout.buffer
    safe_stdout = codecs.getwriter(io_encoding)(stdout, 'replace')
    console_handler = logging.StreamHandler(safe_stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.debug('asdas')
    conn = SMBConnection('media'.encode('ascii', 'ignore'),
                  'aidem99'.encode('ascii', 'ignore'),
                  'zptest'.encode('ascii', 'ignore'),
                  'HA555RPY'.encode('ascii', 'ignore'),
                  domain=''.encode('ascii', 'ignore'),)
    #conn.connect('192.168.0.72'.encode('ascii', 'ignore'))
    conn.connect('10.0.10.2'.encode('ascii', 'ignore'))
    for share in conn.listShares():
        logger.debug(share.name)
    logger.debug(conn.listShares())
    conn.close()