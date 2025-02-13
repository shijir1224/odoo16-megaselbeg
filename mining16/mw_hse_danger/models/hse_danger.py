from odoo import  api, fields, models, _
import time
from datetime import datetime
from odoo.exceptions import UserError



class HseDanger(models.Model):
	_name ='hse.danger'
	_description = 'Hse Danger'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.danger')
		return name
   
	name = fields.Char(string='Дугаар', default=_default_name, required=True, readonly=True)
	sub_name = fields.Char(string='Дэд Гарчиг', tracking=True, required=True)
	date = fields.Date(string='Огноо', default=fields.Date.context_today, required=True , tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', 'danger_attachment_rel', 'danger_id', string="Хавсралт файл", tracking=True)

	def write(self, values):
		if not values.get['attachment_ids']:
			raise UserError(_('Хавсралт заавал оруулна уу!!!!'))
		return super().write(values)
	

class HseDangerRegistration(models.Model):
	_name ='hse.danger.registration'
	_description = 'Hse Danger Registration'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def create(self, vals):
		value = self.search([
			('branch_id', '=', vals['branch_id']), 
			('year_month', '=', vals['year_month'])
		])
		if value:
			raise UserError(_(u'Анхааруулга!!'), _(u'Сонгосон салбар, сонгосон онд бүртгэл байгаа тул дахин үүсгэх боломжгүй.'))
		res = super(HseDangerRegistration, self).create(vals)
		return res

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.danger.registration')
		return name
	
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
   
	name = fields.Char(string='Дугаар', default=_default_name, required=True, readonly=True)
	state = fields.Selection([
		('draft', 'Ноорог'),
		('done', 'Батлагдсан')], 'Төлөв', readonly=True, default='draft')
	branch_id = fields.Many2one('res.branch', string='Төсөл', required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	year_month = fields.Selection(string='Он/сар', selection=_get_year_month, required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('hse.danger.registration.line', 'parent_id', string='Line', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_done(self):
		self.write({'state': 'done'})

class HseDangerRegistrationLine(models.Model):
	_name ='hse.danger.registration.line'
	_description = 'Hse Danger Registration Line'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	parent_id = fields.Many2one('hse.danger.registration', string='Эцэг',)
	chemicals_name = fields.Char(string='Химийн бодисын нэр')
	chemical_formula = fields.Char(string='Химийн томьёо')
	cas_code = fields.Char(string='CAS код')
	license_number = fields.Char(string='Тусгай зөвшөөрлийн дугаар')
	first_balance = fields.Float(string='Эхний үлдэгдэл, тн')
	date = fields.Date(string='Огноо')
	rec_amount = fields.Float(string='Хүлээн авсан хэмжээ, тн')
	rec_employee_id = fields.Many2one('hr.employee', string='Хянасан ажилтны нэр')

	wit_amount = fields.Float(string='Зарлагадсан хэмжээ, тн')
	use_section = fields.Char(string='Ашиглах хэсгийн нэр')
	wit_employee_id = fields.Many2one('hr.employee', string='Хянасан ажилтны нэр')
	total_balance = fields.Float(string='Нийт үлдэгдэл, тн', compute='_compute_total_balance', store=True)
	bag = fields.Integer(string='Уут /Шуудай/, ш')
	iron = fields.Integer(string='Төмөр торх /боошиг/, ш')
	plastic_bag = fields.Integer(string='Хуванцар торх /боошиг/, ш')
	plastic_bottle = fields.Integer(string='Хуванцар сав, ш')

	@api.depends('first_balance','rec_amount','wit_amount')
	def _compute_total_balance(self):
		for item in self:
			if item.first_balance and item.wit_amount:
				item.total_balance = item.first_balance + item.rec_amount - item.wit_amount
			else:
				item.total_balance = 0


class HseCityCode(models.Model):
	_name = 'hse.city.code'
	_description = 'Hse city code'

	code = fields.Integer(string='Код', required=True)
	name = fields.Char(string='Нэр', required=True)

class HseWaterCar(models.Model):
	_name = 'hse.water.car'
	_description = 'Hse water car'

	name = fields.Char(string='Park')
	statenumber = fields.Char(string="Улсын дугаар", required=True)
	company_id = fields.Many2one('res.partner', string='Компани', required=True)
	capacity = fields.Float(string='Хэмжээ')
	water_type = fields.Selection([
		('ahui','Ахуй'),
		('tree','Мод'),
		('uildver','Үйлдвэр')
		], string='Усны төрөл', required=True)
	car = fields.Selection([
		('water','Усны машин'),
		('fire','Галын машин'),
		('other','Бусад')
		], string='Усны машин')
	

class HseWaterRegistration(models.Model):
	_name ='hse.water.registration'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Hse Water Registration'

	@api.model
	def create(self, vals):
		value = self.search([
			('branch_id', '=', vals['branch_id']), 
			('year_month', '=', vals['year_month'])
		])
		if value:
			raise UserError(_(u'Анхааруулга!!'), _(u'Сонгосон салбар, сонгосон онд бүртгэл байгаа тул дахин үүсгэх боломжгүй.'))
		res = super(HseWaterRegistration, self).create(vals)
		return res
	
	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.water.registration')
		return name
	
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
	

	name = fields.Char(string='Дугаар', default=_default_name, required=True, readonly=True)
	state = fields.Selection([('draft','Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, default='draft', tracking=True)
	branch_id = fields.Many2one('res.branch', string='Төсөл', required=True, readonly=True, states={'draft':[('readonly',False)]})
	year_month = fields.Selection(string='Он/сар', selection=_get_year_month, required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	water_registration_line_ids = fields.One2many('hse.water.registration.line', 'parent_id', 'Water registration line', readonly=True, states={'draft':[('readonly',False)]})
	water_registration_line = fields.One2many('hse.water.circulating.registration.line', 'parent_id', 'Water circulating registration line', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

class HseWaterRegistrationLine(models.Model):
	_name = 'hse.water.registration.line'
	_description = 'Hse Water Registration line'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	parent_id = fields.Many2one('hse.water.registration', 'Water_registration', ondelete='cascade', readonly=True)
	well_id = fields.Many2one('hse.water.well', string='худгийн нэр',  required=True)
	date_start = fields.Date(string='Эхлэх хугацаа', default=fields.Date.context_today,  required=True)
	date_end = fields.Date( string='Дуусах хугацаа')
	used_day = fields.Integer(string='Ашигласан хоног', compute='_compute_used_day', store=True, readonly=True)
	counter_number = fields.Char(string='Тоолуурын дугаар')
	counter_before= fields.Float(string='Тоолуурын өмнөх заалт') 
	counter_after = fields.Float(string='Тоолуурын дараах заалт')
	used_water = fields.Float(string='Ашигласан ус/шоо метр/', compute='_compute_used_amount', store=True, readonly=True)

	@api.depends('counter_before','counter_after')
	def _compute_used_amount(self):
		for obj in self:
			if obj.counter_after and obj.counter_before:
				obj.used_water = obj.counter_after - obj.counter_before
			else:
				obj.used_water = 0

	@api.depends('date_start','date_end')
	def _compute_used_day(self):
		for line in self:
			if line.date_start and line.date_end:
				line.used_day = (line.date_end - line.date_start).days
			else:
				line.used_day = 0

class HsecirWaterCulatingRegistrationLine(models.Model):
	_name = 'hse.water.circulating.registration.line'
	_description = 'Hse Water Circulating Registration line'

	parent_id = fields.Many2one('hse.water.registration', 'Water_circulating_registration', ondelete='cascade', readonly=True)
	well_id = fields.Many2one('hse.water.well', string='Хаягдлын далангийн дугаар', required=True)
	date_start = fields.Date(string='Эхлэх хугцаа', default=fields.Date.context_today, required=True)
	date_end = fields.Date(string='Дуусах хугацаа')
	used_day = fields.Integer(string='Ашигласан хоног', readonly=True, compute='_compute_used_day', store=True)
	counter_number = fields.Char(string='Тоолуурын дугаар')
	counter_before= fields.Float(string='Тоолуурын өмнөх заалт') 
	counter_after = fields.Float(string='Тоолуурын дараах заалт')
	used_water = fields.Float(string='Ашигласан ус/шоометр/',  compute='_compute_used_amount', store=True, readonly=True)

	@api.depends('counter_before','counter_after')
	def _compute_used_amount(self):
		for obj in self:
			if obj.counter_after and obj.counter_before:
				obj.used_water = obj.counter_after - obj.counter_before
			else:
				obj.used_water = 0

	@api.depends('date_start','date_end')
	def _compute_used_day(self):
		for line in self:
			if line.date_start and line.date_end:
				line.used_day = (line.date_end - line.date_start).days
			else:
				line.used_day = 0

class HseWaterWell(models.Model):
	_name = 'hse.water.well'
	_description = 'Hse city well'

	code = fields.Integer(string='Код', required=True)
	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
		('well_name','Худгийн нэр, дугаар'),
		('people','Хаягдлын далангийн дугаар'), 
		
	], string='Төрөл', required=True)
	branch_id = fields.Many2one('res.branch', string='Төсөл')