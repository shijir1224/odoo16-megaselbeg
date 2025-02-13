# -*- coding: utf-8 -*-
from datetime import datetime
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time
from odoo import api, models, fields, _

import xlwt
from xlwt import *
import base64
# from report_excel_cell_styles import ReportExcelCellStyles
from odoo.addons.mw_asset.report.report_excel_cell_styles import ReportExcelCellStyles

class AccountAssetStandardReportData(models.TransientModel):

    _name = 'account.asset.report.data'
#     _order = 'category_id ASC'
    _rec_name = 'asset_id'

    wizard_id = fields.Many2one(
        comodel_name='account.asset.report.standard.ledger',
        ondelete='cascade',
        index=True
    )

    report_id = fields.Many2one(
        comodel_name='account.asset.report.standard.ledger.report',
        ondelete='cascade',
        index=True
    )    

    report_obj_id = fields.Many2one(
        comodel_name='account.asset.report.standard.object',
        ondelete='cascade',
        index=True
    )    

    account_id = fields.Many2one(
        'account.account',
        index=True
    )
    asset_id = fields.Many2one(
        'account.asset',
        index=True
    )
    
    group_id = fields.Many2one(
        'account.asset.group',
        index=True
    )

#     category_id = fields.Many2one(
#         'account.asset.category',
#         index=True
#     )

#     code = fields.Char()
#     name = fields.Char()
    qty = fields.Float(digits=(16, 2))
    date = fields.Date(digits=(16, 2))
    asset_acquisition_date = fields.Date(digits=(16, 2))
    initial_value = fields.Float(digits=(16, 2))
    income_value = fields.Float(digits=(16, 2))
    capital_value = fields.Float(digits=(16, 2))
    expense_value = fields.Float(digits=(16, 2))
    final_value = fields.Float(digits=(16, 2))

    initial_depr = fields.Float(digits=(16, 2))
    income_depr = fields.Float(digits=(16, 2))
    capital_depr = fields.Float(digits=(16, 2))
    expense_depr = fields.Float(digits=(16, 2))
    final_depr = fields.Float(digits=(16, 2))
    salvage_value = fields.Float(digits=(16, 2))
    first_value = fields.Float(digits=(16, 2))
    last_value = fields.Float(digits=(16, 2))
    owner = fields.Char('owner')
    branch = fields.Char('branch')
    serial = fields.Char('Serial')
    number = fields.Char('Number')

    department = fields.Char('department')
    job = fields.Char('job')
    internal_code = fields.Char('internal_code')
    location = fields.Char('location')
    close_status = fields.Char('close_status')
    car_number = fields.Char(string='Машины дугаар')
    car_vat = fields.Char(string='Арлын дугаар')
    car_color = fields.Char(string='Машины өнгө')
    asset_type_name = fields.Char(string='Хөрөнгийн төрөл')


#tur asiglahgui
    first_depr_date = fields.Date(digits=(16, 2))

class AccountAssetStandardExcel(models.AbstractModel):
    _name = 'report.account_asset_report.standard_excel'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        print ('456788')
        num_format = '# ##0,00_);(# ##0,00)'#wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        lang_id = self.env['res.lang']._lang_get(lang_code)
        date_format = '%Y-%m-%d'

        report = wizard#.report_id

        def _get_data_float(data):
            if data == None or data == False:
                return 0.0
            else:
                return round(data,2) + 0.0

        def get_date_format(date):
            if date:
#                 date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
                date = date.strftime(date_format)
            return date

        def _header_sheet(sheet):
            sheet.write(0, 4, u'Үндсэн хөрөнгийн дэлгэрэнгүй тайлан', report_format)
            sheet.write(2, 0, _(u'Компани:'), bold)
            sheet.write(3, 0, wizard.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))#report.print_time)

            sheet.write(2, 2, _(u'Эхлэх огноо : %s ') % wizard.date_from if wizard.date_from else '')
            sheet.write(3, 2, _(u'Дуусах огноо : %s ') % wizard.date_to if wizard.date_to else '')

#             sheet.write(2, 4, _('Target Moves:'), bold)
#             sheet.write(3, 4, _('All Entries') )
# 
#             sheet.write(2, 6, _('Only UnReconciled Entries') , bold)

        if True:
            if report.old_temp:
                
#                 file_name = "%s_%s.xls" % (report.name, time.strftime('%Y%m%d_%H%M'),)
                # Custom for standart
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
                'bg_color': '#eaf4fb',
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
                if report.is_owner:
                    #эд хариуцагч
                    sheet = workbook.add_worksheet('Assets')
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 15)
                    sheet.set_column('C:C', 25)
                    sheet.set_column('D:D', 6)
                    sheet.set_column('E:E', 8)
                    sheet.set_column('F:F', 15)
                    sheet.set_column('G:G', 18)
                    sheet.set_column('H:H', 15)
                    sheet.set_column('I:I', 15)
                    sheet.set_column('J:J', 15)
            
                    rowx = 0
                    # create name
                    sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
                    rowx += 1
                    sheet.merge_range(rowx, 1, rowx, 7, u'Хөрөнгийн карт', format_name)
                    if hasattr(wizard, 'owner_emp_id') and wizard.owner_emp_id:                    
#                     if wizard.owner_emp_id:
                        rowx += 1
                        sheet.merge_range(rowx, 1, rowx, 7, u'Эд хариуцагч {0}'.format(wizard.owner_emp_id.name), format_filter)
                    # report duration
                    sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                    # create date
                    sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                    rowx += 3
            
                    sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                    sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн дугаар'), format_title)  # Хөрөнгийн дугаар
                    sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Үндсэн хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
                    sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Элэгдэх сар'), format_title)  # Элэгдэх тоо
                    sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
                    sheet.merge_range(rowx, 5, rowx + 2, 5, _(u'Өртөг'), format_title)  # Өртөг
                    sheet.merge_range(rowx, 6, rowx + 2, 6, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
                    sheet.merge_range(rowx, 7, rowx + 2, 7, _(u'Байршил'), format_title)  # Байршил
                    sheet.merge_range(rowx, 8, rowx + 2, 8, _(u'А/Тушаал'), format_title)  # Байршил
                    sheet.merge_range(rowx, 9, rowx + 2, 9, _(u'Хэлтэс'), format_title)  # Байршил
                    sheet.merge_range(rowx, 10, rowx + 2, 10, _(u'Сериал'), format_title)  # Байршил
                    sheet.merge_range(rowx, 11, rowx + 2, 11, _(u'Тоо хэмжээ'), format_title)  # Байршил
                    rowx += 3
                    
                    def _set_line(line):
#                         print 'line2 ',line
    #                     print '11i',i
                        sheet.write(i, 0, n ,format_content_text)
                        sheet.write(i, 1, line.get('code', ''),format_content_text)
                        sheet.write(i, 2, line.get('name', ''),format_content_text)
    #                     sheet.write(i, 3, '1',format_content_text)
                        sheet.write(i, 3, line.get('method_number', ''), format_content_right)
                        sheet.write(i, 4, get_date_format(line.get('date', '')),format_content_text)
                        sheet.write(i, 5, _get_data_float(line.get('initial_value', '')), format_content_right)
                        sheet.write(i, 6, line.get('owner', ''),format_content_text)
                        sheet.write(i, 7, line.get('branch', ''),format_content_text)
                        sheet.write(i, 8, line.get('job', ''),format_content_text)
                        sheet.write(i, 9, line.get('department', ''),format_content_text)
                        sheet.write(i, 10, line.get('serial', ''),format_content_text)
                        sheet.write(i, 11, '1',format_content_text)
                    row = 7
                    report = wizard.report_id
                    all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'all_lines---------------- ',len(all_lines)
                    totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'totals-------- ',totals
    
                    i=row
                    n=''
                    if totals[0]['income_value'] and totals[0]['final_value']:
                        _set_line(totals[0])
    #                 row += 1
                    for obj in report.report_object_ids:
    #                     print 'obj ',obj
                        lines_obj = []
        #                 obj_id = obj.id
                        obj_id = obj.id
                        for line in all_lines:
    #                         print 'line ',line
                            if line.get('report_obj_id') == obj_id:
                                lines_obj.append(line)
    #                     print 'lines_obj ',lines_obj
                        if lines_obj:
                            row += 1
                            name_view = ''
    #                         if wizard.type == 'account':
    #                             name_view = obj.account_id.display_name
    #                         if wizard.type == 'partner':
    #                             name_view = obj.partner_id.display_name
    #                         if wizard.type == 'journal':
    #                             name_view = obj.journal_id.display_name
    #                         if wizard.type == 'analytic':
    #                             name_view = obj.analytic_account_id.display_name
                            name_view = obj.account_id.name
    #                         print 'name_view ',name_view
                            sheet.write(row, 0, name_view, left)
                            sheet.write(row, 1, '', top)
                            sheet.write(row, 2, '', top)
                            sheet.write(row, 3, '', top)
                            sheet.write(row, 4, '', top)
                            sheet.write(row, 5, '', top)
                            sheet.write(row, 6, '', top)
                            sheet.write(row, 7, '', top)
#                             sheet.write_formula(row, 5,'{=sum('+ self._symbol(row+1, 5)+':'+ self._symbol(row+len(lines_obj),5) +')}', top)
    
                            row += 1
                            start_row = row
                            n=1
                            for i, line in enumerate(lines_obj):
                                i += row
                                _set_line(line)
                                n+=1
                            row = i
                            
                    rowx  +=1+row                          
                    if hasattr(wizard, 'owner_emp_id') and wizard.owner_emp_id:  
#                     if wizard.owner_emp_id:
                        sheet.merge_range(rowx, 1, rowx, 7, u'Эд хариуцагч:....................................../{0}/ '.format(wizard.owner_emp_id.name), format_filter)
                    else:
                        sheet.merge_range(rowx, 1, rowx, 7, u'Эд хариуцагч:........................................./                     / ', format_filter)
                elif report.is_not_cost:
                    #Өртөггүй
                    sheet = workbook.add_worksheet('Assets')
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 15)
                    sheet.set_column('C:C', 20)
                    sheet.set_column('D:D', 6)
                    sheet.set_column('E:E', 8)
                    sheet.set_column('F:F', 14)
                    sheet.set_column('G:G', 14)
                    sheet.set_column('H:H', 14)
                    sheet.set_column('I:I', 14)
                    sheet.set_column('J:J', 14)
                    sheet.set_column('K:K', 14)
                    sheet.set_column('L:L', 14)
                    sheet.set_column('M:M', 14)
                    sheet.set_column('N:N', 14)
                    sheet.set_column('O:O', 14)
                    sheet.set_column('P:P', 14)
                    sheet.set_column('Q:Q', 14)
                    sheet.set_column('R:R', 14)
                    sheet.set_column('S:S', 14)
                    sheet.set_column('T:T', 14)
                    sheet.set_column('U:U', 15)
                    sheet.set_column('V:V', 14)
                    sheet.set_column('W:W', 16)
                    sheet.set_column('Y:Y', 15)
                    sheet.set_column('Z:Z', 15)
                    sheet.set_column('X:X', 15)            
                    rowx = 0
                    # create name
                    sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
                    rowx += 1
                    sheet.merge_range(rowx, 1, rowx, 22, report.name.upper(), format_name)
                    # report duration
                    sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                    # create date
                    sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                    rowx += 3
            
                    sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                    sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн дугаар'), format_title)  # Хөрөнгийн дугаар
                    sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Үндсэн хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
                    sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Элэгдэх сар'), format_title)  # Элэгдэх тоо
                    sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
                    sheet.merge_range(rowx, 5, rowx, 12, _(u'Тоо'), format_title)  # Өртөг
                    sheet.merge_range(rowx + 1, 5, rowx + 2, 5, _(u'Эхний'), format_title)  # Эхний
                    sheet.merge_range(rowx + 1, 6, rowx + 1, 7, _(u'Орлого'), format_title)  # Орлого
                    sheet.write(rowx + 2, 6, _(u'Худалдан aвалт'), format_title)  # Худалдан aвалт
                    sheet.write(rowx + 2, 7, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 8, rowx + 2, 8, _(u'Капиталжуулалт'), format_title)  # Капиталжуулалт
                    sheet.merge_range(rowx + 1, 9, rowx + 2, 9, _(u'Дахин үнэлгээ'), format_title)  # Дахин үнэлгээ
                    sheet.merge_range(rowx + 1, 10, rowx + 1, 11, _(u'Зарлага'), format_title)  #
                    sheet.write(rowx + 2, 10, _(u'Хаагдсан'), format_title)  # Хаагдсан
                    sheet.write(rowx + 2, 11, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 12, rowx + 2, 12, _(u'Эцсийн'), format_title)  # Эцсийн
