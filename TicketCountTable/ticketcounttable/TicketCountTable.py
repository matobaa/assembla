# -*- coding: utf-8 -*-

from StringIO import StringIO
from genshi.core import Markup
from trac.core import TracError
from trac.ticket.api import TicketSystem
from trac.wiki.formatter import Formatter
from trac.wiki.macros import WikiMacroBase


class TicketCountTableMacro(WikiMacroBase):
    u"""指定された２つのパラメータを元に、チケット件数の集計結果を表形式で表示するマクロ。
    『ステータス別優先度別チケット件数一覧』などを簡単に作成することが可能です。
    ロードマップの画面でマイルストーンの説明として使用するといい感じかもしれません。
    """

    u"""
    ReportでSQLを直接書くことにより、同様の表を作成することは可能。
    ただし、Reportで作成した場合、Queryリンクを付加できないのと、
    将来的にReportは廃止予定となっているため、マクロで構築する。
    パラメータがSQLを意識した内容となっているのが微妙ではあるが、そこは気にしないこととする。
    """

    # チケット件数を取得し、テーブルのレンダリングを行う。
    def expand_macro(self, formatter, name, args):
        u"""パラメータを展開する。パラメータは、カンマで区切ることとする。
        パラメータのキーと値は以下のような感じで定義する（キーと値は":"でつなぐ）
        x -> 横軸の表示内容（抽出内容）を"|"で区切ってセット。
             なお、表示対象とするフィールド名は先頭に記載し、具体的な値は"="でつなぐ。値を省略した場合は項目の一覧を自動取得。
             グループ化したいときは "+"でつなぐ。改名したいときは AS で別名をつける。
             例）x:status=new|accepted + assigned AS doing|closed|reopened
        y -> 縦軸の表示内容。設定方法はxと同じ
        q -> 抽出条件(SQLのWHERE条件)。複数の条件を指定する場合は"&"でつなぐ。
             q:milestone=milestone1&owner=hoge
        xa-> x軸部分をクリックした際に表示するカスタムクエリのorderおよびgroup指定。
             xa:order=id&group=status のような感じで指定する。指定がない場合はorder=idのみを自動的に付加する。
        ya-> y軸部分をクリックした際に表示するカスタムクエリのorderおよびgroup指定。
             指定方法はxaと同様。
        m -> 表部分をクリックした際に表示するカスタムクエリのorderおよびgroup指定。
             指定方法はxa/yaと同様。
        """

        # とりあえず、パラメータ中に";"が含まれている場合はエラーとする
        if ';' in args:
            raise TracError('Parameter Error')

        # パラメータをカンマで区切って展開
        # ":"でキーと値に分割してDictionaryに格納（":"で２つに分割できなかったものは処理対象外）
        params = {}
        for value in args.split(','):
            v = value.split(':')
            if len(v) == 2:
                params[v[0]] = v[1]

        # 抽出条件を構築(SQLのWHERE節を構築)
        condition = self.createcondition(params)

        # x軸（横軸）の処理
        xaxiswork = params['x'].split('=')
        xaxiskey = xaxiswork[0]
        xaxiscolname = xaxiskey

        # y軸（縦軸）の処理
        yaxiswork = params['y'].split('=')
        yaxiskey = yaxiswork[0]
        yaxiscolname = yaxiskey

        # Ticketのフィールド一覧を取得する
        xfield = None
        yfield = None
        for field in TicketSystem(self.env).get_ticket_fields():
            if field['name'] == xaxiskey:
                xfield = field
                xaxislabel = xfield['label']
            if field['name'] == yaxiskey:
                yfield = field
                yaxislabel = yfield['label']

        # それぞれの軸がカスタムフィールドか否か
        xcustom = 'custom' in xfield and xfield['custom']
        ycustom = 'custom' in yfield and yfield['custom']
        if xcustom:
            xaxiskey = 'cx.value'
        if ycustom:
            yaxiskey = 'cy.value'

        yaxis = self.getaxisvalues(yaxiswork, yfield, ycustom, yaxiskey, yaxiscolname, condition)
        xaxis = self.getaxisvalues(xaxiswork, xfield, xcustom, xaxiskey, xaxiscolname, condition)

        if len(xaxis) == 0 or len(yaxis) == 0:
            return u'<ul><i>抽出条件に合致するチケットが存在しませんでした</i></ul>'

        query = u'SELECT '
        query += 'CASE '
        for y in yaxis:
            query += 'when %s in (%s) then \'%s\' \n' % (yaxiskey, ",".join(["'%s'" % v.strip() for v in y.split("+")]), y)
        query += 'END as %s' % yaxiskey

        for x in xaxis:
            query += ",sum(case when coalesce(%s,'') IN (%s) then 1 else 0 end)" % (xaxiskey, ",".join(["'%s'" % v.strip() for v in x.split("+")]))
        query += " from ticket "

        # カスタムフィールドを使用している場合はticket_customテーブルを連結する必要あり
        # なお、カスタムフィールドの場合は取得する際の列名がいったんvalueに置き換わってしまうので注意
        if xcustom:
            query += " left outer join ticket_custom as cx on cx.ticket=id and cx.name='%s'" % xaxiscolname
        if ycustom:
            query += " left outer join ticket_custom as cy on cy.ticket=id and cy.name='%s'" % yaxiscolname

        # 条件文及びgroup値を追加
        query += " %s group by %s" % (condition, yaxiskey)

        self.env.log.info(query)

        result = {}
        for row in self.env.db_query(query):
            result[row[0] or ''] = row[1:]

        # queryリンクのパラメータの各要素を構築する
        querycond = 'q' in params and "&%s" % params['q'] or '&order=priority'
        xquery = 'xa' in params and "&%s" % params['xa'] or "&order=id"
        yquery = 'ya' in params and "&%s" % params['ya'] or "&order=id"
        mquery = 'm' in params and "&%s" % params['m'] or "&order=id"

        # 出力テキスト構築
        # x軸のタイトル行を構築する
        xaxislabels = [(yaxislabel + u'＼' + xaxislabel)] + xaxiswork[1] + [u"小計"]
        wikitext = "||%s||\n" % "||".join(["= %s =" % x for x in xaxislabels])

        # 縦計を格納する
        ysum = {}
        for x in xaxis:
            ysum[x] = 0
        for yindex, y in enumerate(yaxis):
            # タイトル列
            wikitext += "||= %s =||" % yaxiswork[1][yindex]
            if y in result:
                each = result[y]
                linesum = 0
                for cnt2, x in enumerate(xaxis):
                    # テーブル部分本体
                    eachval = each[cnt2]
                    wikitext += self.q_or_0("%s=%s&%s=%s%s%s", (yaxiscolname, y, xaxiscolname, x, querycond, mquery), each[cnt2])
                    linesum += eachval
                    ysum[x] += eachval
                # 小計列
                wikitext += self.q_or_0("%s=%s%s%s", (yaxiscolname, y, querycond, yquery), linesum, term="\n")
            else:
                # 該当するy軸に対応するデータがない場合はリンクは付加しない
                for x in xaxis:
                    wikitext += "0||"
                wikitext += "0||\n"

        # 合計行
        wikitext += "||= %s =||" % u"【合計】"
        linesum = 0
        for x in xaxis:
            ysumval = ysum[x]
            wikitext += self.q_or_0("%s=%s%s%s", (xaxiscolname, x, querycond, xquery), ysum[x])
            linesum += ysumval
        # 総合計
        wikitext += self.q_or_0("%s", (querycond[1:],), linesum, term="\n")

        # 構築したwikiテキストをhtmlに変換（expand_macroの戻り値はhtmlそのものとなる）。
        out = StringIO()
        Formatter(self.env, formatter.context).format(wikitext, out)
        return Markup(out.getvalue())

    def q_or_0(self, placefolder, query, value, term=""):
        if value != 0:
            query = tuple(['|'.join(map(lambda x: x.strip(), q.split('+'))) for q in query])
            return ("[query:\"" + placefolder + "\" %s]||" + term) % (query + (value,))
        else:
            return "0||" + term

    # X/Y軸の項目の一覧を取得する
    def getaxisvalues(self, axiswork, field, custom, axiskey, axiscolname, condition):
        axis = None
        if len(axiswork) == 2:  # 項目が指定されている
            axis = axiswork[1].split('|')

            def after_as(asstr):
                p = asstr.split(' AS ')
                return p[0] if len(p) == 1 else p[1]
            axiswork[1] = map(after_as, axis)
            axis = map(lambda asstr: asstr.split(' AS ')[0], axis)
        elif field['type'] in ['select', 'radio']:  # select / radioの場合はoptionsで指定された項目を一覧としてセットする
            axis = field['options']
            if not '' in axis:
                axis.insert(0, '')
            axiswork.extend([axis])
        else:
            if custom:  # DBからデータを取得する;カスタムフィールドの場合
                query = u"SELECT distinct coalesce(value,'') as v from ticket t left outer join ticket_custom c on c.ticket=t.id on c.name='%s' %s order by 1" % (axiswork[0], condition)
            else:  # DBからデータを取得する;それ以外の場合
                query = u"SELECT distinct coalesce(%s,'') as v from ticket t %s order by 1" % (axiskey, condition)
            self.env.log.debug(query)
            axis = [row[0] for row in self.env.db_query(query)]
            axiswork.extend([axis])
        return axis

    # 抽出条件を構築(SQLのWHERE節を構築)
    # int型のものに対しても文字型と同様に''で囲んでいるが、SQLiteなら大丈夫のはず。
    def createcondition(self, params):
        leftjoin = ''
        condition = []
        if not 'q' in params:
            return ""
        conditions = params['q'].split('&')
        for cond in conditions:
            p = cond.split('=')
            if len(p) != 2:
                continue
            for field in TicketSystem(self.env).custom_fields:
                if p[0] == field['name']:
                    leftjoin += " left outer join ticket_custom as %s on %s.ticket=id and %s.name='%s' " % (p[0], p[0], p[0], p[0])
                    p[0] += '.value'
                    break
            orstrs = ','.join(["'%s'" % orcond for orcond in p[1].split('|')])
            condition.append('%s IN (%s)' % (p[0], orstrs))
        return leftjoin + ' where (%s)' % ') AND ('.join(condition)
