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
from odoo.addons.account_asset_report.report.report_excel_cell_styles import ReportExcelCellStyles

class AccountAssetmoveReportData(models.TransientModel):

    _name = 'account.asset.move.report.data'
#     _order = 'category_id ASC'
    _rec_name = 'asset_id'

    wizard_id = fields.Many2one(
        comodel_name='account.asset.report.move.ledger',
        ondelete='cascade',
        index=True
    )

    report_id = fields.Many2one(
        comodel_name='account.asset.report.move.ledger.report',
        ondelete='cascade',
        index=True
    )    

    report_obj_id = fields.Many2one(
        comodel_name='account.asset.report.move.object',
        ondelete='cascade',
        index=True
    )    

    account_id = fields.Many2one(
        'account.account',
        index=True
    )
    asset_id = fields.Many2one(
        'account.asset.asset',
        index=True
    )
    
    group_id = fields.Many2one(
        'account.asset.category',
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
    initial_value = fields.Float(digits=(16, 2))
    income_value = fields.Float(digits=(16, 2))
    move_inc_value = fields.Float(digits=(16, 2))
    expense_value = fields.Float(digits=(16, 2))
    move_exp_value = fields.Float(digits=(16, 2))

    initial_depr = fields.Float(digits=(16, 2))
    income_depr = fields.Float(digits=(16, 2))
    capital_depr = fields.Float(digits=(16, 2))
    expense_depr = fields.Float(digits=(16, 2))
    final_depr = fields.Float(digits=(16, 2))
    salvage_value = fields.Float(digits=(16, 2))

    owner = fields.Char('owner')
    branch = fields.Char('branch')
    serial = fields.Char('Serial')
    number = fields.Char('Number')

    department = fields.Char('department')
    job = fields.Char('job')
    internal_code = fields.Char('internal_code')
    type = fields.Char('Type')
#tur asiglahgui
    first_depr_date = fields.Date(digits=(16, 2))

class AccountAssetmoveExcel(models.AbstractModel):
    _name = 'report.account_asset_report.move_excel'
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

        if True:
            if True:#report.old_temp:
                
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
                sheet = workbook.add_worksheet('Assets')
                sheet.set_column('A:A', 5)
                sheet.set_column('B:B', 25)
                sheet.set_column('C:C', 20)
                sheet.set_column('D:D', 15)
                sheet.set_column('E:E', 10)
                sheet.set_column('F:F', 10)
                sheet.set_column('G:G', 10)
                sheet.set_column('H:H', 10)
                sheet.set_column('I:I', 10)
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
                sheet.merge_range(rowx, 1, rowx, 9, u'Үндсэн хөрөнгийн хөдөлгөөний тайлан /Ангиллаар/', format_name)
                # report duration
                sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
                # create date
                sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
                rowx += 3
        
                sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
                sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн нэр'), format_title)  # Хөрөнгийн дугаар
                sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Бэлтгэн нийлүүлэгч'), format_title)  # Үндсэн хөрөнгийн нэр
                sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Эзэмшигч'), format_title)  # Хөрөнгийн дугаар
                sheet.merge_range(rowx, 4, rowx + 2, 4, _(u'Хөрөнгийн дугаар'), format_title)  # Элэгдэх тоо
                sheet.merge_range(rowx, 5, rowx + 2, 5, _(u'Байршил'), format_title)  # Худалдан авсан огноо
                sheet.merge_range(rowx, 6, rowx + 2, 6, _(u'Гүйлгээний төрөл'), format_title)  # Байршил
                sheet.merge_range(rowx, 7, rowx + 2, 7, _(u'Огноо'), format_title)  # Байршил
                sheet.merge_range(rowx, 8, rowx + 2, 8, _(u'Тоо'), format_title)  # Байршил
                sheet.merge_range(rowx, 9, rowx + 2, 9, _(u'Өртөг'), format_title)  # Байршил
                sheet.merge_range(rowx, 10, rowx + 2, 10, _(u'Нийт өртөг'), format_title)  # Байршил
                sheet.panes_frozen = True
                sheet.horz_split_pos = 8  # freeze the first row
                rowx += 3
                
                def _set_line(line):
#                         print 'line2 ',line
#                     print '11i',i
                    value=line.get('income_value', '')
                    type='Орлого'
                    too='1'
                    if line.get('expense_value', ''):
                        value=-line.get('expense_value', '')
                        too='-1'
                        type='Зарлага'
                    sheet.write(i, 0, n ,format_content_text)
                    sheet.write(i, 1, line.get('name', ''),format_content_text)
                    sheet.write(i, 2, line.get('job', ''),format_content_text)#Beltgen niiluulegch
                    sheet.write(i, 3, line.get('owner', ''),format_content_text)
                    sheet.write(i, 4, line.get('code', ''), format_content_right)
                    sheet.write(i, 5, line.get('branch', ''), format_content_right)
                    sheet.write(i, 6, line.get('type',''), format_content_right)
                    sheet.write(i, 7, get_date_format(line.get('date', '')),format_content_text)
                    sheet.write(i, 8, too,format_content_right)
                    sheet.write(i, 9, _get_data_float(abs(value)), format_content_right)
                    sheet.write(i, 10, _get_data_float(value),format_content_right)
#                     sheet.write(i, 10, _get_data_float(line.get('expense_value', '')), format_content_right)
#                     sheet.write(i, 11, '',format_content_right)
#                     sheet.write(i, 12, _get_data_float(line.get('final_value', '')), format_content_right)
#                     sheet.write(i, 13, _get_data_float(line.get('initial_depr', '')), format_content_right)
#                     sheet.write(i, 14, _get_data_float(0), format_content_right)
#                     sheet.write(i, 15, _get_data_float(line.get('income_depr', '')), format_content_right)
#                     sheet.write(i, 16, _get_data_float(0), format_content_right)
#                     sheet.write(i, 17, _get_data_float(line.get('expense_depr', '')), format_content_right)
#                     sheet.write(i, 18, _get_data_float(line.get('final_depr', '')), format_content_right)
# #                     sheet.write(i, 19, _get_data_float(), format_content_right)
#                     sheet.write(i, 19, _get_data_float(line.get('salvage_value', '')), format_content_right)
#                     sheet.write(i, 20, _get_data_float(line.get('final_value', '')-line.get('final_depr', '')), format_content_right)
#                     sheet.write(i, 21, line.get('department', ''),format_content_text)
#                     sheet.write(i, 22, line.get('job', ''),format_content_text)
#                     sheet.write(i, 23, line.get('owner', ''),format_content_text)
#                     sheet.write(i, 24, line.get('branch', ''),format_content_text)
#                     sheet.write(i, 25, line.get('serial', ''),format_content_text)
#                     sheet.write(i, 26, line.get('number', ''),format_content_text)
#                     sheet.write(i, 27, line.get('internal_code', ''),format_content_text)
                row = 7
                report = wizard.report_id
                all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                 print 'all_lines---------------- ',len(all_lines)
                totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
#                     print 'totals-------- ',totals

                i=row
                n=''
                if totals[0]['income_value'] and totals[0]['move_inc_value']:
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
#                         sheet.write_formula(row, 10,'{=sum('+ self._symbol(row+1, 10)+':'+ self._symbol(row+len(lines_obj),10) +')}', format_group)
#                         sheet.write_formula(row, 11,'{=sum('+ self._symbol(row+1, 11)+':'+ self._symbol(row+len(lines_obj),11) +')}', format_group)
#                         sheet.write_formula(row, 12,'{=sum('+ self._symbol(row+1, 12)+':'+ self._symbol(row+len(lines_obj),12) +')}', format_group)
#                         sheet.write_formula(row, 13,'{=sum('+ self._symbol(row+1, 13)+':'+ self._symbol(row+len(lines_obj),13) +')}', format_group)
#                         sheet.write_formula(row, 14,'{=sum('+ self._symbol(row+1, 14)+':'+ self._symbol(row+len(lines_obj),14) +')}', format_group)
#                         sheet.write_formula(row, 15,'{=sum('+ self._symbol(row+1, 15)+':'+ self._symbol(row+len(lines_obj),15) +')}', format_group)
#                         sheet.write_formula(row, 16,'{=sum('+ self._symbol(row+1, 16)+':'+ self._symbol(row+len(lines_obj),16) +')}', format_group)
#                         sheet.write_formula(row, 17,'{=sum('+ self._symbol(row+1, 17)+':'+ self._symbol(row+len(lines_obj),17) +')}', format_group)
#                         sheet.write_formula(row, 18,'{=sum('+ self._symbol(row+1, 18)+':'+ self._symbol(row+len(lines_obj),18) +')}', format_group)
#                         sheet.write_formula(row, 19,'{=sum('+ self._symbol(row+1, 19)+':'+ self._symbol(row+len(lines_obj),19) +')}', format_group)
#                         sheet.write_formula(row, 20,'{=sum('+ self._symbol(row+1, 20)+':'+ self._symbol(row+len(lines_obj),20) +')}', format_group)
#                         sheet.write(row, 21, '', format_group)
#                         sheet.write(row, 22, '', format_group)
#                         sheet.write(row, 23, '', format_group)
#                         sheet.write(row, 24, '', format_group)
#                         sheet.write(row, 25, '', format_group)
#                         sheet.write(row, 26, '', format_group)
#                         sheet.write(row, 27, '', format_group)

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

                

    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)
    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol
