# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#    $Id:  $
#
#    Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#
#
############################################################################################
from datetime import timedelta
from lxml import etree

import base64
import time
import datetime
from datetime import datetime

import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

import time
import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools.translate import _

import xlwt
from xlwt import *
# from odoo.addons.c2c_reporting_tools.c2c_helper import *
from operator import itemgetter
# from odoo.addons.mn_base import report_helper
import xlsxwriter
from io import BytesIO
logger = logging.getLogger('odoo')

class account_general_ledger(models.TransientModel):
    """
query GL    """
    
#     _inherit = "abstract.report.excel"
    _name = "account.general.ledgerq"
    _description = "General ledger"
    
    
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    account_id = fields.Many2one('account.account', 'Account', )
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))
    target_move = fields.Selection([('all', 'All Entries'),
                                    ('posted', 'All Posted Entries')], 'Target Moves', required=True,default='posted')
    partner_id = fields.Many2one('res.partner', 'Partner', help="If empty, display all partners")
        
    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)
    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol
    
    def print_report(self):
        print ('aaaaaa')
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        file_name = 'general_ledger2.xlsx'

        # CELL styles тодорхойлж байна
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(14)
        h1.set_align('center')
        h1.set_align('vcenter')

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#E6E6E6')
        
        theader_sub = workbook.add_format({'bold': 1,'num_format': '###,###,###.##'})
        theader_sub.set_font_size(9)
        theader_sub.set_text_wrap()
        theader_sub.set_align('center')
        theader_sub.set_align('vcenter')
        theader_sub.set_border(style=1)
        theader_sub.set_bg_color('#FAFAD2')

        content_right = workbook.add_format({'num_format': '###,###,###.##'})
        content_right.set_text_wrap()
        content_right.set_font_size(9)
        content_right.set_border(style=1)
        content_right.set_align('right')

        content_left_bold = workbook.add_format({'bold': 1})
        content_left_bold.set_text_wrap()
        content_left_bold.set_font_size(9)
        content_left_bold.set_border(style=1)
        content_left_bold.set_align('left')

        content_left = workbook.add_format()
        content_left.set_text_wrap()
        content_left.set_font_size(9)
        content_left.set_border(style=1)
        content_left.set_align('left')

        content_date_left = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        content_date_left.set_text_wrap()
        content_date_left.set_font_size(9)
        content_date_left.set_border(style=1)
        content_date_left.set_align('left')

        
        content_left_no = workbook.add_format()
#         content_left_no.set_text_wrap()
        content_left_no.set_font_size(9)
#         content_left_no.set_border(style=1)
        content_left_no.set_align('left')

        p12 = workbook.add_format()
#         content_left_no.set_text_wrap()
        p12.set_font_size(10)
#         content_left_no.set_border(style=1)
        p12.set_align('left')

        bold_amount = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
        bold_amount.set_text_wrap()
        bold_amount.set_font_size(10)
        bold_amount.set_align('left')

        bold_amount_str=workbook.add_format()
        bold_amount_str.set_font_size(10)
        bold_amount_str.set_align('right')        

        right_no = workbook.add_format()
        right_no.set_font_size(10)
        right_no.set_align('right')
     
        center = workbook.add_format({'num_format': '###,###,###.##'})
        center.set_text_wrap()
        center.set_font_size(9)
        center.set_align('right')
        center.set_border(style=1)
        
        center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
        center_bold.set_text_wrap()
        center_bold.set_font_size(9)
        center_bold.set_align('right')
        center_bold.set_border(style=1)

        content_left_noborder = workbook.add_format()
        content_left_noborder.set_text_wrap()
        content_left_noborder.set_font_size(9)
        content_left_noborder.set_align('left')

        content_right_noborder = workbook.add_format()
        content_right_noborder.set_text_wrap()
        content_right_noborder.set_font_size(9)
        content_right_noborder.set_align('right')

        center_noborder = workbook.add_format()
        center_noborder.set_text_wrap()
        center_noborder.set_font_size(9)
        center_noborder.set_align('center')  
        

