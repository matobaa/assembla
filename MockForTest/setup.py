#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='MockForTest',
    version=version,
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='for test',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
#    package_data={ 'mockfortest': ['htdocs/*/*'] },
    entry_points={
        'trac.plugins': [
            'TestSender = tester.sender',
        ],
    },
)
