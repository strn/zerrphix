# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

from zerrphix import logger
from zerrphix.manager import Manager
from zerrphix.options import unicode_argv
from daemon import runner
import os
from ._version import __version__
import psutil
import sys
import uuid
import base64
import shutil
from zerrphix.util.extra import x
from Crypto import Random
from tempfile import gettempdir
import stat
import re
import subprocess
from zerrphix.util.text import date_time
from zerrphix.util.extra import AESCipher
from zerrphix.util.extra import z
import bcrypt
import hashlib
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser
from getpass import getpass, getuser
from builtins import input
import time
import tarfile
from zerrphix.util.network import private_listen_address_list
import socket
from zerrphix.exceptions import GetConfigPath
#log = logging.getLogger(__name__)
#log.addHandler(logging.NullHandler())


#__title__ = 'pyZerrphix'
#__version__ = '0.1.1'
#__author__ = 'Zerrphix Project'
#__copyright__ = 'Copyright (c) 2014-2017 Zerrphix Project'
#__license__ = 'BSD'

PID_FILE = '/tmp/zerrphix.pid'

class FakeManager(object):
    def __init__(self, args):
        """
        :param args: CLI args
        """
        # global manager

        # if not self.unit_test:
        # assert not manager, 'Only one instance of Manager should be created at a time!'
        # elif manager:
        # log.info('last manager was not torn down correctly')

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = PID_FILE
        self.pidfile_timeout = 5

def usage():
    sys.stderr.write('Valid options: start | stop | status | install | redeptemplates %s' % os.linesep)

def check_zerrphix_runnnig():
    pid = None
    if os.path.isfile(PID_FILE):
        with open(PID_FILE) as pid_file:
            line = pid_file.readline()
            try:
                pid = int(line.strip())
            except:
                raise
            else:
                if psutil.pid_exists(pid):
                    return pid
    return pid

def user_input_confirm(user_input):
    db_name_confirmed = False
    while db_name_confirmed is False:
        # make py3 compatible
        db_name_confirm_result = input('%s You have chosen %s is that correct? [y/n]: ' % (
            date_time(), user_input))
        if db_name_confirm_result == 'y' or db_name_confirm_result == 'n':
            return db_name_confirm_result
        else:
            sys.stderr.write('You must enter either y/n. Please try again%s' % (os.linesep))

