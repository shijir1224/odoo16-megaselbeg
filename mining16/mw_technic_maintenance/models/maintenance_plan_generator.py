# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError, Warning
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

class MaintenancePlanGenerator(models.Model):
	_name = 'maintenance.plan.generator'
	_description = 'Maintenance plan generator'
	_order = 'date_start desc, technic_id'

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
	branch_id = fields.Many2one('res.branch', string='Салбар')

	technic_id = fields.Many2one('technic.equipment',string=u'Техник',
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})
	technic_setting_id = fields.Many2one(related='technic_id.technic_setting_id',
		string=u'Техникийн тохиргоо', readonly=True, )
	work_time_per_day = fields.Float(string=u'Өдөрт ажиллах цаг',
		states={'done': [('readonly', True)]})
	start_odometer = fields.Float(string=u'Эхлэх гүйлт',
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	maintenance_type_id = fields.Many2one('maintenance.type',string=u'Засварын төрөл',
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	planner_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, default=_get_user)
	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], default='draft', required=True, string=u'Төлөв', tracking=True)

	generate_type = fields.Selection([
			('only_one', u'Зөвхөн нэг'),
			('all', u'Бүх техник'),
		], default='all', required=True, string=u'Төлөвлөлтийн төрөл')

	is_round_interval = fields.Boolean(string=u'Мото цагийг бүхэлдэх эсэх', default=False,
		states={'done': [('readonly', True)]})

	plan_generated_line = fields.One2many('maintenance.plan.generator.line', 'parent_id', string='Lines', copy=False,
		states={'done': [('readonly', True)]})

	technic_setting_line = fields.One2many('technic.setting.line', 'parent_id', string='Lines', copy=True,
		states={'done': [('readonly', True)]})

	forecast_type = fields.Selection([
			('weekly', u'7 хоногоор'),
			('monthly', u'Сараар'),
			('year', u'Жилээр'),
			('other', u'Бусад'),
		], default='weekly', required=True, string=u'Хугацааны төрөл',
		states={'done': [('readonly', True)]})

	clear_odometer_diff = fields.Selection([
			('half_day', u'Хагас өдрийн гүйлт'),
			('full_day', u'Бүтэн өдрийн гүйлт'),
			('three_day', u'3 өдрийн гүйлт'),
		], string=u'Зөрүү арилгаж нэмэх',
		states={'done': [('readonly', True)]},
		help="Гүйлтийн зөрүү арилгаж хагас, бүтэн өдрийн гүйлт нэмэх үед хэрэглэнэ", )

	start_last_info = fields.Boolean(string='Сүүлд хийгдсэн мэдээллээс эхлэх', default=False,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	only_lv_technic = fields.Boolean(string='Зөвхөн LV эсэх', default=False,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	@api.depends('plan_generated_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.mapped('plan_generated_line.total_amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн', tracking=True, default=0)

	excel_data = fields.Binary('Excel file')
	file_name = fields.Char('File name')

	is_date_start = fields.Boolean(string=u'Эхлэх огнооноос эсэх?', default=False)
	performance_percent = fields.Float(string="Гүйцэтгэлийн хувь", compute="compute_plan_performance", store=True)

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Устгахын тулд эхлээд ноороглох ёстой!'))
		return super(MaintenancePlanGenerator, self).unlink()

	# ============ Custom methods =========
	@api.onchange('technic_id','technic_setting_id')
	def onchange_technic_id(self):
		if self.technic_setting_id:
			self.work_time_per_day = self.technic_setting_id.work_time_per_day

	@api.depends("plan_generated_line","plan_generated_line.plan_id")
	def compute_plan_performance(self):
		for item in self:
			percent = 0
			if item.plan_generated_line:
				plan_ids = item.plan_generated_line.mapped('plan_id')
				percent = len(plan_ids.mapped('workorder_id')) if plan_ids else 0/len(item.plan_generated_line)
			item.performance_percent = percent

	def action_to_draft(self):
		if self.forecast_type == 'year' and self.state == 'done':
			raise UserError(_(u'Жилийн төлөвлөгөөг та ноороглох боломжгүй!'))
		self.state = 'draft'

	def action_to_confirm(self):
		self.planner_id = self.env.user.id
		if self.generate_type == 'only_one':
			if self.start_odometer <= 0:
				raise UserError(_(u'Эхлэх мото цагийг оруулна уу!'))
		else:
			if not self.technic_setting_line and not self.env.context.get('equipment', False):
				raise UserError(_(u'Техникүүдийн мэдээллийг оруулна уу!'))
		self.state = 'confirmed'

	# Excel файлаас дата авах ==============================
	def export_excel_template(self):
		# INIT
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet('Import template')
		file_name = 'technic_import_template.xls'

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(10)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		# Draw rows
		worksheet.write(0, 0, u"ID", contest_left)
		worksheet.write(0, 1, u"Техник", contest_left)
		worksheet.write(0, 2, u"Эхлэх гүйлт", contest_left)
		worksheet.write(0, 3, u"Өдөрт ажиллах цаг", contest_left)
		worksheet.write(0, 4, u"Сүүлд хийгдсэн огноо", contest_left)
		worksheet.write(0, 5, u"Сүүлд хийгдсэн PM дугаар", contest_left)
		worksheet.write(0, 6, u"Ажиллаж эхдэх огноо", contest_left)
		r = 1
		technics = []
		if self.technic_setting_line:
			t_ids = self.technic_setting_line.mapped('technic_id.id')
			technics = self.env['technic.equipment'].search(
						[('id','in',t_ids)],
					order="report_order, program_code")
		else:
			technics = self.env['technic.equipment'].search(
					[('is_tbb_report','=',True)],
				order="report_order, program_code")
		for line in technics:
			worksheet.write(r, 0, line.id, contest_left)
			worksheet.write(r, 1, line.name, contest_left)
			worksheet.write(r, 3, line.technic_setting_id.work_time_per_day, contest_left)
			r += 1
		# Close, Save
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}

	# Excel ээс импорт хийх
	def import_from_excel(self):
		# Өмнөх дата г цэвэрлэх
		self.technic_setting_line.unlink()

		if not self.excel_data:
			raise UserError(_(u'импорт хийх файлыг сонгоно уу!'))

		# File нээх
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			 raise UserError(u'Importing error.\nCheck excel file!')

		book = xlrd.open_workbook(fileobj.name)
		try :
			 sheet = book.sheet_by_index(0)
		except:
			 raise UserError(u'Буруу sheet дугаар байна')

		# Унших
		nrows = sheet.nrows
		setting_lines = []
		for r in range(1,nrows):
			row = sheet.row(r)
			if row[0].value:
				technic_id = row[0].value
				start_odometer = row[2].value or 0
				worktime = row[3].value or 0
				last_date = row[4].value or datetime.now().date()
				last_pm_priority = row[5].value or 0
				start_date = row[6].value if 6 in row else False
				_logger.info("--------import ======%s %s ",str(start_odometer), str(technic_id))
				temp = (0,0,{
					'technic_id': int(technic_id),
					'start_odometer': start_odometer,
					'work_time_per_day': worktime,
					'last_date': last_date,
					'last_pm_priority': last_pm_priority,
					'start_date': start_date,
				})
				setting_lines.append(temp)

		if setting_lines:
			self.technic_setting_line = setting_lines
		return True

	# Одоогийн ДАТА наас импорт хийх
	def import_from_current(self):
		self.technic_setting_line.unlink()
		technics = False
		if not self.only_lv_technic:
			if self.forecast_type != 'year':
				technics = self.env['technic.equipment'].search([
					('state','in',['working','repairing']),
					('owner_type','=','own_asset'),
					('branch_id','=',self.branch_id.id),
					('is_tbb_report','=',True),
					('technic_type','in',['dump','excavator','wheel_excavator','wheel_loader','service_car',
										  'loader','dozer','wheel_dozer','grader','water_truck']),
					])
			else:
				technics = self.env['technic.equipment'].search([
					('state','not in',['draft','inactive']),
					('owner_type','=','own_asset'),
					('branch_id','=',self.branch_id.id),
					('is_tbb_report','=',True),
					('technic_type','in',['dump','excavator','wheel_excavator','wheel_loader','service_car',
										  'loader','dozer','wheel_dozer','grader','water_truck']),
					])
		else:
			if self.forecast_type != 'year':
				technics = self.env['technic.equipment'].search([
					('state','in',['working','repairing']),
					('owner_type','=','own_asset'),
					('branch_id','=',self.branch_id.id),
					('is_tbb_report','=',False)])
			else:
				technics = self.env['technic.equipment'].search([
					('state','not in',['draft']),
					('owner_type','=','own_asset'),
					('branch_id','=',self.branch_id.id),
					('is_tbb_report','=',False)])

		_logger.info("--------import from ==%d====",len(technics))
		setting_lines = []
		for tt in technics:
			temp = False
			# Богино хугацааных бол одоогийн мэдээллээс авах
			if self.forecast_type != 'year':
				temp = (0,0,{
					'technic_id': tt.id,
					'last_pm_priority': tt.last_pm_priority,
					'last_date': tt.last_pm_date,
					'maintenance_type_id': tt.last_pm_id.id,
					'start_odometer': tt.last_pm_odometer,

					'work_time_per_day': tt.technic_setting_id.work_time_per_day,
				})
			# Урт хугацааных бол эхлэх огнооноос өмнөх мэдээллээс авна - Year, month
			else:
				wo = self.env['maintenance.workorder'].search([
					('date_required','<',self.date_start),
					('maintenance_type','=','pm_service'),
					('technic_id','=',tt.id),
					('state','in',['done','closed'])
					], order='date_required desc', limit=1)
				if wo:
					temp = (0,0,{
					'technic_id': tt.id,
					'last_pm_priority': wo.pm_priority,
					'last_date': wo.date_required,
					'maintenance_type_id': wo.maintenance_type_id.id,
					'start_odometer': wo.finish_odometer,
					'work_time_per_day': tt.technic_setting_id.work_time_per_day,
				})

			if temp:
				setting_lines.append(temp)

		if setting_lines:
			self.technic_setting_line = setting_lines
		return True

	def action_to_done(self):
		self.planner_id = self.env.user.id
		if not self.plan_generated_line:
			raise UserError(_(u'Урьдчилсан төлөвлөгөө үүсээгүй байна!\n"Generate" товч дээр дарна уу!'))
		for line in self.plan_generated_line:
			line.create_plan()
		self.state = 'done'

	def generate_lines(self):
		# Өмнөх мөрийг устгах
		self.plan_generated_line.unlink()
		# Хэрэв 1 техникийн план үүсгэж байгаа бол
		if self.generate_type == 'only_one':
			last_odometer = self.technic_id.last_pm_odometer
			last_pm_priority = self.technic_id.last_pm_priority
			work_time_per_day = self.work_time_per_day if self.work_time_per_day else self.technic_id.technic_setting_id.work_time_per_day

			if work_time_per_day == 0:
					raise UserError(_(u'Өдөрт ажиллах цаг 0 байна! %s %d' % (self.technic_id.technic_setting_id.name, technic.technic_setting_id.id)))

			if not self.technic_id.technic_setting_id.pm_material_config:
				raise UserError(_(u'PM үйлчилгээний тохиргоо хийгдээгүй байна!'))

			pm_line_ids = [0]
			for pm_line in self.technic_id.technic_setting_id.pm_material_config:
				pm_line_ids.append(pm_line.id)

			# Сүүлд хийгдсэн PM дугаар авна
			idx = last_pm_priority
			# Сүүлд хийгдсэн PM огноо байвал авна, үгүй бол эхлэх огноог авна
			first = True
			# NEW
			if self.is_date_start:
				temp_date = self.date_start
			else:
				temp_date = datetime.now().date()
			if self.forecast_type == 'year':
				if self.start_last_info:
					temp_date = setting_line.last_date
					last_odometer = setting_line.start_odometer
				else:
					temp_date = self.date_start

			# Дуусах огноо хүртэл давтана
			while temp_date < self.date_end:
				# Next PM олох
				if idx+1 < len(pm_line_ids):
					idx += 1
				else:
					idx = 1

				# Дараагийн PM авах
				pm_config = self.env['maintenance.pm.material.config'].browse(pm_line_ids[idx])
				interval = pm_config.interval
				if self.technic_id.id == 4039:
					print('idx', idx, interval)
					print(aaa)
				if interval <= 0:
						raise UserError(_(u'Interval-ийг тохируулна уу! %s' % technic.technic_setting_id.name))
				# Мото цагийн INTERVAL-аар бүхэлчлэх
				if self.is_round_interval:
					last_odometer = self._round_by_interval(last_odometer, interval)
				# INTERVAL-ийг өдөр лүү хөрвүүлнэ
				days = round(interval / work_time_per_day)
				if pm_config.work_time <= 0:
					temp_date = self._date_increase(temp_date,days)
					continue

				# Зөв эхлэлийг олох
				# Хэрэв хийгдэх мото цаг нь болоогүй бол хойшлуулна
				if first:
					current_mh = self.technic_id.total_odometer if self.technic_id.odometer_unit == 'motoh' else self.technic_id.total_km
					# Гүйлтийн зөрүү арилгах эсэх
					if self.clear_odometer_diff == 'half_day':
						current_mh += work_time_per_day/2
					elif self.clear_odometer_diff == 'full_day':
						current_mh += work_time_per_day
					elif self.clear_odometer_diff == 'three_day':
						current_mh += work_time_per_day*3
					# ===========================
					diff = (last_odometer+interval) - current_mh
					back_day = round(diff / work_time_per_day)
					if back_day >= 1  and diff > 0:
						temp_date = self._date_increase(temp_date,back_day)
					first = False

				# Өнгөрсөн бол давталтаас гарах
				if temp_date >= self.date_end:
					break

				last_odometer += interval
				# Материалын дата бэлдэх
				material_datas = []
				for m_line in pm_config.pm_material_line:
					product = m_line.material_id
					if m_line.is_depend_season:
						product = self.env['depending.season.material']._check_depend_season_material(m_line.material_id, temp_date)
					temp = (0,0,{
						'material_id': product.id,
						'price_unit': product.standard_price,
						'qty': m_line.qty,
						'warehouse_id': m_line.warehouse_id.id,
					})
					material_datas.append(temp)

				# Жилийнх байвал forecast гүйнэ
				if self.forecast_type != 'year':
					# Хэрэв төлөвлөгөөт зогсолт байгаа эсэхийг шалгах
					# Байвал Forecast үүсгэхгүй
					stop_plan = self.env['maintenance.plan.line'].search([
						('maintenance_type','in',['stopped','pm_service']),
						('technic_id','=',self.technic_id.id),
						('state','=','confirmed'),
						('date_required','=',temp_date)])
					if stop_plan:
						temp_date = self._date_increase(temp_date,days)
						continue
				# Зогсолт байхгүй бол
				# Forecast үүсгэх
				vals = {
					'parent_id': self.id,
					'maintenance_type_id': pm_config.maintenance_type_id.id,
					'pm_priority': idx,
					'date_plan': temp_date,
					'technic_id': self.technic_id.id,
					'pm_odometer': last_odometer,
					'work_time': pm_config.work_time,
					'man_hours': pm_config.total_man_hours,
					'pm_material_line': material_datas,
					'description': pm_config.maintenance_type_id.name,
				}
				line = self.env['maintenance.plan.generator.line'].create(vals)
				# ++
				temp_date = self._date_increase(temp_date,days)

			# Хэрэв жилийнх бол
			# Заасан огнооноос илүү дутуу үүссэн LINE ийг устгах
			if self.forecast_type == 'year':
				lines = self.env['maintenance.plan.generator.line'].search([
					('parent_id','=',self.id),
					('date_plan','<',self.date_start),
				])
				lines.unlink()

		# Хэрэв олон техник үүсгэх гэж байгаа бол
		else:
			for setting_line in self.technic_setting_line:
				technic = setting_line.technic_id
				last_odometer = setting_line.start_odometer or technic.last_pm_odometer
				last_pm_priority = setting_line.last_pm_priority or technic.last_pm_priority
				last_pm_date = setting_line.last_date or technic.last_pm_date
				# Сүүлд хийгдсэн PM мэдээлэл шалгах
				if not last_odometer:
					raise UserError(_(u'Сүүлд хийгдсэн PM үйлчилгээний мото цаг оруулаагүй байна!\n %s'%technic.name))
				if not last_pm_priority:
					raise UserError(_(u'Сүүлд хийгдсэн PM үйлчилгээний дугаар оруулаагүй байна!\n %s'%technic.name))
				if not last_pm_date:
					raise UserError(_(u'Сүүлд хийгдсэн PM үйлчилгээний огноо оруулаагүй байна!\n %s'%technic.name))

				work_time_per_day = technic.technic_setting_id.work_time_per_day

				if work_time_per_day == 0:
					raise UserError(_(u'Өдөрт ажиллах цаг 0 байна! %s %d' % (technic.technic_setting_id.name, technic.technic_setting_id.id)))

				if not technic.technic_setting_id.pm_material_config:
					raise UserError(_(u'PM үйлчилгээний тохиргоо хийгдээгүй байна! %s' % technic.technic_setting_id.name))

				pm_line_ids = [0]
				for pm_line in technic.technic_setting_id.pm_material_config:
					pm_line_ids.append(pm_line.id)

				# Сүүлд хийгдсэн PM дугаар авна
				idx = last_pm_priority
				# Сүүлд хийгдсэн PM огноо байвал авна, үгүй бол эхлэх огноог авна
				first = True
				# NEW
				if self.is_date_start:
					temp_date = self.date_start
				else:
					temp_date = datetime.now().date()
				if self.forecast_type == 'year':
					if self.start_last_info:
						temp_date = setting_line.last_date
						last_odometer = setting_line.start_odometer
					else:
						temp_date = self.date_start

				# Дуусах огноо хүртэл давтана
				while temp_date < self.date_end:
					print('temp_date', temp_date)
					# Next PM олох
					if idx+1 < len(pm_line_ids):
						idx += 1
					else:
						idx = 1

					# Дараагийн PM авах
					pm_config = self.env['maintenance.pm.material.config'].browse(pm_line_ids[idx])
					if pm_config.work_time <= 0:
						raise UserError(_(u'{0} техникийн тохиргооны {1} PM дээр засварын цаг тохируулаагүй байна!'.format(technic.technic_setting_id.name, pm_config.maintenance_type_id.name)))
						# continue
					interval = pm_config.interval
					if interval <= 0:
						raise UserError(_(u'Interval-ийг тохируулна уу! %s' % technic.technic_setting_id.name))
					# Мото цагийн INTERVAL-аар бүхэлчлэх
					if self.is_round_interval:
						last_odometer = self._round_by_interval(last_odometer, interval)
					# INTERVAL-ийг өдөр лүү хөрвүүлнэ
					days = round(interval / work_time_per_day) if not technic.technic_setting_id.is_plan_by_time else interval
					days = 1 if days < 1 else days
					# Техникийн тохиргоон дээр ажиллаж эхлэх огноо байгаа эсэхийг шалгах
					# Хэрэв эхлэх огноо байхгүй бол хэвийн forecast гүйж үргэлжлэнэ
					# Эхлэх огноо зааж өгсөн байгаад болоогүй бол forecast ийг гүйлгэхгүй алгасна
					if setting_line.start_date and setting_line.start_date > temp_date:
						temp_date = self._date_increase(temp_date,days)
						print('aaaaaa', temp_date, days)
						continue
					# ===========================================

					_logger.info("---generate ======%s %s %d %d %d",technic.name, temp_date, last_odometer, technic.total_odometer, interval)
					# Зөв эхлэлийг олох
					# Хэрэв хийгдэх мото цаг нь болоогүй бол хойшлуулна
					if first:
						# if self.forecast_type == 'year':  # Түр хасав
						# 	temp_date = self._date_increase(temp_date,days)
						current_mh = technic.total_odometer if technic.odometer_unit == 'motoh' else technic.total_km
						print('===', current_mh)
						# Гүйлтийн зөрүү арилгах эсэх
						if self.clear_odometer_diff == 'half_day':
							current_mh += work_time_per_day/2
						elif self.clear_odometer_diff == 'full_day':
							current_mh += work_time_per_day
						elif self.clear_odometer_diff == 'three_day':
							current_mh += work_time_per_day*3
						# print('=2=', current_mh)
						# ===========================
						diff = (last_odometer+interval) - current_mh
						back_day = round(diff / work_time_per_day)
						if back_day >= 1 and diff > 0:
							temp_date = self._date_increase(temp_date,back_day)
						first = False
					_logger.info("---generate 2=====%s %s %d %d %d",pm_config.name, temp_date, (last_odometer+interval), diff, back_day)
					# Өнгөрсөн бол давталтаас гарах
					if temp_date > self.date_end:
						break

					last_odometer += interval
					# Материалын дата бэлдэх
					material_datas = []
					for m_line in pm_config.pm_material_line:
						template = m_line.template_id
						product = False
						if m_line.is_depend_season:
							template = self.env['depending.season.material']._check_depend_season_material(template, temp_date)
							variants = template.product_variant_ids
							last_baraa = self.env['product.product'].search([('id','in',variants.ids)], order='create_date desc', limit=1)
							if last_baraa:
								product = last_baraa
						temp = (0,0,{
							'template_id': template.id,
							'material_id': product.id if product else False,
							'price_unit': product.standard_price if product else 0,
							'qty': m_line.qty,
							'warehouse_id': m_line.warehouse_id.id,
						})
						material_datas.append(temp)

					# Жилийнх байвал forecast гүйнэ
					if self.forecast_type != 'year':
						# Хэрэв төлөвлөгөөт зогсолт байгаа эсэхийг шалгах
						# Байвал Forecast үүсгэхгүй
						stop_plan = self.env['maintenance.plan.line'].search([
							('maintenance_type','in',['stopped','pm_service']),
							('technic_id','=',technic.id),
							('state','=','confirmed'),
							('date_required','=',temp_date)])
						if stop_plan:
							temp_date = self._date_increase(temp_date,days)
							continue
					# Зогсолт байхгүй бол
					# Forecast үүсгэх
					vals = {
						'parent_id': self.id,
						'maintenance_type_id': pm_config.maintenance_type_id.id,
						'pm_priority': idx,
						'date_plan': temp_date,
						'technic_id': technic.id,
						'pm_odometer': last_odometer,
						'work_time': pm_config.work_time,
						'man_hours': pm_config.total_man_hours,
						'pm_material_line': material_datas,
						'description': pm_config.maintenance_type_id.name,
					}
					line = self.env['maintenance.plan.generator.line'].create(vals)
					print('2222', temp_date, days)
					temp_date = self._date_increase(temp_date,days)

				# Хэрэв жилийнх бол
				# Заасан огнооноос илүү дутуу үүссэн LINE ийг устгах
				if self.forecast_type == 'year':
					lines = self.env['maintenance.plan.generator.line'].search([
						('parent_id','=',self.id),
						('date_plan','<',self.date_start),
					])
					lines.unlink()

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, add):
		return temp_date + timedelta(days=add)
	# Мото цагийн INTERVAL-аар бүхэлчлэх
	def _round_by_interval(self, x, interval):
		vld = x % interval
		if vld > interval/2:
			return (x//interval+1)*interval
		else:
			return (x//interval)*interval

	# Miils рүү хөрвүүлэх
	def _unix_time_millis(self, dt, add):
		epoch = datetime.utcfromtimestamp(0).date()
		date_start = dt
		date_start += timedelta(hours=8+add)
		return (date_start - epoch).total_seconds() * 1000.0

	# Calendar дата бэлдэх
	def get_plan_calendar_datas(self, g_id, mt_ids, context=None):
		datas = {}
		obj = self.env['maintenance.plan.generator'].browse(g_id)
		series = []
		pm_names = {}
		for line in obj.plan_generated_line:
			if mt_ids:
				# Хэрэв шүүлттэй бол
				if line.maintenance_type_id.id in mt_ids:
					temp = {
						'id': 0,
						'name': line.name,
						'technic_name': line.technic_id.name,
						'pm_odometer': line.pm_odometer,
						'work_time': line.work_time,
						'color': line.maintenance_type_id.color,
						'startDate': self._date_increase(line.date_plan,0),
						'endDate': self._date_increase(line.date_plan,round(line.work_time/24)),
					}
					series.append(temp)
			else:
				# Шүүлтгүй бол бүгдийг зурна
				temp = {
					'id': 0,
					'name': line.name,
					'technic_name': line.technic_id.name,
					'pm_odometer': line.pm_odometer,
					'work_time': line.work_time,
					'color': line.maintenance_type_id.color,
					'startDate': self._date_increase(line.date_plan,0),
					'endDate': self._date_increase(line.date_plan,round(line.work_time/24)),
				}
				series.append(temp)
			if line.maintenance_type_id.name not in pm_names:
				pm_names[line.maintenance_type_id.name] = {
					'name':line.maintenance_type_id.name,
					'id': line.maintenance_type_id.id,
					'color': line.maintenance_type_id.color,
				}
		if series:
			datas['calendar_data'] = series
			datas['pm_names'] = pm_names
		else:
			datas['calendar_data'] = False
			datas['pm_names'] = False
		return datas

	# Timeline дата бэлдэх
	def get_plan_datas(self, g_id, context=None):
		datas = {}
		obj = self.env['maintenance.plan.generator'].browse(g_id)
		series = []
		temp_dict = {}
		for line in obj.plan_generated_line:
			temp = {
				'from': self._unix_time_millis(line.date_plan, 0),
				'to': self._unix_time_millis(line.date_plan, line.work_time),
				'technic_name': line.technic_id.name,
				'info': u'<b>Гүйлт: '+str(line.pm_odometer)+u', Зогсох цаг: '+str(line.work_time)+'</b>',
			}
			if line.name not in temp_dict:
				temp_dict[ line.name ] = [temp]
			else:
				temp_dict[ line.name ].append(temp)

		for key in temp_dict:
			temp = {
				'name': key,
				'intervals': temp_dict[key],
			}
			series.append(temp)
		if series:
			datas['timeline_data'] = series
		else:
			datas['timeline_data'] = False
		return datas

	# Pivot оор харах
	def see_expenses_view(self):
		if self.plan_generated_line:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup('mw_technic_maintenance.plan_generator_expense_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance.plan_generator_expense_report_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			return {
				'name': self.name,
				'view_mode': 'pivot',
				'res_model': 'plan.generator.expense.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('g_id','=',self.id)],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

	def export_report(self):
		# GET datas
		query = """
			SELECT
				tt.report_order as report_order,
				tt.technic_type as technic_type,
				tt.technic_name as technic_name,
				tt.technic_id as technic_id,
				tt.dddd as dddd,
				array_agg(tt.description) as description,
				min(tt.mtt_id) as mtt_id,
				sum(tt.work_time) as work_time
			FROM (
				SELECT
					t.report_order as report_order,
					t.technic_type as technic_type,
					t.program_code as technic_name,
					t.id as technic_id,
					plan.date_plan as dddd,
					plan.description as description,
					plan.maintenance_type_id as mtt_id,
					plan.work_time as work_time
				FROM maintenance_plan_generator_line as plan
				LEFT JOIN technic_equipment as t on (t.id = plan.technic_id)
				WHERE
					  plan.parent_id = %d and
					  plan.date_plan >= '%s' and
					  plan.date_plan <= '%s'

				UNION ALL

				SELECT
					t.report_order as report_order,
					t.technic_type as technic_type,
					t.program_code as technic_name,
					t.id as technic_id,
					null as dddd,
					'' as description,
					null as mtt_id,
					0 as work_time
				FROM technic_setting_line as tsl
				LEFT JOIN technic_equipment as t on (t.id = tsl.technic_id)
				WHERE
					  tsl.parent_id = %d
			) as tt
			GROUP BY tt.report_order, tt.technic_type, tt.technic_name, tt.technic_id, tt.dddd
			ORDER BY tt.report_order, tt.technic_name, tt.dddd
		""" % (self.id, self.date_start, self.date_end, self.id)
		self.env.cr.execute(query)
		# print ('======', query)
		plans = self.env.cr.dictfetchall()
		# GET dates
		query_dates = """
			SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
		""" % (self.date_start, self.date_end)
		self.env.cr.execute(query_dates)
		dates_result = self.env.cr.dictfetchall()

		if plans:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Forecast report.xlsx'

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

			header_date = workbook.add_format({'bold': 1})
			header_date.set_text_wrap()
			header_date.set_font_size(7)
			header_date.set_align('center')
			header_date.set_align('vcenter')
			header_date.set_border(style=1)
			header_date.set_bg_color('#E9A227')

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

			contest_right0 = workbook.add_format({'italic':1})
			contest_right0.set_text_wrap()
			contest_right0.set_font_size(10)
			contest_right0.set_align('right')
			contest_right0.set_align('vcenter')

			contest_right_red = workbook.add_format({'italic':1})
			contest_right_red.set_text_wrap()
			contest_right_red.set_font_size(10)
			contest_right_red.set_align('right')
			contest_right_red.set_align('vcenter')
			contest_right_red.set_bg_color('#F89681')

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
			for mtt in self.env['maintenance.type'].search([]):
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
			worksheet.write(0,2, self.name, h1)

			# TABLE HEADER
			row = 1
			worksheet.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet.set_row(2, 20)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+1, 2, u"Техникийн модел", header_wrap)
			worksheet.set_column(2, 2, 25)
			worksheet.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column(3, 3, 10)
			# Сарын өдрүүд зурах
			start_date = self.date_start
			end_date = self.date_end
			col = 4
			col_dict = {}
			for ll in dates_result:
				worksheet.write(row+1, col, ll['dddd'].strftime("%Y-%m-%d"), header_wrap)
				col_dict[ll['dddd']] = col
				col += 1
			worksheet.set_column(4, col-1, 6)

			worksheet.merge_range(row, 4, row, col-1, datetime.strftime(self.date_start, '%Y-%m-%d')+u" -> "+ datetime.strftime(self.date_end, '%Y-%m-%d'), header_date)
			days = (end_date-start_date).days
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
					technic = self.env['technic.equipment'].browse(line['technic_id'])
					worksheet.write(row, 2, technic.name, contest_left)
					worksheet.write(row, 3, '', contest_left)

					norm = technic.technic_setting_id.work_time_per_day or 1
					worksheet.write(row, col+1, days*norm, contest_center)
					worksheet.write_formula(row, col+2,
						'{=SUM('+self._symbol(row,4) +':'+ self._symbol(row, col)+')}', contest_center)
					worksheet.write_formula(row, col+3,
						'{=ROUND(100-('+self._symbol(row,col+2) +'*100/'+ self._symbol(row, col+1)+'),2)}', contest_center)
					sub_totals_address[3].append(self._symbol(row,col+3))

					number += 1
					row += 1

				rr = technic_dict[line['technic_name']]
				if line['dddd'] in col_dict:
					cc = col_dict[line['dddd']]
					# TIME COLOR
					tmp_style = False
					if line['mtt_id']:
						tmp_style = color_styles[line['mtt_id']][1]
					worksheet.write(rr, cc, line['work_time'], tmp_style)

				# Тайлбар
				if line['description']:
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
				worksheet.write(key, col, descriptions_dict[key], contest_left)

			# Sub total
			row_start = 3
			for key in type_dict:
				rr = type_dict[key][1]
				row_start = type_dict[key][0]
				worksheet.write_formula(rr, col+1,
					'{=SUM('+self._symbol(row_start,col+1) +':'+ self._symbol(rr-1, col+1)+')}', sub_total)
				worksheet.write_formula(rr, col+2,
					'{=SUM('+self._symbol(row_start,col+2) +':'+ self._symbol(rr-1, col+2)+')}', sub_total)
				worksheet.write_formula(rr, col+3,
					'{=AVERAGE('+self._symbol(row_start,col+3) +':'+ self._symbol(rr-1, col+3)+')}', sub_total)
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
				worksheet.write(row, 2, color_styles[key][0], contest_right0)
				worksheet.write(row, 3, '', color_styles[key][1])
				row += 1

			# Хэрэглэх материалын нийт тоо болон үлдэгдэл харуулах
			if self.forecast_type != 'other':
				col += 5
				worksheet.set_column(col, col, 45)
				worksheet.write(2, col, u"Бараа материал", header_wrap)
				worksheet.write(2, col+1, u"Үлдэгдэл", header_wrap)
				worksheet.write(2, col+2, u"Хэрэгцээт тоо", header_wrap)
				query = """
					SELECT
						lll.material_id as product_id,
						min(lll.warehouse_id) as warehouse_id,
						sum(lll.qty) as qty
					FROM maintenance_pm_material_line as lll
					LEFT JOIN maintenance_plan_generator_line as plan on plan.id = lll.generator_id
					LEFT JOIN technic_equipment as t on (t.id = plan.technic_id)
					WHERE
						  plan.parent_id = %d and
						  plan.date_plan >= '%s' and
						  plan.date_plan <= '%s'
					GROUP BY lll.material_id, lll.warehouse_id
					ORDER BY lll.material_id
				""" % (self.id, self.date_start, self.date_end)
				self.env.cr.execute(query)
				# print '======', query
				row = 3
				materials = self.env.cr.dictfetchall()
				for line in materials:
					product = self.env['product.product'].browse(line['product_id'])
					if product:
						worksheet.write(row, col, product.display_name, contest_left)
						vld = 0
						warehouse = self.env['stock.warehouse'].browse(line['warehouse_id'])
						if warehouse:
							vld = self.get_available(product, warehouse)
						worksheet.write(row, col+1, vld, contest_right0)
						if vld >= line['qty']:
							worksheet.write(row, col+2, line['qty'], contest_right0)
						else:
							worksheet.write(row, col+2, line['qty'], contest_right_red)
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

	# Барааны үлдэгдэл авах
	def get_available(self, product_id, warehouse_id):
		total_available_qty = 0
		quant_obj = self.env['stock.quant']
		total_available_qty = sum(self.env['stock.quant'].search([('product_id','=',product_id.id),('location_id.set_warehouse_id','=',warehouse_id.id)]).mapped('quantity'))
		return total_available_qty

	# Жилийн хугацааны ТББК авах
	def _get_year_tbbk(self, date1, date2):
		query = """
			SELECT technic_id, mm, sum(work_time) as work_time FROM (
				SELECT
					to_char(ll.date_plan,'YYYY-mm') as mm,
					ll.technic_id as technic_id,
					ll.work_time as work_time
				FROM maintenance_plan_generator_line as ll
				LEFT JOIN maintenance_plan_generator as pl on pl.id = ll.parent_id
				WHERE pl.forecast_type = 'year' and
					 pl.state = 'done' and
					 ll.date_plan >= '%s' and
					 ll.date_plan <= '%s'
				UNION ALL
				SELECT
					to_char(lll.date_plan,'YYYY-mm') as mm,
					lll.technic_id as technic_id,
					lll.work_time as work_time
				FROM maintenance_long_term_line as lll
				LEFT JOIN maintenance_long_term as ll on ll.id = lll.parent_id
				LEFT JOIN technic_component_part as comp on comp.id = lll.component_id
				WHERE (lll.repair_it = 't' or lll.repair_it = true or lll.is_d_check = 't' and lll.is_d_check = true or lll.last_maintenance = 'main_service') and
					 ll.state = 'done' and
					 lll.date_plan >= '%s' and
					 lll.date_plan <= '%s'
			) as tt
			GROUP BY tt.technic_id, tt.mm
			ORDER BY tt.technic_id, tt.mm
		""" % (date1, date2, date1, date2)
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()
		if not query_result:
			return False

		# ===============================================
		datas = {}
		for line in query_result:
			norm = 1
			technic = self.env['technic.equipment'].browse(line['technic_id'])
			if technic.owner_type == 'own_asset':
				if technic.technic_setting_id and technic.is_tbb_report:
					if line['technic_id'] not in datas:
						norm = technic.technic_setting_id.work_time_per_day or 1
						datas[line['technic_id']] = {}
					if line['mm'] not in datas[line['technic_id']]:
						# Нийт өдрийг олох
						days = monthrange(int(line['mm'][:4]),int(line['mm'][5:7]))[1]
						font_times = norm*days
						tbbk = ((font_times-line['work_time'])*100) / font_times
						if tbbk < 0:
							_logger.info("---TBBK ====== %d %s %d %d %d %d", line['technic_id'], line['mm'], days, norm, font_times, tbbk)
						datas[line['technic_id']][line['mm']] = tbbk
		return datas

	def _get_year_tbbk_excel(self, date1, date2):
		query = """
			SELECT
					tt.report_order as report_order,
					tt.technic_type as technic_type,
					tt.technic_name as technic_name,
					tt.technic_id as technic_id,
					tt.mm as mm,
					sum(work_time) as work_time
			FROM (
				SELECT
					t.report_order as report_order,
					t.technic_type as technic_type,
					t.name as technic_name,
					ll.technic_id as technic_id,
					to_char(ll.date_plan,'YYYY-mm') as mm,
					ll.work_time as work_time
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
					t.name as technic_name,
					lll.technic_id as technic_id,
					to_char(lll.date_plan,'YYYY-mm') as mm,
					lll.work_time as work_time
				FROM maintenance_long_term_line as lll
				LEFT JOIN maintenance_long_term as ll on ll.id = lll.parent_id
				LEFT JOIN technic_component_part as comp on comp.id = lll.component_id
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
					llll.technic_id as technic_id,
					to_char(llll.date_plan,'YYYY-mm') as mm,
					llll.work_time as work_time
				FROM tire_forecast_line as llll
				LEFT JOIN tire_plan_generator as tire on tire.id = llll.parent_id
				LEFT JOIN technic_equipment as t on (t.id = llll.technic_id)
				WHERE
					 tire.state in ('confirmed','done') and
					 llll.date_plan >= '%s' and
					 llll.date_plan <= '%s'
			) as tt
			GROUP BY tt.report_order, tt.technic_type, tt.technic_name, tt.technic_id, tt.mm
			ORDER BY tt.report_order, tt.technic_type, tt.technic_name, tt.mm
		""" % (date1, date2, date1, date2, date1, date2)
		print ('=====year tbbk', query)
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()
		return query_result

class MaintenancePlanGeneratorLine(models.Model):
	_name = 'maintenance.plan.generator.line'
	_description = 'Maintenance plan generator line'
	_order = 'date_plan, maintenance_type_id'

	@api.depends('maintenance_type_id')
	def _set_name(self):
		for obj in self:
			obj.name = str(obj.maintenance_type_id.name)
		return True

	# Columns
	parent_id = fields.Many2one('maintenance.plan.generator', string=u'Parent generator', ondelete='cascade')
	name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True)

	maintenance_type_id = fields.Many2one('maintenance.type', string=u'Засварын төрөл', required=True,)
	date_plan = fields.Date(u'Огноо', copy=False, required=True,)

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True,)
	pm_odometer = fields.Float(string=u'Хийгдэх гүйлт', required=True,)
	pm_priority = fields.Integer(string=u'PM дугаар', readonly=True, default=0)
	is_pm = fields.Boolean(related="maintenance_type_id.is_pm", string="PM эсэх")

	work_time = fields.Float(string=u'Засварын цаг', )
	man_hours = fields.Float(string=u'Хүн/цаг', readonly=True, )
	description = fields.Char('Тайлбар', )

	plan_id = fields.Many2one('maintenance.plan.line', string=u'Холбоотой төлөвлөгөө', readonly=True, )
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
		string=u'Ээлж', default='day')

	# Нийт зардал
	@api.depends('pm_material_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.pm_material_line.mapped('amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Материалын дүн', digits=(16,1))
	pm_material_line = fields.One2many('maintenance.pm.material.line', 'generator_id', string='Material lines', )

	# ============ Override ===============
	# def unlink(self):
	# 	for s in self:
	# 		if s.plan_id and s.plan_id.state != 'draft':
	# 			raise UserError(_(u'Төлөвлөгөө үүссэн байна. Устгах боломжгүй!'))
	# 	return super(MaintenancePlanGeneratorLine, self).unlink()

	# ============ Custom =================
	def create_plan(self):
		for obj in self:
			# Сарынx бол төлөвлөгөө үүсгэхгүй
			if obj.parent_id.forecast_type != 'weekly':
				return
			# Material data
			material_datas = []
			for m_line in obj.pm_material_line:
				if m_line.material_id:
					temp = (0,0,{
						'template_id': m_line.template_id.id,
						'product_id': m_line.material_id.id,
						'price_unit': m_line.material_id.standard_price,
						'qty': m_line.qty,
						'is_pm_material': True,
						'warehouse_id': m_line.warehouse_id.id,
					})
					material_datas.append(temp)
				else:
					raise Warning(('%s-%s дээрх %s (%s)бараа хувилбаргүй байна. /Object id:%s/\nОрлуулж болох өөр бараа сонгон уу! эсвэл Хувилбар нэмнэ үү!') % (obj.technic_id.name, obj.maintenance_type_id.name,m_line.template_id.name,m_line.template_id.default_code,m_line.template_id.id))

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
				'origin': 'Generated: '+obj.parent_id.name,
				'maintenance_type_id': obj.maintenance_type_id.id,
				'pm_priority': obj.pm_priority,
				'maintenance_type': 'pm_service',
				'contractor_type': 'internal',
				'generator_line_id': obj.id,
				'date_required': obj.date_plan,
				'technic_id': obj.technic_id.id,
				'start_odometer': obj.pm_odometer,
				'work_time': temp_work_time,
				'man_hours': obj.man_hours,
				'description': obj.description,
				'required_material_line': material_datas,
				'shift': obj.shift,
			}
			plan = self.env['maintenance.plan.line'].create(vals)
			plan.action_to_confirm()
			obj.plan_id = plan.id
			# obj.description = 'Plans: '+ str(plan.id)

			# Хэрэв зөрүү цаг байвал шөнийн план үүсгэх
			if temp_work_time_2 > 0:
				if obj.shift == 'day':
					# Шөнийн ПЛАН үүсгэх
					vals = {
						'branch_id': obj.technic_id.branch_id.id,
						'origin': 'Generated: '+obj.parent_id.name + ', REF plan:'+str(obj.plan_id.name),
						'maintenance_type_id': obj.maintenance_type_id.id,
						'pm_priority': obj.pm_priority,
						'maintenance_type': 'pm_service',
						'contractor_type': 'internal',
						'generator_line_id': obj.id,
						'date_required': obj.date_plan,
						'technic_id': obj.technic_id.id,
						'start_odometer': obj.pm_odometer,
						'work_time': temp_work_time_2,
						'description': obj.description,
						'required_material_line': material_datas,
						'shift': 'night',
						'ref_plan_id': plan.id,
					}
					plan2 = self.env['maintenance.plan.line'].create(vals)
					plan2.action_to_confirm()
					obj.plan_id = plan2.id
					# obj.description += ', '+str(plan2.id)
				else:
					# Маргааш өдрийн ПЛАН үүсгэх
					vals = {
						'branch_id': obj.technic_id.branch_id.id,
						'origin': 'Generated: '+obj.parent_id.name + ', REF plan:'+str(obj.plan_id.name),
						'maintenance_type_id': obj.maintenance_type_id.id,
						'pm_priority': obj.pm_priority,
						'maintenance_type': 'pm_service',
						'contractor_type': 'internal',
						'generator_line_id': obj.id,
						'date_required': obj._date_increase(obj.date_plan,1),
						'technic_id': obj.technic_id.id,
						'start_odometer': obj.pm_odometer,
						'work_time': temp_work_time_2,
						'description': obj.name,
						'required_material_line': material_datas,
						'shift': 'day',
						'ref_plan_id': plan.id,
					}
					plan2 = self.env['maintenance.plan.line'].create(vals)
					plan2.action_to_confirm()
					obj.plan_id = plan2.id
					# obj.description += ', '+str(plan2.id)

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, add):
		return temp_date + timedelta(days=add)

	# Огноо өөрчилвөл хойш гүйж засна
	# ӨХ хийх өдрийг нааш цааш нь татах үед дагаж өөрчлөгддөг болгох
	def change_to_date(self):
		con = dict(self._context)
		con['line_id'] = self.id
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'forecast.change.date',
			'view_mode': 'form',
			'context': con,
			'target': 'new',
		}

