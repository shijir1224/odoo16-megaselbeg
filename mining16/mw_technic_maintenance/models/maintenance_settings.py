# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class MaintenanceInspectionConfig(models.Model):
	_name = 'maintenance.inspection.config'
	_description = 'Maintenance inspection config'
	_order = 'name'

	# Columns
	name = fields.Char(string=u'Нэр', required=True, copy=False )
	branch_id = fields.Many2one('res.branch', string=u"Салбар", required=True,)

	date_type = fields.Selection([
			('weekly', u'7 хоногоор'),
			('monthly', u'Сараар'),
		], string=u'Огнооны төрөл', required=True, default='weekly')

	config_type = fields.Selection([
			('daily_inspection', u'Daily inspection'),
			('daily_engine_inspection', u'Daily engine inspection'),
			('daily_tire_inspection', u'Daily tire inspection'),
			('daily_lubrication', u'Daily lubrication'),
			('daily_welding_job', u'Welding job'),
			('daily_lather_job', u'Lather job'),
		], string=u'Тохиргооны төрөл', required=True, )

	technic_ids = fields.Many2many('technic.equipment', string=u"Техникүүд",
		help=u'Үзлэг хийгдэх техникийн нэрс')

	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж', required=True, default='day' )

	reason_id = fields.Many2one('maintenance.damaged.reason', string=u"Эвдрэлийн шалтгаан")
	system_id = fields.Many2one('maintenance.damaged.type', string=u"Техникийн систем")

	validator_id = fields.Many2one('res.users', string=u"Хариуцагч")
	planned_time = fields.Float(string=u'Төлөвлөсөн цаг', default=0)
	planned_mans = fields.Float(string=u'Төлөвлөсөн хүн', default=0)

	monday = fields.Boolean(string=u'Даваа', default=False)
	tuesday = fields.Boolean(string=u'Мягмар', default=False)
	wednesday = fields.Boolean(string=u'Лхагва', default=False)
	thursday = fields.Boolean(string=u'Пүрэв', default=False)
	friday = fields.Boolean(string=u'Баасан', default=False)
	saturday = fields.Boolean(string=u'Бямба', default=False)
	sunday = fields.Boolean(string=u'Ням', default=False)

	monthly_days = fields.Char(string=u'Сарын үзлэг хийх өдрүүд',
		help=u'ЖШ: 1,4,7,10,13,16,19,22,25,28,31 гэх мэт',)

	_sql_constraints = [('config_name_uniq', 'unique(name)', 'Нэр давхардсан байна!')]

	# Үзлэгийн хуваариас Үзлэгийн WO үүсгэх - CRON
	def test_create_inspection_wo(self):
		self._auto_create_inspection_wo()

	@api.model
	def _auto_create_inspection_wo(self):
		confs = self.env['maintenance.inspection.config'].search([], order="config_type")
		# Байвал WO үүсгэх
		for line in confs:
			wo_create = False
			today = datetime.now()
			next_day = today + timedelta(days=1)
			# 7 хоног болон сарын тохиргоо эсэхййг шалгана
			if line.date_type == 'weekly':
				# 7 хоногийн тохиргоотой бол
				day_name = next_day.strftime("%A").lower()
				if line.read()[0][day_name]:
					wo_create = True
			else:
				day = int(next_day.strftime("%d"))
				daysss = line.monthly_days.split(',')
				if day in daysss:
					wo_create = True

			if wo_create:
				# Ажилж байгаа болон засварт байгаа техникийг олох
				technic_names = line.technic_ids.filtered(lambda l: l.state in ['working','repairing','draft']).mapped('name')
				# Хэрэв техник байхгүй бол үзлэг үүсгэхгүй
				if line.config_type == 'daily_inspection' and not technic_names:
					continue
				technic_id = False
				if len(line.technic_ids) == 1:
					technic_id = line.technic_ids[0].id
				vals = {
					'branch_id': line.branch_id.id,
					'date_required': next_day,
					'maintenance_type': 'daily_works',
					'origin': line.config_type,
					'description': line.name +': '+','.join(technic_names),
					'performance_description': '.',
					# 'performance_description': ','.join(technic_names) +u' : үзлэг хийв.',
					'contractor_type': 'internal',
					'shift': line.shift,
					'validator_id': line.validator_id.id if line.validator_id else False,
					# 'planned_time': line.planned_time,
					'planned_mans': line.planned_mans,
					'damaged_reason_id': line.reason_id.id,
					'damaged_type_id': line.system_id.id,
					'technic_id': technic_id,
				}
				wo_id = self.env['maintenance.workorder'].create(vals)
				wo_id._create_planned_time_line(line.planned_time)

	# PRINT
	def get_technic_names(self, ids):
		text = u'Техник заагаагүй'
		obj = self.env['maintenance.inspection.config'].search([('id','=',ids)])
		if obj.technic_ids:
			text = ','.join(obj.technic_ids.mapped('name'))
		return text

