# setuptools in python2 does not like unicode_literals
from __future__ import division, absolute_import
import io
import sys

from setuptools import setup, find_packages

with io.open('README.rst', encoding='utf-8') as readme:
    long_description = readme.read()

# Populates __version__ without importing the package
__version__ = None
with io.open('zerrphix/_version.py', encoding='utf-8')as ver_file:
    exec (ver_file.read())  # pylint: disable=W0122
if not __version__:
    print('Could not find __version__ from zerrphix/_version.py')
    sys.exit(1)


def load_requirements(filename):
    with io.open(filename, encoding='utf-8') as reqfile:
        return [line.strip() for line in reqfile if not line.startswith('#')]

# https://stackoverflow.com/questions/7522250/how-to-include-package-data-with-setuptools-distribute
setup(
    name='zerrphix',
    version=__version__,
    description='Zerrphix is for HDI DUNE network media players that can utilise the dune_http://'
                ' functionality',
    long_description=long_description,
    author='Zerrphix Project',
    author_email='zerrphix.project@gmail.com',
    license='MIT',
    url='https://github.com/3lixy/Zerrphix',
    #download_url = 'https://github.com/3lixy/Zerrphix/archive/zerrphix-%s.tar.gz' % __version__,
    packages=find_packages(),
    package_data={
        'zerrphix': [
            'templates.tar.gz'
        ],
        'zerrphix.alembic': [
            'script.py.mako',
            'README'
        ],
        'zerrphix.httpserver.admin': [
            'templates/*',
            'templates/dunes/*',
            'templates/film/*',
            'templates/film_collection/*',
            'templates/process/*',
            'templates/report/*',
            'templates/scan_paths/*',
            'templates/settings/*',
            'templates/template/*',
            'templates/tv/*',
            '*.css',
            '*.woff*',
            '*.js'],
    },
    include_package_data=True,
    data_files=[
        ('zerrphix', ['zerrphix/templates.tar.gz',
                      'zerrphix/logo.png'
                      ]),
        ('zerrphix/alembic', ['zerrphix/alembic/README',
                              'zerrphix/alembic/script.py.mako'
                      ]),
        ('zerrphix/httpserver/admin', ['zerrphix/httpserver/admin/font-awesome.min.css',
                                       'zerrphix/httpserver/admin/fontawesome-webfont.woff',
                                       'zerrphix/httpserver/admin/fontawesome-webfont.woff2',
                                       'zerrphix/httpserver/admin/w3.css',
                                       'zerrphix/httpserver/admin/jquery.js'
                                       ])
    ],
    zip_safe=False,
    install_requires=load_requirements('requirements.txt'),
    #tests_require=['pytest'],
    #extras_require={
    #    'dev': load_requirements('dev-requirements.txt')
    #},
    entry_points={
        'console_scripts': ['zerrphix = zerrphix:main'],
        #'gui_scripts': ['zerrphix-headless = zerrphix:main']  # This is useful on Windows to avoid a cmd popup
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7"
    ]
)