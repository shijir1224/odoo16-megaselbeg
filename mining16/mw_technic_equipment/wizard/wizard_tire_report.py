# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardTireReport(models.TransientModel):
	_name = "wizard.tire.report"
	_description = "wizard tire report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(required=True, string=u'Дуусах огноо', )
	technic_ids = fields.Many2many('technic.equipment', string=u'Техник',
		domain=[('rubber_tired','=',True),('state','!=','draft')])
	tire_ids = fields.Many2many('technic.tire', string=u'Дугуй', )

	def export_tire_new_report(self):
		if self.date_start:
			tires = self.env['technic.tire'].search([
				('state','=','using')], order='current_technic_id, current_position, serial_number, brand_id')
			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'tire_new_report.xlsx'

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

			# SHEET 1
			worksheet = workbook.add_worksheet(u'Одоо явж байгаа')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"Хэвийн ажиллаж байгаа дугуйн тайлан", h1)
			worksheet.merge_range(0,4,0,6, u"Огноо: %s -> %s" % (self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d')), contest_center)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet.set_column(1, 1, 20)
			worksheet.write(row, 2, u"Бренд", header_wrap)
			worksheet.set_column(2, 2, 15)
			worksheet.write(row, 3, u"Хэмжээ", header_wrap)
			worksheet.set_column(3, 3, 18)
			worksheet.write(row, 4, u'TRA code', header_wrap)
			worksheet.set_column(4, 4, 20)
			worksheet.write(row, 5, u'Хээний төрөл', header_wrap)
			worksheet.set_column(5, 5, 12)
			worksheet.write(row, 6, u'TKPH', header_wrap)
			worksheet.set_column(6, 6, 10)
			worksheet.write(row, 7, u'Суурьлагдсан техник', header_wrap)
			worksheet.set_column(7, 7, 12)
			worksheet.write(row, 8, u'Парк дугаар', header_wrap)
			worksheet.write(row, 9, u'Байрлал', header_wrap)
			worksheet.write(row, 10, u'Суурьлуулсан огноо', header_wrap)
			worksheet.write(row, 11, u'Суурьлуулах үеийн мото цаг', header_wrap)
			worksheet.write(row, 12, u'Суурьлуулах үеийн КМ', header_wrap)
			worksheet.write(row, 13, u'Одоогийн Мото цаг', header_wrap)
			worksheet.write(row, 14, u'Одоогийн КМ', header_wrap)
			worksheet.write(row, 15, u'Норм хээний гүн', header_wrap)
			worksheet.write(row, 16, u'Одоогийн хээний гүн', header_wrap)
			worksheet.write(row, 17, u'Хээний элэгдлийн хувь', header_wrap)
			worksheet.write(row, 18, u'Төлөв', header_wrap)
			worksheet.set_column(7, 18, 11)
			worksheet.freeze_panes(2, 4)
			# DATA зурах
			row = 2
			number = 1
			for tire in tires:
				current_date =self.env['tire.used.history'].search([('technic_id','=',tire.current_technic_id.id),('position','=',tire.current_position)], limit=1)

				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, tire.serial_number, contest_center)
				worksheet.write(row, 2, tire.brand_id.name, contest_center)
				worksheet.write(row, 3, tire.norm_tire_size, contest_center)
				worksheet.write(row, 4, tire.tra_code, contest_center)
				worksheet.write(row, 5, tire.tread_type, contest_center)
				worksheet.write(row, 6, tire.tkph, contest_center)
				worksheet.write(row, 7, tire.current_technic_id.model_id.name, contest_left)
				worksheet.write(row, 8, tire.current_technic_id.park_number, contest_center)
				worksheet.write(row, 9, tire.current_position, contest_right)
				line = self.env['technic.tire.line'].search([
					('technic_id','=',tire.current_technic_id.id),
					('tire_id','=',tire.id)], limit=1)
				worksheet.write(row, 10, current_date.date.strftime("%Y-%m-%d") or '', contest_center)
				worksheet.write(row, 11, line.odometer_value, contest_right)
				worksheet.write(row, 12, line.odometer_km, contest_right)
				worksheet.write(row, 13, tire.total_moto_hour, contest_right)
				worksheet.write(row, 14, tire.total_km, contest_right)
				worksheet.write(row, 15, tire.norm_tread_deep, contest_right)
				worksheet.write(row, 16, tire.tread_current_deep, contest_right)
				worksheet.write(row, 17, tire.tread_depreciation_percent, contest_right)
				worksheet.write(row, 18, tire.state, contest_center)
				row += 1
				number += 1
				#
			# SHEET 2
			# Шилжүүлгийн тайлан
			worksheet_2 = workbook.add_worksheet(u'Шилжүүлж угсарсан дугуй')
			worksheet_2.set_zoom(80)
			worksheet_2.write(0,2, u"Шилжүүлж угсарсан дугуйн тайлан", h1)
			worksheet_2.merge_range(0,4,0,6, u"Огноо: %s -> %s" % (self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d')), contest_center)

			# TABLE HEADER
			row = 1
			worksheet_2.set_row(1, 25)
			worksheet_2.write(row, 0, u"№", header)
			worksheet_2.set_column(0, 0, 4)
			worksheet_2.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet_2.set_column(1, 1, 20)
			worksheet_2.write(row, 2, u"Бренд", header_wrap)
			worksheet_2.set_column(2, 2, 15)
			worksheet_2.write(row, 3, u"Хэмжээ", header_wrap)
			worksheet_2.set_column(3, 3, 18)
			worksheet_2.write(row, 4, u'TRA code', header_wrap)
			worksheet_2.set_column(4, 4, 20)
			worksheet_2.write(row, 5, u'Хээний төрөл', header_wrap)
			worksheet_2.set_column(5, 5, 12)
			worksheet_2.write(row, 6, u'TKPH', header_wrap)
			worksheet_2.set_column(6, 6, 10)

			# SHEET 3
			# Ашиглалтаас гарсан тайлан
			worksheet_3 = workbook.add_worksheet(u'Ашиглалтаас гарсан дугуй')
			worksheet_3.set_zoom(80)
			worksheet_3.write(0,2, u"Ашиглалтаас гарсан дугуйн тайлан", h1)
			worksheet_3.merge_range(0,4,0,6, u"Огноо: %s -> %s" % (self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d')), contest_center)

			# TABLE HEADER
			row = 1
			worksheet_3.set_row(1, 25)
			worksheet_3.write(row, 0, u"№", header)
			worksheet_3.set_column(0, 0, 4)
			worksheet_3.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet_3.set_column(1, 1, 20)
			worksheet_3.write(row, 2, u"Бренд", header_wrap)
			worksheet_3.set_column(2, 2, 15)
			worksheet_3.write(row, 3, u"Хэмжээ", header_wrap)
			worksheet_3.set_column(3, 3, 18)
			worksheet_3.write(row, 4, u'TRA code', header_wrap)
			worksheet_3.set_column(4, 4, 20)
			worksheet_3.write(row, 5, u'Хээний төрөл', header_wrap)
			worksheet_3.set_column(5, 5, 12)
			worksheet_3.write(row, 6, u'TKPH', header_wrap)
			worksheet_3.set_column(6, 6, 10)

			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}

	def tire_detailed_history_report(self):
		if self.date_start and self.date_end:
			tires = self.tire_ids
			if not self.tire_ids:
				tires = self.env['technic.tire'].search([], order='brand_id, model_id, name')
			if not tires:
				raise UserError(_(u'Бичлэг олдсонгүй!'))

			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'tire_history_report.xlsx'

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

			header_wrap_sub = workbook.add_format({'bold': 1})
			header_wrap_sub.set_text_wrap()
			header_wrap_sub.set_font_size(9)
			header_wrap_sub.set_align('center')
			header_wrap_sub.set_align('vcenter')
			header_wrap_sub.set_border(style=1)
			header_wrap_sub.set_bg_color('#f5cc87')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_warning = workbook.add_format()
			contest_warning.set_text_wrap()
			contest_warning.set_font_size(9)
			contest_warning.set_align('left')
			contest_warning.set_align('vcenter')
			contest_warning.set_border(style=1)
			contest_warning.set_bg_color('#FCD5CC')

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

			worksheet = workbook.add_worksheet(u'Tire detailed report')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"Дугуйн түүхийг харуулах тайлан", h1)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"Брэнд", header)
			worksheet.set_column(0, 0, 15)
			worksheet.write(row, 1, u"Дугуй", header_wrap)
			worksheet.set_column(1, 1, 20)
			worksheet.write(row, 2, u"Төлөв", header_wrap)
			worksheet.set_column(2, 2, 13)
			worksheet.write(row, 3, u"Түүх", header_wrap)
			worksheet.set_column(3, 3, 20)
			worksheet.freeze_panes(2, 4)
			# DATA зурах
			row = 2
			col_max = 0
			number = 1
			for tire in tires:
				info = '%s\n\nХэмжээ: %s\nНийт гүйлт: %d\nНийт КМ: %d\nЭлэгдэл: %d\nХадгалагдсан цаг: %d' % (tire.display_name, tire.norm_tire_size, tire.total_moto_hour, tire.total_km, tire.tread_depreciation_percent_new, tire.stored_time)
				worksheet.merge_range(row, 0, row+5, 0, tire.brand_id.name, contest_center)
				worksheet.merge_range(row, 1, row+5, 1, info, contest_left)
				worksheet.merge_range(row, 2, row+5, 2, tire.state, contest_center)
				# Ашиглалтын түүх зурах
				worksheet.write(row, 3, 'Ашиглалтын түүх', contest_left)
				worksheet.write(row+1, 3, 'Тайлбар', contest_left)
				# Эхэлсэн
				worksheet.write(row, 4, tire.date_of_manufactured.strftime('%Y-%m-%d'), header_wrap_sub)
				worksheet.write(row+1, 4, "Үйлдвэрлэсэн", contest_left)
				worksheet.write(row, 5, tire.date_of_record.strftime('%Y-%m-%d'), header_wrap_sub)
				worksheet.write(row+1, 5, "Эхэлсэн огноо", contest_left)
				cc = 6
				historys = self.env['tire.used.history'].search([('tire_id','=',tire.id)], order='date')
				for hh in historys:
					worksheet.write(row, cc, hh.date.strftime('%Y-%m-%d'), header_wrap_sub)
					desc = ''
					if hh.description:
						desc = hh.description
					print(hh.description, desc, hh.position)
					worksheet.write(row+1, cc, desc+': %d'%hh.position, contest_left)
					info = '%s: %d\nБайрлал: %d' % (hh.technic_id.park_number, hh.technic_odometer, hh.position)
					worksheet.write_comment(row+1, cc, info)
					cc += 1
					col_max = cc if col_max < cc else col_max
				if tire.state == 'retired':
					worksheet.write_comment(row+1, cc-1, "Тайлбар: %s" % tire.retired_description)
				# Үзлэгийн түүх
				worksheet.write(row+2, 3, 'Үзлэгийн түүх', contest_left)
				worksheet.write(row+3, 3, 'Элэгдлийн хувь', contest_left)
				historys = self.env['tire.inspection.line'].search([
					('tire_id','=',tire.id),
					('state','=','done')], order='date')
				cc = 4
				for hh in historys:
					worksheet.write(row+2, cc, hh.date.strftime('%Y-%m-%d'), header_wrap_sub)
					worksheet.write(row+3, cc, hh.depreciation, contest_right)
					if hh.description:
						worksheet.write_comment(row+3, cc, hh.description)
					cc += 1
					col_max = cc if col_max < cc else col_max
				# Гүйлтийн түүх
				worksheet.write(row+4, 3, 'Гүйлтийн түүх', contest_left)
				worksheet.write(row+5, 3, 'Сард гүйсэн гүйлт', contest_left)
				query ="""
					SELECT
						to_char(tt.date, 'YYYY/MM') as dddd,
						sum(tt.increasing_odometer) as odo,
						sum(tt.increasing_km) as km
					FROM tire_depreciation_line as tt
					WHERE
						  tt.tire_id = %d
					GROUP BY dddd
					ORDER BY dddd
				""" % tire.id
				self.env.cr.execute(query)
				historys = self.env.cr.dictfetchall()
				cc = 4
				for hh in historys:
					worksheet.write(row+4, cc, hh['dddd'], header_wrap_sub)
					odometer = hh['odo'] if tire.odometer_unit == 'motoh' else hh['km']
					worksheet.write(row+5, cc, odometer, contest_right)
					cc += 1
					col_max = cc if col_max < cc else col_max
				# -===========================================================
				row += 6
			#
			worksheet.set_column(4, col_max, 11)
			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}

	# Техник дээр дугуйн түүхийг харуулах
	def tire_history_on_technic_report(self):
		if self.date_start:
			technics = self.technic_ids
			if not self.technic_ids:
				technics = self.env['technic.equipment'].search([
					('tire_line','!=',False)], order='report_order')
			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'tire_history_report_on_technic.xlsx'

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

			header_wrap_sub = workbook.add_format({'bold': 1})
			header_wrap_sub.set_text_wrap()
			header_wrap_sub.set_font_size(9)
			header_wrap_sub.set_align('center')
			header_wrap_sub.set_align('vcenter')
			header_wrap_sub.set_border(style=1)
			header_wrap_sub.set_bg_color('#f5cc87')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_warning = workbook.add_format()
			contest_warning.set_text_wrap()
			contest_warning.set_font_size(9)
			contest_warning.set_align('left')
			contest_warning.set_align('vcenter')
			contest_warning.set_border(style=1)
			contest_warning.set_bg_color('#FCD5CC')

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

			worksheet = workbook.add_worksheet(u'Tire report')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"Техник дээрх дугуйн түүхийг харуулах тайлан", h1)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"Техник", header)
			worksheet.write(row, 1, u"Дугуй", header_wrap)
			worksheet.set_column(0, 1, 20)
			worksheet.write(row, 2, u"Байрлал", header_wrap)
			worksheet.set_column(2, 2, 13)
			worksheet.write(row, 3, u"Түүх", header_wrap)
			worksheet.set_column(3, 3, 20)
			worksheet.freeze_panes(2, 4)
			# DATA зурах
			row = 2
			col_max = 0
			number = 1
			for tt in technics:
				r1 = len(tt.tire_line)*6-1
				custom_style = contest_left if tt.technic_setting_id.tire_counts == len(tt.tire_line) else contest_warning
				worksheet.merge_range(row, 0, row+r1, 0, tt.display_name, custom_style)
				for t_line in tt.tire_line:
					tire = t_line.tire_id
					info = '%s\n\nНийт гүйлт: %d\nНийт КМ: %d\nЭлэгдэл: %d' % (tire.display_name, tire.total_moto_hour, tire.total_km, tire.tread_depreciation_percent)
					worksheet.merge_range(row, 1, row+5, 1, info, contest_left)
					worksheet.merge_range(row, 2, row+5, 2, t_line.position, contest_center)
					# Ашиглалтын түүх зурах
					worksheet.write(row, 3, 'Ашиглалтын түүх', contest_left)
					worksheet.write(row+1, 3, 'Тайлбар', contest_left)
					# Эхэлсэн
					worksheet.write(row, 4, tire.date_of_manufactured.strftime('%Y-%m-%d'), header_wrap_sub)
					worksheet.write(row+1, 4, "Үйлдвэрлэсэн огноо", contest_left)
					worksheet.write(row, 5, tire.date_of_record.strftime('%Y-%m-%d'), header_wrap_sub)
					worksheet.write(row+1, 5, "Эхэлсэн огноо", contest_left)
					cc = 6
					historys = self.env['tire.used.history'].search([('tire_id','=',tire.id)], order='date')
					for hh in historys:
						worksheet.write(row, cc, hh.date.strftime('%Y-%m-%d'), header_wrap_sub)
						worksheet.write(row+1, cc, hh.description or '' +': %d'%hh.position or '', contest_left)
						info = '%s: %d\nБайрлал: %d' % (hh.technic_id.park_number, hh.technic_odometer, hh.position)
						worksheet.write_comment(row+1, cc, info)
						cc += 1
						col_max = cc if col_max < cc else col_max
					# Үзлэгийн түүх
					worksheet.write(row+2, 3, 'Үзлэгийн түүх', contest_left)
					worksheet.write(row+3, 3, 'Элэгдлийн хувь', contest_left)
					historys = self.env['tire.inspection.line'].search([
						('tire_id','=',tire.id),
						('state','=','done')], order='date')
					cc = 4
					for hh in historys:
						worksheet.write(row+2, cc, hh.date.strftime('%Y-%m-%d'), header_wrap_sub)
						worksheet.write(row+3, cc, hh.depreciation, contest_right)
						if hh.description:
							worksheet.write_comment(row+3, cc, hh.description)
						cc += 1
						col_max = cc if col_max < cc else col_max
					# Гүйлтийн түүх
					worksheet.write(row+4, 3, 'Гүйлтийн түүх', contest_left)
					worksheet.write(row+5, 3, 'Сард гүйсэн гүйлт', contest_left)
					query ="""
						SELECT
							to_char(tt.date, 'YYYY/MM') as dddd,
							sum(tt.increasing_odometer) as odo,
							sum(tt.increasing_km) as km
						FROM tire_depreciation_line as tt
						WHERE
							  tt.tire_id = %d
						GROUP BY dddd
						ORDER BY dddd
					""" % tire.id
					self.env.cr.execute(query)
					historys = self.env.cr.dictfetchall()
					cc = 4
					for hh in historys:
						worksheet.write(row+4, cc, hh['dddd'], header_wrap_sub)
						odometer = hh['odo'] if tire.odometer_unit == 'motoh' else hh['km']
						worksheet.write(row+5, cc, odometer, contest_right)
						cc += 1
						col_max = cc if col_max < cc else col_max
					# -===========================================================
					row += 6
				#
			worksheet.set_column(4, col_max, 11)

			# SHEET 2 - Тухайн техник дээр ажиллаж байсан дугуйнуудын мэдээлэл
			if self.technic_ids:
				worksheet_2 = workbook.add_worksheet(u'Tire report 2')
				worksheet_2.set_zoom(80)
				worksheet_2.write(0,2, u"Техник дээр ажиллаж байсан дугуйн мэдээлэл", h1)

				# TABLE HEADER
				row = 1
				worksheet_2.set_row(1, 25)
				worksheet_2.write(row, 0, u"Техник", header)
				worksheet_2.write(row, 1, u"Дугуй", header_wrap)
				worksheet_2.set_column(0, 1, 20)
				worksheet_2.write(row, 2, u"Төлөв", header_wrap)
				worksheet_2.set_column(2, 2, 13)
				worksheet_2.write(row, 3, u"Түүх", header_wrap)
				worksheet_2.set_column(3, 3, 20)
				worksheet_2.freeze_panes(2, 4)
				# DATA зурах
				row = 2
				col_max = 0
				number = 1
				for tt in self.technic_ids:
					r1 = row
					query = """
						SELECT
							ll.date as dddd,
							ll.tire_id as tire_id
						FROM tire_used_history as ll
						WHERE ll.technic_id = %d
						GROUP BY ll.date, ll.tire_id
						ORDER BY ll.date
					""" % tt.id
					self.env.cr.execute(query)
					result_tire_ids = self.env.cr.dictfetchall()
					for ll in result_tire_ids:
						tire = self.env['technic.tire'].browse(ll['tire_id'])
						info = '%s\n\nНийт гүйлт: %d\nНийт КМ: %d\nЭлэгдэл: %d' % (tire.display_name, tire.total_moto_hour, tire.total_km, tire.tread_depreciation_percent)
						worksheet_2.merge_range(row, 1, row+5, 1, info, contest_left)
						if tire.state == 'using':
							txt = '%s\n\n%s' % (tire.state, tire.current_technic_id.display_name)
							worksheet_2.merge_range(row, 2, row+5, 2, txt, contest_center)
						else:
							worksheet_2.merge_range(row, 2, row+5, 2, tire.state, contest_center)
						# Ашиглалтын түүх зурах
						worksheet_2.write(row, 3, 'Ашиглалтын түүх', contest_left)
						worksheet_2.write(row+1, 3, 'Тайлбар', contest_left)
						# Эхэлсэн
						worksheet_2.write(row, 4, tire.date_of_manufactured.strftime('%Y-%m-%d'), header_wrap_sub)
						worksheet_2.write(row+1, 4, "Үйлдвэрлэсэн огноо", contest_left)
						worksheet_2.write(row, 5, tire.date_of_record.strftime('%Y-%m-%d'), header_wrap_sub)
						worksheet_2.write(row+1, 5, "Эхэлсэн огноо", contest_left)
						cc = 6
						historys = self.env['tire.used.history'].search([('tire_id','=',tire.id)], order='date')
						for hh in historys:
							worksheet_2.write(row, cc, hh.date.strftime('%Y-%m-%d'), header_wrap_sub)
							worksheet_2.write(row+1, cc, hh.description, contest_left)
							info = '%s: %d\nБайрлал: %d' % (hh.technic_id.park_number, hh.technic_odometer, hh.position)
							worksheet_2.write_comment(row+1, cc, info)
							cc += 1
							col_max = cc if col_max < cc else col_max
						# Үзлэгийн түүх
						worksheet_2.write(row+2, 3, 'Үзлэгийн түүх', contest_left)
						worksheet_2.write(row+3, 3, 'Элэгдлийн хувь', contest_left)
						historys = self.env['tire.inspection.line'].search([
							('tire_id','=',tire.id),
							('parent_id.technic_id','=',tt.id),
							('state','=','done')], order='date')
						cc = 4
						for hh in historys:
							worksheet_2.write(row+2, cc, hh.date.strftime('%Y-%m-%d'), header_wrap_sub)
							worksheet_2.write(row+3, cc, hh.depreciation, contest_right)
							if hh.description:
								worksheet_2.write_comment(row+3, cc, hh.description)
							cc += 1
							col_max = cc if col_max < cc else col_max
						# Гүйлтийн түүх
						worksheet_2.write(row+4, 3, 'Гүйлтийн түүх', contest_left)
						worksheet_2.write(row+5, 3, 'Сард гүйсэн гүйлт', contest_left)
						query ="""
							SELECT
								to_char(tt.date, 'YYYY/MM') as dddd,
								sum(tt.increasing_odometer) as odo,
								sum(tt.increasing_km) as km
							FROM tire_depreciation_line as tt
							WHERE
								  tt.tire_id = %d and
								  tt.technic_id = %d
							GROUP BY dddd
							ORDER BY dddd
						""" % (tire.id, tt.id)
						self.env.cr.execute(query)
						historys = self.env.cr.dictfetchall()
						cc = 4
						for hh in historys:
							worksheet_2.write(row+4, cc, hh['dddd'], header_wrap_sub)
							odometer = hh['odo'] if tire.odometer_unit == 'motoh' else hh['km']
							worksheet_2.write(row+5, cc, odometer, contest_right)
							cc += 1
							col_max = cc if col_max < cc else col_max
						# -===========================================================
						row += 6
					#
					worksheet_2.merge_range(r1, 0, row-1, 0, tt.display_name, contest_left)
				worksheet_2.set_column(4, col_max, 11)

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

	def see_report(self):
		if self.date_start:
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup('mw_technic_equipment.technic_tire_pivot_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_equipment.technic_tire_pivot_report_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			domain = [('state','not in',['draft','retired'])]
			return {
				'name': ('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'technic.tire.pivot.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				# 'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
			}


	def export_report(self):
		if self.date_start:
			tires = self.env['technic.tire'].search([
				('state','not in',['draft','retired'])], order='current_technic_id, current_position, brand_id')
			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'tire_report_'+str(self.date_start)+'.xlsx'

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

			worksheet = workbook.add_worksheet(u'Tire report')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"Дугуйн тайлан", h1)
			worksheet.merge_range(0,4,0,6, u"Огноо: %s -> %s" % (self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d')), contest_center)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"Сериал дугаар", header_wrap)
			worksheet.set_column(1, 1, 20)
			worksheet.write(row, 2, u"Бренд", header_wrap)
			worksheet.set_column(2, 2, 15)
			worksheet.write(row, 3, u"Хэмжээ", header_wrap)
			worksheet.set_column(3, 3, 18)
			worksheet.write(row, 4, u'Парк дугаар', header_wrap)
			worksheet.set_column(4, 4, 20)
			worksheet.write(row, 5, u'Гүйцэтгэл', header_wrap)
			worksheet.set_column(5, 5, 12)
			worksheet.write(row, 6, u'Байрлал', header_wrap)
			worksheet.set_column(6, 6, 10)
			worksheet.write(row, 7, u'Эхлэлийн огноо', header_wrap)
			worksheet.set_column(7, 7, 12)
			worksheet.write(row, 8, u'Эхлэлийн мото цаг', header_wrap)
			worksheet.write(row, 9, u'Төлөв', header_wrap)
			worksheet.write(row, 10, u'Огноо', header_wrap)
			worksheet.write(row, 11, u'Одоогийн мото цаг', header_wrap)
			worksheet.write(row, 12, u'Нийт ажилласан мото цаг', header_wrap)
			worksheet.write(row, 13, u'Шинэ дугуйн хээний гүн', header_wrap)
			worksheet.write(row, 14, u'Одоо байгаа хээний гүн', header_wrap)
			worksheet.write(row, 15, u'Элэгдлийн хувь', header_wrap)
			worksheet.set_column(7, 15, 11)
			worksheet.freeze_panes(2, 4)
			# DATA зурах
			row = 2
			number = 1
			for tire in tires:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, tire.serial_number, contest_center)
				worksheet.write(row, 2, tire.brand_id.name, contest_center)
				worksheet.write(row, 3, tire.norm_tire_size, contest_center)
				worksheet.write(row, 4, tire.current_technic_id.program_code or '', contest_center)
				worksheet.write(row, 5, '', contest_center)
				worksheet.write(row, 6, tire.current_position or '', contest_center)
				worksheet.write(row, 7, tire.date_of_record, contest_center)
				line = self.env['tire.used.history'].search([('description','=','Installed'),('tire_id','=',tire.id)], limit=1)
				worksheet.write(row, 8, line.technic_odometer or 0, contest_center)
				worksheet.write(row, 9, tire.state, contest_center)
				worksheet.write(row, 10, str(datetime.now())[:10], contest_center)
				worksheet.write(row, 11, tire.current_technic_id.total_odometer, contest_center)
				worksheet.write(row, 12, (tire.current_technic_id.total_odometer or 0) - (line.technic_odometer or 0), contest_center)
				worksheet.write(row, 13, tire.norm_tread_deep, contest_center)
				worksheet.write(row, 14, tire.tread_current_deep, contest_center)
				worksheet.write(row, 15, tire.tread_depreciation_percent, contest_center)
				row += 1
				number += 1
				#

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


