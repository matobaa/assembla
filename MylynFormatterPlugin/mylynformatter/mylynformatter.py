#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from itertools import product
from urlparse import urlparse
from xml.parsers import expat

from genshi.builder import tag
from trac.attachment import AttachmentModule, Attachment, \
    IAttachmentChangeListener
from trac.config import ListOption
from trac.core import Component, implements
from trac.resource import Resource
from trac.versioncontrol.api import RepositoryManager
from trac.versioncontrol.web_ui.util import get_allowed_node
from trac.wiki.api import IWikiSyntaxProvider


class WikiFormatter(Component):
    implements(IWikiSyntaxProvider, IAttachmentChangeListener)
    # TODO: implement IRepositoryChangeListener
    # TODO: psfがなくても .projectの位置を指定できるようにする

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        yield (r"((?P<fqcn>[\w.]+)\.[\w]+)?\(((Unknown Source)|((?P<classname>[\w.]+\.java):(?P<lineno>[\d]+)))?\)",
               lambda x, y, z: self._format_link_file(x, 'mylyn', y, y, z))
        yield (r"Resource: (?P<path>[\w/.]+)(.+?Location: line (?P<line>[\d]+))?",
               lambda x, y, z: self._format_link(x, 'mylyn', y, y, z))
    # TODO: divide to two class

    def get_link_resolvers(self):
        return []

    _psf = None  # { project_name: repository_url }
    _srcpathes = {}  # { reponame: [srcpath] }
    void = ListOption('wiki', 'source_path',
        "svn: trunk/theproject/src/main/java trunk/theproject/src/test/java;",
        doc="""
            List of source paths as "reponame: space delimited source paths;"
            e.g. "trunk/theproject/src/main/java trunk/theproject/src/test/java; repo2: trunk/src trunk/test;";

            for example; a String "org.example.Main.method(Main.java:20)" will be link to repository browser
            when the source is found from these source paths, as /trunk/theproject/\ src/main/java/org/example/Main.java.
            (Provided by !MylynFormatter.!WikiFormatter) """)

    # need trailing slash
    _prefixes = {'java.lang.': 'http://docs.oracle.com/javase/7/docs/api/',  # java/lang/Exception.html
                 'javax.rmi.': 'http://docs.oracle.com/javase/7/docs/api/'}  # Example

    # IRepositoryChangeListener methods
