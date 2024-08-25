from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import socket
import time
import urllib2

log = logging.getLogger(__name__)


def download(url, download_path, retry_count=2):
    log.debug('trying to download url: {0} to download_path: {1}'.format(
        url,
        download_path))
    get_image_failed_count = 0
    while get_image_failed_count <= retry_count:
        log.debug('download: {0} attempt {1}'.format(
            url,
            get_image_failed_count + 1))
        try:
            u = urllib2.urlopen(url)
            log.debug('download: {0} response code: {1}'.format(
                url,
                u.code))
            if u.code == 200:
                # print(u.headers["content-type"])
                log.debug('download: {0} headers: {1}'.format(
                    url,
                    u.headers))
                log.debug('download: {0} content-type: {1}'.format(
                    url,
                    u.headers["content-type"]))
                log.debug('download: {0} opening: {1} for writing'.format(
                    url,
                    download_path))
                f = open(download_path, 'wb')
                meta = u.info()
                file_size = int(meta.getheaders("Content-Length")[0])
                log.debug('download: {0} starting download'.format(
                    url,
                    u.code))
                # print("Downloading: %s Bytes: %s" % (download_path, file_size))
                file_size_dl = 0
                block_sz = 4096
                log.debug('')
                while True:
                    buffer = u.read(block_sz)
                    if not buffer:
                        break
                    file_size_dl += len(buffer)
                    f.write(buffer)
                    # status = ur"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                    # status = status + chr(8)*(len(status)+1)
                # TODO: log how long it takes to download
                # log.debug(status)
                f.close()
                log.debug('download: {0} closed: {1}'.format(
                    url,
                    download_path))
                return True
            else:
                log.debug('download: {0} response code: {1} not 200'.format(
                    url,
                    u.code))
        except urllib2.URLError as e:
            log.debug('download: {0} urllib2.URLError: {1}'.format(
                url,
                e))
        except urllib2.HTTPError as e:
            log.debug('download: {0} urllib2.HTTPError: {1}'.format(
                url,
                e))
        except socket.error as e:
            log.debug('download: {0} socket.error: {1}'.format(
                url,
                e))
        get_image_failed_count += 1
        time.sleep(1)

    log.debug('download: {0} exceded number off allowed retry_count {1}'.format(
        url,
        retry_count))
    return False
