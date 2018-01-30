#!  /usr/bin/python3
# -*- coding: utf-8 -*-
''' dontwi is a status transporter script from Mastodon instances to Twitter.

See:
https://github.com/vocalodon/dontwi
'''
from setuptools import setup, find_packages
from os import path
from dontwi.version import __version__

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='dontwi',
    version=__version__,
    description='A status transporter from Mastodon instances to Twitter',
    author='A.Shiomaneki',
    author_email='a.shiomaneki@gmail.com',
    url='https://github.com/vocalodon/dontwi',
    long_description=long_description,
    license='GNU General Public License v3.0',
    packages=['dontwi'],
    test_suite='dontwi.tests'
)