#         print 'lines ',lines
        start_=0
        account_name=''
        account_code=''
        report_name=u'ЕРӨНХИЙ ДЭВТЭР'

        sheet = workbook.add_worksheet(u'ЕЖ')

        
        row = 8
        
        sheet.merge_range(0, 0, 1, 5, report_name, h1)
#         sheet.write_merge(4,4,8,9, u'Огноо: %s - %s '%(data['form']['date_from'],data['form']['date_to']), styledict['text_xf'])
        sheet.merge_range(2, 0,2,2, u'Байгууллагын нэр: %s'%(self.company_id.name), p12)
        sheet.merge_range(3, 0,3,2, u'', p12)
        sheet.merge_range(4, 4,4,5, u'Тайлант үе: %s - %s '%( self.date_from ,self.date_to), content_left_no)
#         sheet.merge_range(5, 4,5,5, u'Эхний үлдэгдэл:', bold_amount_str)
#         

        rowx=5
        sheet.write(rowx+1,0, u'№', theader),
        sheet.write(rowx+1,1, u'Огноо', theader),
        sheet.write(rowx+1,2, u'Дугаар', theader),
        sheet.write(rowx+1,3, u'Журнал', theader),
        sheet.write(rowx+1,4, u'Данс', theader),
        sheet.write(rowx+1,5, u'Салбар', theader),
        sheet.write(rowx+1,6, u'Харилцагч', theader),
        sheet.write(rowx+1,7, u'Гүйлгээний утга', theader),
        sheet.write(rowx+1,8, u'Дебет', theader),
        sheet.write(rowx+1,9, u'Кредит', theader),
        sheet.write(rowx+1,10, u'Үлдэгдэл', theader),
        sheet.write(rowx+1,11, u'Валют', theader),
        sheet.write(rowx+1,12, u'Валют дүн', theader),
        sheet.write(rowx+1,13, u'Харцьсан данс', theader),
        sheet.write(rowx+1,14, u'Үүсгэсэн ажилтан', theader),
        sheet.write(rowx+1,15, u'Регистр', theader),
        
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 19)
        sheet.set_column('D:D', 18)
        sheet.set_column('I:L', 15)
        sheet.set_column('G:G', 20)
        sheet.set_column('E:E', 13)
        sheet.set_column('F:F', 13)
        sheet.set_column('H:H', 30)
        sheet.set_column('M:O', 13)
        rowx+=2
        n=1
#         sheet.write(rowx,0, '', content_left)
#         sheet.write(rowx,1, '', content_left)
#         #sheet.write(rowx,2, u'Эхний үлдэгдэл', content_left)
#         sheet.write(rowx,3, '', content_left)
#         #sheet.write(rowx,4, '', content_left)
#         sheet.write(rowx,4, '', center)
#         sheet.write(rowx,5, '', center)
#         #sheet.write(rowx,6, start, center)
#         rowx += 1
        account_where=""
        if self.account_id:
            account_where+=" and l.account_id={0} ".format(self.account_id.id)
        total_debit=0
        total_credit=0
