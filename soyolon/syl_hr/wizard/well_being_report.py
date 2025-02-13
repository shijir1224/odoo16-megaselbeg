# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta
from odoo.fields import Date

from odoo import tools
from odoo import api, fields, models
import base64
try:
    # Python 2 support
    from base64 import encodebytes
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodebytes


class WellBeingReport(models.TransientModel):
    _name = "well.being.report"

  
    year = fields.Char('Жил')

    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'Идэвхжүүлэлт тайлан')

        file_name = 'Идэвхжүүлэлт тайлан'

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(12)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#fce9da')

        theader1 = workbook.add_format({'bold': 1})
        theader1.set_italic()
        theader1.set_font_size(16)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')


        contest_left = workbook.add_format({'num_format': '#########'})
        contest_left.set_text_wrap()
        contest_left.set_font_size(12)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(12)
        contest_center.set_font('Times new roman')
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_num_format('#,##0')

        content_date_center = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        content_date_center.set_text_wrap()
        content_date_center.set_font_size(12)
        content_date_center.set_border(style=1)
        content_date_center.set_align('vcenter')

        rowx = 0
        sheet.merge_range(rowx + 1, 1, rowx + 1, 9,"Хүний нөөцийн WELL-BEING хөтөлбөрийн үйл ажиллагааны тайлан" , theader1)
        rowx = 3

        sheet.merge_range(rowx, 0, rowx+1, 0, u'№', theader),
        sheet.merge_range(rowx, 1, rowx+1, 1, u'Улирал', theader),
        sheet.merge_range(rowx, 2, rowx+1, 2, u' Үйл ажиллагаа', theader),
        sheet.merge_range(rowx, 3, rowx+1, 3, u'Огноо', theader),
        sheet.merge_range(rowx, 4, rowx, 6, u'Хамрагдсан ажилтан', theader),
        sheet.write(rowx+1, 4, u'Нийт ажилтны тоо', theader),
        sheet.write(rowx+1, 5, u'Тоо', theader),
        sheet.write(rowx+1, 6, u'Хувь', theader),
        sheet.merge_range(rowx, 7, rowx+1, 7, u'Батлагдсан төсөв', theader),
        sheet.merge_range(rowx, 8, rowx+1, 8, u'Гүйцэтгэл', theader),
        sheet.merge_range(rowx, 9, rowx+1, 9, u'Тайлбар', theader),
        sheet.merge_range(rowx, 10, rowx+1, 10, u'Үнэлгээ', theader),
     
        rowx += 1
        sheet.set_column('A:A', 3)
        sheet.set_column('B:G', 20)
        sheet.set_column('D:E', 25)
        sheet.set_column('H:K', 30)
        sheet.set_column('L:O', 38)
        rowx += 1
        n = 1
        query = """SELECT
            wbl.name as name,
            wbl.s_date as s_date,
            wbl.emp_count as emp_count,
            wbl.count as count,
            wbl.procent as procent,
            wbl.budget as budget,
            wbl.performance as performance,
            wbl.description as description,
            wbl.ev as ev,
            wb.quart as quart
            FROM well_being_hr_line as wbl 
            LEFT JOIN well_being_hr as wb ON wb.id = wbl.parent_id
            WHERE wb.year = '%s' """%(self.year) 
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
             
        for rec in records:            
            sheet.write(rowx, 0, n, contest_center)
            sheet.write(rowx, 1, rec['quart'], contest_center)
            sheet.write(rowx, 2, rec['name'],  contest_center)
            sheet.write(rowx, 3, rec['s_date'], content_date_center)
            sheet.write(rowx, 4, rec['emp_count'], contest_center)
            sheet.write(rowx, 5, rec['count'], contest_center)
            sheet.write(rowx, 6,rec['procent'], contest_center)
            sheet.write(rowx, 7, rec['budget'], contest_center)
            sheet.write(rowx, 8, rec['performance'], contest_center)
            sheet.write(rowx, 9, rec['description'], contest_center)
            sheet.write(rowx, 10, rec['ev'], contest_center)

            rowx += 1
            n += 1

        workbook.close()
        out = encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create(
            {'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
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
