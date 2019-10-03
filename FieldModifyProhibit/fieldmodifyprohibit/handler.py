#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trac.config import ListOption
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketManipulator
from genshi.filters.transform import Transformer
from trac.web.api import ITemplateStreamFilter


class Handler(Component):
    implements(ITicketManipulator, IPermissionRequestor, ITemplateStreamFilter)

    # TODO: default values for DEBUG use only.
    prohibited_fields = ListOption('ticket', 'prohibited_field', 'summary, description',
            doc="""Comma-separated list of fields they need permission to change.
            (Provided by !%s)""" % "FieldModifyProhibit")
    action = 'CHANGE_ANY_FIELDS'  # trailing "S" avoids accidental conflict

    def field2role(self, field):
        return "CHANGE_%s_FIELD" % field.upper()

    # IPermissionRequestor methods
    def get_permission_actions(self):
        fields = self.config.getlist('ticket', 'prohibited_field')
        actions = [self.field2role(field) for field in fields]
        return actions + [(self.action, actions)]

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        if ticket.resource.id == None:
            return []
#        if self.action in req.perm:
#            return []
        errors = []
        for field in self.config.getlist('ticket', 'prohibited_field'):
            if self.field2role(field) in req.perm:  # OK, you have permission to change ... skip
                continue
            if field in ticket._old:
                label = field
                for f in ticket.fields:
                    if f['name'] == field:
                        label = f['label']
                        break
                errors.append((label, u'変更するには %s 権限が必要です。 "%s"に戻してください' % (self.field2role(field), ticket._old[field])))
        return errors

    # ITemplateStreamFilter methods
    # this idea is from http://syo.cocolog-nifty.com/freely/2008/10/post-ede0.html
    def filter_stream(self, req, method, filename, stream, formdata):
        if (filename == 'ticket.html'):
            transformer = Transformer()
            for field in self.prohibited_fields:
                required = self.field2role(field)
                if required not in req.perm:
                    xpath = '//*[contains(@id, "field-%s")]' % field
                    tip = u'変更するには %s 権限が必要です。' % required
                    transformer = transformer.select(xpath).attr('disabled', 'disabled').attr('title', tip).end()
            return stream | transformer
        return stream
