# -*- coding: utf-8 -*-

try:
    # Python 2 support
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodestring
import xlsxwriter
from io import BytesIO
import base64

from odoo import fields, models
DATE_FORMAT = "%Y-%m-%d"

class AllowanceReport(models.TransientModel):
    _name = "allowance.report"
    _description = "Allowance report"

    date_from = fields.Date('Эхлэх огноо')
    date_to = fields.Date('Дуусах огноо')

    def export_report(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'Тэтгэмж')

        file_name = 'Тэтгэмж тайлан'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#BEC5D1')

        theader3 = workbook.add_format({'bold': 1})
        theader3.set_font_size(11)
        theader3.set_font('Times new roman')
        theader3.set_align('left')
        theader3.set_align('vcenter')

        contest_date_center = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        contest_date_center.set_text_wrap()
        contest_date_center.set_font_size(9)
        contest_date_center.set_border(style=1)
        contest_date_center.set_align('vcenter')


        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_font('Times new roman')
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_num_format('#,##0')

        rowx=3
        sheet.merge_range(1,1,1,5, u'Тэтгэмжийн тайлан', theader3),

        sheet.merge_range(rowx,1,rowx+1,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+1,2, u'Компани', theader),
        sheet.merge_range(rowx,3,rowx+1,3, u'Ажилтны код', theader),
        sheet.merge_range(rowx,4,rowx+1,4, u'Овог', theader),
        sheet.merge_range(rowx,5,rowx+1,5, u'Нэр', theader),
        sheet.merge_range(rowx,6,rowx+1,6, u'Албан тушаал', theader),
        sheet.merge_range(rowx,7,rowx+1,7, u'Тэтгэмжийн нэр', theader),
        sheet.merge_range(rowx,8,rowx+1,8, u'Тэтгэмжийн төрөл', theader),
        sheet.merge_range(rowx,9,rowx+1,9, u'Мөнгөн дүн', theader),
        sheet.merge_range(rowx,10,rowx+1,10, u'Огноо', theader),
    
        rowx+=2
        
        sheet.set_column('A:A', 2)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 10)
        sheet.set_column('M:M', 10)
        sheet.set_column('N:N', 10)

        query = """SELECT 
            ha.type as type,
            ha.date as date,
            ha.amount as amount,
			he.identification_id as identification_id,
			he.last_name as last_name,
			he.name as name,
            rc.name as company_id,
            hj.id as job_id,
            han.name as allowance_id
			FROM hr_allowance ha
            LEFT JOIN hr_allowance_name han ON han.id = ha.allowance_id
            LEFT JOIN hr_employee he ON he.id = ha.employee_id
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN hr_job hj ON hj.id=he.job_id
            WHERE ha.state ='done' and ha.date >='%s' and ha.date <='%s'
			ORDER BY he.identification_id
            """ % (self.date_from, self.date_to)
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        n = 1
        for rec in records:
            job_name = self.env['hr.job'].search([('id','=',rec['job_id'])]).name
            sheet.write(rowx, 1, n, contest_center)
            sheet.write(rowx, 2, rec['company_id'], contest_center)
            sheet.write(rowx, 3, rec['identification_id'], contest_center)
            sheet.write(rowx, 4, rec['last_name'], contest_center)
            sheet.write(rowx, 5, rec['name'], contest_center)
            sheet.write(rowx, 6, job_name, contest_center)
            sheet.write(rowx, 7, rec['allowance_id'],contest_center)
            sheet.write(rowx, 8, rec['type'], contest_center)
            sheet.write(rowx, 9, rec['amount'], contest_center)
            sheet.write(rowx, 10, rec['date'], contest_date_center)
            rowx +=1
            n +=1

        workbook.close()
        out = encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create(
            {'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&downlodr=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }
    
    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)

    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol
            