#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

# from genshi.builder import tag
# from genshi.core import Markup
from trac.core import implements, Component
from trac.resource import Resource, get_resource_url
from trac.util.translation import _
from trac.util.html import Markup, tag
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_ctxtnav

class VersionNavi(Component):
    """ fix specified version on URL """
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if 'ticket' in data:
            latest = max([0] + [int(c[3]) for c in data['ticket'].get_changelog() if c[2] == u'comment' and c[3]!=u''])
            ticket = data['ticket'].resource
            if ticket.version == None:  # showing latest version, add fix-version link
                add_ctxtnav(req, _('Previous Version'), '?version=%s' % latest)
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



    def _render_history(self, req, page):
        """Extract the complete history for a given page.

        This information is used to present a changelog/history for a given
        page.
        """
        if not page.exists:
            raise TracError(_("Page %(name)s does not exist", name=page.name))

        data = self._page_data(req, page, 'history')

        history = []
        for version, date, author, comment in page.get_history():
            history.append({
                'version': version,
                'date': date,
                'author': author,
                'comment': comment or ''
            })
        data.update({
            'history': history,
            'resource': page.resource,
            'can_edit_comment': 'WIKI_ADMIN' in req.perm(page.resource)
        })
        add_ctxtnav(req, _("Back to %(wikipage)s", wikipage=page.name),
                    req.href.wiki(page.name))
        return 'history_view.html', data