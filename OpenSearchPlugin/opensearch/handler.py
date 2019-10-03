#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.prefs.api import IPreferencePanelProvider
from trac.search.web_ui import SearchModule
from trac.util.datefmt import parse_date, http_date
from trac.util.translation import _
from trac.web.api import ITemplateStreamFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider
from urlparse import urlsplit, urlunsplit


class OpenSeachProvider(Component):
    """OpenSearch Provider, OpenService Accelerator, Federated Search in Windows"""
    implements(ITemplateStreamFilter, IRequestHandler, ITemplateProvider, IPreferencePanelProvider)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('opensearch', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [ResourceManager().resource_filename(__name__, 'templates')]

    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        yield ('opensearch', _('Search'))

    def render_preference_panel(self, req, panel):
        return 'prefs_opensearch.html', {}

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'opensearch.xml':
            # Modify opensearch.xml to add suggest and Federated search
            return stream | Transformer('//OpenSearchDescription') \
                .append(tag.Url(type="application/x-suggestions+xml",
                                template="%s?q={searchTerms}&noquickjump=1" %
                                req.abs_href('/search/suggest'))) \
                .append(tag.Url(type="application/rss+xml",
                                template="%s?q={searchTerms}&noquickjump=1" %
                                req.abs_href('/search/feed')))
        return stream

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ['/search/suggest', '/search/feed', '/search/accelerator', '/search/2010.imesx']

    def process_request(self, req):
        if req.path_info == '/search/2010.imesx':
            return ('imesx.xml', {}, 'application/opensearchdescription+xml')
            # see Also: http://social.technet.microsoft.com/Forums/ja-JP/999dabfc-1a3d-44a9-84ef-295e8ba983fa
        if req.path_info == '/search/accelerator':
            return ('accelerator.xml', {},
                    'application/opensearchdescription+xml')
        handler = self.compmgr[SearchModule]
        template_name, data, content_type = handler.process_request(req)  # @UnusedVariable
        if req.path_info == '/search/suggest':
            return 'suggest.xml', data, "application/x-suggestions+xml"
            # See Also: http://msdn.microsoft.com/ja-jp/library/cc848862(v=vs.85).aspx for open search
        elif req.path_info == '/search/feed':
            scheme, netloc, p, q, f = urlsplit(req.abs_href.base)  # @UnusedVariable
            data['scheme_netloc'] = urlunsplit((scheme, netloc, '', None, None))
            data['rfc822'] = lambda date: http_date(parse_date(date, locale=req.lc_time))
            return 'feed.xml', data, "application/rss+xml"
            # See Also: http://msdn.microsoft.com/en-us/library/dd742958(v=vs.85).aspx for federated search
