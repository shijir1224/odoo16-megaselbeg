# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from calendar import monthrange

import time
import xlsxwriter
from io import BytesIO
import base64

import logging
_logger = logging.getLogger(__name__)

class WizardMaintenanceYearTbbk(models.TransientModel):
	_name = "wizard.maintenance.year.tbbk"  
	_description = "wizard.maintenance.year.tbbk"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	
	# Жилийн Budget Татах
	def export_budget_report(self):
		if self.date_start <= self.date_end:
			query = """
				SELECT 
					tt.report_order as report_order,
					tt.technic_type as technic_type,
					tt.technic_name as technic_name,
					tt.technic_id, 
					tt.mm,
					tt.report_type as report_type,
					sum(tt.amount) as amount,
					array_agg(tt.description) as description
				FROM ( 
					SELECT
						t.report_order as report_order,
						t.technic_type as technic_type,
						t.program_code as technic_name,
						to_char(ll.date_plan,'YYYY-mm') as mm,
						'report_pm' as report_type,
						ll.technic_id as technic_id,
						ll.total_amount as amount,
						'' as description
					FROM maintenance_plan_generator_line as ll
					LEFT JOIN maintenance_plan_generator as pl on pl.id = ll.parent_id
					LEFT JOIN technic_equipment as t on (t.id = ll.technic_id)
					WHERE pl.forecast_type = 'year' and
						 pl.state in ('confirmed','done') and
						 ll.date_plan >= '%s' and
						 ll.date_plan <= '%s'
					UNION ALL
					SELECT
						t.report_order as report_order,
						t.technic_type as technic_type,
						t.program_code as technic_name,
						to_char(lll.date_plan,'YYYY-mm') as mm,
						'report_overhaul' as report_type,
						lll.technic_id as technic_id,
						lll.amount as amount,
						lll.description as description
					FROM maintenance_long_term_line as lll
					LEFT JOIN maintenance_long_term as ll on ll.id = lll.parent_id
					LEFT JOIN technic_equipment as t on (t.id = lll.technic_id)
					WHERE (lll.repair_it = 't' or lll.repair_it = true or lll.is_d_check = 't' and lll.is_d_check = true or lll.last_maintenance = 'main_service') and
						 ll.state in ('confirmed','done') and
						 lll.date_plan >= '%s' and
						 lll.date_plan <= '%s'
					UNION ALL
					SELECT
						t.report_order as report_order,
						t.technic_type as technic_type,
						t.name as technic_name,
						to_char(llll.date_plan,'YYYY-mm') as mm,
						'report_tire' as report_type,
						llll.technic_id as technic_id,
						llll.amount as amount,
						'Change tire' as description
					FROM tire_forecast_line as llll
					LEFT JOIN tire_plan_generator as tire on tire.id = llll.parent_id
					LEFT JOIN technic_equipment as t on (t.id = llll.technic_id)
					WHERE 
						 tire.state in ('confirmed','done') and
						 llll.date_plan >= '%s' and
						 llll.date_plan <= '%s'
				) as tt
				GROUP BY tt.report_order, tt.technic_type, tt.technic_name, tt.technic_id, tt.mm, tt.report_type
				ORDER BY tt.report_order, tt.technic_type, tt.technic_name, tt.mm, tt.report_type
			""" % (self.date_start, self.date_end, self.date_start, self.date_end, self.date_start, self.date_end)
			print ('===', query)
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			if not query_result:
				raise UserError(_(u'Жилийн төлөвлөгөө олдсонгүй!'))

			# GET dates
			query_dates = """
				SELECT to_char(generate_series('%s', '%s', '1 month'::interval)::date,'YYYY-mm') as mm
				GROUP BY mm
				ORDER BY mm
			""" % (self.date_start, self.date_end)
			self.env.cr.execute(query_dates)
			dates_result = self.env.cr.dictfetchall()

			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'maintenance_year_budget.xlsx'

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
			sub_total.set_align('right')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(10)
			sub_total_90.set_align('right')
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
			# contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.0')
			contest_right.set_bg_color('#F7EE5E')

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

			format_hidden = workbook.add_format({'hidden': True})

			# 1 SHEET ========================================================
			worksheet = workbook.add_worksheet(u'НЭГТГЭЛ')
			worksheet.set_zoom(75)
			worksheet.write(0,1, u"ЖИЛИЙН ТӨСӨВ", h1)

			# TABLE HEADER
			row = 1
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 5)
			worksheet.write(row, 1, u"EQUIPMENT MODEL", header_wrap)
			worksheet.write(row, 2, u"PARK №", header_wrap)
			worksheet.set_column(1, 2, 20)
			worksheet.write(row, 3, u"Мото цаг", format_hidden)
			worksheet.set_column('D:D', None, None, {'hidden': True})

			worksheet.write(row, 4, u"DESCRIPTION", header_wrap)
			worksheet.set_column(4, 4, 15)
			worksheet.freeze_panes(2, 4)
			# Сарын өдрүүд зурах
			col = 5
			col_dict = {}
			for ll in dates_result:
				worksheet.write(row, col, ll['mm'].strftime("%Y-%m"), header_wrap)
				col_dict[ll['mm']] = col
				col += 1
			worksheet.set_column(5, col-1, 12)
			worksheet.write(row, col, u"TOTAL", header_wrap)
			worksheet.set_column(col, col, 20)
			col += 1
			
			row = 2
			number = 1
			technic_dict = {}
			total_pm_amount = 0
			total_tire_amount = 0
			total_overhaul_amount = 0
			for line in query_result:
				if line['technic_id'] not in technic_dict:
					worksheet.merge_range(row, 0, row+2, 0, number, number_right)
					technic = self.env['technic.equipment'].browse(line['technic_id'])
					worksheet.merge_range(row, 1, row+2, 1, technic.park_number, contest_left)
					worksheet.merge_range(row, 2, row+2, 2, technic.program_code, contest_center)
					worksheet.write(row, 4, "PM-зардал", contest_left)
					worksheet.write(row+1, 4, "TIRE-зардал", contest_left)
					worksheet.write(row+2, 4, "OVERHAUL-зардал", contest_left)
					technic_dict[ line['technic_id'] ] = row
					number += 1
					row += 3
				
				r = technic_dict[ line['technic_id'] ]
				if line['report_type'] == 'report_pm':
					r = technic_dict[ line['technic_id'] ]
					total_pm_amount += line['amount']
				elif line['report_type'] == 'report_tire':
					r += 1
					total_tire_amount += line['amount']
				elif line['report_type'] == 'report_overhaul':
					r += 2
					total_overhaul_amount += line['amount']

				c = col_dict[ line['mm'] ]
				worksheet.write(r, c, line['amount'], contest_right0)
			# TOTAL =================================================
			for c in range(5, col-1):
				worksheet.write_formula(row, c, 
					'{=SUM('+self._symbol(2, c) +':'+ self._symbol(row-1, c)+')}', sub_total)
			row += 1
			for r in range(2, row):
				worksheet.write_formula(r, col-1, 
					'{=SUM('+self._symbol(r, 5) +':'+ self._symbol(r, col-2)+')}', sub_total)
			worksheet.write_formula(r, col-1, 
					'{=SUM('+self._symbol(r, 5) +':'+ self._symbol(r, col-2)+')}', sub_total)
			row += 1
			worksheet.merge_range(row, col-3, row, col-2, 'НИЙТ PM-зардал',sub_total)
			worksheet.write(row, col-1, total_pm_amount,sub_total)
			worksheet.merge_range(row+1, col-3, row+1, col-2, 'НИЙТ TIRE-зардал',sub_total)
			worksheet.write(row+1, col-1, total_tire_amount,sub_total)
			worksheet.merge_range(row+2, col-3, row+2, col-2, 'НИЙТ OVERHAUL-зардал',sub_total)
			worksheet.write(row+2, col-1, total_overhaul_amount,sub_total)
			# Хэрэглээний зардал олох
			total_amount = 0
			tmp = self.env['maintenance.year.other.expense'].search([
				('state','=','confirmed'),
				('date_year','>=',self.date_start),
				('date_year','<=',self.date_end)
				], limit=1)
			if tmp:
				total_amount = tmp.total_amount
			worksheet.merge_range(row+4, col-3, row+4, col-2, 'ЗАСВАР ХЭРЭГЛЭЭНИЙ-зардал',sub_total)
			worksheet.write(row+4, col-1, total_amount,sub_total)
			# НИЙТ ЗАРДАЛ
			worksheet.merge_range(row+5, col-3, row+5, col-2, 'НИЙТ ЗАСВАР ЖИЛИЙН-ТӨСӨВ',sub_total)
			worksheet.write_formula(row+5, col-1, '{='+self._symbol(row, col-1)+'+'+self._symbol(row+1, col-1)+'+'+self._symbol(row+2, col-1)+'+'+self._symbol(row+4, col-1)+'}',sub_total)
			
			# SHEET 2 ===============================================
			worksheet_2 = workbook.add_worksheet(u'PARTS')
			worksheet_2.set_zoom(75)
			worksheet_2.write(0,1, u"ЖИЛИЙН ТӨСӨВ", h1)

			# TABLE HEADER
			row = 0
			worksheet_2.write(row, 0, u"EQUIPMENT", header_wrap)
			worksheet_2.set_column(0, 0, 20)
			worksheet_2.write(row, 1, u"№", header)
			worksheet_2.set_column(1, 1, 5)
			worksheet_2.write(row, 2, u"DESCRIPTION", header_wrap)
			worksheet_2.set_column(2, 2, 40)
			worksheet_2.write(row, 3, u"PARTS OPTION", header_wrap)
			worksheet_2.write(row, 4, u"PART NUMBER", header_wrap)
			worksheet_2.set_column(3, 4, 15)
			worksheet_2.write(row, 5, u"QTY", header_wrap)
			worksheet_2.write(row, 6, u"UNIT PRICE", header_wrap)
			worksheet_2.write(row, 7, u"TOAL", header_wrap)
			worksheet_2.set_column(6, 7, 18)
			worksheet_2.freeze_panes(2, 4)
			query = """
				SELECT
					t.report_order as report_order,
					t.technic_type as technic_type,
					t.program_code as technic_name,
					lll.technic_id as technic_id,
					lll.component_id as component_id,
					lll.last_maintenance as last_maintenance,
					count(*) as qty,
					sum(lll.amount) as amount
				FROM maintenance_long_term_line as lll
				LEFT JOIN maintenance_long_term as ll on ll.id = lll.parent_id
				LEFT JOIN technic_equipment as t on (t.id = lll.technic_id)
				WHERE (lll.repair_it = 't' or lll.repair_it = true or lll.is_d_check = 't' and lll.is_d_check = true) and
					 ll.state in ('confirmed','done') and
					 lll.date_plan >= '%s' and
					 lll.date_plan <= '%s'
				GROUP BY t.report_order, t.technic_type, t.program_code, lll.technic_id, lll.component_id, lll.last_maintenance
				ORDER BY t.report_order, t.technic_type, t.program_code, lll.component_id
			""" % (self.date_start, self.date_end)
			# print query
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			if query_result:
				row = 1
				merge_row = row
				number = 0
				first = True
				technic_id = 0
				technic_name = ''
				total_amount = 0
				for line in query_result:
					if technic_id != line['technic_id'] and not first:
						worksheet_2.merge_range(merge_row, 0, row-1, 0, technic_name, contest_left)
						worksheet_2.write(row, 4, "НИЙТ", contest_right)
						worksheet_2.write_formula(row, 5, 
							'{=SUM('+self._symbol(merge_row, 5) +':'+ self._symbol(row-1, 5)+')}', contest_right)
						worksheet_2.write_formula(row, 6, 
							'{=SUM('+self._symbol(merge_row, 6) +':'+ self._symbol(row-1, 6)+')}', contest_right)
						worksheet_2.write_formula(row, 7, 
							'{=SUM('+self._symbol(merge_row, 7) +':'+ self._symbol(row-1, 7)+')}', contest_right)
						row += 1
						merge_row = row
						number = 1

					technic = self.env['technic.equipment'].browse(line['technic_id'])
					worksheet_2.write(row, 0, technic.park_number, contest_left)
					worksheet_2.write(row, 1, number, number_right)
					comp = self.env['technic.component.part'].browse(line['component_id'])
					worksheet_2.write(row, 2, comp.display_name, contest_left)
					worksheet_2.write(row, 3, line['last_maintenance'], contest_center)
					worksheet_2.write(row, 4, comp.product_id.default_code, contest_center)
					worksheet_2.write(row, 5, line['qty'], contest_right0)
					worksheet_2.write(row, 6, line['amount']/line['qty'], contest_right0)
					worksheet_2.write(row, 7, line['amount'], contest_right0)
					total_amount += line['amount']
					number += 1
					row += 1
					first = False
					technic_id = line['technic_id']
					technic_name = technic.park_number
				# Total =====
				worksheet_2.write(row, 6, "НИЙТ: ", sub_total)
				worksheet_2.write(row, 7, total_amount, sub_total)

			# SHEET 3 ====================================================
			categ_ids = self.env['product.category'].search([('id','child_of',13)]).mapped('id')
			if len(categ_ids) > 1:
				categ_ids = str(tuple(categ_ids))
			elif len(categ_ids) == 0:
				categ_ids = '(%s)' % categ_ids[0]
			else:
				categ_ids = '(-1)'
			query = """
				SELECT
					to_char(ll.date_plan,'YYYY-mm') as mm,
					pc.name as pc_name, 
					lll.material_id as product_id,
					sum(lll.qty) as qty
				FROM maintenance_pm_material_line as lll
				LEFT JOIN maintenance_plan_generator_line as ll on ll.id = lll.generator_id
				LEFT JOIN maintenance_plan_generator as pl on pl.id = ll.parent_id
				LEFT JOIN product_product as pp on pp.id = lll.material_id
				LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id 
				LEFT JOIN product_category as pc on pc.id = pt.categ_id
				WHERE pl.forecast_type = 'year' and
					 pl.state in ('confirmed','done') and
					 pt.categ_id in %s and 
					 ll.date_plan >= '%s' and
					 ll.date_plan <= '%s'
				GROUP BY mm, pc_name, lll.material_id
				ORDER BY mm, pc_name
			""" % (categ_ids, self.date_start, self.date_end)
			# print '===', query
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			if not query_result:
				raise UserError(_(u'Жилийн төлөвлөгөө олдсонгүй!'))
			worksheet_3 = workbook.add_worksheet(u'OIL нэгтгэл')
			worksheet_3.set_zoom(75)
			worksheet_3.write(0,1, u"ЖИЛИЙН ТӨСӨВ", h1)

			# TABLE HEADER
			row = 1
			worksheet_3.write(row, 0, u"№", header)
			worksheet_3.set_column(0, 0, 5)
			worksheet_3.write(row, 1, u"ТОСНЫ ТӨРӨЛ", header_wrap)
			worksheet_3.write(row, 2, u"ТОСНЫ БРЕНД", header_wrap)
			worksheet_3.set_column(1, 1, 20)
			worksheet_3.set_column(2, 2, 35)
			worksheet_3.freeze_panes(2, 4)
			# Сарын өдрүүд зурах
			col = 3
			col_dict = {}
			for ll in dates_result:
				worksheet_3.write(row, col, ll['mm'].strftime("%Y-%m"), header_wrap)
				col_dict[ll['mm']] = col
				col += 1
			worksheet_3.set_column(3, col-1, 10)
			worksheet_3.write(row, col, u"TOTAL", header_wrap)
			worksheet_3.set_column(col, col, 20)
			col += 1
			
			row = 2
			number = 1
			product_dict = {}
			for line in query_result:
				if line['product_id'] not in product_dict:
					worksheet_3.write(row, 0, number, number_right)
					product = self.env['product.product'].browse(line['product_id'])
					worksheet_3.write(row, 1, line['pc_name'], contest_left)
					worksheet_3.write(row, 2, product.display_name, contest_left)
					product_dict[ line['product_id'] ] = row
					number += 1
					row += 1
				
				r = product_dict[ line['product_id'] ]
				c = col_dict[ line['mm'] ]
				worksheet_3.write(r, c, line['qty'], contest_right0)
			# TOTAL =================================================
			for c in range(3, col-1):
				worksheet_3.write_formula(row, c, 
					'{=SUM('+self._symbol(2, c) +':'+ self._symbol(row-1, c)+')}', sub_total)
			row += 1
			for r in range(2, row):
				worksheet_3.write_formula(r, col-1, 
					'{=SUM('+self._symbol(r, 3) +':'+ self._symbol(r, col-2)+')}', sub_total)

			# SHEET 4 ====================================================
			categ_ids = self.env['product.category'].search([('id','child_of',5)]).mapped('id')
			if len(categ_ids) > 1:
				categ_ids = str(tuple(categ_ids))
			elif len(categ_ids) == 0:
				categ_ids = '(%s)' % categ_ids[0]
			else:
				categ_ids = '(-1)'
			query = """
				SELECT
					to_char(ll.date_plan,'YYYY-mm') as mm,
					lll.material_id as product_id,
					sum(lll.qty) as qty
				FROM maintenance_pm_material_line as lll
				LEFT JOIN maintenance_plan_generator_line as ll on ll.id = lll.generator_id
				LEFT JOIN maintenance_plan_generator as pl on pl.id = ll.parent_id
				LEFT JOIN product_product as pp on pp.id = lll.material_id
				LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id 
				WHERE pl.forecast_type = 'year' and
					 pl.state in ('confirmed','done') and
					 pt.categ_id in %s and 
					 ll.date_plan >= '%s' and
					 ll.date_plan <= '%s'
				GROUP BY mm, lll.material_id
				ORDER BY mm
			""" % (categ_ids, self.date_start, self.date_end)
			# print '===', query
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			if not query_result:
				raise UserError(_(u'Жилийн төлөвлөгөө олдсонгүй!'))
			worksheet_4 = workbook.add_worksheet(u'FILTER нэгтгэл')
			worksheet_4.set_zoom(75)
			worksheet_4.write(0,1, u"ЖИЛИЙН ТӨСӨВ", h1)

			# TABLE HEADER
			row = 1
			worksheet_4.write(row, 0, u"№", header)
			worksheet_4.set_column(0, 0, 5)
			worksheet_4.write(row, 1, u"PART NAME", header_wrap)
			worksheet_4.set_column(1, 1, 30)
			worksheet_4.write(row, 2, u"PART NUMBER", header_wrap)
			worksheet_4.set_column(2, 2, 15)
			worksheet_4.freeze_panes(2, 4)
			# Сарын өдрүүд зурах
			col = 3
			col_dict = {}
			for ll in dates_result:
				worksheet_4.write(row, col, ll['mm'].strftime("%Y-%m"), header_wrap)
				col_dict[ll['mm']] = col
				col += 1
			worksheet_4.set_column(3, col-1, 10)
			worksheet_4.write(row, col, u"TOTAL", header_wrap)
			worksheet_4.set_column(col, col, 20)
			col += 1
			
			row = 2
			number = 1
			product_dict = {}
			for line in query_result:
				if line['product_id'] not in product_dict:
					worksheet_4.write(row, 0, number, number_right)
					product = self.env['product.product'].browse(line['product_id'])
					worksheet_4.write(row, 1, product.name, contest_left)
					worksheet_4.write(row, 2, product.default_code, contest_center)
					product_dict[ line['product_id'] ] = row
					number += 1
					row += 1
				
				r = product_dict[ line['product_id'] ]
				c = col_dict[ line['mm'] ]
				worksheet_4.write(r, c, line['qty'], contest_right0)
			# TOTAL =================================================
			for c in range(3, col-1):
				worksheet_4.write_formula(row, c, 
					'{=SUM('+self._symbol(2, c) +':'+ self._symbol(row-1, c)+')}', sub_total)
			row += 1
			for r in range(2, row):
				worksheet_4.write_formula(r, col-1, 
					'{=SUM('+self._symbol(r, 3) +':'+ self._symbol(r, col-2)+')}', sub_total)

			# SHEET 5 ====================================================
			query = """
				SELECT
					t.report_order as report_order,
					t.technic_type as technic_type,
					t.program_code as technic_name,
					to_char(llll.date_plan,'YYYY-mm') as mm,
					llll.product_id as product_id,
					sum(llll.qty) as qty
				FROM tire_forecast_line as llll
				LEFT JOIN tire_plan_generator as tire on tire.id = llll.parent_id
				LEFT JOIN technic_equipment as t on (t.id = llll.technic_id)
				WHERE 
					 tire.state in ('confirmed','done') and
					 llll.date_plan >= '%s' and
					 llll.date_plan <= '%s'
				GROUP BY report_order, technic_type, technic_name, mm, product_id
				ORDER BY report_order, technic_type, technic_name, mm
			""" % (self.date_start, self.date_end)
			# print '===', query
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			if not query_result:
				raise UserError(_(u'Дугуйн жилийн төлөвлөгөө олдсонгүй!'))
			worksheet_5 = workbook.add_worksheet(u'TIRE нэгтгэл')
			worksheet_5.set_zoom(75)
			worksheet_5.write(0,1, u"ДУГУЙН ЖИЛИЙН ТӨСӨВ", h1)

			# TABLE HEADER
			row = 1
			worksheet_5.write(row, 0, u"№", header)
			worksheet_5.set_column(0, 0, 5)
			worksheet_5.write(row, 1, u"ПАРК ДУГААР", header_wrap)
			worksheet_5.set_column(1, 1, 18)
			worksheet_5.write(row, 2, u"PRODUCT", header_wrap)
			worksheet_5.set_column(2, 2, 35)
			worksheet_5.freeze_panes(2, 4)
			# Сарын өдрүүд зурах
			col = 3
			col_dict = {}
			for ll in dates_result:
				worksheet_5.write(row, col, ll['mm'].strftime("%Y-%m"), header_wrap)
				col_dict[ll['mm']] = col
				col += 1
			worksheet_5.set_column(3, col-1, 10)
			worksheet_5.write(row, col, u"TOTAL", header_wrap)
			worksheet_5.set_column(col, col, 20)
			col += 1
			
			row = 2
			number = 1
			technic_dict = {}
			for line in query_result:
				if line['technic_name'] not in technic_dict:
					worksheet_5.write(row, 0, number, number_right)
					product = self.env['product.product'].browse(line['product_id'])
					worksheet_5.write(row, 1, line['technic_name'], contest_left)
					worksheet_5.write(row, 2, product.name, contest_center)
					technic_dict[ line['technic_name'] ] = row
					number += 1
					row += 1
				
				r = technic_dict[ line['technic_name'] ]
				c = col_dict[ line['mm'] ]
				worksheet_5.write(r, c, line['qty'], contest_right0)
			# TOTAL =================================================
			for c in range(3, col-1):
				worksheet_5.write_formula(row, c, 
					'{=SUM('+self._symbol(2, c) +':'+ self._symbol(row-1, c)+')}', sub_total)
			row += 1
			for r in range(2, row):
				worksheet_5.write_formula(r, col-1, 
					'{=SUM('+self._symbol(r, 3) +':'+ self._symbol(r, col-2)+')}', sub_total)

			# SHEET 6 ====================================================
			worksheet_6 = workbook.add_worksheet(u'ХЭРЭГЛЭЭНИЙ нэгтгэл')
			worksheet_6.set_zoom(90)
			worksheet_6.write(0,1, u"ХЭРЭГЛЭЭНИЙ ЗАСВАРЫН ЖИЛИЙН ТӨСӨВ", h1)

			# TABLE HEADER
			row = 1
			worksheet_6.write(row, 0, u"№", header)
			worksheet_6.set_column(0, 0, 5)
			worksheet_6.write(row, 1, u"НЭР", header_wrap)
			worksheet_6.set_column(1, 1, 18)
			worksheet_6.write(row, 2, u"ТОО ХЭМЖЭЭ", header_wrap)
			worksheet_6.write(row, 3, u"МӨНГӨН ДҮН", header_wrap)
			worksheet_6.set_column(2, 3, 16)
			worksheet_6.freeze_panes(2, 4)
			lines = self.env['maintenance.year.other.expense.line'].search([
				('parent_id.state','=','confirmed'),
				('parent_id.date_year','>=',self.date_start),
				('parent_id.date_year','<=',self.date_end)], order='name')
			row = 2
			number = 1
			for ll in lines:
				worksheet_6.write(row, 0, number, contest_left)
				worksheet_6.write(row, 1, ll.name, contest_left)
				worksheet_6.write(row, 2, ll.qty, contest_right0)
				worksheet_6.write(row, 3, ll.amount, contest_right0)
				row += 1
				number += 1
			# TOTAL ===================
			worksheet_6.write(row, 1, "НИЙТ: ", sub_total)
			worksheet_6.write_formula(row, 2, 
				'{=SUM('+self._symbol(2, 2) +':'+ self._symbol(row-1, 2)+')}', sub_total)
			worksheet_6.write_formula(row, 3, 
				'{=SUM('+self._symbol(2, 3) +':'+ self._symbol(row-1, 3)+')}', sub_total)

			# ------------------------------------------++++++++++++++++++++++++++++++++++
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}

	# TBBK олох
	def _get_tbbk(self, norm, work_time, mm):
		# Нийт өдрийг олох
		days = monthrange(int(mm[:4]),int(mm[5:7]))[1]
		font_times = norm*days
		tbbk = ((font_times-work_time)*100) / font_times
		if tbbk < 0:
			_logger.info("---TBBK ====== %s %d", mm, tbbk)
		return tbbk
	# Жилийн ТББК Татах
	
	def export_report(self):
		if self.date_start <= self.date_end:
			results = self.env['maintenance.plan.generator']._get_year_tbbk_excel(self.date_start, self.date_end)
			if not results:
				raise UserError(_(u'Жилийн төлөвлөгөө олдсонгүй!'))

			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'maintenance_year_tbbk.xlsx'

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
			# contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.0')
			contest_right.set_bg_color('#F7EE5E')

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

			worksheet = workbook.add_worksheet(u'Тайлан: YEAR')
			worksheet.set_zoom(80)
			worksheet.write(0,1, u"ЖИЛИЙН ТББК", h1)

			# TABLE HEADER
			row = 1
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"ТYPE", header_wrap)
			worksheet.write(row, 2, u"Парк №", header_wrap)
			worksheet.set_column(1, 2, 9)
			worksheet.write(row, 3, u"Техникийн нэр", header_wrap)
			worksheet.set_column(3, 3, 22)
			worksheet.freeze_panes(2, 4)

			col = 4
			row = 2
			month_dict = {}
			technic_dict = {}
			tbbk_dict = {}
			number = 1
			technic = False
			percents = []
			for line in results:
				if line['mm'] not in month_dict:
					worksheet.merge_range(1, col, 1, col+1, line['mm'], header_wrap)
					month_dict[ line['mm'] ] = col
					col += 2
				if line['technic_id'] not in technic_dict:
					technic = self.env['technic.equipment'].browse(line['technic_id'])
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 1, line['technic_type'], contest_center)
					worksheet.write(row, 2, technic.program_code, contest_left)
					worksheet.write(row, 3, technic.park_number, contest_left)
					technic_dict[ line['technic_id'] ] = row
					row += 1
					number += 1

				norm = technic.technic_setting_id.work_time_per_day or 1
				tbbk = self._get_tbbk(norm, line['work_time'], line['mm'])
				
				r = technic_dict[ line['technic_id'] ]
				c = month_dict[ line['mm'] ]
				worksheet.write(r, c, line['work_time'], contest_right0)
				worksheet.write(r, c+1, tbbk, contest_right)
				if r in tbbk_dict:
					tbbk_dict[r].append(tbbk)
				else:
					tbbk_dict[r] = [tbbk]

			# Техникийн НИЙТ ТББК
			worksheet.write(1, col, u"НИЙТ ТББК", header_wrap)
			for r in tbbk_dict:
				worksheet.write(r, col, sum(tbbk_dict[r])/len(tbbk_dict[r]), contest_right)
			col += 1
			# Сарын НИЙТ ТББК
			worksheet.write(row, 3, u"НИЙТ ТББК", header_wrap)
			c = 5
			while c < col:
				worksheet.write_formula(row, c, 
						'{=AVERAGE('+self._symbol(2,c) +':'+ self._symbol(row-1, c)+')}', contest_right)
				c += 2
			# ------------------------------------------
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol







