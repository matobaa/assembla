#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script
import datetime

class DotLog(Component):
    """ TODO: write here """
    implements (ITemplateStreamFilter, ITemplateProvider)
    
    #ITemplateProvider methods
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        return [('dotlog', ResourceManager().resource_filename(__name__, 'htdocs'))]

    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'wiki_edit.html' \
            and not req.args.has_key('preview') \
            and not req.args.has_key('diff') \
            and data['page'].old_text.startswith('.LOG'):
                add_script(req, 'dotlog/js/jquery.caret.1.02.js')
                add_script(req, 'dotlog/js/focusonlast.js')

                # タイムスタンプマクロが入っていた場合はTZを意識したマクロを埋め込む。そうでない場合はサーバタイムゾーンで。
                # TODO: DEBUG: とりあえずリテラル。時刻を返すように変更すること。
                data['page'].text += "\r\n\r\n" + "datetime.datetime().now()"
        return stream
