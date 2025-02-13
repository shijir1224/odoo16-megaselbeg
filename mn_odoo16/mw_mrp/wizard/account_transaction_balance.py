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
    from base64 import encodestring
except ImportError:
    from base64 import encodebytes as encodestring
    
import time
import datetime
from datetime import datetime

import xlwt
import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

from io import BytesIO
import xlsxwriter
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles

# _logger = logging.getLogger('odoo')

class AccountTransactionBalanceReport(models.TransientModel):
    """
        Монголын Сангийн Яамнаас баталсан Гүйлгээ Баланс тайлан.
    """
    
    _inherit = "account.transaction.balance.report.new"
    
    is_not_st = fields.Boolean(string='Стандарт өртгийн бичилтгүй?', )
    
#     @api.model
    def create_report_data(self, data,accounts=False):
        ''' Гүйлгээ баланс тайлангийн мэдээллийг боловсруулж
            тайлангийн форматад тохируулан python [{},{},{}...]
            загвараар хүснэгтийн мөр багануудын өгөгдлийг боловсруулна.
            
        '''
        initial_account_ids = []
#         
        account_dict = {}
        account_ids = None
        if accounts:
            account_ids=accounts
        elif self.chart_account_ids:
                account_ids = self.chart_account_ids
        elif self.chart_account_type:
            group_ids = self.env['account.code.type'].search([('id','child_of',self.chart_account_type.ids)])
            account_ids=self.env['account.account'].search([('code_group_id','in',group_ids.ids)])
        else:
            account_ids=self.env['account.account'].search([('company_id','=',self.company_id.id)])
        lines = []
#         include_initial_balance Түр данс бол эхнйи үлдэгдэлгүй
#         context=data['used_context']
        number = 1
        sum_debit = sum_credit = sum_sdebit = sum_scredit = sum_edebit = sum_ecredit = 0.0
        currency_dict={}
        mrp_move_ids=[]
        if self.is_not_st:
            query = """
                    select move_id from mrp_prod_account_move_st_rel 
                """
            self.env.cr.execute(query)
            move_result = self.env.cr.fetchall()                      
            for rr in  move_result:    
                mrp_move_ids.append(rr[0])

            query = """
                    select move_id from mrp_prod_account_move_st_close_rel 
                """
            self.env.cr.execute(query)
            move_result = self.env.cr.fetchall()                      
            for rr in  move_result:    
                mrp_move_ids.append(rr[0])                
                
        for account_id in account_ids:
            data=self.read()[0]
            if len(mrp_move_ids)>0:
                data['extra_domain'] = [('move_id', 'not in', mrp_move_ids)]
            # print ('data111 ',data)
            data['company_id'] = self.company_id.id
            if self.branch_id:
                data['branch_id'] = self.branch_id.id
            if self.branch_ids:
                data['branch_ids'] = self.branch_ids.ids
            data['strict_range'] = True if self.date_from else False  
            data['state']='posted'
            
            
              
            account=account_id.with_context(data) 
            has_move = False
            has_balance = False
# #            print "accountaccountaccount ",account
#             # Тайлант хугацааны дүн
#             print "account_data ",account_data
#             debit = account_data['debit']
#             credit = account_data['credit']
            debit=account.debit
            credit=account.credit
            currency_list=[]
            is_curr=False
            if data['check_balance_method']:
                start_credit = start_debit =0
                if account.balance_start:
#                     if account.user_type_id.balance_type =='passive':
                    if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):

#                         if account.user_type_id.include_initial_balance:
                        start_credit = -account.balance_start
                        start_debit = 0
                    else:
                        start_credit = 0
#                         if account.user_type_id.include_initial_balance:
                        start_debit = account.balance_start
                else:
                    start_credit=0
                    start_debit=0
#                 if account.user_type_id.balance_type =='passive':
                if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):
                    if credit==0 and debit==0:
                        end_credit = start_credit
                        end_debit=0