#                     sheet.merge_range(rowx, 13, rowx, 18, _(u'Хуримтлагдсан элэгдэл'), format_title)  # Өртөг
#                     sheet.merge_range(rowx + 1, 13, rowx + 1, 14, _(u'Эхний'), format_title)  #
#                     sheet.write(rowx + 2, 13, _(u'Эхний'), format_title)  # Эхний
#                     sheet.write(rowx + 2, 14, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
#                     sheet.merge_range(rowx + 1, 15, rowx + 2, 15, _(u'Нэмэгдсэн'), format_title)  # Нэмэгдсэн
#                     sheet.merge_range(rowx + 1, 16, rowx + 1, 17, _(u'Хасагдсан'), format_title)  # Хасагдсан
#                     sheet.write(rowx + 2, 16, _(u'Хаалтаар'), format_title)  # Хаалтаар
#                     sheet.write(rowx + 2, 17, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
#                     sheet.merge_range(rowx + 1, 18, rowx + 2, 18, _(u'Эцсийн'), format_title)  # Эцсийн
#                     sheet.merge_range(rowx, 13, rowx + 2, 19, _(u'Үлдэх өртөг'), format_title)  # Үлдэх өртөг
#                     sheet.merge_range(rowx, 14, rowx + 2, 20, _(u'Үлдэгдэл өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 13, rowx + 2, 13, _(u'Хэлтэс'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 14, rowx + 2, 14, _(u'Албан тушаал'), format_title)  # А/Тушаал
                    sheet.merge_range(rowx, 15, rowx + 2, 15, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
                    sheet.merge_range(rowx, 16, rowx + 2, 16, _(u'Байршил'), format_title)  # Байршил
                    sheet.merge_range(rowx, 17, rowx + 2, 17, _(u'Сериал'), format_title)  # Сериал
                    sheet.merge_range(rowx, 18, rowx + 2, 18, _(u'Улсын дугаар'), format_title)  # Дугаар
                    sheet.merge_range(rowx, 19, rowx + 2, 19, _(u'Дотоод код'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 20, rowx + 2, 20, _(u'Элэгдэл эхлэх огноо'), format_title)  # Хэлтэс

                    rowx += 3
                    
                    def _set_line(line):
#                         print 'line2 ',line
    #                     print '11i',i
                        sheet.write(i, 0, n ,format_content_text)
                        sheet.write(i, 1, line.get('code', ''),format_content_text)
                        sheet.write(i, 2, line.get('name', ''),format_content_text)
    #                     sheet.write(i, 3, '1',format_content_text)
                        sheet.write(i, 3, line.get('method_number', ''), format_content_right)
                        sheet.write(i, 4, get_date_format(line.get('date', '')),format_content_text)
                        sheet.write(i, 5, _get_data_float(line.get('initial_value', '')>0 and 1 or 0), format_content_right)
                        sheet.write(i, 6, _get_data_float(line.get('income_value', '')>0 and 1 or 0), format_content_right)
                        sheet.write(i, 7, '',format_content_right)
                        sheet.write(i, 8, _get_data_float(line.get('capital_value', '')>0 and 1 or 0), format_content_right)
                        sheet.write(i, 9, '',format_content_right)
                        sheet.write(i, 10, _get_data_float(line.get('expense_value', '')>0 and 1 or 0), format_content_right)
                        sheet.write(i, 11, '',format_content_right)
                        sheet.write(i, 12, _get_data_float(line.get('final_value', '')>0 and 1 or 0), format_content_right)
#                         sheet.write(i, 13, _get_data_float(line.get('initial_depr', '')>0 and 1 or 0), format_content_right)
#                         sheet.write(i, 14, _get_data_float(0), format_content_right)
#                         sheet.write(i, 15, _get_data_float(line.get('income_depr', '')>0 and 1 or 0), format_content_right)
#                         sheet.write(i, 16, _get_data_float(0), format_content_right)
#                         sheet.write(i, 17, _get_data_float(line.get('expense_depr', '')>0 and 1 or 0), format_content_right)
#                         sheet.write(i, 18, _get_data_float(line.get('final_depr', '')>0 and 1 or 0), format_content_right)
#     #                     sheet.write(i, 19, _get_data_float(), format_content_right)
#                         sheet.write(i, 19, _get_data_float(line.get('salvage_value', '')), format_content_right)
#                         sheet.write(i, 20, _get_data_float(line.get('final_value', '')-line.get('final_depr', '')), format_content_right)
                        sheet.write(i, 13, line.get('department', ''),format_content_text)
                        sheet.write(i, 14, line.get('job', ''),format_content_text)
                        sheet.write(i, 15, line.get('owner', ''),format_content_text)
                        sheet.write(i, 16, line.get('branch', ''),format_content_text)
                        sheet.write(i, 17, line.get('serial', ''),format_content_text)
                        sheet.write(i, 18, line.get('number', ''),format_content_text)
                        sheet.write(i, 19, line.get('internal_code', ''),format_content_text)
                        sheet.write(i, 20, get_date_format(line.get('first_depr_date', '')),format_content_text)
                    row = 7
                    report = wizard.report_id
                    all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'all_lines---------------- ',len(all_lines)
                    totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                     print 'totals-------- ',totals
    
                    i=row
                    n=''
                    if totals[0]['income_value'] and totals[0]['final_value']:
                        _set_line(totals[0])
    #                 row += 1
                    for obj in report.report_object_ids:
    #                     print 'obj ',obj
                        lines_obj = []
        #                 obj_id = obj.id
                        obj_id = obj.id
                        for line in all_lines:
    #                         print 'line ',line
                            if line.get('report_obj_id') == obj_id:
                                lines_obj.append(line)
    #                     print 'lines_obj ',lines_obj
                        if lines_obj:
                            row += 1
                            name_view = ''
                            query='select name from account_account where id={0}'.format(obj.account_id.id)
                            self.env.cr.execute(query)
                            name_view  = self.env.cr.fetchone()
#                             print ('name_view ',name_view)
                            name_view=name_view[0]
#                             name_view = ''#obj.account_id.name
                            
    #                         print 'name_view ',name_view
                            sheet.write(row, 0, name_view, top)
                            sheet.write(row, 1, '', format_group)
                            sheet.write(row, 2, u'Дэд дүн', format_group)
                            sheet.write(row, 3, '', format_group)
                            sheet.write(row, 4, '', format_group)
                            sheet.write_formula(row, 5,'{=sum('+ self._symbol(row+1, 5)+':'+ self._symbol(row+len(lines_obj),5) +')}', format_group)
                            sheet.write_formula(row, 6,'{=sum('+ self._symbol(row+1, 6)+':'+ self._symbol(row+len(lines_obj),6) +')}', format_group)
                            sheet.write_formula(row, 7,'{=sum('+ self._symbol(row+1, 7)+':'+ self._symbol(row+len(lines_obj),7) +')}', format_group)
                            sheet.write_formula(row, 8,'{=sum('+ self._symbol(row+1, 8)+':'+ self._symbol(row+len(lines_obj),8) +')}', format_group)
                            sheet.write_formula(row, 9,'{=sum('+ self._symbol(row+1, 9)+':'+ self._symbol(row+len(lines_obj),9) +')}', format_group)
                            sheet.write_formula(row, 10,'{=sum('+ self._symbol(row+1, 10)+':'+ self._symbol(row+len(lines_obj),10) +')}', format_group)
                            sheet.write_formula(row, 11,'{=sum('+ self._symbol(row+1, 11)+':'+ self._symbol(row+len(lines_obj),11) +')}', format_group)
                            sheet.write_formula(row, 12,'{=sum('+ self._symbol(row+1, 12)+':'+ self._symbol(row+len(lines_obj),12) +')}', format_group)
#                             sheet.write_formula(row, 13,'{=sum('+ self._symbol(row+1, 13)+':'+ self._symbol(row+len(lines_obj),13) +')}', format_group)
#                             sheet.write_formula(row, 14,'{=sum('+ self._symbol(row+1, 14)+':'+ self._symbol(row+len(lines_obj),14) +')}', format_group)
#                             sheet.write_formula(row, 15,'{=sum('+ self._symbol(row+1, 15)+':'+ self._symbol(row+len(lines_obj),15) +')}', format_group)
#                             sheet.write_formula(row, 16,'{=sum('+ self._symbol(row+1, 16)+':'+ self._symbol(row+len(lines_obj),16) +')}', format_group)
#                             sheet.write_formula(row, 17,'{=sum('+ self._symbol(row+1, 17)+':'+ self._symbol(row+len(lines_obj),17) +')}', format_group)
#                             sheet.write_formula(row, 18,'{=sum('+ self._symbol(row+1, 18)+':'+ self._symbol(row+len(lines_obj),18) +')}', format_group)
#                             sheet.write_formula(row, 19,'{=sum('+ self._symbol(row+1, 19)+':'+ self._symbol(row+len(lines_obj),19) +')}', format_group)
#                             sheet.write_formula(row, 20,'{=sum('+ self._symbol(row+1, 20)+':'+ self._symbol(row+len(lines_obj),20) +')}', format_group)
                            sheet.write(row, 13, '', format_group)
                            sheet.write(row, 14, '', format_group)
                            sheet.write(row, 15, '', format_group)
                            sheet.write(row, 16, '', format_group)
                            sheet.write(row, 17, '', format_group)
                            sheet.write(row, 18, '', format_group)
                            sheet.write(row, 19, '', format_group)
    
                            row += 1
                            start_row = row
    #                         print '1111 ',line
    #                         for i, l in enumerate(all_lines):
    #                             i += row
    #                             _set_line(l)
    # 
    #                         row = i
    # 
    #                         for j, h in enumerate(head):
    #                             sheet.set_column(j, j, h['larg'])# Баганы өргөн
    # 
    #                         _set_table(start_row, row)
    #                         row += 2
                            n=1
                            for i, line in enumerate(lines_obj):
                                i += row
                                _set_line(line)
                                n+=1
                            row = i
                elif report.is_depreciated:
                    sheet = workbook.add_worksheet('Assets')
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 15)
                    sheet.set_column('C:C', 20)
                    sheet.set_column('D:D', 6)
                    sheet.set_column('E:E', 8)
                    sheet.set_column('F:F', 14)
                    sheet.set_column('G:G', 14)
                    sheet.set_column('H:H', 14)
                    sheet.set_column('I:I', 14)
                    sheet.set_column('J:J', 14)
                    sheet.set_column('K:K', 14)
                    sheet.set_column('L:L', 14)
                    sheet.set_column('M:M', 14)
                    sheet.set_column('N:N', 14)
                    sheet.set_column('O:O', 14)
                    sheet.set_column('P:P', 14)
                    sheet.set_column('Q:Q', 14)
                    sheet.set_column('R:R', 14)
                    sheet.set_column('S:S', 14)
                    sheet.set_column('T:T', 14)
                    sheet.set_column('U:U', 15)
                    sheet.set_column('V:V', 14)
                    sheet.set_column('W:W', 16)
                    sheet.set_column('Y:Y', 15)
                    sheet.set_column('Z:Z', 15)
                    sheet.set_column('X:X', 15)            
                    rowx = 0
                    # create name
                    sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
                    rowx += 1
                    sheet.merge_range(rowx, 1, rowx, 19, 'ЭЛЭГДЛИЙН ТАЙЛАН', format_name)
                    # report duration
                    sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                    # create date
                    sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                    rowx += 3
            
                    sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                    sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн дугаар'), format_title)  # Хөрөнгийн дугаар
                    sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Үндсэн хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
                    sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Элэгдэх сар'), format_title)  # Элэгдэх тоо
                    sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
                    # sheet.merge_range(rowx, 5, rowx, 12, _(u'Өртөг'), format_title)  # Өртөг
                    # sheet.merge_range(rowx + 1, 5, rowx + 2, 5, _(u'Эхний'), format_title)  # Эхний
                    # sheet.merge_range(rowx + 1, 6, rowx + 1, 7, _(u'Орлого'), format_title)  # Орлого
                    # sheet.write(rowx + 2, 6, _(u'Худалдан aвалт'), format_title)  # Худалдан aвалт
                    # sheet.write(rowx + 2, 7, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    # sheet.merge_range(rowx + 1, 8, rowx + 2, 8, _(u'Капиталжуулалт'), format_title)  # Капиталжуулалт
                    # sheet.merge_range(rowx + 1, 9, rowx + 2, 9, _(u'Дахин үнэлгээ'), format_title)  # Дахин үнэлгээ
                    # sheet.merge_range(rowx + 1, 10, rowx + 1, 11, _(u'Зарлага'), format_title)  #
                    # sheet.write(rowx + 2, 10, _(u'Хаагдсан'), format_title)  # Хаагдсан
                    # sheet.write(rowx + 2, 11, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx, 5, rowx + 2, 5, _(u'Өртөг'), format_title)  # Эцсийн
                    sheet.merge_range(rowx, 6, rowx, 11, _(u'Хуримтлагдсан элэгдэл'), format_title)  # Өртөг
                    sheet.merge_range(rowx + 1, 6, rowx + 1, 7, _(u'Эхний'), format_title)  #
                    sheet.write(rowx + 2, 6, _(u'Эхний'), format_title)  # Эхний
                    sheet.write(rowx + 2, 7, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 8, rowx + 2, 8, _(u'Нэмэгдсэн'), format_title)  # Нэмэгдсэн
                    sheet.merge_range(rowx + 1, 9, rowx + 1, 10, _(u'Хасагдсан'), format_title)  # Хасагдсан
                    sheet.write(rowx + 2, 9, _(u'Хаалтаар'), format_title)  # Хаалтаар
                    sheet.write(rowx + 2, 10, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 11, rowx + 2, 11, _(u'Эцсийн'), format_title)  # Эцсийн
                    sheet.merge_range(rowx, 12, rowx + 2, 12, _(u'Үлдэх өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 13, rowx + 2, 13, _(u'Үлдэгдэл өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 14, rowx + 2, 14, _(u'Хэлтэс'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 15, rowx + 2, 15, _(u'Албан тушаал'), format_title)  # А/Тушаал
                    sheet.merge_range(rowx, 16, rowx + 2, 16, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
                    sheet.merge_range(rowx, 17, rowx + 2, 17, _(u'Байршил'), format_title)  # Байршил
                    sheet.merge_range(rowx, 18, rowx + 2, 18, _(u'Сериал'), format_title)  # Сериал
                    # sheet.merge_range(rowx, 19, rowx + 2, 19, _(u'Улсын дугаар'), format_title)  # Дугаар
                    # sheet.merge_range(rowx, 20, rowx + 2, 20, _(u'Дотоод код'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 19, rowx + 2, 19, _(u'Элэгдэл эхлэх огноо'), format_title)  # Хэлтэс

                    rowx += 3
                    
                    def _set_line(line):
#                         print 'line2 ',line
    #                     print '11i',i
                        sheet.write(i, 0, n ,format_content_text)
                        sheet.write(i, 1, line.get('code', ''),format_content_text)
                        sheet.write(i, 2, line.get('name', ''),format_content_text)
    #                     sheet.write(i, 3, '1',format_content_text)
                        sheet.write(i, 3, line.get('method_number', ''), format_content_right)
                        sheet.write(i, 4, get_date_format(line.get('date', '')),format_content_text)
                        # sheet.write(i, 5, _get_data_float(line.get('initial_value', '')), format_content_right)
                        # sheet.write(i, 6, _get_data_float(line.get('income_value', '')), format_content_right)
                        # sheet.write(i, 7, '',format_content_right)
                        # sheet.write(i, 8, _get_data_float(line.get('capital_value', '')), format_content_right)
                        # sheet.write(i, 9, '',format_content_right)
                        # sheet.write(i, 10, _get_data_float(line.get('expense_value', '')), format_content_right)
                        # sheet.write(i, 11, '',format_content_right)
                        sheet.write(i, 5, _get_data_float(line.get('final_value', '')), format_content_right)
                        sheet.write(i, 6, _get_data_float(line.get('initial_depr', '')), format_content_right)
                        sheet.write(i, 7, _get_data_float(0), format_content_right)
                        sheet.write(i, 8, _get_data_float(line.get('income_depr', '')), format_content_right)
                        sheet.write(i, 9, _get_data_float(0), format_content_right)
                        sheet.write(i, 10, _get_data_float(line.get('expense_depr', '')), format_content_right)
                        sheet.write(i, 11, _get_data_float(line.get('final_depr', '')), format_content_right)
    #                     sheet.write(i, 19, _get_data_float(), format_content_right)
                        sheet.write(i, 12, _get_data_float(line.get('salvage_value', '')), format_content_right)
                        sheet.write(i, 13, _get_data_float(line.get('final_value', '')-line.get('final_depr', '')), format_content_right)
                        sheet.write(i, 14, line.get('department', ''),format_content_text)
                        sheet.write(i, 15, line.get('job', ''),format_content_text)
                        sheet.write(i, 16, line.get('owner', ''),format_content_text)
                        sheet.write(i, 17, line.get('branch', ''),format_content_text)
                        sheet.write(i, 18, line.get('serial', ''),format_content_text)
                        # sheet.write(i, 19, line.get('number', ''),format_content_text)
                        # sheet.write(i, 20, line.get('internal_code', ''),format_content_text)
                        sheet.write(i, 19, get_date_format(line.get('first_depr_date', '')),format_content_text)
                    row = 7
                    report = wizard.report_id
                    all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'all_lines---------------- ',len(all_lines)
                    totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                     print 'totals-------- ',totals
    
                    i=row
                    n=''
                    if totals[0]['income_value'] and totals[0]['final_value']:
                        _set_line(totals[0])
    #                 row += 1
                    for obj in report.report_object_ids:
    #                     print 'obj ',obj
                        lines_obj = []
        #                 obj_id = obj.id
                        obj_id = obj.id
                        for line in all_lines:
    #                         print 'line ',line
                            if line.get('report_obj_id') == obj_id:
                                lines_obj.append(line)
    #                     print 'lines_obj ',lines_obj
                        if lines_obj:
                            row += 1
                            name_view = ''
    #                         if wizard.type == 'account':
    #                             name_view = obj.account_id.display_name
    #                         if wizard.type == 'partner':
    #                             name_view = obj.partner_id.display_name
    #                         if wizard.type == 'journal':
    #                             name_view = obj.journal_id.display_name
    #                         if wizard.type == 'analytic':
    #                             name_view = obj.analytic_account_id.display_name
#                             print ('obj-----: ',obj)
                            query='select name from account_account where id={0}'.format(obj.account_id.id)
                            self.env.cr.execute(query)
                            name_view  = self.env.cr.fetchone()
#                             print ('name_view ',name_view)
                            name_view=name_view[0]
#                             name_view = ''#obj.account_id.name
                            
    #                         print 'name_view ',name_view
                            sheet.write(row, 0, name_view, top)
                            sheet.write(row, 1, '', format_group)
                            sheet.write(row, 2, u'Дэд дүн', format_group)
                            sheet.write(row, 3, '', format_group)
                            sheet.write(row, 4, '', format_group)
#                             sheet.write(row, 5, '', top)
#                             sheet.write(row, 6, '', top)
#                             sheet.write(row, 7, '', top)
#                             sheet.write(row, 8, '', top)
#                             sheet.write(row, 9, '', top)
#                             sheet.write(row, 10, '', top)
#                             sheet.write(row, 11, '', top)
#                             sheet.write(row, 12, '', top)
#                             sheet.write(row, 13, '', right)
#                             sheet.write(row, 14, '', right)
#                             sheet.write(row, 15, '', right)
#                             sheet.write(row, 16, '', right)
#                             sheet.write(row, 17, '', right)
#                             sheet.write(row, 18, '', right)
#                             sheet.write(row, 19, '', right)
#                             sheet.write(row, 20, '', right)
#                             sheet.write(row, 21, '', right)
                            sheet.write_formula(row, 5,'{=sum('+ self._symbol(row+1, 5)+':'+ self._symbol(row+len(lines_obj),5) +')}', format_group)
                            sheet.write_formula(row, 6,'{=sum('+ self._symbol(row+1, 6)+':'+ self._symbol(row+len(lines_obj),6) +')}', format_group)
                            sheet.write_formula(row, 7,'{=sum('+ self._symbol(row+1, 7)+':'+ self._symbol(row+len(lines_obj),7) +')}', format_group)
                            sheet.write_formula(row, 8,'{=sum('+ self._symbol(row+1, 8)+':'+ self._symbol(row+len(lines_obj),8) +')}', format_group)
                            sheet.write_formula(row, 9,'{=sum('+ self._symbol(row+1, 9)+':'+ self._symbol(row+len(lines_obj),9) +')}', format_group)
                            sheet.write_formula(row, 10,'{=sum('+ self._symbol(row+1, 10)+':'+ self._symbol(row+len(lines_obj),10) +')}', format_group)
                            sheet.write_formula(row, 11,'{=sum('+ self._symbol(row+1, 11)+':'+ self._symbol(row+len(lines_obj),11) +')}', format_group)
                            sheet.write_formula(row, 12,'{=sum('+ self._symbol(row+1, 12)+':'+ self._symbol(row+len(lines_obj),12) +')}', format_group)
                            sheet.write_formula(row, 13,'{=sum('+ self._symbol(row+1, 13)+':'+ self._symbol(row+len(lines_obj),13) +')}', format_group)
                            sheet.write(row, 14, '', format_group)
                            sheet.write(row, 15, '', format_group)
                            sheet.write(row, 16, '', format_group)
                            sheet.write(row, 17, '', format_group)
                            sheet.write(row, 18, '', format_group)
                            sheet.write(row, 19, '', format_group)
                            # sheet.write(row, 20, '', format_group)
    
                            row += 1
                            start_row = row
    #                         print '1111 ',line
    #                         for i, l in enumerate(all_lines):
    #                             i += row
    #                             _set_line(l)
    # 
    #                         row = i
    # 
    #                         for j, h in enumerate(head):
    #                             sheet.set_column(j, j, h['larg'])# Баганы өргөн
    # 
    #                         _set_table(start_row, row)
    #                         row += 2
                            n=1
                            for i, line in enumerate(lines_obj):
                                i += row
                                _set_line(line)
                                n+=1
                            row = i

#                         for j, h in enumerate(head):
#                             sheet.set_column(j, j, h['larg'])
# 
#                         _set_table(start_row, row)
#                         row += 1
#                 def _set_table(start_row, row):
#                     sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
#                                     {'total_row': 1,
#                                      'columns': table,
#                                      'style': 'Table Style Light 9',
#                                      })
                elif report.is_total:
                    sheet = workbook.add_worksheet('Assets')
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 15)
                    sheet.set_column('C:C', 20)
                    sheet.set_column('D:D', 6)
                    sheet.set_column('E:E', 8)
                    sheet.set_column('F:F', 14)
                    sheet.set_column('G:G', 14)
                    sheet.set_column('H:H', 14)
                    sheet.set_column('I:I', 14)
                    sheet.set_column('J:J', 14)
                    sheet.set_column('K:K', 14)
                    sheet.set_column('L:L', 14)
                    sheet.set_column('M:M', 14)
                    sheet.set_column('N:N', 14)
                    sheet.set_column('O:O', 14)
                    sheet.set_column('P:P', 14)
                    sheet.set_column('Q:Q', 14)
                    sheet.set_column('R:R', 14)
                    sheet.set_column('S:S', 14)
                    sheet.set_column('T:T', 14)
                    sheet.set_column('U:U', 15)
                    sheet.set_column('V:V', 14)
                    sheet.set_column('W:W', 16)
                    sheet.set_column('Y:Y', 15)
                    sheet.set_column('Z:Z', 15)
                    sheet.set_column('X:X', 15)            
                    rowx = 0
                    # create name
                    sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
                    rowx += 1
                    sheet.merge_range(rowx, 1, rowx, 12, 'ТОВЧОО ТАЙЛАН', format_name)
                    # report duration
                    sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                    # create date
                    sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                    rowx += 3
            
                    sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                    sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн дугаар'), format_title)  # Хөрөнгийн дугаар
                    sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Үндсэн хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
                    sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Элэгдэх сар'), format_title)  # Элэгдэх тоо
                    sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
                    # sheet.merge_range(rowx, 5, rowx, 12, _(u'Өртөг'), format_title)  # Өртөг
                    # sheet.merge_range(rowx + 1, 5, rowx + 2, 5, _(u'Эхний'), format_title)  # Эхний
                    # sheet.merge_range(rowx + 1, 6, rowx + 1, 7, _(u'Орлого'), format_title)  # Орлого
                    # sheet.write(rowx + 2, 6, _(u'Худалдан aвалт'), format_title)  # Худалдан aвалт
                    # sheet.write(rowx + 2, 7, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    # sheet.merge_range(rowx + 1, 8, rowx + 2, 8, _(u'Капиталжуулалт'), format_title)  # Капиталжуулалт
                    # sheet.merge_range(rowx + 1, 9, rowx + 2, 9, _(u'Дахин үнэлгээ'), format_title)  # Дахин үнэлгээ
                    # sheet.merge_range(rowx + 1, 10, rowx + 1, 11, _(u'Зарлага'), format_title)  #
                    # sheet.write(rowx + 2, 10, _(u'Хаагдсан'), format_title)  # Хаагдсан
                    # sheet.write(rowx + 2, 11, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx, 5, rowx + 2, 5, _(u'Өртөг'), format_title)  # Эцсийн
                    # sheet.merge_range(rowx, 13, rowx, 18, _(u'Хуримтлагдсан элэгдэл'), format_title)  # Өртөг
                    # sheet.merge_range(rowx + 1, 13, rowx + 1, 14, _(u'Эхний'), format_title)  #
                    # sheet.write(rowx + 2, 13, _(u'Эхний'), format_title)  # Эхний
                    # sheet.write(rowx + 2, 14, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    # sheet.merge_range(rowx + 1, 15, rowx + 2, 15, _(u'Нэмэгдсэн'), format_title)  # Нэмэгдсэн
                    # sheet.merge_range(rowx + 1, 16, rowx + 1, 17, _(u'Хасагдсан'), format_title)  # Хасагдсан
                    # sheet.write(rowx + 2, 16, _(u'Хаалтаар'), format_title)  # Хаалтаар
                    # sheet.write(rowx + 2, 17, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx, 6, rowx + 2, 6, _(u'Элэгдэл'), format_title)  # Эцсийн
                    sheet.merge_range(rowx, 7, rowx + 2, 7, _(u'Үлдэх өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 8, rowx + 2, 8, _(u'Үлдэгдэл өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 9, rowx + 2, 9, _(u'Хэлтэс'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 10, rowx + 2, 10, _(u'Албан тушаал'), format_title)  # А/Тушаал
                    sheet.merge_range(rowx, 11, rowx + 2, 11, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
                    sheet.merge_range(rowx, 12, rowx + 2, 12, _(u'Байршил'), format_title)  # Байршил
                    # sheet.merge_range(rowx, 13, rowx + 2, 13, _(u'Сериал'), format_title)  # Сериал
                    # sheet.merge_range(rowx, 14, rowx + 2, 14, _(u'Улсын дугаар'), format_title)  # Дугаар
                    # sheet.merge_range(rowx, 15, rowx + 2, 15, _(u'Дотоод код'), format_title)  # Хэлтэс
                    # sheet.merge_range(rowx, 16, rowx + 2, 16, _(u'Элэгдэл эхлэх огноо'), format_title)  # Хэлтэс

                    rowx += 3
                    
                    def _set_line(line):
#                         print 'line2 ',line
    #                     print '11i',i
                        sheet.write(i, 0, n ,format_content_text)
                        sheet.write(i, 1, line.get('code', ''),format_content_text)
                        sheet.write(i, 2, line.get('name', ''),format_content_text)
    #                     sheet.write(i, 3, '1',format_content_text)
                        sheet.write(i, 3, line.get('method_number', ''), format_content_right)
                        sheet.write(i, 4, get_date_format(line.get('date', '')),format_content_text)
                        # sheet.write(i, 5, _get_data_float(line.get('initial_value', '')), format_content_right)
                        # sheet.write(i, 6, _get_data_float(line.get('income_value', '')), format_content_right)
                        # sheet.write(i, 7, '',format_content_right)
                        # sheet.write(i, 8, _get_data_float(line.get('capital_value', '')), format_content_right)
                        # sheet.write(i, 9, '',format_content_right)
                        # sheet.write(i, 10, _get_data_float(line.get('expense_value', '')), format_content_right)
                        # sheet.write(i, 11, '',format_content_right)
                        sheet.write(i, 5, _get_data_float(line.get('final_value', '')), format_content_right)
                        # sheet.write(i, 13, _get_data_float(line.get('initial_depr', '')), format_content_right)
                        # sheet.write(i, 14, _get_data_float(0), format_content_right)
                        # sheet.write(i, 15, _get_data_float(line.get('income_depr', '')), format_content_right)
                        # sheet.write(i, 16, _get_data_float(0), format_content_right)
                        # sheet.write(i, 17, _get_data_float(line.get('expense_depr', '')), format_content_right)
                        sheet.write(i, 6, _get_data_float(line.get('final_depr', '')), format_content_right)
    #                     sheet.write(i, 19, _get_data_float(), format_content_right)
                        sheet.write(i, 7, _get_data_float(line.get('salvage_value', '')), format_content_right)
                        sheet.write(i, 8, _get_data_float(line.get('final_value', '')-line.get('final_depr', '')), format_content_right)
                        sheet.write(i, 9, line.get('department', ''),format_content_text)
                        sheet.write(i, 10, line.get('job', ''),format_content_text)
                        sheet.write(i, 11, line.get('owner', ''),format_content_text)
                        sheet.write(i, 12, line.get('branch', ''),format_content_text)
                        # sheet.write(i, 1, line.get('serial', ''),format_content_text)
                        # sheet.write(i, 26, line.get('number', ''),format_content_text)
                        # sheet.write(i, 27, line.get('internal_code', ''),format_content_text)
                        # sheet.write(i, 28, get_date_format(line.get('first_depr_date', '')),format_content_text)
                    row = 7
                    report = wizard.report_id
                    all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'all_lines---------------- ',len(all_lines)
                    totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                     print 'totals-------- ',totals
    
                    i=row
                    n=''
                    if totals[0]['income_value'] and totals[0]['final_value']:
                        _set_line(totals[0])
    #                 row += 1
                    for obj in report.report_object_ids:
    #                     print 'obj ',obj
                        lines_obj = []
        #                 obj_id = obj.id
                        obj_id = obj.id
                        for line in all_lines:
    #                         print 'line ',line
                            if line.get('report_obj_id') == obj_id:
                                lines_obj.append(line)
    #                     print 'lines_obj ',lines_obj
                        if lines_obj:
                            row += 1
                            name_view = ''
    #                         if wizard.type == 'account':
    #                             name_view = obj.account_id.display_name
    #                         if wizard.type == 'partner':
    #                             name_view = obj.partner_id.display_name
    #                         if wizard.type == 'journal':
    #                             name_view = obj.journal_id.display_name
    #                         if wizard.type == 'analytic':
    #                             name_view = obj.analytic_account_id.display_name
#                             print ('obj-----: ',obj)
                            query='select name from account_account where id={0}'.format(obj.account_id.id)
                            self.env.cr.execute(query)
                            name_view  = self.env.cr.fetchone()
#                             print ('name_view ',name_view)
                            name_view=name_view[0]
#                             name_view = ''#obj.account_id.name
                            
    #                         print 'name_view ',name_view
                            sheet.write(row, 0, name_view, top)
                            sheet.write(row, 1, '', format_group)
                            sheet.write(row, 2, u'Дэд дүн', format_group)
                            sheet.write(row, 3, '', format_group)
                            sheet.write(row, 4, '', format_group)
#                             sheet.write(row, 5, '', top)
#                             sheet.write(row, 6, '', top)
#                             sheet.write(row, 7, '', top)
#                             sheet.write(row, 8, '', top)
#                             sheet.write(row, 9, '', top)
#                             sheet.write(row, 10, '', top)
#                             sheet.write(row, 11, '', top)
#                             sheet.write(row, 12, '', top)
#                             sheet.write(row, 13, '', right)
#                             sheet.write(row, 14, '', right)
#                             sheet.write(row, 15, '', right)
#                             sheet.write(row, 16, '', right)
#                             sheet.write(row, 17, '', right)
#                             sheet.write(row, 18, '', right)
#                             sheet.write(row, 19, '', right)
#                             sheet.write(row, 20, '', right)
#                             sheet.write(row, 21, '', right)
                            sheet.write_formula(row, 5,'{=sum('+ self._symbol(row+1, 5)+':'+ self._symbol(row+len(lines_obj),5) +')}', format_group)
                            sheet.write_formula(row, 6,'{=sum('+ self._symbol(row+1, 6)+':'+ self._symbol(row+len(lines_obj),6) +')}', format_group)
                            sheet.write_formula(row, 7,'{=sum('+ self._symbol(row+1, 7)+':'+ self._symbol(row+len(lines_obj),7) +')}', format_group)
                            sheet.write_formula(row, 8,'{=sum('+ self._symbol(row+1, 8)+':'+ self._symbol(row+len(lines_obj),8) +')}', format_group)
                            # sheet.write_formula(row, 9,'{=sum('+ self._symbol(row+1, 9)+':'+ self._symbol(row+len(lines_obj),9) +')}', format_group)
                            # sheet.write_formula(row, 10,'{=sum('+ self._symbol(row+1, 10)+':'+ self._symbol(row+len(lines_obj),10) +')}', format_group)
                            # sheet.write_formula(row, 11,'{=sum('+ self._symbol(row+1, 11)+':'+ self._symbol(row+len(lines_obj),11) +')}', format_group)
                            # sheet.write_formula(row, 12,'{=sum('+ self._symbol(row+1, 12)+':'+ self._symbol(row+len(lines_obj),12) +')}', format_group)
                            # sheet.write_formula(row, 13,'{=sum('+ self._symbol(row+1, 13)+':'+ self._symbol(row+len(lines_obj),13) +')}', format_group)
                            # sheet.write_formula(row, 14,'{=sum('+ self._symbol(row+1, 14)+':'+ self._symbol(row+len(lines_obj),14) +')}', format_group)
                            # sheet.write_formula(row, 15,'{=sum('+ self._symbol(row+1, 15)+':'+ self._symbol(row+len(lines_obj),15) +')}', format_group)
                            # sheet.write_formula(row, 16,'{=sum('+ self._symbol(row+1, 16)+':'+ self._symbol(row+len(lines_obj),16) +')}', format_group)
                            # sheet.write_formula(row, 17,'{=sum('+ self._symbol(row+1, 17)+':'+ self._symbol(row+len(lines_obj),17) +')}', format_group)
                            # sheet.write_formula(row, 18,'{=sum('+ self._symbol(row+1, 18)+':'+ self._symbol(row+len(lines_obj),18) +')}', format_group)
                            # sheet.write_formula(row, 19,'{=sum('+ self._symbol(row+1, 19)+':'+ self._symbol(row+len(lines_obj),19) +')}', format_group)
                            # sheet.write_formula(row, 20,'{=sum('+ self._symbol(row+1, 20)+':'+ self._symbol(row+len(lines_obj),20) +')}', format_group)
                            sheet.write(row, 9, '', format_group)
                            sheet.write(row, 10, '', format_group)
                            sheet.write(row, 11, '', format_group)
                            sheet.write(row, 12, '', format_group)
                            # sheet.write(row, 25, '', format_group)
                            # sheet.write(row, 26, '', format_group)
                            # sheet.write(row, 27, '', format_group)
    
                            row += 1
                            start_row = row
    #                         print '1111 ',line
    #                         for i, l in enumerate(all_lines):
    #                             i += row
    #                             _set_line(l)
    # 
    #                         row = i
    # 
    #                         for j, h in enumerate(head):
    #                             sheet.set_column(j, j, h['larg'])# Баганы өргөн
    # 
    #                         _set_table(start_row, row)
    #                         row += 2
                            n=1
                            for i, line in enumerate(lines_obj):
                                i += row
                                _set_line(line)
                                n+=1
                            row = i

#                         for j, h in enumerate(head):
#                             sheet.set_column(j, j, h['larg'])
# 
#                         _set_table(start_row, row)
#                         row += 1
#                 def _set_table(start_row, row):
#                     sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
#                                     {'total_row': 1,
#                                      'columns': table,
#                                      'style': 'Table Style Light 9',
#                                      })
                elif report.is_capital:
                    sheet = workbook.add_worksheet('Assets')
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 15)
                    sheet.set_column('C:C', 20)
                    sheet.set_column('D:D', 6)
                    sheet.set_column('E:E', 8)
                    sheet.set_column('F:F', 14)
                    sheet.set_column('G:G', 14)
                    sheet.set_column('H:H', 14)
                    sheet.set_column('I:I', 14)
                    sheet.set_column('J:J', 14)
                    sheet.set_column('K:K', 14)
                    sheet.set_column('L:L', 14)
                    sheet.set_column('M:M', 14)
                    sheet.set_column('N:N', 14)
                    sheet.set_column('O:O', 14)
                    sheet.set_column('P:P', 14)
                    sheet.set_column('Q:Q', 14)
                    sheet.set_column('R:R', 14)
                    sheet.set_column('S:S', 14)
                    sheet.set_column('T:T', 14)
                    sheet.set_column('U:U', 15)
                    sheet.set_column('V:V', 14)
                    sheet.set_column('W:W', 16)
                    sheet.set_column('Y:Y', 15)
                    sheet.set_column('Z:Z', 15)
                    sheet.set_column('X:X', 15)            
                    rowx = 0
                    # create name
                    sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
                    rowx += 1
                    sheet.merge_range(rowx, 1, rowx, 11, 'КАПИТАЛЖУУЛАЛТЫН ТАЙЛАН', format_name)
                    # report duration
                    sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                    # create date
                    sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                    rowx += 3
            
                    sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                    sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн дугаар'), format_title)  # Хөрөнгийн дугаар
                    sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Үндсэн хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
                    sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Элэгдэх сар'), format_title)  # Элэгдэх тоо
                    sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
                    # sheet.merge_range(rowx, 5, rowx, 12, _(u'Өртөг'), format_title)  # Өртөг
                    sheet.merge_range(rowx, 5, rowx + 2, 5, _(u'Эхний Өртөг'), format_title)  # Эхний
                    # sheet.merge_range(rowx + 1, 6, rowx + 1, 7, _(u'Орлого'), format_title)  # Орлого
                    # sheet.write(rowx + 2, 6, _(u'Худалдан aвалт'), format_title)  # Худалдан aвалт
                    # sheet.write(rowx + 2, 7, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx, 6, rowx + 2, 6, _(u'Капиталжуулалт'), format_title)  # Капиталжуулалт
                    # sheet.merge_range(rowx + 1, 9, rowx + 2, 9, _(u'Дахин үнэлгээ'), format_title)  # Дахин үнэлгээ
                    # sheet.merge_range(rowx + 1, 10, rowx + 1, 11, _(u'Зарлага'), format_title)  #
                    # sheet.write(rowx + 2, 10, _(u'Хаагдсан'), format_title)  # Хаагдсан
                    # sheet.write(rowx + 2, 11, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx, 7, rowx + 2, 7, _(u'Эцсийн Өртөг'), format_title)  # Эцсийн
                    # sheet.merge_range(rowx, 13, rowx, 18, _(u'Хуримтлагдсан элэгдэл'), format_title)  # Өртөг
                    # sheet.merge_range(rowx + 1, 13, rowx + 1, 14, _(u'Эхний'), format_title)  #
                    # sheet.write(rowx + 2, 13, _(u'Эхний'), format_title)  # Эхний
                    # sheet.write(rowx + 2, 14, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    # sheet.merge_range(rowx + 1, 15, rowx + 2, 15, _(u'Нэмэгдсэн'), format_title)  # Нэмэгдсэн
                    # sheet.merge_range(rowx + 1, 16, rowx + 1, 17, _(u'Хасагдсан'), format_title)  # Хасагдсан
                    # sheet.write(rowx + 2, 16, _(u'Хаалтаар'), format_title)  # Хаалтаар
                    # sheet.write(rowx + 2, 17, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    # sheet.merge_range(rowx + 6, rowx + 2, 6, _(u'Элэгдэл'), format_title)  # Эцсийн
                    # sheet.merge_range(rowx, 7, rowx + 2, 7, _(u'Үлдэх өртөг'), format_title)  # Үлдэх өртөг
                    # sheet.merge_range(rowx, 8, rowx + 2, 8, _(u'Үлдэгдэл өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 8, rowx + 2, 8, _(u'Хэлтэс'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 9, rowx + 2, 9, _(u'Албан тушаал'), format_title)  # А/Тушаал
                    sheet.merge_range(rowx, 10, rowx + 2, 10, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
                    sheet.merge_range(rowx, 11, rowx + 2, 11, _(u'Байршил'), format_title)  # Байршил
                    # sheet.merge_range(rowx, 13, rowx + 2, 13, _(u'Сериал'), format_title)  # Сериал
                    # sheet.merge_range(rowx, 14, rowx + 2, 14, _(u'Улсын дугаар'), format_title)  # Дугаар
                    # sheet.merge_range(rowx, 15, rowx + 2, 15, _(u'Дотоод код'), format_title)  # Хэлтэс
                    # sheet.merge_range(rowx, 16, rowx + 2, 16, _(u'Элэгдэл эхлэх огноо'), format_title)  # Хэлтэс

                    rowx += 3
                    
                    def _set_line(line):
#                         print 'line2 ',line
    #                     print '11i',i
                        sheet.write(i, 0, n ,format_content_text)
                        sheet.write(i, 1, line.get('code', ''),format_content_text)
                        sheet.write(i, 2, line.get('name', ''),format_content_text)
    #                     sheet.write(i, 3, '1',format_content_text)
                        sheet.write(i, 3, line.get('method_number', ''), format_content_right)
                        sheet.write(i, 4, get_date_format(line.get('date', '')),format_content_text)
                        sheet.write(i, 5, _get_data_float(line.get('initial_value', '')), format_content_right)
                        # sheet.write(i, 6, _get_data_float(line.get('income_value', '')), format_content_right)
                        # sheet.write(i, 7, '',format_content_right)
                        sheet.write(i, 6, _get_data_float(line.get('capital_value', '')), format_content_right)
                        # sheet.write(i, 9, '',format_content_right)
                        # sheet.write(i, 10, _get_data_float(line.get('expense_value', '')), format_content_right)
                        # sheet.write(i, 11, '',format_content_right)
                        sheet.write(i, 7, _get_data_float(line.get('final_value', '')), format_content_right)
                        # sheet.write(i, 13, _get_data_float(line.get('initial_depr', '')), format_content_right)
                        # sheet.write(i, 14, _get_data_float(0), format_content_right)
                        # sheet.write(i, 15, _get_data_float(line.get('income_depr', '')), format_content_right)
                        # sheet.write(i, 16, _get_data_float(0), format_content_right)
                        # sheet.write(i, 17, _get_data_float(line.get('expense_depr', '')), format_content_right)
                        # sheet.write(i, 6, _get_data_float(line.get('final_depr', '')), format_content_right)
    #                     sheet.write(i, 19, _get_data_float(), format_content_right)
                        # sheet.write(i, 7, _get_data_float(line.get('salvage_value', '')), format_content_right)
                        # sheet.write(i, 8, _get_data_float(line.get('final_value', '')-line.get('final_depr', '')), format_content_right)
                        sheet.write(i, 8, line.get('department', ''),format_content_text)
                        sheet.write(i, 9, line.get('job', ''),format_content_text)
                        sheet.write(i, 10, line.get('owner', ''),format_content_text)
                        sheet.write(i, 11, line.get('branch', ''),format_content_text)
                        # sheet.write(i, 1, line.get('serial', ''),format_content_text)
                        # sheet.write(i, 26, line.get('number', ''),format_content_text)
                        # sheet.write(i, 27, line.get('internal_code', ''),format_content_text)
                        # sheet.write(i, 28, get_date_format(line.get('first_depr_date', '')),format_content_text)
                    row = 7
                    report = wizard.report_id
                    all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'all_lines---------------- ',len(all_lines)
                    totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                     print 'totals-------- ',totals
    
                    i=row
                    n=''
                    if totals[0]['income_value'] and totals[0]['final_value']:
                        _set_line(totals[0])
    #                 row += 1
                    for obj in report.report_object_ids:
    #                     print 'obj ',obj
                        lines_obj = []
        #                 obj_id = obj.id
                        obj_id = obj.id
                        for line in all_lines:
    #                         print 'line ',line
                            if line.get('report_obj_id') == obj_id:
                                lines_obj.append(line)
    #                     print 'lines_obj ',lines_obj
                        if lines_obj:
                            row += 1
                            name_view = ''
    #                         if wizard.type == 'account':
    #                             name_view = obj.account_id.display_name
    #                         if wizard.type == 'partner':
    #                             name_view = obj.partner_id.display_name
    #                         if wizard.type == 'journal':
    #                             name_view = obj.journal_id.display_name
    #                         if wizard.type == 'analytic':
    #                             name_view = obj.analytic_account_id.display_name
#                             print ('obj-----: ',obj)
                            query='select name from account_account where id={0}'.format(obj.account_id.id)
                            self.env.cr.execute(query)
                            name_view  = self.env.cr.fetchone()
#                             print ('name_view ',name_view)
                            name_view=name_view[0]
#                             name_view = ''#obj.account_id.name
                            
    #                         print 'name_view ',name_view
                            sheet.write(row, 0, name_view, top)
                            sheet.write(row, 1, '', format_group)
                            sheet.write(row, 2, u'Дэд дүн', format_group)
                            sheet.write(row, 3, '', format_group)
                            sheet.write(row, 4, '', format_group)
#                             sheet.write(row, 5, '', top)
#                             sheet.write(row, 6, '', top)
#                             sheet.write(row, 7, '', top)
#                             sheet.write(row, 8, '', top)
#                             sheet.write(row, 9, '', top)
#                             sheet.write(row, 10, '', top)
#                             sheet.write(row, 11, '', top)
#                             sheet.write(row, 12, '', top)
#                             sheet.write(row, 13, '', right)
#                             sheet.write(row, 14, '', right)
#                             sheet.write(row, 15, '', right)
#                             sheet.write(row, 16, '', right)
#                             sheet.write(row, 17, '', right)
#                             sheet.write(row, 18, '', right)
#                             sheet.write(row, 19, '', right)
#                             sheet.write(row, 20, '', right)
#                             sheet.write(row, 21, '', right)
                            sheet.write_formula(row, 5,'{=sum('+ self._symbol(row+1, 5)+':'+ self._symbol(row+len(lines_obj),5) +')}', format_group)
                            sheet.write_formula(row, 6,'{=sum('+ self._symbol(row+1, 6)+':'+ self._symbol(row+len(lines_obj),6) +')}', format_group)
                            sheet.write_formula(row, 7,'{=sum('+ self._symbol(row+1, 7)+':'+ self._symbol(row+len(lines_obj),7) +')}', format_group)
                            # sheet.write_formula(row, 8,'{=sum('+ self._symbol(row+1, 8)+':'+ self._symbol(row+len(lines_obj),8) +')}', format_group)
                            # sheet.write_formula(row, 9,'{=sum('+ self._symbol(row+1, 9)+':'+ self._symbol(row+len(lines_obj),9) +')}', format_group)
                            # sheet.write_formula(row, 10,'{=sum('+ self._symbol(row+1, 10)+':'+ self._symbol(row+len(lines_obj),10) +')}', format_group)
                            # sheet.write_formula(row, 11,'{=sum('+ self._symbol(row+1, 11)+':'+ self._symbol(row+len(lines_obj),11) +')}', format_group)
                            # sheet.write_formula(row, 12,'{=sum('+ self._symbol(row+1, 12)+':'+ self._symbol(row+len(lines_obj),12) +')}', format_group)
                            # sheet.write_formula(row, 13,'{=sum('+ self._symbol(row+1, 13)+':'+ self._symbol(row+len(lines_obj),13) +')}', format_group)
                            # sheet.write_formula(row, 14,'{=sum('+ self._symbol(row+1, 14)+':'+ self._symbol(row+len(lines_obj),14) +')}', format_group)
                            # sheet.write_formula(row, 15,'{=sum('+ self._symbol(row+1, 15)+':'+ self._symbol(row+len(lines_obj),15) +')}', format_group)
                            # sheet.write_formula(row, 16,'{=sum('+ self._symbol(row+1, 16)+':'+ self._symbol(row+len(lines_obj),16) +')}', format_group)
                            # sheet.write_formula(row, 17,'{=sum('+ self._symbol(row+1, 17)+':'+ self._symbol(row+len(lines_obj),17) +')}', format_group)
                            # sheet.write_formula(row, 18,'{=sum('+ self._symbol(row+1, 18)+':'+ self._symbol(row+len(lines_obj),18) +')}', format_group)
                            # sheet.write_formula(row, 19,'{=sum('+ self._symbol(row+1, 19)+':'+ self._symbol(row+len(lines_obj),19) +')}', format_group)
                            # sheet.write_formula(row, 20,'{=sum('+ self._symbol(row+1, 20)+':'+ self._symbol(row+len(lines_obj),20) +')}', format_group)
                            sheet.write(row, 8, '', format_group)
                            sheet.write(row, 9, '', format_group)
                            sheet.write(row, 10, '', format_group)
                            sheet.write(row, 11, '', format_group)
                            sheet.write(row, 12, '', format_group)
                            # sheet.write(row, 25, '', format_group)
                            # sheet.write(row, 26, '', format_group)
                            # sheet.write(row, 27, '', format_group)
    
                            row += 1
                            start_row = row
    #                         print '1111 ',line
    #                         for i, l in enumerate(all_lines):
    #                             i += row
    #                             _set_line(l)
    # 
    #                         row = i
    # 
    #                         for j, h in enumerate(head):
    #                             sheet.set_column(j, j, h['larg'])# Баганы өргөн
    # 
    #                         _set_table(start_row, row)
    #                         row += 2
                            n=1
                            for i, line in enumerate(lines_obj):
                                i += row
                                _set_line(line)
                                n+=1
                            row = i

#                         for j, h in enumerate(head):
#                             sheet.set_column(j, j, h['larg'])
# 
#                         _set_table(start_row, row)
#                         row += 1
#                 def _set_table(start_row, row):
#                     sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
#                                     {'total_row': 1,
#                                      'columns': table,
#                                      'style': 'Table Style Light 9',
#                                      })
                else:
                    sheet = workbook.add_worksheet('Assets')
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 15)
                    sheet.set_column('C:C', 20)
                    sheet.set_column('D:D', 6)
                    sheet.set_column('E:E', 8)
                    sheet.set_column('F:F', 14)
                    sheet.set_column('G:G', 14)
                    sheet.set_column('H:H', 14)
                    sheet.set_column('I:I', 14)
                    sheet.set_column('J:J', 14)
                    sheet.set_column('K:K', 14)
                    sheet.set_column('L:L', 14)
                    sheet.set_column('M:M', 14)
                    sheet.set_column('N:N', 14)
                    sheet.set_column('O:O', 14)
                    sheet.set_column('P:P', 14)
                    sheet.set_column('Q:Q', 14)
                    sheet.set_column('R:R', 14)
                    sheet.set_column('S:S', 14)
                    sheet.set_column('T:T', 14)
                    sheet.set_column('U:U', 15)
                    sheet.set_column('V:V', 14)
                    sheet.set_column('W:W', 16)
                    sheet.set_column('Y:Y', 15)
                    sheet.set_column('Z:Z', 15)
                    sheet.set_column('X:X', 15)            
                    rowx = 0
                    # create name
                    sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
                    rowx += 1
                    sheet.merge_range(rowx, 1, rowx, 22, report.name.upper(), format_name)
                    # report duration
                    sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                    # create date
                    sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                    rowx += 3
            
                    sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                    sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн дугаар'), format_title)  # Хөрөнгийн дугаар
                    sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Үндсэн хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
                    sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Элэгдэх сар'), format_title)  # Элэгдэх тоо
                    sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
                    sheet.merge_range(rowx, 5, rowx, 10, _(u'Өртөг'), format_title)  # Өртөг
                    sheet.merge_range(rowx + 1, 5, rowx + 2, 5, _(u'Эхний'), format_title)  # Эхний
                    sheet.merge_range(rowx + 1, 6, rowx + 2, 6, _(u'Орлого'), format_title)  # Орлого
                    # sheet.write(rowx + 2, 6, _(u'Худалдан aвалт'), format_title)  # Худалдан aвалт
                    # sheet.write(rowx + 2, 7, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 7, rowx + 2, 7, _(u'Капиталжуулалт'), format_title)  # Капиталжуулалт
                    sheet.merge_range(rowx + 1, 8, rowx + 2, 8, _(u'Дахин үнэлгээ'), format_title)  # Дахин үнэлгээ
                    sheet.merge_range(rowx + 1, 9, rowx + 2, 9, _(u'Зарлага'), format_title)  #
                    # sheet.write(rowx + 2, 10, _(u'Хаагдсан'), format_title)  # Хаагдсан
                    # sheet.write(rowx + 2, 11, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 10, rowx + 2, 10, _(u'Эцсийн'), format_title)  # Эцсийн
                    sheet.merge_range(rowx, 11, rowx, 15, _(u'Хуримтлагдсан элэгдэл'), format_title)  # Өртөг
                    sheet.merge_range(rowx + 1, 11, rowx + 2, 11, _(u'Эхний'), format_title)  #
                    # sheet.write(rowx + 2, 13, _(u'Эхний'), format_title)  # Эхний
                    # sheet.write(rowx + 2, 14, _(u'Хөдөлгөөнөөр'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 12, rowx + 2, 12, _(u'Нэмэгдсэн'), format_title)  # Нэмэгдсэн
                    sheet.merge_range(rowx + 1, 13, rowx + 1, 14, _(u'Хасагдсан'), format_title)  # Хасагдсан
                    sheet.write(rowx + 2, 13, _(u'Хаалтаар'), format_title)  # Хаалтаар
                    sheet.write(rowx + 2, 14, _(u'Зарлагаар'), format_title)  # Хөдөлгөөнөөр
                    sheet.merge_range(rowx + 1, 15, rowx + 2, 15, _(u'Эцсийн'), format_title)  # Эцсийн
                    sheet.merge_range(rowx, 16, rowx + 2, 16, _(u'Үлдэгдэл өртөг'), format_title)  # Үлдэх өртөг
                    sheet.merge_range(rowx, 17, rowx + 2, 17, _(u'Хөрөнгийн төрөл'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 18, rowx + 2, 18, _(u'Хэлтэс'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 19, rowx + 2, 19, _(u'Албан тушаал'), format_title)  # А/Тушаал
                    sheet.merge_range(rowx, 20, rowx + 2, 20, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
                    sheet.merge_range(rowx, 21, rowx + 2, 21, _(u'Байршил'), format_title)  # Байршил
                    sheet.merge_range(rowx, 22, rowx + 2, 22, _(u'Сериал'), format_title)  # Сериал
                    sheet.merge_range(rowx, 23, rowx + 2, 23, _(u'Улсын дугаар'), format_title)  # Дугаар
                    sheet.merge_range(rowx, 24, rowx + 2, 24, _(u'Хуучин код'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 25, rowx + 2, 25, _(u'Элэгдэл эхлэх огноо'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 26, rowx + 2, 26, _(u'Хаасан төлөв'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 27, rowx + 2, 27, _(u'Арлын дугаар'), format_title)  # Хэлтэс
                    sheet.merge_range(rowx, 28, rowx + 2, 28, _(u'Өнгө'), format_title)  # Хэлтэс
                    rowx += 3
                    
                    def _set_line(line):
#                         print 'line2 ',line
    #                     print '11i',i
                        sheet.write(i, 0, n ,format_content_text)
                        sheet.write(i, 1, line.get('code', ''),format_content_text)
                        sheet.write(i, 2, line.get('name', ''),format_content_text)
    #                     sheet.write(i, 3, '1',format_content_text)
                        sheet.write(i, 3, line.get('method_number', ''), format_content_right)
                        sheet.write(i, 4, get_date_format(line.get('date', '')),format_content_text)
                        sheet.write(i, 5, _get_data_float(line.get('initial_value', '')), format_content_right)
                        sheet.write(i, 6, _get_data_float(line.get('income_value', '')), format_content_right)
                        # sheet.write(i, 7, format_content_right)
                        sheet.write(i, 7, _get_data_float(line.get('capital_value', '')), format_content_right)
                        sheet.write(i, 8, '',format_content_right)
                        sheet.write(i, 9, _get_data_float(line.get('expense_value', '')), format_content_right)
                        # sheet.write(i, 11, '',format_content_right)
                        sheet.write(i, 10, _get_data_float(line.get('final_value', '')), format_content_right)
                        sheet.write(i, 11, _get_data_float(line.get('initial_depr', '')), format_content_right)
                        # sheet.write(i, 14, _get_data_float(0), format_content_right)
                        sheet.write(i, 12, _get_data_float(line.get('income_depr', '')), format_content_right)
                        sheet.write(i, 13, _get_data_float(0), format_content_right)
                        sheet.write(i, 14, _get_data_float(line.get('expense_depr', '')), format_content_right)
                        sheet.write(i, 15, _get_data_float(line.get('final_depr', '')), format_content_right)
    #                     sheet.write(i, 19, _get_data_float(), format_content_right)
                        # sheet.write(i, 19, _get_data_float(line.get('salvage_value', '')), format_content_right)
                        sheet.write(i, 16, _get_data_float(line.get('final_value', '')-line.get('final_depr', '')), format_content_right)
                        sheet.write(i, 17, line.get('asset_type_name', ''),format_content_text)
                        sheet.write(i, 18, line.get('department', ''),format_content_text)
                        sheet.write(i, 19, line.get('job', ''),format_content_text)
                        sheet.write(i, 20, line.get('owner', ''),format_content_text)
                        sheet.write(i, 21, line.get('branch', ''),format_content_text)
                        sheet.write(i, 22, line.get('serial', ''),format_content_text)
                        sheet.write(i, 23, line.get('car_number', ''),format_content_text)
                        sheet.write(i, 24, line.get('internal_code', ''),format_content_text)
                        sheet.write(i, 25, get_date_format(line.get('first_depr_date', '')),format_content_text)
                        sheet.write(i, 26, line.get('close_status', ''),format_content_text)
                        sheet.write(i, 27, line.get('car_vat', ''),format_content_text)
                        sheet.write(i, 28, line.get('car_color', ''),format_content_text)
                    row = 7
                    report = wizard.report_id
                    all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
    #                 print 'all_lines---------------- ',len(all_lines)
                    totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                     print 'totals-------- ',totals
    
                    i=row
                    n=''
                    if totals[0]['income_value'] and totals[0]['final_value']:
                        _set_line(totals[0])
    #                 row += 1
                    for obj in report.report_object_ids:
    #                     print 'obj ',obj
                        lines_obj = []
        #                 obj_id = obj.id
                        obj_id = obj.id
                        for line in all_lines:
    #                         print 'line ',line
                            if line.get('report_obj_id') == obj_id:
                                lines_obj.append(line)
    #                     print 'lines_obj ',lines_obj
                        if lines_obj:
                            row += 1
                            name_view = ''
    #                         if wizard.type == 'account':
    #                             name_view = obj.account_id.display_name
    #                         if wizard.type == 'partner':
    #                             name_view = obj.partner_id.display_name
    #                         if wizard.type == 'journal':
    #                             name_view = obj.journal_id.display_name
    #                         if wizard.type == 'analytic':
    #                             name_view = obj.analytic_account_id.display_name
#                             print ('obj-----: ',obj)
                            query='select name from account_account where id={0}'.format(obj.account_id.id)
                            self.env.cr.execute(query)
                            name_view  = self.env.cr.fetchone()
#                             print ('name_view ',name_view)
                            name_view=name_view[0]
#                             name_view = ''#obj.account_id.name
                            
    #                         print 'name_view ',name_view
                            sheet.write(row, 0, name_view, top)
                            sheet.write(row, 1, '', format_group)
                            sheet.write(row, 2, u'Дэд дүн', format_group)
                            sheet.write(row, 3, '', format_group)
                            sheet.write(row, 4, '', format_group)
                            sheet.write_formula(row, 5,'{=sum('+ self._symbol(row+1, 5)+':'+ self._symbol(row+len(lines_obj),5) +')}', format_group)
                            sheet.write_formula(row, 6,'{=sum('+ self._symbol(row+1, 6)+':'+ self._symbol(row+len(lines_obj),6) +')}', format_group)
                            sheet.write_formula(row, 7,'{=sum('+ self._symbol(row+1, 7)+':'+ self._symbol(row+len(lines_obj),7) +')}', format_group)
                            sheet.write_formula(row, 8,'{=sum('+ self._symbol(row+1, 8)+':'+ self._symbol(row+len(lines_obj),8) +')}', format_group)
                            sheet.write_formula(row, 9,'{=sum('+ self._symbol(row+1, 9)+':'+ self._symbol(row+len(lines_obj),9) +')}', format_group)
                            sheet.write_formula(row, 10,'{=sum('+ self._symbol(row+1, 10)+':'+ self._symbol(row+len(lines_obj),10) +')}', format_group)
                            sheet.write_formula(row, 11,'{=sum('+ self._symbol(row+1, 11)+':'+ self._symbol(row+len(lines_obj),11) +')}', format_group)
                            sheet.write_formula(row, 12,'{=sum('+ self._symbol(row+1, 12)+':'+ self._symbol(row+len(lines_obj),12) +')}', format_group)
                            sheet.write_formula(row, 13,'{=sum('+ self._symbol(row+1, 13)+':'+ self._symbol(row+len(lines_obj),13) +')}', format_group)
                            sheet.write_formula(row, 14,'{=sum('+ self._symbol(row+1, 14)+':'+ self._symbol(row+len(lines_obj),14) +')}', format_group)
                            sheet.write_formula(row, 15,'{=sum('+ self._symbol(row+1, 15)+':'+ self._symbol(row+len(lines_obj),15) +')}', format_group)
                            sheet.write_formula(row, 16,'{=sum('+ self._symbol(row+1, 16)+':'+ self._symbol(row+len(lines_obj),16) +')}', format_group)
                            sheet.write(row, 17, '', format_group)
                            sheet.write(row, 18, '', format_group)
                            sheet.write(row, 19, '', format_group)
                            sheet.write(row, 20, '', format_group)
                            sheet.write(row, 21, '', format_group)
                            sheet.write(row, 22, '', format_group)
                            sheet.write(row, 23, '', format_group)
                            sheet.write(row, 24, '', format_group)
                            sheet.write(row, 25, '', format_group)
                            sheet.write(row, 26, '', format_group)
                            sheet.write(row, 27, '', format_group)
                            sheet.write(row, 28, '', format_group)
                            # sheet.write(row, 29, '', format_group)
                            row += 1
                            start_row = row
    #                         print '1111 ',line
    #                         for i, l in enumerate(all_lines):
    #                             i += row
    #                             _set_line(l)
    # 
    #                         row = i
    # 
    #                         for j, h in enumerate(head):
    #                             sheet.set_column(j, j, h['larg'])# Баганы өргөн
    # 
    #                         _set_table(start_row, row)
    #                         row += 2
                            n=1
                            for i, line in enumerate(lines_obj):
                                i += row
                                _set_line(line)
                                n+=1
                            row = i

#                         for j, h in enumerate(head):
#                             sheet.set_column(j, j, h['larg'])
# 
#                         _set_table(start_row, row)
#                         row += 1
#                 def _set_table(start_row, row):
#                     sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
#                                     {'total_row': 1,
#                                      'columns': table,
#                                      'style': 'Table Style Light 9',
#                                      })
                
            else:  # not summary

                head = [
                    {'name': _(u'Дд'),
                     'larg': 8,
                     'col': {}},
                    {'name': _(u'Хөрөнгийн код'),
                     'larg': 18,
                     'col': {}},
                    {'name': _(u'Хөрөнгийн нэр'),
                     'larg': 40,
                     'col': {}},
                    {'name': _(u'Тоо'),
                     'larg': 10,
                     'col': {}},
                    {'name': _(u'Худалдан авсан огноо'),
                     'larg': 12,
                     'col': {}},
                    {'name': _(u'Худалдан авсан үнэ'),
                     'larg': 15,
                     'col': {}},
                    {'name': _( u'Эхний үлдэгдэл'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'Орлого'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'Капиталжуулалт'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'Зарлага'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'Эцсийн үлдэгдэл'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _( u'ХЭ/Эхний үлдэгдэл'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'ХЭ/Орлого'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'ХЭ/Зарлага'),
                     'larg':15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _(u'ХЭ/Эцсийн үлдэгдэл'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
#                     {'name': _('Amount Currency'),
#                         'larg': 15,
#                         'col': {}},
#                     {'name': _('Match.'),
#                      'larg': 10,
#                      'col': {}},
                ]
                table = []
                for h in head:
                    col = {'header': h['name']}
                    col.update(h['col'])
                    table.append(col)

                def _set_line(line):
#                     print 'line ',line
#                     print '11i',i
                    sheet.write(i, 0, n )
                    sheet.write(i, 1, line.get('code', ''))
                    sheet.write(i, 2, line.get('name', ''))
#                     sheet.write(i, 3, '1')
                    sheet.write(i, 3, _get_data_float(line.get('method_number', '')))
                    sheet.write(i, 4, get_date_format(line.get('date', '')))
                    sheet.write(i, 5, '')
                    sheet.write(i, 6, _get_data_float(line.get('initial_value', '')), currency_format)
                    sheet.write(i, 7, _get_data_float(line.get('income_value', '')), currency_format)
                    sheet.write(i, 8, _get_data_float(line.get('capital_value', '')), currency_format)
                    sheet.write(i, 9, _get_data_float(line.get('expense_value', '')), currency_format)
                    sheet.write(i, 10, _get_data_float(line.get('final_value', '')), currency_format)
                    sheet.write(i, 11, _get_data_float(line.get('initial_depr', '')), currency_format)
                    sheet.write(i, 12, _get_data_float(line.get('income_depr', '')), currency_format)
                    sheet.write(i, 13, _get_data_float(line.get('expense_depr', '')), currency_format)
                    sheet.write(i, 14, _get_data_float(line.get('final_depr', '')), currency_format)
                    
                    if line.get('amount_currency', ''):
                        sheet.write(i, 12, _get_data_float(line.get('amount_currency', '')), workbook.add_format({'num_format': line.get('currency')}))
                    sheet.write(i, 13, line.get('matching_number', ''))

                def _set_table(start_row, row):
#                     print 'start_row11 ',start_row
#                     print 'row1111 ',row
                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })

                # With total workbook
                sheet = workbook.add_worksheet('asset_detail' + _(' Totals'))
                _header_sheet(sheet)

                row = 6
                report = wizard.report_id
                all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                 print 'all_lines---------------- ',len(all_lines)
                for obj in report.report_object_ids:
#                     print 'obj ',obj
                    lines_obj = []
    #                 obj_id = obj.id
                    obj_id = obj.id
                    for line in all_lines:
#                         print 'line ',line
                        if line.get('report_obj_id') == obj_id:
                            lines_obj.append(line)
#                     print 'lines_obj ',lines_obj
                    if lines_obj:
                        row += 1
                        name_view = ''
#                         if wizard.type == 'account':
#                             name_view = obj.account_id.display_name
#                         if wizard.type == 'partner':
#                             name_view = obj.partner_id.display_name
#                         if wizard.type == 'journal':
#                             name_view = obj.journal_id.display_name
#                         if wizard.type == 'analytic':
#                             name_view = obj.analytic_account_id.display_name
                        name_view = obj.account_id.name+' - '+ obj.branch_id.name
#                         print 'name_view ',name_view
                        sheet.write(row, 0, name_view, left)
                        sheet.write(row, 1, '', top)
                        sheet.write(row, 2, '', top)
                        sheet.write(row, 3, '', top)
                        sheet.write(row, 4, '', top)
                        sheet.write(row, 5, '', top)
                        sheet.write(row, 6, '', top)
                        sheet.write(row, 7, '', top)
                        sheet.write(row, 8, '', top)
                        sheet.write(row, 9, '', top)
                        sheet.write(row, 10, '', top)
                        sheet.write(row, 11, '', top)
                        sheet.write(row, 12, '', top)
                        sheet.write(row, 13, '', right)
                        sheet.write(row, 14, '', right)

                        row += 2
                        start_row = row
#                         print '1111 ',line
#                         for i, l in enumerate(all_lines):
#                             i += row
#                             _set_line(l)
# 
#                         row = i
# 
#                         for j, h in enumerate(head):
#                             sheet.set_column(j, j, h['larg'])# Баганы өргөн
# 
#                         _set_table(start_row, row)
#                         row += 2
                        n=1
                        for i, line in enumerate(lines_obj):
                            i += row
                            _set_line(line)
                            n+=1
                        row = i

                        for j, h in enumerate(head):
                            sheet.set_column(j, j, h['larg'])

                        _set_table(start_row, row)
                        row += 2

                # Pivot workbook
#                 sheet = workbook.add_worksheet(report.name)
#                 _header_sheet(sheet)

                # Head
#                 if all_lines:
#                     row = 6
#                     row += 1
#                     start_row = row
#                     for i, l in enumerate(all_lines):
#                         i += row
#                         _set_line(l)
#                     row = i
# 
#                     for j, h in enumerate(head):
#                         sheet.set_column(j, j, h['larg'])
# 
#                     _set_table(start_row, row)

    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)
    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol
