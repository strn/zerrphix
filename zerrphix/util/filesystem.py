from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os
import re
import socket
import sys
import time
import subprocess

from smb import base as smb_base
from smb import smb_structs
from smb.SMBConnection import SMBConnection

from six import string_types
from zerrphix.constants import pattern_diskfilefolder, diskfilefolder_types_dict, min_film_filsize
from io import BytesIO
import traceback

log = logging.getLogger(__name__)


class SMBConnectionAssertionError(Exception):
    def __init__(self, message):
        super(SMBConnectionAssertionError, self).__init__(message)


class smbfs(object):
    # TODO: Case insensitive
    def __init__(self, connection_dict, idle_limit=60):
        self.smbcon = False
        self.first_conn_use = 0
        self.last_conn_use = 0
        self.idle_limit = idle_limit
        self.connection_dict = connection_dict

    def initSMBCon(self):
        # TODO: log input
        if 'domain' in self.connection_dict.keys():
            domain = self.connection_dict['domain'].encode('ascii', 'ignore')
        else:
            domain = ''

        return SMBConnection(self.connection_dict['username'].encode('ascii', 'ignore'),
                             self.connection_dict['password'].encode('ascii', 'ignore'),
                             self.connection_dict['my_name'].encode('ascii', 'ignore'),
                             self.connection_dict['remote_name'].encode('ascii', 'ignore'),
                             domain=domain)

    def close(self):
        if hasattr(self.smbcon, 'close'):
            self.smbcon.close()
            # todo monitor how mayne times connections are open and closed
            log.info('closed smb connection')
        return True

    def retrieveFileFromOffset(self, path, file_obj, offset=0, max_length=1, timeout=30):
        if self.connect():
            try:
                retrieved_file = self.smbcon.retrieveFileFromOffset(self.connection_dict['share'], path,
                                                                    file_obj, offset, max_length, timeout)
            except smb_structs.OperationFailure as e:
                log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                            type(str(e)))
                return None
            except smb_base.SMBTimeout as e:
                log.warning('Exception: smb_base.SMBTimeout trying to get file file_attributes for share %s, path %s',
                            self.connection_dict['share'], path)
                return None
            else:
                return retrieved_file[0], retrieved_file[1]

    def connect(self, retry_count=2):
        epoch_now = int(time.time())
        if epoch_now - self.last_conn_use >= self.idle_limit or self.last_conn_use == 0 or (
            self.first_conn_use + 100 <= epoch_now):
            if hasattr(self.smbcon, 'close'):
                self.smbcon.close()
                log.warning('closed smb connection')

            # todo monitor how mayne times connections are open and closed
            log.info(('CREATING NEW CON epoch_now: {0} - self.last_conn_use: {1} is {4} >= self.idle_limit: {2}'
                      ' or self.last_conn_use: {3} = 0.').format(epoch_now,
                                                                 self.last_conn_use,
                                                                 self.idle_limit,
                                                                 self.last_conn_use,
                                                                 epoch_now - self.last_conn_use))
            # traceback.print_stack()
            self.smbcon = self.initSMBCon()
            connect_attempt_count = 0
            # while connect_attempt_count <= retry_count:
            # connect_attempt_count += 1
            try:
                assert self.smbcon.connect(self.connection_dict['host'].encode('ascii', 'ignore'),
                                           self.connection_dict['port'])
            except socket.error as e:
                exception_message = ('cannot connect to {0} on port {1}.\n'
                                     'Please check the ip/hostname and port are correct.\n'
                                     '{2}').format(self.connection_dict['host'],
                                                   self.connection_dict['port'],
                                                   e)
                log.exception(exception_message)
                # if retry_count == connect_attempt_count:
                raise socket.error(exception_message)
            except smb_base.NotConnectedError:
                exception_message = ('NotConnectedError cannot connect to %s, remote_name %s on port %s.\n'
                                     'Please check the connection details (ip and port should be valid, but no neceasarily the'
                                     'correct ones for the host, as'
                                     ' socket.error shuld be thrown if host is not conteactable).\n'
                                     'Share %s, username %s.' % (self.connection_dict['host'],
                                                                 self.connection_dict['remote_name'],
                                                                 self.connection_dict['port'],
                                                                 self.connection_dict['share'],
                                                                 self.connection_dict['username']
                                                                 ))
                log.exception(exception_message)
                raise smb_base.NotConnectedError(exception_message)
            except smb_base.NotReadyError as e:
                exception_message = ('NotReadyError cannot connect to %s, remote_name %s on port %s.\n'
                                     '%s.\n'
                                     'Please check the connection details (ip and port should be valid, but no neceasarily the'
                                     'correct ones for the host, as'
                                     ' socket.error shuld be thrown if host is not conteactable).\n'
                                     'Share %s, username %s.' % (self.connection_dict['host'],
                                                                 self.connection_dict['remote_name'],
                                                                 self.connection_dict['port'],
                                                                 str(e),
                                                                 self.connection_dict['share'],
                                                                 self.connection_dict['username']
                                                                 ))
                log.exception(exception_message)
                raise smb_base.NotReadyError(exception_message)
            except smb_base.SMBTimeout as e:
                exception_message = ('SMBTimeout to {0} on port {1}.\n'
                                     'Please check the ip/hostname/network for issues.\n'
                                     '{2}').format(self.connection_dict['host'],
                                                   self.connection_dict['port'],
                                                   e)
                log.exception(exception_message)
                raise smb_base.SMBTimeout(exception_message)
            except AssertionError:
                log.exception('AssertionError cannot connect to %s, remote_name %s on port %s.\n'
                              'Please check the connection details (ip and port should be valid, but no neceasarily the'
                              'correct ones for the host, as'
                              ' socket.error shuld be thrown if host is not conteactable).\n'
                              'Share %s, username %s.' % (self.connection_dict['host'],
                                                          self.connection_dict['remote_name'],
                                                          self.connection_dict['port'],
                                                          self.connection_dict['share'],
                                                          self.connection_dict['username']
                                                          ))
                # if retry_count == connect_attempt_count:
                raise SMBConnectionAssertionError('SMBConnectionAssertionError cannot connect to %s, '
                                                  'remote_name %s on port %s.\n'
                                                  'Please check the connection details (ip and port should be valid, but no neceasarily the'
                                                  'correct ones for the host, as'
                                                  ' socket.error shuld be thrown if host is not conteactable).\n'
                                                  'Share %s, username %s.' % (self.connection_dict['host'],
                                                                              self.connection_dict['remote_name'],
                                                                              self.connection_dict['port'],
                                                                              self.connection_dict['share'],
                                                                              self.connection_dict['username']
                                                                              ))
            else:
                # log.error(self.connection_dict)
                # log.error(self.smbcon.username)
                # log.error(self.smbcon.password)
                # log.error(self.smbcon.domain)
                # log.error(self.smbcon.my_name)
                # log.error(self.smbcon.remote_name)
                # log.error(self.connection_dict['host'])
                self.last_conn_use = int(time.time())
                self.first_conn_use = int(time.time())
                return True
        else:
            log.debug(('epoch_now: {0} - self.last_conn_use: {1} is not >= self.idle_limit: {2}'
                       ' and self.last_conn_use: {3} != 0.').format(epoch_now,
                                                                    self.last_conn_use,
                                                                    self.idle_limit,
                                                                    self.last_conn_use))
            # print('allready connected')
            self.last_conn_use = int(time.time())
            return True

    def isdir(self, path):
        if self.connect():
            try:
                file_attributes = self.smbcon.getAttributes(self.connection_dict['share'], path)
            except smb_structs.OperationFailure as e:
                log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                            type(str(e)))
                return False
            except smb_base.SMBTimeout as e:
                log.warning('Exception: smb_base.SMBTimeout trying to get file file_attributes for share %s, path %s',
                            self.connection_dict['share'], path)
                return False
            else:
                if file_attributes.isDirectory:
                    log.debug(
                        '''{0} in self.connection_dict['share']: {1} on self.connection_dict['host']: {2} is a directory'''.format(
                            path,
                            self.connection_dict['share'],
                            self.connection_dict['host']))
                    return True
                else:
                    log.debug(
                        '''{0} in self.connection_dict['share']: {1} on self.connection_dict['host']: {2} is not a directory'''.format(
                            path,
                            self.connection_dict['share'],
                            self.connection_dict['host']))
                    return False

    def isfile(self, path):
        if self.connect():
            try:
                file_attributes = self.smbcon.getAttributes(self.connection_dict['share'], path)
            except smb_structs.OperationFailure as e:
                log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                            type(str(e)))
                return False
            except smb_base.SMBTimeout as e:
                log.warning('Exception: smb_base.SMBTimeout trying to get file file_attributes for share %s, path %s',
                            self.connection_dict['share'], path)
                return False
            else:
                if file_attributes.isDirectory:
                    log.debug(
                        '''{0} in self.connection_dict['share']: {1} on self.connection_dict['host']: {2} is not a file'''.format(
                            path,
                            self.connection_dict['share'],
                            self.connection_dict['host']))
                    return False
                else:
                    log.debug(
                        '''{0} in self.connection_dict['share']: {1} on self.connection_dict['host']: {2} is a file'''.format(
                            path,
                            self.connection_dict['share'],
                            self.connection_dict['host']))
                    return True

    def listdir(self, path, dir_only=False, file_only=False):
        filefolder_list = []
        if self.connect():
            try:
                SharedFiles = self.smbcon.listPath(self.connection_dict['share'], path)
            except smb_structs.OperationFailure as e:
                log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                            type(str(e)))
                return False
            except smb_base.SMBTimeout as e:
                log.warning('Exception: smb_base.SMBTimeout trying to list path for share %s, path %s',
                            self.connection_dict['share'], path)
                return False
            else:
                for SharedFile in SharedFiles:
                    if SharedFile.filename != '.' and SharedFile.filename != '..':
                        if dir_only == True:
                            if SharedFile.isDirectory:
                                filefolder_list.append(SharedFile.filename)
                        elif file_only == True:
                            if not SharedFile.isDirectory:
                                filefolder_list.append(SharedFile.filename)
                        else:
                            filefolder_list.append(SharedFile.filename)
        return filefolder_list

    def getmtime(self, path):
        try:
            file_attributes = self.smbcon.getAttributes(self.connection_dict['share'], path)
        except smb_structs.OperationFailure as e:
            log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                        type(str(e)))
            return None
        except smb_base.SMBTimeout as e:
            log.warning('Exception: smb_base.SMBTimeout trying to get file file_attributes for share %s, path %s',
                        self.connection_dict['share'], path)
            return None
        else:
            # log.debug('file_attributes.last_attr_change_time %s', file_attributes.last_attr_change_time)
            # log.debug('file_attributes.last_access_time %s', file_attributes.last_attr_change_time)
            # log.debug('file_attributes.last_write_time %s', file_attributes.last_attr_change_time)
            # raise SystemExit
            return file_attributes.last_attr_change_time

    def getsize(self, path):
        if self.isfile(path):
            try:
                file_attributes = self.smbcon.getAttributes(self.connection_dict['share'], path)
            except smb_structs.OperationFailure as e:
                log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                            type(str(e)))
                return None
            except smb_base.SMBTimeout as e:
                log.warning('Exception: smb_base.SMBTimeout trying to get file file_attributes for share %s, path %s',
                            self.connection_dict['share'], path)
                return None
            else:
                return file_attributes.file_size
        else:
            return None

    def mkdir(self, path):
        if self.connect():
            if self.isdir(path) == False:
                try:
                    self.smbcon.createDirectory(self.connection_dict['share'], path)
                except smb_structs.OperationFailure:
                    if self.isfile(path) == True:
                        log.warning(
                            '''{0} in share: {1}: is a file. Cannot make a directory with same name.'''.format(
                                path,
                                self.connection_dict['share']))
                    else:
                        log.critical(
                            '''cannot make dir {0} in share: {1} on self.connection_dict['host']: {2}'''.format(
                                path,
                                self.connection_dict['share'],
                                self.connection_dict['host']))

                    return False
                except smb_base.SMBTimeout as e:
                    log.warning('Exception: smb_base.SMBTimeout trying create directory for share %s, path %s',
                                self.connection_dict['share'], path)
                    return False
                else:
                    log.debug(
                        '''{0} in self.connection_dict['share']: {1} on self.connection_dict['host']: {2} is a dir'''.format(
                            path,
                            self.connection_dict['share'],
                            self.connection_dict['host']))
                    return True
            else:
                log.debug(
                    '''{0} in self.connection_dict['share']: {1} on self.connection_dict['host']: {2} is a dir'''.format(
                        path,
                        self.connection_dict['share'],
                        self.connection_dict['host']))
                return True
        return False

    def storeFile(self, path, file_obj):
        if self.connect():
            try:
                return self.smbcon.storeFile(self.connection_dict['share'], path, file_obj)
            except smb_structs.OperationFailure as e:
                log.warning('Exception: smb_structs.OperationFailure\n\n%s\n\noccured %s type(str(e))', str(e),
                            type(str(e)))
                return None
            except smb_base.SMBTimeout as e:
                log.warning('Exception: smb_base.SMBTimeout trying to store file for share %s, path %s',
                            self.connection_dict['share'], path)
                return None
        else:
            return None

    @staticmethod
    def join(a, *p):
        """Join two or more pathname components, inserting '/' as needed.
        If any component is an absolute path, all previous path components
        will be discarded."""
        path = a
        for b in p:
            if b.startswith('/'):
                path = b
            elif path == '' or path.endswith('/'):
                path += b
            else:
                path += '/' + b
        return path

    def islink(self, path):
        # don't think it is possible to detect symlinks over smb if not please open an issue and cite the reference
        # i gues also warning that recurse walk is possible if symlink exists on the raw filesystem and follow
        # symlinks is enabled. althought there is unintentional protection against this via the levels argument in
        # the functions that use walk
        return False

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        """Directory tree generator.
        For each directory in the directory tree rooted at top (including top
        itself, but excluding '.' and '..'), yields a 3-tuple

            dirpath, dirnames, filenames

        dirpath is a string, the path to the directory.  dirnames is a list of
        the names of the subdirectories in dirpath (excluding '.' and '..').
        filenames is a list of the names of the non-directory files in dirpath.
        Note that the names in the lists are just names, with no path components.
        To get a full path (which begins with top) to a file or directory in
        dirpath, do os.path.join(dirpath, name).

        If optional arg 'topdown' is true or not specified, the triple for a
        directory is generated before the triples for any of its subdirectories
        (directories are generated top down).  If topdown is false, the triple
        for a directory is generated after the triples for all of its
        subdirectories (directories are generated bottom up).

        When topdown is true, the caller can modify the dirnames list in-place
        (e.g., via del or slice assignment), and walk will only recurse into the
        subdirectories whose names remain in dirnames; this can be used to prune
        the search, or to impose a specific order of visiting.  Modifying
        dirnames when topdown is false is ineffective, since the directories in
        dirnames have already been generated by the time dirnames itself is
        generated.

        By default errors from the os.listdir() call are ignored.  If
        optional arg 'onerror' is specified, it should be a function; it
        will be called with one argument, an os.error instance.  It can
        report the error to continue with the walk, or raise the exception
        to abort the walk.  Note that the filename is available as the
        filename attribute of the exception object.

        By default, os.walk does not follow symbolic links to subdirectories on
        systems that support them.  In order to get this functionality, set the
        optional argument 'followlinks' to true.

        Caution:  if you pass a relative pathname for top, don't change the
        current working directory between resumptions of walk.  walk never
        changes the current directory, and assumes that the client doesn't
        either.
        Example:
        import os
        from os.path import join, getsize
        for root, dirs, files in os.walk('python/Lib/email'):
            print root, "consumes",
            print sum([getsize(join(root, name)) for name in files]),
            print "bytes in", len(files), "non-directory files"
            if 'CVS' in dirs:
                dirs.remove('CVS')  # don't visit CVS directories


        pysm samba symlinks
        https://github.com/miketeo/pysmb/issues/35
        pysmb is capable of returning the reparse status if the remote server returns it.
        This has been tested to be true when the server is running Windows 7.
        """

        # from os.path import join, isdir, islink

        # We may not have read permission for top, in which case we can't
        # get a list of the files the directory contains.  os.path.walk
        # always suppressed the exception then, rather than blow up for a
        # minor reason when (say) a thousand readable directories are still
        # left to visit.  That logic is copied here.
        if self.connect():
            try:
                # Note that listdir and error are globals in this module due
                # to earlier import-*.
                names = self.listdir(top)
            except smb_structs.OperationFailure as err:
                log.warning('smb_structs.OperationFailure: {0}, top: {1}').format(err, top)
                if onerror is not None:
                    raise Exception(err)
                return

            dirs, nondirs = [], []
            for name in names:
                if self.isdir(self.join(top, name)):
                    dirs.append(name)
                else:
                    nondirs.append(name)

            if topdown:
                yield top, dirs, nondirs
            for name in dirs:
                path = self.join(top, name)
                if followlinks or not self.islink(path):
                    for x in self.walk(path, topdown, onerror, followlinks):
                        yield x
            if not topdown:
                yield top, dirs, nondirs