#     def changeset_added(self, repos, changeset):
#         self._psf = None  # { project_name: repository_url }
#         self._srcpathes = {}  # { reponame: [srcpath] }
# 
#     def changeset_modified(self, repos, changeset, old_changeset):
#         self._psf = None  # { project_name: repository_url }
#         self._srcpathes = {}  # { reponame: [srcpath] }

    # IAttachmentChangeListener methods
    def attachment_reparented(self, attachment, old_parent_realm=None, old_parent_id=None):
        """Called when an attachment is added."""
        if (attachment.filename == 'projectSet.psf' and
                (attachment.parent_id == 'TeamProjectSet' and
                 attachment.parent_realm == 'wiki') or
                (old_parent_id == 'TeamProjectSet' and
                 old_parent_realm == 'wiki')):
            self._psf = None  # { project_name: repository_url }
            self._srcpathes = {}  # { reponame: [srcpath] }

    attachment_added = attachment_reparented
    attachment_deleted = attachment_added

    def get_psf(self):
        """ parse attached "team project set" for Eclipse IDE
            returns a-list as [ Eclipse project name -> repository URL ] """
        if self._psf is None:
            self._psf = {}
            psfResource = Resource('wiki', 'TeamProjectSet').child('attachment', 'projectSet.psf')
            if (self.compmgr[AttachmentModule].resource_exists(psfResource)):
                psf = Attachment(self.env, psfResource)

                def startElement(name, attrs):
                    if name == 'project':
                        attr = attrs.get('reference', "").split(',')
                        self._psf[attr[2]] = urlparse(attr[1]).path  # trim leading scheme/port
                reader = expat.ParserCreate()
                reader.StartElementHandler = startElement
                reader.ParseFile(psf.open())
                # specify checkout dir in server subversion directory
                rm = RepositoryManager(self.env)
                repos = rm.get_all_repositories()
                for projectname in self._psf.keys():
                    path = self._psf.get(projectname) + '/.project'
                    for reponame in repos:
                        repo = rm.get_repository(reponame)
                        if not repo:
                            continue
                        for npath in self.iter_lstrip(path):
                            if not repo.has_node(npath, None):
                                continue
                            self._psf[projectname] = npath[:-9]

                            # search .classpath here
                            npath = npath[:-9] + '/.classpath'
                            if not repo.has_node(npath, None):
                                continue
                            node = repo.get_node(npath, None)
                            srcpathes = self.parse_classpath(node.get_content())
                            self._srcpathes[repo.reponame] = map(lambda x: npath[:-10] + x, srcpathes)
            else:  # TeamProjectSet not found
                for repo in self.config.getlist('wiki', 'source_path', sep=';'):
                    # expected: "svn: trunk/theproject/src/main/java trunk/theproject/src/test/java;"
                    repo = repo.split(':')
                    repo, srcpaths = len(repo) < 2 and ("", repo[0]) or repo  # no leading reponame, use default repo
                    self._srcpathes[repo] = self._srcpathes.get(repo, [])
                    self._srcpathes[repo].extend([s.rstrip('/') + '/' for s in srcpaths.split(' ') if s])
        return self._psf  # { project_name: repository_url, ... }

    @staticmethod
    def parse_classpath(content):
        pathes = []

        def startElement(name, attrs):
            if name == 'classpathentry' and attrs.get('kind', '') == 'src':
                pathes.append(attrs.get('path') + '/')
        reader = expat.ParserCreate()
        reader.StartElementHandler = startElement
        reader.ParseFile(content)
        return pathes

    @staticmethod
    def iter_lstrip(npath, sep='/'):
        """ returns aaa/bbb/ccc, bbb/ccc, ccc ... and so on """
        npath = 'dummy/' + npath.lstrip('/')
        for i in range(npath.count(sep)):  # @UnusedVariable(i)
            npath = npath[npath.find(sep) + 1:]  # trim leading element
            yield npath

    def _format_link(self, formatter, ns, target, label, fullmatch=None):
        """ returns a tag for
            Resource: Projectname/path/to/src/org/example/package/Class.java Line: 123 """
        # search repository
        rm = RepositoryManager(self.env)
        line = fullmatch.group('line')
        line = line and '#L%s' % line or ""
        # option 1: search with unmodified path
        path = fullmatch.group('path')
        reponame, repos, npath = rm.get_repository_by_path(path)  # @UnusedVariable
        node = get_allowed_node(repos, npath, None, formatter.perm)
        if node:
            return tag.a(label, href=formatter.href.browser(path) + line, class_="source")
        # option 2: search with "/trunk/" + path
        path = "/trunk/" + fullmatch.group('path')
        reponame, repos, npath = rm.get_repository_by_path(path)  # @UnusedVariable
        node = get_allowed_node(repos, npath, None, formatter.perm)
        if node:
            return tag.a(label, href=formatter.href.browser(path) + line, class_="source")
        # option 3: heuristic search in repositories for subversion
        projectname, trailing = fullmatch.group('path').lstrip('/').split('/', 1)
        psf = self.get_psf()
        if projectname in psf:
            # subversion can checkout in the middle of repository
            path = psf[projectname] + '/' + trailing
            repos = rm.get_all_repositories()
            for npath, reponame in product(self.iter_lstrip(path), repos):
                repo = rm.get_repository(reponame)
                node = get_allowed_node(repo, npath, None, formatter.perm)
                if node:
                    return tag.a(label, class_="source",
                                 href=formatter.href.browser(repo.reponame + '/' + node.path) + line)
        return tag.a(label, class_='missing source')

    def _format_link_file(self, formatter, ns, target, label, fullmatch=None):
        """ returns a tag for
            org.example.package.Class.method(Class.java:123) """
        fqcn = fullmatch.group("fqcn")
        classname = fullmatch.group("classname")
        line = fullmatch.group("lineno")
        line = line and '#L%s' % line or ""
        rm = RepositoryManager(self.env)
        self.get_psf()  # force parse
        # search repositories by fully qualified class name
        if fqcn:
            fqcn_filename = fqcn.replace('.', '/') + ".java"
            for reponame in self._srcpathes.keys():
                repo = rm.get_repository(reponame)
                if not repo:
                    continue
                for srcpath in self._srcpathes[reponame]:
                    try:
                        if repo.has_node(srcpath + fqcn_filename, None):
                            return tag.a(label, href=formatter.href.browser(reponame + '/' + srcpath + fqcn_filename) + line, class_="source")
                    except Exception, e:  # GIT throws exception if MBCS used in fqcn
                        self.env.log.error(e)
                        pass
# implemented but not fit i feel
#             for prefix in self._prefixes.keys():
#                 if fqcn.startswith(prefix):
#                     href = self._prefixes[prefix] + fqcn.replace('.', '/') + '.html'
#                     return tag.a(label, href=href, class_="file")
            return label  # not missing resource
        # search repository by classname
        if classname:
            try:
                from multireposearch.sqlindexer import SqlIndexer
                reposearch = self.compmgr[SqlIndexer]
                search_results = [result for result in reposearch.find_words((classname,))]
                if search_results:
                    filename, reponame = search_results[0]
                    return tag.a(label, href=formatter.href.browser(reponame + '/' + filename) + line, class_="source")
            except Exception, e:  # SqlIndexer not installed nor enabled
                formatter.env.log.error(e)
                formatter.env.log.error("It's better using http://trac-hacks.org/wiki/MultiRepoSearchPlugin")

        # not found
        return tag.a(label, class_='missing source')