# Change order date
class ForecastChangeDate(models.TransientModel):
	_name = 'forecast.change.date'
	_description = u'forecast change date'

	date = fields.Date('Солих Огноо', required=True)

	def change_to_date(self):
		if self._context['line_id']:
			obj = self.env['maintenance.plan.generator.line'].browse(self._context['line_id'])
			if obj.date_plan:
				d1 = self.date
				d2 = obj.date_plan
				days = (d1 - d2).days
				if days != 0:
					wtpd = obj.technic_id.technic_setting_id.work_time_per_day
					ref_lines = self.env['maintenance.plan.generator.line'].search([
						('parent_id','=',obj.parent_id.id),
						('technic_id','=',obj.technic_id.id),
						('date_plan','>',obj.date_plan)], order='date_plan')
					for ll in ref_lines:
						ll.date_plan = ll.date_plan + timedelta(days=days)
						ll.pm_odometer += days*wtpd
					obj.date_plan = self.date
					obj.pm_odometer += days*wtpd
					return {
						'type': 'ir.actions.client',
						'tag': 'reload',
					}

class TechinicSeetingLine(models.Model):
	_name = 'technic.setting.line'
	_description = 'Technic setting line'
	_order = 'report_order, program_code, technic_id'

	@api.depends('maintenance_type_id')
	def _set_name(self):
		for obj in self:
			obj.name = str(obj.maintenance_type_id.name)
		return True

	# Columns
	parent_id = fields.Many2one('maintenance.plan.generator', string=u'Parent generator', ondelete='cascade')
	parent_long_term_id = fields.Many2one('maintenance.long.term', string=u'Parent long term', ondelete='cascade')

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,)
	report_order = fields.Char(related='technic_id.report_order', string=u'Sort', readonly=True, store=True)
	program_code = fields.Char(related='technic_id.program_code', string=u'Sort 2', readonly=True, store=True)
	technic_setting_id = fields.Many2one(related='technic_id.technic_setting_id',
		string=u'Техникийн тохиргоо', readonly=True, )
	start_odometer = fields.Float(string=u'Эхлэх гүйлт', required=True,)
	work_time_per_day = fields.Float(string=u'Өдөрт ажиллах цаг', )

	last_date = fields.Date(string=u'Хийгдсэн огноо', )
	last_pm_priority = fields.Integer(string=u'PM дугаар', default=0)
	maintenance_type_id = fields.Many2one('maintenance.type', string=u'PM нэр', readonly=True, )
	description = fields.Text(string=u'Тайлбар', readonly=True, )

	start_date = fields.Date(string=u'Ажиллах эхлэх', )

	@api.onchange('technic_id')
	def onchange_technic_id(self):
		if self.technic_id.technic_setting_id:
			self.work_time_per_day = self.technic_id.technic_setting_id.work_time_per_day

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, add):
		return temp_date + timedelta(days=add)

	# Мото цагийн INTERVAL-аар бүхэлчлэх
	def _round_by_interval(self, x, interval):
		vld = x % interval
		if vld > interval/2:
			return (x//interval+1)*interval
		else:
			return (x//interval)*interval

	# Зөвхөн 1 техникийн Forecast үүсгэх
	def create_one_forecast(self):
		# Өмнөх мөрийг устгах
		self.env['maintenance.plan.generator.line'].search([
			('parent_id','=',self.parent_id.id),
			('technic_id','=',self.technic_id.id)]).unlink()

		# Шинээр техникийн план үүсгэх
		last_odometer = self.start_odometer
		last_pm_priority = self.last_pm_priority or self.technic_id.last_pm_priority
		work_time_per_day = self.work_time_per_day

		if work_time_per_day == 0:
				raise UserError(_(u'Өдөрт ажиллах цаг 0 байна! %s %d' % (self.technic_id.technic_setting_id.name, self.technic_id.technic_setting_id.id)))

		if not self.technic_id.technic_setting_id.pm_material_config:
			raise UserError(_(u'PM үйлчилгээний тохиргоо хийгдээгүй байна!'))

		pm_line_ids = [0]
		for pm_line in self.technic_id.technic_setting_id.pm_material_config:
			pm_line_ids.append(pm_line.id)

		# Сүүлд хийгдсэн PM дугаар авна
		idx = last_pm_priority
		# Сүүлд хийгдсэн PM огноо байвал авна, үгүй бол эхлэх огноог авна
		first = True
		temp_date = datetime.now().date()
		if self.parent_id.forecast_type == 'year':
			if self.parent_id.start_last_info:
				temp_date = self.last_date
				last_odometer = self.start_odometer
			else:
				temp_date = self.parent_id.date_start
		# temp_date = self.date_start
		# Дуусах огноо хүртэл давтана
		while temp_date < self.parent_id.date_end:
			# Next PM олох
			if idx+1 < len(pm_line_ids):
				idx += 1
			else:
				idx = 1

			# Дараагийн PM авах
			pm_config = self.env['maintenance.pm.material.config'].browse(pm_line_ids[idx])
			if pm_config.work_time <= 0:
				continue
			interval = pm_config.interval
			if interval <= 0:
				raise UserError(_(u'Interval-ийг тохируулна уу! %s' % pm_config.name))
			# Мото цагийн INTERVAL-аар бүхэлчлэх
			if self.parent_id.is_round_interval:
				last_odometer = self._round_by_interval(last_odometer, interval)

			# INTERVAL-ийг өдөр лүү хөрвүүлнэ
			days = round(interval / work_time_per_day)
			_logger.info("---generate ======%s %s %d %d %d %d",self.technic_id.name, temp_date, last_odometer, self.technic_id.total_odometer, interval, days)

			# Техникийн тохиргоон дээр ажиллаж эхлэх огноо байгаа эсэхийг шалгах
			# Хэрэв эхлэх огноо байхгүй бол хэвийн forecast гүйж үргэлжлэнэ
			# Эхлэх огноо зааж өгсөн байгаад болоогүй бол forecast ийг гүйлгэхгүй алгасна
			if self.start_date and self.start_date > temp_date:
				temp_date = self._date_increase(temp_date,days)
				continue
			# ===========================================

			# Зөв эхлэлийг олох
			# Хэрэв хийгдэх мото цаг нь болоогүй бол хойшлуулна
			if first:
				current_mh = self.technic_id.total_odometer if self.technic_id.odometer_unit == 'motoh' else self.technic_id.total_km
				# Гүйлтийн зөрүү арилгах эсэх
				if self.parent_id.clear_odometer_diff == 'half_day':
					current_mh += work_time_per_day/2
				elif self.parent_id.clear_odometer_diff == 'full_day':
					current_mh += work_time_per_day
				elif self.parent_id.clear_odometer_diff == 'three_day':
					current_mh += work_time_per_day*3
				# ===========================
				diff = (last_odometer+interval) - current_mh
				back_day = round(diff / work_time_per_day)
				if back_day >= 1  and diff > 0:
					temp_date = self._date_increase(temp_date,back_day)
				first = False
			_logger.info("---generate 2=====%s %d %d %d %d",temp_date, (last_odometer+interval), diff, back_day, days)
			# Өнгөрсөн бол давталтаас гарах
			if temp_date >= self.parent_id.date_end:
				break

			last_odometer += interval
			# Материалын дата бэлдэх
			material_datas = []
			for m_line in pm_config.pm_material_line:
				product = m_line.material_id
				if m_line.is_depend_season:
					product = self.env['depending.season.material']._check_depend_season_material(m_line.material_id, temp_date)
				temp = (0,0,{
					'material_id': product.id,
					'price_unit': product.standard_price,
					'qty': m_line.qty,
					'warehouse_id': m_line.warehouse_id.id,
				})
				material_datas.append(temp)

			# Жилийнх байвал forecast гүйнэ
			if self.parent_id.forecast_type != 'year':
				# Хэрэв төлөвлөгөөт зогсолт байгаа эсэхийг шалгах
				# Байвал Forecast үүсгэхгүй
				stop_plan = self.env['maintenance.plan.line'].search([
					('maintenance_type','in',['stopped','pm_service']),
					('technic_id','=',self.technic_id.id),
					('state','=','confirmed'),
					('date_required','=',temp_date)])
				if stop_plan:
					temp_date = self._date_increase(temp_date,days)
					continue
			# Зогсолт байхгүй бол
			# Forecast үүсгэх
			print ('================', pm_config.total_man_hours)
			vals = {
				'parent_id': self.parent_id.id,
				'maintenance_type_id': pm_config.maintenance_type_id.id,
				'pm_priority': idx,
				'date_plan': temp_date,
				'technic_id': self.technic_id.id,
				'pm_odometer': last_odometer,
				'work_time': pm_config.work_time,
				'man_hours': pm_config.total_man_hours,
				'pm_material_line': material_datas,
				'description': pm_config.maintenance_type_id.name,
			}
			line = self.env['maintenance.plan.generator.line'].create(vals)
			_logger.info("---generate last=====%d %s", line.pm_priority, line.maintenance_type_id.name)
			# ++
			temp_date = self._date_increase(temp_date,days)

		# Хэрэв жилийнх бол
		# Заасан огнооноос илүү дутуу үүссэн LINE ийг устгах
		if self.parent_id.forecast_type == 'year':
			lines = self.env['maintenance.plan.generator.line'].search([
				('parent_id','=',self.parent_id.id),
				('date_plan','<',self.parent_id.date_start),
			])
			lines.unlink()