def make_dir(_dir):
    # log.error('dir %s', _dir)
    if not os.path.exists(_dir):
        try:
            os.mkdir(_dir)
            return True
        except (OSError, IOError) as e:
            log.critical('Error making dir {0}. {1}'.format(
                _dir, e), exc_info=True)
            return False
            # return Exception('Error making dir {0}. {1}'.format(
            # _dir, e))
    # return Exception('Error making dir {0}. {1}'.format(
    # _dir, e))
    elif os.path.isdir(_dir):
        return True
    elif os.path.exists(_dir):
        log.debug('{0} exists but not a dir'.format(
            _dir), exc_info=True)
        return False
        # return Exception('{0} exists but not a dir'.format(
        # _dir))
    log.error('should not be able to get here')
    return False


def strip_trailing_sep(path):
    return path.rstrip(os.sep)


def get_file_extension(path):
    """
    Return the extension fom a path.

    Parameters
    ----------
    path : basestring

    Returns
    -------
    Extension of path WITHOUT leading dot
    """

    # is path is of type (aka instance) bsestring
    if isinstance(path, string_types):
        # os.path.splitext returns a list with two items
        # Item 1 ([1])is the extension but it is .extension.
        # We want the extension without the preceeding dot. so
        # we remove the first char [1:] of the extension [1]
        return os.path.splitext(path)[1][1:]

    return False


