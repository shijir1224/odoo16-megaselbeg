# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from io import BytesIO
import xlsxwriter
import base64
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    created_production_id = fields.Many2one('mrp.production', 'Үүсгэсэн ҮЗ', copy=False)


    def print_line(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'ЭА')

        file_name = 'ЭА'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(10)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#EFEFFF')

        theader2 = workbook.add_format({'bold': 1})
        theader2.set_font_size(12)
        theader2.set_font('Times new roman')
        theader2.set_align('center')
        theader2.set_align('vcenter')

        theader3 = workbook.add_format({'bold': 1})
        theader3.set_font_size(12)
        theader3.set_font('Times new roman')
        theader3.set_align('left')
        theader3.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(10)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)
        contest_left.set_bg_color('#EFEFFF')

        contest_left1 = workbook.add_format({'bold': 1})
        contest_left1.set_text_wrap()
        contest_left1.set_font_size(10)
        contest_left1.set_font('Times new roman')
        contest_left1.set_align('left')
        contest_left1.set_align('vcenter')
        contest_left1.set_border(style=1)
        contest_left1.set_bg_color('#EFEFFF')
        contest_left1.set_rotation(90)

        rowx=0
        save_row=3
        sheet.merge_range(rowx+0,0,rowx+0,3, u'"TTJVCO" LLC', theader3),
        sheet.merge_range(rowx+1,0,rowx+1,9, u'Ээлжийн амралтын олговор авах ажилчид', theader2),

        rowx=3
        sheet.merge_range(rowx, 0,rowx+3,0, u'Хэлтэс', theader),
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'ID', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Албан тушаал', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Компанид ажилд орсон огноо', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Улсад ажилласан жил', theader),
        sheet.merge_range(rowx,8,rowx+3,8, u'Амрах хоног', contest_left1),
        sheet.merge_range(rowx,9,rowx+3,9, u'Өмнө жилийн ЭА олговор авсан огноо', theader),
        sheet.merge_range(rowx,10,rowx+3,10, u'Ажлын байр', theader),
        sheet.freeze_panes(7, 0)
        rowx+=4
        
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 4)
        sheet.set_column('D:D', 13)
        sheet.set_column('E:E', 13)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 10)
        sheet.set_column('I:I', 3)
        sheet.set_column('J:J', 10)
        n=1
        minikin={}
        for data in self.line_ids:
            if data.employee_id.is_minikin==True:
                minikin='Хэвийн бус'
            else:
                minikin='Хэвийн'
            sheet.write(rowx, 0, data.employee_id.department_id.name,contest_left)
            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 4, data.employee_id.name,contest_left)
            sheet.write(rowx, 5, data.employee_id.job_id.name,contest_left)
            sheet.write(rowx, 6, data.in_company_date,contest_left)
            sheet.write(rowx, 7, data.uls_year,contest_left)
            sheet.write(rowx, 8, data.count_day,contest_left)
            sheet.write(rowx, 9, data.before_year_shipt_leave_date,contest_left)
            sheet.write(rowx, 10, minikin,contest_left)

            rowx+=1
            n+=1

        rowx += 1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'res_id': excel_id.id,
            'view_id': False,
#             'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }  