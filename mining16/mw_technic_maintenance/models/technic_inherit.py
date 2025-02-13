# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class TechnicEquipmentSettingInherit(models.Model):
	_inherit = 'technic.equipment.setting'

	pm_material_config = fields.One2many('maintenance.pm.material.config', 'technic_setting_id',
		string='PM тохиргоо')
	is_plan_by_time = fields.Boolean(string=u'Хугацаагаар төлөвлөх эсэх?', default=False)
	work_time_per_day = fields.Float(string=u'Өдөрт ажиллах цаг', required=True,
		help=u"Техникийн өдөрт бүтээлтэй ажиллах цаг")

class MaintenancePmMaterialConfig(models.Model):
	_name = 'maintenance.pm.material.config'
	_description = 'Maintenance PM material config'
	_order = 'priority, name'

	@api.depends('maintenance_type_id')
	def _set_name(self):
		for obj in self:
			obj.name = str(obj.maintenance_type_id.name)+' / Material config'
		return True

	@api.depends('pm_material_line')
	def _methods_compute(self):
		# Нийт тоог олгох
		for obj in self:
			obj.total_amount = sum(obj.mapped('pm_material_line.amount'))
	technic_setting_id = fields.Many2one('technic.equipment.setting', 'Technic setting', ondelete='cascade', readonly=True, )

	priority = fields.Integer(string='Зэрэглэл', required=True,)
	name = fields.Char(compute='_set_name',string='Нэр', readonly=True, store=True)
	maintenance_type_id = fields.Many2one('maintenance.type', string=u'Засварын төрөл', required=True,
		domain=[('is_pm','=',True)])
	interval = fields.Integer(string=u'Үйлчилгээний интервал', required=True,)
	interval_uom = fields.Char(string="Интервал нэгж", compute="_compute_interval_uom")
	work_time = fields.Float(string=u'Засварын цаг', required=True,)
	pm_material_line = fields.One2many('maintenance.pm.material.line', 'parent_id', string='Parent',
		required=True, copy=True)
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн', default=0)

	inspection_setting_id = fields.Many2one('technic.inspection.setting', string=u'Үзлэгийн тохиргоо', )

	# Хүн цагийн мэдээлэл бүртгэх
	employee_man_hour_line = fields.One2many('employee.man.hour.line', 'parent_id', string='Parent',
		required=True, copy=True)
	total_man_hours = fields.Float(compute='_compute_total_man_hours',
		string=u'Нийт хүн цаг', copy=False, store=True)
	
	@api.depends('employee_man_hour_line','work_time','employee_man_hour_line.qty')
	def _compute_total_man_hours(self):
		for obj in self:
			obj.total_man_hours = sum(obj.employee_man_hour_line.mapped('qty')) * obj.work_time

	@api.depends('technic_setting_id','technic_setting_id.odometer_unit')
	def _compute_interval_uom(self):
		for item in self:
			if item.technic_setting_id:
				item.interval_uom = item.technic_setting_id.odometer_unit
			else:
				item.interval_uom = False

	# PM материал copy paste хийх
	def copy_pm_lines(self):
		if self.pm_material_line:
			line = self.copy()
			self.technic_setting_id.pm_material_config = [(4,line.id)]
			return {
				'type': 'ir.actions.client',
				'tag': 'reload',
			}

	# PM материал copy paste хийх
	def compute_man_hours(self):
		confs = self.env['maintenance.pm.material.config'].search([('employee_man_hour_line','!=',False)])
		for line in confs:
			line._compute_total_man_hours()