#                     elif debit>credit:
                    else:
                        end_credit = start_credit + credit - debit
                        end_debit=0
                        
                else:
                    if credit==0 and debit==0:
                        end_debit = start_debit
                        end_credit = 0
                    else:
                        end_debit = start_debit + debit - credit
                        end_credit = 0
                if self.is_currency:
                    query = """
                            (select 'start' as name, sum(amount_currency) as debit, 0 as credit,aml.currency_id,account_id 
                                                from account_move_line aml 
                                                        left join account_move m on aml.move_id=m.id 
                                                where aml.date<'{0}' 
                                                    and m.state='posted' 
                                                    and amount_currency <>0 
                                                    and account_id ={2}
                                                    and m.company_id = {3}
                                                group by aml.currency_id,account_id
                             )
                             union all
                             (select 'debit' as name, sum(amount_currency) as debit, 0 as credit,aml.currency_id,account_id 
                                                from account_move_line aml 
                                                        left join account_move m on aml.move_id=m.id 
                                                where aml.date between '{0}' and '{1}'
                                                    and m.state='posted' 
                                                    and amount_currency >0 
                                                    and account_id ={2}
                                                    and m.company_id = {3}
                                                group by aml.currency_id,account_id
                             )
                              union all
                             (select 'credit' as name, 0 as debit, sum(amount_currency) as credit,aml.currency_id,account_id 
                                                from account_move_line aml 
                                                        left join account_move m on aml.move_id=m.id 
                                                where aml.date between '{0}' and '{1}'
                                                    and m.state='posted' 
                                                    and amount_currency <0 
                                                    and account_id ={2}
                                                    and m.company_id = {3}
                                                group by aml.currency_id,account_id
                             )
                        """.format(self.date_from,self.date_to,account.id,self.company_id.id)
#                     print ('query22 ',query)
                    self.env.cr.execute(query)
                    query_result = self.env.cr.dictfetchall()                      
#                     print ('query_result22',query_result)
                    cstart=0
                    cdebit=0
                    ccredit=0
                    currency_id=False
                    if account.currency_id:
                        currname=account.currency_id.name
                        for i in query_result:
                            if not currname and i['currency_id']:
                                currname=self.env['res.currency'].browse(i['currency_id']).name
                            if currency_id!=i['currency_id']:
                                print ('==========================================')
                            currency_id=i['currency_id']
                            if i['name']=='start' and i.get('debit',0):
                                cstart+=i['debit']
                            elif i['name']=='debit' and i.get('debit',0):
                                cdebit+=i['debit']
                            if i['name']=='credit' and i.get('credit',0):
                                ccredit+=i['credit']
                            is_curr=True
                        
                        currency_list.append
                        cend=cstart+cdebit+ccredit
                        currency_list=[ '', account.code+'', currname, cstart>0 and cstart or 0, cstart<0 and cstart or 0,cdebit, ccredit, cend>0 and cend or 0, cend<0 and cend or 0, False ]

                if debit != 0 or credit != 0 or start_credit !=0 or start_debit !=0:
                    has_move = True # Тухайн тайлант хугацаанд гүйлгээ хийсэн байвал тайланд тусгана.

            else:
                acc=self.env['account.account'].browse(account.id)
#                 if account.user_type_id.balance_type =='passive':
                if account.balance_start<0:
                    if account.balance_start!=0:
                        start_credit =  abs(account.balance_start)
                        start_debit = 0.0
                        end_debit = 0.0
                    else:
                        start_credit=0
                        start_debit=0
                    end_credit = start_credit + credit - debit
                else :
                    if account.balance_start!=0:
                        start_debit = abs(account.balance_start)
                        start_credit = 0.0
                    else:
                        start_credit=0
                        start_debit=0
                    end_debit = start_debit + debit - credit
                    end_credit = 0.0
                if end_debit<0:
                    end_credit = abs(end_debit)
                    end_debit=0
                elif end_credit<0:
                    end_debit = abs(end_credit)
                    end_credit=0
                if end_debit != 0 or end_credit != 0 or start_debit != 0 or start_credit != 0 :
                    has_balance = True # Тухайн тайлант хугацаанд үлдэгдэлтэй байвал тайланд тусгана.
            if not has_balance and not has_move :
                continue
#             
            sum_debit += debit
            sum_credit += credit
            sum_sdebit += start_debit
            sum_scredit += start_credit
            sum_edebit += end_debit
            sum_ecredit += end_credit
