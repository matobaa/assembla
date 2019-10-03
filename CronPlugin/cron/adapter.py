# -*- coding: utf-8 -*-

""" Adapter for other plug-ins.

contains:
 - Adapter for ScheduledWorkflow; http://trac-hacks.org/wiki/ScheduledWorkflowPlugin
 - Adapter for TicketReminder; http://trac-hacks.org/wiki/TicketReminderPlugin
 - Adapter for Email2Trac; http://trac-hacks.org/wiki/MailToTracPlugin

these adapter enables with plug-in depends on.
"""

from cron.engine import ICronJob
from trac.config import PathOption
from trac.core import Component, implements

try:
    from scheduledworkflow import ScheduledWorkflow

    class ScheduledWorkflowCronJob(Component):
        """ Adapter for ScheduledWorkflow; http://trac-hacks.org/wiki/ScheduledWorkflowPlugin """
        implements(ICronJob)

        # ICronJob methods
        def run(self):
            target = self.compmgr[ScheduledWorkflow]
            if not target:
                return
            target._do_transition('new', 'assigned', 0, 'scheduled workflow daemon')

        def default_time(self):
            return '@weekly'

except ImportError:
    pass


try:
    from ticketreminder.api import TicketReminder

    class TicketReminderCronJob(Component):
        """ Adapter for TicketReminder; http://trac-hacks.org/wiki/TicketReminderPlugin """
        implements(ICronJob)

        # ICronJob methods
        def run(self):
            target = self.compmgr[TicketReminder]
            if not target:
                return
            target._do_check_and_send()

        def default_time(self):
            return '@daily'
except:
    pass

try:
    from mail2trac.email2trac import Email2Trac

    class Email2TracCronJob(Component):
        """ Adapter for Email2Trac; http://trac-hacks.org/wiki/MailToTracPlugin """
        implements(ICronJob)

        filepath = PathOption('crontab', 'email2trac.filepath',
                          doc="Full path to rfc:5322 text to handle by !MailToTracPlugin")

        # ICronJob methods
        def run(self):
            target = self.compmgr[Email2Trac]
            filepath = self.config.getpath('crontab', 'email2trac.filepath', None)

            if not target:
                return
            if not filepath:
                self.log.debug("Please specify [crontab]-email2trac.filepath in trac.ini.")
                return
            target.main(filepath)

        def default_time(self):
            return '@weekly'
except:
    pass
