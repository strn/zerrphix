# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

import logging

from sqlalchemy import orm
from tempfile import NamedTemporaryFile
from zerrphix.db.tables import TABLES
from zerrphix.util.filesystem import make_dir, smbfs
from pymediainfo import MediaInfo
from zerrphix.util.text import date_time
from zerrphix.db import commit
import threading
from functools import wraps
import time
log = logging.getLogger(__name__)

import ctypes
import errno
from ctypes.util import find_library
from functools import partial

CLOCK_PROCESS_CPUTIME_ID = 2  # time.h
CLOCK_MONOTONIC_RAW = 4

clockid_t = ctypes.c_int
time_t = ctypes.c_long


class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', time_t),         # seconds
        ('tv_nsec', ctypes.c_long)  # nanoseconds
    ]
_clock_gettime = ctypes.CDLL(find_library('rt'), use_errno=True).clock_gettime
_clock_gettime.argtypes = [clockid_t, ctypes.POINTER(timespec)]


def clock_gettime(clk_id):
    tp = timespec()
    if _clock_gettime(clk_id, ctypes.byref(tp)) < 0:
        err = ctypes.get_errno()
        msg = errno.errorcode[err]
        if err == errno.EINVAL:
            msg += (" The clk_id specified is not supported on this system"
                    " clk_id=%r") % (clk_id,)
        raise OSError(err, msg)
    return tp.tv_sec + tp.tv_nsec * 1e-9

try:
    from time import perf_counter, process_time
except ImportError:  # Python <3.3
    perf_counter = partial(clock_gettime, CLOCK_MONOTONIC_RAW)
    perf_counter.__name__ = 'perf_counter'
    process_time = partial(clock_gettime, CLOCK_PROCESS_CPUTIME_ID)
    process_time.__name__ = 'process_time'


# https://gist.github.com/gregburek/1441055
def rate_limited(max_per_interval, interval):
    """Rate-limits the decorated function locally, for one process."""
    lock = threading.Lock()
    min_interval = float(interval) / max_per_interval

    def decorate(func):
        last_time_called = [perf_counter()]

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            try:
                elapsed = perf_counter() - last_time_called[0]
                left_to_wait = min_interval - elapsed
                if left_to_wait > 0:
                    time.sleep(left_to_wait)

                return func(*args, **kwargs)
            finally:
                last_time_called[0] = perf_counter()
                lock.release()

        return rate_limited_function

    return decorate

#@RateLimited(2)  # 2 per second at most
#def PrintNumber(num):
#    print num


def is_digit(_input, greather_than=None):
    if isinstance(_input, basestring):
        try:
            _int = int(_input)
        except TypeError as e:
            return False
        except ValueError as e:
            return False
        else:
            if isinstance(greather_than, int):
                if _int > greather_than:
                    return True
            else:
                return True
    elif isinstance(_input, int):
        if isinstance(greather_than, int):
            if _input > greather_than:
                return True
        else:
            return True
    return False


def list1_not_in_list2(list1, list2):
    for val in list1:
        if val not in list2:
            return True
    return False

def smbfs_mediainfo(path, smbcon, size=1000000):
    file_metadata = NamedTemporaryFile()
    file_metadata_path = file_metadata.name
    log.debug('file_metadata_path %s', file_metadata_path)
    # raise SystemExit
    try:
        file_attributes, bytes_written = smbcon.retrieveFileFromOffset(path, file_metadata, offset=0,
                                                                   max_length=size, timeout=10)
    except TypeError:
        log.warning('TypeError Occured. Does the path %s exist?', path)
        media_info = None
    else:
        log.debug('file_attributes %s, bytes_written %s', file_attributes, bytes_written)
        media_info = MediaInfo.parse(file_metadata_path)
    log.debug('file_metadata type %s', type(file_metadata))
    # file_metadata.seek(0)
    file_metadata.close()
    ## some files need more data to be read before all track data is discovered
    #if hasattr(media_info, 'tracks'):
    #    if len(media_info.tracks) <= 1:
    #        file_metadata = NamedTemporaryFile()
    #        file_metadata_path = file_metadata.name
    #        log.debug('file_metadata_path %s', file_metadata_path)
    #        # raise SystemExit
    #        file_attributes, bytes_written = smbcon.retrieveFileFromOffset(path, file_metadata, offset=0,
    #                                                                       max_length=50000, timeout=10)
    #        log.debug('file_attributes %s, bytes_written %s', file_attributes, bytes_written)
    #        log.debug('file_metadata type %s', type(file_metadata))
    #        # file_metadata.seek(0)
    #        media_info = MediaInfo.parse(file_metadata_path)
    #        file_metadata.close()
    return media_info

def time_run_between(time_a_true, time_b_true, not_run=False):

    # time_pattern = r"^[0-23]{2}[0-59]{2}|2400$"

    if time.strptime(time_a_true, '%H%M') and time.strptime(time_b_true, '%H%M'):

        if time_a_true == "2400":
            time_a_true = "0000"

        if time_b_true == "2400":
            time_b_true = "0000"

        time_a = int(time_a_true)
        time_b = int(time_b_true)

        current_time = int(time.strftime("%H%M", time.localtime(time.time())))

        if time_b > time_a:
            if current_time >= time_a and current_time <= time_b:
                if not not_run:
                    return True
            else:
                if not_run:
                    return True
        else:
            if current_time >= time_a or current_time <= time_b:
                if not not_run:
                    return True
            else:
                if not_run:
                    return True
    else:
        log.error('''Cannot convert time_a_true %s to time.strptime(time_a_true, '%H%M')''' 
                  ''' and or convert time_b_true %s to time.strptime(time_b_true, '%H%M')''')
    return False