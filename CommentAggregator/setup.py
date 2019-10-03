#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='CommentAggregator',
    version='0.1',
    license='Not Decided yet; now under development; will be Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='aggregate changes in ticket history',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
#    package_data={ 'commentaggregator': [
#                      'templates/*.html',
#                      'htdocs/*/*'] },
    entry_points={
        'trac.plugins': 'CommentAggregator = commentaggregator.ticket'
        },
    )
