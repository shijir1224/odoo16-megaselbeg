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
from datetime import date

import xlwt
import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
from operator import itemgetter
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

# _logger = logging.getLogger('odoo')

class account_equity_changes_report(models.TransientModel):
    """
        Монголын Сангийн Яамнаас баталсан Өмчийн өөрчлөлтийн тайлан.
    """
    
    _name = "account.equity.changes.report"
    _description = "Account Transaction Balance Report"
    
    @api.model
    def _default_report(self):
        domain = [
            ('report_type', '=', u'equity'),
        ]
        return self.env['account.financial.html.report'].search(domain, limit=1)
        
    report_id = fields.Many2one('account.financial.html.report',required=True,
        default=_default_report,
                                string='Report')
    date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    target_move = fields.Selection([('posted', 'Батлагдсан гүйлгээ'),
                                    ('all', 'Бүх гүйлгээ'),
                                    ], string='Target Moves', required=True, default='posted')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
#     branch_ids = fields.Many2many('res.branch', string='Branches')


    def _print_report(self, data):
        data['form'].update(self._build_contexts(data))
        body = (u"Гүйлгээний баланс (Журналын тоо='%s', Эхлэх Огноо='%s', Дуусах Огноо='%s')") % (len(data['form']['journal_ids']), data['form']['date_from'], data['form']['date_from'])
        message = u"[Тайлан][PDF][PROCESSING] %s" % body
        return self._make_excel(data)
    
    def check_report(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        company_obj = self.env['res.company']
        
        
        ezxf = xlwt.easyxf
        heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        text_xf = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        text_right_xf = ezxf('font: bold off; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;')
        text_bold_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        text_bold_right_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;')
        text_center_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        number_xf = ezxf('font: bold off; align: horz right; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')
        number_bold_xf = ezxf('font: bold on; align: horz right; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')
        number_green_xf = ezxf('font: italic on; align: horz right; borders: top thin, left thin, bottom thin, right thin;pattern: pattern solid, fore_colour gray25;', num_format_str='#,##0.00')
        text_green_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;pattern: pattern solid, fore_colour gray25;')
        
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Balance sheet')

        sheet.write(2, 2, u'ӨМЧИЙН ӨӨРЧЛӨЛТИЙН ТАЙЛАН', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
        sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(self.company_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.row(1).height = 400
        sheet.write(4, 3, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write_merge(4, 4, 8, 9, u'Тайлант хугацаа: %s - %s'%
                    (self.date_from,
                    self.date_to
                    ),ezxf('font:bold off;align:wrap off,vert centre,horiz right;'))              
        rowx = 5
        sheet.write(rowx, 0, u'№', heading_xf)
        sheet.write(rowx, 1, u'Үзүүлэлт', heading_xf)
        sheet.write(rowx, 2, u'Өмч', heading_xf)
        sheet.write(rowx, 3, u'Халаасны хувьцаа', heading_xf)
        sheet.write(rowx, 4, u'Нэмж төлөгдсөн капитал', heading_xf)
        sheet.write(rowx, 5, u'Хөрөнгийн дахин үнэлгээний нэмэгдэл', heading_xf)
        sheet.write(rowx, 6, u'Гадаад валютын хөрвүүлэлтийн нөөц', heading_xf)
        sheet.write(rowx, 7, u'Эздийн өмчийн бусад хэсэг', heading_xf)
        sheet.write(rowx, 8, u'Хуримтлагдсан ашиг', heading_xf)
        sheet.write(rowx, 9, u'Нийт дүн', heading_xf)
#        
        rowx += 1
#         Өмнөх он

#         Тухайн он
        report_obj = self.env['account.financial.html.report'].browse(self.report_id.id)
        report_rows=[
                '20.. оны 12-р сарын 31-ны үлдэгдэл',
                'Нягтлан бодох бүртгэлийн бодлогын өөрчлөлтийн нөлөө, алдааны залруулга',
                'Залруулсан  үлдэгдэл',
                'Тайлант үеийн цэвэр ашиг (алдагдал)',
                'Бусад дэлгэрэнгүй орлого',
                'Өмчид гарсан өөрчлөлт',
                'Зарласан ногдол ашиг',
                'Дахин үнэлгээний нэмэгдлийн хэрэгжсэн дүн',
#                 '20.. оны 12-р сарын 31-ны үлдэгдэл',
                ]

        d=self.read()
        # date_from=self.date_from-relativedelta(years=1)
        # date_to=self.date_to-relativedelta(years=1)
        date_from=date(self.date_from.year - 1, 1, 1)
        date_to=date(self.date_to.year - 1, 12, 31)

        data = {'branch_ids':False,
                'date_from':date_from,
                'date_to':date_to,
                'target_move': 'posted',
                'company_id':[self.company_id.id],}

        report_obj = self.env['account.financial.html.report'].browse(self.report_id.id)
        n=1
        report_datas = report_obj.create_report_equity_data(data)
#         print ('report_datas1 ',report_datas)
        totals=[0,0,0,0,0,0,0,0]
        hh_next=0
        nt_next=0
        du_next=0
        for line in report_rows:
            text=text_xf
            number=number_xf
            ashig=0
            eq=0
            du=0
            hh=0
            nt=0
            if n in (1,3):
                ashig=abs(report_datas['ashig_start']) 
                # eq=abs(report_datas['eq_start'])
                eq=abs(report_datas['eq_end']-report_datas['eq_start'])
                
            elif n==4:
                ashig=report_datas['ashig_credit']-report_datas['ashig_debit'] 
            if n==8:
                du=abs(report_datas['du_end'] - report_datas['du_start'])
                du_next=du
            if n==6:
                hh=abs(report_datas['hh_end']-report_datas['hh_start']) #-report_datas['nt_start']
                nt=abs(report_datas['nt_end']-report_datas['nt_start'])
                hh_next=hh
                nt_next=nt
#             if n==5:
#              	nt=report_datas['nt_start']
            sheet.write(rowx, 0, n,text)
            sheet.write(rowx, 1, line, text)
            sheet.write(rowx, 2, eq , number)
            sheet.write(rowx, 3, hh , number)
            sheet.write(rowx, 4, nt, number)
            sheet.write(rowx, 5, du , number)
            sheet.write(rowx, 6, report_datas['gv_start'] , number)
            sheet.write(rowx, 7, report_datas['other_start'] , number)
            sheet.write(rowx, 8, ashig, number)
            sheet.write(rowx, 9, eq+hh+nt+du+report_datas['gv_start']+report_datas['other_start']+ashig, number)
            n+=1
            rowx += 1
            
#             totals[0]+=hh
#             totals[0]+=nt
#             totals[0]+=du
#             totals[0]+=eq
#             totals[0]+=eq
            if n>=3:
                totals[7]+=eq+hh+nt+du+report_datas['gv_start']+report_datas['other_start']+ashig
                totals[0]+=eq
                totals[6]+=ashig

                totals[1]+=hh
                totals[2]+=nt
                totals[3]+=du
#                 totals[4]+=eq
#                 totals[0]+=eq
                
#             totals[0]+=eq
#         n+=1
        # sheet.write(rowx, 0, n,text)
        # sheet.write(rowx, 1, '20.. оны 12-р сарын 31-ны үлдэгдэл', text)
        # sheet.write(rowx, 2, totals[0] , number)
        # sheet.write(rowx, 3, totals[1] , number)
        # sheet.write(rowx, 4, totals[2], number)
        # sheet.write(rowx, 5, totals[3] , number)
        # sheet.write(rowx, 6, totals[4] , number)
        # sheet.write(rowx, 7, totals[5] , number)
        # sheet.write(rowx, 8, totals[6], number)
        # sheet.write(rowx, 9, totals[7], number)

        
#тухайн жил
        self.env.cr.commit()
        d=self.read()
#         print ('d2 ',d)
        d[0].update({'branch_ids':False})
        report_obj = self.env['account.financial.html.report'].browse(self.report_id.id)
        n=1
        report_datas = report_obj.create_report_equity_data(d[0])
#         print ('report_datas2 ',report_datas)
        totals=[0,0,0,0,0,0,0,0]
        # rowx+=1
        totals[1]+=hh_next
        totals[2]+=nt_next
        totals[3]+=du_next
        
        for line in report_rows:
            text=text_xf
            number=number_xf
            ashig=0
            eq=0
            du=0
            hh=0
            nt=0
            if n in (1,3):
                ashig=abs(report_datas['ashig_start']) 
                eq=abs(report_datas['eq_start'])
                if n==1:
                    hh=hh_next
                    nt=nt_next
                    du=du_next
            elif n==4:
                ashig=report_datas['ashig_credit']-report_datas['ashig_debit'] 
            if n==8:
                du=abs(report_datas['du_end'] - report_datas['du_start'])
            if n==6:
                hh=abs(report_datas['hh_end']-report_datas['hh_start']) #-report_datas['nt_start']
                nt=abs(report_datas['nt_end']-report_datas['nt_start'])
#             if n==5:
#             	nt=report_datas['nt_start']
            sheet.write(rowx, 0, n,text)
            sheet.write(rowx, 1, line, text)
            sheet.write(rowx, 2, eq , number)
            sheet.write(rowx, 3, hh , number)
            sheet.write(rowx, 4, nt, number)
            sheet.write(rowx, 5, du , number)
            sheet.write(rowx, 6, report_datas['gv_start'] , number)
            sheet.write(rowx, 7, report_datas['other_start'] , number)
            sheet.write(rowx, 8, ashig, number)
            sheet.write(rowx, 9, eq+hh+nt+du+report_datas['gv_start']+report_datas['other_start']+ashig, number)
            n+=1
            rowx += 1
            
#             totals[0]+=hh
#             totals[0]+=nt
#             totals[0]+=du
#             totals[0]+=eq
#             totals[0]+=eq
            if n>=3:
                totals[7]+=eq+hh+nt+du+report_datas['gv_start']+report_datas['other_start']+ashig
                totals[0]+=eq
                totals[6]+=ashig

                totals[1]+=hh
                totals[2]+=nt
                totals[3]+=du
#                 totals[4]+=eq
#                 totals[0]+=eq
                
#             totals[0]+=eq
#         n+=1
        sheet.write(rowx, 0, n,text)
        sheet.write(rowx, 1, '20.. оны 12-р сарын 31-ны үлдэгдэл', text)
        sheet.write(rowx, 2, totals[0] , number)
        sheet.write(rowx, 3, totals[1] , number)
        sheet.write(rowx, 4, totals[2], number)
        sheet.write(rowx, 5, totals[3] , number)
        sheet.write(rowx, 6, totals[4] , number)
        sheet.write(rowx, 7, totals[5] , number)
        sheet.write(rowx, 8, totals[6], number)
        sheet.write(rowx, 9, totals[7], number)
                
        
        inch = 3000
        sheet.col(0).width = int(0.7*inch)
        sheet.col(1).width = int(4*inch)
        sheet.col(2).width = int(1.5*inch)
        sheet.col(3).width = int(1.5*inch)
        sheet.col(4).width = int(1.5*inch)
        sheet.col(5).width = int(1.5*inch)
        sheet.col(6).width = int(1.5*inch)
        sheet.col(7).width = int(1.5*inch)
        sheet.col(8).width = int(1.5*inch)
        sheet.col(9).width = int(1.5*inch)
        sheet.row(7).height = 500
         
        sheet.write(rowx+2, 1,  u'Боловсруулсан нягтлан бодогч.........................................../ %s /' %(self.env.user.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        
        sheet.write(rowx+4, 1, u'Хянасан ерөнхий нягтлан бодогч....................................../\
                                                 /', ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
        
        sheet.write(rowx+6, 1, u"Тайлан татсан огноо: %s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)
        
        filename = "equity_changes_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
        out = base64.encodebytes(buffer.getvalue())
        buffer.close()
        
        excel_id = self.env['report.excel.output'].create({
                                'data':out,
                                'name':filename
        })
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }    
                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

