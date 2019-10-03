#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from StringIO import StringIO
from datetime import datetime
from genshi.builder import tag
from genshi.core import QName
from genshi.filters.transform import Transformer, ENTER
from svn.core import Stream
from trac.attachment import Attachment, AttachmentModule
from trac.core import Component, implements, TracError
from trac.mimeview.api import IHTMLPreviewRenderer, Mimeview
from trac.resource import get_resource_url, Resource, IResourceManager, \
    get_resource_name, ResourceNotFound
from trac.util.datefmt import http_date, to_datetime
from trac.util.text import pretty_size, unicode_unquote
from trac.util.translation import _
from trac.versioncontrol.api import RepositoryManager, NoSuchChangeset
from trac.versioncontrol.web_ui.browser import BrowserModule
from trac.versioncontrol.web_ui.util import get_existing_node, get_path_links
from trac.web.api import IRequestHandler, RequestDone, ITemplateStreamFilter
from trac.web.chrome import web_context, add_stylesheet, add_link
from trac.web.href import Href
from trac.web.wsgi import _FileWrapper
from trac.wiki.api import IWikiSyntaxProvider
from zipfile import ZipFile, ZipExtFile
import os
import re


class ZipRenderer(Component):
    """Renderer for ZIP archive."""
    implements(IResourceManager, IHTMLPreviewRenderer, IRequestHandler, IWikiSyntaxProvider, ITemplateStreamFilter)

    # IWikiSyntaxProvider methods
    def _format_link(self, formatter, ns, target, label):
        link, params, fragment = formatter.split_link(target)  # @UnusedVariable
        ids = link.split(':', 2)
        if len(ids) == 3:  # has a parent; filename!/path:realm:id
            localid = ids[0]
            parent_realm = ids[1]
            ids = ids[2].split(':', 2)
            if len(ids) == 3:
                resource = Resource(ids[1], ids[2]).child(parent_realm, ids[0]).child('zip', localid)
            elif len(ids) == 1:
                resource = Resource(parent_realm, ids[0]).child('zip', localid)
            else:
                resource = None
            return tag.a(label,
                 href=get_resource_url(self.env, resource, formatter.href))

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('raw-zip', self._format_link)
        yield ('zip', self._format_link)

    # IResourceManager methods
    def get_resource_realms(self):
        yield 'zip'
        yield 'raw-zip'

    def get_resource_url(self, resource, href, **kwargs):
        if not resource.parent:
            return None
        prefix = 'zip'
        format_ = kwargs.get('format')
        if format_ in ['raw']:
            kwargs.pop('format')
            prefix = format_ + '-zip'
        parent_href = unicode_unquote(get_resource_url(self.env,
                            resource.parent(version=None), Href('')))
        return href(prefix, "%s!/%s" % (parent_href, resource.id or ''), **kwargs)

    def get_resource_description(self, resource, format=None, **kwargs):  # @ReservedAssignment
        if not resource.parent:
            return _("Unparented zip %(id)s", id=resource.id)
        if format == 'compact':
            return '%s (%s)' % (resource.id,
                    get_resource_name(self.env, resource.parent))
        elif format == 'summary':
            return Attachment(self.env, resource).description
        if resource.id:
            return _("'%(id)s' in %(parent)s", id=resource.id,
                     parent=get_resource_name(self.env, resource.parent))
        else:
            return _("zipped file in %(parent)s",
                     parent=get_resource_name(self.env, resource.parent))

    def resource_exists(self, resource):
        try:
            attachment = Attachment(self.env, resource.parent)
            return os.path.exists(attachment.path)
        except ResourceNotFound:
            return False

    # IHTMLPreviewRenderer methods
    def get_extra_mimetypes(self):
        yield ('application/x-zip-compressed', ['egg', 'jar', 'apk', 'epub', 'kmz', 'xpi', 'ipa'])
        yield ('text/plain', ['MANIFEST.MF', 'PKG-INFO'])

    def get_quality_ratio(self, mimetype):
        if mimetype in ["application/zip", "application/x-zip-compressed"]:
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        if content and content.input:
            max_size = self.env.config.getint('attachment', 'max_zip_size', default=2097152)
            if isinstance(content.input, Stream) \
                    or isinstance(content.input, ZipExtFile):
                zipfile = ZipFile(StringIO(content.input.read(max_size)))
            else:
                zipfile = ZipFile(content.input)
            listitems = []
            for info in zipfile.infolist():
                resource = context.resource.child('zip', info.filename)
                href = get_resource_url(self.env, resource, context.href, rev=resource.parent.version)
                raw_href = get_resource_url(self.env, resource, context.href, format='raw')
                listitems.append(tag.li(
                    tag.a(info.filename, href=href, title=_("View attachment")),
                    tag.a(u'\u200B', href=raw_href, class_="trac-rawlink", title=_("Download")),
                    " (%s)" % pretty_size(info.file_size)))
            return tag.ul([listitems])

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/(raw-)?zip(?:/zip)*/attachment/([^/]+)/([^!]*)/([^/!]+)(!/.+)?(@.+)?$', req.path_info)
        # I know that attachment cannot have revision ... it's junk code
        if match:
            req.args['format'], realm, resource_id, archive, req.args['path'], rev = match.groups()
            req.args['attachment'] = Resource(realm, resource_id).child('attachment', archive)
            if rev:
                req.args['rev'] = rev[1:]
            return True
        match = re.match(r'/(raw-)?zip(?:/zip)*/(export|browser|file)/([^!]+)(!/[^@]+)?(@.+)?$', req.path_info)
        if match:
            req.args['format'], realm, resource_id, req.args['path'], rev = match.groups()
            req.args['browser'] = Resource(realm, resource_id)
            if rev:
                req.args['rev'] = rev[1:]
            return True
        pass

    def process_request(self, req):
        max_size = self.env.config.getint('attachment', 'max_zip_size', default=2097152)
        attachment = req.args.get('attachment', None)
        browser = req.args.get('browser', None)
        resource = attachment or browser
        xhr = req.get_header('X-Requested-With') == 'XMLHttpRequest'
        if not req.args['path'] and not xhr:  # if request have no name in zip;
            req.args['path'] = resource.id  # instead of browserModule.match_request(req)
            return self.compmgr[browser and BrowserModule or AttachmentModule].process_request(req)

        rev = req.args.get('rev', None)
        if rev and rev.lower() in ('', 'head'):
            rev = None
        if attachment:
            req.perm(resource).require('ATTACHMENT_VIEW')
            attachment = Attachment(self.env, attachment)
            fileobj = attachment.open()

        elif browser:
            req.perm(resource).require('FILE_VIEW')
            rm = RepositoryManager(self.env)
            reponame, repos, path = rm.get_repository_by_path(resource.id)
            if not repos and reponame:
                raise ResourceNotFound(_("Repository '%(repo)s' not found",
                                     repo=reponame))
            if repos:
                try:
                    node = get_existing_node(req, repos, path, rev)
                except NoSuchChangeset, e:
                    raise ResourceNotFound(e.message,
                                           _('Invalid changeset number'))
            fileobj = node.get_content()
        else:
            raise TracError('Not Implemented')

        name = (req.args['path'] or '')[2:]

        if name:
            for element in [e.lstrip('/') for e in name.split('!')]:
                zipfile = ZipFile(StringIO(fileobj.read(max_size)))
                fileobj = zipfile.open(element)
            context = web_context(req, resource.child('zip', name, version=rev))
        else:
            context = web_context(req)

        if xhr:
            zipfile = ZipFile(StringIO(fileobj.read(max_size)))
            data = {
                'reponame': reponame, 'stickyrev': node.created_rev,
                'display_rev': lambda x: x,
                'dir': {'entries': [{
                         'name': info.filename,
                         'kind': node.kind,
                         'content_length': info.file_size,
                         'path': path + (req.args['path'] or '') + '!/' + info.filename,
                         'raw_href': None,
                         'created_rev': node.created_rev,
                         } for info in zipfile.infolist()],
                        'changes': {node.created_rev: None},
                    },
            }
            return 'dir_entries.html', data, None

        try:
            zipinfo = zipfile.getinfo(element)
        except KeyError:
            raise ResourceNotFound(_("Attchment '%(title)s' does not exist.",  # FIXME: in browser, wrong message
                         title=name),
                       _('Invalid filename in Zip'))

        str_data = fileobj.peek(512)
        mimeview = Mimeview(self.env)
        mime_type = mimeview.get_mimetype(name, str_data)
        if mime_type and 'charset=' not in mime_type:
            charset = mimeview.get_charset(str_data, mime_type)
            mime_type = mime_type + '; charset=' + charset

        if req.args['format'] != 'raw-':  # format != raw
            href = unicode_unquote(get_resource_url(self.env, resource, Href('')))
            href += '!/' + name
            rawurl = req.href('raw-zip', href, rev=rev)
            add_stylesheet(req, 'common/css/code.css')
            add_link(req, 'alternate', rawurl, _('Original Format'), mime_type)
            preview = mimeview.preview_data(
                context,
                fileobj, zipinfo.file_size, mime_type, name, rawurl,
                 annotations=['lineno'])
            if attachment:
                attachment.resource = context.resource
                data = {'preview': preview,
                    'attachment': attachment}
                return 'attachment.html', data, None
            elif browser:
                path_links = get_path_links(req.href, reponame, path, rev)
                path_links.append({'name': '!' + name, 'href': req.href('zip', href, rev=rev)})
                data = {
                    'size': node.content_length,
                    'repos': repos,
                    'path_links': path_links,
                    'file': {
                            'changeset': repos.get_changeset(node.created_rev),
                            'preview': preview,
                            'size': node.content_length,
                             },
                    'display_rev': lambda x: x,
                    'reponame': reponame,
                    'stickyrev': rev,
                    'created_rev': rev,
                    'created_path': path,
                    'dir': False,
                    'context': context
                }
                add_stylesheet(req, 'common/css/browser.css')
#                add_script(req, 'common/js/expand_dir.js')
                return 'browser.html', data, None
        # else:
        # format == raw
        y, m, d, hh, mm, ss = zipinfo.date_time
        last_modified = http_date(to_datetime(datetime(y, m, d, hh, mm, ss)))
        if last_modified == req.get_header('If-Modified-Since'):
            req.send_response(304)
            req.send_header('Content-Length', 0)
            req.end_headers()
            raise RequestDone
        else:
            req.send_response(200)
            if not self.env.config.getbool('attachment', 'render_unsafe_content'):
                req.send_header('Content-Disposition', 'attachment')
            req.send_header('Content-Type', mime_type)
            req.send_header('Content-Length', zipinfo.file_size)
            req.send_header('Last-Modified', last_modified)
            req.end_headers()
            file_wrapper = req.environ.get('wsgi.file_wrapper', _FileWrapper)
            req._response = file_wrapper(fileobj, 4096)
            raise RequestDone

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        """ To use expander on zip file in directory view;
            replace <a class='file' href='.../browser/.......zip'>
                 to <a class='dir'  href='.../zip/browser/...zip'> """
        class AttrReplaceTransform(object):
            def __init__(self, name, by, to, count=None):
                self.name, self.by, self.to, self.count = name, by, to, count

            def __call__(self, stream):
                for mark, (kind, data, pos) in stream:
                    if mark is ENTER:
                        href = data[1].get(self.name).replace(self.by, self.to, self.count)
                        data = (data[0], data[1] | [(QName('href'), href)])
                    yield mark, (kind, data, pos)

        if filename in ['browser.html', 'dir_entries.html']:
            stream |= Transformer() \
                        .select('//td[@class="name"]//a[matches(@href, ".zip$")]') \
                        .apply(AttrReplaceTransform('href', 'browser', 'zip/browser', 1)) \
                        .attr('class', 'dir') \
                        .end() \
                        .select('//td[@class="name"]//a[contains(@href, ".zip?")]') \
                        .apply(AttrReplaceTransform('href', 'browser', 'zip/browser', 1)) \
                        .attr('class', 'dir') \
                        .end() \
                        .select('//td[@class="name"]//a[contains(@href, "!/")]') \
                        .apply(AttrReplaceTransform('href', 'browser', 'zip/browser', 1))
        return stream
