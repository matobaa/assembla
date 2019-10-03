# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider


class Handler(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('numberlisttoticketlist', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'search.html':
            return stream
        add_script(req, 'numberlisttoticketlist/js/onsubmit.js')
        add_script(req, 'common/js/resizer.js')
        return stream | Transformer('//div[@id="help"]').before(
            tag.form(tag.textarea(rows='5', cols='40', class_='trac-resizable'),
                     tag.input(type='submit', value='Show ticket list'), id='extsearch', action='#'))
