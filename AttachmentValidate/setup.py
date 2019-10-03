#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys

setup(
    name='AttachmentValidate',
    version='0.1',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/AttachmentValidatePlugin',
    description='validates attachments are exist or not',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    #package_data={
    #    'attachmentvalidate': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css']
    #    },
    entry_points={
        'trac.plugins': 'AttachmentValidate = attachmentvalidate.console'
        },
    )
