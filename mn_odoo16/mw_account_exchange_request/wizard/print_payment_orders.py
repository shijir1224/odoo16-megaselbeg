from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time, datetime
from io import BytesIO
import base64
import os,xlrd

import time
from io import BytesIO
import xlsxwriter
# from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles
import base64


class PrintOrder(models.TransientModel):
    _name = 'print.payment.request'
    _description = 'Print'


    @api.model
    def _get_default_date(self):
        context = dict(self.env.context)
        active_id = self.env['payment.request'].browse(context.get('active_id'))
        return active_id.date

    date = fields.Date(u'огноо',default=_get_default_date)
    bank_account_id = fields.Many2one('res.partner.bank', string='Гарах данс')

    def run(self):
        context = dict(self.env.context)
        active_ids = self.env['payment.request'].browse(context.get('active_ids'))
        return self.action_print(active_ids)
        
    def action_print(self,active_ids):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        datas = self
#         self=active_ids
        print('active_ids ',active_ids)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Sheet1')

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
    
        format_title = {
            'font_name': 'Times New Roman',
            'font_size': 12,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': 1,
            'bg_color': '#b3c6ff'
        }
        

        format_group_left_l = {
            'font_name': 'Times New Roman',
            'font_size': 9,
            'bold': False,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
#             'bg_color': '#CFE7F5'
        }

        format_group_left_b = {
            'font_name': 'Times New Roman',
            'font_size': 11,
            'bold': False,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
#             'bg_color': '#CFE7F5'
        }        
        
        format_group_center = workbook.add_format(format_group_center)
        format_name = workbook.add_format(format_name)
        format_content_text_footer = workbook.add_format(format_content_text_footer)
        format_filter = workbook.add_format(ReportExcelCellStyles.format_filter)
        format_title = workbook.add_format(format_title)
        format_group_right = workbook.add_format(ReportExcelCellStyles.format_group_right)
        format_group_float = workbook.add_format(ReportExcelCellStyles.format_group_float)
        format_group_left = workbook.add_format(format_group_left_b)
        format_content_text = workbook.add_format(ReportExcelCellStyles.format_content_text)
        format_content_number = workbook.add_format(ReportExcelCellStyles.format_content_number)
        format_content_float = workbook.add_format(ReportExcelCellStyles.format_content_float)
        format_content_center = workbook.add_format(ReportExcelCellStyles.format_content_center)
        format_group = workbook.add_format(format_group)

        format_group_little_left = workbook.add_format(format_group_left_l)

        format_content_right = workbook.add_format(format_content_right)             
#         duration = self.get_period(cr, uid, form)

        rowx = 0
        worksheet.write(rowx, 0, u'Гүйлгээний төрөл', format_title)
        worksheet.write(rowx, 1, u'Шилжүүлэх данс', format_title)
        worksheet.write(rowx, 2, u'Шилжүүлэх дансны валют', format_title)
        worksheet.write(rowx, 3, u'Хүлээн авах банк/салбар', format_title)
        worksheet.write(rowx, 4, u'Хүлээн авах данс', format_title)
        worksheet.write(rowx, 5, u'Хүлээн авагчийн нэр', format_title)
        worksheet.write(rowx, 6, u'Хүлээн авах дансны валют', format_title)
        worksheet.write(rowx, 7, u'Гүйлгээний утга', format_title)
        worksheet.write(rowx, 8, u'Чухал дүн', format_title)
        worksheet.write(rowx, 9, u'Гүйлгээний дүн', format_title)

        rowx += 1
#         
        worksheet.set_column('A:A', 9)
        worksheet.set_column('B:G', 15)

        worksheet.set_column('H:H', 18)

        worksheet.set_column('J:J', 15)
#               
        n=1
        for req in active_ids:
            amount=0
#             for acc in req.assigned_ids:
#                 if not acc.is_paid:
            code=20
            acc_number=''
            bank_code=''
            acc_num=''
            partner=''
            if req.bank_id and req.bank_id.bic:
#                 if req.bank_id.bic=='5000':
#                     code=10
#                     acc_number='5129081003'
                if self.bank_account_id:   
                    acc_number=self.bank_account_id.acc_number
                    code=self.bank_account_id.bank_id and self.bank_account_id.bank_id.bic or ''
                bank_code=req.bank_id.bic
            if req.dans_id:
                acc_num=req.dans_id.acc_number
                partner=(req.dans_id.acc_holder_name and req.dans_id.acc_holder_name) or (req.partner_id and req.partner_id.name) or ''
            utga=req.narration_id and req.narration_id.name or req.description
            if req.desc_line_ids:
                for dec in req.desc_line_ids:
                    utga+=dec.name+' '
#             if req.postpone_id and req.postpone_id.cancel_id and req.postpone_id.cancel_id.insurance_id:
#                 utga=u'Цуцлалт '+req.postpone_id.cancel_id.insurance_id.name

            worksheet.write(rowx, 0, code, format_group_left)
            worksheet.write(rowx, 1, acc_number, format_group_left)
            worksheet.write(rowx, 2, 'MNT', format_group_left)
            worksheet.write(rowx, 3, bank_code, format_group_left)
            worksheet.write(rowx, 4, acc_num, format_group_left)
            worksheet.write(rowx, 5,  partner, format_group_left)
            worksheet.write(rowx, 6,  'MNT', format_group_left)
            worksheet.write(rowx, 7, utga, format_group_left)
            worksheet.write(rowx, 8, 1, format_group_left)
            worksheet.write(rowx, 9, req.amount, format_content_right)
            rowx += 1
                    
        from io import StringIO
#         output = BytesIO()
        
        file_name = "төлбөр_%s.xlsx" % (time.strftime('%Y%m%d_%H%M'),)
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
