from __future__ import unicode_literals, division, absolute_import, print_function
import logging
import logging.handlers
import os.path
import tempfile
import gzip
import shutil
import threading
import warnings
import collections
import sys
import codecs
from zerrphix._version import __version__
from zerrphix.util.text import io_encoding
import time
# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15
# environment variables to modify rotating log parameters from defaults of 1 MB and 9 files
ENV_MAXBYTES = 'FLEXGET_LOG_MAXBYTES'
ENV_MAXCOUNT = 'FLEXGET_LOG_MAXCOUNT'

# Stores `task`, logging `session_id`, and redirected `output` stream in a thread local context
#local_context = threading.local()


def get_level_no(level):
    if not isinstance(level, int):
        # Cannot use getLevelName here as in 3.4.0 it returns a string.
        level = level.upper()
        if level == 'TRACE':
            level = TRACE
        elif level == 'VERBOSE':
            level = VERBOSE
        else:
            level = getattr(logging, level)

    return level
# import logging.config
# http://www.blog.pythonlibrary.org/2012/08/02/python-101-an-intro-to-logging/
# http://stackoverflow.com/questions/8467978/python-want-logging-with-log-rotation-and-compression
_logging_configured = False
_buff_handler = None
_logging_started = False
_fh = None
_ch = None

class RollingBuffer(collections.deque):
    """File-like that keeps a certain number of lines of text in memory."""

    def write(self, line):
        self.append(line)