class MaintenancePmMaterialLine(models.Model):
	_name = 'maintenance.pm.material.line'
	_description = 'Maintenance PM material line'
	_order = 'material_id'

	@api.depends('price_unit','qty')
	def _get_amount(self):
		for obj in self:
			obj.amount = obj.qty * obj.price_unit

	parent_id = fields.Many2one('maintenance.pm.material.config', string=u'PM тохиргоо', ondelete='cascade')
	generator_id = fields.Many2one('maintenance.plan.generator.line', string=u'Forecast', ondelete='cascade')

	maintenance_type_id = fields.Many2one(related='parent_id.maintenance_type_id', string=u'Засварын төрөл', readonly=True,)
	technic_setting_id = fields.Many2one(related='parent_id.technic_setting_id', string='Техникийн тохиргоо', ondelete='cascade', readonly=True, )

	template_id = fields.Many2one('product.template', string=u'Барааны Темплате', required=True)
	material_id = fields.Many2one('product.product',string='Бараа', compute="compute_pm_product", store=True)
	categ_id = fields.Many2one(related='material_id.categ_id', string=u'Ангилал', readonly=True, store=True )
	price_unit = fields.Float(string='Нэгж үнэ', required=True,)
	qty = fields.Float('Тоо хэмжээ', digits = (16,1), required=True, default=1)
	amount = fields.Float(compute='_get_amount',
		store=True, string=u'Дүн', copy=False)
	description = fields.Char('Тайлбар', )
	is_depend_season = fields.Boolean(string='Улирлаас хамааралтай эсэх', default=False,
		help="Тухайн материал нь улиралаас хамаарч өөрчлөгддөг эсэх")

	warehouse_id = fields.Many2one('stock.warehouse',string=u'Агуулах', required=False)

	# @api.onchange('material_id')
	# def onchange_qty(self):
	# 	if self.material_id:
	# 		price_unit = self.material_id.standard_price
	# 		self.price_unit = price_unit

	@api.depends('template_id','template_id.product_variant_ids')
	def compute_pm_product(self):
		for item in self:
			if item.template_id:
				variants = item.template_id.product_variant_ids
				last_baraa = False
				if variants:
					print('variats',variants)
					last_baraa = self.env['product.product'].search([('id','in',variants.ids)], order='create_date desc', limit=1)
				if last_baraa:
					print(last_baraa)
					item.material_id = last_baraa.id
					price_unit = last_baraa.standard_price
					item.price_unit = price_unit
				if not item.material_id:
					item.material_id = False
			else:
				item.material_id = False

class TechnicEquipmentInherit(models.Model):
	_inherit = 'technic.equipment'

	last_pm_id = fields.Many2one('maintenance.type', string=u'Сүүлд хийгдсэн PM',
		# readonly=True,
		)
	last_pm_odometer = fields.Float(string=u'Сүүлд хийгдсэн PM гүйлт', digits = (16,1),
		# readonly=True,
		)
	last_pm_priority = fields.Integer(string=u'PM дугаар', default=0,
		# readonly=True,
		)
	last_pm_date = fields.Date(string=u'Сүүлд хийгдсэн PM огноо', default=0,
		# readonly=True,
		)

	oil_sample_line = fields.One2many('maintenance.oil.sample', 'technic_id',
		string='Тосны дээж', readonly=True,
		domain=[('state','!=','draft')])

	# ТББК ыг авах
	def get_technic_planned_tbbk(self, date_from, date_to):
		plan_ids = self.env['maintenance.plan.line'].sudo().search(
						[('date_required','>=',date_from),
						 ('date_required','<=',date_to),
						 ('state','not in',['draft','cancelled']),
						 ('technic_id','=',self.id)])
		# Нийт засварын цаг
		repair_time = sum(plan_ids.mapped('work_time'))
		# ТББК бодох
		start_date = datetime.strptime(date_from, "%Y-%m-%d")
		end_date = datetime.strptime(date_to, "%Y-%m-%d")
		days = (end_date-start_date).days + 1
		norm = self.technic_setting_id.work_time_per_day or 1

		tbbk = 100 - (repair_time*100)/(norm*days)
		res = { 'tbbk': tbbk, 'repair_time': repair_time }
		return res

	# Холбоотой засварууд харах
	def see_workorders(self):
		action = self.env.ref('mw_technic_maintenance.action_maintenance_workorder').read()[0]
		action['domain'] = [('technic_id','=', self.id)]
		return action

class TechnicComponentPart(models.Model):
	_inherit = 'technic.component.part'
	# Чат илгээх груп авах
	def _get_send_group(self):
		return self.env.ref('mw_technic_maintenance.group_maintenance_planner')

class EmployeeManHourLine(models.Model):
	_name = 'employee.man.hour.line'
	_description = 'Employe Man Hour Line'
	_order = 'job_id'

	parent_id = fields.Many2one('maintenance.pm.material.config', string=u'PM config', ondelete='cascade')
	job_id = fields.Many2one('hr.job',string='Албан тушаал', required=True,)
	qty = fields.Integer(string='Тоо', required=True, default=1)