class MaintenanceDelayReason(models.Model):
	_name = 'maintenance.delay.reason'
	_description = 'Maintenance delay reason'
	_order = 'name'

	@api.depends('code','name')
	def name_get(self):
		result = []
		for s in self:
			name = str(s.code) +'. '+ s.name
			result.append((s.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('code', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	# Columns
	name = fields.Char(u'Нэр', required=True, size=64, copy=False )
	code = fields.Char(u'Код', required=True, size=18, )
	color = fields.Char(u'Өнгө', required=True, default='#fcba03')
	description = fields.Text(u'Тайлбар', )
	is_maintenance_reason = fields.Boolean(string=u'Засварын цаг эсэх', required=True,
		default=False)

	_sql_constraints = [('delay_reason_name_uniq', 'unique(name)', 'Нэр давхардсан байна!')]

class MaintenanceType(models.Model):
	_name = 'maintenance.type'
	_description = 'Maintenance type'
	_order = 'name'

	# Columns
	name = fields.Char(string=u'Нэр', required=True, size=64, copy=False )
	color = fields.Char(string=u'Өнгө', required=True, default='#fcba03')
	is_pm = fields.Boolean(string=u'PM үйлчилгээ эсэх', default=False)
	is_waiting_part = fields.Boolean(string=u'Зогсолт эсэх', default=False)
	is_waiting_tire = fields.Boolean(string=u'Дугуй хүлээх', default=False)
	description = fields.Text(u'Тайлбар', )

	_sql_constraints = [('type_name_uniq', 'unique(name)','Нэр давхардсан байна!'),]

class MaintenanceDamagedReason(models.Model):
	_name = 'maintenance.damaged.reason'
	_description = 'Maintenance damaged reason'
	_order = 'name'

	@api.depends('code','name')
	def name_get(self):
		result = []
		for s in self:
			name = s.code +'. '+ s.name
			result.append((s.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('code', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	# Columns
	name = fields.Char(u'Нэр', required=True, size=64, )
	code = fields.Char(u'Код', required=True, size=8, )
	description = fields.Text(u'Тайлбар', )
	company_id = fields.Many2one('res.company', string="Компани", tracking=True, default=lambda self: self.env.user.company_id)

	_sql_constraints = [('damaged_reason_name_uniq', 'unique(name,company_id)','Нэр давхардсан байна!')]

class WorkorderRateDescription(models.Model):
	_name = 'workorder.rate.description'
	_description = 'Workorder rate description'
	_order = 'name'
	# Columns
	name = fields.Char(u'Тайлбар', required=True, )

class MaintenanceDamagedType(models.Model):
	_name = 'maintenance.damaged.type'
	_description = 'Maintenance damaged type'
	_order = 'name'

	@api.depends('code','name')
	def name_get(self):
		result = []
		for s in self:
			name = s.code +' / '+ s.name
			result.append((s.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('code', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	# Columns
	name = fields.Char(u'Нэр', required=True, size=64, )
	code = fields.Char(u'Код', required=True, size=10, )
	parent_id = fields.Many2one('maintenance.damaged.type', string=u'Толгой систем', copy=False,)
	description = fields.Text(u'Тайлбар', )
	is_oil_sample = fields.Boolean(string=u"Тосны эд анги эсэх")
	company_id = fields.Many2one('res.company', string="Компани", tracking=True, default=lambda self: self.env.user.company_id)
	child_parent_ids = fields.One2many('maintenance.damaged.type','parent_id', string='Children')

	_sql_constraints = [('damaged_type_name_uniq', 'unique(name)','Нэр давхардсан байна!')]

class MaintenanceExperienceLibrary(models.Model):
	_name = 'maintenance.experience.library'
	_description = 'Maintenance experience library'
	_order = 'name'
	# Columns

	@api.depends('damaged_type_id','damaged_reason_id')
	def _set_name(self):
		for obj in self:
			if obj.damaged_type_id and obj.damaged_reason_id:
				obj.name = obj.damaged_type_id.name +' / '+ obj.damaged_reason_id.name

	@api.model
	def _get_user(self):
		return self.env.user.id

	name = fields.Char(string=u'Нэр', compute=_set_name, store=True, )
	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Эвдрэлийн төрөл',
		copy=False, required=True,)
	damaged_reason_id = fields.Many2one('maintenance.damaged.reason', string=u'Эвдрэлийн шалтгаан', copy=False,)
	description = fields.Text(string=u'Хийгдэх ажил', required=True,)
	performance_description = fields.Text(string=u'Хийгдсэн ажил', required=True,)
	workorder_id = fields.Many2one('maintenance.workorder', string=u'Холбоотой WO', copy=False, readonly=True, )
	user_id = fields.Many2one('res.users', string=u'Хэрэглэгч', default=_get_user, readonly=True)

	warehouse_id = fields.Many2one('stock.warehouse', string=u'Салбар', readonly=True)
