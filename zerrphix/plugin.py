# -*- coding: utf-8 -*-
import logging
import os

from path import Path

import zerrphix.plugins as plugins_pkg
from zerrphix.config import get_user_plugins_dir
from zerrphix.util.filesystem import strip_trailing_sep

log = logging.getLogger(__name__)


class DependencyError(Exception):
    """Plugin depends on other plugin, but it cannot be loaded.
    Args:
        issued_by: name of the plugin trying to do the import
        missing: name of the plugin or library that is missing
        message: user readable error message
    All args are optional.
    """

    def __init__(self, issued_by=None, missing=None, message=None, silent=False):
        super(DependencyError, self).__init__()
        self.issued_by = issued_by
        self.missing = missing
        self._message = message
        self.silent = silent

    def _get_message(self):
        if self._message:
            return self._message
        else:
            return 'Plugin `%s` requires dependency `%s`' % (self.issued_by, self.missing)

    def _set_message(self, message):
        self._message = message

    def has_message(self):
        return self._message is not None

    message = property(_get_message, _set_message)

    def __str__(self):
        return '<DependencyError(issued_by=%r,missing=%r,message=%r,silent=%r)>' % \
               (self.issued_by, self.missing, self.message, self.silent)


def _get_buitin_plugins_path():
    """
    :returns: List of directories where plugins should be tried to load from.
    """
    # Get basic path from environment
    paths = []

    # Add zerrphix.plugins directory (core plugins)
    paths.append(os.path.abspath(os.path.dirname(plugins_pkg.__file__)))
    log.debug('plugins_pkg.__file__ %s' % plugins_pkg.__file__)
    log.debug('os.path.dirname(plugins_pkg.__file__) %s' % os.path.dirname(plugins_pkg.__file__))
    log.debug('os.path.abspath(os.path.dirname(plugins_pkg.__file__)) %s' % os.path.abspath(os.path.dirname(plugins_pkg.__file__)))
    return paths


def load_plugins(args, extra_dirs=None):
    """
    Load plugins from the standard plugin paths.
    :param list extra_dirs: Extra directories from where plugins are loaded.
    """
    # global plugins_loaded

    if not extra_dirs:
        extra_dirs = []

    # Add zerrphix.plugins directory (core plugins)
    extra_dirs.extend(_get_buitin_plugins_path())

    # start_time = time.time()
    # Import all the plugins
    loaded_plugins = []

    # user_plugins_dir = get_user_plugins_dir(args)

    user_plugins_dir = get_user_plugins_dir(args)

    log.debug('user_plugins_dir: {0}'.format(user_plugins_dir))

    if user_plugins_dir is not None:
        extra_dirs.append(user_plugins_dir)

    loaded_plugins.extend(_load_plugins_from_dirs(extra_dirs))
    # _load_plugins_from_packages()
    # Register them
    # fire_event('plugin.register')
    # Plugins should only be registered once, remove their handlers after
    # remove_event_handlers('plugin.register')
    # After they have all been registered, instantiate them
    # for plugin in list(plugins.values()):
    # plugin.initialize()
    # took = time.time() - start_time
    # plugins_loaded = True
    # log.debug('Plugins took %.2f seconds to load. %s plugins in registry.', took, len(plugins.keys()))

    return loaded_plugins


def _load_plugins_from_dirs(dirs):
    """
    :param list dirs: Directories from where plugins are loaded from
    """

    loaded_plugins = []

    log.debug('Trying to load plugins from: {0}'.format(dirs))
    dirs = [Path(os.path.normpath(d)) for d in dirs if os.path.isdir(d)]

    # print('dirs', dirs)
    # add all dirs to plugins_pkg load path so that imports work properly from any of the plugin dirs
    plugins_pkg.__path__ = list(map(strip_trailing_sep, dirs))
    # print('plugins_pkg.__path__', plugins_pkg.__path__)
    for plugins_dir in dirs:
        for plugin_path in plugins_dir.walkfiles('*.py'):
            log.debug('plugin_path.name %s', plugin_path.name)
            if plugin_path.name == '__init__.py':
                continue
            # Split the relative path from the plugins dir to current file's parent dir to find subpackage names
            plugin_subpackages = [_f for _f in plugin_path.relpath(plugins_dir).parent.splitall() if _f]
            module_name = '.'.join([plugins_pkg.__name__] + plugin_subpackages + [plugin_path.namebase])
            # print('module_name', module_name)
            try:
                __import__(module_name)
            except DependencyError as e:
                if e.has_message():
                    msg = str(e)
                else:
                    msg = 'Plugin `%s` requires `%s` to load.', e.issued_by or module_name, e.missing or 'N/A'
                if not e.silent:
                    log.warning(msg)
                else:
                    log.error(msg)
            except ImportError:
                log.critical('Plugin `%s` failed to import dependencies', module_name, exc_info=True)
            except ValueError as e:
                # Debugging #2755
                log.error('ValueError attempting to import `%s` (from %s): %s', module_name, plugin_path, e)
            except Exception:
                log.critical('Exception while loading plugin %s', module_name, exc_info=True)
                raise
            else:
                log.debug('Loaded module %s from %s', module_name, plugin_path)
                loaded_plugins.append(module_name)

    return loaded_plugins
    # _check_phase_queue()
