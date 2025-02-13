from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardComponentReport(models.TransientModel):
	_name = "wizard.retired.tire.report"
	_description = "wizard retired tire report"
	
	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(string='Дуусах огноо', required=True)
	state = fields.Selection([
		('before_deadline','Хугацаанаас өмнө'),
		('after_deadline','Хугацаандаа'),    
		],string = 'Актласан төрөл') 

	def export_report(self):
		if self.state == 'before_deadline':
		# 	# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'retired_tires_before_deadline_report_'+'.xlsx'

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

			worksheet = workbook.add_worksheet(u'Retired tires before deadline report')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"Хугацаанаас өмнө актлагдсан дугуй", h1)

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
			worksheet.write(row, 4, u"Байрлал", header_wrap)
			worksheet.set_column(4, 4, 5)
			worksheet.write(row, 5, u"Акталсан огноо", header_wrap)
			worksheet.set_column(5, 5, 15)
			worksheet.write(row, 6, u"Төлөв", header_wrap)
			worksheet.set_column(6, 6, 10)
			worksheet.write(row, 7, u"Одоогийн мото цаг", header_wrap)
			worksheet.set_column(7, 7, 15)
			worksheet.write(row, 8, u"Одоо байгаа хээний гүн", header_wrap)
			worksheet.set_column(8, 8, 15)
			row = 2
			number = 1
			before = self.env['technic.tire'].search([('date_of_retired','>=',self.date_start.strftime("%Y-%m-%d")),('date_of_retired', '<=', self.date_end.strftime("%Y-%m-%d")),('retire_type','=','before_dealine')])
			for obj in before:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, obj.serial_number, contest_center)
				worksheet.write(row, 2, obj.brand_id.name, contest_center)
				worksheet.write(row, 3, obj.norm_tire_size, contest_center)
				worksheet.write(row, 4, obj.current_position, contest_center)
				worksheet.write(row, 5, obj.date_of_retired.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 6, obj.state, contest_center)
				worksheet.write(row, 7, obj.total_moto_hour, contest_center)
				worksheet.write(row, 8, obj.tread_current_deep, contest_center)
				row += 1
				number += 1
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		elif self.state == 'after_deadline':
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'retired_tires_after_deadline_report_'+'.xlsx'

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

			worksheet = workbook.add_worksheet(u'Retired tires after deadline report')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"Хугацаандаа актлагдсан дугуй", h1)

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
			worksheet.write(row, 4, u"Байрлал", header_wrap)
			worksheet.set_column(4, 4, 5)
			worksheet.write(row, 5, u"Акталсан огноо", header_wrap)
			worksheet.set_column(5, 5, 15)
			worksheet.write(row, 6, u"Төлөв", header_wrap)
			worksheet.set_column(6, 6, 10)
			worksheet.write(row, 7, u"Одоогийн мото цаг", header_wrap)
			worksheet.set_column(7, 7, 15)
			worksheet.write(row, 8, u"Одоо байгаа хээний гүн", header_wrap)
			worksheet.set_column(8, 8, 15)
			row = 2
			number = 1
			for item in self.env['technic.tire'].search([('date_of_retired','>=',self.date_start.strftime("%Y-%m-%d")),('date_of_retired', '<=', self.date_end.strftime("%Y-%m-%d")),('retire_type','=','after_deadline')]):
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, item.serial_number, contest_center)
				worksheet.write(row, 2, item.brand_id.name, contest_center)
				worksheet.write(row, 3, item.norm_tire_size, contest_center)
				worksheet.write(row, 4, item.current_position, contest_center)
				worksheet.write(row, 5, item.date_of_retired.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 6, item.state, contest_center)
				worksheet.write(row, 7, item.total_moto_hour, contest_center)
				worksheet.write(row, 8, item.tread_current_deep, contest_center)
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


