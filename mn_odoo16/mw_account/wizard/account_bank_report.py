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
from io import BytesIO
import base64
import time
import datetime
from datetime import datetime

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

from datetime import timedelta
from lxml import etree
from odoo.tools.translate import _

from operator import itemgetter
import collections
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
import xlsxwriter

import logging

_logger = logging.getLogger(__name__)

class account_bank_report(models.TransientModel):
    _name = "account.bank.report"
    _description = "Account bank report"
 
    date_from = fields.Date('Эхлэх огноо',required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_to =  fields.Date('Дуусах огноо',required=True,default=lambda *a: time.strftime('%Y-%m-%d') )
    journal_id = fields.Many2one('account.journal', string="Харилцахын журнал", domain=[('type', 'in', ['bank', 'cash'])])
    by_month=fields.Boolean(u'Үлдэгдэл сараар',default=False, invisible="1")
    sum_month=fields.Boolean(u'Сараар',default=False)
    sum_day=fields.Boolean(u'Өдрөөр',default=False)
    journal_ids = fields.Many2many('account.journal', string="Харилцахын журнал", domain=[('type', 'in', ['bank', 'cash'])])
    # many_journal =fields.Boolean
#     target_move = fields.Selection([('done', 'All Posted Entries'),
#                                          ('all', 'All Entries'),
#                                         ], 'Target Moves')
                                        
                                        
    def print_report_window(self):

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        file_name = 'Cash_report.xlsx'

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
        theader.set_bg_color('#D1D0CE')

        content_right = workbook.add_format()
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
        self_br=self       
        payment_line = self.env['account.bank.statement.line']
#         req_ids = payment_request.search(cr, 1, [('id','in',ids)], order="bank_account_id desc")
        request_obj = self_br.journal_ids
#         lines=payment_line.search([('statement_id','in',context['active_ids']),('date','>=',self_br.date_from),
#                                                                             ('date','<=',self_br.date_to)],order="date asc, id asc")
#         lines=payment_line.search([('journal_id','=',request_obj[0].journal_id.id),('date','>=',self_br.date_from),
#                                                                             ('date','<=',self_br.date_to)],order="date asc, id asc")
        lines=payment_line.search([('journal_id','in',request_obj.ids),('date','>=',self_br.date_from),
                                                                        ('date','<=',self_br.date_to),
                                                                        ('move_id.state','=','posted'),
                                                                        ],order="date asc, id asc")
        cr=self.env.cr

#         print 'lines ',lines
        start_=0
        account_name=''
        account_code=''
        report_name=''
        start=0
        new_date = self_br.date_from - timedelta(days=1)
        # start_obj=payment_line.search([('journal_id','=',request_obj.id),('date','=',new_date)],limit=1)
        journal_ids=self.env['account.journal'].search([('id','in',request_obj.ids)])
        # query  =""""""
        start_obj =False
        if len(journal_ids) > 1:
            query = """SELECT absl.id  FROM account_bank_statement_line absl 
                    left join account_move as am on am.id = absl.move_id
                    WHERE am.journal_id in {1} and am.date<'{0}' 
                    order by am.date desc, am.id desc limit 1""".format(self.date_from,tuple(journal_ids.ids))
            cr.execute(query)
            start_obj = cr.fetchall()      
        else:
            query = """SELECT absl.id  FROM account_bank_statement_line absl 
                    left join account_move as am on am.id = absl.move_id
                    WHERE am.journal_id = {1} and am.date<'{0}' 
                    order by am.date desc, am.id desc limit 1""".format(self.date_from,journal_ids.id)
            cr.execute(query)
            start_obj = cr.fetchall()      
        # print('start_obj', start_obj)
        if start_obj:
            statement_id= start_obj[0]
            start_obj=payment_line.search([('id','=',statement_id)],limit=1)
            start = start_obj.running_balance
            # print('safasf',start)
        account_name =''
        account_code =''
        for s in request_obj:
            account_name+=s.default_account_id.name + ', '  
            account_code+=s.default_account_id.code+ ', '  
            # if self.by_month:
            #     start=s.running_balance
            #     for l in s.line_ids:
            #         if l.date<self_br.date_from:
            #             start+=l.amount
                    
            if s.type=='bank':
                report_name =u'Харилцахын гүйлгээний тайлан'
            else:
                report_name =u'Бэлэн мөнгөний гүйлгээний тайлан'
        verbose_total = ''
        currency = {}
        verbose_total_dict = {}
        amounts = {}
        amount = 0.0
        curr_amount = 0.0
        total_amounts = 0.0
        confirm = ''
        amount_in=0
        amount_out=0
        account_ids =''
        sheet = workbook.add_worksheet(u'ЕД')

        
        row = 8
        
        sheet.merge_range(0, 0, 1, 7, report_name, h1)
#         sheet.write_merge(4,4,8,9, u'Огноо: %s - %s '%(data['form']['date_from'],data['form']['date_to']), styledict['text_xf'])
        sheet.merge_range(2, 0,2,2, u'Байгууллагын нэр: %s'%(self.env.company.name), p12)
        sheet.merge_range(3, 0,3,2, u'', p12)
        sheet.merge_range(4, 0,4,1, u'Дансны дугаар: ', right_no)
        sheet.merge_range(4, 2,4,4, u'%s'%account_code, p12)
        sheet.merge_range(5, 0,5,1, u'Дансны нэр: ', right_no)
        sheet.merge_range(5, 2,5,3, u'%s'%account_name, p12)
        sheet.merge_range(4, 5,4,6, u'Тайлант үе: %s - %s '%( self_br.date_from ,self_br.date_to), content_left_no)
        sheet.merge_range(5, 4,5,5, u'Эхний үлдэгдэл:', bold_amount_str)
        sheet.merge_range(5, 6,5,8, start, bold_amount)
        

        rowx=5
        #sheet.merge_range(rowx, 0,rowx+1,0, u'Дд', theader),
        #sheet.merge_range(rowx,1,rowx,2, u'Баримтын', theader),
        #sheet.merge_range(rowx,3,rowx+1,4, u'Гүйлгээний утга', theader),
        #sheet.merge_range(rowx,4,rowx+1,4, u'Харилцагч', theader),
        #sheet.merge_range(rowx,5,rowx,6, u'Мөнгөн дүн', theader),
        #sheet.merge_range(rowx,7,rowx+1,7, u'Үлдэгдэл', theader),
#         sheet.merge_range(rowx,6,rowx+1,6, u'Аналитик данс', theader),
        sheet.write(rowx+1,0, u'Д/д', theader)
        sheet.write(rowx+1,1, u'Огноо', theader)
        sheet.write(rowx+1,2, u'Дугаар', theader)
        sheet.write(rowx+1,3, u'Харилцагч', theader)
        sheet.write(rowx+1,4, u'Гүйлгээний утга', theader)
        sheet.write(rowx+1,5, u'Банкны утга', theader)
        sheet.write(rowx+1,6, u'Орлого', theader)
        sheet.write(rowx+1,7, u'Зарлага', theader)
        sheet.write(rowx+1,8, u'Үлдэгдэл', theader)
        sheet.write(rowx+1,9, u'Мөнгөн гүйлгээ төрөл', theader)
        sheet.write(rowx+1,10, u'Харьцсан данс', theader)
        sheet.freeze_panes(8,0)
        
#         sheet.merge_range(rowx,10,rowx+1,10, u'Хэрэглэгч', theader),
        account_obj = self.pool.get('account.account')
        
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 19)
        sheet.set_column('D:D', 20)
        #sheet.set_column('E:E', 25)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:H', 13)
        sheet.set_column('I:I', 13)
        sheet.set_column('J:J', 25)
        sheet.set_column('K:K', 15)
        rowx+=2
        n=1
        sheet.write(rowx,0, '', content_left)
        sheet.write(rowx,1, '', content_left)
        #sheet.write(rowx,2, u'Эхний үлдэгдэл', content_left)
        sheet.write(rowx,3, '', content_left)
        #sheet.write(rowx,4, '', content_left)
        sheet.write(rowx,4, '', center)
        sheet.write(rowx,5, '', center)
        #sheet.write(rowx,6, start, center)
        rowx += 1

        total_in_a=0
        total_out=0
        
