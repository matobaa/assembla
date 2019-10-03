#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TicketCountTable'
VERSION = '0.0.6'

setup(
    name=PACKAGE, version=VERSION,
    description='The easy ticket number of cases is totaled by two specified items.',
    author="", author_email="",
    license='NewBSD', url='',
    zip_safe=True,
    packages = ['ticketcounttable'],
    entry_points = {
        'trac.plugins': [
            'ticketcounttable.TicketCountTable = ticketcounttable.TicketCountTable',
        ]
    }
)
