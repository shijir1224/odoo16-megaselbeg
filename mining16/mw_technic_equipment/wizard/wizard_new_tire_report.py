from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardComponentReport(models.TransientModel):
	_name = "wizard.new.tire.report"
	_description = "wizard new tire report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(string='Дуусах огноо', required=True)

	def export_report(self):
		if self.date_start:
		# 	# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'new_tire_report_'+str(self.date_start)+'.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#E9A227')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(9)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)

			worksheet = workbook.add_worksheet(u'New tire report')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"Шинэ дугуйн тайлан", h1)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet.set_column(1, 1, 15)
			worksheet.write(row, 2, u"Дугуй бренд", header_wrap)
			worksheet.set_column(2, 2, 20)
			worksheet.write(row, 3, u"Хэмжээ", header_wrap)
			worksheet.set_column(3, 3, 10)
			worksheet.write(row, 4, u"Парк дугаар", header_wrap)
			worksheet.set_column(4, 4, 15)
			worksheet.write(row, 5, u"Байрлал", header_wrap)
			worksheet.set_column(5, 5, 5)
			worksheet.write(row, 6, u"Эхлэлийн огноо", header_wrap)
			worksheet.set_column(6, 6, 15)
			worksheet.write(row, 7, u"Төлөв", header_wrap)
			worksheet.set_column(7, 7, 10)
			worksheet.write(row, 8, u"Одоогийн мото цаг", header_wrap)
			worksheet.set_column(8, 8, 15)
			worksheet.write(row, 9, u"Одоо байгаа хээний гүн", header_wrap)
			worksheet.set_column(9, 9, 15)
			# worksheet.write(row, 10, u"Элэгдлийн хувь", header_wrap)
			# worksheet.set_column(10, 10, 30)
			row = 2
			number = 1
			for item in self.env['tire.used.history'].search([('date','>=',self.date_start.strftime("%Y-%m-%d")),('date', '<=', self.date_end.strftime("%Y-%m-%d")),('description','=','Суурьлуулсан, Шинэ дугуй суурьлуулсан')]):
				if date.today() - item.date < timedelta(days=365):
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 1, item.tire_id.serial_number, contest_center)
					worksheet.write(row, 2, item.tire_id.brand_id.name, contest_center)
					worksheet.write(row, 3, item.tire_id.norm_tire_size, contest_center)
					worksheet.write(row, 4, item.tire_id.current_technic_id.program_code or '', contest_center)
					worksheet.write(row, 5, item.tire_id.current_position, contest_center)
					worksheet.write(row, 6, item.tire_id.date_of_record.strftime("%Y-%m-%d"), contest_center)
					worksheet.write(row, 7, item.tire_id.state, contest_center)
					worksheet.write(row, 8, item.tire_id.total_moto_hour, contest_center)
					worksheet.write(row, 9, item.tire_id.tread_current_deep, contest_center)
					# worksheet.write(row, 9, item.tire_id.tread_depreciation_percent_new, contest_center)
					row += 1
					number += 1
			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol


