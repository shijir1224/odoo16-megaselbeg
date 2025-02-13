from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardComponentReport(models.TransientModel):
	_name = "wizard.location.tire.report"
	_description = "wizard location tire report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(string='Дуусах огноо', required=True)
	location = fields.Selection([
		('first','1-р байрлал'),
		('second','2-р байрлал'),    
		],string = 'Дугуйн байрлал') 

	def export_report(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = '1, 2-р байрлалын дугуй'+'.xlsx'

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

		if self.location == 'first':
		# 	# Generate EXCEL
			worksheet = workbook.add_worksheet(u'1st position tire report')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"1-р байрлалын дугуйнуудын тайлан", h1)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"Дугуй бренд", header_wrap)
			worksheet.set_column(0, 0, 20)
			worksheet.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet.set_column(1, 1, 15)
			worksheet.write(row, 2, u"TKPH", header_wrap)
			worksheet.set_column(2, 2, 20)
			worksheet.write(row, 3, u"Үйлдвэрлэгсэн огноо", header_wrap)
			worksheet.set_column(3, 3, 20)
			worksheet.write(row, 4, u"Суурьлуулсан огноо", header_wrap)
			worksheet.set_column(4, 4, 10)
			worksheet.write(row, 5, u"Шилжүүлж ашигласан түүх", header_wrap)
			worksheet.set_column(5, 5, 10)
			worksheet.write(row, 6, u"Одоо ашиглаж байгаа техник", header_wrap)
			worksheet.set_column(6, 6, 15)
			worksheet.write(row, 7, u"Одоогийн байрлал", header_wrap)
			worksheet.set_column(7, 7, 15)
			worksheet.write(row, 8, u"Одоогийн мото цаг", header_wrap)
			worksheet.set_column(8, 8, 15)
			row = 2
			number = 1
			before = self.env['technic.tire'].search([('current_position','=',"1")])
			for obj in before:
				worksheet.write(row, 0, obj.brand_id.name, contest_center)
				worksheet.write(row, 1, obj.serial_number, contest_center)
				worksheet.write(row, 2, obj.tkph, contest_center)
				worksheet.write(row, 3, obj.date_of_manufactured.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 4, obj.date_of_record.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 5, dict(obj._fields['new_or_old'].selection).get(obj.new_or_old), contest_center)
				worksheet.write(row, 6, obj.current_technic_id.name, contest_center)
				worksheet.write(row, 7, obj.current_position, contest_center)
				worksheet.write(row, 8, obj.total_moto_hour)
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
		elif self.location == 'second':
			# 	# Generate EXCEL
			worksheet = workbook.add_worksheet(u'2nd position tire report')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"2-р байрлалын дугуйнуудын тайлан", h1)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"Дугуй бренд", header_wrap)
			worksheet.set_column(0, 0, 20)
			worksheet.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet.set_column(1, 1, 15)
			worksheet.write(row, 2, u"TKPH", header_wrap)
			worksheet.set_column(2, 2, 20)
			worksheet.write(row, 3, u"Үйлдвэрлэгсэн огноо", header_wrap)
			worksheet.set_column(3, 3, 20)
			worksheet.write(row, 4, u"Суурьлуулсан огноо", header_wrap)
			worksheet.set_column(4, 4, 10)
			worksheet.write(row, 5, u"Шилжүүлж ашигласан түүх", header_wrap)
			worksheet.set_column(5, 5, 10)
			worksheet.write(row, 6, u"Одоо ашиглаж байгаа техник", header_wrap)
			worksheet.set_column(6, 6, 15)
			worksheet.write(row, 7, u"Одоогийн байрлал", header_wrap)
			worksheet.set_column(7, 7, 15)
			worksheet.write(row, 8, u"Одоогийн мото цаг", header_wrap)
			worksheet.set_column(8, 8, 15)
			row = 2
			number = 1
			before = self.env['technic.tire'].search([('current_position','=',"2")])
			for obj in before:
				worksheet.write(row, 0, obj.brand_id.name, contest_center)
				worksheet.write(row, 1, obj.serial_number, contest_center)
				worksheet.write(row, 2, obj.tkph, contest_center)
				worksheet.write(row, 3, obj.date_of_manufactured.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 4, obj.date_of_record.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 5, dict(obj._fields['new_or_old'].selection).get(obj.new_or_old), contest_center)
				worksheet.write(row, 6, obj.current_technic_id.name, contest_center)
				# dict(obj._fields['new_or_old'].selection).get(obj.new_or_old)	
				worksheet.write(row, 7, obj.current_position, contest_center)
				worksheet.write(row, 8, obj.total_moto_hour)
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
