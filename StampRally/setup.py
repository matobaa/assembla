#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys

setup(
    name='StampRally',
    version='0.1',
    license='Not Specified Yet, Copyright (c) by matobaa',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='indicate who and when change ticket\'s status',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
    package_data={ 'stamprally': [
                      'templates/*.html',
                      'htdocs/*/*'] },
    entry_points={
        'trac.plugins': 'StampRally = stamprally.ticket'
        },
    )
