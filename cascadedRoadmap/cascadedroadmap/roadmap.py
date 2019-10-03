from trac.ticket import Milestone, TicketSystem
from trac.ticket.roadmap import RoadmapModule, apply_ticket_permissions, \
    get_ticket_stats, milestone_stats_data
from trac.web.chrome import add_link, add_notice, add_script, add_stylesheet, \
    add_warning, Chrome
from trac.util.translation import _
    
def get_tickets_for_milestone(env, db, milestone, field='component'):
    cursor = db.cursor()
    fields = TicketSystem(env).get_ticket_fields()
    if field in [f['name'] for f in fields if not f.get('custom')]:
        cursor.execute("SELECT id,status,%s FROM ticket WHERE milestone like %%s "
                       "ORDER BY %s" % (field, field), (milestone + '%',))
    else:
        cursor.execute("SELECT id,status,value FROM ticket LEFT OUTER "
                       "JOIN ticket_custom ON (id=ticket AND name=%s) "
                       "WHERE milestone like %s ORDER BY value", (field, milestone + '%'))
    tickets = []
    for tkt_id, status, fieldval in cursor:
        tickets.append({'id': tkt_id, 'status': status, field: fieldval})
    return tickets
  
class CascadedRoadmapModule(RoadmapModule):
    def match_request(self, req):
        return req.path_info == '/roadmap'

    def process_request(self, req):
        req.perm.require('MILESTONE_VIEW')

        show = req.args.getlist('show')
        if 'all' in show:
            show = ['completed']

        db = self.env.get_db_cnx()
        milestones = Milestone.select(self.env, 'completed' in show, db)
        if 'noduedate' in show:
            milestones = [m for m in milestones
                          if m.due is not None or m.completed]
        milestones = [m for m in milestones
                      if 'MILESTONE_VIEW' in req.perm(m.resource)]

        stats = []
        queries = []

        for milestone in milestones:
            tickets = get_tickets_for_milestone(self.env, db, milestone.name,
                                                'owner')
            tickets = apply_ticket_permissions(self.env, req, tickets)
            stat = get_ticket_stats(self.stats_provider, tickets)
            stats.append(milestone_stats_data(self.env, req, stat,
                                              '^' + milestone.name))
            #milestone['tickets'] = tickets # for the iCalendar view

        if req.args.get('format') == 'ics':
            self.render_ics(req, db, milestones)
            return

        # FIXME should use the 'webcal:' scheme, probably
        username = None
        if req.authname and req.authname != 'anonymous':
            username = req.authname
        icshref = req.href.roadmap(show=show, user=username, format='ics')
        add_link(req, 'alternate', icshref, _('iCalendar'), 'text/calendar',
                 'ics')

        data = {
            'milestones': milestones,
            'milestone_stats': stats,
            'queries': queries,
            'show': show,
        }
        add_stylesheet(req, 'common/css/roadmap.css')
        return 'roadmap.html', data, None
