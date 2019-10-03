#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trac.admin.api import IAdminCommandProvider
from trac.attachment import Attachment
from trac.core import Component, implements
from trac.resource import resource_exists
from trac.util.text import print_table


class ValidateCommand(Component):
    """ Provides 'attachment validate' command for trac-admin script. """
    implements(IAdminCommandProvider)
    
    QUERY = "SELECT type,id,filename FROM attachment ORDER BY type,id,filename"

    # IAdminCommandProvider methods
    def get_admin_commands(self):
        yield ('attachment validate', '',
               """list all attachments and Validate attachments are existed or not.
               
               leading '!' indicator means the attachment is not found.""",
               None, self._do_validate)

    def _do_validate(self):
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute(ValidateCommand.QUERY)
        attachment_exists = self._attachment_exists
        print_table([(attachment_exists(type, id, filename) and ' ' or '!',
                      type + ':' + id,
                      filename)
                     for type, id, filename in cursor])

    def _attachment_exists(self, type, id, filename):
        att = Attachment(self.env, type, id, filename)
        return resource_exists(self.env, att.resource)