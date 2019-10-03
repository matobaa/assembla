#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from genshi.core import Markup
from trac.core import implements, Component
from trac.resource import Resource, get_resource_url
from trac.util.translation import _
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_ctxtnav


class VersionFix(Component):
    """ fix specified version on URL """
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if 'ticket' in data:
            latest = max([0] + [int(c[3]) for c in data['ticket'].get_changelog() if c[2] == u'comment' and c[3]!=u''])
            ticket = data['ticket'].resource
            if ticket.version == None:  # showing latest version, add fix-version link
                add_ctxtnav(req, _('Ticket History'), '?version=%s' % latest)
            else:  # showing specified version; add latest-version link
                r, i, v = ticket.realm, ticket.id, ticket.version
                prev_link, next_link = None, None
                if v > 0:
                    prev_link = tag.a(_('Previous Version'),
                                      href=get_resource_url(self.env, Resource(r, i, v - 1), req.href),
                                      class_='prev')
                if v < latest:
                    next_link = tag.a(_('Next Version'),
                                      href=get_resource_url(self.env, Resource(r, i, v + 1), req.href),
                                      class_='next')

                add_ctxtnav(req, tag.span(Markup('&larr; '), prev_link or _('Previous Version'),
                                          class_=not prev_link and 'missing' or None))
                add_ctxtnav(req, tag.a(_('View Latest Version'),
                                       href=get_resource_url(self.env, Resource(r, i, None), req.href)))
                add_ctxtnav(req, tag.span(next_link or _('Next Version'), Markup(' &rarr;'),
                                          class_=not next_link and 'missing' or None))
        return stream