def main(args=None):
    """Main entry point for Command Line Interface"""
    if args is None:
        # Decode all arguments to unicode before parsing
        args = unicode_argv()[1:]

    # Used flexget manger implementation see LICENSE.flexget https://github.com/Flexget/Flexget/blob/develop/LICENSE
    # try:
    # git tag -d 12345
    # git push origin :refs/tags/12345
    manager = None

    if len(sys.argv) >= 2:
        if sys.argv[1] == 'start':
            pid = check_zerrphix_runnnig()
            if pid is None:
                logger.initialize()
                try:
                    manager = Manager(args)
                except (IOError, ValueError) as e:
                    if any(arg in ['debug', '--debug'] for arg in [a.lower() for a in sys.argv]):
                        import traceback
                        traceback.print_exc()
                        raise
                    else:
                        sys.stderr.write('Could not instantiate manager: %s' % str(e))
                    sys.exit(1)
                except GetConfigPath as e:
                    sys.stderr.write('%s%s' % (str(e), os.linesep))
            else:
                sys.stdout.write('Zerrphix is already running with PID %s.%s' % (pid, os.linesep))
        elif sys.argv[1] == 'stop':
            manager = FakeManager(args)
        #manager.run()
        """
        >>> import psutil
        >>> psutil.pid_exists(2353)
        True
        """
        if sys.argv[1] in ['start', 'stop']:
            time.sleep(1)
            if manager is not None:
                if sys.argv[1] == 'start':
                    sys.stdout.write('\rTrying to start zerrphix. Please wait ...%s' % (os.linesep))
                else:
                    sys.stdout.write('\rTrying to stop zerrphix.  Please wait ...%s' % (os.linesep))
                uid = os.geteuid()
                gid = os.getegid()
                daemon_runner = runner.DaemonRunner(manager)
                daemon_runner.daemon_context.uid = uid
                daemon_runner.daemon_context.gid = gid
                try:
                    daemon_runner.do_action()
                except runner.DaemonRunnerStopFailureError as e:
                    error_message = str(e)
                    if re.search(r'''PID file .* not locked''', error_message, flags=re.I|re.U):
                        sys.stderr.write('Zerrphix is not running%s' % os.linesep)
                    else:
                        sys.stderr.write('Could not stop zerrphix %s' % os.linesep)
                        sys.stderr.write('%s%s' % (error_message, os.linesep))
            time.sleep(1)
        elif sys.argv[1] == 'status':
            pid = check_zerrphix_runnnig()
            if isinstance(pid, int):
                sys.stdout.write('Zerrphix is running with PID %s.%s' % (pid, os.linesep))
            else:
                sys.stdout.write('Zerrphix is not running.%s' % os.linesep)
        elif sys.argv[1] == 'redeptemplates':
            templates_archive_path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                'templates.tar.gz'
            )
            sys.stderr.write('%s Installing default templates%s' % (date_time(), os.linesep))
            user_home_dir = os.path.abspath(os.path.expanduser('~'))
            zerrphix_root_dir = os.path.join(user_home_dir, '.zerrphix')
            template_root_dir = os.path.join(zerrphix_root_dir, 'template_store')
            if os.path.isfile(templates_archive_path):
                templates_archive = tarfile.open(templates_archive_path)
                templates_archive.extractall(template_root_dir)
                sys.stderr.write('%s Installed default templates%s' % (date_time(), os.linesep))
            else:
                sys.stderr.write('%s templates_archive_path %s does not exist%s' % (
                    date_time(), templates_archive_path, os.linesep
                ))
                sys.exit(1)
        elif sys.argv[1] == 'install':
            user_home_dir = os.path.abspath(os.path.expanduser('~'))
            zerrphix_root_dir = os.path.join(user_home_dir, '.zerrphix')
            try:
                if not os.path.isdir(zerrphix_root_dir):
                    os.mkdir(zerrphix_root_dir)
            except Exception as e:
                sys.stderr.write('%s Cannot make dir %s%s' % (date_time(), zerrphix_root_dir, os.linesep))
                sys.stderr.write('%s %s%s' % (date_time(), e, os.linesep))
                sys.stderr.write('%s Program terminating%s' % (date_time(), os.linesep))
                sys.exit(1)
            else:
                sys.stdout.write('%s Install starting %s' % (date_time(), os.linesep))
                config = ConfigParser(allow_no_value=True)
                db_name_set = False
                while db_name_set is False:
                    # make py3 compatible
                    db_name = input('%s Please choose a database name for zerrphix to use or press enter to leave as'
                                    ' the default (zerrphix): ' % date_time())
                    if not db_name:
                        db_name = 'zerrphix'
                    db_name = re.sub(r'''[^\w]''', '', db_name)
                    db_name = db_name[:255]
                    db_name_confirm_result = user_input_confirm(db_name)
                    #db_name_confirm = ('You have chosen %s as the db name is that correct? [y/n]: ')
                    if db_name_confirm_result == 'y':
                        db_name_set = True
                    elif db_name_confirm_result == 'n':
                        db_name_set = False
                config.add_section('database')
                config.set('database', '; dialect http://docs.sqlalchemy.org/en/latest/dialects/ sqlite is NOT supported'
                                       ' by zerrphix')
                config.set('database', 'dialect', 'mysql')
                config.set('database', '; python db module')
                config.set('database', 'pyconnector', 'pymysql')
                config.set('database', '; username')
                config.set('database', 'username', 'zerrphix')
                config.set('database', '; password')
                mysql_zerrphix_user_pwd = hashlib.sha256(Random.get_random_bytes(256)).hexdigest()[:16]
                config.set('database', 'password', mysql_zerrphix_user_pwd)
                config.set('database', '; e.g. localhost')
                config.set('database', 'host', 'localhost')
                config.set('database', '; port db is running on')
                config.set('database', 'port', '3306')
                config.set('database', '; database name')
                config.set('database', 'database', db_name)
                config.set('database', '; mysql use utf8mb4, others use utf8')
                config.set('database', 'charset', 'utf8mb4')

                config.add_section('flask')
                config.set('flask', '; flask secret key. If this is changed any user who is logged in will have'
                                    ' to login again.')
                holder_flask = hashlib.sha256(Random.get_random_bytes(256)).hexdigest()[:16] # this is for flask
                config.set('flask', 'holder', holder_flask)

                config.add_section('global')
                config.set('global', '; ::config_root:: is the folder this file is in')
                config.set('global', '; where to store the downloaded images')
                config.set('global', 'downloaded_images_root_path', '::config_root::%sdownloaded_images' % os.sep)
                config.set('global', '; where to store the rendered images for dune_http and the admin web ui')
                config.set('global', 'rendered_image_root_path', '::config_root::%srendered' % os.sep)
                config.set('global', '; where to store the the templates')
                config.set('global', 'template_store_path', '::config_root::%stemplate_store' % os.sep)
                # template store path

                # https://www.laurentluce.com/posts/python-and-cryptography-with-pycrypto/
                sys.stdout.write('%s Generating crypto keys %s' % (date_time(), os.linesep))
                #random_generator = Random.new().read
                key = hashlib.sha256(Random.get_random_bytes(256)).hexdigest()
                holder_config = x(key) # put this in [global] holder =
                config.set('global', '; the secret that is used to encrypt the samba passwords that need to be stored in'
                                     ' the db')
                config.set('global', 'holder', holder_config)

                #local_ip_string = ' '.join(getIPs())
                local_ip_string = ''
                for ip in private_listen_address_list():
                    local_ip_string += '%s, ' % ip
                local_ip_string = local_ip_string.strip(', ')
                dune_http_server_listen_ip_set = False
                while dune_http_server_listen_ip_set is False:
                    dune_http_server_listen_ip = input(
                        '%s Please choose an ip address for the DUNE'
                        ' httpserver to listen on. The available address(s) that have been detected are %s.'
                        ' Please note if this device is set to DHCP ip allocation then it might change over time.'
                        ' Alternatively you can just press enter to listen on all ports (0.0.0.0): ' % (date_time(),
                                                                                              local_ip_string))
                    # todo some more input sanitisation here
                    if not dune_http_server_listen_ip:
                        dune_http_server_listen_ip = '0.0.0.0'
                        if user_input_confirm(dune_http_server_listen_ip) == 'y':
                            dune_http_server_listen_ip_set = True
                    else:
                        try:
                            socket.inet_aton(dune_http_server_listen_ip.strip())
                        except Exception as e:
                            sys.stderr.write('%s Please enter a vlid ip address %s' % (
                                date_time(), os.linesep
                            ))
                        else:
                            if user_input_confirm(dune_http_server_listen_ip) == 'y':
                                dune_http_server_listen_ip_set = True

                dune_http_server_listen_port_set = False
                while dune_http_server_listen_port_set is False:
                    dune_http_server_listen_port = input('%s Please specify a port for the DUNE httpserver to listen on'
                                                       ' or press enter to to use the default (9000): ' % (date_time()))
                    # todo some more input sanitisation here
                    if not dune_http_server_listen_port:
                        dune_http_server_listen_port = '9000'
                        if user_input_confirm(dune_http_server_listen_port) == 'y':
                            dune_http_server_listen_port_set = True
                    else:
                        if dune_http_server_listen_port.strip().isdigit():
                            dune_http_server_listen_port_set = True
                        else:
                            sys.stderr.write('%s Please enter a vlid port (numbers only) %s' % (
                                date_time(), os.linesep
                            ))

                admin_http_server_listen_ip_set = False
                while admin_http_server_listen_ip_set is False:
                    admin_http_server_listen_ip = input(
                        '%s Please choose an ip address for the ADMIN'
                        ' httpserver to listen on. Please note if this device is set to DHCP ip allocation then it'
                        ' might change over time. The available address(s) that have been detected are %s.'
                        ' Alternatively you can just press enter to listen on all ip addresses (0.0.0.0): ' % (date_time(),
                                                                                              local_ip_string))
                    # todo some more input sanitisation here
                    if not admin_http_server_listen_ip:
                        admin_http_server_listen_ip = '0.0.0.0'
                        if user_input_confirm(admin_http_server_listen_ip) == 'y':
                            admin_http_server_listen_ip_set = True
                    else:
                        try:
                            socket.inet_aton(admin_http_server_listen_ip.strip())
                        except Exception as e:
                            sys.stderr.write('%s Please enter a vlid ip address %s' % (
                                date_time(), os.linesep
                            ))
                        else:
                            if user_input_confirm(admin_http_server_listen_ip) == 'y':
                                admin_http_server_listen_ip_set = True

                admin_http_server_listen_port_set = False
                while admin_http_server_listen_port_set is False:
                    admin_http_server_listen_port = input('%s Please specify a port for the ADMIN httpserver to listen on'
                                                       ' or press enter to to use the default (9001): ' % (date_time()))
                    # todo some more input sanitisation here
                    if not admin_http_server_listen_port:
                        admin_http_server_listen_port = '9001'
                        if user_input_confirm(admin_http_server_listen_port) == 'y':
                            admin_http_server_listen_port_set = True
                    else:
                        if admin_http_server_listen_port.strip().isdigit():
                            admin_http_server_listen_port_set = True
                        else:
                            sys.stderr.write('%s Please enter a vlid port (numbers only) %s' % (
                                date_time(), os.linesep
                            ))

                config.add_section('httpserver')
                config.set('httpserver', '; the ip for the dune httpserver to listen on. A value of 0.0.0.0 will cause the '
                                      'httpserver to listen on all interfaces.')
                config.set('httpserver', 'dune_http_server_listen_ip', dune_http_server_listen_ip.strip())
                config.set('httpserver', '; the port for the dune httpserver to listen on.')
                config.set('httpserver', 'dune_http_server_listen_port', int(dune_http_server_listen_port.strip()))
                config.set('httpserver', '; the ip for the admin httpserver to listen on. A value of 0.0.0.0 will cause the '
                                      'httpserver to listen on all interfaces.')
                config.set('httpserver', 'admin_http_server_listen_ip', admin_http_server_listen_ip.strip())
                config.set('httpserver', '; the port for the dune httpserver to listen on.')
                config.set('httpserver', 'admin_http_server_listen_port', int(admin_http_server_listen_port.strip()))
                config.set('httpserver', '; enable debug mode for the admin web interface (when set to true introduces'
                                         ' a security vulnerability).')
                config.set('httpserver', 'admin_http_server_debug', 'False')

                config.add_section('logging')
                config.set('logging', '; the path to write the logs')
                config.set('logging', 'log_file_path', os.path.join(user_home_dir, 'zerrphix.log'))
                config.set('logging', '; how many bytes a log file can be. 1000000 = 1 MegaByte')
                config.set('logging', 'log_file_maxbytes', '1000000')
                config.set('logging', '; The maximum number of log files that can be present')
                config.set('logging', 'log_file_backupCount', '3')
                config.set('logging', '; log to file level error, info or debug')
                config.set('logging', 'log_file_level', 'info')
                config.set('logging', '; 1 = compress log files, 0 = do not compress log files')
                config.set('logging', 'log_to_file_compression', '0')
                config.set('logging', '; log to the console')
                config.set('logging', 'log_to_console', '0')
                config.set('logging', '; log to console level error, info or debug')
                config.set('logging', 'log_to_console_level', 'error')
                config_file_path = os.path.join(zerrphix_root_dir ,b'zerrphix.ini')
                if os.path.exists(config_file_path):
                    old_ini_file_name = '%s.%s' % (config_file_path, date_time(type='ymd_hms'))
                    shutil.move(config_file_path, old_ini_file_name)
                with open(config_file_path, b'w') as tcfg:
                    config.write(tcfg)

                install_templates_set = False
                while install_templates_set is False:
                    install_templates = input('%s Install default template(s)? This will re-install them'
                                              ' if they already exist [y/n]: ' % date_time())
                    # todo some more input sanitisation here
                    if install_templates == 'y':
                        install_templates_set = True
                    elif install_templates == 'n':
                        install_templates_set = True
                    else:
                        sys.stderr.write('You must choose y or n%s' % (os.linesep))

                template_root_dir = os.path.join(zerrphix_root_dir, 'template_store')
                if install_templates == 'y':
                    if not os.path.isdir(template_root_dir):
                        try:
                            os.mkdir(template_root_dir)
                        except OSError as e:
                            sys.stderr.write('%s Cannot make template_root_dir %s OSError %s%s' % (
                                date_time(), template_root_dir, str(e), os.linesep
                            ))
                            sys.exit(1)
                        except Exception as e:
                            sys.stderr.write('%s Cannot make template_root_dir %s Exception %s%s' % (
                                date_time(), template_root_dir, str(e), os.linesep
                            ))
                            sys.exit(1)
                    templates_archive_path = os.path.join(
                        os.path.abspath(os.path.dirname(__file__)),
                        'templates.tar.gz'
                    )

                    sys.stderr.write('%s Installing default templates%s' % (date_time(), os.linesep))
                    if os.path.isfile(templates_archive_path):
                        templates_archive = tarfile.open(templates_archive_path)
                        templates_archive.extractall(template_root_dir)
                        sys.stderr.write('%s Installed default templates%s' % (date_time(), os.linesep))
                    else:
                        sys.stderr.write('%s templates_archive_path %s does not exist%s' % (
                            date_time(), templates_archive_path, os.linesep
                        ))
                        sys.exit(1)
                default_template_path = os.path.join(
                    template_root_dir, 'default'
                )
                #raise SystemExit
                sys.stdout.write('%s Please enter the username you want to use with zerrphix'
                                 ' this will be used for the dune and the admin web ui %s' % (
                    date_time(), os.linesep))
                #make py3 compatible
                username_set = False
                while username_set is False:
                    username = input('%s Username: ' % date_time())
                    # todo some more input sanitisation here
                    if not username:
                        sys.stderr.write('%s Username cannot be empty. Please Try again%s' % (date_time(),
                                                                                              os.linesep))
                    else:
                        username_confirmed = user_input_confirm(username)
                        if username_confirmed == 'y':
                            username_set = True
                passwords_match = False
                while passwords_match is False:
                    # make py3 compatible
                    password = getpass('%s Password: ' % date_time())
                    if password:
                        retype_password = getpass('%s ReType-Password: ' % date_time())
                        if password == retype_password:
                            passwords_match = True
                        else:
                            sys.stderr.write('%s Passwords do not match. Please Try again%s' % (date_time(), os.linesep))
                    else:
                        sys.stderr.write('%s Password cannot be blank. Please Try again%s' % (date_time(), os.linesep))
                user_lang_dict = {'1': '1823',
                                  '2': '1942',
                                  '3': '1539'}
                user_lang_choice_dict = {'1': 'English',
                                         '2': 'Francais',
                                         '3': 'Deutsche'}
                user_lang_set = False
                while user_lang_set is False:
                    sys.stderr.write('%s 1) English%s' % (date_time(), os.linesep))
                    sys.stderr.write('%s 2) Francais%s' % (date_time(), os.linesep))
                    sys.stderr.write('%s 3) Deutsche%s' % (date_time(), os.linesep))
                    user_lang = input('{date_time} Please Choose a language from the above list to use for when'
                                      ' acquiring film and tv data/images: '.format(line_sep=os.linesep,
                                                                 date_time=date_time()))
                    if user_lang not in user_lang_dict:
                        sys.stderr.write('%s Please choose an option from the list. Please Try again%s' % (date_time(),
                                                                                                           os.linesep))
                    else:
                        user_lang_confirmed = user_input_confirm(user_lang_choice_dict[user_lang])
                        if user_lang_confirmed == 'y':
                            user_lang_set = True
                sys.stdout.write('%s Hashing password using bcrypt %s' % (date_time(), os.linesep))
                password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                sys.stdout.write('%s Generating files for db install %s' % (date_time(), os.linesep))
                temp_dir = gettempdir()
                # todo create db in a serperate file to exlude it
                from zerrphix.install.zerrphix_first_install_drop_db import zerrphix_first_install_drop_db
                from zerrphix.install.zerrphix_first_install_create_db import zerrphix_first_install_create_db
                from zerrphix.install.zerrphix_first_install_create_tables import zerrphix_first_install_create_tables
                from zerrphix.install.zerrphix_first_install_populate_tables import zerrphix_first_install_populate_tables
                from zerrphix.install.zerrphix_first_install_post_populate import zerrphix_first_install_post_populate
                from zerrphix.install.zerrphix_first_install_add_user import zerrphix_first_install_add_user
                from zerrphix.install.zerrphix_first_install_add_mysql_user import zerrphix_first_install_add_mysql_user

                drop_db_set = False
                while drop_db_set is False:
                    # make py3 compatible
                    drop_db = input('%s Remove database %s if it exists? Choose y for a new install or'
                                    ' a complete re-install [y/n]: ' % (date_time(), db_name))
                    if drop_db == 'y':
                        drop_db = '1'
                        drop_db_set = True
                    elif drop_db == 'n':
                        drop_db = '0'
                        drop_db_set = True
                    else:
                        sys.stderr.write('%s You must enter either y/n. Please Try again%s' % (date_time(),
                                                                                               os.linesep))

                install_mysql_set = False
                while install_mysql_set is False:
                    # make py3 compatible
                    install_mysql = input('%s Zerrphix requires mysql, a database engine to store information.'
                                          ' Mysql can be install manually, however it must be running and root login'
                                          ' accessible via unix socket plugin for the zerrphix install process'
                                          ' to complete sucessfully. You can use e to exit this install to'
                                          ' manually install mysql if that is your prefernce. Do you want this script'
                                          ' to install mysql (recommneded)? [y/n/e]: ' % date_time())
                    if install_mysql == 'y':
                        install_mysql = '1'
                        install_mysql_set = True
                    elif install_mysql == 'n':
                        install_mysql = '0'
                        install_mysql_set = True
                    elif install_mysql == 'e':
                        sys.exit(0)
                    else:
                        sys.stderr.write('You must enter either y/n/e. Please Try again%s' % (os.linesep))

                zerrphix_first_install_drop_db_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_drop_db.sql')
                zerrphix_first_install_drop_db = re.sub(r'''::db_name::''', db_name, zerrphix_first_install_drop_db)

                with open(zerrphix_first_install_drop_db_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_drop_db:
                        sqlfile.write(line)

                zerrphix_first_install_create_db_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_create_db.sql')

                zerrphix_first_install_create_db = re.sub(r'''::db_name::''', db_name, zerrphix_first_install_create_db)
                with open(zerrphix_first_install_create_db_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_create_db:
                        sqlfile.write(line)

                zerrphix_first_install_create_tables_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_create_tables.sql')
                with open(zerrphix_first_install_create_tables_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_create_tables:
                        sqlfile.write(line)

                zerrphix_first_install_populate_tables_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_populate_tables.sql')
                with open(zerrphix_first_install_populate_tables_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_populate_tables:
                        try:
                            sqlfile.write(line)
                        except UnicodeDecodeError as e:
                            print(type(line))
                            print(line)
                            print(repr(line))
                            sys.exit(1)

                zerrphix_first_install_post_populate = re.sub('::template_path::', default_template_path, zerrphix_first_install_post_populate)
                zerrphix_first_install_post_populate_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_post_populate.sql')
                with open(zerrphix_first_install_post_populate_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_post_populate:
                        sqlfile.write(line)

                zerrphix_first_install_add_user = re.sub('::username::', username, zerrphix_first_install_add_user)
                zerrphix_first_install_add_user = re.sub('::password::', password, zerrphix_first_install_add_user)
                zerrphix_first_install_add_user = re.sub('::last_edit_datetime::', date_time(), zerrphix_first_install_add_user)
                if user_lang not in user_lang_dict:
                    zerrphix_first_install_add_user = re.sub('::lang::', '1823',
                                                             zerrphix_first_install_add_user)
                else:
                    zerrphix_first_install_add_user = re.sub('::lang::', user_lang_dict[user_lang],
                                                             zerrphix_first_install_add_user)

                zerrphix_first_install_add_user_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_add_user.sql')
                with open(zerrphix_first_install_add_user_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_add_user:
                        sqlfile.write(line)

                zerrphix_first_install_add_mysql_user = re.sub('::password::', mysql_zerrphix_user_pwd, zerrphix_first_install_add_mysql_user)
                zerrphix_first_install_add_mysql_user = re.sub(r'''::db_name::''', db_name, zerrphix_first_install_add_mysql_user)
                zerrphix_first_install_add_mysql_user_sql_filename = os.path.join(temp_dir,
                                                                                 'zerrphix_first_install_add_mysql_user.sql')
                with open(zerrphix_first_install_add_mysql_user_sql_filename, b'w') as sqlfile:
                    for line in zerrphix_first_install_add_mysql_user:
                        sqlfile.write(line)

                from zerrphix.install.install_mysql import install_mysql_bash

                install_mysql_bash = re.sub('::temp_dir::', temp_dir, install_mysql_bash)
                install_mysql_bash = re.sub('::os_sep::', os.sep, install_mysql_bash)
                install_mysql_bash = re.sub('::db_name::', db_name, install_mysql_bash)
                install_mysql_bash = re.sub('::install_mysql_server::', install_mysql, install_mysql_bash)
                install_mysql_bash = re.sub('::drop_db_if_exists::', drop_db, install_mysql_bash)

                install_mysql_bash_filename =  os.path.join(temp_dir,
                                                               'install_mysql_bash.sh')
                with open(install_mysql_bash_filename, b'w') as bashfile:
                    for line in install_mysql_bash:
                        bashfile.write(line)
                # https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python
                st = os.stat(install_mysql_bash_filename)
                os.chmod(install_mysql_bash_filename, st.st_mode | stat.S_IEXEC)
                # https://stackoverflow.com/questions/436198/what-is-an-alternative-to-execfile-in-python-3
                #exec(open(install_mysql_bash_filename).read())
                bash_log_file = os.path.join(temp_dir, 'zp_mysql_install.log')
                bash_log_error_file = os.path.join(temp_dir, 'zp_mysql_install_error.log')
                sys.stdout.write('%s Calling bash script %s%s' % (date_time(), install_mysql_bash_filename, os.linesep))
                sys.stdout.write('%s Log file will be found %s %s' % (date_time(),
                                                                      bash_log_file,
                                                                      os.linesep))
                sys.stdout.write('%s Error Log file will be found %s %s' % (date_time(),
                                                                            bash_log_error_file,
                                                                      os.linesep))
                # todo add return code
                # todo add first user
                # todo create zerrphix.ini
                bash_log_error_file_handler = open(bash_log_error_file, b'w')
                mysql_root_password = hashlib.sha256(Random.get_random_bytes(256)).hexdigest()[:16]  # this is for flask
                #printed_password = False
                #while printed_password is False:
                #    # make py3 compatible
                #    print_password = input('About to print the mysql root password to the console. You shold not need to'
                #                           ' use it. The plugin for mysql root user is expected to be unix_socket'
                #                           ' which only allows you to login as root by using sudo mysql -u root.'
                #                           ' Enter y when ready and press the return/enter key: [y/n]')
                #    if print_password.lower() == 'y':
                #        sys.stdout.write('%s mysql root password: %s%s' % (date_time(), mysql_root_password, os.linesep))
                #        printed_password = True
                # We do not want to re-direct stdout to a file otherwise we will not see the prompts
                #sys.exit(1)
                return_code = subprocess.call(['bash', install_mysql_bash_filename, mysql_root_password], stderr=bash_log_error_file_handler)
                if return_code == 0:
                    sys.stdout.write('%s Installed and setup db %s' % (date_time(), os.linesep))
                    sys.stdout.write('%s Removing Temporary Files %s' % (date_time(), os.linesep))
                    os.remove(zerrphix_first_install_drop_db_sql_filename)
                    os.remove(zerrphix_first_install_create_db_sql_filename)
                    os.remove(zerrphix_first_install_add_mysql_user_sql_filename)
                    os.remove(zerrphix_first_install_create_tables_sql_filename)
                    os.remove(zerrphix_first_install_populate_tables_sql_filename)
                    os.remove(zerrphix_first_install_post_populate_sql_filename)
                    os.remove(zerrphix_first_install_add_user_sql_filename)
                    os.remove(install_mysql_bash_filename)
                    sys.stdout.write('%s Install completed %s' % (date_time(), os.linesep))
                    sys.stdout.write('%s Please run %s%s%s start%s%sto start zerrphix program%s' % (date_time(),
                                                                                                    os.linesep,
                                                                                                    os.linesep,
                                                                                                    sys.argv[0],
                                                                                                    os.linesep,
                                                                                                    os.linesep,
                                                                                                    os.linesep))
                    bash_log_error_file_handler.close()
                    if os.path.exists(bash_log_error_file):
                        os.remove(bash_log_error_file)
                    if os.path.exists(bash_log_file):
                        os.remove(bash_log_file)
                else:
                    bash_log_error_file_handler.close()
                    if os.path.exists(bash_log_error_file):
                        with open(bash_log_error_file, b'r') as bash_log_error_file_f:
                            for line in bash_log_error_file_f.readlines():
                                sys.stderr.write(line)
                    sys.stderr.write('%s Bash script encountered an error. Please look at'
                                     ' %s and %s%s' % (date_time(), bash_log_error_file, bash_log_file, os.linesep))
        else:
            usage()
    else:
        usage()

    #print('Press enter to show the terminal/console prompt\r')



# except (IOError, ValueError) as e:
#
#	if any(arg in ['debug', '--debug'] for arg in [a.lower() for a in sys.argv]):
#		import traceback
#		traceback.print_exc()
#	else:
#		print('Could not instantiate manager: {0}'.format(e), file=sys.stderr)
#		traceback.print_exc()
#	sys.exit(1)

# https://blog.openshift.com/use-flask-login-to-add-user-authentication-to-your-python-application/
