# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardComponentReport(models.TransientModel):
	_name = "wizard.component.report"
	_description = "wizard component report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(string='Дуусах огноо', required=True)
	technic_id  = fields.Many2one('technic.equipment', string='Техник сонгох')
	technic_ids  = fields.Many2many('technic.equipment', string='Техникүүд сонгох')
	product_id = fields.Many2one('product.product', string='Компонент сонгох')
	product_ids = fields.Many2many('product.product', string='Компонентууд сонгох')
	technic_component_id = fields.Many2one('technic.component.part', string="Component_id")
	state = fields.Selection([
		('draft','Draft'),
		('new','New'),
		('using','Using'),
		('inactive','Inactive'),
		('repairing','Repairing'),
		('retired','Retired')], string='Төлөв')

	def export_report(self):

		components = []
		if self.state:
			if not self.technic_ids and not self.product_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('is_lv_component','=',False),
						('state','=',self.state),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
			elif self.technic_ids and not self.product_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('current_technic_id', 'in', self.technic_ids.ids),
						('is_lv_component','=',False),
						('state','=',self.state),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
			elif self.product_ids and not self.technic_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('product_id', 'in', self.product_ids.ids),
						('is_lv_component','=',False),
						('state','=',self.state),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
			elif self.product_ids and self.technic_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('current_technic_id', 'in', self.technic_ids.ids),
						('product_id', '=', self.product_id.id),
						('is_lv_component','=',False),
						('state','=',self.state),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
		else:
			if not self.technic_ids and not self.product_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('is_lv_component','=',False),
						('state','not in',['draft','retired']),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
			elif self.technic_ids and not self.product_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('current_technic_id', 'in', self.technic_ids.ids),
						('is_lv_component','=',False),
						('state','not in',['draft','retired']),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
			elif self.product_ids and not self.technic_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('product_id', 'in', self.product_ids.ids),
						('is_lv_component','=',False),
						('state','not in',['draft','retired']),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')
			elif self.product_ids and self.technic_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('current_technic_id', 'in', self.technic_ids.ids),
						('product_id', 'in', self.product_ids.ids),
						('is_lv_component','=',False),
						('state','not in',['draft','retired']),
						'|',('company_id','=',False),('company_id','child_of',[self.env.user.company_id.id])], order='report_order, program_code, current_technic_id, product_id')


		if components:


			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'component_report_'+str(self.date_start)+'.xlsx'

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

			worksheet = workbook.add_worksheet(u'Component report')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"Компонент тайлан", h1)
			worksheet.write(0,3, u"Огноо: "+str(self.date_start) + '-'+str(self.date_end), contest_center)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 25)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"Нэр", header_wrap)
			worksheet.set_column(1, 1, 30)
			worksheet.write(row, 2, u"Сериал дугаар", header_wrap)
			worksheet.set_column(2, 2, 15)
			worksheet.write(row, 3, u"Эд ангийн дугаар", header_wrap)
			worksheet.set_column(3, 3, 15)
			worksheet.write(row, 4, u"Нийт Odometer", header_wrap)
			worksheet.set_column(4, 4, 15)
			worksheet.write(row, 5, u"Төлөв", header_wrap)
			worksheet.set_column(5, 6, 12)
			worksheet.write(row, 6, u"Strategy", header_wrap)
			worksheet.write(row, 7, u'Одоогийн техник', header_wrap)
			worksheet.set_column(7, 7, 18)
			worksheet.write(row, 8, u'Ажилласан мото/цаг', header_wrap)
			worksheet.set_column(8, 8, 12)
			worksheet.write(row, 9, u'Засварласан огноо', header_wrap)
			worksheet.set_column(9, 9, 12)
			worksheet.freeze_panes(2, 4)
			# DATA зурах
			before_technic_cols = []
			row = 2
			number = 1
			for component in components:
				before_col = 10
				first = True
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, component.name, contest_left)
				worksheet.write(row, 2, component.serial_number, contest_left)
				worksheet.write(row, 3, component.real_part_number, contest_left)
				worksheet.write(row, 4, component.total_odometer, contest_right)
				worksheet.write(row, 5, component.state, contest_center)
				worksheet.write(row, 6, component.last_maintenance, contest_center)

				worksheet.write(row, 9, component.last_date.strftime("%Y-%m-%d"), contest_center)
				# Өмнөх техникийн мэдээлэл зурах
				before_datas = component._get_used_technics()
				if before_datas['names']:
					for i in range(0,len(before_datas['names'])):
						if before_col not in before_technic_cols:
							worksheet.write(1, before_col, u'Өмнөх техник', header_wrap)
							worksheet.write(1, before_col+1, u'Ажилласан мото/цаг', header_wrap)
							worksheet.set_column(before_col, before_col+1, 12)
							before_technic_cols.append(before_col)

						if component.current_technic_id and component.current_technic_id.park_number == before_datas['park_num'][i] and first:
							# Одоогийн техник
							worksheet.write(row, 7, component.current_technic_id.park_number or '', contest_center)
							worksheet.write(row, 8, before_datas['datas'][i] or 0, contest_right)
						else:
							worksheet.write(row, before_col, before_datas['park_num'][i], contest_center)
							worksheet.write(row, before_col+1, before_datas['datas'][i] or 0, contest_right)
							before_col += 2
						first = False

				row += 1
				number += 1
				#

			# LV component

			components = []
			if not self.technic_ids and not self.product_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('is_lv_component','=',True),
						('state','not in',['draft','retired'])], order='report_order, program_code, current_technic_id, product_id')
			elif self.technic_ids and not self.product_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('current_technic_id', 'in', self.technic_ids.ids),
						('is_lv_component','=',True),
						('state','not in',['draft','retired'])], order='report_order, program_code, current_technic_id, product_id')
			elif self.product_ids and not self.technic_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('product_id', 'in', self.product_ids.ids),
						('is_lv_component','=',True),
						('state','not in',['draft','retired'])], order='report_order, program_code, current_technic_id, product_id')
			elif self.product_ids and self.technic_ids:
				components = self.env['technic.component.part'].search([
						('date_of_set', '>=', self.date_start),
						('date_of_set', '<=', self.date_end),
						('current_technic_id', 'in', self.technic_ids.ids),
						('product_id', 'in', self.product_ids.ids),
						('is_lv_component','=',True),
						('state','not in',['draft','retired'])], order='report_order, program_code, current_technic_id, product_id')

			if components:
				worksheet_2 = workbook.add_worksheet(u'LV Component report')
				worksheet_2.set_zoom(80)
				worksheet_2.write(0,2, u"LV Компонент тайлан", h1)
				worksheet_2.write(0,4, u"Огноо: "+str(self.date_start), contest_center)

				# TABLE HEADER
				row = 1
				worksheet_2.set_row(1, 25)
				worksheet_2.write(row, 0, u"№", header)
				worksheet_2.set_column(0, 0, 4)
				worksheet_2.write(row, 1, u"Нэр Сериал дугаар", header_wrap)
				worksheet_2.set_column(1, 1, 30)
				worksheet_2.write(row, 2, u"Нийт Odometer", header_wrap)
				worksheet_2.set_column(2, 2, 15)
				worksheet_2.write(row, 3, u"Төлөв", header_wrap)
				worksheet_2.set_column(3, 4, 12)
				worksheet_2.write(row, 4, u"Strategy", header_wrap)
				worksheet_2.write(row, 5, u'Одоогийн техник', header_wrap)
				worksheet_2.set_column(5, 5, 18)
				worksheet_2.write(row, 6, u'Ажилласан мото/цаг', header_wrap)
				worksheet_2.set_column(6, 6, 12)
				worksheet_2.write(row, 7, u'Засварласан огноо', header_wrap)
				worksheet_2.set_column(7, 7, 12)
				worksheet_2.freeze_panes(2, 4)

				before_technic_cols = []
				row = 2
				number = 1
				for component in components:
					before_col = 8
					first = True
					worksheet_2.write(row, 0, number, number_right)
					worksheet_2.write(row, 1, component.name, contest_left)
					worksheet_2.write(row, 2, component.total_odometer, contest_right)
					worksheet_2.write(row, 3, component.state, contest_center)
					worksheet_2.write(row, 4, component.last_maintenance, contest_center)

					worksheet_2.write(row, 7, component.last_date, contest_center)
					# Өмнөх техникийн мэдээлэл зурах
					before_datas = component._get_used_technics()
					if before_datas['names']:
						for i in range(0,len(before_datas['names'])):
							if before_col not in before_technic_cols:
								worksheet_2.write(1, before_col, u'Өмнөх техник', header_wrap)
								worksheet_2.write(1, before_col+1, u'Ажилласан мото/цаг', header_wrap)
								worksheet_2.set_column(before_col, before_col+1, 12)
								before_technic_cols.append(before_col)

							if component.current_technic_id and component.current_technic_id.program_code == before_datas['names'][i] and first:
								# Одоогийн техник
								worksheet_2.write(row, 5, component.current_technic_id.program_code or '', contest_center)
								worksheet_2.write(row, 6, before_datas['datas'][i] or 0, contest_right)
							else:
								worksheet_2.write(row, before_col, before_datas['names'][i], contest_center)
								worksheet_2.write(row, before_col+1, before_datas['datas'][i] or 0, contest_right)
								before_col += 2
							first = False

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


