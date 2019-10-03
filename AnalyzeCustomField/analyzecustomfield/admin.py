#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pkg_resources import ResourceManager
from trac.admin.api import IAdminPanelProvider, IAdminCommandProvider
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider
import json

# なにを見たいか?
# チケット総数
# 有効な値が入っている割合 (未記入 or 既定値を除いた割合)
# 値のばらつき具合

# 可能であれば
# 縦持ちのカスタムフィールドを横持ちにしたい
# 横持ちのカスタムフィールドを縦持ちにしたい
# レポートを書き換える必要があるかもしれない

def analyze(self):
    count_values = """
        SELECT name, COUNT(value) FROM (
            SELECT DISTINCT name, value FROM ticket_custom
        ) GROUP BY name """
    count_valid = "SELECT name, COUNT(value) FROM ticket_custom GROUP BY name"
    count_all = "SELECT count(id) from ticket"
    
    ticket = TicketSystem(self.env)
    cfields = ticket.get_custom_fields()
    db = self.env.get_read_db()
    cursor = db.cursor()
    # QTY of Valid data, without Default value
    valid = {}
    cursor.execute(count_valid)
    for name, count in cursor:
        valid[name] = count
    # QTY of data valiation for valiation
    cursor.execute(count_values)
    valiation = {}
    for name, count in cursor:
        valiation[name] = count
    # rebuild cfields
    for field in cfields:
        field['valiation'] = valiation.get(field['name'], 0)
        field['valid'] = valid.get(field['name'], 0)
    data = {'cfields':cfields}
    # Ticket QTY
    cursor.execute(count_all)
    data['qty'] = cursor.fetchone()
    # build notdefined list
    notdefined = []
    for name in [name for name in valid.keys() if name not in [field.get('name') for field in cfields]]:
        notdefined.append({
                        'name':name,
                        'label':'N/A',
                        'type':'N/A',
                        'valiation':valiation.get(name, 0),
                        'valid':valid.get(name, 0)})
    data['notdefined'] = notdefined
    return data

class AdminPanel(Component):
    implements(ITemplateProvider, IAdminPanelProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [ResourceManager().resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        return []

    # IAdminPanelProvider methods
    def get_admin_panels(self,req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', _("Ticket System"),
                   'analyzecustomfirld', _("Analyze Custom Fields")) 

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TICKET_ADMIN')
        data = analyze(self)
        return ('analayzecustomfield.html', data)

class Command(Component):
    implements(IAdminCommandProvider)
    
    # IAdminCommandProvider methods
    def get_admin_commands(self):
        yield ('customfield analyze', '', 'Analyze custom field', None, self.command)
    
    def command(self):
        data = analyze(self)
        print json.dumps(data, indent=2)
