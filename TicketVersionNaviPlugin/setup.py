#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='TicketVersionNavi',
    version=version,
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='https://trac.assembla.com/matobaa',
    description='Add navigation for ticket version',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
#    package_data={'ticketversionnavi': ['htdocs/*/*']},
    entry_points={
        'trac.plugins': [
            'TicketVersionNavi.Navi = ticketversionnavi.navi',
        ]
    },
)