#             lines.append([ str(number), account_data['code'], account_data['name'], start_debit, start_credit,
#                 credit, credit, end_debit, end_credit ])
            lines.append([ str(number), account.code, account.name, start_debit, start_credit,
                debit, credit, end_debit, end_credit, False ])
            if is_curr:
                lines.append(currency_list)
#             lines.append([ str(number), account.code, account.name, start_debit, start_credit,
#                 debit, credit, end_debit, end_credit ])
            number += 1
        sums =[sum_sdebit, sum_scredit, sum_debit, sum_credit, sum_edebit, sum_ecredit]
#         sum_line = [['', u'Нийт дүн', '', sum_sdebit, sum_scredit, sum_debit, sum_credit, sum_edebit, sum_ecredit,True]]
        lines.sort(key=lambda x:x[1])
#         return sum_line + lines    
        return lines,sums

    def check_report(self,):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
         
        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
        data['form']['company_id'] = form['company_id'][0]
        data['form']['account_ids'] = data['form']['chart_account_ids']
        data['form']['state'] = 'posted'
#         data['form']['company_type'] = data['form']['company_type']
        data['form']['check_balance_method'] = form['check_balance_method']
        data['form']['is_categ'] = form['is_categ']
        data['form']['is_parent'] = form['is_parent']
        return self._make_excel(data)
    
    def _make_excel(self, data):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        datas = data
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        account_obj = self.pool.get('account.account')
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Transfer Balance')

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)
        
        h2 = workbook.add_format()
        h2.set_font_size(9)

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#6495ED')

        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(9)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        header_wrap.set_bg_color('#6495ED')

        footer = workbook.add_format({'bold': 1})
        footer.set_text_wrap()
        footer.set_font_size(9)
        footer.set_align('right')
        footer.set_align('vcenter')
        footer.set_border(style=1)
        footer.set_bg_color('#F0FFFF')
        footer.set_num_format('#,##0.00')
        footer.set_font_name('Times New Roman')
        

        content_color_float = workbook.add_format()
        content_color_float.set_text_wrap()
        content_color_float.set_font_size(9)
        content_color_float.set_align('right')
        content_color_float.set_align('vcenter')
        content_color_float.set_border(style=1)
        content_color_float.set_bg_color('#87CEFA')
        content_color_float.set_num_format('#,##0.00')        

        format_name = {
            'font_name': 'Times New Roman',
            'font_size': 14,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter'
        }
        # create formats
        format_content_text_footer = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'align': 'vcenter',
        'valign': 'vcenter',
        }
        format_content_right = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
        }
        format_group_center = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        }
        format_group = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5',
        'num_format': '#,##0.00'
        }
        
        format_group_center = workbook.add_format(format_group_center)
        format_name = workbook.add_format(format_name)
        format_content_text_footer = workbook.add_format(format_content_text_footer)
        format_filter = workbook.add_format(ReportExcelCellStyles.format_filter)
        format_title = workbook.add_format(ReportExcelCellStyles.format_title)
        format_group_right = workbook.add_format(ReportExcelCellStyles.format_group_right)
        format_group_float = workbook.add_format(ReportExcelCellStyles.format_group_float)
        format_group_left = workbook.add_format(ReportExcelCellStyles.format_group_left)
        format_content_text = workbook.add_format(ReportExcelCellStyles.format_content_text)
        format_content_number = workbook.add_format(ReportExcelCellStyles.format_content_number)
        format_content_float = workbook.add_format(ReportExcelCellStyles.format_content_float)
        format_content_center = workbook.add_format(ReportExcelCellStyles.format_content_center)
        format_group = workbook.add_format(format_group)

        format_content_right = workbook.add_format(format_content_right)             
        
        worksheet.write(0, 1, u'Маягт ГБ', h2)
        worksheet.write(0, 5, u'Байгууллагын нэр: %s' %(self.company_id.name), h2)
        
        worksheet.write(2, 3, u'ГҮЙЛГЭЭ БАЛАНС', h1)
        worksheet.write(3, 1, u'Дугаар:', h2)
        worksheet.write(3, 6, u'Огноо: %s' %(time.strftime('%Y-%m-%d'),), h2)
        worksheet.write(5, 5, u'Тайлан хугацаа: %s - %s'%
                (self.date_from,
                 self.date_to
                 ),h2)

        rowx = 7
        worksheet.merge_range(rowx, 0,rowx+1,  0, u'Д/д', format_title)
        worksheet.merge_range(rowx, 1,rowx+1,  1, u'Дансны дугаар', format_title)
        worksheet.merge_range(rowx, 2, rowx+1, 2, u'Дансны нэр', format_title)
        worksheet.merge_range(rowx, 3, rowx, 4, u'Эхний үлдэгдэл', format_title)
        worksheet.merge_range(rowx, 5, rowx+1, 5, u'Дебет гүйлгээ', format_title)
        worksheet.merge_range(rowx, 6, rowx+1, 6, u'Кредит гүйлгээ', format_title)
        worksheet.merge_range(rowx, 7, rowx, 8, u'Эцсийн үлдэгдэл', format_title)
        rowx += 1
        worksheet.write(rowx, 3, u'Дебет', format_title)
        worksheet.write(rowx, 4, u'Кредит', format_title)
        worksheet.write(rowx, 7, u'Дебет', format_title)
        worksheet.write(rowx, 8, u'Кредит', format_title)
        rowx += 1
        
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 22)
        worksheet.set_column('D:I', 16)

