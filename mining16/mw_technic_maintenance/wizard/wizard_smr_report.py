# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time
import xlsxwriter
from io import BytesIO
import base64

import logging
_logger = logging.getLogger(__name__)

class WizardSMRReport(models.TransientModel):
	_name = "wizard.smr.report"  
	_description = "wizard.smr.report"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	
	def export_report(self):
		if self.date_start <= self.date_end:
			query = """
				SELECT 
					temp.report_order as report_order,
					temp.technic_name as technic_name,
					temp.program_code as program_code,
					temp.technic_id as technic_id,
					temp.dddd as dddd,
					max(temp.qty) as qty
				FROM (
					SELECT
						tt.report_order as report_order,
						tt.name as technic_name,
						tt.program_code as program_code, 
						mhl.technic_id as technic_id,
						mhl.last_odometer_value as qty,
						mh.date as dddd
					FROM mining_motohour_entry_line as mhl
					LEFT JOIN mining_daily_entry as mh on mh.id = mhl.motohour_id
					LEFT JOIN technic_equipment as tt on (tt.id = mhl.technic_id)
					WHERE -- mh.state = 'approved' and
						  mh.date >= '%s' and
						  mh.date <= '%s' and
						  mh.shift = 'night' and 
						  tt.owner_type = 'own_asset' 
			 	UNION ALL
					
					SELECT 
						tt.report_order as report_order,
						tt.name as technic_name,
						tt.program_code as program_code,
						tt.id as technic_id,
						0 as qty,
						null as dddd
					FROM technic_equipment as tt
					LEFT JOIN technic_equipment_setting as ts on ts.id = tt.technic_setting_id
					WHERE 
						  tt.state in ('working','repairing','stopped') and 
						  tt.owner_type = 'own_asset' 
						  and tt.is_tbb_report
				) as temp
				GROUP BY temp.report_order, temp.program_code, temp.technic_name, temp.technic_id, temp.dddd
				ORDER BY temp.report_order, temp.program_code, temp.technic_name, temp.dddd
			""" % (datetime.strftime(self.date_start, '%Y-%m-%d'), datetime.strftime(self.date_end, '%Y-%m-%d'))
			self.env.cr.execute(query)
			# print '======', query
			moto_hours = self.env.cr.dictfetchall()

			query_dates = """
				SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
			""" % (datetime.strftime(self.date_start, '%Y-%m-%d'), datetime.strftime(self.date_end, '%Y-%m-%d'))
			self.env.cr.execute(query_dates)
			dates_result = self.env.cr.dictfetchall()

			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'smr_report_' + self.date_end.strftime("%Y-%m-%d") + '.xlsx'

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

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			contest_center_plan = workbook.add_format()
			contest_center_plan.set_text_wrap()
			contest_center_plan.set_font_size(9)
			contest_center_plan.set_align('center')
			contest_center_plan.set_align('vcenter')
			contest_center_plan.set_border(style=1)
			contest_center_plan.set_bg_color('#4BFEE0')

			contest_smr_plan = workbook.add_format()
			contest_smr_plan.set_text_wrap()
			contest_smr_plan.set_font_size(9)
			contest_smr_plan.set_align('center')
			contest_smr_plan.set_align('vcenter')
			contest_smr_plan.set_border(style=1)
			contest_smr_plan.set_bg_color('#acb8bf')

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(9)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			# PM ийн өнгө авах
			color_styles = {}
			for mtt in self.env['maintenance.type'].search([], order='name'):
				contest_time = workbook.add_format()
				contest_time.set_text_wrap()
				contest_time.set_font_size(9)
				contest_time.set_align('center')
				contest_time.set_align('vcenter')
				contest_time.set_border(style=1)
				contest_time.set_bg_color(mtt.color)
				color_styles[mtt.id] = [mtt.name, contest_time]

			# TABLE HEADER
			worksheet = workbook.add_worksheet(u'SMR')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"SMR report", h1)
			
			row = 1
			worksheet.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+1, 2, u"Техникийн нэр", header_wrap)
			worksheet.set_column(2, 2, 18)
			worksheet.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column(3, 3, 10)
			# LV - Sheet 2
			worksheet_2 = workbook.add_worksheet(u'SMR - LV')
			worksheet_2.set_zoom(80)
			worksheet_2.write(0,2, u"SMR LV report", h1)

			worksheet_2.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet_2.set_column(0, 0, 5)
			worksheet_2.set_column(1, 1, 4)
			worksheet_2.merge_range(row, 1, row+1, 2, u"Техникийн нэр", header_wrap)
			worksheet_2.set_column(2, 2, 18)
			worksheet_2.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet_2.set_column(3, 3, 10)

			# PARTs - Sheet 3
			worksheet_3 = workbook.add_worksheet(u'SMR - PARTs')
			worksheet_3.set_zoom(80)
			worksheet_3.write(0,2, u"SMR PARTs report", h1)

			worksheet_3.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet_3.set_column(0, 0, 5)
			worksheet_3.set_column(1, 1, 4)
			worksheet_3.merge_range(row, 1, row+1, 2, u"Техникийн нэр", header_wrap)
			worksheet_3.set_column(2, 2, 18)
			worksheet_3.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet_3.set_column(3, 3, 10)
			
			# Сарын өдрүүд зурах
			col_dict = {}
			col = 4
			for ll in dates_result:
				worksheet.write(row+1, col, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
				worksheet_2.write(row+1, col, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
				worksheet_3.write(row+1, col, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
				col_dict[ll['dddd']] = col
				col += 1
			worksheet.set_column(4, col-1, 10)
			worksheet.merge_range(row, 4, row, col-1, u'Тайлант хугацаа: '+datetime.strftime(self.date_start, '%Y-%m-%d')+' -> '+datetime.strftime(self.date_end, '%Y-%m-%d'), header_wrap)
			worksheet.freeze_panes(3, 4)
			# LV - Sheet 2
			worksheet_2.set_column(4, col-1, 10)
			worksheet_2.merge_range(row, 4, row, col-1, u'Тайлант хугацаа: '+datetime.strftime(self.date_start, '%Y-%m-%d')+' -> '+datetime.strftime(self.date_end, '%Y-%m-%d'), header_wrap)
			worksheet_2.freeze_panes(3, 4)
			# PARTs - Sheet 3
			worksheet_3.set_column(4, col-1, 10)
			worksheet_3.merge_range(row, 4, row, col-1, u'Тайлант хугацаа: '+datetime.strftime(self.date_start, '%Y-%m-%d')+' -> '+datetime.strftime(self.date_end, '%Y-%m-%d'), header_wrap)
			worksheet_3.freeze_panes(3, 4)

			# DATA зурах
			row_dict = {}
			row = 3
			number = 1
			for line in moto_hours:
				technic = self.env['technic.equipment'].sudo().browse(line['technic_id'])
				if line['technic_id'] not in row_dict:
					worksheet.write(row, 0, number, number_right)
					worksheet.merge_range(row, 1, row, 2, technic.park_number, contest_left)
					worksheet.write(row, 3, technic.program_code, contest_left)
					row_dict[line['technic_id']] = row
					row += 1
					number += 1

				if line['dddd']:
					tmp_style = contest_center
					qty = line['qty']
					rr = row_dict[line['technic_id']]
					cc = col_dict[line['dddd']]

					# Тухайн SMR WO байгаа эсэхийг шалгах
					wo_comment = ""
					wo = self.env['maintenance.workorder'].search([
						('state','in',['done','closed']),
						('into_smr_report','=',True),
						('technic_id','=',technic.id),
						('date_required','=',line['dddd'])
						], limit=1)
					if wo:
						_logger.info("---SRM WO ====== %s %d", wo.name, wo.id)
						tmp_style = contest_smr_plan
						qty = wo.finish_odometer
						wo_comment = wo.name +':\n'+ (wo.comment_smr_report or wo.performance_description)
						worksheet.write_comment(rr, cc, wo_comment)

					# Тухайн өдөр хийгдсэн PM байгаа эсэхийг шалгах
					wo = self.env['maintenance.workorder'].search([
						('state','in',['done','closed']),
						('maintenance_type','=','pm_service'),
						('technic_id','=',technic.id),
						('date_required','=',line['dddd'])
						], limit=1)
					if wo:
						if wo.maintenance_type_id.id in color_styles:
							tmp_style = color_styles[wo.maintenance_type_id.id][1]
							qty = wo.finish_odometer if wo.finish_odometer > qty else qty
							comment = wo.name +':\n'+ wo.maintenance_type_id.name
							worksheet.write_comment(rr, cc, comment+'\n'+wo_comment)

					worksheet.write(rr, cc, qty, tmp_style)
				# 

			# PM colors DESC
			row += 1
			for key in color_styles:
				worksheet.write(row, 2, color_styles[key][0], contest_right)
				worksheet.write(row, 3, '', color_styles[key][1])
				row += 1

			# 7 хоногийн План олох
			# Өдрийг ахиулах
			date1 = self.date_end + timedelta(days=1)
			date1 = date1.strftime('%Y-%m-%d')
			# 
			date2 = self.date_end + timedelta(days=7)
			date2 = date2.strftime('%Y-%m-%d')
			# Огноо зурах
			query_dates = """
				SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
			""" % (date1, date2)
			self.env.cr.execute(query_dates)
			dates_result = self.env.cr.dictfetchall()
			c0 = col
			for ll in dates_result:
				worksheet.write(2, col, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
				col_dict[ll['dddd']] = col
				col += 1
			worksheet.set_column(4, col-1, 10)
			worksheet.merge_range(1, c0, 1, col-1, u'ПЛАН: 7 хоног', header_wrap)
			# SEARCH
			# Хойшлуулаагүй төлөвлөгөө
			plans = self.env['maintenance.plan.line'].search([
				('state','!=','draft'),
				('maintenance_type','=','pm_service'),
				('ref_plan_id','=',False),
				('to_delay','=',False),
				('date_required','>=',date1),
				('date_required','<=',date2)])

			# Зурах
			for line in plans:
				technic = line.technic_id
				if technic.id not in row_dict:
					worksheet.write(row, 0, number, number_right)
					worksheet.merge_range(row, 1, row, 2, technic.park_number, contest_left)
					worksheet.write(row, 3, technic.program_code, contest_left)
					row_dict[technic.id] = row
					row += 1
					number += 1

				rr = row_dict[technic.id]
				cc = col_dict[line.date_required]

				worksheet.write(rr, cc, line.maintenance_type_id.name, contest_center_plan)
				worksheet.write_comment(rr, cc, line.name+':\n'+line.description)

			# Хойшлуулсан төлөвлөгөө зурах
			plans = self.env['maintenance.plan.line'].search([
				('state','!=','draft'),
				('maintenance_type','=','pm_service'),
				('ref_plan_id','=',False),
				('to_delay','=',True),
				('to_delay_date','>=',date1),
				('to_delay_date','<=',date2)])
			for line in plans:

				technic = line.technic_id
				if technic.id not in row_dict:
					worksheet.write(row, 0, number, number_right)
					worksheet.merge_range(row, 1, row, 2, technic.park_number, contest_left)
					worksheet.write(row, 3, technic.program_code, contest_left)
					row_dict[technic.id] = row
					row += 1
					number += 1

				rr = row_dict[technic.id]
				cc = col_dict[line.to_delay_date]

				worksheet.write(rr, cc, line.maintenance_type_id.name, contest_center_plan)
				worksheet.write_comment(rr, cc, line.name+':\n'+line.description)

			# LV буюу ТББ тооцохгүй техникүүд =======================================
			query = """
				SELECT 
					tt.technic_type as technic_type,
					tt.program_code as program_code,
					tt.name as name,
					tt.technic_id as technic_id,
					max(tt.qty) as qty,
					tt.dddd as dddd
				FROM (
					SELECT 
						t.technic_type as technic_type,
				 	t.program_code as program_code,
				 	t.name as name,
						ti.technic_id as technic_id,
						ti.odometer_value as qty,
						ti.date_inspection as dddd
					FROM technic_inspection as ti
					LEFT JOIN technic_equipment as t on t.id = ti.technic_id
					LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
					WHERE ti.state = 'done' and
						  ti.date_inspection >= '%s' and
						  ti.date_inspection <= '%s' and
						  t.owner_type = 'own_asset' and 
						  (t.is_tbb_report != true or t.is_tbb_report is null)
						  -- and t.technic_type in ('service_car','technology_technic','achaanii_mashin','transportation_vehicle')
					UNION ALL

					SELECT 
				 	t.technic_type as technic_type,
				 	t.program_code as program_code,
				 	t.name as name,
						t.id as technic_id,
						0 as qty,
						null as dddd
					FROM technic_equipment as t
					LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
					WHERE 
						  t.owner_type = 'own_asset' and
						  t.state not in ('draft','parking','inactive') and 
						  (t.is_tbb_report != true or t.is_tbb_report is null)
				) as tt
				GROUP BY tt.technic_type, tt.program_code, tt.name, tt.technic_id, tt.dddd
				ORDER BY tt.technic_type, tt.program_code, tt.name, tt.dddd
			""" % (datetime.strftime(self.date_start, '%Y-%m-%d'), datetime.strftime(self.date_end, '%Y-%m-%d'))
			self.env.cr.execute(query)
			# print '======', query
			query_result = self.env.cr.dictfetchall()
			# DATA зурах
			row_dict = {}
			technic_dict = []
			row = 3
			number = 1
			for line in query_result:
				technic = self.env['technic.equipment'].sudo().browse(line['technic_id'])
				if line['technic_id'] not in row_dict:
					worksheet_2.write(row, 0, number, number_right)
					worksheet_2.merge_range(row, 1, row, 2, technic.park_number, contest_left)
					worksheet_2.write(row, 3, technic.program_code, contest_left)
					row_dict[line['technic_id']] = row
					row += 1
					number += 1
					technic_dict.append(line['technic_id'])

				if line['dddd']:
					tmp_style = contest_center
					qty = line['qty']
					rr = row_dict[line['technic_id']]
					cc = col_dict[line['dddd']]

					# Тухайн SMR WO байгаа эсэхийг шалгах
					wo = self.env['maintenance.workorder'].search([
						('state','in',['done','closed']),
						('into_smr_report','=',True),
						('technic_id','=',technic.id),
						('date_required','=',line['dddd'])
						], limit=1)
					if wo:
						tmp_style = contest_smr_plan
						qty = wo.finish_odometer
						comment = (wo.performance_description or '') +'\n'+(wo.name or '')
						worksheet_2.write_comment(rr, cc, comment)

					# Тухайн өдөр хийгдсэн PM байгаа эсэхийг шалгах
					wo = self.env['maintenance.workorder'].search([
						('state','in',['done','closed']),
						('maintenance_type','=','pm_service'),
						('technic_id','=',technic.id),
						# ('pm_priority','!=',0),
						('date_required','=',line['dddd'])
						], limit=1)
					if wo:
						if wo.maintenance_type_id.id in color_styles:
							tmp_style = color_styles[wo.maintenance_type_id.id][1]
							qty = wo.finish_odometer
							comment = wo.maintenance_type_id.name +'\n'+wo.name
							worksheet_2.write_comment(rr, cc, comment)

					worksheet_2.write(rr, cc, qty, tmp_style)

			# PARTs =======================================
			query = """
				SELECT 
					tt.technic_type as technic_type,
					tt.program_code as program_code,
					tt.name as name,
					tt.technic_id as technic_id,
					tt.waiting_id as waiting_id
				FROM (
					SELECT 
						t.technic_type as technic_type,
				 	t.program_code as program_code,
				 	t.name as name,
						mpw.technic_id as technic_id,
						mpw.id as waiting_id
					FROM maintenance_parts_waiting as mpw
					LEFT JOIN technic_equipment as t on t.id = mpw.technic_id
					LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
					WHERE mpw.state = 'confirmed' and
						  mpw.date_start >= '%s' and
						  mpw.date_end <= '%s'
					UNION ALL
					SELECT 
				 	t.technic_type as technic_type,
				 	t.program_code as program_code,
				 	t.name as name,
						t.id as technic_id,
						null as waiting_id
					FROM technic_equipment as t
					LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
					WHERE 
						  t.owner_type = 'own_asset' and
						  t.state not in ('draft','parking','inactive') and 
						  (t.is_tbb_report != true or t.is_tbb_report is null)
				) as tt
				GROUP BY tt.technic_type, tt.program_code, tt.name, tt.technic_id, tt.waiting_id
				ORDER BY tt.technic_type, tt.program_code, tt.name
			""" % (datetime.strftime(self.date_start, '%Y-%m-%d'), datetime.strftime(self.date_end, '%Y-%m-%d'))
			self.env.cr.execute(query)
			print ('======', query)
			query_result = self.env.cr.dictfetchall()
			# DATA зурах
			contest_red = workbook.add_format()
			contest_red.set_text_wrap()
			contest_red.set_font_size(9)
			contest_red.set_align('center')
			contest_red.set_align('vcenter')
			contest_red.set_border(style=1)
			contest_red.set_bg_color("#FA7765")

			contest_blue = workbook.add_format()
			contest_blue.set_text_wrap()
			contest_blue.set_font_size(9)
			contest_blue.set_align('center')
			contest_blue.set_align('vcenter')
			contest_blue.set_border(style=1)
			contest_blue.set_bg_color("#65B9FA")

			row_dict = {}
			technic_dict = []
			row = 3
			number = 1
			for line in query_result:
				technic = self.env['technic.equipment'].sudo().browse(line['technic_id'])
				if line['technic_id'] not in row_dict:
					worksheet_3.write(row, 0, number, number_right)
					worksheet_3.merge_range(row, 1, row, 2, technic.park_number, contest_left)
					worksheet_3.write(row, 3, technic.program_code, contest_left)
					row_dict[line['technic_id']] = row
					row += 1
					number += 1
					technic_dict.append(line['technic_id'])

				if line['waiting_id']:
					tmp_style = contest_blue
					mpw = self.env['maintenance.parts.waiting'].browse(line['waiting_id'])
					rr = row_dict[line['technic_id']]

					if mpw.technic_status == 'stopped':
						tmp_style = contest_red
					query_dates = """
					SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
					""" % (datetime.strftime(mpw.date_start, '%Y-%m-%d'), datetime.strftime(mpw.date_end, '%Y-%m-%d'))
					self.env.cr.execute(query_dates)
					dates_result2 = self.env.cr.dictfetchall()
					for line in dates_result2:
						if line['dddd'] in col_dict:
							cc = col_dict[line['dddd']]
							worksheet_3.write(rr, cc, "", tmp_style)
							worksheet_3.write_comment(rr, cc, mpw.name)

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