#         self.env.cr.execute("select * from ( "
#                             "select '2021-01-01' as date "
#                             "    , 'Эхний үлдэгдэл' utga "
#                             "   , '' as branch "
#                              "   , '' as  customer_name "
#                              "   , a.code as  account "
#                              "   , '' as  analytic "
#                              "   , '' as  entry "
#                              "   , '' as  journal "
#                              "   , '' as  currency "
#                              "   , 1 as m_id  "
#                              "   , 2 as l_id "
#                              "   , sum(l.debit) as debit "
#                              "   , sum(l.credit) as credit "
#                              "   , sum(l.amount_currency)  as amount_currency "
#                              "   , 3 as create_uid "
#                              "   , '' as vat "
#                              "   , '' as haritsan "
#                              "   from account_move_line l "
#                              "   left join account_move m on l.move_id=m.id "
#                              "   left join account_account a on l.account_id=a.id "
#                              "   left join res_partner rp on l.partner_id=rp.id "
#                     "WHERE m.state = 'posted' "+" "+ account_where+ " "
#                    "AND m.date < %s and m.company_id = %s  group by a.code "
#                             " UNION ALL "                   
#                         "select l.date "
#                             "    , l.name utga "
#                             "   , b.name branch "
#                              "   , rp.name AS customer_name "
#                              "   , a.code account "
#                              "   , aaa.name AS analytic "
#                              "   , m.name as entry "
#                              "   , aj.name AS journal "
#                              "   , rc.name AS currency "
#                              "   , m.id as m_id "
#                              "   , l.id  as l_id "
#                              "   , l.debit "
#                              "   , l.credit "
#                              "   , l.amount_currency "
#                              "   , l.create_uid "
#                              "   , rp.vat "
#                              "   , (select array_to_string (array_agg (code), ',') AS code from account_account where id in "
#                              "   (select account_id from account_move_line ll where move_id=l.move_id and ll.id<>l.id)) as haritsan "
#                              "   from account_move_line l "
#                              "   left join account_move m on l.move_id=m.id "
#                              "   left join res_branch b on l.branch_id=b.id "
#                              "   left join account_account a on l.account_id=a.id "
#                              "   left join res_partner rp on l.partner_id=rp.id "
#                              "   left join account_journal aj on l.journal_id=aj.id "
#                              "   left join account_analytic_account aaa on aaa.id=l.analytic_account_id "
#                              "   left join res_currency rc on l.currency_id=rc.id "
#                     "WHERE m.state = 'posted' "+" "+ account_where+ " "
#                    "AND m.date >= %s and m.date <= %s and m.company_id = %s "
#                    ") as foo order by account,date ",
#                    
#             (self.date_from,self.company_id.id,self.date_from,self.date_to, self.company_id.id))
        
#                                 "    ooo.account_name, "

#                              "   , 1 as m_id  "
#                              "   , 2 as l_id "

# 
#                         "    ( "
#                         "    SELECT array_to_string(array_agg(account_account.code), ','::text) AS code "
#                         "    FROM account_account "
#                         "    WHERE (account_account.id IN ( SELECT ll.account_id "
#                         "    FROM account_move_line ll "
#                         "    WHERE ll.move_id = l.move_id AND ll.id <> l.id and l.debit!=ll.debit and (l.name=ll.name or l.debit=ll.credit) limit 1 )) "
#                         "    ) AS exchange_account, "
#                         "    ( "
#                         "    SELECT array_to_string(array_agg(account_account.code), ','::text) AS code "
#                         "    FROM account_account "
#                         "    WHERE (account_account.id IN ( SELECT ll.account_id "
#                         "    FROM account_move_line ll "
#                         "    WHERE ll.move_id = l.move_id AND ll.id <> l.id)) "
#                         "    ) AS exchange_account1 "
        self.env.cr.execute("select * from ( "
                            "select '2021-01-01' as date "
                            "    , 'Эхний үлдэгдэл' utga "
                            "   , '' as branch "
                             "   , '' as  customer_name "
                             "   , a.code as  account "
                        #      "   , '' as  analytic "
                             "   , '' as  entry "
                             "   , '' as  journal "
                             "   , '' as  currency "
                             "   , sum(l.debit) as debit "
                             "   , sum(l.credit) as credit "
                             "   , sum(l.amount_currency)  as amount_currency "
                             "   , 'c1' as create_uid "
                             "   , '' as vat "
                             "   , '' as haritsan "
                             "   from account_move_line l "
                             "   left join account_move m on l.move_id=m.id "
                             "   left join account_account a on l.account_id=a.id "
                             "   left join res_partner rp on l.partner_id=rp.id "
                    "WHERE m.state = 'posted' "+" "+ account_where+ " "
                   "AND m.date < %s and m.company_id = %s  group by a.code "
                            " UNION ALL "        
                        "  SELECT ooo.date, "
                        "    ooo.txn_value as utga, "
                        "    ooo.branch, "
                        "    ooo.customer_name, "
                        "    ooo.account, "
                        # "    ooo.analytic, "
                        "    ooo.entry, "
                        "    ooo.journal, "
                        "    ooo.currency, "
                        "    ooo.debit, "
                        "    ooo.credit, "
                        "    ooo.amount_currency, "
                        "    ooo.create_uid, "
                        "    ooo.vat, "                        
                        " CASE "
                        "    WHEN ooo.exchange_account IS NULL THEN ooo.exchange_account1 "
                        "    ELSE ooo.exchange_account "
                        "    END AS exchange_account "
                        "    FROM  "
                        "    ( SELECT l.date,"
                        "    l.name AS txn_value, "
                        "    b.name AS branch, "
                        "   rp.name AS customer_name, "
                        "    a.code AS account, "
                        "    a.name AS account_name, "
                        # "    aaa.name AS analytic, "
                        "    m.name AS entry, "
                        "    aj.name AS journal,"
                        "    rc.name AS currency, "
                        "    l.debit, "
                        "    l.credit, "
                        "    l.amount_currency, "
                        "    (select login from res_users where id=l.create_uid) as create_uid, "
                        "    rp.vat, "
                        "    (     SELECT array_to_string(array_agg(account_account.code), ','::text) AS code     "
                        "     FROM account_account     "
                        "         WHERE (account_account.id IN ( SELECT ll.account_id     FROM account_move_line ll     "
                        "                                      WHERE ll.move_id = l.move_id AND ll.id <> l.id and ((l.debit>0 and ll.credit>0) or (l.credit>0 and ll.debit>0)) and (l.name=ll.name or l.debit=ll.credit) limit 1 ))     ) AS exchange_account,     "
                        "    (     SELECT array_to_string(array_agg(account_account.code), ','::text) AS code     "
                        "     FROM account_account     "
                        "     WHERE (account_account.id IN ( SELECT ll.account_id    "
                        "                                   FROM account_move_line ll    "
                        "                                   WHERE ll.move_id = l.move_id AND ll.id <> l.id and ((l.debit>0 and ll.credit>0) or (l.credit>0 and ll.debit>0))))    limit 1 ) "
                        "            AS exchange_account1                             "
                        "    FROM account_move_line l "
                        "    LEFT JOIN account_move m ON l.move_id = m.id "
                        "    LEFT JOIN res_branch b ON l.branch_id = b.id "
                        "    LEFT JOIN account_account a ON l.account_id = a.id "
                        "    LEFT JOIN res_partner rp ON l.partner_id = rp.id "
                        "    LEFT JOIN account_journal aj ON l.journal_id = aj.id "
                        # "    LEFT JOIN account_analytic_account aaa ON aaa.id = l.analytic_account_id "
                        "    LEFT JOIN res_currency rc ON l.currency_id = rc.id "
                        "    WHERE m.state::text = 'posted'::text "+" "+ account_where+ " "
                   "AND m.date >= %s and m.date <= %s and m.company_id = %s "
                   " )  as ooo) as foo order by account,date ",
                   
            (self.date_from,self.company_id.id,self.date_from,self.date_to, self.company_id.id))        
            
        
        results = self.env.cr.dictfetchall()
#         print ('results ',results)  
        ids=[]
#         for id in mids:
#             ids.append(id[0])
#         lines=self.env['account.move'].get_order_line_xl(ids)
#         print ('lineslineslines ',lines)
        
        number=1
        j=False
        i=1
        for k in results:
            date=k['date']
            if k['utga']=='Эхний үлдэгдэл':
                date=''
                acc=k['account']
