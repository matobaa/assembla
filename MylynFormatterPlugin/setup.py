#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='MylynFormatter',
    version=version,
    classifiers=['Development Status :: 4 - Beta',
                 'Framework :: Trac'],
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='TODO: Write here',
    zip_safe=True,
#     packages=find_packages(exclude=['*.tests']),
#     package_data={'mylynformatter': ['templates/**']},
    entry_points={
        'trac.plugins': [
            'Mylynformatter = mylynformatter.mylynformatter',
        ]
    },
)
