#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.session import DetachedSession
from genshi.filters.transform import Transformer

class Marker(Component):
    implements (ITemplateStreamFilter)
    
    class ReportSession(DetachedSession):
        def __init__(self, env, sid):
            super(Marker.ReportSession, self).__init__(env, None)
            self.get_session('__report:%s' % sid, authenticated=142857)

    def get_known_sessions(self):
        cursor = self.env.get_read_db().cursor()
        cursor.execute('SELECT sid, last_visit FROM session WHERE authenticated=%s', (142857,))
        sessions = [{'sid': row[0][9:], 'last_visit': row[1]} for row in cursor.fetchall()]
        return sessions

    def filter_stream(self, req, method, filename, stream, data):
        if filename in ['report_list.html']:
            # indicate to active report
            known_sessions = self.get_known_sessions()
            for session in known_sessions:
                xpath = '//div[@id="content"]//td[@class="report"]/a[@href="%s/report/%s"]' \
                            % (req.href.base, session.get('sid'))
                stream |= Transformer(xpath).append("*")
        if filename in ['report_view.html', 'query.html']:
            # mark the report active
            id = 'report_resource' in data and data['report_resource'].id \
                or ('report' in data) and data['report'] and data['report'].get('id') \
                or None
            if id:
                session = Marker.ReportSession(self.env, id)
                session['user'] = req.authname
                session.save()
        return stream