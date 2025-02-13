# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo import tools


class mw_environment_training(models.Model):
	_name = 'env.training'
	_description = "Environmental Training"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'training_date DESC'

	def find_department(self):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		if employee:
			return employee.department_id.id
		else:
			return False

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	training_date = fields.Date('Сургалтын огноо', required=True,  default=fields.Datetime.now, readonly=True, states={'draft':[('readonly',False)]})
	# topic_id = fields.Many2one('env.parameter', string='Сургалтын сэдэв', domain="[('type','=','training'),('is_active','=', 'active')]", required=True, readonly=True, states={'draft':[('readonly',False)]})
	topic_id = fields.Many2many('env.parameter','type_id', 'topic_id', string='Сургалтын сэдэв', domain="[('type','=','training'),('is_active','=', 'active')]", required=True, readonly=True, states={'draft':[('readonly',False)]})
	trainee_type = fields.Selection([
		('employees', 'Компанийн ажилтнууд'),
		('contracts', 'Гэрээт ажилтнууд'),
		('visitors', 'Зочид')], string='Суралцагчид', default='employees', required=True, readonly=True, states={'draft':[('readonly',False)]})
	number_of_trainees = fields.Integer(string='Суралцагчдын тоо', default=0, required=True, readonly=True, states={'draft':[('readonly',False)]})
	employee_id = fields.Many2one('hr.employee', string='Сургалт явуулсан', readonly=True, states={'draft':[('readonly',False)]})
	# department_id = fields.Many2one('hr.department', string='Хэлтэс', default=find_department, readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, default=default_location, domain="[('is_active','=', 'active')]", readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)
	
	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Сургалт).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})	

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, ' (' + obj.mining_location.name + ' : ' + obj.training_date.strftime("%Y-%m-%d") + ')'))
		return result 

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_training, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res


class mw_environment_violation_subtype(models.Model):
	_name = 'env.violation.subtype'
	_description = "Environmental Violation Sub Type"

	violation_subtype = fields.Text(u'Зөрчил дутагдал')
	violation_id = fields.Many2one('env.parameter', string=u'Зөрчил дутагдлын төрөл',
								   domain="[('type','=','violation'),('is_active', '=', 'active')]", required=True)

	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.violation_subtype))
		return result

class mw_environment_violation_reason(models.Model):
	_name = 'env.violation.reason'
	_description = "Environmental Violation Reason"

	reason = fields.Char(u'Шалтгаан')
	violation_id = fields.Many2one('env.parameter', string=u'Зөрчил дутагдлын төрөл',
								   domain="[('type','=','violation'),('is_active', '=', 'active')]", required=True)

	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.reason))
		return result

class mw_environment_violation_response(models.Model):
	_name = 'env.violation.response'
	_description = "Environmental Violation Response"

	response = fields.Char(u'Хариу арга хэмжээ')
	violation_id = fields.Many2one('env.parameter', string=u'Зөрчил дутагдлын төрөл',
								   domain="[('type','=','violation'),('is_active', '=', 'active')]", required=True)

	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.response))
		return result


class mw_environment_inspection_line(models.Model):
	_name = 'env.inspection.line'
	_description = "Environmental Inspection Line"

	inspection_id = fields.Many2one('env.inspection', string='Үл тохирол', ondelete='cascade', store=True)
	violation = fields.Many2one('env.parameter', string='Зөрчил дутагдал', domain="[('type','=','violation'),('is_active', '=', 'active')]", required=True)
	violation_subtype = fields.Many2one('env.violation.subtype', string='Зөрчлийн дэд төрөл', domain="[('violation_id','=',violation)]")
	violation_reason = fields.Many2one('env.violation.reason', string='Яагаад', domain="[('violation_id','=',violation)]")
	location = fields.Many2one('env.parameter', string='Байршил', domain="[('type','=','location'),('is_active', '=', 'active')]", required=True)
	inspected_by = fields.Selection([
		('env_employee', 'Байгаль орчны мэргэжилтэн'),
		('internal_audit', 'Дотоод хяналт шалгалт'),
		('external_audit', 'Хөндлөнгийн хяналт шалгалт'),
		('by_employees', 'Ажилчдын мэдээлснээр'),
		('by_request', 'Санал гомдлын дагуу'),
		('by_citizen', 'Нөлөөллийн бүсийн иргэн'),
		('by_herder', 'Малчин иргэн'),
		('by_local_gov', 'Орон нутгийн засаг захиргаа'),
		('by_other', 'Бусад (тайлбар)'),
	], string='Хэн илрүүлсэн', required=True)
	inspected_by_comment = fields.Text('Хэн илрүүлсэн /тайлбар/')
	location = fields.Many2one('env.parameter', string='Байршил', domain="[('type','=','location'),('is_active', '=', 'active')]", required=True)
	violation_response = fields.Many2many('env.violation.response', string = 'Хэрхэн арга хэмжээ авсан?', domain="[('violation_id','=',violation)]")
	violation_response_comment = fields.Text('Авсан арга хэмжээ /тайлбар/')
	required_time = fields.Char('Шаардлагатай хугацаа')
	is_fixed = fields.Boolean('Арилгасан эсэх', default=False)


class mw_environment_violation_response_line(models.Model):
	_name = 'env.violation.response.line'
	_description = "Environmental Inspected Violation Response Line"

	inspection_id = fields.Many2one('env.inspection', string='Үл тохирол', ondelete='cascade')
	response_action = fields.Text('Авсан хариу арга хэмжээ')
	response_by = fields.Many2one('res.users', 'Ажилтан')
	response_date = fields.Date('Огноо')
	response_action_rate = fields.Integer('Биелэлтийн %')