#         for request in request_obj:
#             for line in request.line_ids:
        if self.sum_day:
            sums={}
            for line in lines:
#                     start+=line.amount
                    total_amounts+=line.amount
                    if line.amount>0:
                        amount_in+=line.amount
                    else:
                        amount_out+=abs(line.amount)
                    in_a=0
                    out=0
                    if line.amount>0:
                        in_a=line.amount
                    else:
                        out=-line.amount
                    if sums.get(line.date,False):
                        sums[line.date]['in_a']+=in_a
                        sums[line.date]['out']+=out
#                         sums[line.date]['start']+=start
                    else:
                        sums[line.date]={'in_a':in_a,
                                         'out':out,
#                                          'start':start,
                                         }
                        
#                     sheet.write(rowx-1,0, n, content_left)
#                     sheet.write(rowx-1,1, line.date, content_date_left)
#                     sheet.write(rowx-1,2, line.ref, content_left)
#                     sheet.write(rowx-1,3, line.partner_id and line.partner_id.name or '', content_left)
#                     sheet.write(rowx-1,4, line.name, content_left)
#              #       sheet.write(rowx,4, line.partner_id and line.partner_id.name or '', content_left)
#                     sheet.write(rowx-1,5, in_a, center)
#                     sheet.write(rowx-1,6, out, center)
#                     sheet.write(rowx-1,7, start, center)
#                     rowx += 1
                    n+=1
                    total_in_a+=in_a
                    total_out+=out      
                                            
            for s in sums:
