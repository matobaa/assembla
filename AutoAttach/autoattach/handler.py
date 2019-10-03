from trac.attachment import Attachment
from trac.core import Component, implements
from trac.wiki.api import IWikiMacroProvider
import os

_inbox = 'inbox'

class Handler(Component):
    implements(IWikiMacroProvider)
    
    #IWikiMacroProvider methods
    def get_macros(self):
        yield 'AutoAttach'
        
    def expand_macro(self, formatter, name, content, args=None):
        parent = formatter.resource
        this_page = Attachment(self.env, parent.realm, parent.id)
        path = this_page.path
        path = path[len(os.path.join(self.env.path, 'attachments/')):]
        path = os.path.join(self.env.path, _inbox, path)
        path = os.path.realpath(path)  # follow symbolic link if needed
        if not os.path.exists(path) and not os.path.isdir(path):
            return
        newfiles = os.listdir(path)
        for attachment in Attachment.select(self.env, parent.realm, parent.id):
            if attachment.filename in newfiles:
                newfiles.remove(attachment.filename) # avoid overwrite
        if len(newfiles) == 0:
            return
        for filename in newfiles:
            fullpath = os.path.join(path, filename)
            if not os.path.isfile(fullpath):
                continue # skip it
            stat = os.stat(fullpath)
            this_page = Attachment(self.env, parent.realm, parent.id)
            this_page.author = __package__ # attacher name
            this_page.insert(filename, file(fullpath), stat.st_size)
            self.log.debug('ATTACHED NEW FILE: %s' % filename)