#         if data['form']['is_categ']:
#             worksheet.merge_range(rowx, rowx, 0, 0, u'', format_title)
                
        if not self.is_categ:
            report_datas,sums = self.create_report_data(data)
            
            rowx += 1
            worksheet.write(rowx, 0, u'', footer)
            worksheet.merge_range(rowx, 1,rowx, 2, u'НИЙТ ДҮН', footer)
            worksheet.write(rowx, 3, sums[0], footer)
            worksheet.write(rowx, 4, sums[1], footer)
            worksheet.write(rowx, 5, sums[2], footer)
            worksheet.write(rowx, 6, sums[3], footer)
            worksheet.write(rowx, 7, sums[4], footer)
            worksheet.write(rowx, 8, sums[5], footer)
 
            for line in report_datas:
                rowx += 1
                if  line[9]:
                    worksheet.write(rowx, 0, line[0], format_title)
                    worksheet.write(rowx, 1, line[1], format_title)
                    worksheet.write(rowx, 2, line[2], format_title)
                    worksheet.write(rowx, 3, line[3], format_title)
                    worksheet.write(rowx, 4, line[4], format_title)
                    worksheet.write(rowx, 5, line[5], format_title)
                    worksheet.write(rowx, 6, line[6], format_title)
                    worksheet.write(rowx, 7, line[7], format_title)
                    worksheet.write(rowx, 8, line[8], format_title)
                else:
                    if line[0]=='':
    #                     format_content_float=format_title
                        worksheet.write(rowx, 0, line[0], format_content_text)
                        worksheet.write(rowx, 1, line[1], content_color_float)
                        worksheet.write(rowx, 2, line[2], content_color_float)
                        worksheet.write(rowx, 3, line[3], content_color_float)
                        worksheet.write(rowx, 4, line[4], content_color_float)
                        worksheet.write(rowx, 5, line[5], content_color_float)
                        worksheet.write(rowx, 6, line[6], content_color_float)
                        worksheet.write(rowx, 7, line[7], content_color_float)
                        worksheet.write(rowx, 8, line[8], content_color_float)    
                    else:
                        worksheet.write(rowx, 0, line[0], format_content_text)
                        worksheet.write(rowx, 1, line[1], format_content_text)
                        worksheet.write(rowx, 2, line[2], format_content_text)
                        worksheet.write(rowx, 3, line[3], format_content_float)
                        worksheet.write(rowx, 4, line[4], format_content_float)
                        worksheet.write(rowx, 5, line[5], format_content_float)
                        worksheet.write(rowx, 6, line[6], format_content_float)
                        worksheet.write(rowx, 7, line[7], format_content_float)
                        worksheet.write(rowx, 8, line[8], format_content_float)  
        else:
            if self.chart_account_type:
                type_ids = self.env['account.code.type'].search([('id','child_of',self.chart_account_type.ids),
                                                                 ('account_ids','!=',False)])
            else:
                type_ids= self.env['account.code.type'].search([])
            print ('type_ids ',type_ids)
            for gr_type in type_ids:
                account_ids=self.env['account.account'].search([('code_group_id','=',gr_type.id)])
                if account_ids:
                    print ('gr_type:::: ',gr_type.name)
                    print ('account_ids++++ ',account_ids)
                    data['form'].update({'chart_account_ids':account_ids.ids})
                    report_datas,sums = self.create_report_data(data['form'],account_ids)
                    
                    rowx += 1
                    worksheet.write(rowx, 0, u'', footer)
                    worksheet.merge_range(rowx, 1,rowx, 2, u'ДҮН {0} '.format(gr_type.name), footer)
                    worksheet.write(rowx, 3, sums[0], footer)
                    worksheet.write(rowx, 4, sums[1], footer)
                    worksheet.write(rowx, 5, sums[2], footer)
                    worksheet.write(rowx, 6, sums[3], footer)
                    worksheet.write(rowx, 7, sums[4], footer)
                    worksheet.write(rowx, 8, sums[5], footer)
         
                    for line in report_datas:
                        rowx += 1
                        print ('line ',line)
                        if  line[9]:
                            worksheet.write(rowx, 0, line[0], format_title)
                            worksheet.write(rowx, 1, line[1], format_title)
                            worksheet.write(rowx, 2, line[2], format_title)
                            worksheet.write(rowx, 3, line[3], format_title)
                            worksheet.write(rowx, 4, line[4], format_title)
                            worksheet.write(rowx, 5, line[5], format_title)
                            worksheet.write(rowx, 6, line[6], format_title)
                            worksheet.write(rowx, 7, line[7], format_title)
                            worksheet.write(rowx, 8, line[8], format_title)
                        else:
                            if line[0]=='':
            #                     format_content_float=format_title
                                worksheet.write(rowx, 0, line[0], format_content_text)
                                worksheet.write(rowx, 1, line[1], content_color_float)
                                worksheet.write(rowx, 2, line[2], content_color_float)
                                worksheet.write(rowx, 3, line[3], content_color_float)
                                worksheet.write(rowx, 4, line[4], content_color_float)
                                worksheet.write(rowx, 5, line[5], content_color_float)
                                worksheet.write(rowx, 6, line[6], content_color_float)
                                worksheet.write(rowx, 7, line[7], content_color_float)
                                worksheet.write(rowx, 8, line[8], content_color_float)    
                            else:
                                worksheet.write(rowx, 0, line[0], format_content_text)
                                worksheet.write(rowx, 1, line[1], format_content_text)
                                worksheet.write(rowx, 2, line[2], format_content_text)
                                worksheet.write(rowx, 3, line[3], format_content_float)
                                worksheet.write(rowx, 4, line[4], format_content_float)
                                worksheet.write(rowx, 5, line[5], format_content_float)
                                worksheet.write(rowx, 6, line[6], format_content_float)
                                worksheet.write(rowx, 7, line[7], format_content_float)
                                worksheet.write(rowx, 8, line[8], format_content_float)
            #Группгүй дансдыг нэг гаргачихий
            if not self.chart_account_type:
                account_ids=self.env['account.account'].search([('code_group_id','=',False)])
                if account_ids:
                        data['form'].update({'chart_account_ids':account_ids.ids})
                        report_datas,sums = self.create_report_data(data['form'],account_ids)
                        
                        rowx += 1
                        worksheet.write(rowx, 0, u'', footer)
                        worksheet.merge_range(rowx, 1,rowx, 2, u'ДҮН АНГИЛАЛГҮЙ', footer)
                        worksheet.write(rowx, 3, sums[0], footer)
                        worksheet.write(rowx, 4, sums[1], footer)
                        worksheet.write(rowx, 5, sums[2], footer)
                        worksheet.write(rowx, 6, sums[3], footer)
                        worksheet.write(rowx, 7, sums[4], footer)
                        worksheet.write(rowx, 8, sums[5], footer)
             
                        for line in report_datas:
                            rowx += 1
                            if  line[9]:
                                worksheet.write(rowx, 0, line[0], format_title)
                                worksheet.write(rowx, 1, line[1], format_title)
                                worksheet.write(rowx, 2, line[2], format_title)
                                worksheet.write(rowx, 3, line[3], format_title)
                                worksheet.write(rowx, 4, line[4], format_title)
                                worksheet.write(rowx, 5, line[5], format_title)
                                worksheet.write(rowx, 6, line[6], format_title)
                                worksheet.write(rowx, 7, line[7], format_title)
                                worksheet.write(rowx, 8, line[8], format_title)
                            else:
                                if line[0]=='':
                #                     format_content_float=format_title
                                    worksheet.write(rowx, 0, line[0], format_content_text)
                                    worksheet.write(rowx, 1, line[1], content_color_float)
                                    worksheet.write(rowx, 2, line[2], content_color_float)
                                    worksheet.write(rowx, 3, line[3], content_color_float)
                                    worksheet.write(rowx, 4, line[4], content_color_float)
                                    worksheet.write(rowx, 5, line[5], content_color_float)
                                    worksheet.write(rowx, 6, line[6], content_color_float)
                                    worksheet.write(rowx, 7, line[7], content_color_float)
                                    worksheet.write(rowx, 8, line[8], content_color_float)    
                                else:
                                    worksheet.write(rowx, 0, line[0], format_content_text)
                                    worksheet.write(rowx, 1, line[1], format_content_text)
                                    worksheet.write(rowx, 2, line[2], format_content_text)
                                    worksheet.write(rowx, 3, line[3], format_content_float)
                                    worksheet.write(rowx, 4, line[4], format_content_float)
                                    worksheet.write(rowx, 5, line[5], format_content_float)
                                    worksheet.write(rowx, 6, line[6], format_content_float)
                                    worksheet.write(rowx, 7, line[7], format_content_float)
                                    worksheet.write(rowx, 8, line[8], format_content_float)            
                                                                             
        inch = 3000
         
        worksheet.write(rowx+2, 2, u'Боловсруулсан нягтлан бодогч.........................................../\
                                                 /',h2)
        worksheet.write(rowx+4, 2, u'Хянасан ерөнхий нягтлан бодогч....................................../\
                                                 /', h2)
        from io import StringIO
        file_name = "transfer_balance_%s.xlsx" % (time.strftime('%Y%m%d_%H%M'),)
        workbook.close()
        out = encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
        
    def create_report_data_pivot(self, data):
        initial_account_ids = []
