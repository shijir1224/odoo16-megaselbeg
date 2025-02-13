# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardEquipmentFiresystemReport(models.TransientModel):
	_name = "wizard.equipment.firesystem.report"  
	_description = "wizard equipment firesystem report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)

	
	def export_report(self):
		if self.date_start:
			technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('owner_type','=','own_asset'),
				('with_fire_system','=',True)
				], order='report_order, program_code')
			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'equipment_firesystem_'+str(self.date_start)+'.xlsx'

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

			worksheet = workbook.add_worksheet(u'Equipment firesystem report')
			worksheet.set_zoom(100)
			worksheet.write(0,2, u"Firesystem тайлан", h1)
			worksheet.write(0,4, u"Огноо: "+str(self.date_start), contest_center)

			# TABLE HEADER
			row = 1
			worksheet.set_row(row, 30)
			worksheet.write(row, 0, u"№", header_wrap)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"ПАРК №", header_wrap)
			worksheet.set_column(1, 9, 15)
			worksheet.write(row, 2, u"MODEL", header_wrap)
			worksheet.write(row, 3, u"Галын системийн төрөл", header_wrap)
			worksheet.write(row, 4, u"Сүүлд хийсэн үйлчилгээний мэдээ", header_wrap)
			worksheet.write(row, 5, u"Төлөв", header_wrap)
			worksheet.write(row, 6, u"Засвар үйлчилгээний давтамж", header_wrap)
			worksheet.write(row, 7, u"Дараагийн үйлчилгээ хийх огноо", header_wrap)
			worksheet.freeze_panes(2, 0)
			# DATA зурах
			row = 2
			number = 1
			for tt in technics:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, tt.program_code, contest_center)
				worksheet.write(row, 2, tt.model_id.name, contest_left)
				worksheet.write(row, 3, tt.fire_system_type, contest_center)
				worksheet.write(row, 4, tt.fire_system_last_date, contest_center)
				worksheet.write(row, 5, tt.fire_system_state, contest_center)
				worksheet.write(row, 6, str(tt.fire_system_period)+u' сар', contest_right)
				worksheet.write(row, 7, tt.fire_system_next_date, contest_center)
				row += 1
				number += 1
			# ========================================
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