class mw_environment_inspection(models.Model):
	_name = 'env.inspection'
	_description = "Environmental Inspection"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'inspection_date DESC'

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	inspection_date = fields.Date('Шалгалтын огноо', required=True,  default=fields.Datetime.now, readonly=True, states={'draft':[('readonly',False)]})
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', tracking=True, default='draft', readonly=True, states={'draft':[('readonly',False)]})
	inspection_type = fields.Selection([
		('planned', 'Төлөвлөгөөт'),
		('unplanned', 'Төлөвлөгөөт бус')], string='Хяналт шалгалтын төрөл', default='planned', required=True, readonly=True, states={'draft':[('readonly',False)]})
	inspector = fields.Selection([
		('department', 'Үйлдвэр, уурхай, нэгж хэсэг'),
		('company', 'Компанийн төв оффисоос'),
		('country', 'Улсаас'),
		('state', 'Аймгаас'),
		('city', 'Сумаас')], string='Хяналт шалгалт явуулсан', required=True, readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('env.inspection.line', 'inspection_id', string='Violations', store=True, readonly=True, states={'draft':[('readonly',False)]})
	response_line_ids = fields.One2many('env.violation.response.line', 'inspection_id', string='Violation Response', readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', default=default_location, required=True, domain="[('is_active','=', 'active')]", tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	is_fixed = fields.Boolean('Арилгасан эсэх', default=False, readonly=True, states={'draft':[('readonly',False)]})
	manager_comment = fields.Text('Удирдлагын зааварчилгаа', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	progress_rate = fields.Integer('Хариу арга хэмжээний биелэлт %', compute="_compute_progress_rate", readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Үл тохирол).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})	

	def _compute_progress_rate(self):
		for record in self:
			total_response=0
			total_response = len(record.response_line_ids)
			total_response_rate = 0
			response_items_lines = self.env['env.violation.response.line'].search([('inspection_id', '=', record.id)])
			if response_items_lines:
				for response_items_line in response_items_lines:
					total_response_rate += response_items_line.response_action_rate
			mean_response_rate = 0
			record.progress_rate = mean_response_rate
			if total_response>0:
			   mean_response_rate = total_response_rate/total_response
			


	@api.depends('inspector')
	def _get_category(self):
		selection = False
		if self.inspector:
			if self.inspector == "department" or self.inspector == "company":
				selection = 'internal'
			else:
				selection = 'external'
		self.inspector_category = selection
		# return {'value': {'inspector_category': selection}}


	inspector_category = fields.Selection([
		('internal', 'Дотоод хяналт шалгалт'),
		('external', 'Хөндлөнгийн байгууллагын шалгалт')
	], string='Хяналт шалгалтын ангилал', compute=_get_category, store=True, readonly=True)

	def name_get(self):
		result = []
		for obj in self:
			inspector_name = dict(self._fields['inspector'].selection).get(self.inspector)
			result.append(
				(obj.id, inspector_name + ' (' + obj.mining_location.name + ' : ' + obj.inspection_date.strftime("%Y-%m-%d") + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_inspection, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res

class mw_environment_inspection_violation_report(models.Model):
	_name = 'env.inspection.violation'
	_description = "Environment Inspection Violation View"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_auto = False

	id = fields.Integer('ID', readonly=True)
	inspection_id = fields.Integer('Үл тохирол', readonly=True)
	#violation_id = fields.Integer(string=u'Зөрчил дутагдлын төрөл ID', readonly=True)
	violation_id = fields.Many2one('env.parameter', string=u'Зөрчил дутагдал', domain="[('type','=','violation'),('is_active', '=', 'active')]", required=True)
	violation_subtype_id = fields.Many2one('env.violation.subtype', string='Зөрчил дутагдлын төрөл')
	violation_reason_id = fields.Many2one('env.violation.reason', string='Шалтгаан')
	inspection_date = fields.Date('Үл тохирол огноо')
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', tracking=True)

	def init(self):
		# tools.drop_view_if_exists(cr, self._table)
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE or REPLACE VIEW env_inspection_violation as
			SELECT ins.id,
				line.inspection_id,  line.violation as violation_id, line.violation_subtype as violation_subtype_id, 
				line.violation_reason as violation_reason_id, ins.inspection_date, ins.mining_location 
			FROM env_inspection ins
			INNER JOIN env_inspection_line line on ins.id = line.inspection_id
		""")
#

class mw_environment_accident(models.Model):
	_name = 'env.accident'
	_description = "Environmental Accident"
	_order = 'accident_date DESC'

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, obj.violation.name + ' (' + obj.mining_location.name + ' : ' + obj.accident_date.strftime('%Y-%m-%d') + ')'))
		return result

	accident_date = fields.Date('Accident Date', required=True,  default=fields.Datetime.now)
	note = fields.Text('Note')
	violation = fields.Many2one('env.parameter', string='Violation', domain="[('type','=','violation'),('is_active', '=', 'active')]", required=True)
	location = fields.Many2one('env.parameter', string='Location', domain="[('type','=','location'),('is_active', '=', 'active')]", required=True)
	is_fixed = fields.Boolean('Fixed', default=False)
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', default=default_location, required=True, domain="[('is_active','=', 'active')]")

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_accident, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res

class MwEnvironmentWaterLine(models.Model):
	_name = 'env.water.line'
	_description = "Environmental Water Line"
	_order = 'month ASC'

	month = fields.Selection([
		('01', '1-р сар'), ('02', '2-р сар'), ('03', '3-р сар'),
		('04', '4-р сар'), ('05', '5-р сар'), ('06', '6-р сар'),
		('07', '7-р сар'), ('08', '8-р сар'), ('09', '9-р сар'),
		('10', '10-р сар'), ('11', '11-р сар'), ('12', '12-р сар'), ], string='Month')

	water_source = fields.Many2one('env.parameter', string='Усны эх сурвалж', domain="[('type','=','source'),('is_active','=', 'active')]")
	start_amount = fields.Float("Тоолуурын эхний заалт")
	end_amount = fields.Float("Тоолуурын эцсийн заалт")
	amount = fields.Float("Зөрүү хэмжээ /м3/", compute='_compute_amount', readonly=True, store=True)
	water_id = fields.Many2one('env.water', string='Water', ondelete='cascade')
	dedication = fields.Selection([
		('process', 'Процесс'),
		('garden', 'Ногоон байгууламж'),
		('road', 'Замын арчилгаа'),
	], string='Зориулалт')
	dedication_id = fields.Many2one('env.parameter', string='Зориулалт', domain="[('type','=','dedication'),('is_active','=', 'active')]")
	# price = fields.Integer(related='dedication_id.price', string='Нэгж үнэ', readonly=True, store=True)
	# price = fields.Integer(string='Нэгж үнэ')
	price = fields.Float(string='Нэгж үнэ')
	total_amount = fields.Float(string='Нийт үнэ', compute='_compute_total_amount', store=True)

	@api.depends('price','amount')
	def _compute_total_amount(self):
		for line in self:
			if line.price and line.amount:
				line.total_amount = line.price * line.amount
			else:
				 line.total_amount = 0

	@api.depends('start_amount','end_amount')
	def _compute_amount(self):
		for line in self:
			if line.start_amount and line.end_amount:
				line.amount = line.end_amount - line.start_amount
			else:
				 line.amount = 0


class MwEnvironmentWaterPayment(models.Model):
	_name = 'env.water.payment'
	_description = "Environmental Water Payment"
	_order = 'pay_date ASC'

	pay_date = fields.Date('Төлсөн огноо', required=True,  default=fields.Datetime.now) 
	amount = fields.Float("Төлсөн дүн", required=True)
	note = fields.Text("Тайлбар")
	water_id = fields.Many2one('env.water', string='Water ID', ondelete='cascade')

class MwEnvironmentWaterResLine(models.Model):
	_name = 'env.water.res.line'
	_description = "Environmental Water Res Line"

	water_m = fields.Selection([
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('15', '15'),
		('20', '20'),
		('25', '25'),
		('30', '30'),
		('32', '32'),
		('35', '35'),
		('40', '40'),
		('45', '45'),
		('50', '50'),
		('55', '55'),
		('60', '60'),
		('65', '65'),
		('70', '70'),
		('75', '75'),
		('80', '80'),
		('85', '85'),
		('90', '90'),
		('95', '95'),
		('100', '100')
	], default=False, string="Нэг рейсийн усны хэмжээ/M3/")
	water_source = fields.Many2one('env.parameter', string='Усны эх сурвалж', domain="[('type','=','source'),('is_active','=', 'active')]")
	dedication_id = fields.Many2one('env.parameter', string='Зориулалт', domain="[('type','=','dedication'),('is_active','=', 'active')]")
	res_number = fields.Float(string='Рейсийн тоо')
	res_amount = fields.Float(string='Нэгж үнэ')
	total_amount = fields.Float(compute='_compute_total_amount', string='Нийт үнэ')
	total_acc = fields.Float(compute='_compute_acc', string='Нийт хэмээ')

	res_id = fields.Many2one('env.water', string='Рейс', ondelete='cascade')

	@api.depends('res_number','water_m')
	def _compute_acc(self):
		for acc in self:
			if acc.res_number and acc.water_m:
				acc.total_acc = float(acc.water_m ) * acc.res_number
			else:
				acc.total_acc = 0

	@api.depends('res_amount','total_acc')
	def _compute_total_amount(self):
		for line in self:
			if line.res_amount and line.total_acc :
				line.total_amount =line.res_amount * line.total_acc
			else:
				 line.total_amount = 0

class MwEnvironmenWaterDirtyLine(models.Model):
	_name = 'env.water.dirty.line'
	_description = "Environmental Water dirty Line"
	
	water_dirty = fields.Many2one('env.parameter', string='Бохир ус сурвалж', domain="[('type','=','source'),('is_active','=', 'active')]")
	dirty_amount = fields.Float(string='Нэгж үнэ/m3/')
	dirty_acc = fields.Float(string='Усны хэмжээ/m3/')
	total_amount = fields.Float(compute='_compute_total_amount',string='Нийт төлөх дүн')

	dirty_id = fields.Many2one('env.water', string='Бохир ус', ondelete='cascade')
	
	@api.depends('dirty_amount','dirty_acc')
	def _compute_total_amount(self):
		for line in self:
			if line.dirty_amount and line.dirty_acc :
				line.total_amount =line.dirty_amount * line.dirty_acc
			else:
				 line.total_amount = 0
class MakEnvironmentWater(models.Model):
	_name = 'env.water'
	_description = "Environmental Water"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'year DESC'

	def _get_year(self):
		year_list = []
		current_year = datetime.now().year
		for j in range(current_year + 1, current_year - 25, -1):
			year_list.append((str(j), str(j)))
		return year_list
	
	@api.depends('payment_ids', 'payment_ids.amount','pay_amount', 'line_res_ids', 'line_res_ids.total_amount')
	def _payment_amount(self):
		total = 0
		if self.water_type == 'usage':
			for payment in self.payment_ids:
				total = payment.amount
			self.total_payment = sum([line.amount for line in self.payment_ids])
			self.balance = self.pay_amount - total
		elif self.water_type == 'usage_res':
			self.pay_amount = sum([line.total_amount for line in self.line_res_ids])
			self.balance = self.pay_amount - self.total_payment
			self.accumulated_amount = sum([line.total_acc for line in self.line_res_ids])
			for payment in self.payment_ids:
				total = payment.amount
			self.total_payment = sum([line.amount for line in self.payment_ids])
			self.balance = self.pay_amount - total
		elif self.water_type == 'dirty':
			self.pay_amount = sum([line.total_amount for line in self.dirty_ids])
			self.balance = self.pay_amount - self.total_payment
			self.accumulated_amount = sum([line.dirty_acc for line in self.dirty_ids])
			for payment in self.payment_ids:
				total = payment.amount
			self.total_payment = sum([line.amount for line in self.payment_ids])
			self.balance = self.pay_amount - total
		else:
			self.total_payment = 0
			self.balance = 0

	@api.depends('line_ids.amount', 'amount')
	def _accumulated_amount(self):
		total = 0
		for line in self.line_ids:
			total = total + line.amount
		self.accumulated_amount = total
		self.pay_amount = sum(self.line_ids.mapped('total_amount'))
	
	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False
	

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	water_type = fields.Selection([
		('usage', 'Ус ашиглалт'),
		('usage_res', 'Ус ашиглалт /рейс/'),
		('dirty', 'Ахуйн бохир ус')
	], string='Төрөл', required=True, default='usage', readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	amount = fields.Float("Зөвшөөрөгдсөн хэмжээ/м3/", required=True, readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	year = fields.Selection(string='Он', selection=_get_year, readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('env.water.line', 'water_id', string='Усны бүртгэл/сараар/', readonly=True, states={'draft':[('readonly',False)]})
	date = fields.Date(string='Огноо', default=fields.Date.context_today, required=True,  readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	line_res_ids = fields.One2many('env.water.res.line', 'res_id', string='Усны бүртгэл/рейс/', readonly=True, states={'draft':[('readonly',False)]})
	payment_ids = fields.One2many('env.water.payment', 'water_id', string='Төлбөрүүд', readonly=True, states={'draft':[('readonly',False)]})
	dirty_ids = fields.One2many('env.water.dirty.line', 'dirty_id', string='бохир ус', readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', default=default_location, required=True, domain="[('is_active','=', 'active')]", readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	accumulated_amount = fields.Float(compute=_accumulated_amount, string='Нийт хэмжээ /м3/', store=True, readonly=True)
	pay_amount = fields.Float(compute=_accumulated_amount, string='Нийт төлөх дүн', store=True, readonly=True)
	allowed_payment = fields.Float(string='Төлбөр-дүгнэлтээр', readonly=True, states={'draft':[('readonly',False)]})
	total_payment = fields.Float(compute=_payment_amount, string='Нийт төлсөн дүн', store=True, readonly=True, compute_sudo=True)
	balance = fields.Float(compute=_payment_amount,  string='Төлбөрийн үлдэгдэл', store=False, readonly=True, compute_sudo=True)
	residual_amount = fields.Float(compute='_residual_amount', string='Үлдсэн хэмжээ /м3/', store=True, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Ус ашиглалт).')
		else: 
			self.write({'state': 'done'})

	@api.depends('amount', 'accumulated_amount')
	def _residual_amount(self):
		for item in self:
			item.residual_amount = item.amount - item.accumulated_amount

	def action_to_draft(self):
		self.write({'state': 'draft'})

	@api.model
	def create(self, vals):
		value = self.search([
			('mining_location', '=', vals['mining_location']), 
			('date', '=', vals['date']),
			'|','|',
			('water_type','=','usage'),
			('water_type','=','usage_res'),
			('water_type','=','dirty')
		])
		if value:
			raise UserError('Анхааруулга!!!, Сонгосон уурхайд, сонгосон онд, сонгосон усны зориулалтаар бүртгэл байгаа тул дахин үүсгэх боломжгүй.')
		res = super(MakEnvironmentWater, self).create(vals)
		return res

	def name_get(self):
		result = []
		for obj in self:
			if self.water_type == 'usage':
				result.append(
					(obj.id, '(' + obj.mining_location.name + ' : ' + obj.date.strftime('%Y-%m-%d') + ')'))
			elif self.water_type == 'usage_res':
				result.append(
					(obj.id, 'Ус ашиглалт /рейс/ (' + obj.mining_location.name + ' : ' + obj.date.strftime('%Y-%m-%d') + ')'))
			else:
				result.append(
					(obj.id, 'Ахуйн бохир ус (' + obj.mining_location.name + ' : ' + obj.date.strftime('%Y-%m-%d') + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(MakEnvironmentWater, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date', 'balance', 'price', 'pay_amount'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res


class MwEnvironmentWaste(models.Model):
	_name = 'env.waste'
	_description = "Environmental Waste"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'year_month DESC'

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	waste_type = fields.Many2one('env.parameter', string='Хог хаягдлын төрөл', required=True, domain="[('type','=','waste_type'),('is_active','=', 'active')]",  readonly=True, states={'draft':[('readonly',False)]})
	waste_category = fields.Selection(related='waste_type.category', string='Хог хаягдлын ангилал', store=True, readonly=True, states={'draft':[('readonly',False)]})
	amount = fields.Float("Хог хаягдлын хэмжээ /т/", digits=(16, 4), required=True,  readonly=True, states={'draft':[('readonly',False)]})
	reused_amount = fields.Float("Дахин ашигласан /т/", digits=(16, 4),  readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	department_id = fields.Many2one('hr.department', default=lambda self: self.env.user.department_id, string='Хэлтэс', store=True)
	department_ids = fields.Many2many('hr.department', default=lambda self: self.env.user.department_ids, string='Хэлтэсүүд', store=True)
	source = fields.Selection([
		('hospital', 'Эмнэлэг'),
		('mine', 'Уурхай'),
		('factory', 'Үйлдвэр'),
		('lab', 'Лаборатори'),
		('office', 'Оффис'),
	], string='Эх үүсвэр', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	contract_id = fields.Many2one('contract.document.real', string='Холбоотой гэрээ', tracking=True, domain="[('state_type','in',['done','ended']),'|',('department_id','=',department_id),('department_id','in',department_ids)]", readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Хог хаягдал).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def _get_year_month(self):
		year_list = []
		current_year = datetime.now().year
		current_month = datetime.now().month
		for j in range(current_month, 0, -1):
			year_month = str(current_year) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(12, 0, -1):
			year_month = str(current_year - 1) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(2, 25, 1):
			year_month = str(current_year - j) + "/12"
			year_list.append((year_month, year_month))
		return year_list

	@api.depends('reused_amount')
	def _reused_percent(self):
		if self.reused_amount and self.amount:
			reused_percent = int(self.reused_amount * 100 / self.amount)
		else:
			reused_percent = 0
		self.reused_percent = str(reused_percent) + " %"
	
	@api.onchange('year_month')
	def _get_year(self):
		if self.year_month:
			self.year = self.year_month[0:4]
		else:
			self.year = str(datetime.now().year)

	reused_percent = fields.Char("Дахин ашиглалтын хувь", compute=_reused_percent, readonly=True, states={'draft':[('readonly',False)]})
	note = fields.Text("Тайлбар", readonly=True, states={'draft':[('readonly',False)]})
	year_month = fields.Selection(string='Он/Сар', selection=_get_year_month, readonly=True, states={'draft':[('readonly',False)]})
	year = fields.Char('Он', readonly=True, states={'draft':[('readonly',False)]})
	uom = fields.Selection([
		('tonne', 'Тонн'),
		('kilo', 'Колограм'),
		('piece', 'Ширхэг')], string="Uom", default='tonne', readonly=True)
	waste_date = fields.Date('Огноо', required=True,  default=fields.Datetime.now, readonly=True, states={'draft':[('readonly',False)]})

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	_defaults = {
		'year_month': str(datetime.now().year) + ("/" if datetime.now().month > 9 else "/0") + str(
		datetime.now().month),
	}

	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, default=default_location, domain="[('is_active','=', 'active')]",  readonly=True, states={'draft':[('readonly',False)]}, tracking=True)


	@api.model
	def create(self, vals):
		value = self.search([('mining_location', '=', vals['mining_location']), ('waste_date', '=', vals['waste_date']),
							 ('waste_type', '=', vals['waste_type'])])
		if value:
			raise UserError('Анхааруулга!!!, Сонгосон уурхайд, сонгосон сард, сонгосон хог хаягдлын төрлөөр бүртгэл байгаа тул дахин үүсгэх боломжгүй.')
		res = super(MwEnvironmentWaste, self).create(vals)
		return res

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, obj.waste_type.name + ' (' + obj.mining_location.name + ' : ' + obj.waste_date.strftime('%Y-%m-%d') + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(MwEnvironmentWaste, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res


class mw_environment_rehab_line(models.Model):
	_name = 'env.rehab.line'
	_description = "Environmental Rehabilitation Line"


	rehab_location_id = fields.Many2one('env.parameter', string='Байршил', required=True, domain="[('type','=','rehab_location'),('is_active','=', 'active')]")
	rehab_type = fields.Many2one('env.parameter', string='Нөхөн сэргээлтийн төрөл', required=True, domain="[('type','=','rehab_type'),('is_active','=', 'active')]")
	rehab_category = fields.Selection('Нөхөн сэргээлтийн ангилал', related='rehab_type.category', store=True, readonly=True)
	amount = fields.Float("Нөхөн сэргээсэн талбай /га/", required=True)
	note = fields.Text("Тайлбар")
	rehab_id = fields.Many2one('env.rehab', string='Rehabilitation ID', ondelete='cascade')
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт')
	date = fields.Date(string='Огноо', required=True, default=fields.Date.context_today)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	mining_location = fields.Many2one(related='rehab_id.mining_location', string='Үйлдвэр уурхай', readonly=True, store=True)


	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Нөхөн сэргээлт).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


class mw_environment_rehab_land(models.Model):
	_name = 'env.rehab.land'
	_description = "Environmental Affected Land"


	approved_date = fields.Date(string='Зөвшөөрөл авсан огноо', required=True, default=fields.Date.context_today)
	used_date = fields.Date(string='Хийгдсэн огноо', required=True, default=fields.Date.context_today)
	rehab_location_id = fields.Many2one('env.parameter', string='Байршил', required=True, domain="[('type','=','rehab_location'),('is_active','=', 'active')]")
	dedication = fields.Char("Зориулалт")
	amount = fields.Float("Хөндсөн талбай /га/", required=True)
	note = fields.Text("Тайлбар")
	rehab_id = fields.Many2one('env.rehab', string='Rehabilitation', ondelete='cascade')
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт')
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	mining_location = fields.Many2one(related='rehab_id.mining_location', string='Үйлдвэр уурхай', readonly=True, store=True)


	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Газар хөндөлт).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

class mw_environment_rehab(models.Model):
	_name = 'env.rehab'
	_description = "Environmental Rehabilitation"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'year DESC'


	def _get_year(self):
		year_list = []
		current_year = datetime.now().year
		for j in range(current_year + 1, current_year - 25, -1):
			year_list.append((str(j), str(j)))
		return year_list

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	year = fields.Selection(string='Он', selection=_get_year, required=True, readonly=True, states={'draft':[('readonly',False)]})
	location_id = fields.Many2one('env.parameter', string='Байршил', domain="[('type','=','rehab_location'),('is_active','=', 'active')]", readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('env.rehab.line', 'rehab_id', string='Rehabilitation', readonly=True, states={'draft':[('readonly',False)]})
	land_ids = fields.One2many('env.rehab.land', 'rehab_id', string='Affected Land', readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', default=default_location, required=True, domain="[('is_active','=', 'active')]", tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)
	
	def action_to_done(self):
		for item in self.line_ids:
			if not item.attachment_ids:
				raise  UserError('Хавсралт оруулна уу!!!(Газар хөндөлт).')
		for line in self.land_ids:
			if not line.attachment_ids:
				raise  UserError('Хавсралт оруулна уу!!!(Газар хөндөлт).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	@api.depends('line_ids', 'line_ids.amount')
	def _total_rehab(self):
		total = 0
		for rehab in self.line_ids:
			total = total + rehab.amount
		self.total_rehab = total

	total_rehab = fields.Float(compute=_total_rehab, string='Нийт нөхөн сэргээсэн талбай /га/', store=True, readonly=True)

	@api.depends('land_ids', 'land_ids.amount')
	def _total_land(self):
		total = 0
		for land in self.land_ids:
			total = total + land.amount
		self.total_land = total

	total_land = fields.Float(compute=_total_land, string='Нийт хөндсөн талбай /га/', store=True, readonly=True)

	@api.model
	def create(self, vals):
		value = self.search([('mining_location', '=', vals['mining_location']), ('year', '=', vals['year'])])
		if value:
			raise UserError('Анхааруулга!!!, Сонгосон уурхайд, сонгосон онд, сонгосон байршилд бүртгэл байгаа тул дахин үүсгэх боломжгүй.')

		res = super(mw_environment_rehab, self).create(vals)
		return res

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, obj.mining_location.name + ' : ' + obj.year + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_rehab, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res

class mw_environment_animal(models.Model):
	_name = 'env.animal'
	_description = "Environmental Animal"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date DESC'

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Datetime(string='Огноо', required=True, default=fields.Datetime.now, readonly=True, states={'draft':[('readonly',False)]})
	animal = fields.Many2one('env.parameter', string='Ан амьтан', required=True, domain="[('type','=','animal'),('is_active','=', 'active')]", readonly=True, states={'draft':[('readonly',False)]})
	animal_category = fields.Selection(string='Амьтны ангилал', related='animal.category', store=True, readonly=True)
	number = fields.Integer("Харагдсан тоо", required=True, readonly=True, states={'draft':[('readonly',False)]})
	location = fields.Char("Байршил/Гараар бичих/", readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	location_id = fields.Many2one('env.mining.line', string='Байршил', readonly=True, states={'draft':[('readonly',False)]})
	image= fields.Image(related='animal.image', readonly=True)

	gender = fields.Selection([
		('male', 'Эр'),
		('female', 'Эм'),
		('idk', 'Тодорхойгүй')], 'Хүйсийн бүтэц', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Амьтны үзэгдэл).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def _get_year_month(self):
		year_list = []
		current_year = datetime.now().year
		current_month = datetime.now().month
		for j in range(current_month, 0, -1):
			year_month = str(current_year) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(12, 0, -1):
			year_month = str(current_year - 1) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(2, 7, 1):
			year_month = str(current_year - j) + "/12"
			year_list.append((year_month, year_month))
		return year_list
	
	year_month = fields.Selection(string='Он/Сар', selection=_get_year_month)


	@api.onchange('year_month')
	def _get_year(self):
		if self.year_month:
			self.year = self.year_month[0:4]
		else:
			self.year = str(datetime.now().year)

	year = fields.Char('Он')

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	_defaults = {
		'year_month': str(datetime.now().year) + ("/" if datetime.now().month > 9 else "/0") + str(
			datetime.now().month),
		'mining_location': default_location
	}

	@api.model
	def create(self, vals):

		value = self.search([
			('mining_location', '=', vals['mining_location']), 
			('date','=', vals['date']),
			('animal', '=', vals['animal'])])
		if value:
			raise UserError('Анхааруулга!!!, Сонгосон уурхайд, сонгосон сард, сонгосон амьтнаар бүртгэл байгаа тул дахин үүсгэх боломжгүй.')
		res = super(mw_environment_animal, self).create(vals)
		return res

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, obj.animal.name + ' (' + obj.mining_location.name + ' : ' + obj.date.strftime('%Y-%m-%d') + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_animal, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res


class mw_environment_expense(models.Model):
	_name = 'env.expense'
	_description = "Environmental Expense"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'expense_date DESC'

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	expense_date = fields.Date("Огноо", required=True,  default=fields.Datetime.now, readonly=True, states={'draft':[('readonly',False)]})
	expense_type = fields.Many2one('env.parameter', string='Бараа материал, Үйлчилгээний төрөл', required=True, domain="[('type','=','expense_type'),('is_active','=', 'active')]",  readonly=True, states={'draft':[('readonly',False)]})
	expense_category = fields.Selection(string='Ангилал', related='expense_type.category', store=True,  readonly=True, states={'draft':[('readonly',False)]})
	amount = fields.Float('Мөнгөн дүн', required=True,  readonly=True, states={'draft':[('readonly',False)]})
	note = fields.Text('Тайлбар',  readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', default=default_location, required=True, domain="[('is_active','=', 'active')]", readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	payment_state = fields.Selection([
		('not_paid', 'Төлөгдөөгүй'),
		('paided', 'Төлөгдсөн')
	], 'Төлбөрийн төлөв', 
	tracking=True, default='not_paid', readonly=False)
	# compute='_compute_payment_state', store=True,
	
	department_id = fields.Many2one('hr.department', default=lambda self: self.env.user.department_id, string='Хэлтэс', store=True)
	contract_id = fields.Many2one('contract.document.real', string='Холбоотой гэрээ', tracking=True, domain="[('state_type','=','done'),('department_id','=',department_id)]", readonly=True, states={'draft':[('readonly',False)]})
	payment_ids = fields.One2many(related='contract_id.payment_line_ids', string='Төлбөрийн мэдээлэл', readonly=True)
	total_paid = fields.Float(string='Нийт дүн', compute='_compute_payment', readonly=True)
	total_paided = fields.Float(string='Нийт төлөгдөөгүй дүн', compute='_compute_payment', readonly=True)
	toal_unpaid = fields.Float(string='Үлдэгдэл дүн', compute='_compute_payment', readonly=True)
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)

	@api.depends('contract_id','payment_ids')
	def _compute_payment(self):
		for item in self:
			if item.payment_ids:
				item.total_paid = sum(item.payment_ids.mapped('paid_amount'))
				item.total_paided = sum(item.payment_ids.mapped('disburse_amount'))
				item.toal_unpaid = sum(item.payment_ids.mapped('paid_amount')) - sum(item.payment_ids.mapped('disburse_amount'))
			else:
				item.total_paid = 0
				item.total_paided = 0
				item.toal_unpaid = 0
	
	
				
	@api.depends('contract_id','payment_ids')
	def _compute_payment(self):
		for item in self:
			if item.payment_ids:
				item.total_paid = sum(item.payment_ids.mapped('paid_amount'))
				item.total_paided = sum(item.payment_ids.mapped('disburse_amount'))
				item.toal_unpaid = sum(item.payment_ids.mapped('paid_amount')) - sum(item.payment_ids.mapped('disburse_amount'))
			else:
				item.total_paid = 0
				item.total_paided = 0
				item.toal_unpaid = 0
	
	# @api.depends('contract_id','payment_ids','total_paid')
	# def _compute_payment_state(self):
	# 	for item in self:
	# 		if item.toal_unpaid == 0 and item.total_paid!=0:
	# 			item.payment_state = 'paided'
	# 		else:
	# 			item.payment_state = 'not_paid'


	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Бараа материал, Үйлчилгээний зардал).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, obj.expense_type.name + ' (' + obj.mining_location.name + ' : ' + obj.expense_date.strftime('%Y-%m-%d') + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_expense, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res

class mw_environment_garden(models.Model):
	_name = 'env.garden'
	_description = "Environmental Garden"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'year_month DESC'

	def _get_year(self):
		year_list = []
		current_year = datetime.now().year
		for j in range(current_year + 1, current_year - 25, -1):
			year_list.append((str(j), str(j)))
		return year_list

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]",  readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	garden_line_ids = fields.One2many('env.garden.line', 'garden_id', string='Ногоон байгууламж line', readonly=True, states={'draft':[('readonly',False)]})
	garden_type = fields.Selection([
		('garden', 'Арчилгаа')], 'Төрөл', tracking=True, default='garden', required=True, readonly=True, states={'draft':[('readonly',False)]})
	year = fields.Selection(string='Он', selection=_get_year, required=True, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)

	def action_to_done(self):
		for item in self.garden_line_ids:
			if not item.attachment_ids:
				raise  UserError('Хавсралт оруулна уу!!!(Ногоон байгууламжийн арчилгаа).')
			else: 
				self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def _get_year_month(self):
		year_list = []
		current_year = datetime.now().year
		current_month = datetime.now().month
		for j in range(current_month, 0, -1):
			year_month = str(current_year) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(12, 0, -1):
			year_month = str(current_year - 1) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(2, 7, 1):
			year_month = str(current_year - j) + "/12"
			year_list.append((year_month, year_month))
		return year_list

	year_month = fields.Selection(string='Он/Сар', selection=_get_year_month)

	@api.onchange('year_month')
	def _get_year(self):
		if self.year_month:
			self.year = self.year_month[0:4]
		else:
			self.year = str(datetime.now().year)

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	_defaults = {
		'year_month': str(datetime.now().year) + ("/" if datetime.now().month > 9 else "/0") + str(
			datetime.now().month),
		'mining_location': default_location
	}

	@api.model
	def create(self, vals):
		value = self.search([
			('mining_location', '=', vals['mining_location']),
			('year', '=', vals['year']),
		])
		if value:
			raise UserError('Анхааруулга!!!, Сонгосон уурхайд, сонгосон сар, сонгосон төрөлд бүртгэл байгаа тул дахин үүсгэх боломжгүй.')

		res = super(mw_environment_garden, self).create(vals)
		return res

	def name_get(self):
		result = []
		for obj in self:
			result.append(
				(obj.id, ' (' + obj.mining_location.name + ' : ' + obj.year + ')'))
		return result

	def fields_get(self, allfields=None, attributes=None):
		res = super(mw_environment_garden, self).fields_get(allfields, attributes=attributes)
		fields = set(res.keys())
		for field in fields:
			if field in ('create_uid', 'create_date', 'write_uid', 'write_date'):
				res[field]['selectable'] = False  # to hide in Add Custom filter view
				res[field]['sortable'] = False  # to hide in group by view
				res[field]['exportable'] = False  # to hide in export list
				res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
		return res

class EnvGardenLine(models.Model):
	_name = 'env.garden.line'
	_description = "Environmental Garden Line"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date DESC'


	date = fields.Date(string='Огноо', required=True, default=fields.Date.context_today)
	garden_location = fields.Char(string='Байршил')
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	garden_activity = fields.Many2one('env.parameter', string='Үйл ажиллагаа', domain="[('type','=','garden_activity'),('is_active','=', 'active')]")
	amount = fields.Integer(string='Тоо хэмжээ')
	uom = fields.Selection(string='Хэмжих нэгж', related='garden_activity.category', store=True)
	note = fields.Text('Тайлбар')
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт')
	garden_id = fields.Many2one('env.garden', string='Ногоон байгууламж')
	mining_location = fields.Many2one(related='garden_id.mining_location', string='Үйлдвэр уурхай')
	user_id = fields.Many2one('res.users', string='Бүртгэсэн',  default=lambda self: self.env.user.id)

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Ногоон байгууламж).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


class MwEnvTree(models.Model):
	_name = 'env.tree'
	_description = "Environmental Tree"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'year_month DESC'

	def _get_year(self):
		year_list = []
		current_year = datetime.now().year
		for j in range(current_year + 1, current_year - 25, -1):
			year_list.append((str(j), str(j)))
		return year_list

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]",  readonly=True, states={'draft':[('readonly',False)]}, tracking=True)
	tree_line_ids = fields.One2many('env.tree.line', 'tree_id', string='Мод бут line', readonly=True, states={'draft':[('readonly',False)]})
	tree_type = fields.Selection([
		('tree', 'Модны бүртгэл')], 'Төрөл', tracking=True, default='tree', required=True, readonly=True, states={'draft':[('readonly',False)]})
	year = fields.Selection(string='Он', selection=_get_year, required=True, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one(related='mining_location.company_id', string='Компани', readonly=True, store=True)
	
	def action_to_done(self):
		for item in self.garden_line_ids:
			if not item.attachment_ids:
				raise  UserError('Хавсралт оруулна уу!!!(Ногоон байгууламжийн арчилгаа).')
			else: 
				self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def _get_year_month(self):
		year_list = []
		current_year = datetime.now().year
		current_month = datetime.now().month
		for j in range(current_month, 0, -1):
			year_month = str(current_year) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(12, 0, -1):
			year_month = str(current_year - 1) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(2, 7, 1):
			year_month = str(current_year - j) + "/12"
			year_list.append((year_month, year_month))
		return year_list

	year_month = fields.Selection(string='Он/Сар', selection=_get_year_month)


class EnvTreeLine(models.Model):
	_name = 'env.tree.line'
	_description = "Environmental Tree Line"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date DESC'

	@api.depends('number', 'new_number')
	def _get_total_number(self):
		for item in self:
			if item.number:
				item.total_number = item.number + item.new_number - item.delete_tree if item.new_number else item.number
			else:
				item.total_number = item.new_number - item.delete_tree if item.new_number else False


	date = fields.Date(string='Огноо', required=True, default=fields.Date.context_today)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	tree_id = fields.Many2one('env.tree', string='Мод бут')
	note = fields.Text('Тайлбар')
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт')
	mining_location = fields.Many2one(related='tree_id.mining_location', string='Үйлдвэр уурхай')
	tree = fields.Many2one('env.parameter', string='Мод бут', domain="[('type','=','tree'),('is_active','=', 'active')]")
	season = fields.Selection([
		('fall', 'Намар'),
		('spring', 'Хавар'),
		('other', 'Бусад үед')], string='Улирал', default='fall')
	number = fields.Integer('Хуучин байсан мод')
	delete_tree = fields.Integer('Хорогдсон мод')
	new_number = fields.Integer('Шинэ мод', default=0)
	total_number = fields.Integer('Нийт тоо ширхэг', readonly=True, compute=_get_total_number, store=True)
	user_id = fields.Many2one('res.users', string='Бүртгэсэн',  default=lambda self: self.env.user.id)


	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Мод бут).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})