#                 print ('sss ',s)
                start+=sums[s]['in_a']-sums[s]['out']
                sheet.write(rowx-1,0, n, content_left)
                sheet.write(rowx-1,1, s, content_date_left)
                sheet.write(rowx-1,2, '', content_left)
                sheet.write(rowx-1,3, '', content_left)
                sheet.write(rowx-1,4, str(s)+u' өдрийн нийт', content_left)
                sheet.write(rowx-1,5, sums[s]['in_a'], center)
                sheet.write(rowx-1,6, sums[s]['out'], center)
                sheet.write(rowx-1,7, start, center)
                sheet.write(rowx-1,8, '', center)
                rowx += 1
                n+=1
#                     total_in_a+=in_a
#                     total_out+=out  
        elif self.sum_month:
            sums={}
            for line in lines:
#                     start+=line.amount
                    total_amounts+=line.amount
                    if line.amount>0:
                        amount_in+=line.amount
                    else:
                        amount_out+=abs(line.amount)
                    in_a=0
                    out=0
                    if line.amount>0:
                        in_a=line.amount
                    else:
                        out=-line.amount
                    if sums.get(str(line.date.year)+'-'+str(line.date.month),False):
                        sums[str(line.date.year)+'-'+str(line.date.month)]['in_a']+=in_a
                        sums[str(line.date.year)+'-'+str(line.date.month)]['out']+=out
#                         sums[line.date]['start']+=start
                    else:
                        sums[str(line.date.year)+'-'+str(line.date.month)]={'in_a':in_a,
                                         'out':out,
#                                          'start':start,
                                         }
                        
#                     sheet.write(rowx-1,0, n, content_left)
#                     sheet.write(rowx-1,1, line.date, content_date_left)
#                     sheet.write(rowx-1,2, line.ref, content_left)
#                     sheet.write(rowx-1,3, line.partner_id and line.partner_id.name or '', content_left)
#                     sheet.write(rowx-1,4, line.name, content_left)
#              #       sheet.write(rowx,4, line.partner_id and line.partner_id.name or '', content_left)
#                     sheet.write(rowx-1,5, in_a, center)
#                     sheet.write(rowx-1,6, out, center)
#                     sheet.write(rowx-1,7, start, center)
#                     rowx += 1
                    n+=1
                    total_in_a+=in_a
                    total_out+=out      
                                            
            for s in sums:
#                 print ('sss ',s)
                start+=sums[s]['in_a']-sums[s]['out']
                sheet.write(rowx-1,0, n, content_left)
                sheet.write(rowx-1,1, s, content_left)
                sheet.write(rowx-1,2, '', content_left)
                sheet.write(rowx-1,3, '', content_left)
                sheet.write(rowx-1,4, str(s)+u' сарын нийт', content_left)
                sheet.write(rowx-1,5, sums[s]['in_a'], center)
                sheet.write(rowx-1,6, sums[s]['out'], center)
                sheet.write(rowx-1,7, start, center)
                sheet.write(rowx-1,8, '', center)
                rowx += 1
                n+=1