#                 sheet.write(rowx-1,0, 0, theader_sub)
#                 sheet.write(rowx-1,1, '', theader_sub)
#                 sheet.write(rowx-1,2, '', theader_sub)
#                 sheet.write(rowx-1,3, '', theader_sub)
#                 sheet.write(rowx-1,4, '', theader_sub)
#                 sheet.write(rowx-1,5, '', theader_sub)
#                 sheet.write(rowx-1,6, 'Данс', theader_sub)
#                 sheet.write(rowx-1,7, acc, theader_sub)
#                 sheet.write(rowx-1,8, '', theader_sub)
#                 sheet.write(rowx-1,9, '', theader_sub)
#                 sheet.write(rowx-1,10, '', theader_sub)
#                 sheet.write(rowx-1,11, '', theader_sub)
#                 sheet.write(rowx-1,12, '', theader_sub)
#                 sheet.write(rowx-1,13, '', theader_sub)
#                 sheet.write(rowx-1,14, '', theader_sub)
                #өмнөх данс эхний үлд
#                 rowx += 1
                if j:
                    sheet.write(rowx, 0, '',theader_sub)
                    sheet.write(rowx, 1, '', theader_sub)
                    sheet.write(rowx, 2, u'Дэд дүн', theader_sub)
                    sheet.write(rowx, 3, '', theader_sub)
                    sheet.write(rowx, 4, '', theader_sub)
                    sheet.write(rowx, 5, '', theader_sub)
                    sheet.write(rowx, 6, '', theader_sub)
                    sheet.write(rowx, 7, '', theader_sub)
                    sheet.write_formula(rowx, 8,'=sum(I{0}:I{1})'.format(rowx-i,rowx), theader_sub) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
                    sheet.write_formula(rowx, 9,'=sum(J{0}:J{1})'.format(rowx-i,rowx), theader_sub) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
                    sheet.write_formula(rowx, 10,'=sum(K{0}:K{1})'.format(rowx-i,rowx), theader_sub) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
                    sheet.write_formula(rowx, 11,'=sum(L{0}:L{1})'.format(rowx-i,rowx), theader_sub) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
                    sheet.write_formula(rowx, 12,'=sum(M{0}:M{1})'.format(rowx-i,rowx), theader_sub) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
#                     sheet.write_formula(rowx, 9,'=sum('+ self._symbol(rowx-i, 9)+':'+ self._symbol(rowx,9) +')', theader_sub)
#                     sheet.write_formula(rowx, 10,'{=sum('+ self._symbol(rowx-i, 10)+':'+ self._symbol(rowx,10) +')}', theader_sub)
#                     sheet.write_formula(rowx, 11,'{=sum('+ self._symbol(rowx-i, 11)+':'+ self._symbol(rowx,11) +')}', theader_sub)
#                     sheet.write_formula(rowx, 12,'{=sum('+ self._symbol(rowx-i, 12)+':'+ self._symbol(rowx,12) +')}', theader_sub)
                    sheet.write(rowx, 13, '', theader_sub)
                    sheet.write(rowx, 14, '', theader_sub)
                    sheet.write(rowx, 15, '', theader_sub)
                    rowx += 2 
#                 rowx += 2   
                sheet.write(rowx,0, 0, theader_sub)
                sheet.write(rowx,1, '', theader_sub)
                sheet.write(rowx,2, '', theader_sub)
                sheet.write(rowx,3, 'Данс', theader_sub)
                sheet.write(rowx,4, acc, theader_sub)
                sheet.write(rowx,5, '', theader_sub)
                sheet.write(rowx,6, '', theader_sub)
                sheet.write(rowx,7, 'Эхний үлдэгдэл', theader_sub)
                sheet.write(rowx,8, k['debit'], theader_sub)
                sheet.write(rowx,9, k['credit'], theader_sub)
#                 sheet.write(rowx,10, k['currency'], theader_sub)
                sheet.write_formula(rowx, 10,'=I{0}-J{1}'.format(rowx+1,rowx+1), theader_sub) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
                sheet.write(rowx,11, k['currency'], theader_sub)
                sheet.write(rowx,12, k['amount_currency'], theader_sub)
                sheet.write(rowx,13, '', theader_sub)
                sheet.write(rowx,14, '', theader_sub)
                sheet.write(rowx,15, '', theader_sub)
                rowx += 1
                row=rowx
                #өмнөх данс эхний үлд