def get_filename_root(path):
    """
    Return the filename root of the basename of path.

    Parameters
    ----------
    path : basestring

    Returns
    -------
    unicode string
        filname root of the BASRNAME of path
    """

    if isinstance(path, string_types):
        basename = os.path.basename(path)
        return os.path.splitext(basename)[0]
    return False


def get_filename_root_and_extension(path):
    """
    Return the filename root and the extension of the basename of path.

    Parameters
    ----------
    path : basestring

    Returns
    -------
    unicode string
        filname root of the BASRNAME of path

    unicode string
        extension of the BASRNAME of path WITHOUT leading dot
    """

    if isinstance(path, basestring):
        basename = os.path.basename(path)
        filename_split = os.path.splitext(basename)
        filename_root = filename_split[0]
        filename_extension = filename_split[1][1:]
        return filename_root, filename_extension
    return False


def get_path_basename(path):
    """
    Return the basename of path.

    Return the basename of path is basestring otherwise
    return False

    Parameters
    ----------
    path : basestring

    Returns
    -------
    unicode string | False
        basename of the BASRNAME of path if path is basestring FALSE if not
    """

    if isinstance(path, string_types):
        return os.path.basename(path)
    return False


def get_subdirectories(path):
    """
    Return the basename of path.

    Return the basename of path is basestring otherwise
    return False

    Parameters
    ----------
    path : basestring

    Returns
    -------
    unicode string | False
        basename of the BASRNAME of path if path is basestring FALSE if not
    """

    if os.path.isdir(path):
        return [name for name in os.listdir(path)
                if os.path.isdir(os.path.join(path, name))]
    return []


