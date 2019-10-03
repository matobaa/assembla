# -*- coding: utf-8 -*-

from datetime import datetime
from pkg_resources import ResourceManager
from trac.admin.api import IAdminPanelProvider
from trac.core import Component, implements, Interface, ExtensionPoint
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_warning
import threading
import time


class ICronJob(Interface):
    """ Scheduled job.
        run() will be executed on specified time by cron daemon.
        You can present default_time() that returns String
        as time to execute like '0 0 1 * *'
     """

    def run():  # @NoSelf
        """ entry point that will be executed on specified times."""

section = 'crontab'
getkey = lambda job: "%s.%s" % (job.__class__.__module__, job.__class__.__name__)
ANY = range(0, 60)
ZERO = [0]
ONE = [1]
NEVER = []


class Daemon(Component):
    implements(IRequestHandler, IAdminPanelProvider, ITemplateProvider)

    jobs = ExtensionPoint(ICronJob)
    engine = None
    entries = {}

    def __init__(self):
        Component.__init__(self)
        self.entries = self.get_entries()
        self.__class__.engine = self
        t = threading.Thread(target=self.poll)
        t.daemon = True
        t.start()

    # NOTE:
    #  I cannot use compmgr.is_enabled() because in case that the egg in project/plugin folder
    #  always enable even if no configuration line in [component] section.
    #  -> mandatory adding the configuration line in trac.ini
    # NOTE:
    #  I cannot use compmgr.is_enabled() because in case that execute with tracd-script
    #  and disabled in configuration always the method returns true.
    #  I have to see the configuration not via compmgr.
    def poll(self):
        key = '%s.%s' % (self.__module__, self.__class__.__name__)
        while True:
            if not self.config.getbool('components', key):
                self.env.log.debug("cron engine has disabled ... exiting.")
                break  # exit when disabled
            if self != self.__class__.engine:
                self.env.log.debug("cron engine rebooted ... old thread is exiting.")
                break  # exit when another thread is created
            # runs every interval in seconds
            now = datetime.now()
            for job in self.jobs:
                # decide execute the job or not
                entry = self.entries[getkey(job)]
                if entry and \
                        now.minute in entry[0] and \
                        now.hour in entry[1] and \
                        now.month in entry[3] and \
                        (now.day in entry[2] or \
                            (now.weekday() + 1) % 7 in entry[4]):
                    try:
                        job.run()
                    except:
                        self.env.log.exception("Unexpected error:")
                else:
#                    self.env.log.debug('Skipped: ' + job.__repr__())
                    pass
            time.sleep(10 - datetime.now().second % 10)
        pass  # thread end
        self.env.log.debug("exit from polling loop. " + self.__repr__())

    def parse_entry(self, arg):  # str is not contains space char
        # throws ValueError if int(str) fails
        if arg == '*':  # "*"
            return ANY
        result = []
        params = arg.split(',')  # "1,2,3-5,6-10/2" -> ["1", "2", "3-5", "6-10/2"]
        for param in params:
            if not "-" in param:
                result.append(int(param))  # "1", "2" -> [ ..., 1, 2]
                continue
            param = param.split('-', 1)  # "3-5" -> ["3", "5"]  # "6-10/2" -> ["6", "10/2"]
            if not '/' in param[1]:
                result.extend(range(int(param[0]), int(param[1]) + 1))  # [ ..., 3, 4, 5]
                continue
            param[1], step = param[1].split('/', 1)
            result.extend(range(int(param[0]), int(param[1]) + 1, int(step)))  # [ ..., 6, 8, 10]
        return result

    def load_entry(self, entry):
        # http://svn.freebsd.org/base/head/usr.sbin/cron/lib/entry.c
        entry = entry.strip()
        if entry.startswith('#'):
            return [NEVER, NEVER, NEVER, NEVER, NEVER]
        elif entry.startswith('@reboot'):
            return False  # Not Implemented
        elif entry.startswith('@yearly'):
            return [ZERO, ZERO, ONE, ONE, ANY]
        elif entry.startswith('@annually'):
            return [ZERO, ZERO, ONE, ONE, ANY]
        elif entry.startswith('@monthly'):
            return [ZERO, ZERO, ONE, ANY, ANY]
        elif entry.startswith('@weekly'):
            return [ZERO, ZERO, ANY, ANY, ZERO]
        elif entry.startswith('@daily'):
            return [ZERO, ZERO, ANY, ANY, ANY]
        elif entry.startswith('@midnight'):
            return [ZERO, ZERO, ANY, ANY, ANY]
        elif entry.startswith('@hourly'):
            return [ZERO, ANY, ANY, ANY, ANY]
        elif entry.startswith('@every_minute'):
            return [ANY, ANY, ANY, ANY, ANY]
        elif entry.startswith('@every_second'):
            return False  # Not Implemented
        else:  # about to parse numerics
            entries = entry.split(' ')
            if len(entries) != 5:
                return False  # Not Implemented
            try:
                return map(self.parse_entry, entries)
            except:  # ValueError
                return False

    def get_entries(self):
        result = {}
        for job in self.jobs:
            key = getkey(job)
            time_field = self.config.get(section, key, False) or \
                (job.default_time() if 'default_time' in dir(job) else '# 0 * * * *')
            result[key] = self.load_entry(time_field)
        return result

    # IRequestHandler Methods
    def match_request(self, req):
        return False

    def process_request(self, req):
        pass

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('cron', 'Cron', 'crontab', 'Crontab')

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TICKET_ADMIN')
        if req.method == 'POST':
            darty = False
            for key in req.args.keys():
                if key.startswith('cron_'):
                    entry_string = req.args.get(key)
                    entry = self.load_entry(entry_string)
                    if entry:
                        self.entries[key[5:]] = entry
                        self.config.set(section, key[5:], entry_string)
                        darty = True
                    else:
                        # notify.append({key[5:], entry_string})
                        add_warning(req, "cycle \"%s\" cannot recognized for %s. " % (entry_string, key[5:]))
                        pass
            if darty and len(req.chrome['warnings']) == 0:
                self.config.save()
                req.redirect(req.href.admin(category, page))
        data = []
        for job in self.jobs:
            key = getkey(job)
            entry_string = req.args.get('cron_' + key) or \
                self.config.get(section, key, False) or \
                (job.default_time() if 'default_time' in dir(job) else '# 0 * * * *')
            data.append({'name': key,
                          'cycle': entry_string})
        return 'crontab.html', {'jobs': data}

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [ResourceManager().resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []


class ExampleCronjob(Component):
    implements(ICronJob)

    def run(self):
        self.env.log.debug(self.__repr__())

    def default_time(self):
        return '0 0 1 * *'
