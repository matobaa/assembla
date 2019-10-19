# -*- coding: utf-8 -*-

from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, ITemplateProvider


class Handler(Component):
    implements(IRequestFilter, ITemplateProvider)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('numberlisttoticketlist', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'search.html':
            add_script(req, 'numberlisttoticketlist/js/onsubmit.js')
            add_script(req, 'common/js/resizer.js')
        return template, data, content_type
