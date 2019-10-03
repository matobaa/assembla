#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome

class Report(Component):
    implements(ITemplateProvider, ITemplateStreamFilter)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [ResourceManager().resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        return [('common', ResourceManager().resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream
        if not 'id' in req.args:
            return stream
        columns = self.config.getlist('stamprarry', 'statuses', \
                                      default=[u'created', u'assigned', u'accepted', u'closed'])
        if not data.has_key('ticket'):
            return stream
        ticket = data['ticket']
        created = ('', 'created',ticket.time_created.strftime('%x'), ticket.values['reporter'])
        status_changes = {}
        if data.has_key('changes'):
            changes = data['changes']
            for change in changes:
                try:
                    key = change['fields']['status']['new']
                    value = (change['date'].strftime('%x'), change['author'])
                    status_changes[key] = value # if existed, override it
                except KeyError, AttributeError:
                    continue
        comfirmer = []
        for column in columns:
            if column=='created':
                comfirmer.append(created)
            elif status_changes.has_key(column):
                date, author = status_changes[column]
                comfirmer.append(('', column, date, author))
            else:
                comfirmer.append(('void',column, '-', '-'))
        data = { 'comfirmer': comfirmer }
        add_stylesheet(req, 'common/css/stamprally.css')
        template = Chrome(self.env).load_template('stamprally.html')
        content = template.generate(**data)
        return stream | Transformer("//div[@id='ticket']") \
                .append(tag.div(content, **{'class': "confirmer" }))

