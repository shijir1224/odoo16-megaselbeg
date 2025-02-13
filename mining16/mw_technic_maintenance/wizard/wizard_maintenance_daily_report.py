# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import collections
from calendar import monthrange

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardMaintenanceDailyReport(models.TransientModel):
	_name = "wizard.maintenance.daily.report"  
	_description = "wizard.maintenance.daily.report"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-%d'))
	include_not_closed = fields.Boolean(string=u'Дуусаагүй ажлыг оруулах', default=True)
	include_call = fields.Boolean(string=u'Дуудлага оруулах эсэх', default=False)
	include_waiting_parts = fields.Boolean(string=u'Wainting parts оруулах эсэх', default=False)
	
	def export_report(self):

		if self.date_start:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'daily report '+self.date_start.strftime("%Y-%m-%d")+'.xlsx'

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

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(9)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_left_desc = workbook.add_format()
			contest_left_desc.set_text_wrap()
			contest_left_desc.set_font_size(9)
			contest_left_desc.set_align('left')
			contest_left_desc.set_align('vcenter')
			contest_left_desc.set_border(style=1)

			contest_left_desc_night = workbook.add_format()
			contest_left_desc_night.set_text_wrap()
			contest_left_desc_night.set_font_size(9)
			contest_left_desc_night.set_align('left')
			contest_left_desc_night.set_align('vcenter')
			contest_left_desc_night.set_border(style=1)
			contest_left_desc_night.set_bg_color('#C0C0C0')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			worksheet = workbook.add_worksheet(u'MAINTENANCE DAILY REPORT')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"MAINTENANCE DAILY: "+datetime.strftime(self.date_start, '%Y-%m-%d'), h1)

			# TABLE HEADER
			row = 1
			worksheet.set_row(1, 30)
			worksheet.write(row, 0, u'№', header_wrap)
			worksheet.set_column(0, 0, 3)
			worksheet.write(row, 1, u'Date', header_wrap)
			worksheet.set_column(2, 2, 10)
			worksheet.write(row, 2, u'Work Order', header_wrap)
			worksheet.set_column(2, 2, 12)
			worksheet.write(row, 3, u'Equipment', header_wrap)
			worksheet.set_column(3, 3, 28)
			worksheet.write(row, 4, u'Equipment description', header_wrap)
			worksheet.write(row, 5, u'Type', header_wrap)
			worksheet.set_column(5, 5, 10)
			worksheet.write(row, 6, u'Ээлж', header_wrap)
			worksheet.set_column(6, 6, 8)
			worksheet.write(row, 7, u'Description', header_wrap)
			worksheet.set_column(7, 7, 70)
			worksheet.write(row, 8, u'Status', header_wrap)
			worksheet.set_column(8, 8, 8)
			worksheet.write(row, 9, u'Priority', header_wrap)
			worksheet.write(row, 10, u'Duration', header_wrap)
			worksheet.write(row, 11, u'Man power', header_wrap)
			worksheet.write(row, 12, u'M/hr', header_wrap)
			worksheet.set_column(9, 12, 5)
			worksheet.write(row, 13, u'Shift Foreman', header_wrap)
			worksheet.set_column(13, 13, 15)

			state_dict = {
				'open': 'open',
				'reopen': 'reopen',
				'analysing': 'analysing',
				'waiting_part': 'waiting_issue',
				'ordered_part': 'waiting_part',
				'waiting_labour': 'waiting_labour',
				'ready': 'ready',
				'processing': 'processing',
				'done': 'done',
				'closed': 'closed',
			}

			# 1. Үзлэгийн хуваариас автоматоор үүссэн WO ууд 
			wos = self.env['maintenance.workorder'].search([
				('date_required','=',self.date_start),
				('state','not in',['draft','cancelled','ordered_part','waiting_labour']),
				('maintenance_type','=','daily_works'),
				('origin','in',['daily_inspection','daily_lubrication',
								'daily_engine_inspection','daily_tire_inspection'])], order='name, origin')

			row = 2
			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 13, u"Техникийн өдөр тутмын үзлэг", sub_total)
			row += 1
			number = 1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				temp_style = contest_left_desc
				if line.shift == 'night':
					temp_style = contest_left_desc_night
				worksheet.write(row, 3, line.technic_id.name or '', temp_style)
				worksheet.write(row, 4, line.technic_id.program_code, temp_style)
				worksheet.write(row, 5, line.maintenance_type, temp_style)
				worksheet.write(row, 6, line.shift, temp_style)
				worksheet.write(row, 7, line.description, temp_style)
				worksheet.write(row, 8, state_dict[line.state], contest_center)
				worksheet.write(row, 9, line.priority, contest_center)
				worksheet.write(row, 10, line.planned_time, contest_center)
				worksheet.write(row, 11, line.planned_mans, contest_center)
				worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
				worksheet.write(row, 13, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

			# 2. Өдөр тутмын гагнуур, токерын ажлууд 
			wos = self.env['maintenance.workorder'].search([
				('date_required','=',self.date_start),
				('state','not in',['draft','cancelled','ordered_part','waiting_labour']),
				('origin','in',['daily_lather_job','daily_welding_job','crane_job'])], order='name')

			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 13, u"Welding Job and Lather Job", sub_total)
			row += 1
			number = 1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				temp_style = contest_left_desc
				if line.shift == 'night':
					temp_style = contest_left_desc_night
				worksheet.write(row, 3, line.technic_id.name or '', temp_style)
				worksheet.write(row, 4, line.technic_id.program_code, temp_style)
				worksheet.write(row, 5, line.maintenance_type, temp_style)
				worksheet.write(row, 6, line.shift, temp_style)
				worksheet.write(row, 7, line.description, temp_style)
				worksheet.write(row, 8, state_dict[line.state], contest_center)
				worksheet.write(row, 9, line.priority, contest_center)
				worksheet.write(row, 10, line.planned_time, contest_center)
				worksheet.write(row, 11, line.planned_mans, contest_center)
				worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
				worksheet.write(row, 13, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

			# 3. LV нүүдийн засвар
			wos = self.env['maintenance.workorder'].search([
				('date_required','=',self.date_start),
				('technic_id','!=',False),
				('technic_id.technic_type','in',['service_car','mechanizm','transportation_vehicle','equipment']),
				('state','not in',['draft','cancelled','ordered_part','waiting_labour']),
				('origin','not in',['daily_welding_job','daily_lather_job'])], order='name')

			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 13, u"LV засварууд", sub_total)
			row += 1
			number = 1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				temp_style = contest_left_desc
				if line.shift == 'night':
					temp_style = contest_left_desc_night
				worksheet.write(row, 3, line.technic_id.name or '', temp_style)
				worksheet.write(row, 4, line.technic_id.program_code, temp_style)
				worksheet.write(row, 5, line.maintenance_type, temp_style)
				worksheet.write(row, 6, line.shift, temp_style)
				worksheet.write(row, 7, line.description, temp_style)
				worksheet.write(row, 8, state_dict[line.state], contest_center)
				worksheet.write(row, 9, line.priority, contest_center)
				worksheet.write(row, 10, line.planned_time, contest_center)
				worksheet.write(row, 11, line.planned_mans, contest_center)
				worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
				worksheet.write(row, 13, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

			# 4. Дуусаагүй WO ууд, Өмнөх 
			if self.include_not_closed:
				wos = self.env['maintenance.workorder'].search([
					('date_required','<',self.date_start),
					('state','not in',['draft','cancelled','closed','done','ordered_part','waiting_labour'])], order='name')

				worksheet.write(row, 0, "#", sub_total)
				worksheet.merge_range(row, 1, row, 13, u"Дуусаагүй ажлууд", sub_total)
				row += 1
				number = 1
				for line in wos:
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 1, line.date_required, contest_center)
					worksheet.write(row, 2, line.name, contest_center)
					temp_style = contest_left_desc
					if line.shift == 'night':
						temp_style = contest_left_desc_night
					worksheet.write(row, 3, line.technic_id.name or '', temp_style)
					worksheet.write(row, 4, line.technic_id.program_code, temp_style)
					worksheet.write(row, 5, line.maintenance_type, temp_style)
					worksheet.write(row, 6, line.shift, temp_style)
					worksheet.write(row, 7, line.description, temp_style)
					worksheet.write(row, 8, state_dict[line.state], contest_center)
					worksheet.write(row, 9, line.priority, contest_center)
					worksheet.write(row, 10, line.planned_time, contest_center)
					worksheet.write(row, 11, line.planned_mans, contest_center)
					worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
					worksheet.write(row, 13, line.validator_id.name or '', contest_left)
					row += 1
					number += 1

			# 5. Өнөөдрийн хийгдэх ажлууд
			wos = self.env['maintenance.workorder'].search([
				('date_required','=',self.date_start),
				('technic_id','!=',False),
				('technic_id.technic_type','not in',['service_car','mechanizm','transportation_vehicle','equipment']),
				('state','not in',['draft','cancelled','ordered_part','waiting_labour']),
				('maintenance_type','in',['main_service','pm_service','planned'])], order='name')

			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 13, u"Planned job", sub_total)
			row += 1
			number = 1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				temp_style = contest_left_desc
				if line.shift == 'night':
					temp_style = contest_left_desc_night
				worksheet.write(row, 3, line.technic_id.name or '', temp_style)
				worksheet.write(row, 4, line.technic_id.program_code, temp_style)
				worksheet.write(row, 5, line.maintenance_type, temp_style)
				worksheet.write(row, 6, line.shift, temp_style)
				worksheet.write(row, 7, line.description, temp_style)
				worksheet.write(row, 8, state_dict[line.state], contest_center)
				worksheet.write(row, 9, line.priority, contest_center)
				worksheet.write(row, 10, line.planned_time, contest_center)
				worksheet.write(row, 11, line.planned_mans, contest_center)
				worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
				worksheet.write(row, 13, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

			# 6. Төлөвлөгөөт бус засварууд
			wos = self.env['maintenance.workorder'].search([
				('date_required','=',self.date_start),
				('technic_id','!=',False),
				('technic_id.technic_type','not in',['service_car','mechanizm','transportation_vehicle','equipment']),
				('state','not in',['draft','cancelled','ordered_part','waiting_labour']),
				('maintenance_type','=','not_planned'),
				('origin','not in',['daily_welding_job','daily_lather_job'])], order='name')

			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 13, u"Breakdown Job", sub_total)
			row += 1
			number = 1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				temp_style = contest_left_desc
				if line.shift == 'night':
					temp_style = contest_left_desc_night
				worksheet.write(row, 3, line.technic_id.name or '', temp_style)
				worksheet.write(row, 4, line.technic_id.program_code, temp_style)
				worksheet.write(row, 5, line.maintenance_type, temp_style)
				worksheet.write(row, 6, line.shift, temp_style)
				worksheet.write(row, 7, line.description, temp_style)
				worksheet.write(row, 8, state_dict[line.state], contest_center)
				worksheet.write(row, 9, line.priority, contest_center)
				worksheet.write(row, 10, line.planned_time, contest_center)
				worksheet.write(row, 11, line.planned_mans, contest_center)
				worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
				worksheet.write(row, 13, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

			# 7. Waiting labour засварууд
			wos = self.env['maintenance.workorder'].search([
				('state','=','waiting_labour')], order='name')

			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 13, u"Waiting labour", sub_total)
			row += 1
			number = 1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				temp_style = contest_left_desc
				if line.shift == 'night':
					temp_style = contest_left_desc_night
				worksheet.write(row, 3, line.technic_id.name or '', temp_style)
				worksheet.write(row, 4, line.technic_id.program_code, temp_style)
				worksheet.write(row, 5, line.maintenance_type, temp_style)
				worksheet.write(row, 6, line.shift, temp_style)
				worksheet.write(row, 7, line.description, temp_style)
				worksheet.write(row, 8, state_dict[line.state], contest_center)
				worksheet.write(row, 9, line.priority, contest_center)
				worksheet.write(row, 10, line.planned_time, contest_center)
				worksheet.write(row, 11, line.planned_mans, contest_center)
				worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
				worksheet.write(row, 13, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

			# 8. Waiting parts засварууд
			if self.include_waiting_parts:
				wos = self.env['maintenance.workorder'].search([
					('state','=','ordered_part')], order='name')

				worksheet.write(row, 0, "#", sub_total)
				worksheet.merge_range(row, 1, row, 13, u"Waiting parts", sub_total)
				row += 1
				number = 1
				for line in wos:
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 1, line.date_required, contest_center)
					worksheet.write(row, 2, line.name, contest_center)
					temp_style = contest_left_desc
					if line.shift == 'night':
						temp_style = contest_left_desc_night
					worksheet.write(row, 3, line.technic_id.name or '', temp_style)
					worksheet.write(row, 4, line.technic_id.program_code, temp_style)
					worksheet.write(row, 5, line.maintenance_type, temp_style)
					worksheet.write(row, 6, line.shift, temp_style)
					worksheet.write(row, 7, line.description, temp_style)
					worksheet.write(row, 8, state_dict[line.state], contest_center)
					worksheet.write(row, 9, line.priority, contest_center)
					worksheet.write(row, 10, line.planned_time, contest_center)
					worksheet.write(row, 11, line.planned_mans, contest_center)
					worksheet.write(row, 12, (line.planned_time * line.planned_mans) or 0, contest_right)
					worksheet.write(row, 13, line.validator_id.name or '', contest_left)
					row += 1
					number += 1

			# 9. Засварын дуудлагын ажлууд
			if self.include_call:
				calls = self.env['maintenance.call'].search([
					('state','!=','draft'),
					('date_required','=',self.date_start)], order='name')

				worksheet.write(row, 0, "#", sub_total)
				worksheet.merge_range(row, 1, row, 13, u"Дуудлагын засвар", sub_total)
				row += 1
				number = 1
				for line in calls:
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 1, line.date_required, contest_center)
					worksheet.write(row, 2, line.name, contest_center)
					temp_style = contest_left_desc
					if line.shift == 'night':
						temp_style = contest_left_desc_night
					worksheet.write(row, 3, line.technic_id.name or '', temp_style)
					worksheet.write(row, 4, line.technic_id.program_code, temp_style)
					worksheet.write(row, 5, line.call_type, temp_style)
					worksheet.write(row, 6, line.shift, temp_style)
					worksheet.write(row, 7, line.description+": "+(line.performance_description or ''), temp_style)
					worksheet.write(row, 8, line.state, contest_center)
					worksheet.write(row, 9, '', contest_center)
					worksheet.write(row, 10, '', contest_center)
					worksheet.write(row, 11, '', contest_center)
					worksheet.write(row, 12, '', contest_right)
					worksheet.write(row, 13, line.validator_id.name or '', contest_left)
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



