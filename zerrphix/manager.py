# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, absolute_import, print_function

# from zerrphix.db.tables import TABLES
import logging

from zerrphix.config import get_global_config_dict
from zerrphix.config import load_config
from zerrphix.db import setup_db
from zerrphix.film import FILM
from zerrphix.httpserver.dune import DuneHTTPSvr
from zerrphix.httpserver.admin import AdminHTTPSvr
from zerrphix.tv import TV
#from zerrphix.util import smbfs_connection_dict_dune
#from zerrphix.util.db import DBCommon
from zerrphix.db.tables import TABLES
from zerrphix.db import commit
from zerrphix.db import construct_connection_string
from zerrphix.db import setup_engine
from sqlalchemy import orm
from datetime import datetime
from zerrphix.util.filesystem import make_dir, smbfs
from hashlib import sha256
import tarfile
from pkg_resources import resource_filename
from zerrphix.util.text import date_time
#from zerrphix.util.image_store import c
import os
import tempfile
import traceback
import threading
import time
from zerrphix import logger
from types import MethodType
from datetime import timedelta
from zerrphix.util.network import private_listen_address_list
import sys
from sqlalchemy import exc
from alembic import command
from alembic.config import Config as AlConfig
import pprint
#from alembic.migration import MigrationContext
#from sqlalchemy import create_engine

log = logging.getLogger(__name__)

# threading http://stackoverflow.com/questions/268629/how-to-stop-basehttpserver-serve-forever-in-a-basehttprequesthandler-subclass
# http://stackoverflow.com/questions/473620/how-do-you-create-a-daemon-in-python
# http://stackoverflow.com/questions/17035077/python-logging-to-multiple-log-files-from-different-classes
# https://blog.petrzemek.net/2014/03/23/restarting-a-python-script-within-itself/
# http://stackoverflow.com/questions/4330111/python-thread-daemon-property
# http://www.bogotobogo.com/python/Multithread/python_multithreading_Daemon_join_method_threads.php
# http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
# http://stackoverflow.com/questions/6524459/stopping-a-thread-after-a-certain-amount-of-time
# http://stackoverflow.com/questions/10705680/how-can-i-restart-a-basehttpserver-instance
# http://stackoverflow.com/questions/13497330/proper-way-to-restart-http-server-in-python
# https://stackoverflow.com/questions/29681326/sqlalchemy-in-multithread-scoped-session
# https://stackoverflow.com/questions/20056300/python-print-output-of-each-thread-to-seperate-file-no-processes
# http://docs.python.org/2/howto/logging.html#logging-advanced-tutorial

