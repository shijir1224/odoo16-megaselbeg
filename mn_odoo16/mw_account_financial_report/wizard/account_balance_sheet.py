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
try:
    # Python 2 support
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodestring
    
import time
import datetime
from datetime import datetime

import xlwt
import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError, ValidationError
from operator import itemgetter
from collections import OrderedDict
# _logger = logging.getLogger('odoo')

class account_balance_sheet_report(models.TransientModel):
    """
        Монголын Сангийн Яамнаас баталсан Баланс тайлан.
    """
    
    _name = "account.balance.sheet.report"
    _description = "Account Transaction Balance Report"
    
    @api.model
    def _default_report(self):
        domain = [
            ('name', '=', u'Баланс тайлан'),
        ]
        return self.env['account.financial.html.report'].search(domain, limit=1)
        
#     check_balance_method = fields.Boolean('Check balance method',default=True)
#     chart_account_ids = fields.Many2many('account.account', string='Accounts')
    report_id = fields.Many2one('account.financial.html.report',required=True,
        default=_default_report,
#         domain=[('report_type','=','balance')],
                                string='Report')
    date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    branch_ids = fields.Many2many('res.branch', string='Branches')
    lang_type = fields.Selection([('en', 'En'),
                                    ('mn', 'Mn'),
                                    ], string='Language', required=True, default='mn')
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.constrains("company_id", "date_range_id")
    def _check_company_id_date_range_id(self):
        for rec in self.sudo():
            if (
                rec.company_id
                and rec.date_range_id.company_id
                and rec.company_id != rec.date_range_id.company_id
            ):
                raise ValidationError(
                    _(
                        "The Company in the General Ledger Report Wizard and in "
                        "Date Range must be the same."
                    )
                )
    def _print_report(self, data):
        # print "guilgee balancee   23165465464654654654",data
        data['form'].update(self._build_contexts(data))
#         form = self.read()[0]
#         data = self.pre_print_report(data)
#         print "data ",data
#         data['form']['company_id'] = form['company_id'][0]
#         data['form']['account_ids'] = data['form']['chart_account_ids']
# #         data['form']['company_type'] = data['form']['company_type']
#         data['form']['check_balance_method'] = form['check_balance_method']
#         data['form']['is_excel'] = form['is_excel']
        body = (u"Гүйлгээний баланс (Журналын тоо='%s', Эхлэх Огноо='%s', Дуусах Огноо='%s')") % (len(data['form']['journal_ids']), data['form']['date_from'], data['form']['date_from'])
        message = u"[Тайлан][PDF][PROCESSING] %s" % body
#         logger.notifyChannel(u"[Тайлан][PDF][PROCESSING]", netsvc.LOG_DEBUG, body)
#         _logger.debug('body')

#         if  form['is_excel']:
        return self._make_excel(data)
    
    def check_report(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        report_obj = self.env['account.financial.html.report'].browse(self.report_id.id)
        d=self.read()
        report_datas = report_obj.create_report_data(d[0])
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
        rowx = 5
        if self.lang_type=='en':
            sheet.write(2, 2, u'Balance sheet', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
            sheet.write_merge(3, 3, 0, 2,  u'Report name: %s' %(self.report_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write_merge(4, 4, 0, 2,  u'Company: %s' %(self.company_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.row(1).height = 400
            sheet.write(4, 3, u"%s year %s month %s day" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write_merge(rowx, rowx+1, 0, 0, u'Number', heading_xf)
            sheet.write_merge(rowx, rowx+1, 1, 1, u'Items', heading_xf)
            sheet.write_merge(rowx, rowx, 2, 3, u'Balance', heading_xf)
            sheet.write_merge(rowx+1, rowx+1, 2, 2, str(self.date_from), heading_xf)
            sheet.write_merge(rowx+1, rowx+1, 3, 3, str(self.date_to), heading_xf)

        else:
            sheet.write(2, 2, u'САНХҮҮГИЙН БАЙДЛЫН ТАЙЛАН', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
            # sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(self.report_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(self.company_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.row(1).height = 400
            sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
            sheet.write_merge(rowx, rowx+1, 1, 1, u'БАЛАНСЫН ЗҮЙЛС', heading_xf)
            sheet.write_merge(rowx, rowx, 2, 3, u'Үлдэгдэл', heading_xf)
            sheet.write_merge(rowx+1, rowx+1, 2, 2, str(self.date_from), heading_xf)
            sheet.write_merge(rowx+1, rowx+1, 3, 3, str(self.date_to), heading_xf)
#        
        rowx += 1
        # print ('report_datas ',report_datas)
        # sorted_x = OrderedDict(sorted(report_datas.seq(), key=itemgetter(1)))
        # s_list=sorted(sorted_x.iterkeys())
        # s_list=sorted(report_datas[line]['seq'])
        # s_list = sorted(report_datas.items(), key=lambda item: item[1]['seq'])
        for line in report_datas:
            rowx += 1
            text=text_xf
            number=number_xf
            if report_datas[line]['type']=='credit':
                if report_datas[line]['balance']>0:
                    balance=-report_datas[line]['balance']
                else:
                    balance=abs(report_datas[line]['balance'])
                if report_datas[line]['balance_start']>0:
                    balance_start=-report_datas[line]['balance_start']
                else:
                    balance_start=abs(report_datas[line]['balance_start'])
            else:
                if report_datas[line]['balance']>0:
                    balance=report_datas[line]['balance']
                else:
                    balance=(report_datas[line]['balance'])
                if report_datas[line]['balance_start']>0:
                    balance_start=report_datas[line]['balance_start']
                else:
                    balance_start=(report_datas[line]['balance_start'])                    
#             balance+=balance_start
            if report_datas[line]['is_bold']:
                text=text_bold_xf
                number=number_bold_xf
            if not report_datas[line]['is_number']:
                balance=''
                balance_start=''
            name=report_datas[line]['name']
            if self.lang_type=='en':
                name=report_datas[line]['name_en']
                
            sheet.write(rowx, 0, report_datas[line]['number'],text)
            sheet.write(rowx, 1, name, text)
            sheet.write(rowx, 2, balance_start, number)
            sheet.write(rowx, 3, balance, number)

#             sheet.write(rowx, 4, line[4], number_xf)
#             sheet.write(rowx, 5, line[5], number_xf)
#             sheet.write(rowx, 6, line[6], number_xf)
#             sheet.write(rowx, 7, line[7], number_xf)
#             sheet.write(rowx, 8, line[8], number_xf)
 
        #sheet.set_panes_frozen(True) # frozen headings instead of split panes
        #sheet.set_horz_split_pos(2) # in general, freeze after last heading row
        #sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
        #sheet.set_col_default_width(True)
        inch = 3000
        sheet.col(0).width = int(0.7*inch)
        sheet.col(1).width = int(4.5*inch)
        sheet.col(2).width = int(2*inch)
        sheet.col(3).width = int(2*inch)
        sheet.row(7).height = 500
         
        # sheet.write(rowx+2, 1, u'Боловсруулсан нягтлан бодогч.........................................../\
        #                                          /',ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
        sheet.write(rowx+2, 1,  u'Боловсруулсан нягтлан бодогч.........................................../ %s /' %(self.env.user.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))


        sheet.write(rowx+4, 1, u'Хянасан ерөнхий нягтлан бодогч....................................../\
                                                 /', ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
        sheet.write(rowx+6, 1, u"Тайлан татсан огноо: %s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)
        
        filename = "balance_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
        out = encodestring(buffer.getvalue())
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

