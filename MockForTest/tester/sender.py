# encoding: utf-8

from trac.core import Component, implements
from trac.notification import IEmailSender


class TestEmailSender(Component):
    """ Dummy Email Sender; dump to debug log.

    To use this, select TestEmailSender in \"smtp_enabled\",
    enable \"smtp_enabled\" in admin/tracini/notification,
    and set recipients e-mail address in the user's preferences. """
    implements(IEmailSender)

    #IEmailSender methods
    def send(self, from_addr, recipients, message):
        self.env.log.debug("""
        TestEmailSender:
        To: %s
        from: %s

        %s""" % (recipients, from_addr, message))