# restarting thread
# http://www.ianbicking.org/blog/2007/09/re-raising-exceptions.html
# https://stackoverflow.com/questions/29692250/restarting-a-thread-in-python
# def threadwrap(threadfunc):
#    def wrapper():
#        while True:
#            try:
#                threadfunc()
#            except BaseException as e:
#                print('{!r}; restarting thread'.format(e))
#            else:
#                print('exited normally, bad thread; restarting')
#    return wrapper
#
#thread_dict = {
#    'a': threading.Thread(target=wrapper(a), name='a'),
#    'b': threading.Thread(target=wrapper(b), name='b')
#}
#
class Manager(object):
    """Manager class for FlexGet

    """

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
        self.pidfile_path = '/tmp/zerrphix.pid'
        self.pidfile_timeout = 5
        self.args = args
        #self.library_config_dict = {}
        #self.create_root_download_folder = MethodType(create_root_download_folder, self)
        try:
            self.global_config_dict = get_global_config_dict(self.args)
        except:
            logger.start(console_level=logger.TRACE, to_file=False)
            # re-raise the exception from
            raise
        # print(self.global_config_dict)



    # TODO: add new plugins to db

    # self.config = {}
    """
    https://stackoverflow.com/questions/8236647/after-i-create-my-tables-using-sqlalchemy-how-can-i-add-additional-columns-to-i
    You can add column with Table.append_column method.

    test = Column('test', Integer)
    User.__table__.append(test)
    But this will not fire the ALTER TABLE command to add that column in database. As per doc given for append_column that command you have to run manually after adding that column in model.
    """

    # This function allows the function passed to it to be restarted if it dies.
    def threadWrapper(self, func, threadName, source_id, **kwargs):
        while True:
            try:
                func(**kwargs)
            except Exception as e:
                traceback_string = traceback.format_exc()
                log.exception('inner function %s exited with exception %s for thread %s', func.__name__, traceback_string,
                              threadName)
                session = self.Session()
                date_time_yesterday = date_time(timedelta(days=1))
                text = str(e)
                try:
                    zp_db_log = session.query(
                        TABLES.ZP_DB_LOG
                    ).filter(
                        TABLES.ZP_DB_LOG.TEXT==text,
                        TABLES.ZP_DB_LOG.TRACEBACK==traceback_string,
                        TABLES.ZP_DB_LOG.SOURCE_ID==source_id,
                        TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME > date_time_yesterday,
                        TABLES.ZP_DB_LOG.LEVEL == 60
                    ).order_by(TABLES.ZP_DB_LOG.LAST_OCCURRENCE_DATE_TIME.desc()).limit(1).one()
                except orm.exc.NoResultFound:
                    add_zp_db_log = TABLES.ZP_DB_LOG(
                        EPOCH='{:0.8f}'.format((datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()),
                        TEXT=text,
                        TRACEBACK=traceback_string,
                        COUNT_24=1,
                        SOURCE_ID=source_id,
                        FIRST_OCCURRENCE_DATE_TIME = date_time(),
                        LAST_OCCURRENCE_DATE_TIME = date_time(),
                        LEVEL=60
                    )
                    session.add(add_zp_db_log)
                    commit(session)
                else:
                    zp_db_log.COUNT_24 += 1
                    zp_db_log.LAST_OCCURRENCE_DATE_TIME = date_time()
                    commit(session)
                session.close()
                log.info('sleeping 30 seconds before starting thread %s inner function %s', threadName,
                         func.__name__)
            else:
                log.error('inner function %s exited for unknown reason. This should not happen. Please check logs for'
                          'last entry before this message for this thread %s', threadName)
                session = self.Session()
                new_error = TABLES.ZP_ERROR_RAISED(TEXT='inner function %s exited for unknown reason. '
                                                                      'This should not happen. Please check logs for'
                                                                      'last entry before this message for this thread '
                                                                      '%s',
                                                           SOURCE_ID=source_id)
                session.add(new_error)
                commit(session)
                session.close()
                log.info('sleeping 30 seconds before starting thread %s inner function %s', threadName,
                         func.__name__)
            time.sleep(30)

    def run(self):
        # We have to the main file logger here as the deamon process creats a forked process and if this is done
        # in manager init then we get a illegal seek as the descriptor is lost/destroyed
        log_file = os.path.expanduser(self.global_config_dict['log_file_path'])
        # If an absolute path is not specified, use the config directory.
        if not os.path.isabs(log_file):
            log_file = os.path.join(self.global_config_dict['config_dirname'], log_file)

        logger.start(file_path=log_file,
                     file_level=self.global_config_dict['log_file_level'].upper(),
                     to_console=self.global_config_dict['log_to_console'],
                     console_level=self.global_config_dict['log_to_console_level'].upper(),
                     maxBytes=self.global_config_dict['log_file_maxbytes'],
                     backupCount=self.global_config_dict['log_file_backupCount'],
                     compression=self.global_config_dict['log_to_file_compression'])
        #logger.initializesss(self.args)
        #log.debug('adasdadasdasd')
        #time.sleep(222)
        log.info('main called with args: {0}'.format(self.args))
        log.info('args {0}'.format(self.args))
        log.debug('getting config')
        self.config, self.config_root_dir = load_config(self.args)
        log.debug('got config')
        ##if self.create_root_download_folder() is True:
        log.debug('setting up db connection')
        log.debug('setting up alembic')
        db_config_dict = dict(self.config.items('database'))
        db_echo = False
        if 'echo' in db_config_dict:
            if db_config_dict['echo'].lower() == 'true':
                db_echo = True
        connection_string = construct_connection_string(self.config_root_dir, db_config_dict)
        # https://stackoverflow.com/questions/24622170/using-alembic-api-from-inside-application-code
        # https://stackoverflow.com/questions/37311214/how-i-can-disable-alembic-logging-at-runtime
        ## alembic upgrade head

        #engine = setup_engine(connection_string)
        #conn = engine.connect()
        #context = MigrationContext.configure(conn)
        #alembic_cfg = Config(os.path.join(self.config_root_dir, "alembic.ini"))
        #command.stamp(alembic_cfg, "head")

        #alembic_cfg = Config(os.path.join(self.config_root_dir, "alembic.ini"))
        alembic_cfg = AlConfig()
        alembic_cfg.set_main_option("script_location", "zerrphix:alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", connection_string)
        #alembic_cfg.set_section_option("", "", "")
        #alembic_cfg.set_section_option("loggers", "keys", "root,sqlalchemy,alembic")
        #alembic_cfg.set_section_option("handlers", "keys", "console")
        #alembic_cfg.set_section_option("formatters", "keys", "generic")
        #alembic_cfg.set_section_option("logger_root", "level", "WARN")
        #alembic_cfg.set_section_option("logger_root", "handlers", "console")
        #alembic_cfg.set_section_option("logger_root", "qualname", "")
        #alembic_cfg.set_section_option("logger_sqlalchemy", "level", "WARN")
        #alembic_cfg.set_section_option("logger_sqlalchemy", "handlers", "")
        #alembic_cfg.set_section_option("logger_sqlalchemy", "qualname", "sqlalchemy.engine")
        #alembic_cfg.set_section_option("handler_console", "class", "StreamHandler")
        #alembic_cfg.set_section_option("handler_console", "args", "(sys.stderr,)")
        #alembic_cfg.set_section_option("handler_console", "level", "INFO")
        #alembic_cfg.set_section_option("handler_console", "formatter", "generic")
        #alembic_cfg.set_section_option("formatter_generic", "format", "%%(levelname)-5.5s [%%(name)s] %%(message)s")
        #alembic_cfg.set_section_option("formatter_generic", "datefmt", "%%H:%%M:%%S")
        #setattr(alembic_cfg.cmd_opts, 'upgrade', 'head')
        #alembic_cfg.set_main_option('script_location', alembic_directory)
        #alembic_cfg.set_main_option('script_location', '/home/zerrphix/zerrphix/alembic')
        #alembic_cfg.cmd_opts = argparse.Namespace()  # arguments stub
        #alembic_cfg..cmd_opts =

        # If it is required to pass -x parameters to alembic
        #x_arg = 'user_parameter=' + user_parameter
        #if not hasattr(alembic_cfg.cmd_opts, 'x'):
        #    if x_arg is not None:
        #        setattr(alembic_cfg.cmd_opts, 'x', [])
        #        if isinstance(x_arg, list) or isinstance(x_arg, tuple):
        #            for x in x_arg:
        #                alembic_cfg.cmd_opts.x.append(x)
        #        else:
        #            alembic_cfg.cmd_opts.x.append(x_arg)
        #    else:
        #        setattr(alembic_cfg.cmd_opts, 'x', None)

        # prepare and run the command
        #log.error('running alembic')
        logging.getLogger('alembic').setLevel(logging.WARNING)
        #for handler in logging.getLogger('alembic').handlers:
        #    print(handler)
        ##revision = 'head'
        #sql = False
        #tag = None
        command.upgrade(alembic_cfg, 'head')
        #for handler in logging.getLogger('alembic').handlers:
        #    print(handler)
        #print(command.stamp(alembic_cfg, revision, sql=sql, tag=tag))

        # upgrade command
        #print(command.upgrade(alembic_cfg, revision, sql=sql, tag=tag))
        ##
        log.debug('alembic completed (schema upgrade)')
        print('alembic completed (schema upgrade)')

        #time.sleep(30000)
        #raise SystemExit('alembic completed')
        try:
            self.Session = setup_db(connection_string, db_echo)
        except exc.OperationalError as e:
            log.error('OperationalError %s', str(e))
            print('OperationalError %s' % str(e))
            print('Exiting')
            sys.exit(1)
        else:
            log.debug('set up db connection')
            ##self.make_render_root_dir()
            #self.make_temp_download_dir()
            ##self.make_user_uploaded_images_root_dir_path()
            template_file_path = resource_filename('zerrphix', 'templates.tar.gz')
            with open(template_file_path) as template_file:
                template_file_sha256sum = sha256(template_file.read()).hexdigest()
            log.debug('calc template_file_sha256sum %s', template_file_sha256sum)
            session = self.Session()
            zp_template = session.query(TABLES.ZP_TEMPLATE).filter(
                TABLES.ZP_TEMPLATE.ID == 1
            ).one()
            log.debug('db template_file_sha256sum %s', zp_template.CURRENT_SHA256)
            if zp_template.CURRENT_SHA256 != template_file_sha256sum:
                template_file_archve = tarfile.open(template_file_path)
                print('Updating default temaplte(s)')
                template_file_archve.extractall(self.global_config_dict['template_store_path'])
                zp_template.CURRENT_SHA256 = template_file_sha256sum
                zp_template.LAST_MOD_DATETIME = date_time()
                commit(session)
            session.close()
            #if '--film' in self.args or '-f' in self.args:
            #log.debug('--film or -f in args: {0}'.format(self.args))
            kwargs = {'args': self.args,
                      'Session': self.Session,
                      'global_config_dict': self.global_config_dict}
            film = FILM(**kwargs)
            #film.run()
            #film_thread = threading.Thread(target=film.run, name='filmThread')
            film_thread = threading.Thread(target=self.threadWrapper, args=[film.run, 'filmThread', 1], name='filmThread')
            film_thread.daemon = True

            #if '--tv' in self.args or '-t' in self.args:
            #log.debug('--tv or -t in args: {0}'.format(self.args))
            tv = TV(**kwargs)
            #tv.run()
            # tv_thread = threading.Thread(target=tv.run, name='tvThread')
            tv_thread = threading.Thread(target=self.threadWrapper, args=[tv.run, 'tvThread', 2], name='tvThread')
            tv_thread.daemon = True

            #if '--dunehttpserver' in self.args or '-dht' in self.args:
            #log.debug('--httpserver or -ht in args: {0}'.format(self.args))
            dunehttpserver = DuneHTTPSvr(self.Session, self.global_config_dict)
            #dunehttpserver.run()
            #dunehttpserver_thread = threading.Thread(target=dunehttpserver.run, name='dhtpThread')
            dunehttpserver_thread = threading.Thread(target=self.threadWrapper,
                                                     args=[dunehttpserver.run, 'dhtpThread', 3], name='dhtpThread')
            dunehttpserver_thread.daemon = True

            #if '--adminhttpserver' in self.args or '-aht' in self.args:
            #log.debug('--httpserver or -ht in args: {0}'.format(self.args))
            adminhttpserver = AdminHTTPSvr(self.args, self.Session, self.global_config_dict)
            #adminhttpserver.app.run(threaded=True, host="0.0.0.0", port=9001, debug=True)
            #adminhttpserver.app.run()
            #adminhttpserver_thread = threading.Thread(target=adminhttpserver.app.run, name='ahtpThread', kwargs={'threaded':True,
            #                                                                                      'host': "0.0.0.0",
            #                                                                                      'port': 9001,
            #                                                                                      'debug': True,
            #                                                                                    'use_reloader': False})
            adminhttpserver_thread = threading.Thread(target=self.threadWrapper, name='ahtpThread',
                                                      args=[adminhttpserver.app.run, 'ahtpThread', 4],
                                                      kwargs={'threaded':True,
                                                              'host': self.global_config_dict['admin_http_server_listen_ip'],
                                                              'port': self.global_config_dict['admin_http_server_listen_port'],
                                                              'debug': self.global_config_dict['admin_http_server_debug'],
                                                              'use_reloader': False})
            adminhttpserver_thread.daemon = True

            #if '-a' in self.args:
            #    for i in range(1, 5):
            #        log.debug(i)
            #        if i == 1:
            #            film = FILM(self.args, self.config, self.config_root_dir, self.Session, self.global_config_dict)
            #            film.run()


            film_thread.start()
            print('Film Thread Starts')
            log.debug('starting tv thread')
            tv_thread.start()
            print('TV Thread Starts')
            log.debug('started tv thread')
            log.debug('starting dunehttp thread')
            dunehttpserver_thread.start()
            dune_http_server_announce_string = 'DUNE HTTP Server on Listening %s:%s Starts. Url(s):' % (
                  self.global_config_dict['dune_http_server_listen_ip'],
                  self.global_config_dict['dune_http_server_listen_port'])
            if self.global_config_dict['dune_http_server_listen_ip'] == '0.0.0.0':
                for ip in private_listen_address_list():
                    dune_http_server_announce_string += ' http://%s:%s'% (
                        ip,
                    self.global_config_dict['dune_http_server_listen_port'])
            else:
                dune_http_server_announce_string += ' http://%s:%s' % (
                    self.global_config_dict['dune_http_server_listen_ip'],
                    self.global_config_dict['dune_http_server_listen_port'])
            print(dune_http_server_announce_string.strip())
            log.debug('started dunehttp thread')
            log.debug('starting adminhttp thread')
            adminhttpserver_thread.start()
            admin_http_server_announce_string = 'ADMIN HTTP Server on Listening %s:%s Starts. Url(s):' % (
                  self.global_config_dict['admin_http_server_listen_ip'],
                  self.global_config_dict['admin_http_server_listen_port'])
            if self.global_config_dict['admin_http_server_listen_ip'] == '0.0.0.0':
                for ip in private_listen_address_list():
                    admin_http_server_announce_string += ' http://%s:%s'% (
                        ip,
                    self.global_config_dict['admin_http_server_listen_port'])
            else:
                admin_http_server_announce_string += ' http://%s:%s' % (
                    self.global_config_dict['admin_http_server_listen_ip'],
                    self.global_config_dict['admin_http_server_listen_port'])
            print(admin_http_server_announce_string.strip())
            log.debug('started adminhttp thread')
            log.debug('All threads started')
            print('Press enter to show the terminal/console prompt\r')
            while True:
                time.sleep(60)
        #else:
        #    log.critical('cannot create_root_download_folder dir %s',
        #                 self.global_config_dict['downloaded_images_root_path'])

    #def make_temp_download_dir(self):
    #    if self.global_config_dict['keep_downloaded_images'] is False:
    #        self.global_config_dict['keep_downloaded_images_temp_dir'] = tempfile.mkdtemp()

    #def make_user_uploaded_images_root_dir_pathh(self):
    #    if make_dir(self.global_config_dict['user_uploaded_images_root_dir_path']):
    #        root_entity_list = ['film', 'film_collection', 'tv']
    #        for root_entity in root_entity_list:
    #            make_dir(os.path.join(self.global_config_dict['user_uploaded_images_root_dir_path'], root_entity))