#                     total_in_a+=in_a
#                     total_out+=out            
        else:
            team_ids = lines.mapped('journal_id')

            for team_categ in team_ids:
                transuud = lines.filtered(lambda r: r.journal_id.id == team_categ.id)
                # rowx += 1
                sheet.merge_range(rowx, 0, rowx,10, team_categ.name if team_categ else '', theader)
                rowx += 1
                n=1
                start = 0
                for line in transuud:
                # rowx += 1
                        accountSss=[]
                        start+=line.amount
                        total_amounts+=line.amount
                        if line.amount>0:
                            amount_in+=line.amount
                            # query='select a.code from account_move_line l left join \
                            #                                         account_move m on l.move_id=m.id left join \
                            #                                         account_account a on l.account_id=a.id left join \
                            #                 where \
                            #                 m.id = \'{0}\' and l.credit >0 '.format(line.move_id.id)
                            # cr.execute(query)
                            # credit_accounts_accounts=cr.fetchall()
                            query = "SELECT a.code as code FROM account_move_line l \
                            LEFT JOIN account_move m ON l.move_id = m.id \
                            LEFT JOIN account_account a ON l.account_id = a.id \
                            WHERE m.id = '{0}' AND l.credit > 0".format(str(line.move_id.id))
                            cr.execute(query)
                            credit_accounts_accounts = cr.fetchall()      
                            # account_ids += credit_accounts_accounts               
                            # print('safsaf',credit_accounts_accounts['code'], type(credit_accounts_accounts['code']))
                            for kk in credit_accounts_accounts:
                                accountSss.append(kk[0])
                                # print('safsaf',kk[0])
                        else:
                            amount_out+=abs(line.amount)
                            query = "SELECT a.code as code FROM account_move_line l \
                            LEFT JOIN account_move m ON l.move_id = m.id \
                            LEFT JOIN account_account a ON l.account_id = a.id \
                            WHERE m.id = '{0}' AND l.debit > 0".format(str(line.move_id.id))
                            cr.execute(query)
                            credit_accounts_accounts = cr.fetchall()      
                            # account_ids += credit_accounts_accounts               
                            # print('safsaf',credit_accounts_accounts['code'], type(credit_accounts_accounts['code']))
                            for kk in credit_accounts_accounts:
                                accountSss.append(kk[0])
                                # print('safsaf',kk[0])
                        in_a=0
                        out=0
                        if line.amount>0:
                            in_a=line.amount
                        else:
                            out=-line.amount
                        sheet.write(rowx,0, n, content_left)
                        sheet.write(rowx,1, line.date, content_date_left)
                        sheet.write(rowx,2, line.name, content_left)
                        sheet.write(rowx,3, line.partner_id and line.partner_id.name or '', content_left)
                        sheet.write(rowx,4, line.payment_ref, content_left)
                        sheet.write(rowx,5, line.bank_ref, content_left)
                        sheet.write(rowx,6, in_a, center)
                        sheet.write(rowx,7, out, center)
                        sheet.write(rowx,8, line.running_balance, center)
                        sheet.write(rowx,9, line.cash_type_id and line.cash_type_id.display_name or '', center) 
                        # sheet.write(rowx,9, '\n'.join(credit_accounts_accounts[0]) , center) 
                        sheet.write(rowx,10, '\n'.join(accountSss) , center) 
                        rowx += 1
                        n+=1
                        total_in_a+=in_a
                        total_out+=out
                # rowx+=1
                # end_row = rowx
        rowx += 1                
        sheet.write(rowx-1,0, '', content_left)
        sheet.write(rowx-1,1, '', content_left)
        sheet.write(rowx-1,2, u'Дүн', content_left)
        sheet.write(rowx-1,3, '', content_left)
        sheet.write(rowx-1,4, '', content_left)
        #sheet.write(rowx,4, '', content_left)
        sheet.write(rowx-1,5, '', content_left)
        sheet.write(rowx-1,6, total_in_a, center)
        sheet.write(rowx-1,7, total_out, center)
        sheet.write(rowx-1,8, '', center)
        sheet.write(rowx-1,9, '', center)
        sheet.write(rowx-1,10, '', center)
        rowx += 1                
#            
        total_amounts = abs(total_amounts)
        
        
        sheet.merge_range(rowx, 1, rowx, 5, u'Орлогын ...... зарлагын ...... ширхэг баримтыг шалгаж хүлээн авсан болно.', p12)
        sheet.merge_range(rowx+1, 2, rowx+1, 5, u'', content_left_no)
        sheet.merge_range(rowx+2, 2, rowx+2, 5, u'Нягтлан бодогч:  __________________________', p12)
        sheet.merge_range(rowx+3, 2, rowx+3, 5, u'', content_left_no)
        sheet.merge_range(rowx+4, 2, rowx+4, 5, u'Мөнгөний нярав: __________________________', p12)
        
#        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 100)        

#         workbook.close()
# 
#         out = base64.encodebytes(output.getvalue())
#         excel_id = self.pool.get('report.excel.output').create(cr, uid,{'data': out, 'name': file_name}, context=context)
# 
#         return {
#             'name': 'Export Result',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'report.excel.output',
#             'res_id': excel_id,
#             'view_id': False,
#             'context': context,
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#             'nodestroy': True,
#         }

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        file_name='payment_report.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
# 
#         from StringIO import StringIO
#         buffer = StringIO()
#         book.save(buffer)
#         buffer.seek(0)
#          
#         filename = "partner_detail_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
#         out = base64.encodebytes(buffer.getvalue())
#         buffer.close()
#          
#         excel_id = self.env['report.excel.output'].create({
#                                 'data':out,
#                                 'name':filename
#         })
#         mod_obj = self.env['ir.model.data']
#         form_res = mod_obj.get_object_reference('mn_base', 'action_excel_output_view')
#         form_id = form_res and form_res[1] or False
#         return {
#              'type' : 'ir.actions.act_url',
#              'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
#              'target': 'new',
#         }
        
                         
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
