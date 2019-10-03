#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='InterTracForTicket',
    version=version,
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='TODO: Describe here',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    entry_points={
        'trac.plugins': [
            'InterTracForTicketPlugin = intertracforticket.wrapper',
        ],
    },
)
