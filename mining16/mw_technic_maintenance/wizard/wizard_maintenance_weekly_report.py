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

class WizardMaintenanceWeeklyReport(models.TransientModel):
	_name = "wizard.maintenance.weekly.report"
	_description = "wizard.maintenance.weekly.report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-%d'))

	def export_report(self):

		dt = self.date_start
		week_number = dt.isocalendar()[1]
		ds = dt - timedelta(days=dt.weekday())
		de = ds + timedelta(days=6)

		query = """
			SELECT
				tt.technic_type as technic_type,
				tt.technic_name as technic_name,
				tt.technic_id as technic_id,
				tt.dddd as dddd,
				tt.shift as shift,
				array_agg(tt.description) as description,
				sum(tt.work_time) as work_time
			FROM (
				SELECT
					t.technic_type as technic_type,
					t.report_order as report_order,
					t.park_number as technic_name,
					t.program_code as program_code,
					t.id as technic_id,
					plan.date_required as dddd,
					plan.shift as shift,
					plan.description as description,
					plan.work_time as work_time
				FROM maintenance_plan_line as plan
				LEFT JOIN technic_equipment as t on (t.id = plan.technic_id)
				WHERE
					  plan.date_required >= '%s' and
					  plan.date_required <= '%s' and
					  plan.state not in ('draft','cancelled')

				UNION ALL

				SELECT
					t.technic_type as technic_type,
					t.report_order as report_order,
					t.park_number as technic_name,
					t.program_code as program_code,
					t.id as technic_id,
					null as dddd,
					'' as shift,
					'' as description,
					0.5 as work_time
				FROM technic_equipment as t
				LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
				WHERE
					  t.state in ('working','repairing','stopped') and
					  t.owner_type = 'own_asset'
					  and t.is_tbb_report
			) as tt
			GROUP BY tt.report_order, tt.technic_type, tt.technic_name, tt.program_code, tt.technic_id, tt.dddd, tt.shift
			ORDER BY tt.report_order, tt.technic_name, tt.program_code, tt.dddd, tt.shift
		""" % (ds, de)
		self.env.cr.execute(query)
		# print '======', query
		plans = self.env.cr.dictfetchall()
		# GET dates
		query_dates = """
			SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
		""" % (ds, de)
		self.env.cr.execute(query_dates)
		dates_result = self.env.cr.dictfetchall()

		if plans:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'weekly report.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_font_size(10)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#E9A227')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(10)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			cell_day = workbook.add_format({'underline':1})
			cell_day.set_text_wrap()
			cell_day.set_font_size(10)
			cell_day.set_align('center')
			cell_day.set_align('vcenter')

			cell_night = workbook.add_format({'underline':1})
			cell_night.set_text_wrap()
			cell_night.set_font_size(10)
			cell_night.set_align('center')
			cell_night.set_align('vcenter')
			cell_night.set_bg_color('#CDCDCB')

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(10)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(10)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)

			grand_total = workbook.add_format({'bold': 1})
			grand_total.set_text_wrap()
			grand_total.set_font_size(10)
			grand_total.set_align('center')
			grand_total.set_align('vcenter')
			grand_total.set_border(style=1)
			grand_total.set_bg_color('#0ACB94')

			contest_center_per = workbook.add_format()
			contest_center_per.set_text_wrap()
			contest_center_per.set_font_size(10)
			contest_center_per.set_align('center')
			contest_center_per.set_align('vcenter')
			contest_center_per.set_border(style=1)
			contest_center_per.set_num_format('0.0%')

			grand_total_per = workbook.add_format({'bold': 1})
			grand_total_per.set_text_wrap()
			grand_total_per.set_font_size(10)
			grand_total_per.set_align('center')
			grand_total_per.set_align('vcenter')
			grand_total_per.set_border(style=1)
			grand_total_per.set_bg_color('#0ACB94')
			grand_total_per.set_num_format('0.0%')

			sub_total_per = workbook.add_format({'bold': 1})
			sub_total_per.set_text_wrap()
			sub_total_per.set_font_size(10)
			sub_total_per.set_align('center')
			sub_total_per.set_align('vcenter')
			sub_total_per.set_border(style=1)
			sub_total_per.set_bg_color('#F7EE5E')
			sub_total_per.set_num_format('0.0%')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(10)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(10)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_right0 = workbook.add_format({'italic':1})
			contest_right0.set_text_wrap()
			contest_right0.set_font_size(10)
			contest_right0.set_align('right')
			contest_right0.set_align('vcenter')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(10)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(10)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			worksheet = workbook.add_worksheet(u'Тайлан: Week'+str(week_number))
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"WEEKLY MAINTENANCE PLAN", h1)

			# TABLE HEADER
			row = 1
			worksheet.merge_range(row, 0, row+2, 0, u"№", header)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+2, 2, u"Техникийн модел", header_wrap)
			worksheet.set_column(2, 2, 25)
			worksheet.merge_range(row, 3, row+2, 3, u"PLANNED WORK", header_wrap)
			worksheet.set_column(3, 3, 25)
			# 7 хоногийн өдрүүд зурах
			days = 7
			day_names = {1:u'Даваа',2:u'Мягмар',3:u'Лхагва',4:u'Пүрэв',5:u'Баасан',6:u'Бямба',7:u'Ням'}
			col = 4
			d = 1
			col_dict = {}
			for ll in dates_result:
				if ll['dddd']:
					worksheet.merge_range(row, col, row, col+1, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
					worksheet.merge_range(row+1, col, row+1, col+1, day_names[d], header_wrap)
					worksheet.write(row+2, col, u'Өдөр', header_wrap)
					worksheet.write(row+2, col+1, u'Шөнө', header_wrap)
					col_dict[ll['dddd']] = col
					col += 2
					d += 1
			worksheet.set_column(4, 17, 5)
			# --------------
			worksheet.merge_range(row, col, row+2, col, u"Ажиллавал зохих цаг", header_wrap)
			worksheet.merge_range(row, col+1, row+2, col+1, u"Т/З/Ц", header_wrap)
			worksheet.merge_range(row, col+2, row+2, col+2, u"ТББК", header_wrap)
			worksheet.freeze_panes(4, 4)

			row = 4
			row_start = 4
			number = 1
			type_dict = {}
			technic_dict = {}
			descriptions = ''
			type_name = ''
			first = True
			total_font_time = 0
			total_repair_time = 0

			sub_totals_address = {
				1:[],2:[],3:[]
			}

			descriptions_dict = {}

			for line in plans:
				if not first and type_name != line['technic_type']:
					worksheet.merge_range(row_start, 1, row-1, 1, type_name, sub_total_90)
					worksheet.merge_range(row, 0, row, col-1, u'НИЙТ: '+type_name, sub_total)
					type_dict[type_name] = [row_start, row]
					row += 1
					row_start = row

				if line['technic_name'] not in technic_dict:
					technic_dict[line['technic_name']] = row
					# DATA
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 2, line['technic_name'], contest_left)
					worksheet.write(row, 3, '', contest_left)
					technic = self.env['technic.equipment'].browse(line['technic_id'])

					norm = technic.technic_setting_id.work_time_per_day or 1
					worksheet.write(row, col, days*norm, contest_center)
					worksheet.write_formula(row, col+1,
						'{=SUM('+self._symbol(row,4) +':'+ self._symbol(row, col-1)+')}', contest_center)
					worksheet.write_formula(row, col+2,
						'{=('+self._symbol(row,col) +'-'+ self._symbol(row, col+1)+')/'+self._symbol(row,col)+'}', contest_center_per)
					sub_totals_address[3].append(self._symbol(row,col+2))

					number += 1
					row += 1

				# Цаг зурах
				if line['dddd']:
					rr = technic_dict[line['technic_name']]
					cc = col_dict[line['dddd']]
					if line['shift'] == 'day':
						worksheet.write(rr, cc, line['work_time'], cell_day)
					else:
						worksheet.write(rr, cc+1, line['work_time'], cell_night)

					# Тайлбар
					txt = line['description'][0]
					if rr in descriptions_dict:
						descriptions_dict[rr].append(txt)
					else:
						descriptions_dict[rr] = [txt]

				first = False
				type_name = line['technic_type']

			# Last Subtotal
			worksheet.merge_range(row_start, 1, row-1, 1, type_name, sub_total_90)
			worksheet.merge_range(row, 0, row, col-1, u'НИЙТ: '+type_name, sub_total)
			type_dict[type_name] = [row_start, row]
			row += 1
			# Нийт тайлбар зурах
			for key in descriptions_dict:
				txt = ','.join(set(descriptions_dict[key]))
				worksheet.write(key, 3, txt, contest_left)

			# Sub total
			row_start = 4
			for key in type_dict:
				rr = type_dict[key][1]
				row_start = type_dict[key][0]
				worksheet.write_formula(rr, col,
					'{=SUM('+self._symbol(row_start,col) +':'+ self._symbol(rr-1, col)+')}', sub_total)
				worksheet.write_formula(rr, col+1,
					'{=SUM('+self._symbol(row_start,col+1) +':'+ self._symbol(rr-1, col+1)+')}', sub_total)
				worksheet.write_formula(rr, col+2,
					'{=AVERAGE('+self._symbol(row_start,col+2) +':'+ self._symbol(rr-1, col+2)+')}', sub_total_per)
				row_start = rr+1

				sub_totals_address[1].append(self._symbol(rr,col))
				sub_totals_address[2].append(self._symbol(rr,col+1))

			# Grand total
			worksheet.merge_range(row, 0, row, col-1, u'Нийт ТББК:', grand_total)
			worksheet.write_formula(row, col,'{=IFERROR('+ '+'.join(sub_totals_address[1]) +',0)}', grand_total)
			worksheet.write_formula(row, col+1,'{=IFERROR('+ '+'.join(sub_totals_address[2]) +',0)}', grand_total)
			ttbbk = '{=IFERROR(('+ '+'.join(sub_totals_address[3]) +')/%d,0)}' % len(sub_totals_address[3])
			worksheet.write_formula(row, col+2, ttbbk, grand_total_per)
			row += 1

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

	# Гүйцэтгэл татах

	def export_report_performance(self):

		dt = self.date_start
		week_number = dt.isocalendar()[1]
		ds = dt - timedelta(days=dt.weekday())
		de = ds + timedelta(days=6)

		ds = ds.strftime('%Y-%m-%d')
		de = de.strftime('%Y-%m-%d')

		query = """
			SELECT
				t.report_order as report_order,
				t.technic_type as technic_type,
				t.park_number as technic_name,
				t.id as technic_id,
				per.date as dddd,
				daily.shift as shift,
				sum(per.repair_time) as work_time
			FROM mining_motohour_entry_line as per
			LEFT JOIN mining_daily_entry as daily on (daily.id = per.motohour_id)
			LEFT JOIN technic_equipment as t on (t.id = per.technic_id)
			LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
			WHERE
				  per.date >= '%s' and
				  per.date <= '%s' and
				  t.state in ('working','repairing','stopped') and
				  t.owner_type = 'own_asset' and
				  t.is_tbb_report
			GROUP BY t.report_order, t.technic_type, t.park_number, t.id, per.date, daily.shift
			ORDER BY t.report_order, t.park_number, t.program_code, per.date, daily.shift
		""" % (ds, de)
		self.env.cr.execute(query)
		print ('======', query)
		plans = self.env.cr.dictfetchall()
		# GET dates
		query_dates = """
			SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
		""" % (ds, de)
		self.env.cr.execute(query_dates)
		dates_result = self.env.cr.dictfetchall()

		if plans:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'weekly performance report.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_font_size(10)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#E9A227')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(10)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			cell_day = workbook.add_format({'underline':1})
			cell_day.set_text_wrap()
			cell_day.set_font_size(10)
			cell_day.set_align('center')
			cell_day.set_align('vcenter')

			cell_night = workbook.add_format({'underline':1})
			cell_night.set_text_wrap()
			cell_night.set_font_size(10)
			cell_night.set_align('center')
			cell_night.set_align('vcenter')
			cell_night.set_bg_color('#CDCDCB')

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(10)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(10)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)

			grand_total = workbook.add_format({'bold': 1})
			grand_total.set_text_wrap()
			grand_total.set_font_size(10)
			grand_total.set_align('center')
			grand_total.set_align('vcenter')
			grand_total.set_border(style=1)
			grand_total.set_bg_color('#0ACB94')

			contest_center_per = workbook.add_format()
			contest_center_per.set_text_wrap()
			contest_center_per.set_font_size(10)
			contest_center_per.set_align('center')
			contest_center_per.set_align('vcenter')
			contest_center_per.set_border(style=1)
			contest_center_per.set_num_format('0.0%')

			grand_total_per = workbook.add_format({'bold': 1})
			grand_total_per.set_text_wrap()
			grand_total_per.set_font_size(10)
			grand_total_per.set_align('center')
			grand_total_per.set_align('vcenter')
			grand_total_per.set_border(style=1)
			grand_total_per.set_bg_color('#0ACB94')
			grand_total_per.set_num_format('0.0%')

			sub_total_per = workbook.add_format({'bold': 1})
			sub_total_per.set_text_wrap()
			sub_total_per.set_font_size(10)
			sub_total_per.set_align('center')
			sub_total_per.set_align('vcenter')
			sub_total_per.set_border(style=1)
			sub_total_per.set_bg_color('#F7EE5E')
			sub_total_per.set_num_format('0.0%')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(10)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(10)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_right0 = workbook.add_format({'italic':1})
			contest_right0.set_text_wrap()
			contest_right0.set_font_size(10)
			contest_right0.set_align('right')
			contest_right0.set_align('vcenter')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(10)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(10)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			worksheet = workbook.add_worksheet(u'Тайлан: Week'+str(week_number))
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"WEEKLY MAINTENANCE PERFORMANCE", h1)

			# TABLE HEADER
			row = 1
			worksheet.merge_range(row, 0, row+2, 0, u"№", header)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+2, 2, u"Техникийн модел", header_wrap)
			worksheet.set_column(2, 2, 25)
			worksheet.merge_range(row, 3, row+2, 3, u"COMMENTs", header_wrap)
			worksheet.set_column(3, 3, 25)
			# 7 хоногийн өдрүүд зурах
			days = 7
			day_names = {1:u'Даваа',2:u'Мягмар',3:u'Лхагва',4:u'Пүрэв',5:u'Баасан',6:u'Бямба',7:u'Ням'}
			col = 4
			d = 1
			col_dict = {}
			for ll in dates_result:
				worksheet.merge_range(row, col, row, col+1, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
				worksheet.merge_range(row+1, col, row+1, col+1, day_names[d], header_wrap)
				worksheet.write(row+2, col, u'Өдөр', header_wrap)
				worksheet.write(row+2, col+1, u'Шөнө', header_wrap)
				col_dict[ll['dddd']] = col
				col += 2
				d += 1
			worksheet.set_column(4, 17, 5)
			# --------------
			worksheet.merge_range(row, col, row+2, col, u"Засварын цаг", header_wrap)
			worksheet.merge_range(row, col+1, row+2, col+1, u"Төлөвлөсөн ТББ %", header_wrap)
			worksheet.merge_range(row, col+2, row+2, col+2, u"Бодит ТББ %", header_wrap)
			worksheet.set_column(col+1, col+2, 12)
			worksheet.freeze_panes(4, 4)

			row = 4
			number = 1
			type_dict = {}
			row_start = 4
			technic_dict = {}
			descriptions = ''
			type_name = ''
			first = True
			total_font_time = 0
			total_repair_time = 0

			sub_totals_address = {
				1:[],2:[],3:[]
			}

			for line in plans:
				if not first and type_name != line['technic_type']:
					worksheet.merge_range(row_start, 1, row-1, 1, type_name, sub_total_90)
					worksheet.merge_range(row, 0, row, col-1, u'НИЙТ: '+type_name, sub_total)
					type_dict[type_name] = [row_start, row]
					row += 1
					row_start = row

				if line['technic_name'] not in technic_dict:
					technic_dict[line['technic_name']] = row
					# DATA
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 2, line['technic_name'], contest_left)
					worksheet.write(row, 3, '', contest_left)

					technic = self.env['technic.equipment'].browse(line['technic_id'])

					worksheet.write_formula(row, col,
						'{=SUM('+self._symbol(row,4) +':'+ self._symbol(row, col-1)+')}', contest_center)

					p_tbbk = technic.get_technic_planned_tbbk(ds, de)['tbbk'] or 0
					# print '===', technic.name, p_tbbk
					worksheet.write(row, col+1, round(p_tbbk,2), contest_center)

					tbbk = technic.get_technic_tbbk(ds, de)['tbbk'] or 0
					worksheet.write(row, col+2, round(tbbk,2), contest_center)

					sub_totals_address[2].append(self._symbol(row,col+1))
					sub_totals_address[3].append(self._symbol(row,col+2))

					number += 1
					row += 1

				# Цаг зурах
				rr = technic_dict[line['technic_name']]
				cc = col_dict[line['dddd']]
				if line['shift'] == 'day':
					worksheet.write(rr, cc, line['work_time'], cell_day)
				else:
					worksheet.write(rr, cc+1, line['work_time'], cell_night)

				first = False
				type_name = line['technic_type']

			# Last Subtotal
			worksheet.merge_range(row_start, 1, row-1, 1, type_name, sub_total_90)
			worksheet.merge_range(row, 0, row, col-1, u'НИЙТ: '+type_name, sub_total)
			type_dict[type_name] = [row_start, row]
			row += 1
			# Нийт тайлбар зурах
			for key in technic_dict:
				desc = self.env['maintenance.workorder'].search([
					('date_required','>=',ds),
					('date_required','<=', de),
					('state','in',['closed','done']),
					('maintenance_type_id','!=',False),
					('technic_id.name','=',key)]).mapped('maintenance_type_id.name')
				worksheet.write(technic_dict[key], 3, ','.join(desc), contest_left)

			# Sub total
			row_start = 4
			for key in type_dict:
				rr = type_dict[key][1]
				row_start = type_dict[key][0]
				worksheet.write_formula(rr, col,
					'{=SUM('+self._symbol(row_start,col) +':'+ self._symbol(rr-1, col)+')}', sub_total)
				worksheet.write_formula(rr, col+1,
					'{=ROUND(AVERAGE('+self._symbol(row_start,col+1) +':'+ self._symbol(rr-1, col+1)+'),2)}', sub_total)
				worksheet.write_formula(rr, col+2,
					'{=ROUND(AVERAGE('+self._symbol(row_start,col+2) +':'+ self._symbol(rr-1, col+2)+'),2)}', sub_total)

				sub_totals_address[1].append(self._symbol(rr,col))

			# Grand total
			worksheet.merge_range(row, 0, row, col-1, u'Нийт ТББК:', grand_total)
			worksheet.write_formula(row, col,'{=IFERROR('+ '+'.join(sub_totals_address[1]) +',0)}', grand_total)
			ptbbk = '{=IFERROR(ROUND(('+ '+'.join(sub_totals_address[2]) +')/%d,2),0)}' % len(sub_totals_address[2])
			worksheet.write_formula(row, col+1, ptbbk, grand_total)
			ttbbk = '{=IFERROR(ROUND(('+ '+'.join(sub_totals_address[3]) +')/%d,2),0)}' % len(sub_totals_address[3])
			worksheet.write_formula(row, col+2, ttbbk, grand_total)
			row += 1

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



