#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version='0.4'

setup(
    name='DotLog',
    version=version,
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='timestamp and focus on last automatically in ".LOG" page, like windows notepad',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={ 'dotlog': ['htdocs/*/*'] },
    entry_points={
        'trac.plugins': [
            'DotLog = dotlog.wiki',
        ]
    },
)