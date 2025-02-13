# -*- coding: utf-8 -*-
from odoo import models, fields

import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64
from datetime import date

class HseWaterRegistrationReport(models.TransientModel):
	_name = "hse.water.registration.report"
	_description = "hse_water_registration_report.report"

	date_start = fields.Date(string='Эхлэх огноо', required=True,  default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(string='Дуусах огноо', required=True)
	branch_id = fields.Many2one('res.branch', string='Төсөл', required=True)

	def _set_capitalize(self, txt):
		if txt:
			return txt.capitalize()
		else:
			return txt

	def excel_report(self):
		if self.date_start <= self.date_end:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name ='Усны тайлан.xlsx'

			header = workbook.add_format({'bold': 1})
			header.set_font_size(10)
			header.set_font('Times new roman')
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#FBE5D6')

			normal_wrap = workbook.add_format()
			normal_wrap.set_text_wrap()
			normal_wrap.set_font_size(9)
			normal_wrap.set_font('Times new roman')
			normal_wrap.set_align('center')
			normal_wrap.set_align('vcenter')
			normal_wrap.set_border(style=1)
			normal_wrap.set_bg_color('FFFFFF')

			normal_left = workbook.add_format()
			normal_left.set_text_wrap()
			normal_left.set_font_size(9)
			normal_left.set_font('Times new roman')
			normal_left.set_align('center')
			normal_left.set_align('vcenter')
			normal_left.set_border(style=1)
			normal_left.set_bg_color('#FBE5D6')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_font('Times new roman')
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)
			contest_center.set_bg_color('#DEEBF7')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_font('Times new roman')
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)
			contest_left.set_bg_color('#DEEBF7')

			number_format = workbook.add_format()
			number_format.set_text_wrap()
			number_format.set_font_size(9)
			number_format.set_font('Times new roman')
			number_format.set_align('center')
			number_format.set_align('vcenter')
			number_format.set_border(style=1)

			worksheet = workbook.add_worksheet(u'Усны тайлан')
			row = +0
			worksheet.merge_range(row, 0, row, 19, u'Усны тайлан', header)
			worksheet.merge_range( 1, 0, 1, 11, u'Цэвэр ус', header)
			worksheet.merge_range(1 , 12, 1, 19, u'Эргэлтйн ус', header)
			worksheet.write(2, 0, u'№', contest_left)
			worksheet.write(2, 1,u'Төслийн нэр', contest_left)
			worksheet.write(2, 2, u'Үүсэгсэн огноо', contest_left)
			worksheet.write(2, 3, u'Он сар', contest_left)
			worksheet.write(2, 4, u'Худгийн нэр', contest_left)
			worksheet.write(2, 5, u'Эхлэх хугцаа', contest_left)
			worksheet.write(2, 6, u'Дуусгах хуцаа', contest_left)
			worksheet.write(2, 7, u'Ашигласан хоног', contest_left)
			worksheet.write(2, 8, u'Тоолуурын дугаар', contest_left)
			worksheet.write(2, 9, u'Тоолуурын өмнөх заалт', contest_left)
			worksheet.write(2, 10, u'Тоолуурын дараах заалт', contest_left)
			worksheet.write(2, 11, u'Ашгилсан ус/шоометр/', contest_left)
			worksheet.write(2, 12, u'Хаягдлын далангийн дугаар', contest_left)
			worksheet.write(2, 13, u'Эхлэх хугцаа', contest_left)
			worksheet.write(2, 14, u'Дуусгах хуцаа', contest_left)
			worksheet.write(2, 15, u'Ашигласан хоног', contest_left)
			worksheet.write(2, 16, u'Тоолуурын дугаар', contest_left)
			worksheet.write(2, 17, u'Тоолуурын өмнөх заалт', contest_left)
			worksheet.write(2, 18, u'Тоолуурын дараах заалт', contest_left)
			worksheet.write(2, 19, u'Ашгилсан ус/шоометр/', contest_left)
			# row = 3
			worksheet.set_row(row + 2, 25)
			worksheet.set_column('A:A', 3)
			worksheet.set_column('H:H', 15)
			worksheet.set_column('I:I', 15)
			worksheet.set_column('C:C', 15)
			worksheet.set_column('J:J', 15)
			worksheet.set_column('K:K', 15)
			worksheet.set_column('L:L', 15)
			worksheet.set_column('M:M', 15)
			worksheet.set_column('P:P', 15)
			worksheet.set_column('Q:Q', 15)
			worksheet.set_column('R:R', 15)
			worksheet.set_column('S:S', 15)
			worksheet.set_column('T:T', 15)
			worksheet.write(3, 0, u'', normal_wrap)
			worksheet.write(3, 1,u'', normal_wrap)
			worksheet.write(3, 2, u'', normal_wrap)
			worksheet.write(3, 3, u'', normal_wrap)
			worksheet.write(3, 4, u'', normal_wrap)
			worksheet.write(3, 5, u'', normal_wrap)
			worksheet.write(3, 6, u'', normal_wrap)
			worksheet.write(3, 7, u'', normal_wrap)
			worksheet.write(3, 8, u'', normal_wrap)
			worksheet.write(3, 9, u'', normal_wrap)
			worksheet.write(3, 10, u'', normal_wrap)
			worksheet.write(3, 11, u'', normal_wrap)
			worksheet.write(3, 12, u'', normal_wrap)
			worksheet.write(3, 13, u'', normal_wrap)
			worksheet.write(3, 14, u'', normal_wrap)
			worksheet.write(3, 15, u'', normal_wrap)
			worksheet.write(3, 16, u'', normal_wrap)
			worksheet.write(3, 17, u'', normal_wrap)
			worksheet.write(3, 18, u'', normal_wrap)
			worksheet.write(3, 19, u'', normal_wrap)
			
			row += 3
			domains=[
				('date_start', '>=', self.date_start),
				('date_start', '<=', self.date_end)
			]
			if self.branch_id:
				domains.append(('parent_id.branch_id','=',self.branch_id.id))
			waters = self.env['hse.water.registration.line'].search(domains)
			for water in waters:
				worksheet.write(row, 0, row, normal_wrap)
				worksheet.write(row, 1, self._set_capitalize(water.parent_id.branch_id.name) if water.parent_id.branch_id.name else '', normal_wrap)
				worksheet.write(row, 2, water.parent_id.create_date.strftime('%Y-%m-%d') if water.parent_id.create_date else '', normal_wrap)
				worksheet.write(row, 3, water.parent_id.year_month if water.parent_id.year_month else '', normal_wrap)
				worksheet.write(row, 4, self._set_capitalize(water.well_id.name) if water.well_id else '', normal_wrap)
				worksheet.write(row, 5, water.date_start.strftime('%Y-%m-%d') if water.date_start else ' ', normal_wrap)
				worksheet.write(row, 6, water.date_end.strftime('%Y-%m-%d') if water.date_end else ' ', normal_wrap)
				worksheet.write(row, 7, water.used_day if water.used_day else ' ', normal_wrap)
				worksheet.write(row, 8, water.counter_number if water.counter_number else ' ', normal_wrap)
				worksheet.write(row, 9, water.counter_before if water.counter_before else ' ', normal_wrap)
				worksheet.write(row, 10, water.counter_after if water.counter_after else ' ', normal_wrap)
				worksheet.write(row, 11, water.used_water if water.used_water else ' ', normal_wrap)
				worksheet.write(row, 12, self._set_capitalize(water.well_id.name) if water.well_id else ' ', normal_wrap)
				worksheet.write(row, 13, water.date_start.strftime('%Y-%m-%d') if water.date_start else ' ', normal_wrap)
				worksheet.write(row, 14, water.date_end.strftime('%Y-%m-%d') if water.date_end else ' ', normal_wrap)
				worksheet.write(row, 15, water.used_day if water.used_day else ' ', normal_wrap)
				worksheet.write(row, 16, water.counter_number if water.counter_number else ' ', normal_wrap)
				worksheet.write(row, 17, water.counter_before if water.counter_before else ' ', normal_wrap)
				worksheet.write(row, 18, water.counter_after if water.counter_after else ' ', normal_wrap)
				worksheet.write(row, 19, water.used_water if water.used_water else ' ', normal_wrap)
				row += 1

			# =============================
			workbook.close()
			out=base64.encodebytes(output.getvalue())
			excel_id=self.env['report.excel.output'].create(
				{'data': out, 'name': file_name})

			return {
				 'type': 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError((u'Бичлэг олдсонгүй!'))