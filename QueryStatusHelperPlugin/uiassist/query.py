from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider
from pkg_resources import ResourceManager


class Checkbox(Component):
    """TODO: CLASSDOC Write HERE """
    
    implements(ITemplateProvider, ITemplateStreamFilter)
    
    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if(filename=='query.html'):
            add_script(req, 'querystatushelper/js/enabler.js')
        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('querystatushelper', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []