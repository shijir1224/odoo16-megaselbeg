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


class ResignedReport(models.TransientModel):
    _name = "resigned.report"

    company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id)
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил' )
    date_from = fields.Date('Эхлэх огноо')
    date_to = fields.Date('Дуусах огноо')

    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'Ажлаас гарах ярилцлагын тайлан ')

        file_name = 'Ажлаас гарах ярилцлагын тайлан'

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
        
        sheet.merge_range(rowx + 1, 1, rowx + 1, 13,  self.company_id.name + " " + "компани " + self.work_location_id.name + " " + "ажилчдын ажлаас гарах үеийн ярилцлагын тайлан" , theader1)
        rowx = 3

        sheet.merge_range(rowx, 0, rowx+1, 0, u'№', theader),
        sheet.merge_range(rowx, 1, rowx+1, 1, u'Ажилтны код', theader),
        sheet.merge_range(rowx, 2, rowx+1, 2, u' Нэр', theader),
        sheet.merge_range(rowx, 3, rowx+1, 3, u' Хэлтэс', theader),
        sheet.merge_range(rowx, 4, rowx+1, 4, u'Албан тушаал', theader),
        sheet.merge_range(rowx, 5, rowx+1, 5, u'Ажлаас гарсан огноо', theader),
        sheet.merge_range(rowx, 6, rowx+1, 6, u'Ажлаас гарсан шалтгаан', theader),
        sheet.merge_range(rowx, 7, rowx+1, 7, u'Та авч байсан цалиндаа хэр сэтгэл ханамжтай байсан бэ?', theader),
        sheet.merge_range(rowx, 8, rowx+1, 8, u'Таны хийж байсан ажил таны мэдлэг, ур чадварыг хэр ашиглаж чадаж байсан вэ?', theader),
        sheet.merge_range(rowx, 9, rowx+1, 9, u'Байгууллага ажилтнуудынхаа санал бодлыг хэр хүлээж авч хэрэгжүүлдэг гэж та бодож байна?', theader),
        sheet.merge_range(rowx, 10, rowx+1, 10, u'Байгууллагаас хэрэгжүүлж буй нийгмийн хангамж, дэмжлэгт ямар үнэлэлт өгөх вэ?', theader),
        sheet.merge_range(rowx, 11, rowx+1, 11, u'Соёолон интернэшнл” ХХК-д ажиллахад давуу тал нь юу байсан бэ?', theader),
        sheet.merge_range(rowx, 12, rowx+1, 12, u'“Соёолон интернэшнл” ХХК-д ажиллахад дутагдалтай тал нь юу байсан бэ?', theader),
        sheet.merge_range(rowx, 13, rowx+1, 13, u'Байгууллага доторх карьер өсөлтийн талаар саналаа үлдээнэ үү?', theader),
        sheet.merge_range(rowx, 14, rowx+1, 14, u'Цаашид ажил сайжруулах тухай үнэтэй санал сэтгэгдэлээ үлдээнэ үү?', theader),


        rowx += 1
        sheet.set_column('A:A', 3)
        sheet.set_column('B:G', 20)
        sheet.set_column('D:E', 25)
        sheet.set_column('H:K', 30)
        sheet.set_column('L:O', 38)

        rowx += 1
        n = 1



        query = """SELECT
                hr.last_name as last_name,
                hr.name as name,
                hr.id as hr_id,
                hr.identification_id as identification_id,
                hr.work_end_date as work_end_date,
                hj.id as hj_id,
                hr.advantage as advantage,
                hr.weakness as weakness,
                hr.career_growth as career_growth,
                hr.comment as comment,
                hd.name as dep_name
                FROM hr_employee as hr 
                LEFT JOIN hr_department as hd ON hd.id = hr.department_id
                LEFT JOIN hr_job as hj ON hj.id = hr.job_id
                WHERE hr.work_location_id ='%s' and hr.work_end_date>='%s' and hr.work_end_date<='%s'
                and hr.employee_type = 'resigned'"""%(self.work_location_id.id, self.date_from, self.date_to )  

        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
             
        for rec in records:            
            hr_id = self.env['hr.employee'].sudo().browse(int(rec['hr_id']))
            job_name = self.env['hr.job'].search([('id','=', rec['hj_id'])]).name



            sheet.write(rowx, 0, n, contest_left)
            sheet.write(rowx, 1, rec['identification_id'], contest_left)
            sheet.write(rowx, 2, rec['name'],  contest_left)
            sheet.write(rowx, 3, rec['dep_name'], contest_left)
            sheet.write(rowx, 4, job_name, contest_left)
            sheet.write(rowx, 5, rec['work_end_date'], content_date_center)
            sheet.write(rowx, 6, dict(hr_id._fields['resigned_type'].selection).get(hr_id.resigned_type), contest_center)
            sheet.write(rowx, 7, dict(hr_id._fields['satisfaction'].selection).get(hr_id.satisfaction), contest_center)
            sheet.write(rowx, 8, dict(hr_id._fields['used_skill'].selection).get(hr_id.used_skill), contest_center)
            sheet.write(rowx, 9, dict(hr_id._fields['emp_offer'].selection).get(hr_id.emp_offer), contest_center)
            sheet.write(rowx, 10, dict(hr_id._fields['social_support'].selection).get(hr_id.social_support), contest_center)
            sheet.write(rowx, 11, rec['advantage'], contest_left)
            sheet.write(rowx, 12, rec['weakness'], contest_left)
            sheet.write(rowx, 13, rec['career_growth'], contest_left)
            sheet.write(rowx, 14, rec['comment'], contest_left)


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
