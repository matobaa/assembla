from trac.core import Component, implements
from trac.web.api import IRequestHandler
from trac.wiki.intertrac import InterTracDispatcher


class InterTracForTicket(Component):
    implements(IRequestHandler)

    wrapped = None

    # IRequestHandler Methods
    def match_request(self, req):
        return False

    def process_request(self, req):
        pass

    def __init__(self):
        Component.__init__(self)
        if not self.wrapped:
            self.wrap()

    def wrap(self):
        target = self.compmgr[InterTracDispatcher]
        if not target:
            return

        def process_request(*args, **kwargs):  # hook method
            req = args[0]
            if req:
                link = req.args.get('link', '')
                if isinstance(link, unicode) and link.isdigit():
                    req.args['link'] = u"#%s" % link
            return self.wrapped(*args, **kwargs)
        self.wrapped = target.process_request
        target.process_request = process_request