def find_largest_file_in_dir(path, scan_path, valid_extension_list=False, min_file_size=2000000, levels=2,
                             smbcon=None):
    """
    Return a dict for largest file in path, for x level(s) deep.

    Does not distinguish between files and symlinks

    Parameters
    ----------
    path : basestring
    scan_path : basestring
    valid_extension_list : list (optional)
        List of extensions e.g. (mkv, avi) that the extension of any file found
        must match to be a valid returable file
        Default : False
    min_file_size : int
        minimum filesizein byte. To disable set to 0. Default 2000000 (200mbyte)
    levels : int (optional)
        The number of directories levels beneath path to search in. 0 is path only

    Returns
    -------
    Dict
        Dict
            if no files found
                {'file_size': 0} 
            if file(s) found
                {u'extension': u'mp4',
                u'type_id': 1,
                u'filename_root': u'Some File', # Filename root of file found
                u'last_path': u'/Some Folder/Some File.mp4', # scan_path removed from full path of file
                u'folder_list': [u'Some Folder'], # All folders in last path
                u'file_size': 2015856, # Filesize of file found
                u'filename': u'Some File.mp4'} # filename of the file found
    """

    if smbcon is not None:
        return smbfs_find_largest_file_in_dir(path, scan_path,
                                              smbcon, valid_extension_list=valid_extension_list,
                                              min_file_size=2000000, levels=levels)
    else:
        # set return dict up incase we get not files
        return_dict = {'file_size': 0}

        # if path is a dir
        if os.path.isdir(path):
            # normalise path - this could be done earlier
            path = os.path.normpath(path)
            # count the number of path seperators in path to walk
            startinglevel = path.count(os.sep)
            # current_walk_path is the current abs path os.walk is currently on
            # fileList are the files in current_walk_path
            # subdirlist is a list of dirs in current_walk_path
            for current_walk_path, subdirList, fileList in os.walk(path):
                # level is number of path seperators in current path minus path to walk
                level = current_walk_path.count(os.sep) - startinglevel
                log.debug('current_walk_path: {0} for path: {1} is level: {2}'.format(
                    current_walk_path,
                    path,
                    level))
                if level < levels or levels == 0:
                    for fname in fileList:
                        file_path = os.path.join(current_walk_path, fname)
                        # get filesize in bytes
                        file_size = os.path.getsize(file_path)
                        log.debug('file_path: {0} has size: {1}'.format(
                            file_path,
                            file_size))
                        if (file_size > return_dict[
                            'file_size'] and file_size > min_film_filsize) or min_film_filsize == 0:
                            log.debug(
                                '''(file_size: {0} > return_dict['file_size']: {1} and file_size > min_film_filsize) or min_film_filsize == 0'''.format(
                                    file_size,
                                    return_dict['file_size']))
                            update_dict = False
                            file_filename_root, file_extension = get_filename_root_and_extension(fname)
                            if isinstance(valid_extension_list, list):
                                log.debug('valid_extension_list: {0} is list'.format(
                                    valid_extension_list))
                                log.debug('file_filename_root: {0} and file_extension: {1}'.format(
                                    file_filename_root,
                                    file_extension))
                                if file_extension.lower() in valid_extension_list:
                                    log.debug('file_extension: {0} in valid_extension_list: {1}'.format(
                                        file_extension,
                                        valid_extension_list))
                                    update_dict = True
                            else:
                                update_dict = True

                            if update_dict == True:
                                last_path = re.sub(r"""^{0}""".format(re.escape(scan_path)), '', current_walk_path)
                                return_dict['file_size'] = file_size
                                return_dict['filename'] = fname
                                return_dict['filename_root'] = file_filename_root
                                return_dict['extension'] = file_extension
                                return_dict['current_walk_path'] = os.path.join(last_path, fname)
                                return_dict['folder_list'] = [x for x in last_path.split(os.sep) if
                                                              x]  # only non empty strings
                                return_dict['type_id'] = 1

        if return_dict['file_size'] > 0:
            return return_dict
        else:
            return {'type_id': False}