class ZerrphixLogger(logging.Logger):
    """Custom logger that adds trace and verbose logging methods, and contextual information to log records."""

    #def __init__(self, name):
    #    super(ZerrphixLogger, self).__init__(name)
    def trace(self, msg, *args, **kwargs):
        """Log at TRACE level (more detailed than DEBUG)."""
        self.log(TRACE, msg, *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """Log at VERBOSE level """
        self.log(VERBOSE, msg, *args, **kwargs)

# Modified from flexget https://github.com/Flexget
# Stores the last 50 debug messages
debug_buffer = RollingBuffer(maxlen=50)

# https://github.com/rkreddy46/python_code_reference/blob/master/compressed_log_rotator.py
class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d.gz" % (self.baseFilename, i)
                dfn = "%s.%d.gz" % (self.baseFilename, i + 1)
                if os.path.exists(sfn):
                    # print "%s -> %s" % (sfn, dfn)
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1.gz"
            if os.path.exists(dfn):
                os.remove(dfn)
            # These two lines below are the only new lines. I commented out the os.rename(self.baseFilename, dfn) and
            #  replaced it with these two lines.
            with open(self.baseFilename, 'rb') as f_in, gzip.open(dfn, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            # os.rename(self.baseFilename, dfn)
            # print "%s -> %s" % (self.baseFilename, dfn)
        self.mode = 'w'
        self.stream = self._open()

# Modified from flexget https://github.com/Flexget
class ZerrphixFormatter(logging.Formatter):
    """Custom formatter that can handle both regular log records and those created by FlexGetLogger"""
    # figure out what the -int does
    # zerrphix_fmt = '%(asctime)-15s %(levelname)-8s %(name)-13s %(task)-15s %(message)s'
    zerrphix_fmt = '%(asctime)s [%(threadName)s] %(levelname)8s:%(name)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s'

    def __init__(self):
        logging.Formatter.__init__(self, self.zerrphix_fmt, '%Y-%m-%d %H:%M:%S')

    #def format(self, record):
    #    if not hasattr(record, 'task'):
    #        record.task = ''
    #    return logging.Formatter.format(self, record)

def initialize(unit_test=False):
    """Prepare logging.
    """
    global _logging_configured, _logging_started, _buff_handler

    if _logging_configured:
        return

    if 'dev' in __version__:
        # warnings.filterwarnings('always', category=DeprecationWarning, module='zerrphix.*')
        pass
    warnings.simplefilter('once', append=True)
    logging.addLevelName(TRACE, 'TRACE')
    logging.addLevelName(VERBOSE, 'VERBOSE')
    _logging_configured = True

    # with unit test we want pytest to add the handlers
    if unit_test:
        _logging_started = True
        return

    # Store any log messages in a buffer until we `start` function is run
    logger = logging.getLogger()
    _buff_handler = logging.handlers.BufferingHandler(1000 * 1000)
    logger.addHandler(_buff_handler)
    logger.setLevel(logging.NOTSET)

    # Add a handler that sores the last 50 debug lines to `debug_buffer` for use in crash reports
    crash_handler = logging.StreamHandler(debug_buffer)
    crash_handler.setLevel(logging.DEBUG)
    crash_handler.setFormatter(ZerrphixFormatter())
    logger.addHandler(crash_handler)

def start(file_path=None, file_level=logging.INFO, console_level=logging.INFO,
          to_console=True, to_file=True, maxBytes=100000, backupCount=3,
          compression=0):
    """After initialization, start file logging.
    """
    global _logging_started

    assert _logging_configured
    if _logging_started:
        return

    # root logger
    logger = logging.getLogger()
    #level = get_level_no(level)
    logger.setLevel(TRACE)
    #logger.setLevel(logging.DEBUG)

    formatter = ZerrphixFormatter()
    #formatter = logging.Formatter(
    #    '%(asctime)s [%(threadName)s] %(levelname)8s:%(name)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s')
    #
    if to_file:
        #file_handler = logging.handlers.RotatingFileHandler(filename,
        #                                                    maxBytes=int(os.environ.get(ENV_MAXBYTES, 1000 * 1024)),
        #                                                    backupCount=int(os.environ.get(ENV_MAXCOUNT, 9)))
        if compression == 1:
            file_handler = CompressedRotatingFileHandler(file_path, mode='a',
                                          maxBytes=maxBytes,
                                          backupCount=backupCount,
                                        # allow this to be configured ??
                                          encoding='utf-8')
        else:
            file_handler = logging.handlers.RotatingFileHandler(file_path, mode='a',
                                          maxBytes=maxBytes,
                                          backupCount=backupCount,
                                        # allow this to be configured ??
                                          encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(get_level_no(file_level))
        logger.addHandler(file_handler)
        #LogfilePath = os.path.join(tempfile.gettempdir(), 'zerrphixwwww.log')
        #_fh = logging.handlers.RotatingFileHandler(LogfilePath, mode='a',
        #_fh = CompressedRotatingFileHandler(LogfilePath, mode='a',
        #                                           maxBytes=50000000,
        #                                           backupCount=15,
        #                                           encoding='utf-8')

        #_fh.setFormatter(formatter)
        #_fh.setLevel(logging.DEBUG)

        #logger.addHandler(_fh)
    # without --cron we log to console
    if to_console:
        # Make sure we don't send any characters that the current terminal doesn't support printing
        stdout = sys.stdout
        if hasattr(stdout, 'buffer'):
            # On python 3, we need to get the buffer directly to support writing bytes
            stdout = stdout.buffer
        safe_stdout = codecs.getwriter(io_encoding)(stdout, 'replace')
        console_handler = logging.StreamHandler(safe_stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(get_level_no(console_level))
        logger.addHandler(console_handler)

        #_ch = logging.StreamHandler()
        #_ch.setLevel(logging.ERROR)
        #_ch.setFormatter(formatter)

    # flush what we have stored from the plugin initialization
    logger.removeHandler(_buff_handler)
    #print(logger.handlers)
    #for sss in logger.handlers:
    #    print(sss)
    #    print(sss.level)
    if _buff_handler:
        for record in _buff_handler.buffer:
            if logger.isEnabledFor(record.levelno):
     #           print(record)
     #           print(dir(record))
                logger.handle(record)
        _buff_handler.flush()
    _logging_started = True
    logger.info('Logger setup')
    #print(logger.handlers)
    logger.info('Listing loggers')
    for handler in logger.handlers:
        logger.info('logger: %s' % handler)

    logging.getLogger("requests").setLevel(get_level_no(file_level))
    logging.getLogger("urllib3").setLevel(get_level_no(file_level))
    logging.getLogger('sqlalchemy.engine').setLevel(get_level_no(file_level))
    #    print(dir(sss))
    #    if hasattr(sss, 'baseFilename'):
    #        print(sss.baseFilename)
            #sss.shouldRollover()
    #time.sleep(3000)


# file_handler = logging.handlers.RotatingFileHandler('/tmp/zptest.log', maxBytes=1000 * 1024, backupCount=9)
# file_handler.setFormatter(formatter)
# file_handler.setLevel(level)
# logger.addHandler(file_handler)

# Set our custom logger class as default
#print(logging.getLoggerClass())
#print(dir(logging.getLoggerClass()))
# this module has to be imported on the init of the progam to work
logging.setLoggerClass(ZerrphixLogger)
#logging.addLevelName(TRACE, 'TRACE')
#print(dir(logging.getLoggerClass()))