#                 sheet.write(rowx, 0, '',theader_sub)
#                 sheet.write(rowx, 1, '', theader_sub)
#                 sheet.write(rowx, 2, u'Дэд дүн2', theader_sub)
#                 sheet.write(rowx, 3, '', theader_sub)
#                 sheet.write(rowx, 4, '', theader_sub)
#                 sheet.write(rowx, 5, '', theader_sub)
#                 sheet.write(rowx, 6, '', theader_sub)
#                 sheet.write(rowx, 7, '', theader_sub)
#                 sheet.write_formula(rowx, 8,'{=sum('+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')}', theader_sub)
#                 sheet.write_formula(rowx, 9,'{=sum('+ self._symbol(rowx-i, 9)+':'+ self._symbol(rowx,9) +')}', theader_sub)
#                 sheet.write_formula(rowx, 10,'{=sum('+ self._symbol(rowx-i, 10)+':'+ self._symbol(rowx,10) +')}', theader_sub)
#                 sheet.write_formula(rowx, 11,'{=sum('+ self._symbol(rowx-i, 11)+':'+ self._symbol(rowx,11) +')}', theader_sub)
#                 sheet.write(rowx, 12, '', theader_sub)
#                 sheet.write(rowx, 13, '', theader_sub)
#                 sheet.write(rowx, 14, '', theader_sub)
#                 rowx += 1
                i=1
                j=True
                
                continue
            sheet.write(rowx,0, n, content_left)
            sheet.write(rowx,1, date, content_date_left)
            sheet.write(rowx,2, k['entry'], content_left)
            sheet.write(rowx,3, k['journal'], content_left)
            sheet.write(rowx,4, k['account'], content_right)
            sheet.write(rowx,5, k['branch'], content_left)
            sheet.write(rowx,6, k['customer_name'], content_left)
            sheet.write(rowx,7, k['utga'], content_left)
            sheet.write(rowx,8, k['debit'], content_right)
            sheet.write(rowx,9, k['credit'], content_right)
#             sheet.write(rowx,10, k['currency'], content_right)
#             sheet.write_formula(rowx, 10,'{=sum('+ self._symbol(rowx-i, 10)+':'+ self._symbol(rowx,10) +')}', content_right)
            sheet.write_formula(rowx, 10,'=K{0}+I{1}-J{1}'.format(rowx,rowx+1,rowx+1), content_right) #+ self._symbol(rowx-i, 8)+':'+ self._symbol(rowx,8) +')', theader_sub)
            sheet.write(rowx,11, k['currency'], content_right)
            sheet.write(rowx,12, k['amount_currency'], content_right)
            sheet.write(rowx,13, k['haritsan'], content_right)
            sheet.write(rowx,14, k['create_uid'], content_right)
            sheet.write(rowx,15, k['vat'], content_right)
            i+=1
#             total_debit+=k[4]
#             total_credit+=k[5]
            rowx += 1
            n+=1

#         sheet.write(rowx-1,0, '', content_left)
#         sheet.write(rowx-1,1, '', content_left)
#         sheet.write(rowx-1,2, u'Дүн', content_left)
#         sheet.write(rowx-1,3, '', content_left)
#         sheet.write(rowx-1,4, total_debit, center)
#         sheet.write(rowx-1,5, total_credit, center)
        rowx += 1                
# #            
#         total_amounts = abs(total_amounts)
        
        
        sheet.merge_range(rowx, 1, rowx, 5, u'Орлогын ...... зарлагын ...... ширхэг баримтыг шалгаж хүлээн авсан болно.', p12)
        sheet.merge_range(rowx+1, 2, rowx+1, 5, u'', content_left_no)
        sheet.merge_range(rowx+2, 2, rowx+2, 5, u'Хөтөлсөн нягтлан бодогч:  __________________________', p12)
        sheet.merge_range(rowx+3, 2, rowx+3, 5, u'', content_left_no)
        sheet.merge_range(rowx+4, 2, rowx+4, 5, u'Хянасан: __________________________', p12)
        
#        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 100)        


        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
