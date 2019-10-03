#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter, IRequestFilter
import re
from trac.util.datefmt import to_utimestamp

class Aggregator(Component):
    implements(ITemplateStreamFilter, IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if not 'aggregate' in req.args \
                or not data \
                or not 'ticket' in data \
                or not 'changes' in data:
            return template, data, content_type
        ticket = data['ticket']
        if not 'TICKET_MODIFY' in req.perm(ticket.resource):
            return template, data, content_type
        cnum = int(req.args['aggregate'])
        changes = iter(data['changes'])
        for change in changes:
            if 'cnum' in change and change['cnum'] == cnum:
                self._aggregate(ticket.id, change, changes.next())
                req.redirect(req.href.ticket(ticket.id) + '#comment:%d' % cnum)
        return template, data, content_type
 
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream
        if 'cnum_edit' in req.args: # comment editing
            return stream
        ticket = data.get('ticket')
        if not 'TICKET_MODIFY' in req.perm(ticket.resource):
            return stream
        transformer = Transformer()
        if data.has_key('changes'):
            changes = data['changes']
            # 前のコメントと, field の重複がなく, authorが一致していて, 時間が離れていない場合, Aggregateボタンを出す
            aggregatable = set()
            last = {'date': datetime.now(), 'fields': {}, 'author': None}
            for change in changes:
                try:
                    delta = change['date'].replace(tzinfo=None) - last['date'].replace(tzinfo=None)
                    if last['author'] == change['author'] \
                            and len(set(last['fields'].keys()) & set(change['fields'].keys())) == 0 \
                            and delta.days == 0 and delta.seconds <= 3600:
                        aggregatable.add(last['cnum'])
                except KeyError, e:
                    pass
                except AttributeError, e:
                    pass
                last = change
            self.log.debug('aggregatable: %s' % aggregatable)
            # Build transformer
            for cnum in aggregatable:
                transformer = transformer \
                    .select('//div[@id="changelog"]/div[@id="trac-change-%s"]/h3[@class="change"])' % cnum) \
                    .after(tag.form(tag.input(type='hidden', name='aggregate', value=cnum),
                                    tag.div(tag.input(type='submit', value='Aggregate', title="to next"),
                                            class_='inlinebuttons'))) \
                    .end()
        return stream | transformer

    def _aggregate(self, id, aggregator, aggregatee):
        self.log.debug('aggregator: %s' % aggregator)
        self.log.debug('aggregatee: %s' % aggregatee)
        if 'replyto' in aggregatee:
            pass # TODO: Write here
        @self.env.with_transaction()
        def do_aggregate(db):
            cursor = db.cursor()
            self.log.debug("DELETE FROM ticket_change WHERE field='comment' AND oldvalue=%s AND newvalue='' AND ticket=%s" %
                           (aggregatee['cnum'], id))
            cursor.execute("DELETE FROM ticket_change WHERE field='comment' AND oldvalue=%s AND newvalue='' AND ticket=%s",
                           (aggregatee['cnum'], id))
            cursor.execute("UPDATE ticket_change SET time=%s WHERE time=%s AND ticket=%s", 
                           (to_utimestamp(aggregatee['date']), to_utimestamp(aggregator['date']), id))
        pass
    
    # 試験:
    # 前提バリエーション: 通常コメント(ノートあり/なし/更新あり/ノート削除/ノート追加), 返答(元,先), 添付
    # アサーション： 
    #  a. 集約できること
    #  b. Follow/Reply-Toリンクが期待通り機能する
    #  c. ノート履歴が残る
    # 試験パターン:
    #  1. ノートあり  + ノートなし                a.OK
    #  1. ノートあり  + 返答元
    #  1. ノートあり  + 返答先
    #  1. ノートあり  + 添付
    #  1. ノートなし + ノートあり                 a.NG
    #  1. ノートなし + 更新あり
    #  1. ノート削除 + ノート追加
    #  1. ノート追加 + ノート削除
    #  1. 返答元 + ノートあり
    #  1. 返答元 + 返答先 (連携なし)
    #  1. 返答元 + 返答先 (連携あり)
    #  1. 返答先 + 返答元
    