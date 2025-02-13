# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

from calendar import monthrange

import logging
_logger = logging.getLogger(__name__)

class MaintenanceLongTerm(models.Model):
	_name = 'maintenance.long.term'
	_description = 'Maintenance Long Term'
	_order = 'date_start desc, name'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	date = fields.Datetime(string=u'Үүсгэсэн огноо', readonly=True, default=datetime.now(), copy=False)
	name = fields.Char(string=u'Нэр', copy=False,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
	date_start = fields.Date(string=u'Эхлэх огноо', copy=True, required=True,
		states={'done': [('readonly', True)]})
	date_end = fields.Date(string=u'Дуусах огноо', copy=True, required=True,
		states={'done': [('readonly', True)]})
	utilization_mth = fields.Integer(string=u'Сард ажиллах норм', default=0,
		states={'done': [('readonly', True)]})

	planner_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, default=_get_user)
	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], default='draft', required=True, string=u'Төлөв', tracking=True)

	long_term_line = fields.One2many('maintenance.long.term.line', 'parent_id', string='Lines', copy=False,
		states={'done': [('readonly', True)]})

	technic_setting_line = fields.One2many('technic.setting.line', 'parent_long_term_id', string='Lines', copy=True,
		states={'done': [('readonly', True)]})

	@api.depends('long_term_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.mapped('long_term_line.amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн', tracking=True, default=0)

	excel_data = fields.Binary('Excel file')
	file_name = fields.Char('File name')

	only_lv_technic = fields.Boolean(string='Зөвхөн LV эсэх', default=False,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Устгахын тулд эхлээд ноороглох ёстой!'))
		return super(MaintenanceLongTerm, self).unlink()

	# ============ Custom methods =========
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		self.planner_id = self.env.user.id
		if not self.technic_setting_line:
			raise UserError(_(u'Техникүүдийн мэдээллийг оруулна уу!'))
		self.state = 'confirmed'

	# Одоогийн ДАТА наас импорт хийх
	def import_from_current(self):
		self.technic_setting_line.unlink()
		technics = False
		if not self.only_lv_technic:
			technics = self.env['technic.equipment'].search([
				('state','not in',['draft']),
				('owner_type','=','own_asset'),
				('component_part_line','!=',False),
				('technic_type','in',['dump','excavator','wheel_excavator','wheel_loader','service_car',
									  'loader','dozer','wheel_dozer','grader','water_truck']),
				])
		else:
			technics = self.env['technic.equipment'].search([
				('state','not in',['draft']),
				('owner_type','=','own_asset'),
				('is_tbb_report','=',False)])
		_logger.info("--------import from ==%d====",len(technics))
		setting_lines = []
		for tt in technics:
			temp = (0,0,{
				'technic_id': tt.id,
				'last_date': tt.last_pm_date,
				'start_odometer': tt.last_pm_odometer,
				'work_time_per_day': tt.technic_setting_id.work_time_per_day,
			})
			setting_lines.append(temp)
		if setting_lines:
			self.technic_setting_line = setting_lines
		return True

	def action_to_done(self):
		self.planner_id = self.env.user.id
		if not self.long_term_line:
			raise UserError(_(u'LONG TERM төлөвлөгөө үүсээгүй байна!\n"Generate" товч дээр дарна уу!'))
		# for line in self.long_term_line:
		# 	line.create_plan()
		self.state = 'done'

	def generate_lines(self):
		# Өмнөх мөрийг устгах
		self.long_term_line.unlink()
		for setting_line in self.technic_setting_line:

			technic = setting_line.technic_id
			work_time_per_day = technic.technic_setting_id.work_time_per_day or 20
			utilization_mth = self.utilization_mth if self.utilization_mth else 30 * work_time_per_day

			for comp in technic.component_part_line:
				# Сүүлд хийгдсэн засварын төрлөөс хамаарч норм мото цаг өөр байна
				# Мөн засварын цагийг зөв олох
				frequency = 0
				work_time = 0
				if not comp.component_config_id:
					comp.set_component_config_id()
				if comp.last_maintenance == 'exchange':
					frequency = comp.norm_odometer or comp.component_config_id.norm_odometer
					work_time = comp.component_config_id.work_time
				elif comp.last_maintenance == 'overhaul':
					frequency = comp.norm_overhaul_odometer or comp.component_config_id.norm_overhaul_odometer
					work_time = comp.component_config_id.work_time_overhaul
				elif comp.last_maintenance == 'reseal':
					frequency = comp.norm_reseal_odometer or comp.component_config_id.norm_reseal_odometer
					work_time = comp.component_config_id.work_time_reseal
				else:
					frequency = comp.norm_odometer
					work_time = comp.component_config_id.work_time

				_logger.info("\n--------LongTerm ======%s %s %s %d %d",technic.park_number, comp.name, comp.last_maintenance, frequency, work_time)
				if frequency == 0:
					raise UserError(_(u'%s, Ажиллах нормыг оруулаагүй байна! %s, id: %d\n' % (comp.last_maintenance, comp.display_name, comp.id)))
				if work_time == 0:
					raise UserError(_(u'%s техник, Засварын цагийг оруулаагүй байна! %s, id: %d\n' % (technic.park_number, comp.display_name, comp.id)))

				# D-check ийн норм олох
				d_check_norm = comp.component_config_id.norm_dcheck_odometer or 0

				current_odometer = comp.total_odometer
				last_odometer = comp.last_odometer
				worked_motohour = current_odometer #- last_odometer

				# temp_date = datetime.now().strftime('%Y-%m-%d')
				temp_date = self.date_start
				# Дуусах огноо хүртэл давтана
				while temp_date < self.date_end:
					# Техникийн тохиргоон дээр ажиллаж эхлэх огноо байгаа эсэхийг шалгах
					# Хэрэв эхлэх огноо байхгүй бол хэвийн forecast гүйж үргэлжлэнэ
					# Эхлэх огноо зааж өгсөн байгаад болоогүй бол forecast ийг гүйлгэхгүй алгасна
					if setting_line.start_date and setting_line.start_date > temp_date:
						temp_date = self._date_increase(temp_date)
						continue
					# ===========================================
					vals = {}
					tt = worked_motohour
					temp_d_check = 0
					amount = 0
					vals['repair_it'] = False
					if worked_motohour >= frequency:
						vals['repair_it'] = True
						worked_motohour = 0
						if comp.last_maintenance == 'exchange':
							if comp.product_id:
								amount = comp.product_id.standard_price
							else:
								amount = comp.component_config_id.amount_exchange
						elif comp.last_maintenance == 'overhaul':
							amount = comp.component_config_id.amount_overhaul
						elif comp.last_maintenance == 'reseal':
							amount = comp.component_config_id.amount_reseal
						else:
							if comp.product_id:
								amount = comp.product_id.standard_price
							else:
								amount = comp.component_config_id.amount_exchange
						vals['last_maintenance'] = comp.last_maintenance
						vals['description'] = comp.last_maintenance

					# Forecast үүсгэх
					vals['parent_id'] = self.id
					vals['technic_id'] = technic.id
					vals['component_id'] = comp.id
					vals['date_plan'] = temp_date
					vals['date_str'] = temp_date.strftime("%Y-%m-%d")[:7]
					vals['current_odometer'] = current_odometer
					vals['last_odometer'] = last_odometer
					vals['set_odometer'] = comp.set_odometer
					vals['repair_odometer'] = tt
					vals['frequency'] = frequency
					vals['amount'] = amount
					vals['work_time'] = work_time if vals['repair_it'] else 0

					if not vals['repair_it'] and d_check_norm > 0:
						if d_check_norm-utilization_mth/2 <= worked_motohour and worked_motohour < d_check_norm+utilization_mth/2:
							vals['is_d_check'] = True
							work_time = comp.component_config_id.work_time_dcheck
							vals['work_time'] = work_time
							amount = comp.component_config_id.amount_d_check
							vals['amount'] = amount
							vals['description'] = 'D-check'

					line = self.env['maintenance.long.term.line'].create(vals)

					temp_date = self._date_increase(temp_date)
					utilization_mth = self.utilization_mth if self.utilization_mth else 30 * work_time_per_day
					worked_motohour += utilization_mth

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date):
		days = monthrange(temp_date.year,temp_date.month)[1]
		date1 = temp_date
		date2 = date1 + timedelta(days=days)
		return date2

	# Pivot оор харах
	def see_expenses_view(self):
		if self.long_term_line:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_long_term_line_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_long_term_line_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			return {
				'name': self.name,
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'maintenance.long.term.line',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('parent_id','=',self.id)],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

	def export_report(self):
		if self.long_term_line:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Forecast report.xlsx'

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

			contest_right = workbook.add_format({'italic':1})
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)

			red_temp = workbook.add_format({'italic':1})
			red_temp.set_text_wrap()
			red_temp.set_font_size(9)
			red_temp.set_align('right')
			red_temp.set_align('vcenter')
			red_temp.set_border(style=1)
			red_temp.set_bg_color('#FF9F9B')

			contest_right_do = workbook.add_format({'italic':1})
			contest_right_do.set_text_wrap()
			contest_right_do.set_font_size(9)
			contest_right_do.set_align('right')
			contest_right_do.set_align('vcenter')
			contest_right_do.set_border(style=1)
			contest_right_do.set_bg_color('#FF9F9B')

			contest_right_d_check = workbook.add_format({'italic':1})
			contest_right_d_check.set_text_wrap()
			contest_right_d_check.set_font_size(9)
			contest_right_d_check.set_align('right')
			contest_right_d_check.set_align('vcenter')
			contest_right_d_check.set_border(style=1)
			contest_right_d_check.set_bg_color('#20fa24')

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

			worksheet = workbook.add_worksheet(u'Component - Moto hours')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"LONG TERM - Forecast", h1)

			row = 1
			for tt in self.technic_setting_line.mapped('technic_id'):
				# TABLE HEADER
				worksheet.merge_range(row+0, 0, row+0, 1, u"Техникийн нэр", header_wrap)
				worksheet.merge_range(row+1, 0, row+1, 1, u"Техникийн модел", header_wrap)
				worksheet.merge_range(row+2, 0, row+2, 1, u"Техникийн сериал", header_wrap)
				worksheet.merge_range(row+3, 0, row+3, 1, u"Техникийн төрөл", header_wrap)
				worksheet.merge_range(row+4, 0, row+4, 1, u"Сайтын нэр", header_wrap)
				worksheet.merge_range(row+0, 6, row+0, 8, u"Үйлдвэрлэсэн огноо", header_wrap)
				worksheet.merge_range(row+1, 6, row+1, 8, u"Сайтад эхэлсэн огноо", header_wrap)
				worksheet.merge_range(row+2, 6, row+2, 8, u"Сарын дундаж мото цаг", header_wrap)
				worksheet.merge_range(row+3, 6, row+3, 8, u"Сайт дээрх мот цаг", header_wrap)
				worksheet.merge_range(row+4, 6, row+4, 8, u"Нийт ажилласан мот цаг", header_wrap)
				worksheet.merge_range(row+3, 10, row+3, 12, u"Сайт дээрх явахын км/цаг", header_wrap)
				worksheet.merge_range(row+4, 10, row+4, 12, u"Нийт явсан км цаг", header_wrap)
				worksheet.merge_range(row, 15, row+4, 16, u"Шилжсэн түүх", header_wrap)
				worksheet.merge_range(row, 17, row, 18, u"Байршил-1", header_wrap)
				worksheet.merge_range(row, 19, row, 20, u"Байршил-2", header_wrap)
				worksheet.merge_range(row, 21, row, 22, u"Байршил-3", header_wrap)

				worksheet.merge_range(row+0, 2, row+0, 5, tt.name, contest_center)
				worksheet.merge_range(row+1, 2, row+1, 5, tt.technic_setting_id.model_id.name, contest_center)
				worksheet.merge_range(row+2, 2, row+2, 5, tt.vin_number, contest_center)
				worksheet.merge_range(row+3, 2, row+3, 5, dict(tt.technic_setting_id._fields['technic_type'].selection).get(tt.technic_setting_id.technic_type), contest_center)
				worksheet.merge_range(row+4, 2, row+4, 5, tt.tech_location, contest_center)
				worksheet.write(row+0, 9, tt.manufactured_date.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row+1, 9, tt.start_date.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row+2, 9, self.utilization_mth or 30*tt.technic_setting_id.work_time_per_day, contest_center)
				worksheet.write(row+4, 9, tt.total_odometer, contest_center)
				worksheet.write(row+4, 13, tt.total_km or '', contest_center)
				worksheet.merge_range(row+1, 17, row+4, 18, tt.tech_location, contest_center)
				worksheet.write(row+3, 9, tt.total_odometer, contest_center)
				worksheet.write(row+3, 13, tt.total_km or '', contest_center)
				if tt.move_line_ids:
					worksheet.write(row+3, 9, tt.total_odometer-sum(tt.mapped('move_line_ids.moto_hour')), contest_center)
					if tt.total_km:
						worksheet.write(row+3, 13, tt.total_km-sum(tt.mapped('move_line_ids.km')), contest_center)
				history = self.env['technic.move.history'].search([('technic_id','=',tt.id)], order='date desc', limit=2)
				col_h = 0
				for i in history:
					if i.new_tech_location:
						worksheet.merge_range(row+1, 19+col_h, row+4, 20+col_h, i.new_tech_location, contest_center)
					else:
						worksheet.merge_range(row+1, 19+col_h, row+4, 20+col_h, i.new_branch_id.name, contest_center)
					col_h += 2
					print(i)
				# --------------
				lines = self.env['maintenance.long.term.line'].search([
					('parent_id','=',self.id),
					('technic_id','=',tt.id)], order='date_str, date_plan, component_id, repair_odometer')
				row_dict = {}
				col_dict = {}
				col = 11
				rr = row + 7
				for line in lines:
					worksheet.set_row(row+6, 25)
					worksheet.write(row+6, 0, u'Компонент', header_wrap)
					worksheet.write(row+6, 1, u'Сэлбэг дугаар', header_wrap)
					worksheet.write(row+6, 2, u'Сериал', header_wrap)
					worksheet.write(row+6, 3, u'Байршил', header_wrap)
					worksheet.write(row+6, 4, u'Сэргээн зассан мот цаг', header_wrap)
					worksheet.write(row+6, 5, u'Угсарсан мот цаг', header_wrap)
					worksheet.write(row+6, 6, u'Угсарсан огноо', header_wrap)
					worksheet.write(row+6, 7, u'Reseal хугацаа', header_wrap)
					worksheet.write(row+6, 8, u'Overhaul хугацаа', header_wrap)
					worksheet.write(row+6, 9, u'Reseal мот цаг', header_wrap)
					worksheet.write(row+6, 10, u'Frequency', header_wrap)
					if line.date_str not in col_dict:
						col_dict[line.date_str] = col
						worksheet.write(row+6, col, line.date_str, header_wrap)
						col += 1
					if line.component_id.id not in row_dict:
						worksheet.write(rr, 0, line.component_id.name, contest_left)
						worksheet.write(rr, 1, line.component_id.real_part_number or '', contest_left)
						worksheet.write(rr, 2, line.component_id.serial_number or '', contest_left)
						worksheet.write(rr, 3, line.component_id.part_location or '', contest_left)
						worksheet.write(rr, 4, line.component_id.last_odometer, contest_left)
						worksheet.write(rr, 5, line.component_id.set_odometer, contest_left)
						worksheet.write(rr, 6, line.component_id.date_of_set.strftime('%Y-%M-%d') if line.component_id.date_of_set else '', contest_left)
						if line.component_id.reseal_date_diff<0:
							temp_id_1 = red_temp
						else:
							temp_id_1 = contest_right
						if line.component_id.overhaul_date_diff<0:
							temp_id_2 = red_temp
						else:
							temp_id_2 = contest_right
						if line.component_id.reseal_odometer_diff<0:
							temp_id_3 = red_temp
						else:
							temp_id_3 = contest_right
						worksheet.write(rr, 7, line.component_id.reseal_date_diff, temp_id_1)
						worksheet.write(rr, 8, line.component_id.overhaul_date_diff, temp_id_2)
						worksheet.write(rr, 9, line.component_id.reseal_odometer_diff, temp_id_3)
						worksheet.write(rr, 10, line.frequency, contest_right)
						row_dict[line.component_id.id] = rr
						rr += 1

					r0 = row_dict[line.component_id.id]
					cc = col_dict[line.date_str]
					temp_style = contest_right
					if line.repair_it:
						temp_style = contest_right_do
					elif line.is_d_check:
						temp_style = contest_right_d_check
					worksheet.write(r0, cc, line.repair_odometer, temp_style)
				if rr-row+1 > 5:
					row += (rr-row+1)
				else:
					row += 6

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

class MaintenanceLongTermLine(models.Model):
	_name = 'maintenance.long.term.line'
	_description = 'Maintenance Long Term Line'
	_order = 'date_str, date_plan, technic_id, component_id, repair_odometer'

	# Columns
	parent_id = fields.Many2one('maintenance.long.term', string=u'Parent long term', ondelete='cascade')

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,)
	component_id = fields.Many2one('technic.component.part', string=u'Компонент', )
	date_plan = fields.Date(u'Огноо', copy=False, required=True,)
	date_str = fields.Char(u'Сар', copy=False, required=True, readonly=True)

	current_odometer = fields.Float(string=u'SMU', required=True,)
	last_odometer = fields.Float(string=u'Last repair odometer', required=True,)
	set_odometer = fields.Float(string=u'Set odometer', required=True,)
	frequency = fields.Integer(string=u'Frequency', required=True,)
	repair_odometer = fields.Float(string=u'Odometer', required=True, default=0)
	work_time = fields.Float(string=u'Зарцуулах цаг', required=True,)
	repair_it = fields.Boolean(string=u'Засах эсэх', default=False)
	is_d_check = fields.Boolean(string=u'D-check эсэх', default=False)

	last_maintenance = fields.Selection([
		('exchange','Exchange'),
		('overhaul','Overhaul'),
		('reseal','Reseal'),
		('main_service','Урсгал засвар')], string='Last maintenance', )

	description = fields.Char('Тайлбар', )

	amount = fields.Float(string=u'Мөнгөн дүн', )
	plan_id = fields.Many2one('maintenance.plan.line', string=u'REF plan', readonly=True, )

	start_date = fields.Date(string=u'Ажиллах эхлэх', )

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.plan_id and s.plan_id.state != 'draft':
				raise UserError(_(u'Төлөвлөгөө үүссэн байна. Устгах боломжгүй!'))
		return super(MaintenanceLongTermLine, self).unlink()

	# ============ Custom =================
	@api.onchange('date_plan')
	def _onchange_date_plan(self):
		if self.date_plan:
			self.date_str = self.date_plan.strftime("%Y-%m-%d")[:7]

	@api.onchange('last_maintenance')
	def onchange_last_maintenance(self):
		if self.last_maintenance == 'exchange':
			self.frequency = self.component_id.norm_odometer
			self.work_time = self.component_id.component_config_id.work_time
			self.amount = self.component_id.product_id.standard_price if self.component_id.product_id else self.component_id.component_config_id.amount_exchange
		elif self.last_maintenance == 'overhaul':
			self.frequency = self.component_id.norm_overhaul_odometer
			self.work_time = self.component_id.component_config_id.work_time_overhaul
			self.amount = self.component_id.component_config_id.amount_overhaul
		elif self.last_maintenance == 'reseal':
			self.frequency = self.component_id.norm_reseal_odometer
			self.work_time = self.component_id.component_config_id.work_time_reseal
			self.amount = self.component_id.component_config_id.amount_reseal

	def create_plan(self):
		for obj in self:
			# Material data
			material_datas = []
			for m_line in obj.pm_material_line:
				temp = (0,0,{
					'product_id': m_line.material_id.id,
					'price_unit': m_line.price_unit,
					'qty': m_line.qty,
					'is_pm_material': True,
				})
				material_datas.append(temp)

			# 10 цаг буюу 1 ээлжинд багтах эсэх
			shift_hour = obj.technic_id.technic_setting_id.work_time_per_day / 2
			temp_work_time = obj.work_time
			temp_work_time_2 = 0
			if obj.work_time > shift_hour:
				temp_work_time = shift_hour
				temp_work_time_2 = obj.work_time - shift_hour

			# Өдрийн ПЛАН үүсгэх
			vals = {
				'branch_id': obj.technic_id.branch_id.id,
				'origin': 'Generated: '+self.parent_id.name,
				'maintenance_type_id': obj.maintenance_type_id.id,
				'pm_priority': obj.pm_priority,
				'maintenance_type': 'pm_service',
				'contractor_type': 'internal',
				'generator_line_id': obj.id,
				'date_required': obj.date_plan,
				'technic_id': obj.technic_id.id,
				'start_odometer': obj.pm_odometer,
				'work_time': temp_work_time,
				'description': obj.name,
				'required_material_line': material_datas,
				'shift': 'day',
			}
			plan = self.env['maintenance.plan.line'].create(vals)
			plan.action_to_confirm()
			obj.plan_id = plan.id
			obj.description = 'Plans: '+ str(plan.id)

			# Хэрэв зөрүү цаг байвал шөнийн план үүсгэх
			if temp_work_time_2 > 0:
				# Шөнийн ПЛАН үүсгэх
				vals = {
					'branch_id': obj.technic_id.branch_id.id,
					'origin': 'Generated: '+self.parent_id.name + ', REF plan:'+str(obj.plan_id.name),
					'maintenance_type_id': obj.maintenance_type_id.id,
					'pm_priority': obj.pm_priority,
					'maintenance_type': 'pm_service',
					'contractor_type': 'internal',
					'generator_line_id': obj.id,
					'date_required': obj.date_plan,
					'technic_id': obj.technic_id.id,
					'start_odometer': obj.pm_odometer,
					'work_time': temp_work_time_2,
					'description': obj.name,
					'shift': 'night',
				}
				plan = self.env['maintenance.plan.line'].create(vals)
				plan.action_to_confirm()
				obj.plan_id = plan.id
				obj.description += ', '+str(plan.id)
