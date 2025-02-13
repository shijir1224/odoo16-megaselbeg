# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardEquipmentMasterSheetReport(models.TransientModel):
	_name = "wizard.equipment.master.sheet.report"  
	_description = "wizard equipment master sheet report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)

	
	def export_report(self):
		if self.date_start:
			technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('owner_type','=','own_asset'),
				('is_tbb_report','=',True)
				], order='report_order, program_code')
			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'equipment_master_sheet_'+str(self.date_start)+'.xlsx'

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

			worksheet = workbook.add_worksheet(u'Equipment master sheet')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"MASTER SHEET тайлан", h1)
			worksheet.write(0,4, u"Огноо: "+str(self.date_start), contest_center)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.merge_range(row, 1, row+1, 1, u"TYPE", header_wrap)
			worksheet.set_column(1, 1, 15)
			worksheet.set_column(2, 25, 15)
			worksheet.merge_range(row, 2,row+1, 2, u"MASHINE BRAND", header_wrap)
			worksheet.merge_range(row, 3, row+1, 3, u"MODEL", header_wrap)
			worksheet.merge_range(row, 4, row+1, 4, u'FLEET #', header_wrap)
			worksheet.merge_range(row, 5,row+1, 5, u'SERIAL NUMBER', header_wrap)

			worksheet.merge_range(row, 6, row, 8,u'ENGINE', header_wrap)
			worksheet.write(row+1, 6, u"ENGINE BRAND", header_wrap)
			worksheet.write(row+1, 7, u"ENGINE MODEL", header_wrap)
			worksheet.write(row+1, 8, u"ENGINE SN", header_wrap)
			worksheet.merge_range(row, 9, row+1, 9, u"TRANSMISSION SN", header_wrap)

			worksheet.merge_range(row, 10, row+1, 10, u"GENERATOR, ALTERNATOR SN", header_wrap)
			
			worksheet.merge_range(row, 11, row, 12,u'WHEEL MOTOR SN', header_wrap)
			worksheet.write(row+1, 11, u"LHS", header_wrap)
			worksheet.write(row+1, 12, u"RHS", header_wrap)

			worksheet.merge_range(row, 13, row+1, 13,u'ENGINE POWER', header_wrap)
			worksheet.merge_range(row, 14, row+1, 14, u"FUEL TANK CAPACITY/L", header_wrap)
			worksheet.merge_range(row, 15, row+1, 15, u"OPERATING WEIGHT/kg", header_wrap)
			worksheet.merge_range(row, 16, row+1, 16, u"Payload capacity tonn/bucket m3", header_wrap)
			worksheet.merge_range(row, 17, row+1, 17, u"LENGTH", header_wrap)
			worksheet.merge_range(row, 18, row+1, 18, u"WIDTH", header_wrap)
			worksheet.merge_range(row, 19, row+1, 19, u"HEIGHT", header_wrap)
			worksheet.merge_range(row, 20, row+1, 20, u"Үйлдвэрлэсэн он", header_wrap)
			worksheet.merge_range(row, 21, row+1, 21, u"Ашиглаж эхэлсэн огноо", header_wrap)
			worksheet.merge_range(row, 22, row+1, 22, u"Улсын дугаар", header_wrap)
			worksheet.freeze_panes(3, 6)
			worksheet.set_zoom(75)
			# DATA зурах
			row = 3
			number = 1
			for tt in technics:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, tt.technic_type, contest_left)
				worksheet.write(row, 2, tt.model_id.brand_id.name, contest_center)
				worksheet.write(row, 3, tt.model_id.name, contest_center)
				worksheet.write(row, 4, tt.program_code, contest_center)
				worksheet.write(row, 5, tt.vin_number, contest_center)
				worksheet.write(row, 6, tt.technic_setting_id.engine_type, contest_center)
				worksheet.write(row, 7, tt.technic_setting_id.engine_mark, contest_center)
				# Компонент мэдээлэл авах
				temp_dict = {}
				for ll in tt.component_part_line:
					if ll.component_type:
						temp_dict[ll.component_type] = ll.serial_number
				worksheet.write(row, 8, temp_dict['engine'] if 'engine' in temp_dict else '', contest_center)
				worksheet.write(row, 9, temp_dict['transmission'] if 'transmission' in temp_dict else '', contest_center)
				worksheet.write(row, 10, temp_dict['generator_alternator'] if 'generator_alternator' in temp_dict else '', contest_center)
				worksheet.write(row, 11, temp_dict['wheel_motor_l'] if 'wheel_motor_l' in temp_dict else '', contest_center)
				worksheet.write(row, 12, temp_dict['wheel_motor_r'] if 'wheel_motor_r' in temp_dict else '', contest_center)
				worksheet.write(row, 13, tt.technic_setting_id.engine_capacity, contest_center)
				worksheet.write(row, 14, tt.technic_setting_id.fuel_tank_capacity, contest_center)
				worksheet.write(row, 15, tt.technic_setting_id.operating_weight, contest_center)
				worksheet.write(row, 16, tt.technic_setting_id.carrying_tonnage, contest_center)
				worksheet.write(row, 17, tt.technic_setting_id.body_length, contest_center)
				worksheet.write(row, 18, tt.technic_setting_id.body_width, contest_center)
				worksheet.write(row, 19, tt.technic_setting_id.body_height, contest_center)
				worksheet.write(row, 20, tt.manufactured_date, contest_center)
				worksheet.write(row, 21, tt.start_date, contest_center)
				worksheet.write(row, 22, tt.state_number, contest_center)
				
				row += 1
				number += 1

			# LV ------------==============
			lv_technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('owner_type','=','own_asset'),
				('is_tbb_report','=',False)
				], order='report_order, program_code')
			if lv_technics:
				worksheet_2 = workbook.add_worksheet(u'LV Equipment master')
				worksheet_2.set_zoom(80)
				worksheet_2.write(0,2, u"MASTER SHEET LV", h1)
				worksheet_2.write(0,4, u"Огноо: "+str(self.date_start), contest_center)

				# TABLE HEADER
				row = 1
				worksheet_2.set_row(1, 25)
				worksheet_2.merge_range(row, 0, row+1, 0, u"№", header)
				worksheet_2.set_column(0, 0, 4)
				worksheet_2.merge_range(row, 1, row+1, 1, u"TYPE", header_wrap)
				worksheet_2.set_column(1, 1, 15)
				worksheet_2.set_column(2, 25, 15)
				worksheet_2.merge_range(row, 2,row+1, 2, u"MASHINE BRAND", header_wrap)
				worksheet_2.merge_range(row, 3, row+1, 3, u"MODEL", header_wrap)
				worksheet_2.merge_range(row, 4, row+1, 4, u'FLEET #', header_wrap)
				worksheet_2.merge_range(row, 5,row+1, 5, u'SERIAL NUMBER', header_wrap)

				worksheet_2.merge_range(row, 6, row, 8,u'ENGINE', header_wrap)
				worksheet_2.write(row+1, 6, u"ENGINE BRAND", header_wrap)
				worksheet_2.write(row+1, 7, u"ENGINE MODEL", header_wrap)
				worksheet_2.write(row+1, 8, u"ENGINE SN", header_wrap)
				worksheet_2.merge_range(row, 9, row+1, 9, u"TRANSMISSION SN", header_wrap)

				worksheet_2.merge_range(row, 10, row+1, 10, u"GENERATOR, ALTERNATOR SN", header_wrap)
				
				worksheet_2.merge_range(row, 11, row, 12,u'WHEEL MOTOR SN', header_wrap)
				worksheet_2.write(row+1, 11, u"LHS", header_wrap)
				worksheet_2.write(row+1, 12, u"RHS", header_wrap)

				worksheet_2.merge_range(row, 13, row+1, 13,u'ENGINE POWER', header_wrap)
				worksheet_2.merge_range(row, 14, row+1, 14, u"FUEL TANK CAPACITY/L", header_wrap)
				worksheet_2.merge_range(row, 15, row+1, 15, u"OPERATING WEIGHT/kg", header_wrap)
				worksheet_2.merge_range(row, 16, row+1, 16, u"Payload capacity tonn/bucket m3", header_wrap)
				worksheet_2.merge_range(row, 17, row+1, 17, u"LENGTH", header_wrap)
				worksheet_2.merge_range(row, 18, row+1, 18, u"WIDTH", header_wrap)
				worksheet_2.merge_range(row, 19, row+1, 19, u"HEIGHT", header_wrap)
				worksheet_2.merge_range(row, 20, row+1, 20, u"Үйлдвэрлэсэн он", header_wrap)
				worksheet_2.merge_range(row, 21, row+1, 21, u"Ашиглаж эхэлсэн огноо", header_wrap)
				worksheet_2.merge_range(row, 22, row+1, 22, u"Улсын дугаар", header_wrap)
				worksheet_2.freeze_panes(3, 6)
				worksheet_2.set_zoom(75)
				# DATA зурах
				row = 3
				number = 1
				for tt in lv_technics:
					worksheet_2.write(row, 0, number, number_right)
					worksheet_2.write(row, 1, tt.technic_type, contest_left)
					worksheet_2.write(row, 2, tt.model_id.brand_id.name, contest_center)
					worksheet_2.write(row, 3, tt.model_id.name, contest_center)
					worksheet_2.write(row, 4, tt.program_code, contest_center)
					worksheet_2.write(row, 5, tt.vin_number, contest_center)
					worksheet_2.write(row, 6, tt.technic_setting_id.engine_type, contest_center)
					worksheet_2.write(row, 7, tt.technic_setting_id.engine_mark, contest_center)
					# Компонент мэдээлэл авах
					temp_dict = {}
					for ll in tt.component_part_line:
						if ll.component_type:
							temp_dict[ll.component_type] = ll.serial_number
					worksheet_2.write(row, 8, temp_dict['engine'] if 'engine' in temp_dict else '', contest_center)
					worksheet_2.write(row, 9, temp_dict['transmission'] if 'transmission' in temp_dict else '', contest_center)
					worksheet_2.write(row, 10, temp_dict['generator_alternator'] if 'generator_alternator' in temp_dict else '', contest_center)
					worksheet_2.write(row, 11, temp_dict['wheel_motor_l'] if 'wheel_motor_l' in temp_dict else '', contest_center)
					worksheet_2.write(row, 12, temp_dict['wheel_motor_r'] if 'wheel_motor_r' in temp_dict else '', contest_center)
					worksheet_2.write(row, 13, tt.technic_setting_id.engine_capacity, contest_center)
					worksheet_2.write(row, 14, tt.technic_setting_id.fuel_tank_capacity, contest_center)
					worksheet_2.write(row, 15, tt.technic_setting_id.operating_weight, contest_center)
					worksheet_2.write(row, 16, tt.technic_setting_id.carrying_tonnage, contest_center)
					worksheet_2.write(row, 17, tt.technic_setting_id.body_length, contest_center)
					worksheet_2.write(row, 18, tt.technic_setting_id.body_width, contest_center)
					worksheet_2.write(row, 19, tt.technic_setting_id.body_height, contest_center)
					worksheet_2.write(row, 20, tt.manufactured_date, contest_center)
					worksheet_2.write(row, 21, tt.start_date, contest_center)
					worksheet_2.write(row, 22, tt.state_number, contest_center)
					
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