#         
        account_dict = {}
        account_ids = None
        if self.chart_account_ids:
            account_ids = self.chart_account_ids
        else:
            account_ids=self.env['account.account'].search([('company_id','=',self.company_id.id)])
        lines = []
#         include_initial_balance Түр данс бол эхнйи үлдэгдэлгүй
#         context=data['used_context']
        number = 1
        sum_debit = sum_credit = sum_sdebit = sum_scredit = sum_edebit = sum_ecredit = 0.0
        for account_id in account_ids:
            data['used_context']['company_id']=data['company_id']
            data['used_context']['state']='posted'
            account=account_id.with_context(data.get('used_context',{})) 
            has_move = False
            has_balance = False
# #            print "accountaccountaccount ",account
            debit=account.debit
            credit=account.credit
            if data['check_balance_method']:
                if account.balance_start:
#                     if account.balance_start>0:
#                         start_credit = 0
#                         start_debit = account.balance_start
#                     else:
#                         start_credit = account.balance_start
#                         start_debit = 0
#                     if account.user_type_id.name in ('Payable','Current Liabilities','Non-current Liabilities','Equity',
#                                               'Current Year Earnings','Other Income','Income'):
#                     if account.user_type_id.balance_type =='passive':
                    if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):

#                         if account.user_type_id.include_initial_balance:
                        start_credit = -account.balance_start
                        start_debit = 0
                    else:
                        start_credit = 0