def smbfs_find_largest_file_in_dir(path, scan_path, smbcon, valid_extension_list=False, min_file_size=2000000,
                                   levels=2):
    """
    Return a dict for largest file in path, for x level(s) deep.

    Does not distinguish between files and symlinks

    Parameters
    ----------
    path : basestring
    scan_path : basestring
    valid_extension_list : list (optional)
        List of extensions e.g. (mkv, avi) that the extension of any file found
        must match to be a valid returable file
        Default : False
    min_file_size : int
        minimum filesizein byte. To disable set to 0. Default 2000000 (200mbyte)
    levels : int (optional)
        The number of directories levels beneath path to search in. 0 is path only

    Returns
    -------
    Dict
        Dict
            if no files found
                {'file_size': 0}
            if file(s) found
                {u'extension': u'mp4',
                u'type_id': 1,
                u'filename_root': u'Some File', # Filename root of file found
                u'last_path': u'/Some Folder/Some File.mp4', # scan_path removed from full path of file
                u'folder_list': [u'Some Folder'], # All folders in last path
                u'file_size': 2015856, # Filesize of file found
                u'filename': u'Some File.mp4'} # filename of the file found
    """

    # set return dict up incase we get not files
    return_dict = {'file_size': 0}

    log.debug('valid_extension_list %s', valid_extension_list)

    # if path is a dir
    if smbcon.isdir(path):
        # normalise path - this could be done earlier
        # todo change to smbfs normpath
        path = os.path.normpath(path)
        # count the number of path seperators in path to walk
        # todo change to smbfs.sep
        startinglevel = path.count(os.sep)
        # current_walk_path is the current abs path os.walk is currently on
        # fileList are the files in current_walk_path
        # subdirlist is a list of dirs in current_walk_path
        for current_walk_path, subdirList, fileList in smbcon.walk(path):
            # level is number of path seperators in current path minus path to walk
            # todo change to smbfs.sep
            level = current_walk_path.count(os.sep) - startinglevel
            log.debug('current_walk_path: {0} for path: {1} is level: {2}'.format(
                current_walk_path,
                path,
                level))
            if level < levels or levels == 0:
                for fname in fileList:
                    file_path = smbfs.join(current_walk_path, fname)
                    # get filesize in bytes
                    file_size = smbcon.getsize(file_path)
                    log.debug('file_path %s size %s', file_path, file_size)
                    # raise SystemExit
                    log.debug('file_path: {0} has size: {1}'.format(
                        file_path,
                        file_size))
                    if (file_size > return_dict['file_size'] and file_size > min_film_filsize) or min_film_filsize == 0:
                        log.debug(
                            '''(file_size: {0} > return_dict['file_size']: {1} and file_size > min_film_filsize) or min_film_filsize == 0'''.format(
                                file_size,
                                return_dict['file_size']))
                        update_dict = False
                        file_filename_root, file_extension = get_filename_root_and_extension(fname)
                        if isinstance(valid_extension_list, list):
                            log.debug('valid_extension_list: {0} is list'.format(
                                valid_extension_list))
                            log.debug('file_filename_root: {0} and file_extension: {1}'.format(
                                file_filename_root,
                                file_extension))
                            if file_extension.lower() in valid_extension_list:
                                log.debug('file_extension: {0} in valid_extension_list: {1}'.format(
                                    file_extension,
                                    valid_extension_list))
                                update_dict = True
                        else:
                            update_dict = True
                        log.debug('update dict is %s for %s', update_dict, smbfs.join(current_walk_path, fname))
                        if update_dict is True:
                            last_path = re.sub(r"""^{0}""".format(re.escape(scan_path)), '', current_walk_path)
                            return_dict['file_size'] = file_size
                            return_dict['filename'] = fname
                            return_dict['filename_root'] = file_filename_root
                            return_dict['extension'] = file_extension
                            return_dict['current_walk_path'] = os.path.join(last_path, fname)
                            return_dict['last_path'] = smbfs.join(last_path, fname)
                            return_dict['folder_list'] = [x for x in last_path.split(os.sep) if
                                                          x]  # only non empty strings
                            return_dict['type_id'] = 1
                    else:
                        log.debug(
                            '''(NOT -- file_size: {0} > return_dict['file_size']: {1} and file_size > min_film_filsize) or min_film_filsize == 0'''.format(
                                file_size,
                                return_dict['file_size']))

    if return_dict['file_size'] > 0:
        return return_dict
    else:
        return {'type_id': False}


