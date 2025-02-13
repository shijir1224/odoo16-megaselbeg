# -*- coding: utf-8 -*-


from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import calendar
import time
import base64
import xlsxwriter
from io import BytesIO
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

class mining_plan_view(models.TransientModel):
	_name = 'mining.plan.view'
	_description = 'mining plan view'

	@api.model
	def _get_default_branch(self):
		if self.env.user.branch_id:
			return self.env.user.branch_id.id
		else:
			return False
	
	@api.model
	def _default_view_type(self):
		if self.env.context.get('view_type_exca_dump',False):
			return self.env.context.get('view_type_exca_dump',False)
		else:
			return False

	@api.model
	def _default_plan_type(self):
		if self.env.context.get('plan_type',False):
			return self.env.context.get('plan_type',False)
		else:
			return False
	# Columns
	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо', default=fields.Date.context_today)
	branch_id = fields.Many2one('res.branch', string=u'Салбар', default=_get_default_branch)
	group_type = fields.Selection([('day','Day'),('month','Month'),('year','Year')], string=u'Group type', default='day')
	view_type = fields.Selection([('exca','Exca'),('dump','Dump'),('drill','Drill')], string=u'View type', default=_default_view_type)
	plan_type = fields.Selection([('tsag_ashiglalt','tsag_ashiglalt'),('ajillah_tsag','ajillah_tsag'),('buteel','buteel')], string=u'Plan type', default=_default_plan_type)
	
	def view_plan(self):
		pass
	
	@api.onchange('date_start','date_end')
	def onch_date(self):
		if self.date_start and self.date_end:
			diff_date = (self.date_end-self.date_start)
			if diff_date.days<=365 and diff_date.days>=45:
				self.group_type = 'month'
			elif diff_date.days>=366:
				self.group_type = 'month'
		else:
			self.group_type = 'day'

	def get_plan_actual(self, group_type, date, tech_id, vals):
		def get_date(item_date):
			item_date = datetime.strptime(str(item_date), "%Y-%m-%d")
			if group_type=='month':
				item_date = item_date.strftime( "%Y-%m")
			elif group_type=='year':
				item_date = item_date.strftime( "%Y")
			else:
				item_date = item_date.strftime("%Y-%m-%d")
			return str(item_date)
		plan = 0
		actual = 0
		for item in vals:
			if str(item['technic_id'])==str(tech_id) and get_date(item['date']) == str(date):
				plan += float(item['js_plan'])
				print("item['js_actual']",item['js_actual'], type(item['js_actual']))
				actual += float(item['js_actual'])
		
		datas = {
			'plan': plan,
			'actual': actual,
		}
		return datas

	def get_buteel(self, date_start, date_end, branch_id, view_type_where):
		query = """
			SELECT
				te.report_order as report_order,
				tt.technic_type as technic_type,
				te.name as technic_name,
				te.id as technic_id,
				tt.date as date,
				coalesce(sum(tt.sum_m3_plan),0) as js_plan,
				coalesce(sum(tt.sum_m3),0) as js_actual,
				coalesce(sum(tt.sum_m3_sur),0) as sum_m3_sur
				from mining_production_report as tt
				left join technic_equipment as te on (te.id=tt.excavator_id or te.id=tt.dump_id)
				where tt.date>='{0}' and tt.date<='{1}' and tt.branch_id='{2}'
				and te.id is not null {3}
				group by 1,2,3,4,5
		""".format(str(date_start), str(date_end), branch_id, view_type_where)
		self.env.cr.execute(query)
		print('===  get_buteel  ', query)
		plans = self.env.cr.dictfetchall()
		return plans

	def get_tsag_ashiglalt(self, date_start, date_end, branch_id, view_type_where):
		# case when (coalesce(sum(tt.plan_run_hour),0)+coalesce(sum(tt.plan_repair_hour))>=coalesce(sum(tt.sum_repair_time),0) then (coalesce(sum(tt.plan_run_hour),0)+coalesce(sum(tt.plan_repair_hour))-coalesce(sum(tt.sum_repair_time),0) else 0 end as js_plan,
		# case when coalesce(sum(tt.plan_run_hour),0)>=coalesce(sum(tt.sum_repair_time),0) then coalesce(sum(tt.plan_run_hour),0)-coalesce(sum(tt.sum_repair_time),0) else 0 end as js_plan,
		query = """
			SELECT
				te.report_order as report_order,
				te.technic_type as technic_type,
				te.name as technic_name,
				te.id as technic_id,
				tt.date as date,
				case when (coalesce(sum(tt.plan_run_hour),0)+coalesce(sum(tt.plan_repair_hour)))>=coalesce(sum(tt.sum_repair_time),0) then (coalesce(sum(tt.plan_run_hour),0)+coalesce(sum(tt.plan_repair_hour)))-coalesce(sum(tt.sum_repair_time),0) else 0 end as js_plan,
				coalesce(sum(tt.sum_production_time),0) as js_actual
				from report_mining_technic_analyze as tt
				left join technic_equipment as te on (te.id=tt.technic_id)
				where tt.date>='{0}' and tt.date<='{1}' and tt.branch_id='{2}'
				and te.id is not null {3}
				group by 1,2,3,4,5
		""".format(str(date_start), str(date_end), branch_id, view_type_where)
		self.env.cr.execute(query)
		print('===  get_tsag_ashiglalt  ', query)
		plans = self.env.cr.dictfetchall()
		return plans
	
	def get_ajillah_tsag(self, date_start, date_end, branch_id, view_type_where):
		query = """
			SELECT
				te.report_order as report_order,
				te.technic_type as technic_type,
				te.name as technic_name,
				te.id as technic_id,
				tt.date as date,
				coalesce(sum(tt.plan_run_hour),0) as js_plan,
				coalesce(sum(tt.plan_run_hour_util),0) as js_actual
				from report_mining_technic_analyze as tt
				left join technic_equipment as te on (te.id=tt.technic_id)
				where tt.date>='{0}' and tt.date<='{1}' and tt.branch_id='{2}'
				and te.id is not null {3}
				group by 1,2,3,4,5
		""".format(str(date_start), str(date_end), branch_id, view_type_where)
		self.env.cr.execute(query)
		print('===  get_ajillah_tsag  ', query)
		plans = self.env.cr.dictfetchall()
		return plans

	def too(self, x):
		if x%1 == 0:
			return "{0:,.0f}".format(x)
		else:
			return "{0:,.1f}".format(x)

	def get_datas(self, date_start, date_end, branch_id, group_type, view_type, plan_type, context=None):
		datas = {}
		technic_rows = []
		date_cols = []
		date_cols_real = []
		if date_start and date_end and date_start <= date_end:
			sd = datetime.strptime(date_start, "%Y-%m-%d")
			ed = datetime.strptime(date_end, "%Y-%m-%d")
			view_type_where =''
			if view_type=='exca':
				view_type_where =" and te.technic_type in ('excavator','loader') "
			elif view_type=='dump':
				view_type_where =" and te.technic_type in ('dump') "
			elif view_type == 'drill':
				view_type_where =" and te.technic_type in ('drill') "
			print ('view_type_where',view_type_where)
			# days = (ed-sd).days+1
			
			if plan_type=='tsag_ashiglalt':
				plans = self.get_tsag_ashiglalt(date_start, date_end, branch_id, view_type_where)
			elif plan_type=='ajillah_tsag':
				plans = self.get_ajillah_tsag(date_start, date_end, branch_id, view_type_where)
			else:
				plans = self.get_buteel(date_start, date_end, branch_id, view_type_where)
			# Төлөвлөгөө ===============================
			
			def get_day_between(s_date, e_date):
				d_cols = []
				d_cols_r = []
				delta = relativedelta(days=1)
				if group_type=='month':
					delta = relativedelta(months=1)
				elif group_type=='year':
					delta = relativedelta(years=1)
				while s_date <= e_date:
					if group_type=='day':
						d_cols.append(s_date.strftime("%Y-%m-%d"))
						d_cols_r.append(s_date.strftime("%a")+'.'+s_date.strftime("%b-%d"))
					elif group_type=='month':
						d_cols.append(s_date.strftime("%Y-%m"))
					elif group_type=='year':
						d_cols.append(s_date.strftime("%Y"))
					s_date += delta

				return d_cols,d_cols_r
			
			if plans:
				tech_ids = []
				for pp in plans:
					tech_ids.append(pp['technic_id'])
				tech_ids = list(set(tech_ids))
				tech_ids = self.env['technic.equipment'].search([('id','in',tech_ids)])
				plan_lines = []
				date_cols,date_cols_real = get_day_between(sd, ed)
				
				for tech in tech_ids:
					technic_obj_id = tech
					dicts = {
						'technic_id': technic_obj_id.id,
						'technic_name': technic_obj_id.name,
						'park_number': technic_obj_id.park_number,
						'date_plans': [],
					}
					date_plans = []
					plan_total = 0
					actual_total = 0
					actual_huvi = 0
					for dd in date_cols:
						d_vals = {}
						pp_df = self.get_plan_actual(group_type, dd, technic_obj_id.id, plans)
						d_vals['plan'] = self.too(pp_df['plan'])
						d_vals['actual'] = self.too(pp_df['actual'])
						plan_total += pp_df['plan']
						actual_total += pp_df['actual']
						date_plans.append(d_vals)
						
					dicts['plan_total'] =  self.too(plan_total)
					dicts['actual_total'] = self.too(actual_total)
					dicts['actual_huvi'] = self.too(100*actual_total/plan_total) if plan_total!=0 else 0 
					dicts['date_plans'] = date_plans
					technic_rows.append(dicts)
				# Өдрийн дүүргэлт
		datas = {'plan_lines': technic_rows, 'date_cols': date_cols_real or date_cols, 'plan_type': plan_type}
		return datas

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

	def export_report(self):
		datas = self.get_datas(self.date_start.strftime("%Y-%m-%d"), self.date_end.strftime("%Y-%m-%d"), self.branch_id.id, self.group_type, self.view_type, self.plan_type)
		# datas = datas['performance_lines']
		print('\n\nDAILY INFO\n',datas)
		if datas:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			if self.plan_type=='tsag_ashiglalt':
				file_name = 'Цаг ашиглалт'
			elif self.plan_type=='ajillah_tsag':
				file_name = 'Ажиллах цаг'
			else:
				file_name = 'Бүтээл'
			
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
			header_wrap.set_bg_color('#eff8fe')

			
			contest_right = workbook.add_format({'italic':1})
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.0')

			contest_right_do = workbook.add_format({'italic':1})
			contest_right_do.set_text_wrap()
			contest_right_do.set_font_size(9)
			contest_right_do.set_align('right')
			contest_right_do.set_align('vcenter')
			contest_right_do.set_border(style=1)
			contest_right_do.set_bg_color('#d6d5ff')
			contest_right_do.set_num_format('#,##0.0')

			contest_right_d_check = workbook.add_format({'italic':1})
			contest_right_d_check.set_text_wrap()
			contest_right_d_check.set_font_size(9)
			contest_right_d_check.set_align('right')
			contest_right_d_check.set_align('vcenter')
			contest_right_d_check.set_border(style=1)
			contest_right_d_check.set_bg_color('#20fa24')
			contest_right_d_check.set_num_format('#,##0.0')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)
			contest_left.set_num_format('#,##0.0')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)
			contest_center.set_num_format('#,##0.0')

			worksheet = workbook.add_worksheet(file_name)
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"%s %s %s %s" %(file_name,self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'), self.branch_id.display_name), h1)
			row = 1

			worksheet.write(row, 0, u'Техникийн нэр', header_wrap)
			worksheet.write(row, 1, u'Үзүүлэлт', header_wrap)
			colno = 2
			for ddate in datas['date_cols']:
				worksheet.write(row, colno, ddate, header_wrap)
				colno += 1
			worksheet.write(row, colno, u'Нийт', header_wrap)
			worksheet.write(row, colno+1, u'Гүйцэтгэл %', header_wrap)

			row += 1
			worksheet.set_column('A:A', 15)
			worksheet.set_column('B:B', 10)
			worksheet.freeze_panes(2, 1)
			for line in datas['plan_lines']:
				worksheet.merge_range(row, 0, row + 1, 0, line['technic_name'], contest_center)
				worksheet.write(row, 1, 'Төлөвлөгөө', contest_right_do)
				worksheet.write(row+1, 1, 'Гүйцэтгэл', contest_right)
				colno = 2
				for pline in line['date_plans']:
					worksheet.write(row, colno, pline['plan'] or '', contest_right_do)
					print(pline['actual'], type(pline['actual']))
					worksheet.write(row+1, colno, pline['actual'] or '', contest_right)
					colno += 1

				worksheet.write_formula(row, colno, '{=SUM('+self._symbol(row, 2) +':'+ self._symbol(row, colno-1)+')}', contest_right)
				worksheet.write_formula(row, colno+1, '{=IFERROR(AVERAGE('+self._symbol(row, 2) +':'+ self._symbol(row, colno-1)+'),0)}', contest_right)
				row += 1
				worksheet.write_formula(row, colno, '{=SUM('+self._symbol(row, 2) +':'+ self._symbol(row, colno-1)+')}', contest_right)
				worksheet.write_formula(row, colno+1, '{=IFERROR(AVERAGE('+self._symbol(row, 2) +':'+ self._symbol(row, colno-1)+'),0)}', contest_right)
				row += 1

			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))