#                         if account.user_type_id.include_initial_balance:
                        start_debit = account.balance_start
                else:
                    start_credit=0
                    start_debit=0
#                 if account.user_type_id.balance_type =='passive':
                if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):

                    if credit==0 and debit==0:
                        end_credit = start_credit
                        end_debit=0
#                     elif debit>credit:
                    else:
                        end_credit = start_credit + credit - debit
                        end_debit=0
                        
                else:
                    if credit==0 and debit==0:
                        end_debit = start_debit
                        end_credit = 0
                    else:
                        end_debit = start_debit + debit - credit
                        end_credit = 0

            if debit != 0 or credit != 0 or start_credit !=0 or start_debit !=0:
                has_move = True # Тухайн тайлант хугацаанд гүйлгээ хийсэн байвал тайланд тусгана.
                

            else:
                acc=self.env['account.account'].browse(account.id)
#                 if acc.user_type_id.name in ('Payable','Current Liabilities','Non-current Liabilities','Equity',
#                                           'Current Year Earnings','Other Income','Income'):
#                 if account.user_type_id.balance_type =='passive':
                if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):

                    if account.balance_start:
#                         start_credit =  initial_bals[account_data['id']][0]['credit'] - initial_bals[account_data['id']][0]['debit']
#                         if account.user_type_id.include_initial_balance:
                        start_credit =  abs(account.balance_start)
                        start_debit = 0.0
                        end_debit = 0.0
                    else:
                        start_credit=0
                        start_debit=0
                    end_credit = start_credit + credit - debit
                else :
                    if account.balance_start:
#                         start_debit = initial_bals[account_data['id']][0]['debit'] - initial_bals[account_data['id']][0]['credit']
#                         if account.user_type_id.include_initial_balance:
                        start_debit = abs(account.balance_start)
                        start_credit = 0.0
                    else:
                        start_credit=0
                        start_debit=0
                    end_debit = start_debit + debit - credit
                    end_credit = 0.0
             
            if end_debit != 0 or end_credit != 0 or start_debit != 0 or start_credit != 0 :
                has_balance = True # Тухайн тайлант хугацаанд үлдэгдэлтэй байвал тайланд тусгана.
            if not has_balance and not has_move :
                continue
#             
#             lines.append([ str(number), account_data['code'], account_data['name'], start_debit, start_credit,
#                 credit, credit, end_debit, end_credit ])
            lines.append([ account, start_debit, start_credit,
                debit, credit, end_debit, end_credit ])

#             lines.append([ str(number), account.code, account.name, start_debit, start_credit,
#                 debit, credit, end_debit, end_credit ])
            number += 1
# 
#         print "lines:::::::::::::::::::::::::::::",lines
        lines.sort(key=lambda x:x[1])
        return lines    
    

    def get_domain(self, domain, donwload=False):
        domain_val = ''
        account_ids=[]
        if self.chart_account_ids:
            account_ids = self.chart_account_ids
        elif self.chart_account_type:
            group_ids = self.env['account.code.type'].search([('id','child_of',self.chart_account_type.ids)])
            account_ids=self.env['account.account'].search([('code_group_id','in',group_ids.ids)])
        else:
            account_ids=self.env['account.account'].search([('company_id','=',self.company_id.id)])        
        # domain.append(('date','!=',False))
        if self.branch_id:
            domain.append(('branch_id','=',self.branch_id.id))
        if self.branch_ids:
            domain.append(('branch_id','in',self.branch_ids.ids))
            
        domain.append(('move_id.state','=','posted'))
        if account_ids:
            domain.append(('account_id','in',account_ids.ids))
        domain.append('|')
        # domain.append(('date','!=',False))
        domain.append(('date_init','<',self.date_from))
        domain.append('&')
        domain.append(('date','<=',self.date_to))
        domain.append(('date','>=',self.date_from))

        mrp_move_ids=[]
        if self.is_not_st:
            query = """
                    select move_id from mrp_prod_account_move_st_rel 
                """
            self.env.cr.execute(query)
            move_result = self.env.cr.fetchall()                      
            for rr in  move_result:    
                mrp_move_ids.append(rr[0])

            query = """
                    select move_id from mrp_prod_account_move_st_close_rel 
                """
            self.env.cr.execute(query)
            move_result = self.env.cr.fetchall()                      
            for rr in  move_result:    
                mrp_move_ids.append(rr[0])                
        if len(mrp_move_ids)>0:
            domain.append(('move_id','not in',mrp_move_ids))
                
        return domain    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