def detect_video_diskfolder(path, scan_path, smbcon=None):
    """
    Determine if path is a video disk folder (e.g. DVD, BluRay)

    Parameters
    ----------
    path : basestring
    scan_path : basestring

    Returns
    -------
    Dict
        If path not detected as disk folder
            {'type_id': False}
        If detected as disk folder
            {u'last_path': u'/Some Film #2008 DVD', # scan_path removed from full path of file
            u'type_name': u'VIDEO_TS', # Description for disk folder type detected
            u'type_id': 20} # id for disk folder type detected
    """

    return_dict = {'type_id': False}

    if smbcon is not None:
        filfolders = smbcon.listdir(path)
    else:
        filfolders = os.listdir(path)

    log.debug('filfolders: {0} for path: {1}'.format(
        filfolders,
        path))

    # perhaps make this a bit better specifc file or folder matches. At the moment e.g. VIDEO_TS will match file for folder

    for filfolder in filfolders:

        pattern_diskfilefolder_search_result = re.search(pattern_diskfilefolder, filfolder)

        if pattern_diskfilefolder_search_result:
            log.debug('filfolder: {0} for path: {1} matched the pattern {2}'.format(
                filfolder,
                path,
                pattern_diskfilefolder))

            diskfilefolder_found = pattern_diskfilefolder_search_result.groupdict()['diskfilefolder']

            last_path = re.sub(r"""^{0}""".format(re.escape(scan_path)), '', path)

            log.debug('last_path: {0} for path: {1} and scan_path: {2}'.format(
                last_path,
                path,
                scan_path))

            return_dict['type_id'] = diskfilefolder_types_dict[diskfilefolder_found.upper()]
            return_dict['type_name'] = diskfilefolder_found
            return_dict['last_path'] = last_path

            return return_dict

    log.debug('none of the filfolders or files: {0} for path: {1} match the pattern {2}'.format(
        filfolders,
        path,
        pattern_diskfilefolder))

    return return_dict


