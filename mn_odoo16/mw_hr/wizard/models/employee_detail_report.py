# -*- coding: utf-8 -*-

import xlsxwriter
from io import BytesIO

from odoo import fields, models
import base64
try:
    # Python 2 support
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodestring


class EmployeeDetailReport(models.TransientModel):
    _name = "hr.employee.detail.report"
    _description = 'hr employee detail report'

    company_id = fields.Many2one('res.company', string='Компани')

    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'report')

        file_name = 'Ажилтны тайлан'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(8)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#fce9da')

        theader1 = workbook.add_format({'bold': 1})
        theader1.set_italic()
        theader1.set_font_size(8)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')
        theader1.set_border(style=1)
        theader1.set_bg_color('#dbedf3')

        theader2 = workbook.add_format({'bold': 1})
        theader2.set_italic()
        theader2.set_font_size(8)
        theader2.set_text_wrap()
        theader2.set_font('Times new roman')
        theader2.set_align('center')
        theader2.set_align('vcenter')
        theader2.set_border(style=1)
        theader2.set_bg_color('#d8bed8')

        contest_left = workbook.add_format({'num_format': '###,###,###'})
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

        content_date_center = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        content_date_center.set_text_wrap()
        content_date_center.set_font_size(9)
        content_date_center.set_border(style=1)
        content_date_center.set_align('vcenter')

        rowx = 0
        rowx = 2

        sheet.merge_range(rowx, 0, rowx+3, 0, u'№', theader),
        sheet.merge_range(rowx, 1, rowx+3, 1, u'Овог', theader),
        sheet.merge_range(rowx, 2, rowx+3, 2, u'Нэр', theader),
        sheet.merge_range(rowx, 3, rowx+3, 3, u'Албан тушаал', theader),
        sheet.merge_range(rowx, 4, rowx+3, 4, u'Хэлтэс', theader),
        sheet.merge_range(rowx, 5, rowx+3, 5, u'Ажилтны код', theader),
        sheet.merge_range(rowx, 6, rowx+3, 6, u'Ажилд орсон огноо', theader),
        sheet.merge_range(rowx, 7, rowx+3, 7, u'Регистр', theader),
        sheet.merge_range(rowx, 8, rowx+3, 8, u'Төрсөн огноо', theader),
        sheet.merge_range(rowx, 9, rowx+3, 9, u'Хүйс', theader),
        sheet.merge_range(rowx, 10, rowx+3, 10, u'Нас', theader),
        sheet.merge_range(rowx, 11, rowx+3, 11, u'Утасны дугаар', theader),
        sheet.merge_range(rowx, 12, rowx+3, 12, u'И-мэйл', theader),
        sheet.merge_range(rowx, 13, rowx+3, 13, u'Ажилтны төлөв', theader),
        sheet.merge_range(rowx, 14, rowx+3, 14, u'Амрах хоног', theader),
        sheet.merge_range(rowx, 15, rowx+3, 15, u'Компанид ажилласан жил/Хэвийн/', theader),
        sheet.merge_range(rowx, 16, rowx+3, 16, u'Улсад ажилласан жил/Хэвийн/', theader),
        sheet.merge_range(rowx, 17, rowx+3, 17, u'Компанид ажилласан жил/Хэвийн бус/', theader),
        sheet.merge_range(rowx, 18, rowx+3, 18, u'Улсад ажилласан жил/Хэвийн бус/', theader),
        sheet.merge_range(rowx, 19, rowx+3, 19, u'Нийт улсад ажилласан жил', theader),
        sheet.merge_range(rowx, 20, rowx, 25, u'Төгссөн сургууль', theader1),
        sheet.merge_range(rowx+1, 20, rowx+3, 20, u'Сургуулийн нэр', theader1),
        sheet.merge_range(rowx+1, 21, rowx+3, 21, u'Эрдмийн зэрэг', theader1)
        sheet.merge_range(rowx+1, 22, rowx+3, 22, u'Мэргэжил', theader1)
        sheet.merge_range(rowx+1, 23, rowx+3, 23, u'Элссэн', theader1)
        sheet.merge_range(rowx+1, 24, rowx+3, 24, u'Төгссөн', theader1)
        sheet.merge_range(rowx+1, 25, rowx+3, 25, u'Голч оноо', theader2)
        sheet.merge_range(rowx, 26, rowx+3, 26, u'Хүүхдийн тоо', theader)
        rowx += 1
        sheet.set_column('A:A', 5)
        sheet.set_column('C:C', 15)
        sheet.set_column('K:K', 8)
        sheet.set_column('D:D', 15)
        sheet.set_column('O:O', 8)
        sheet.set_column('F:F', 10)
        sheet.set_column('E:E', 15)
        sheet.set_column('M:M', 30)
        sheet.set_column('N:N', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('U:U', 27)

        query = """SELECT
            hr.id as hr_id,
            hr.last_name as last_name,
            hr.name as name,
            hr.children as children,
            hr.passport_id as passport_id,
            hr.age as age,
            hr.work_phone as work_phone,
            hr.work_email as work_email,
            hr.engagement_in_company as in_date,
            hr.identification_id as identification_id,
            hr.employee_type as employee_type,
            hj.id as job_id,
            hd.id as department
        FROM hr_employee hr
        LEFT JOIN hr_department hd ON hd.id = hr.department_id
        LEFT JOIN hr_job hj ON hj.id = hr.job_id
        LEFT JOIN res_company rc ON rc.id = hr.company_id
        WHERE hr.employee_type IN ('employee', 'trainee', 'contractor') AND rc.id = %s
        ORDER BY hr.id
        """
        self.env.cr.execute(query, (self.company_id.id,))

        records = self.env.cr.dictfetchall()
        rowx += 3
        n = 1
        level = ''
        status = 0
        gender = ''
        for rec in records:
            emp_id = self.env['hr.employee'].search([('id', '=', rec['hr_id'])], limit=1)
            job_name = self.env['hr.job'].search([('id', '=', rec['job_id'])], limit=1).name
            department_name = self.env['hr.department'].search([('id', '=', rec['department'])]).name
            emp_ids = rec['hr_id']
            emp = self.env['hr.employee'].browse(emp_ids)
            emp_name = emp.with_context(lang='en_US').name if emp.exists() else 'Бүртгэлгүй'
            query1 = """SELECT
                hr.id as hr_id,
                hs.id as hs_id,
                hsn.name as hsn_name,
                hs.start_date as start_date,
                hs.end_date as end_date,
                hs.honest as honest,
                hs.job as job,
                hs.education_level as education_level
                FROM hr_employee hr
                LEFT JOIN hr_school hs ON hs.employee_id=hr.id
                LEFT JOIN hr_school_name hsn ON hsn.id=hs.name
                WHERE hr.id=%s
                ORDER BY hr.name""" % (rec['hr_id'])
            self.env.cr.execute(query1)
            recs = self.env.cr.dictfetchall()
            education_level = ''
            status = ''
            rowl = rowx
            t = 0
            s = 0

            for r in recs:
                if r['education_level'] == 'basilar':
                    education_level = 'Суурь боловсрол'
                elif r['education_level'] == 't_senior':
                    education_level = 'Тусгай дунд'
                elif r['education_level'] == 'senior':
                    education_level = 'Бүрэн дунд'
                elif r['education_level'] == 'bachelor':
                    education_level = 'Бакалавр'
                elif r['education_level'] == 'master':
                    education_level = 'Магисрт'
                elif r['education_level'] == 'doctor':
                    education_level = 'Доктор'
                elif r['education_level'] == 'propessor':
                    education_level = 'Профессор'

                sheet.write(rowl, 20, r['hsn_name'], contest_left)
                sheet.write(rowl, 21, education_level, contest_left)
                sheet.write(rowl, 22, r['job'], contest_left)
                sheet.write(rowl, 23, r['start_date'], content_date_center)
                sheet.write(rowl, 24, r['end_date'], content_date_center)
                sheet.write(rowl, 25, r['honest'], contest_left)
                rowl += 1
                t += 1

            if t <= 1:
                sheet.write(rowx, 0, n, contest_left)
                sheet.write(rowx, 1, rec['last_name'], contest_left)
                sheet.write(rowx, 2, emp_name, contest_left)
                sheet.write(rowx, 3, job_name, contest_left)
                sheet.write(rowx, 4, department_name, contest_left)
                sheet.write(rowx, 5, rec['identification_id'], contest_left)
                sheet.write(rowx, 6, rec['in_date'], content_date_center)
                sheet.write(rowx, 7, rec['passport_id'], contest_left)
                sheet.write(rowx, 8, emp_id.birthday, content_date_center)
                sheet.write(rowx, 9, dict(emp_id._fields['gender'].selection).get(emp_id.gender), contest_left)
                sheet.write(rowx, 10, rec['age'], contest_left)
                sheet.write(rowx, 11, rec['work_phone'], contest_left)
                sheet.write(rowx, 12, rec['work_email'], contest_left)
                sheet.write(rowx, 13, dict(emp_id._fields['employee_type'].selection).get(emp_id.employee_type), contest_left)
                sheet.write(rowx, 14, emp_id.days_of_annualleave, contest_left)
                sheet.write(rowx, 15, emp_id.natural_compa_work_year, contest_left)
                sheet.write(rowx, 16, emp_id.natural_uls_work_year, contest_left)
                sheet.write(rowx, 17, emp_id.minikin_compa_work_year, contest_left)
                sheet.write(rowx, 18, emp_id.minikin_uls_work_year, contest_left)
                sheet.write(rowx, 19, emp_id.sum_uls_work_year, contest_left)
                sheet.write(rowx, 26, rec['children'], contest_left)
            else:
                sheet.merge_range(rowx, 0, rowx+t-1, 0, n, contest_left)
                sheet.merge_range(rowx, 1, rowx+t-1, 1,
                                  rec['last_name'], contest_left)
                sheet.write(rowx, 2, emp_name, contest_left)
                sheet.merge_range(rowx, 3, rowx+t-1, 3,
                                  job_name, contest_left)
                sheet.write(rowx, 4, department_name, contest_left)
                sheet.merge_range(rowx, 4, rowx+t-1, 4, department_name, contest_left)
                sheet.merge_range(rowx, 5, rowx+t-1, 5,
                                  rec['identification_id'], contest_left)
                sheet.merge_range(rowx, 6, rowx+t-1, 6,
                                  rec['in_date'], content_date_center)
                sheet.merge_range(rowx, 7, rowx+t-1, 7,
                                  rec['passport_id'], contest_left)
                sheet.merge_range(rowx, 8, rowx+t-1, 8,
                                  emp_id.birthday, content_date_center)
                sheet.merge_range(rowx, 9, rowx+t-1, 9,
                                  dict(emp_id._fields['gender'].selection).get(emp_id.gender), contest_left)
                sheet.merge_range(rowx, 10, rowx+t-1, 10,
                                  rec['age'], contest_left)
                sheet.merge_range(rowx, 11, rowx+t-1, 11,
                                  rec['work_phone'], contest_left)
                sheet.merge_range(rowx, 12, rowx+t-1, 12,
                                  rec['work_email'], contest_left)
                sheet.merge_range(rowx, 13, rowx+t-1, 13,
                                  status, contest_left)
                sheet.merge_range(rowx, 14, rowx+t-1, 14,
                                  emp_id.days_of_annualleave, contest_left)
                sheet.merge_range(rowx, 15, rowx+t-1, 15,
                                  emp_id.natural_compa_work_year, contest_left)
                sheet.merge_range(rowx, 16, rowx+t-1, 16,
                                  emp_id.natural_uls_work_year, contest_left)
                sheet.merge_range(rowx, 17, rowx+t-1, 17,
                                    emp_id.minikin_compa_work_year, contest_left)
                sheet.merge_range(rowx, 18, rowx+t-1, 18,
                                    emp_id.minikin_uls_work_year, contest_left)
                sheet.merge_range(rowx, 19, rowx+t-1, 19,
                                    emp_id.sum_uls_work_year, contest_left)
                sheet.merge_range(rowx, 26, rowx+t-1, 26,
                                    rec['children'], contest_left)
            rowx += t
            n += 1

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

