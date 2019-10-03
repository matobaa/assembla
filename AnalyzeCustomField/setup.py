#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='AnalyzeCustomField',
    version='0.2',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='Analyze Custom Field',
    zip_safe=False,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
    package_data={ 'analyzecustomfield': [
                      'templates/*.html'] },
    entry_points={
        'trac.plugins': [
            'AnalyzeCustomField = analyzecustomfield.admin'
        ]
    },
)