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
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodestring


class EmployeeTurnoverReport(models.TransientModel):
    _name = "employee.turnover.report"
    _description = 'employee turnover report'

    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date('Эхлэх огноо')
    date_to = fields.Date('Дуусах огноо')

    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'report')

        file_name = 'Эргэцийн тайлан'

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

        rowx = 3					
        sheet.merge_range(rowx, 0, rowx+1, 0, u'№', theader),
        sheet.merge_range(rowx, 1, rowx, 2, u'Эргэц тооцсон хугацаа', theader),
        sheet.write(rowx+1, 1, u'Эхлэх хугацаа', theader),
        sheet.write(rowx+1, 2, u'Дуусах хугацаа', theader),
        sheet.merge_range(rowx, 3, rowx, 4, u'Ажилтны тоо', theader),
        sheet.write(rowx+1, 3, u'Эхлэх хугацааны ажилтны тоо', theader),
        sheet.write(rowx+1, 4, u'Дуусах хугацааны ажилтны тоо', theader),
        sheet.merge_range(rowx, 5, rowx+1, 5, u'Шинээр ажилд авсан ажилтны тоо', theader),
        sheet.merge_range(rowx, 6, rowx+1, 6, u'Компани дотроо шилжин ажилласан ажилтны тоо', theader),
        sheet.merge_range(rowx, 7, rowx+1, 7, u'Өөрийн хүсэлтээр ажлаас гарсан ажилтны тоо', theader),
        sheet.merge_range(rowx, 8, rowx+1, 8, u'Ажил олгогчийн зүгээс ажлаас чөлөөлсөн ажилтны тоо', theader),
        sheet.merge_range(rowx, 9, rowx+1, 9, u'Нийт эргэц/хувь', theader),
        sheet.merge_range(rowx, 10, rowx+1, 10, u'Өөрийн хүсэлтээр ажлаас гарсан ажилтнуудын эргэцэд эзлэх хувь', theader),
        sheet.merge_range(rowx, 11, rowx+1, 11, u'Тогтоон барилтын хувь', theader),
        sheet.merge_range(rowx, 12, rowx+1, 12, u'Одоогийн ажилтнуудын дундаж ажилласан хугацаа (жил)', theader),
        sheet.merge_range(rowx, 13, rowx+1, 13, u'Ажлаас гарсан ажилтнуудын нийт тоо', theader),
        sheet.merge_range(rowx, 14, rowx+1, 14, u'Ажлаас гарсан ажилтнуудын ажилласан дундаж хугацаа (жил)', theader),
        rowx += 1
      
        n = 1
        turn_over=0
        type1_percent=0
        togtoon=0
        # Шинээр ажилд авсан ажилтны тоо
        emp_pool = self.env['hr.employee'].search([('engagement_in_company', '>=', self.date_from),('engagement_in_company', '<=', self.date_to),('employee_type','not in',('resigned','waiting','blacklist','freelance'))])
        # Ажилтны тоо
        emps = self.env['hr.employee'].search([('employee_type','not in',('resigned','waiting','blacklist','freelance'))])   
        #  Ажлаас гарсан ажилтны тоо
        emp_re_pool = self.env['hr.employee'].search([('work_end_date', '>=', self.date_from),('work_end_date', '<=', self.date_to),('employee_type', '=','resigned')])
      
        # Эхлэх хугацааны ажилтны тоо
        emp_pool_from = self.env['hr.employee'].search([('engagement_in_company', '<=', self.date_from),('employee_type','not in',('resigned','waiting','blacklist','freelance','contractor'))])
        # Дуусах хугацааны ажилтны тоо
        emp_pool_to = self.env['hr.employee'].search([('engagement_in_company', '<=', self.date_to),('employee_type','not in',('resigned','waiting','blacklist','freelance','contractor'))])
        # Компани дотроо шилжин ажилласан ажилтны тоо
        order_pool = self.env['hr.order'].search([('type', '=', 'type4'),('starttime', '>=', self.date_from),('starttime', '<=', self.date_to),('state', '=', 'done')])
        # Өөрийн хүсэлтээр ажлаас гарсан ажилтны тоо
        order_type1 = self.env['hr.employee'].search([('resigned_type', '=', 'type1'),('work_end_date', '>=', self.date_from),('work_end_date', '<=', self.date_to),('employee_type', '=', 'resigned')])
        # Ажил олгогчийн зүгээс ажлаас чөлөөлсөн ажилтны тоо
        order_type2 = self.env['hr.employee'].search([('resigned_type', '=', 'type2'),('work_end_date', '>=', self.date_from),('work_end_date', '<=', self.date_to),('employee_type', '=', 'resigned')])
       
        # Тогтвортой байдлын хувь \RR\= (7/9)x100=77.7%
        # Эргэцийн хувь= (2/9)x100= 22.2%

        #  Нийт эргэц/хувь
        if len(emp_re_pool)>0 and len(emp_pool_from) and len(emp_pool_to):
            turn_over = len(emp_re_pool)/ ((len(emp_pool_from) +len(emp_pool_to))/2) * 100

         # Өөрийн хүсэлтээр ажлаас гарсан ажилтнуудын эргэцэд эзлэх хувь
        if len(order_type1)>0 and turn_over>0:
            type1_percent = len(order_type1) * 100/ turn_over
        # Тогтоон барилтын хувь
        if  len(emp_pool_to)>0:
            togtoon =  ((len(emp_pool_from) + len(emp_pool_to))/2) / len(emp_pool_to) * 100
        # Одоогийн ажилтнуудын дундаж ажилласан хугацаа
        delta_all_month=0
        delta_all_month_avg=0
        res_all_month_avg=0
        delta_rec_all_month=0
        emp_ids = self.env['hr.employee'].sudo().search([('employee_type','in',('employee','trainee','contractor'))])
        for emp in emp_ids:
            today = Date.today()
            in_date = datetime.strptime(str(emp.engagement_in_company), "%Y-%m-%d")
            today = datetime.strptime(str(today), "%Y-%m-%d")
            delta = today - in_date
            delta_all_month += delta.days
        if delta_all_month>0:
            delta_all_month_avg = (delta_all_month/len(emp_ids))/365

        rec_emp_ids = self.env['hr.employee'].sudo().search([('employee_type','in',('resigned','blacklist'))])
        for emp in rec_emp_ids:
            today = Date.today()
            in_date = datetime.strptime(str(emp.engagement_in_company), "%Y-%m-%d")
            today = datetime.strptime(str(today), "%Y-%m-%d")
            delta = today - in_date
            delta_rec_all_month += delta.days
        if delta_rec_all_month>0:
            res_all_month_avg = (delta_rec_all_month/len(rec_emp_ids))/365

        # Ажлаас гарсан ажилтнуудын ажилласан дундаж хугацаа
        emp_res_ids = self.env['hr.employee'].sudo().search([('employee_type','=','resigned')])
        for emp in emp_res_ids:
            today = Date.today()
            if emp.work_end_date and emp.engagement_in_company:
                in_date = datetime.strptime(str(emp.work_end_date), "%Y-%m-%d")
                en_date = datetime.strptime(str(emp.engagement_in_company), "%Y-%m-%d")
                delta = in_date - en_date
        
        sheet.write(rowx+1, 1, self.date_from, content_date_center)
        sheet.write(rowx+1, 2, self.date_to, content_date_center)
        sheet.write(rowx+1, 3, len(emp_pool_from), contest_left)
        sheet.write(rowx+1, 4, len(emp_pool_to), contest_left)
        sheet.write(rowx+1, 5, len(emp_pool), contest_left)
        sheet.write(rowx+1, 6, len(order_pool), contest_left)
        sheet.write(rowx+1, 7, len(order_type1), contest_left)
        sheet.write(rowx+1, 8, len(order_type2), contest_left)
        sheet.write(rowx+1, 9, turn_over ,contest_left)
        sheet.write(rowx+1, 10, type1_percent, contest_left)
        sheet.write(rowx+1, 11, togtoon, contest_left)
        sheet.write(rowx+1, 12, delta_all_month_avg, contest_left)
        sheet.write(rowx+1, 13, len(emp_re_pool), contest_left)
        sheet.write(rowx+1, 14, res_all_month_avg, contest_left)
        rowx += 1
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