def get_folder_contents_type(path, scan_path, smbcon=None, valid_extension_list=None, type_only=False):
    """
    Determine if path is a video disk folder (e.g. DVD)
    or contains a film file (e.g. some film.mkv)

    Parameters
    ----------
    path : basestring
    scan_path : basestring
    valid_extension_list : List
    type_only : True|False

    Returns
    -------
    Dict
        If path not detected as disk folder
            {'type_id': False}
        If detected as disk folder
            {u'last_path': u'/Some Film #2008 DVD', # scan_path removed from full path of file
            u'type_name': u'VIDEO_TS', # Description for disk folder type detected
            u'type_id': 20} # id for disk folder type detected
        If detected as film file
                {u'provider_ids': {'imdb': 'tt123456'}, # provider ids found from nfo files
                u'extension': u'mp4',
                u'type_id': 1,
                u'filename_root': u'Some File', # Filename root of file found
                u'last_path': u'/Some Folder/Some File.mp4', # scan_path removed from full path of file
                u'folder_list': [u'Some Folder'], # All folders in last path
                u'file_size': 2015856, # Filesize of file found
                u'filename': u'Some File.mp4'} # filename of the file found			
    """

    detect_video_diskfolder_result = detect_video_diskfolder(path, scan_path, smbcon=smbcon)

    if detect_video_diskfolder_result['type_id'] != False:
        return detect_video_diskfolder_result

    largest_file_in_dir = find_largest_file_in_dir(path, scan_path, valid_extension_list, smbcon=smbcon)

    log.debug('largest_file_in_dir: {0} for path: {1} with valid_extension_list: {2}'.format(
        largest_file_in_dir,
        path,
        valid_extension_list))

    if largest_file_in_dir['type_id'] != False:

        if largest_file_in_dir['file_size'] > 0:
            # if a file has been found from largest_file_in_dir check to see
            # if there as are any nfo files
            largest_file_in_dir['provider_ids'] = search_ifo_files_for_provider_id(path)

    return largest_file_in_dir


def search_ifo_files_for_provider_id(path):
    """
    Search nfo files for provider ids

    Parameters
    ----------
    path : basestring

    Returns
    -------
    Dict
        If no provider ids found
            {} # Empty dict
        If provider id(s) found
            {'imdb': 'tt123456'}
    """

    # move pattern_dict to constants
    pattern_dict = {'imdb': [r'(?=(tt[0-9]{7}))']}

    return_dict = {}

    if os.path.isdir(path):

        # normalise path - this could be done earlier
        path = os.path.normpath(path)

        # count the number of path seperators in path to walk
        startinglevel = path.count(os.sep)

        for current_walk_path, subdirList, fileList in os.walk(path):

            # level is number of path seperators in current path minus path to walk

            level = current_walk_path.count(os.sep) - startinglevel

            log.debug('current_walk_path: {0} for path: {1} is level: {2}'.format(
                current_walk_path,
                path,
                level))

            if level < 2:

                for fname in fileList:

                    file_path = os.path.join(current_walk_path, fname)

                    file_filename, file_extension = os.path.splitext(file_path)

                    if file_extension.lower() == '.nfo':

                        for i, line in enumerate(open(file_path)):

                            for provider in pattern_dict:

                                for pattern in pattern_dict[provider]:

                                    matches = re.findall(pattern, line, re.I)

                                    for match in matches:

                                        if not return_dict.has_key(provider):
                                            return_dict[provider] = []

                                        if match not in return_dict[provider]:
                                            return_dict[provider].append(match)
    return return_dict


def os_casesless_check():
    """
    Determine if filesystem is caseless

    Returns
    -------
    True|False
        True if os is caseless
        False if os is not caseless
    """

    for filefolder in sys.path:

        # a letter is needed to check for case
        if re.search(r"""[a-zA-Z]""", filefolder):

            if os.path.isdir(filefolder):

                if os.path.isdir(filefolder.upper()) and os.path.isdir(filefolder.lower()):
                    return True

                return False

            if os.path.isfile(filefolder):

                if os.path.isfile(filefolder.upper()) and os.path.isfile(filefolder.lower()):
                    return True

                return False


def check_for_exisiting_default_image(download_folder, image_type, startswith):
    """Check to see if the raw image has allready been downloaded

        Args:
            | download_folder (string): full path to the download folder
            | image_type (string): the image type (icon/synopsis)
            | startswith (string): the first part of the filename

        Returns:
            string: filename or None is no file can be found

    """
    if os.path.isdir(download_folder):
        log.debug('{0} exists and is a folder'.format(download_folder))
        for filefolder in os.listdir(download_folder):
            if os.path.isfile(os.path.join(download_folder, filefolder)):
                if filefolder.startswith(startswith):
                    return filefolder
    else:
        log.debug('{0} does not exist or is not a folder'.format(download_folder))
    return None


# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def path_avail_space(path, hr=False):
    path_fo = os.open(path, os.O_RDONLY)
    path_fstatvfs = os.fstatvfs(path_fo)
    if hr is True:
        path_fstatvfs_avail = sizeof_fmt(path_fstatvfs.f_bavail * path_fstatvfs.f_bsize)
    else:
        path_fstatvfs_avail = path_fstatvfs.f_bavail * path_fstatvfs.f_bsize
    os.close(path_fo)
    return path_fstatvfs_avail


def execute(command, display_stdout=False, _shell=False):
    process = subprocess.Popen(command, shell=_shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    if display_stdout:
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() != None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    # if (exitCode == 0):
    # print exitCode
    return exitCode, output


class SMB_Buffer_Wrapper(object):

    def __init__(self, smbcon, path, bytes_to_read=7 * 188 * 10):
        self.smbcon = smbcon
        self.path = path
        self.seek_position = 0
        self.bytes_to_read = bytes_to_read
        self.size = self.smbcon.getsize(self.path)

    def seek(self, seek_to):
        self.seek_position = seek_to

    def tell(self):
        return self.seek_position

    def read(self, bytes_to_read=None):
        tmp_bytes_obj = BytesIO()
        if not isinstance(bytes_to_read, int):
            bytes_to_read = self.bytes_to_read
        self.smbcon.retrieveFileFromOffset(self.path, tmp_bytes_obj,
                                           offset=self.seek_position,
                                           max_length=bytes_to_read,
                                           timeout=10)
        new_seek_position = self.tell() + bytes_to_read
        if new_seek_position > self.size:
            self.seek_position = self.size
        else:
            self.seek_position = new_seek_position
        tmp_bytes_obj.seek(0)
        Buffer = tmp_bytes_obj.read()
        tmp_bytes_obj.truncate(0)
        tmp_bytes_obj.close()
        return Buffer