class TechnicInspection(models.Model):
	_inherit = 'technic.inspection'

	workorder_id = fields.Many2one('maintenance.workorder', string='Workorder', readonly=True, )

	def create_workorder(self):
		if self.workorder_id:
			raise UserError(_(u'WO аль хэдийн үүссэн байна!'))
		# WO үүсгэх
		if self.inspection_type == 'daily':
			desc = ''
			for ll in self.inspection_line:
				if not ll.is_check:
					desc += ll.check_name
					if ll.description:
						desc += ': '+ll.description+', '
					else:
						desc += ', '
			vals = {
				'date_required': self.date_inspection,
				'maintenance_type': 'not_planned',
				'origin': self.name,
				'branch_id': self.branch_id.id,
				'technic_id': self.technic_id.id,
				'description': u'Техникийн үзлэг - '+desc,
				'start_odometer': 0,
				'shift': self.shift,
				'contractor_type': 'internal',
				'inspection_id': self.id,
			}
			wo_id = self.env['maintenance.workorder'].create(vals)
			self.workorder_id = wo_id.id

			# Planner луу MSG илгээх
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_maintenance'),
				('name','=','group_maintenance_planner')])
			group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
			partners = []
			for receiver in group.users:
				if receiver.partner_id:
					if self.env.user.partner_id.id != receiver.partner_id.id:
						partners.append(receiver.partner_id)
			html = u"<span style='font-size:10pt; font-weight:bold; color:red;'>%s үзлэгээс %s техник дээр WO үүсгэлээ!</span>" % (self.name, self.technic_id.name)
			# self.env.user.send_chat(html, partners)
			self.env.user.send_emails(partners=partners, body=html, attachment_ids=False)

	# Асуудалтай үзлэг байвал
	# Үзлэгийн ажил үүсгэнэ
	def action_to_done(self):
		res = super(TechnicInspection, self).action_to_done()
		if self.inspection_type == 'daily':
			for line in self.inspection_line:
				if not line.is_check and line.item_id.is_important:
					vals = {
						'origin': self.name,
						'branch_id': self.branch_id.id,
						'name': line.description,
						'technic_id': self.technic_id.id,
						'technic_odometer': self.odometer_value,
						'inspection_item_id': line.item_id.id,
					}
					self.env['technic.inspection.work'].create(vals)
		return res

class TechnicInspectionWork(models.Model):
	_name = 'technic.inspection.work'
	_description = 'Technic Inspection Work'
	_order = 'date_required desc'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True)

	origin = fields.Char(string=u'Эх баримт', copy=False, readonly=True, )
	date = fields.Datetime(string=u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_required = fields.Date(string=u'Хийгдэх огноо',
		states={'wo_created':[('readonly', True)],'closed':[('readonly', True)]})
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', copy=True, readonly=True, )
	technic_odometer = fields.Float('Техник гүйлт', readonly=True, )

	inspection_item_id = fields.Many2one('technic.inspection.item', string=u'Үзлэгийн нэр', copy=False,
		required=True, readonly=True, )
	name = fields.Char(u'Тайлбар', copy=False, readonly=True, )

	user_id = fields.Many2one('res.users', string=u'Клерк', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string=u'Төлөвлөгч', readonly=True, copy=False,)

	description = fields.Text(u'Авсан арга хэмжээ',
		states={'closed':[('readonly', True)]})
	workorder_id = fields.Many2one('maintenance.workorder', string=u'Холбоотой WO', readonly=True, )
	date_close = fields.Datetime(u'Хаасан огноо', readonly=True, copy=False,)

	state = fields.Selection([
		('draft', u'Ноорог'),
		('wo_created', u'WO үүсгэсэн'),
		('closed', u'Хаагдсан'),],
		default='draft', string=u'Төлөв', tracking=True)

	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(TechnicInspectionWork, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_close(self):
		if not self.description and not self.workorder_id:
			raise UserError(_(u'Авсан арга хэмжээг оруулна уу!'))
		self.state = 'closed'
		self.date_close = datetime.now()

	def action_create_workorder(self):
		if not self.date_required:
			raise UserError(_(u'Хийгдэх огноог оруулна уу!'))
		if self.workorder_id:
			raise UserError(_(u'WO үүссэн байна!'))
		# WO үүсгэх
		vals = {
			'date_required': self.date_required,
			'maintenance_type': 'not_planned',
			'origin': self.origin,
			'branch_id': self.branch_id.id,
			'technic_id': self.technic_id.id,
			'description': self.name,
			'start_odometer': self.technic_id.total_odometer,
			'contractor_type': 'internal',
		}
		wo_id = self.env['maintenance.workorder'].create(vals)
		self.workorder_id = wo_id.id
		self.validator_id = self.env.user.id
		self.state = 'wo_created'

class technicEquipmentLogStatus(models.Model):
	_inherit = 'technic.equipment.log.status'