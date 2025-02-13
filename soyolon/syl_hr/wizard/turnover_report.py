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


class HrTurnoverReport(models.TransientModel):
	_name = "hr.turnover.report"

  
	s_date = fields.Date('Эхлэх огноо')
	e_date = fields.Date('Дуусах огноо')
	work_location_id = fields.Many2one('hr.work.location', string='Ажлын байршил')

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Эргэцийн тайлан')

		file_name = 'Эргэцийн тайлан'
		
		theader1 = workbook.add_format({'bold': 1})
		theader1.set_italic()
		theader1.set_font_size(16)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')
		theader1.set_num_format('#0')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(12)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#fce9da')

		contest_center = workbook.add_format({'num_format': '#,##0.00'})
		contest_center.set_text_wrap()
		contest_center.set_font_size(12)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0.00')

		content_date_center = workbook.add_format({'num_format': 'YYYY-MM-DD'})
		content_date_center.set_text_wrap()
		content_date_center.set_font_size(12)
		content_date_center.set_border(style=1)
		content_date_center.set_align('vcenter')

		rowx = 0
		sheet.merge_range(0, 0, 0, 3,"Хүний нөөцийн эргэц" , theader1)
		sheet.merge_range(2, 0, 2, 3,self.s_date.year, theader1)
		rowx = 5

		sheet.merge_range(rowx, 0, rowx+1, 0, u'№', theader),
		sheet.merge_range(rowx, 1, rowx+1, 1, u'Сар', theader),
		sheet.merge_range(rowx, 2, rowx+1, 2, u'Ажлаас гарсан ажилтны тоо', theader),
		sheet.merge_range(rowx, 3, rowx+1, 3, u'Сарын эхэнд байсан ажилтны тоо', theader),
		sheet.merge_range(rowx, 4, rowx+1, 4, u'Сарын сүүлээрх ажилтны тоо', theader),
		sheet.merge_range(rowx, 5, rowx+1, 5, u'Дундаж ажилтны тоо', theader),
		sheet.merge_range(rowx, 6, rowx+1, 6, u'Хүний нөөцийн эргэц', theader),
		
	 
		rowx += 1
		sheet.set_column('A:A', 3)
		sheet.set_column('B:G', 20)
		sheet.set_column('D:E', 25)
		sheet.set_column('H:K', 30)
		sheet.set_column('L:O', 38)
		rowx += 1
		n = 1
		query = """SELECT
			wbl.e_date as e_date,
			sum(wbl.resigned_emp) as resigned_emp,
			sum(wbl.smonth_emp) as smonth_emp,
			sum(wbl.emonth_emp) as emonth_emp,
			sum(wbl.avg_emp) as avg_emp,
			sum(wbl.turn_over) as turn_over
			FROM hr_turnover as wbl 
			WHERE wbl.s_date >= '%s' and wbl.e_date <= '%s'
			GROUP BY wbl.e_date
			ORDER BY wbl.e_date
			"""%(self.s_date,self.e_date) 
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		
		for rec in records:			
			sheet.write(rowx, 0, n, contest_center)
			sheet.write(rowx, 1, rec['e_date'], content_date_center)
			sheet.write(rowx, 2, rec['resigned_emp'],  contest_center)
			sheet.write(rowx, 3, rec['smonth_emp'], contest_center)
			sheet.write(rowx, 4, rec['emonth_emp'], contest_center)
			sheet.write(rowx, 5,rec['avg_emp'], contest_center)
			sheet.write(rowx, 6, rec['turn_over'], contest_center)
			rowx += 1
			n += 1
		save_row=8
		sheet.merge_range(rowx,0,rowx,1, u"Жилийн дундаж", theader)
		sheet.write_formula(rowx, 2, '{=AVG('+self._symbol(save_row-1, 2) +':'+ self._symbol(rowx-1, 2)+')}', contest_center)
		sheet.write_formula(rowx, 3, '{=AVG('+self._symbol(save_row-1, 3) +':'+ self._symbol(rowx-1, 3)+')}', contest_center)
		sheet.write_formula(rowx, 4, '{=AVG('+self._symbol(save_row-1, 4) +':'+ self._symbol(rowx-1, 4)+')}', contest_center)
		sheet.write_formula(rowx, 5, '{=AVG('+self._symbol(save_row-1, 5) +':'+ self._symbol(rowx-1, 5)+')}', contest_center)
		sheet.write_formula(rowx, 6, '{=AVG('+self._symbol(save_row-1, 6) +':'+ self._symbol(rowx-1, 6)+')}', contest_center)

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
