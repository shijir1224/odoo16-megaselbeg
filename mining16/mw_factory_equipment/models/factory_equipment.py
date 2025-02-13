# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import ODOMETER_UNIT
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

TECHNIC_TYPE.append(('equipment','Тоног төхөөрөмж'))

class TechnicModelModel(models.Model):
	_inherit = 'technic.model.model'

class TechnicInspection(models.Model):
	_inherit = 'technic.inspection'
	_description = 'Тоног төхөөрөмжийн үзлэг'

	equipment_id = fields.Many2one('factory.equipment', string='Equipment',  )
	# technic_id = fields.Many2one('technic.equipment', string='Technic', required=False, )
	department_id = fields.Many2one('hr.department', string='Хэсэг' ,default=lambda self: self.env.user.department_id.id,)
	equipment_num = fields.Char(related='equipment_id.vin_number' ,  string='Тоног төхөөрөмжийн дугаар')
	responent_ids = fields.Many2many('hr.employee', string=u'Ажилтан')
	work_hours = fields.Float(string='Ажилласан цаг')
	inspection_type = fields.Selection(selection_add=[('planned', 'Төлөвлөгөөт'),('unplanned','Төлөвлөгөөт бус')])
	
	def print_inspection_equipment(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','technic.inspection')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','equipment')], limit=1)

		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

	def get_inspection_lines(self):
		return

	def _check_date_technic(self):
		for obj in self:
			check_ids = self.env['technic.inspection'].search([('date_inspection','=',obj.date_inspection),
											  '|',('technic_id','=',obj.technic_id.id if obj.technic_id else False),('equipment_id','=',obj.equipment_id.id if obj.equipment_id else False),
											  ('shift','=',obj.shift),
											  ('inspection_type','=',obj.inspection_type)])
			if len(check_ids) > 1:
				return False
		return True
	
	def get_inspection(self):
		ctx = dict(self._context or {})
		print ('sssssss' , ctx)
		if 'inspection_id' in ctx:
			return self.env['technic.inspection.setting'].browse(ctx['inspection_id'])
		elif self.equipment_id:
			return self.equipment_id.equipment_setting_id.inspection_config_id
		elif self.technic_id:
			return self.technic_id.technic_setting_id.inspection_config_id
		else:
			return False

	def action_to_open(self):
		if not self.inspection_line:
			inspection_setting = self.inspection_config_id
			print ('inspection_setting' , inspection_setting)
			if inspection_setting:
				for line in inspection_setting.item_line:
					vals = {
						'parent_id': self.id,
						'item_id': line.id,
						'check_name': line.name,
						'is_check': True,
					}
					self.env['technic.inspection.line'].create(vals)
				# Өмнөх үзлэгийн тайлбар
				if self.technic_id:
					last_ins = self.env['technic.inspection'].search([
						('technic_id','=',self.technic_id.id),
						('state','=','done')], order="date_inspection desc", limit=5)
				elif self.equipment_id:
					last_ins = self.env['technic.inspection'].search([
						('equipment_id','=',self.equipment_id.id),
						('state','=','done')], order="date_inspection desc", limit=5)
				notes= ''
				for ll in last_ins:
					if ll.operator_note:
						notes += ll.date_inspection.strftime("%Y-%m-%d")+' : \n('+ll.operator_note+')\n'
				self.previous_operator_note = notes
			else:
				raise UserError(_('Not found Inspection list configuration!'))
		
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('technic.inspection')
		self.setting_name = self.technic_id.technic_setting_id.inspection_config_id.name or ' - ' if self.technic_id else self.equipment_id.equipment_setting_id.inspection_config_id.name or ' - ' if self.equipment_id else '' 
		self.state = 'open'
		self.reminder_note = self.technic_id.technic_setting_id.inspection_config_id.reminder_note if self.technic_id else self.equipment_id.equipment_setting_id.inspection_config_id.reminder_note if self.equipment_id else ''
			
class FactoryFacility(models.Model):
	_name = 'factory.facility'
	_description = 'Facilities'

	name = fields.Char(string='Байгууламжын нэршил', required=True)
	total_odometer = fields.Float(string="Мотоцаг", default=0, readonly=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True)
	equipment_ids = fields.One2many('factory.equipment', 'facility_id', string='Суурилуулсан тоногтөхөөрөмжүүд')

	_sql_constraints = [('name_uniq', 'UNIQUE(name, branch_id)', 'Байгууламж давхцаж болохгүй!')]

class FactoryEquipmentSetting(models.Model):
	_name = 'factory.equipment.setting'
	_description = 'Setting of the factory equipment'
	_inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]
	_order = 'report_order, name'

	@api.depends('model_id','model_id.modelname','model_id.brand_id','model_id.brand_id.name')
	def _set_name(self):
		for item in self:
			if item.model_id:
				item.name = item.model_id.name+' : Тохиргоо'
			else:
				item.name = "New"

	name = fields.Char(compute='_set_name', string=u'Нэр',
					   readonly=True, store=True, default="-")
	model_id = fields.Many2one('technic.model.model',
							   string=u'Загварын нэр', required=True, copy=False)
	inspection_config_id = fields.Many2one('technic.inspection.setting',
		string=u'Үзлэгийн тохиргоо', required=True,)

	report_order = fields.Char(string='Тайлангийн эрэмбэ', default='999')

	seats = fields.Integer(string='Суудлын тоо',
						   help='Number of seats of the vehicle')
	doors = fields.Integer(string='Хаалганы тоо',
						   help='Number of doors of the vehicle')
	# fuel_type = fields.Selection(FUEL_TYPE, string='Энергийн эх үүсвэр', help='Fuel Used by the vehicle')
	# engine_design = fields.Selection(ENGINE_DESIGN, string='Хөдөлгүүрийн хийц', help='Engine design')

	engine_power = fields.Float(
		string='Хөдөлгүүрийн чадал, квт', digits=(16, 1),)
	engine_capacity = fields.Float(string='Хөдөлгүүрийн багтаамж, литр',
		digits=(16, 1), help='Engine capacity litre')
	engine_mark = fields.Char(string='Хөдөлгүүрийн модель', help='Engine mark...')
	engine_type = fields.Char(string='Хөдөлгүүрийн бренд', help='Engine type...')
	work_time_per_day = fields.Float(string=u'Өдөрт ажиллах цаг', required=True, help=u"Техникийн өдөрт бүтээлтэй ажиллах цаг")
	pm_material_config = fields.One2many('maintenance.pm.material.config', 'equipment_setting_id', string='PM тохиргоо')

	carrying_capacity = fields.Float(
		string='Тэвшний багтаамж, м³', digits=(16, 1), help='Struck capacity(m3)')
	carrying_tonnage = fields.Float(
		string='Тэвшний даац, тн', digits=(16, 1), help='Struck tonnage')
	bucket_capacity = fields.Float(
		string='Шанаганы багтаамж, м³', digits=(16, 1), help='Bucket capacity(m3)')
	blade_capacity = fields.Float(
		string='Хутганы багтаамж, м³', digits=(16, 1), help='Blade capacity(m3)')
	blade_width = fields.Float(
		string='Хусуурын өргөн, м', digits=(16, 1), help='Blade width(m)')
	lifting_capacity = fields.Float(
		string='Өргөх хүчин чадал, тн', digits = (16,1), help='Lifting capacity')
	power_capacity = fields.Float(
		string='Чадал, квт', digits = (16,1), help='power capacity(kilowatt)')
	pressure_capacity = fields.Float(
		string='Даралт, bar', digits = (16,1), help='pressure capacity(bar)')
	volume = fields.Float(
		string='Эзэлхүүн, м³/мин', digits = (16,1), help='volume(bar)')
	electric_current = fields.Float(
		string='Гүйдэл, ампер', digits = (16,1), help='electric_current(A)')
	vibration_power = fields.Float(
		string='Чичиргээний чадал, квт', digits = (16,1), help='vibration power(kilowatt)')


	body_length = fields.Float(string='Нийт урт, м', digits = (16,1), )
	body_width = fields.Float(string='Нийт өргөн, м', digits = (16,1), )
	body_height = fields.Float(string='Нийт өндөр, м', digits = (16,1), )

	fuel_tank_capacity = fields.Float(string='Түлшний танкны багтаамж, литр', digits = (16,1), )
	operating_weight = fields.Float(string='Ажлын жин, тн', digits = (16,1), )

	# transmission = fields.Selection(TRANSMISSION,
	# 	string='Төрөл', help='Transmission Used by the vehicle')
	transmission_type = fields.Char(string="Модель", help="Transmission type")
	transmission_mark = fields.Char(string="Бренд", help="Transmission mark")
	transmission_power = fields.Float(string="Transmission Чадал, квт", help="Transmission power")

	rpm_min = fields.Float(string='RPM Min',digits = (16,1), required=False)
	rpm_ave = fields.Float(string='RPM Average',digits = (16,1), required=False)
	rpm_max = fields.Float(string='RPM Max',digits = (16,1), required=False)
	fuel_low_idle = fields.Float(string='Fuel low idle',digits = (16,1), required=False)
	fuel_medium_idle = fields.Float(string='Fuel medium idle',digits = (16,1), required=False)
	fuel_high_idle = fields.Float(string='Fuel high idle',digits = (16,1), required=False)

	odometer_unit = fields.Selection(ODOMETER_UNIT,
		string='Гүйлтийн нэгж',required=True)

	technic_type = fields.Selection(TECHNIC_TYPE,
		string ='Тоног төхөөрөмжийн төрөл',required=True)

	# technic_sub_type = fields.Selection(TECHNIC_SUB_TYPE,
	# 	string =u'Техникийн дэд төрөл')

	rubber_tired = fields.Boolean(string='Дугуйтай эсэх?', default=True)
	is_plan_by_time = fields.Boolean(string=u'Хугацаагаар төлөвлөх эсэх?', default=False)
	is_tbb_report = fields.Boolean(string=u'ТББ тооцох эсэх?', default=False)
	is_tbb_mining = fields.Boolean(string=u'Уул ТББ тооцох эсэх?', default=False, tracking=True)
	position_format = fields.Char(string='Байрлалын формат', help=u'ЖШ: 1-2,2-2, дамп 1-2,2-4 гэх мэт')
	tire_counts = fields.Integer(string=u'Нийт дугуйн тоо', default=0)

	component_config_line2 = fields.One2many('technic.component.config', 'parent_id2', string='Компонентийн тохиргоо', )
	img_of_parts = fields.Binary(string='Схем зураг', attachment=True, copy=False,
		help="Picture of parts")
	pic_width = fields.Float(string='Зурагны өргөн', digits = (16,1), required=False)
	pic_height = fields.Float(string='Зурагны өндөр', digits = (16,1), required=False)

	# Баталгаат хугацаа, гүйлт
	warranty_period = fields.Integer(string=u'Баталгаат хугацаа, сар', help=u'Баталгаат хугацааг сараар тооцно')
	warranty_odometer = fields.Integer(string=u'Баталгаат гүйлт', help=u'Баталгаа өгсөн гүйлт')
	technic_ids = fields.One2many('factory.equipment', 'equipment_setting_id', string=u'Техникүүд', readonly=True)
	company_id = fields.Many2one('res.company', string="Компани")

	# Асфальт дэвсэгч
	work_mass = fields.Float(string=u'Ажлын жин, тн')
	length_flat_min = fields.Float(string=u'Дэвсэлтийн ХБ өргөн, м')
	length_flat_max = fields.Float(string=u'Дэвсэлтийн ХИ өргөн, м')
	bunker_capacity = fields.Float(string=u'Бункерийн багтаамж, м3')

	
	# дата бэлдэх
	def get_datas(self, c_id, context=None):
		obj = self.env['technic.equipment.setting'].browse(c_id)
		parts = []
		for line in obj.component_config_line2:
				temp = {
				'number': line.sequence,
				'title': '['+line.component_id.default_code+'] '+line.component_id.name,
				'top': line.position_y,
				'left': line.position_x,
				}
				parts.append(temp)
		return parts

	_sql_constraints = [
		('name_uniq', 'unique(model_id)', 'Model must be unique!'),
	]

	# ------------ OVERRIDE ================
	def write(self, vals):
		res = super(FactoryEquipmentSetting, self).write(vals)
		if 'model_id' in vals:
			model = self.env['technic.model.model'].browse(vals['model_id'])
			model.equipment_setting_id = self.id
		return res

	# Methods
	def get_position_format(self, setting_id, context=None):
		obj = self.env['technic.equipment.setting'].browse(setting_id)
		return obj.position_format or False

	# Default PM тохиргоо үүсгэх
	def set_default_pm_line(self):
		type_ids = self.env['maintenance.type'].sudo().search([('is_pm','=',True)])
		setting_ids = self.env['technic.equipment.setting'].sudo().search([('is_tbb_report','=',True)])
		for setting in setting_ids:
			if setting.technic_type in ['dump','excavator','wheel_excavator','wheel_loader','service_car','loader','dozer','wheel_dozer','grader','water_truck']:
				setting.pm_material_config.sorted('priority')
				if not setting.pm_material_config:
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 1,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 2,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 500')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 3,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 4,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 1000')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 5,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 6,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 500')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 7,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'equipment_setting_id': setting.id,
						'priority': 8,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 2000')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
				# for config in setting.pm_material_config.sorted('priority'):
				# 	if config.priority == 1:
				# 	# type_ids = self.env['maintenance.type'].sudo().search([('is_pm','=',True)])
				# 	if 'PM 250' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 500' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 1000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 2000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 3000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 4000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
					# config

	def _change(self):
		for item in self:
			for tech in item.technic_ids:
				tech.is_tbb_report = item.is_tbb_report
				tech.is_tbb_mining = item.is_tbb_mining

	@api.onchange('is_tbb_mining','is_tbb_report')
	def onchange_is_tbb(self):
		self._change()

class MainMeasurement(models.Model):
	_name = 'equipment.main.attribute'
	_description = 'Equipment main attribute'

	name = fields.Char(string="Үзүүлэлтийн нэршил", required=True)
	value = fields.Char(string="Үзүүлэлтийн утга")
	equipment_id = fields.Many2one('factory.equipment', string="Тоног төхөөрөмж")
	component_id = fields.Many2one('technic.component.part', string="Компонент")

	# Устгахгүй
	def unlink(self):
		for item in self:
			if not item.value:
				return False
		return super(MainMeasurement, self).unlink()

class FactoryEquipment(models.Model):
	_name = 'factory.equipment'
	_description = 'Factory equipment'
	_inherit = ['mail.thread']
	_order = 'report_order, name'


	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', '|', '|', '|',('program_code', operator, name),('park_number', operator, name),('name', operator, name),('vin_number', operator, name),('state_number', operator, name)]
			# if operator in expression.NEGATIVE_TERM_OPERATORS:
			# 	domain = ['&'] + domain
		technics = self.search(domain + args, limit=limit)
		return technics.name_get()
	
	def name_get(self):
		res = []
		for item in self:
			name = item.name or ''
			if item.vin_number:
				# name = item.state_number+'/ ' + item.park_number+' /'+item.model_id.name+'/ '
				name = item.vin_number+' /'+item.name+'/ '
			res.append((item.id, name))
		return res

	@api.depends('owner_type','program_code','park_number', 'model_id', 'model_id.name', 'model_id.brand_id', 'model_id.brand_id.name')
	def _set_name(self):
		for obj in self:
			# if obj.owner_type == 'own_asset' and obj.park_number:
			#     obj.name = obj.park_number+' /'+obj.model_id.name+'/'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
			# elif obj.owner_type == 'rent' and obj.park_number:
			#     obj.name = obj.park_number+' /'+obj.model_id.name+' /RENT'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
			# elif obj.owner_type == 'contracted' and obj.park_number:
			#     obj.name = obj.park_number+' /'+obj.model_id.name+' /CONT'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
			# else:
			#     obj.name = obj.park_number+' /'+obj.model_id.name+'/'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
			obj.name = obj.park_number

	def force_name(self):
		technis = self.env['technic.equipment'].sudo().search([])
		for item in technis:
			item._set_name()

	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,)


	name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True, default="-")
	vin_number = fields.Char(string='Сериал дугаар', required=True,)
	park_number = fields.Char(string='Парк дугаар', required=True, tracking=True,
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	state_number = fields.Char(string='Улсын дугаар',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	document_number = fields.Char(string='Гэрчилгээний дугаар',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	engine_serial = fields.Char(string='Хөдөлгүүрийн сериал',)

	program_code = fields.Char(string=u'Програм код',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	manufactured_date = fields.Date(string=u'Үйлдвэрлэсэн огноо', required=True,
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	start_date = fields.Date(string=u'Эхлэсэн огноо', required=True,
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	color = fields.Char(string='Өнгө',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	asset_id = fields.Many2one('account.asset.asset', string='Холбоотой хөрөнгө', # required=True,
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]}
				)
	partner_id = fields.Many2one('res.partner', string=u'Холбоотой харилцагч', )
	responent_id = fields.Many2one('res.partner', string=u'Хариуцагч')
	department_id = fields.Many2one('hr.department', string=u'Холбоотой хэлтэс', )

	owner_type = fields.Selection(OWNER_TYPE,
		string=u'Эзэмшлийн төрөл', default='own_asset', required=True, tracking=True)

	parent_id = fields.Many2one('factory.equipment', string=u'Толгой тоног төхөөрөмж', required=False,)
	facility_id = fields.Many2one('factory.facility', string=u'Суурилуулсан байгууламж', required=False,)
	equipment_setting_id = fields.Many2one('factory.equipment.setting', string=u'Тоног төхөөрөмжийн тохиргоо',
		required=True, help='Technic norn and setting')
	model_id = fields.Many2one(related='equipment_setting_id.model_id', string='Загвар', readonly=True, store=True)
	image = fields.Binary(related='model_id.image', string='Зураг')
	main_attribute_ids = fields.One2many('equipment.main.attribute','equipment_id', string="Үндсэн үзүүлэлтүүд")

	technic_type = fields.Selection(related='equipment_setting_id.technic_type', string='Техникийн төрөл',
		readonly=True, store=True)
	report_order = fields.Char(related='equipment_setting_id.report_order', string='Тайлангийн эрэмбэ',
		readonly=True, store=True)

	odometer_unit = fields.Selection(related='equipment_setting_id.odometer_unit', string='Гүйлтийн нэгж',
		readonly=True, store=True)

	# OTHER INFO
	carrying_capacity = fields.Float(string='Тэвшний багтаамж, м³', digits=(16, 1), help='Struck capacity(m3)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	carrying_tonnage = fields.Float(string='Тэвшний даац, тн', digits=(16, 1), help='Struck tonnage',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	bucket_capacity = fields.Float(string='Шанаганы багтаамж, м³', digits=(16, 1), help='Bucket capacity(m3)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	blade_capacity = fields.Float(string='Хутганы багтаамж, м³', digits=(16, 1), help='Blade capacity(m3)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	blade_width = fields.Float(string='Хусуурын өргөн, м', digits=(16, 1), help='Blade width(m)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	lifting_capacity = fields.Float(string='Өргөх хүчин чадал, тн', digits = (16,1), help='Lifting capacity',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	power_capacity = fields.Float(string='Чадал, квт', digits = (16,1), help='power capacity(kilowatt)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	pressure_capacity = fields.Float(string='Даралт, bar', digits = (16,1), help='pressure capacity(bar)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	volume = fields.Float(string='Эзэлхүүн, м³/мин', digits = (16,1), help='volume(bar)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	electric_current = fields.Float(string='Гүйдэл, ампер', digits = (16,1), help='electric_current(A)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	vibration_power = fields.Float(string='Чичиргээний чадал, квт', digits = (16,1), help='vibration power(kilowatt)',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	operating_weight = fields.Float(string='Ажлын жин, тн', digits = (16,1),
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	seats = fields.Integer(string='Суудлын тоо', help='Number of seats of the vehicle',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	total_km = fields.Float(string='Нийт KM', digits = (16,1), default=0,
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
	total_odometer = fields.Float(string='Нийт гүйлт', digits = (16,1), default=0,)

	state = fields.Selection([
		('draft','Draft'),
		('stopped','Stopped'),
		('working','Working'),
		('parking','Parking'),
		('repairing','Repairing'),
		('inactive',u'Актласан')],
		string='Төлөв', default='draft', tracking=True)
	status_note = fields.Text(string='Статус тайлбар', readonly=True, )


	tire_line = fields.One2many('technic.tire.line', 'technic_id',string='Дугуй', readonly=True, domain=[('state','=','set')])
	# tire_counts = fields.Integer(related="equipment_setting_id.tire_counts", readonly=True, store=True,)

	move_line_ids = fields.One2many('technic.move.history', 'technic_id',string='Шилжсэн түүх', readonly=True)

	component_part_line = fields.One2many('technic.component.part', 'current_equipment_id',string='Components',
		# readonly=True, domain=[('state','=','set')],
		)
	# img_of_parts = fields.Binary(related='equipment_setting_id.img_of_parts',
	# 	string='Схем зураг', readonly=True, )
	# pic_width = fields.Float(related='equipment_setting_id.pic_width',
	# 	string='Зурагны өргөн', digits = (16,1), required=True)
	# pic_height = fields.Float(related='equipment_setting_id.pic_height',
	# 	string='Зурагны өндөр', digits = (16,1), required=True)

	# Баталгаат хугацаа, гүйлт
	with_warrenty = fields.Boolean(string=u'Баталгаат эсэх?', default=False)
	# warranty_period = fields.Integer(related='equipment_setting_id.warranty_period', string=u'Баталгаат хугацаа',
	# 	help=u'Баталгаат хугацааг сараар тооцно', store=True, readonly=True, )
	# warranty_odometer = fields.Integer(related='equipment_setting_id.warranty_odometer', string=u'Баталгаат гүйлт',
	# 	help=u'Баталгаа өгсөн гүйлт', store=True, readonly=True, )
	warrenty_date = fields.Date(string=u'Баталгаа эхэлсэн огноо',
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	# Даатгалын мэдээлэл
	with_insurance = fields.Boolean(string='Даатгалтай эсэх?', default=False,)
	insurance_company_name = fields.Char(string=u'Даатгалын газар', )
	insurance_payment_amount = fields.Float(string=u'Даатгалын төлбөр', )
	insurance_contract_number = fields.Char(string=u'Даатгал гэрээний дугаар', )
	insurance_date_end = fields.Date(string=u'Даатгал дуусах', )
	# Татвар үзлэг хийх өдөр
	state_inspection_date_end = fields.Date(string=u'Улсын үзлэг дуусах огноо', )
	state_tax_date_end = fields.Date(string=u'Татвар төлөх огноо', )

	# Краны магадлагаа
	validation_register_id = fields.Char(string=u"МХЕГ-н краны бүртгэлийн дугаар")
	validation_start_date = fields.Date(string=u"Магадлагаа хийгдсэн огноо")
	validation_end_date = fields.Date(string=u"Магадлагаа дуусах огноо")

	# @api.depends('warranty_period','warranty_odometer','warrenty_date','with_warrenty')
	# def _get_warranty_info(self):
	# 	for obj in self:
	# 		if obj.with_warrenty:
	# 			txt = "-"
	# 			if obj.warrenty_date and obj.equipment_setting_id.warranty_period > 0:
	# 				a = obj.warrenty_date
	# 				b = datetime.now().date()
	# 				delta = b - a
	# 				days = obj.warranty_period * 30
	# 				if days > delta.days:
	# 					date1 = obj.warrenty_date
	# 					date2 = date1 + timedelta(days=days)
	# 					txt = u"<b style='color:green;'>Дуусах өдөр: %s, Үлдсэн: %d өдөр</b>" % (date2.strftime('%Y-%m-%d'), days-delta.days)
	# 				else:
	# 					txt = u"<b style='color:red;'>Баталгаа дууссан! Хэтэрсэн өдөр: %d</b>" % (delta.days-days)
	# 			if obj.equipment_setting_id.warranty_odometer > 0:
	# 				delta = obj.equipment_setting_id.warranty_odometer - (obj.total_odometer if obj.odometer_unit == 'motoh' else obj.total_km)
	# 				if delta > 0:
	# 					txt += u"<br/><b style='color:green;'>Үлдсэн: %d гүйлт</b>" % (delta)
	# 				else:
	# 					txt += u"<br/><b style='color:red;'>Баталгаа дууссан! Хэтэрсэн гүйлт: %d</b>" % (delta)
	# 			obj.warranty_info = txt
	# 		else:
	# 			obj.warranty_info = '-'
	# warranty_info = fields.Html(string='Warranty info',
	# 	readonly=True, compute="_get_warranty_info", )

	# Галын системийн бүртгэл
	with_fire_system = fields.Boolean(string=u'Галын системтэй эсэх?', default=False)
	# fire_system_state = fields.Selection(FIRE_SYSTEM_STATE,
	# 	string=u'Галын системийн төлөв', default='normal', )
	# fire_system_brand = fields.Selection(FIRE_SYSTEM_BRAND,
	# 	string=u'Системийн бренд', default='fsi', )
	fire_system_type = fields.Char(string=u'Системийн төрөл', help=u'Fire system type')
	# fire_system_type = fields.Selection([
	# 	('fsi',u'FSI'),
	# 	('ansul',u'Ansul'),
	# 	('ansul_china',u'Ansul/China')],
	# 	string=u'Системийн төрөл', default='fsi', )
	fire_system_install_date = fields.Date(string=u'Суурьлуулсан огноо')
	fire_system_last_date = fields.Date(string=u'Сүүлд үйлчилгээ хийгдсэн огноо', )
	fire_system_period = fields.Integer(string=u'Засвар үйлчилгээний давтамж', help=u"Сараар тооцож оруулна уу")

	@api.depends('with_fire_system','fire_system_last_date','fire_system_period')
	def get_next_date(self):
		for obj in self:
			if obj.with_fire_system and obj.fire_system_period and obj.fire_system_last_date:
				date1 = obj.fire_system_last_date
				obj.fire_system_next_date = date1 + relativedelta(months=+obj.fire_system_period)
			else:
				obj.fire_system_next_date = ''
	fire_system_next_date = fields.Date(string=u"Дараагийн үйлчилгээ хийх огноо", readonly=True,
		compute=get_next_date, store=True, default=False)

	# ТББК
	is_tbb_report = fields.Boolean(string=u'ТББ тооцох эсэх?', default=False)
	is_tbb_mining = fields.Boolean(string=u'Уул ТББ тооцох эсэх?', default=False, tracking=True)

	# =================== Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноороглох ёстой!'))
		return super(FactoryEquipment, self).unlink()

	# =================== Custom methods ===================
	def get_odometer_datas(self, t_id, context=None):
		if t_id:
			obj = self.env['technic.equipment'].browse(t_id)
			return {'total_odometer': obj.total_odometer, 'total_km': obj.total_km}
		else:
			return {'total_odometer': 0, 'total_km': 0}

	# Компонентийн ДАТА бэлдэх
	def get_component_datas(self, t_id, context=None):
		parts = []
		if t_id:
			obj = self.env['technic.equipment'].browse(t_id)
			for line in obj.component_part_line:
				position_y = 0
				position_x = 0
				if line.component_config_id:
					position_y = line.component_config_id.position_y
					position_x = line.component_config_id.position_x
				else:
					if line.sequence:
						if line.current_technic_id:
							config_id = line.current_technic_id.equipment_setting_id.component_config_line2.filtered(lambda l: l.sequence == line.sequence)
							position_y = config_id.position_y
							position_x = config_id.position_x
				temp = {
					'top': position_y,
					'left': position_x,
					'number': line.sequence,
					'title': '['+line.product_id.default_code+'] '+line.product_id.name,
					'total_odometer': line.total_odometer,
					'last_odometer': line.last_odometer,
					'diff': line.total_odometer - line.last_odometer,
				}
				parts.append(temp)
		return parts

	# Холбоотой үзлэгүүдийг харах
	def see_inspections(self):
		action = self.env.ref('mw_technic_equipment.action_technic_inspection').read()[0]
		action['domain'] = [('technic_id','=', self.id)]
		return action
	
	# Тоног төхөөрөмжүүд
	def see_child_equipments(self):
		action = self.env.ref('mw_factory_equipment.action_factory_equipment').read()[0]
		action['domain'] = [('parent_id','=', self.id)]
		action['context'] = {}
		return action
	
	def see_parent_equipment(self):
		action = self.env.ref('mw_factory_equipment.action_factory_equipment').read()[0]
		action['context'] = {}
		return action


	# Компонент эд ангийн бүрэн эсэхийг шалгах
	@api.depends('component_part_line','equipment_setting_id.component_config_line2')
	def check_components(self):
		for obj in self:
			message = '-'
			for cl in obj.equipment_setting_id.component_config_line2:
				if cl.component_id.product_tmpl_id.id not in obj.component_part_line.mapped('product_id.product_tmpl_id.id'):
						message += u'<font color="red"><b>[%s] %s</b></font> - эд анги дутуу байна.<br>' % (cl.component_id.default_code, cl.component_id.name)
			for cl in obj.component_part_line:
				if cl.product_id.product_tmpl_id.id not in obj.equipment_setting_id.component_config_line2.mapped('component_id.product_tmpl_id.id'):
						message += u'<font color="green"><b>[%s] %s</b></font> - эд анги илүү байна.<br>' % (cl.product_id.default_code, cl.product_id.name)
			obj.components_info = message

	components_info = fields.Html(string=u"Компонентийн мэдээлэл", readonly=True,
		compute=check_components, store=True, )

	retire_attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', readonly=True,)

	# Санхүү
	account_id = fields.Many2one('account.account', string=u'Данс', copy=False,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]},)
	account_analytic_id = fields.Many2one('account.analytic.account', string=u'Аналитик данс', copy=False,
		states={'done': [('readonly', True)]}, )

	# tulshnii_zarlaga_ids = fields.Many2one('oil.fuel.line', string='Түлшний зарлагын мэдээлэл',)

	is_active = fields.Boolean(string=u'Is Active', default=False)

	_sql_constraints = [
		('technic_uniq', 'unique(vin_number,company_id)', "Тоног төхөөрөмжийн сериал давхардсан байна!"),
	]

	# Зарагдсан техникийг идэвхигүй болгох
	def make_deactive(self):
		self.is_active = True

	def make_active(self):
		self.is_active = True

	@api.onchange('equipment_setting_id')
	def onchange_equipment_setting_id(self):
		if self.equipment_setting_id:
			self.carrying_capacity = self.equipment_setting_id.carrying_capacity
			self.carrying_tonnage = self.equipment_setting_id.carrying_tonnage
			self.bucket_capacity = self.equipment_setting_id.bucket_capacity
			self.write({'is_tbb_report': self.equipment_setting_id.is_tbb_report})
			self.write({'is_tbb_mining': self.equipment_setting_id.is_tbb_mining})

	# ================= CUSTOM METHODs =============
	# Шилжүүлэх
	def move_to_branch(self):
		context = dict(self._context)
		context.update({'technic_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'technic.move.history.wizard',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}
	# Гараар нэмэгдүүлэх
	def manual_increase_odometer(self):
		context = dict(self._context)
		context.update({'technic_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'technic.odometer.increase',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}
	# Техник статус оруулах
	def create_technic_status(self):
		context = dict(self._context)
		context.update({'technic_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'technic.equipment.log.status',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}

	def _check_past_days(self, i_date):
		past_date = datetime.now() + timedelta(days=-4)
		if past_date.date() > i_date:
			return True
		else:
			return False

	# Техник МЦ, КМ нэмэгдүүлэх func
	def _increase_odometer(self, i_date, last_motoh, last_km, diff, diff_km, shift, is_manual=None):
		if self.state not in ['draft']:
			# Гараар нэмж байгаа бол хамаагүй
			if not is_manual:
				# Уулаас нэмж байгаа өдөр нь хэд хоногийн өмнөх эсэхийг шалгана.
				# Заасан хугацаанаас хэтэрсэн бол мото цагийг нэмэхгүй
				if self._check_past_days(i_date):
					return

			motoh = last_motoh - self.total_odometer
			km = last_km - self.total_km
			# Шинэчлэх
			self.total_odometer = last_motoh
			if self.total_km > 0 and last_km > 0:
				self.total_km = last_km
			else:
				self.total_km +=  diff_km

			# Нэмэгдүүлэлт байвал
			if diff > 0:
				motoh = diff
			if diff_km > 0:
				km = diff_km

			# Дугуйтай бол дугуй нэмэгдүүлэх
			if self.rubber_tired:
				for t_line in self.tire_line:
					t_line.tire_id._increase_odometer(i_date, motoh, km, shift)
			# Компоненттэй бол компонент нэмэгдүүлэх
			if self.component_part_line:
				for c_line in self.component_part_line:
					c_line._increase_odometer(i_date, motoh, shift)

	# Дугуйн мэдээлэл зурах
	def get_tire_line_datas(self, technic_id, context=None):
		data = {}
		obj = self.env['technic.equipment'].browse(technic_id)
		for line in obj.tire_line:
			data[line.position] = {'serial': line.serial,'tire_id': line.tire_id.id}
		return data

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_parking(self):
		self.state = 'parking'

	def action_to_inactive(self):
		context = dict(self._context)
		context.update({'technic_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'technic.retire.history.wizard',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}

	def action_to_stop(self):
		self.state = 'stopped'

	def action_to_working(self):
		self.state = 'working'

	# Техникийн Баталгаат хугацаа шалгах - Крон метод - CRON
	def _get_warrenty_period(self):
		if self.with_warrenty:
			if self.start_date and self.equipment_setting_id.warranty_period > 0:
				a = self.start_date
				b = datetime.now().date()
				delta = b - a
				days = self.warranty_period * 30
				return days - delta.days
			else:
				return 0
		else:
			return -1

	def _get_warrenty_odometer(self):
		if self.with_warrenty:
			if self.equipment_setting_id.warranty_odometer > 0:
				delta = self.equipment_setting_id.warranty_odometer - (self.total_odometer if self.odometer_unit == 'motoh' else self.total_km)
				return delta
			else:
				return 0
		return -1

	def test_check_technic_warrenty(self):
		self._check_technic_warrenty()

	@api.model
	def _check_technic_warrenty(self):
		technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('owner_type','=','own_asset'),
				('with_warrenty','=',True)
				], order='report_order, program_code')
		msg = []
		for line in technics:
			txt = ""
			days = line._get_warrenty_period()
			if 0 < days and days < 6:
				txt = u"%d Өдөр дутуу байна" % days
			motoh = line._get_warrenty_odometer()
			if 0 < motoh and motoh < 100:
				txt += u"%d Гүйлт дутуу байна" % motoh

			if txt:
				msg.append(str(line.program_code)+': '+txt)
		if msg:
			# Get group
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_equipment'),
				('name','in',['group_technic_module_admin'])])
			group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
			partners = []
			for receiver in group.users:
				if receiver.partner_id:
					if self.env.user.partner_id.id != receiver.partner_id.id:
						partners.append(receiver.partner_id)
			html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Баталгаат хугацаа дуусч байгаа:<br/>" + ','.join(msg)+'</span>'
			# self.env.user.send_chat(html, partners)
			self.env.user.send_emails(partners=partners, body=html, attachment_ids=False)

	@api.model
	def _check_technic_insurance(self):
		today = datetime.now()
		date_stop = today + timedelta(days=7)
		msg = []
		# Даатгалын огноо шалгах
		technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('insurance_date_end','=',date_stop.date()),
				('with_insurance','=',True)
				], order='report_order, program_code')
		for tt in technics:
			txt = "%s-ын даатгал(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
			msg.append(txt)
		# Татвар огноо шалгах
		technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('state_tax_date_end','=',date_stop.date()),
				('with_insurance','=',True)
				], order='report_order, program_code')
		for tt in technics:
			txt = "%s-ын татвар(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
			msg.append(txt)
		# Үзлэг огноо шалгах
		technics = self.env['technic.equipment'].search([
				('state','!=','draft'),
				('state_inspection_date_end','=',date_stop.date()),
				('with_insurance','=',True)
				], order='report_order, program_code')
		for tt in technics:
			txt = "%s-ын үзлэг(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
			msg.append(txt)

		# ===========================
		if msg:
			# Get group
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_equipment'),
				('name','in',['group_technic_insurance_user'])])
			group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
			partner_ids = group.mapped('users.partner_id')
			html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Хугацаа дуусч байгаа:<br/>" + ','.join(msg)+'</span>'
			# self.env.user.send_chat(html, partner_ids)
			self.env.user.send_emails(partners=partner_ids, body=html, attachment_ids=False)

	def see_workorders_fac(self):
		action = self.env.ref('mw_factory_equipment.action_maintenance_workorder_factory').read()[0]
		action['domain'] = [('equipment_id','=', self.id)]
		return action

class MaintenancePlanEquipmentLine(models.Model):
	_inherit = 'maintenance.plan.line'

	equipment_id = fields.Many2one('factory.equipment', string=u'Тоног төхөөрөмж', readonly=True, required=True,)

class TechinicSettingLine(models.Model):
	_inherit = 'technic.setting.line'

	equipment_id = fields.Many2one('factory.equipment', string=u'Тоног төхөөрөмж', required=True,)
	
class MaintenancePlanGenerator(models.Model):
	_inherit = 'maintenance.plan.generator'

	equipment_id = fields.Many2one('factory.equipment', string=u'Тоног төхөөрөмж',)
	# sector_id = fields.Many2one('hr.department', string=u'Хэсэг', required=True,)
	department_id = fields.Many2one('hr.department', string='Хэсэг' ,default=lambda self: self.env.user.department_id.id,)
	only_lv_technic = fields.Boolean(string='Зөвхөн LV эсэх', default=False,)
	clear_odometer_diff = fields.Selection([
			('half_day', u'Хагас өдрийн гүйлт'),
			('full_day', u'Бүтэн өдрийн гүйлт'),
			('three_day', u'3 өдрийн гүйлт'),
		], string=u'Зөрүү арилгаж нэмэх',
		states={'done': [('readonly', True)]},
		help="Гүйлтийн зөрүү арилгаж хагас, бүтэн өдрийн гүйлт нэмэх үед хэрэглэнэ", )
	is_round_interval = fields.Boolean(string=u'Мото цагийг бүхэлдэх эсэх', default=False,
		states={'done': [('readonly', True)]})
	generate_type = fields.Selection([
			('only_one', u'Зөвхөн нэг'),
			('all', u'Бүх техник'),
		], default='all', required=True, string=u'Төлөвлөлтийн төрөл')

class MaintenancePlanGeneratorLine(models.Model):
	_inherit = 'maintenance.plan.generator.line'

	equipment_id = fields.Many2one('factory.equipment', string=u'Тоног төхөөрөмж', required=True,)

	def create_plan_equipment(self):
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
			shift_hour = obj.equipment_id.equipment_setting_id.work_time_per_day / 2
			temp_work_time = obj.work_time
			temp_work_time_2 = 0
			if obj.work_time > shift_hour:
				temp_work_time = shift_hour
				temp_work_time_2 = obj.work_time - shift_hour

			# Өдрийн ПЛАН үүсгэх
			vals = {
				'branch_id': obj.equipment_id.branch_id.id,
				'origin': 'Generated: '+obj.parent_id.name,
				'maintenance_type_id': obj.maintenance_type_id.id,
				'pm_priority': obj.pm_priority,
				'maintenance_type': 'pm_service',
				'contractor_type': 'internal',
				'generator_line_id': obj.id,
				'date_required': obj.date_plan,
				'equipment_id': obj.equipment_id.id,
				'start_odometer': obj.pm_odometer,
				'work_time': temp_work_time,
				'man_hours': obj.man_hours,
				'description': obj.name,
				'required_material_line': material_datas,
				'shift': obj.shift,
			}
			plan = self.env['maintenance.plan.line'].create(vals)
			plan.action_to_confirm()
			obj.plan_id = plan.id
			obj.description = 'Plans: '+ str(plan.id)

			# Хэрэв зөрүү цаг байвал шөнийн план үүсгэх
			if temp_work_time_2 > 0:
				if obj.shift == 'day':
					# Шөнийн ПЛАН үүсгэх
					vals = {
						'branch_id': obj.equipment_id.branch_id.id,
						'origin': 'Generated: '+obj.parent_id.name + ', REF plan:'+str(obj.plan_id.name),
						'maintenance_type_id': obj.maintenance_type_id.id,
						'pm_priority': obj.pm_priority,
						'maintenance_type': 'pm_service',
						'contractor_type': 'internal',
						'generator_line_id': obj.id,
						'date_required': obj.date_plan,
						'equipment_id': obj.equipment_id.id,
						'start_odometer': obj.pm_odometer,
						'work_time': temp_work_time_2,
						'description': obj.name,
						'shift': 'night',
						'ref_plan_id': plan.id,
					}
					plan2 = self.env['maintenance.plan.line'].create(vals)
					plan2.action_to_confirm()
					obj.plan_id = plan2.id
					obj.description += ', '+str(plan2.id)
				else:
					# Маргааш өдрийн ПЛАН үүсгэх
					vals = {
						'branch_id': obj.equipment_id.branch_id.id,
						'origin': 'Generated: '+obj.parent_id.name + ', REF plan:'+str(obj.plan_id.name),
						'maintenance_type_id': obj.maintenance_type_id.id,
						'pm_priority': obj.pm_priority,
						'maintenance_type': 'pm_service',
						'contractor_type': 'internal',
						'generator_line_id': obj.id,
						'date_required': obj._date_increase(obj.date_plan,1),
						'equipment_id': obj.equipment_id.id,
						'start_odometer': obj.pm_odometer,
						'work_time': temp_work_time_2,
						'description': obj.name,
						'shift': 'day',
						'ref_plan_id': plan.id,
					}
					plan2 = self.env['maintenance.plan.line'].create(vals)
					plan2.action_to_confirm()
					obj.plan_id = plan2.id
					obj.description += ', '+str(plan2.id)