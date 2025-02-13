# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import collections
from calendar import monthrange

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardMaintenanceMonthlyReport(models.TransientModel):
	_name = "wizard.maintenance.monthly.report"
	_description = "wizard maintenance monthly report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))

	def export_report(self):

		year = int(self.date_start.year)
		month = int(self.date_start.month)
		days = monthrange(year,month)[1]
		ds = datetime.strftime(self.date_start,'%Y-%m-01')
		de = datetime.strftime(self.date_start, '%Y-%m-' + str(days))

		query = """
			SELECT
				t.report_order as report_order,
				t.technic_type as technic_type,
				t.name as technic_name,
				t.id as technic_id,
				plan.date_required as dddd,
				array_agg(plan.description) as description,
				min(plan.maintenance_type_id) as mtt_id,
				sum(plan.work_time) as work_time
			FROM maintenance_plan_line as plan
			LEFT JOIN technic_equipment as t on (t.id = plan.technic_id)
			WHERE
				  plan.date_required >= '%s' and
				  plan.date_required <= '%s' and
				  plan.state not in ('draft','cancelled')
			GROUP BY t.report_order, t.technic_type, t.name, t.id, plan.date_required
			ORDER BY t.report_order, t.technic_type, t.name, plan.date_required
		""" % (ds, de)
		self.env.cr.execute(query)
		print ('======', query)
		plans = self.env.cr.dictfetchall()

		if plans:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Monthly report.xlsx'

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

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(10)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#FABC51')

			grand_total = workbook.add_format({'bold': 1})
			grand_total.set_text_wrap()
			grand_total.set_font_size(10)
			grand_total.set_align('center')
			grand_total.set_align('vcenter')
			grand_total.set_border(style=1)
			grand_total.set_bg_color('#E49000')

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

			# PM ийн өнгө авах
			color_styles = {}
			for mtt in self.env['maintenance.type'].search([], order='name'):
				contest_time = workbook.add_format()
				contest_time.set_text_wrap()
				contest_time.set_font_size(10)
				contest_time.set_align('center')
				contest_time.set_align('vcenter')
				contest_time.set_border(style=1)
				contest_time.set_bg_color(mtt.color)
				color_styles[mtt.id] = [mtt.name, contest_time]

			# Борлуулагчаар харуулах sheet
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.set_zoom(65)
			worksheet.write(0,2, u"MONTHLY REPORT", h1)

			# TABLE HEADER
			row = 1
			worksheet.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+1, 2, u"Техникийн модел", header_wrap)
			worksheet.set_column(2, 2, 25)
			worksheet.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column(3, 3, 10)
			# Сарын өдрүүд зурах
			for i in range(4,days+4):
				worksheet.write(row+1, i, i-3, header_wrap)
			worksheet.set_column(4, days+3, 4)
			worksheet.merge_range(row, 4, row, days+3, str(month)+u"-р сар", header_wrap)
			col = days+4
			# --------------
			worksheet.merge_range(row, col, row+1, col, u"Хийгдэх ажил", header_wrap)
			worksheet.set_column(col, col, 25)
			worksheet.merge_range(row, col+1, row+1, col+1, u"Ажиллавал зохих цаг", header_wrap)
			worksheet.merge_range(row, col+2, row+1, col+2, u"Т/З/Ц", header_wrap)
			worksheet.merge_range(row, col+3, row+1, col+3, u"ТББК", header_wrap)
			worksheet.freeze_panes(3, 4)

			row = 3
			number = 1
			type_dict = {}
			technic_dict = {}
			descriptions = ''
			type_name = ''
			row_start = 3
			first = True
			total_font_time = 0
			total_repair_time = 0

			sub_totals_address = {
				1:[],2:[],3:[]
			}

			descriptions_dict = {}

			for line in plans:
				if not first and type_name != line['technic_type']:
					worksheet.merge_range(row, 0, row, col, u'НИЙТ: '+type_name, sub_total)
					type_dict[type_name] = [row_start, row]
					row += 1
					row_start = row

				if line['technic_name'] not in technic_dict:
					technic_dict[line['technic_name']] = row
					# DATA
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 2, line['technic_name'] or '', contest_left)
					worksheet.write(row, 3, '', contest_left)
					technic = self.env['technic.equipment'].browse(line['technic_id'])

					norm = technic.technic_setting_id.work_time_per_day or 1
					worksheet.write(row, col+1, days*norm, contest_center)
					worksheet.write_formula(row, col+2,
						'{=SUM('+self._symbol(row,4) +':'+ self._symbol(row, days+3)+')}', contest_center)
					worksheet.write_formula(row, col+3,
						'{=ROUND(100-('+self._symbol(row,col+2) +'*100/'+ self._symbol(row, col+1)+'),2)}', contest_center)
					sub_totals_address[3].append(self._symbol(row,col+3))

					number += 1
					row += 1

				rr = technic_dict[line['technic_name']]
				cc = int(line['dddd'].day)+3

				# TIME COLOR
				tmp_style = False
				if line['mtt_id']:
					tmp_style = color_styles[line['mtt_id']][1]
				worksheet.write(rr, cc, line['work_time'], tmp_style)

				# Тайлбар
				txt = ','.join(line['description'])
				if rr in descriptions_dict:
					descriptions_dict[rr] += ', '+txt
				else:
					descriptions_dict[rr] = txt

				first = False
				type_name = line['technic_type']

			# Last Subtotal
			worksheet.merge_range(row, 0, row, col, u'НИЙТ: '+type_name, sub_total)
			type_dict[type_name] = [row_start, row]
			row += 1
			# Нийт тайлбар зурах
			for key in descriptions_dict:
				worksheet.write(key, col, descriptions_dict[key] or '', contest_left)

			# Sub total
			for key in type_dict:
				rr = type_dict[key][1]
				row_start = type_dict[key][0]
				worksheet.write_formula(rr, col+1,
					'{=SUM('+self._symbol(row_start,col+1) +':'+ self._symbol(rr-1, col+1)+')}', sub_total)
				worksheet.write_formula(rr, col+2,
					'{=ROUND(AVERAGE('+self._symbol(row_start,col+2) +':'+ self._symbol(rr-1, col+2)+'),2)}', sub_total)
				worksheet.write_formula(rr, col+3,
					'{=ROUND(AVERAGE('+self._symbol(row_start,col+3) +':'+ self._symbol(rr-1, col+3)+'),2)}', sub_total)
				row_start = rr+1

				sub_totals_address[1].append(self._symbol(rr,col+1))
				sub_totals_address[2].append(self._symbol(rr,col+2))

			# Grand total
			worksheet.merge_range(row, 0, row, col, u'Нийт ТББК:', grand_total)
			worksheet.write_formula(row, col+1,'{=IFERROR('+ '+'.join(sub_totals_address[1]) +',0)}', grand_total)
			worksheet.write_formula(row, col+2,'{=IFERROR('+ '+'.join(sub_totals_address[2]) +',0)}', grand_total)
			ttbbk = '{=IFERROR(ROUND(('+ '+'.join(sub_totals_address[3]) +')/%d,2),0)}' % len(sub_totals_address[3])
			worksheet.write_formula(row, col+3, ttbbk, grand_total)
			row += 1

			# PM colors DESC
			row += 1
			for key in color_styles:
				worksheet.write(row, 2, color_styles[key][0] or '', contest_right0)
				worksheet.write(row, 3, '', color_styles[key][1])
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

		year = int(self.date_start.year)
		month = int(self.date_start.month)
		days = monthrange(year,month)[1]
		ds = datetime.strftime(self.date_start,'%Y-%m-01')
		de = datetime.strftime(self.date_start, '%Y-%m-' + str(days))

		query = """
			SELECT
				t.report_order as report_order,
				t.technic_type as technic_type,
				t.name as technic_name,
				t.id as technic_id,
				per.date as dddd,
				-- array_agg(per.description) as description,
				sum(per.repair_time) as work_time
			FROM mining_motohour_entry_line as per
			LEFT JOIN technic_equipment as t on (t.id = per.technic_id)
			LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
			WHERE
				  per.date >= '%s' and
				  per.date <= '%s' and
				  t.state in ('working','repairing','stopped') and
				  t.owner_type = 'own_asset' and
				  t.is_tbb_report
			GROUP BY t.report_order, t.technic_type, t.name, t.id, per.date
			ORDER BY t.report_order, t.technic_type, t.name, per.date
		""" % (ds, de)
		print('=========================================',ds,de,type(ds),type(de))
		self.env.cr.execute(query)
		# print '======', query
		pers = self.env.cr.dictfetchall()

		if pers:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Monthly performance report.xlsx'

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

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(10)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#FABC51')

			grand_total = workbook.add_format({'bold': 1})
			grand_total.set_text_wrap()
			grand_total.set_font_size(10)
			grand_total.set_align('center')
			grand_total.set_align('vcenter')
			grand_total.set_border(style=1)
			grand_total.set_bg_color('#E49000')

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

			# Борлуулагчаар харуулах sheet
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.set_zoom(65)
			worksheet.write(0,2, u"MONTHLY PERFORMANCE REPORT", h1)

			# TABLE HEADER
			row = 1
			worksheet.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+1, 2, u"Техникийн модел", header_wrap)
			worksheet.set_column(2, 2, 25)
			worksheet.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column(3, 3, 10)
			# Сарын өдрүүд зурах
			for i in range(4,days+4):
				worksheet.write(row+1, i, i-3, header_wrap)
			worksheet.set_column(4, days+3, 4)
			worksheet.merge_range(row, 4, row, days+3, str(month)+u"-р сар", header_wrap)
			col = days+4
			# --------------
			worksheet.merge_range(row, col, row+1, col, u"Хийгдэх ажил", header_wrap)
			worksheet.set_column(col, col, 25)
			worksheet.merge_range(row, col+1, row+1, col+1, u"Засварын цаг", header_wrap)
			worksheet.merge_range(row, col+2, row+1, col+2, u"Төлөвлөсөн ТББ %", header_wrap)
			worksheet.merge_range(row, col+3, row+1, col+3, u"Бодит ТББ %", header_wrap)
			worksheet.set_column(col+2, col+3, 12)
			worksheet.freeze_panes(3, 4)

			row = 3
			number = 1
			type_dict = {}
			row_start = 3
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

			for line in pers:
				if not first and type_name != line['technic_type']:
					worksheet.merge_range(row, 0, row, col, u'НИЙТ: '+type_name, sub_total)
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

					worksheet.write_formula(row, col+1,
						'{=SUM('+self._symbol(row,4) +':'+ self._symbol(row, days+3)+')}', contest_center)
					p_tbbk = technic.get_technic_planned_tbbk(ds, de)['tbbk'] or 0
					worksheet.write(row, col+2, round(p_tbbk,2), contest_center)

					tbbk = technic.get_technic_tbbk(ds, de)['tbbk'] or 0
					worksheet.write(row, col+3, round(tbbk,2), contest_center)

					sub_totals_address[3].append(self._symbol(row,col+3))

					number += 1
					row += 1

				rr = technic_dict[line['technic_name']]
				cc = int(line['dddd'].strftime('%Y-%m-%d')[8:])+3
				worksheet.write(rr, cc, line['work_time'], contest_center)

				# # Тайлбар
				# txt = ','.join(line['description'])
				# if rr in descriptions_dict:
				# 	descriptions_dict[rr] += ', '+txt
				# else:
				# 	descriptions_dict[rr] = txt

				first = False
				type_name = line['technic_type']

			# Last Subtotal
			worksheet.merge_range(row, 0, row, col, u'НИЙТ: '+type_name, sub_total)
			type_dict[type_name] = [row_start, row]
			row += 1
			# Нийт тайлбар зурах
			# for key in descriptions_dict:
			# 	worksheet.write(key, col, descriptions_dict[key], contest_left)

			# Sub total
			for key in type_dict:
				rr = type_dict[key][1]
				row_start = type_dict[key][0]
				worksheet.write_formula(rr, col+1,
					'{=SUM('+self._symbol(row_start,col+1) +':'+ self._symbol(rr-1, col+1)+')}', sub_total)
				worksheet.write_formula(rr, col+2,
					'{=ROUND(AVERAGE('+self._symbol(row_start,col+2) +':'+ self._symbol(rr-1, col+2)+'),2)}', sub_total)
				worksheet.write_formula(rr, col+3,
					'{=ROUND(AVERAGE('+self._symbol(row_start,col+3) +':'+ self._symbol(rr-1, col+3)+'),2)}', sub_total)

				sub_totals_address[1].append(self._symbol(rr,col+1))
				sub_totals_address[2].append(self._symbol(rr,col+2))

			# Grand total
			worksheet.merge_range(row, 0, row, col, u'Нийт ТББК:', grand_total)
			worksheet.write_formula(row, col+1,'{=IFERROR('+ '+'.join(sub_totals_address[1]) +',0)}', grand_total)
			ptbbk = '{=IFERROR(ROUND(('+ '+'.join(sub_totals_address[2]) +')/%d,2),0)}' % len(sub_totals_address[2])
			worksheet.write_formula(row, col+2, ptbbk, grand_total)
			ttbbk = '{=IFERROR(ROUND(('+ '+'.join(sub_totals_address[3]) +')/%d,2),0)}' % len(sub_totals_address[3])
			worksheet.write_formula(row, col+3, ttbbk, grand_total)
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



