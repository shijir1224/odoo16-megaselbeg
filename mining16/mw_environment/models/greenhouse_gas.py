# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
import time
from odoo.exceptions import UserError


class mak_environment_object(models.Model):
	_name = 'env.object'
	_description = "Environmental Object"
	_inherit = ['mail.thread','mail.activity.mixin']
	_order = 'area_size DESC'

	_sql_constraints = [
		('name_uniq', 'UNIQUE(name, object_company)', 'Object and company must be unique')
	]

	@api.model
	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.name))
		return result

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False


	name = fields.Char('Объектын нэр', required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	object_uom = fields.Selection([
		('га', 'га'),
		('м2', 'м2')],'Хэмжих нэгж', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	area_size = fields.Float('Талбайн хэмжээ', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", defautl=default_location, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id, readonly=True, tracking=True)
	date_object = fields.Date('Үүсгэсэн огноо', default=fields.Date.context_today, readonly=True)
	technical_ids = fields.One2many('env.technical', 'env_object', string='Техникүүд', readonly=True, states={'draft':[('readonly',False)]})
	heat = fields.One2many('env.heat', 'env_object', 'Дулаанууд', readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	sector_id = fields.Many2one('hr.department', string='Сектор', default=lambda self: self.env.user.department_id.id, readonly=True)
	object_location_id = fields.Many2one('account.asset.location', string='Байрлал', tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	object_company_id = fields.Many2one('res.company', 'Компани', tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})

	@api.onchange('object_company_id')
	def onch_location_dom(self):
		if self.object_company_id:
			search_domain = [('company_id', '=', self.object_company_id.id)]
			domain = {'object_location_id': search_domain}
			return {'domain': domain}

	def technic_import(self):
		for item in self:
			if item.technical_ids:
				raise  UserError('Техникийн мэдээлэл оруулсан байна. (Мөрны мэдээллээ устгана уу).')
			else:
				technic_ids = self.env['account.asset'].search([('company_id', '=', item.object_company_id.id),('location_id', '=', item.object_location_id.id)])
				for line in technic_ids:
					self.env['env.technical'].create({
						'env_object': self.id,
						'asset_source_id': line.id,
						'quantity': 1,
					})		

	def clear_lines(self):
		self.technical_ids.unlink()			


class mak_environment_technic(models.Model):
	_name = 'env.technical'
	_description = "Environmental Technic"
	_order = 'asset_source_id DESC'
	_rec_name = 'asset_source_id'

	_sql_constraints = [
		('name_uniq', 'UNIQUE(asset_source_id, env_object)', 'Technical source and object must be unique')
	]

	@api.model
	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.asset_source_id))
		return result
	
	state = fields.Selection(related='env_object.state', string='Төлөв', store=True, readonly=True)
	asset_source_id = fields.Many2one('account.asset', string='Хөрөнгө', reqired=True)
	env_object = fields.Many2one('env.object', string='Объект')
	quantity = fields.Integer('Тоо хэмжээ', default=1)
	technic_uom = fields.Many2one('uom.uom', 'Хэмжих нэгж')
	capacity = fields.Float('Хүчин чадал')
	description = fields.Char('Тайлбар')
	technic_type = fields.Boolean('Түлш эсэх', default=False)
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	location_id = fields.Many2one(related='env_object.object_location_id', string='Байрлал', readonly=True, store=True)
	company_id = fields.Many2one(related='env_object.object_company_id', string='Компани', readonly=True, store=True)


class MakTechnicEquipment(models.Model):
	_inherit = 'technic.equipment'
	_description = "Technic equipment"
	_order = 'create_date DESC'
	
	engine_capacity = fields.Float(related="technic_setting_id.engine_capacity", string='Хөдөлгүүрийн багтаамж', store=True)
	engine_power = fields.Float(related="technic_setting_id.engine_power", store=True)
	fuel_medium_idle = fields.Float(related="technic_setting_id.fuel_medium_idle", string='Дундаж зарцуулалт', store=True)
	fuel_type = fields.Selection(related="technic_setting_id.fuel_type", string='Хөдөлгүүрийн төрөл', store=True)
	gearbox_type = fields.Selection(related="technic_setting_id.transmission", string='Хурдны хайрцгийн төрөл', store=True)
	technic_type = fields.Selection(related="technic_setting_id.technic_type", store=True)
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	sector_id = fields.Many2one('hr.department', string='Сектор', default=lambda self: self.env.user.sector_id.id, readonly=True)
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id)
	avg_fuel = fields.Float('Зарцуулсан түлш', digits=(15,4), store=True)
	technic_fuel_ids = fields.One2many('env.technic', 'technic_id', string='Түлшний түүх', readonly=True)
				
	@api.depends('engine_power')
	def _compute_total_fuel(self):
		fuels = self.env['oil.fuel.line'].sudo().search([('technic_id','=',self.id),('parent_id.state','!=','done')])
		if fuels:
			self.avg_fuel = sum(fuels.mapped('product_qty'))
		else:
			self.avg_fuel = 0
	

	def total_fuel_line(self):
		fuels = self.env['oil.fuel.line'].sudo().search([('technic_id','=',self.id),('parent_id.state','!=','done')])
		if fuels:
			self.avg_fuel = sum(fuels.mapped('product_qty'))
		else:
			self.avg_fuel = 0
	

	def total_fuel_all(self):
		technic_ids = self.env['technic.equipment'].search([('id','!=', False)])
		if technic_ids:
			for line in technic_ids:
				line.total_fuel_line()


class mak_environment_tseh(models.Model):
	_name = 'env.tseh'
	_description = "Environmental TSEH"
	_inherit = ['mail.thread','mail.activity.mixin']
	_rec_name = 'mining_location'

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", defautl=default_location, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_from = fields.Date("Эхлэх огноо", default=time.strftime('%Y-%m-01'), required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_to = fields.Date("Дуусах огноо",  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	consu_fuel = fields.Float('Түлшний зарцуулалт', digits=(15,4), readonly=True, states={'draft':[('readonly',False)]})
	uom_id = fields.Many2one('uom.uom', 'Хэмжих нэгж',  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	sector_id = fields.Many2one('hr.department', string='Сектор', default=lambda self: self.env.user.sector_id.id, readonly=True)
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id, required=True, readonly=True)
	consumption_electricity = fields.Float('Цахилгааны хэрэглээ', digits=(15,4),  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	install_capacity = fields.Float(string='Суурьлагдсан хүчин чадал', digits=(16,4), readonly=True, states={'draft':[('readonly',False)]})
	downtime = fields.Float(string='Сул зогсолт', digits=(16,4), readonly=True, states={'draft':[('readonly',False)]})
	pay_off = fields.Float(string='Алдангa', digits=(16,4), readonly=True, states={'draft':[('readonly',False)]})
	savings = fields.Float(string='Хэмнэлт', digits=(16,4), readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('env.tseh.line', 'tseh_id', string='Объектууд')
	mvt_time = fields.Float(string='МВт.цаг', compute='_compute_amount', store=True, readonly=True)
	tonn_mvt = fields.Float(string='тонн/МВт.цаг', default=0.75, readonly=True)
	tonn_co2 = fields.Float(string='тонн/CO2', compute='_compute_amount', store=True, readonly=True)
	gg_co2 = fields.Float(string='Gg CO2', compute='_compute_amount', store=True, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Цахилгаан).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


	@api.depends('consumption_electricity','mining_location')
	def _compute_amount(self):
		for item in self:
			if item.consumption_electricity:
				item.mvt_time = item.consumption_electricity/1000				
				item.tonn_co2 = item.mvt_time*item.tonn_mvt
				item.gg_co2 = item.tonn_co2/1000
			else:
				item.mvt_time = 0
				item.tonn_co2 = 0
				item.gg_co2 = 0

	def clear_lines(self):
		self.line_ids.unlink()

	def object_import(self):
		for item in self:
			if item.line_ids:
				raise  UserError('Объектын мэдээлэл оруулсан байна. (Мөрны мэдээллээ устгана уу).')
			else:
				line_ids = self.env['env.object'].search([('object_company_id', '=', item.company_id.id),('mining_location', '=', item.mining_location.id)])
				for line in line_ids:
					self.env['env.tseh.line'].create({
						'tseh_id': self.id,
						'env_object': line.id,
					})

class EnvTsehLine(models.Model):
	_name = 'env.tseh.line'
	_description = "Environmental Tseh Line"
	_inherit = ['mail.thread','mail.activity.mixin']
	

	tseh_id = fields.Many2one('env.tseh', string='TSEH ID', ondelete='cascade', readonly=True)
	mining_location = fields.Many2one(related='tseh_id.mining_location', string='Үйлдвэр, Уурхай', store=True, readonly=True)
	env_object = fields.Many2one('env.object', string='Объект', required=True, domain="[('mining_location','=', mining_location)]")
	electric_consumption = fields.Float(string='Цахилгаан эрчим хүчний хэрэглээ', digits=(16,4))


class mak_environment_heat(models.Model):
	_name = 'env.heat'
	_description = "Environmental Heat"
	_inherit = ['mail.thread','mail.activity.mixin']
	_rec_name = 'mining_location'

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", defautl=default_location, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_from = fields.Date("Эхлэх огноо", default=time.strftime('%Y-%m-01'), required=True,  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_to = fields.Date("Дуусах огноо",  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	uom_id = fields.Many2one('uom.uom', 'Хэмжих нэгж',  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	env_object = fields.Many2one('env.object', string='Объект', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	sector_id = fields.Many2one('hr.department', string='Сектор', default=lambda self: self.env.user.sector_id.id, readonly=True)
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, tracking=True, readonly=True)
	line_ids = fields.One2many('env.heat.line', 'heat_id', string='Объектууд', readonly=True, states={'draft':[('readonly',False)]})
	source = fields.Selection([
		('coal', 'Нүүрс'),
		('center', 'Төвийн шугам')
	], string='Дулааны эх үүсвэр', default='coal', readonly=True, states={'draft':[('readonly',False)]})
	desc = fields.Char(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Дулаан).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


	def clear_lines(self):
		self.line_ids.unlink()

	def object_import(self):
		for item in self:
			if item.line_ids:
				raise  UserError('Объектын мэдээлэл оруулсан байна. (Мөрны мэдээллээ устгана уу).')
			else:
				line_ids = self.env['env.object'].search([('object_company_id', '=', item.company_id.id),('mining_location', '=', item.mining_location.id)])
				for line in line_ids:
					self.env['env.heat.line'].create({
						'heat_id': self.id,
						'env_object': line.id,
					})

class EnvHeatLine(models.Model):
	_name = 'env.heat.line'
	_description = "Environmental Heat Line"
	_inherit = ['mail.thread','mail.activity.mixin']

	heat_id = fields.Many2one('env.heat', string='HEAT ID', ondelete='cascade', readonly=True)
	env_object = fields.Many2one('env.object', string='Объект', ondelete='cascade', required=True, domain="[('mining_location','=', mining_location)]")
	used_coal = fields.Float(string='Ашигласан нүүрсний хэмжээ/тн/', digits=(16,4))
	used_calor_coal = fields.Float(string='Ашигласан нүүрсний илчлэг', digits=(16,4))
	mining_location = fields.Many2one(related='heat_id.mining_location', string='Үйлдвэр, Уурхай', store=True, readonly=True)


class EnvTechnic(models.Model):
	_name = 'env.technic'
	_description = "Environmental Technic"
	_inherit = ['mail.thread','mail.activity.mixin']
	_rec_name = 'technic_id'


	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	technic_id = fields.Many2one('technic.equipment', string='Техник', ondelete='cascade', required=True, readonly=True, states={'draft':[('readonly',False)]})
	engine_capacity = fields.Float(related="technic_id.technic_setting_id.engine_capacity", string='Хөдөлгүүрийн багтаамж', store=True, readonly=True)
	branch_id = fields.Many2one(related='technic_id.branch_id', string='Салбар', store=True, readonly=True, states={'draft':[('readonly',False)]})
	date_from = fields.Date("Эхлэх огноо", default=time.strftime('%Y-%m-01'), required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_to = fields.Date("Дуусах огноо",  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', 'Үйлдвэр/Уурхай', ondelete='cascade', required=True, readonly=True, states={'draft':[('readonly',False)]})
	owner_type = fields.Selection(related='technic_id.owner_type', string='Эзэмшлийн төрөл', readonly=True, states={'draft':[('readonly',False)]})
	technic_category = fields.Selection([
		('small', 'Бага оврын'),
		('medium', 'Дунд оврын'),
		('big', 'Хүнд даацын')
	], string='Tехник ангилал', readonly=True, states={'draft':[('readonly',False)]})

	fuel_type = fields.Selection([
		('diesel', 'Дизель'),
		('gas', 'Бензин'),
		('hybrid', 'Цахилгаан')
	], string='Түлшний систем', readonly=True, states={'draft':[('readonly',False)]})
	fuel_amount = fields.Float('Түлшний хэрэглээ', digits=(15,4),  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	uom_id = fields.Many2one('uom.uom', 'Хэмжих нэгж',  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	kg = fields.Float(string='Kg',  compute='_compute_amount', store=True, readonly=True)
	tn = fields.Float(string='Tn', compute='_compute_amount', store=True, readonly=True)
	tj = fields.Float(string='Хэрэглээ TJ', compute='_compute_amount', store=True, readonly=True)
	kg_CO2 = fields.Float(string='kg CO2/TJ', default=74100, readonly=True)
	kg_CH4 = fields.Float(string='kg CH4/TJ', default=3, readonly=True)
	kg_N2O = fields.Float(string='kg N2O/TJ', default=6, readonly=True)
	tn_CO2 = fields.Float(string='tn CO2', compute='_compute_amount', store=True, readonly=True)
	tn_CH4 = fields.Float(string='tn CH4', compute='_compute_amount', store=True, readonly=True)
	tn_N2O = fields.Float(string='tn N2O', compute='_compute_amount', store=True, readonly=True)
	co2e_co2 = fields.Float(string='CO2e(CO2)', compute='_compute_amount', store=True, readonly=True)
	co2e_ch4 = fields.Float(string='CO2e(CH4)', compute='_compute_amount', store=True, readonly=True)
	co2e_n20 = fields.Float(string='CO2e(N20)', compute='_compute_amount', store=True, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		# if not self.attachment_ids:
		# 	raise  UserError('Хавсралт оруулна уу!!!(Техник).')
		# else: 
		self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


	@api.depends('fuel_amount','technic_category','technic_id')
	def _compute_amount(self):
		for item in self:
			if item.fuel_amount and item.fuel_type:
				item.kg = item.fuel_amount*0.85
				item.tn = item.kg/1000
				item.tj = item.tn*43
				item.kg_CO2 = 74100
				item.kg_CH4 = 3
				item.kg_N2O = 0.6
				item.tn_CO2 = item.tj*item.kg_CO2/10**6
				item.tn_CH4 = item.tj*item.kg_CH4/10**6
				item.tn_N2O = item.tj*item.kg_N2O/10**6
				item.co2e_co2 = item.tn_CO2*1
				item.co2e_ch4 = item.tn_CH4*21
				item.co2e_n20 = item.tn_N2O*310
			else:
				item.kg = 0
				item.tn = 0
				item.tj = 0
				item.tn_CO2 = 0
				item.tn_CH4 = 0
				item.tn_N2O = 0
				item.co2e_co2 = 0
				item.co2e_ch4 = 0
				item.co2e_n20 = 0


class EnvMiningQuant(models.Model):
	_name = 'env.mining.quant'
	_description = "Environmental Mining Quantaties"
	_inherit = ['mail.thread','mail.activity.mixin']
	_rec_name = 'mining_location'


	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', 'Үйлдвэр/Уурхай', ondelete='cascade', required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_from = fields.Date("Эхлэх огноо", default=time.strftime('%Y-%m-01'), required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_to = fields.Date("Дуусах огноо",  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	mining_category = fields.Selection([
		('coal', 'Нүүрс'),
		('lime', 'Шохойн чулуу'),
		('gypsum', 'Гөлтгөнө'),
		('clay_sand', 'Шавар, Элс'),
		('copper', 'Зэс-Молибдени')
	], string=' Ашигт малтмалын төрөл', readonly=True, states={'draft':[('readonly',False)]})
	mining_amount = fields.Float('Олборлосон хэмжээ', digits=(15,4),  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	uom_id = fields.Many2one('uom.uom', 'Хэмжих нэгж',  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	ave_revolution = fields.Float(string='Дундаж илчлэг', digits=(15,4),  tracking=True, readonly=True, states={'draft':[('readonly',False)]})

	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		# if not self.attachment_ids:
		# 	raise  UserError('Хавсралт оруулна уу!!!(Олборлолтын мэдээ).')
		# else: 
		self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


class EnvContractShipping(models.Model):
	_name = 'env.contract.shipping'
	_description = "Environmental Contract Shipping"
	_inherit = ['mail.thread','mail.activity.mixin']
	_rec_name = 'technic_id'

	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	technic_id = fields.Many2one('technic.equipment', 'Тээврийн хэрэгслийн марк', ondelete='cascade', required=True, domain="[('branch_id','=',branch_id),('owner_type','=','contracted')]", readonly=True, states={'draft':[('readonly',False)]})
	engine_capacity = fields.Float(related="technic_id.technic_setting_id.engine_capacity", string='Хөдөлгүүрийн багтаамж', store=True, readonly=True)
	date_from = fields.Date("Эхлэх огноо", default=time.strftime('%Y-%m-01'), required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_to = fields.Date("Дуусах огноо",  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	shipping_purpose = fields.Char(string='Тээвэр зориулалт', readonly=True, states={'draft':[('readonly',False)]})
	shipping_way = fields.Char(string='Тээвэр хийсэн чиглэл', readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one(related='mining_location.branch_id', string='Салбар', readonly=True, states={'draft':[('readonly',False)]})
	shipping_way_km = fields.Float(string='Чиглэлийн км', readonly=True, states={'draft':[('readonly',False)]})
	res = fields.Integer(string='Рейсийн тоо', readonly=True, states={'draft':[('readonly',False)]})
	total_km = fields.Float(string='Нийт км', compute='_compute_total_km', store=True, readonly=True, states={'draft':[('readonly',False)]})
	fuel_amount = fields.Float(string='Түлшний хэрэглээ', readonly=True, states={'draft':[('readonly',False)]})
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", defautl=default_location, readonly=True, states={'draft':[('readonly',False)]})
	env_object = fields.Many2one('env.object', string='Объект', ondelete='cascade', required=True, domain="[('mining_location','=', mining_location)]", readonly=True, states={'draft':[('readonly',False)]})
	tj = fields.Float(string='Түлшний хэрэглээ TJ', compute='_compute_amount', store=True, readonly=True, digits=(15,4))
	kg_CO2 = fields.Float(string='kg CO2/TJ', default=74100, readonly=True)
	kg_CH4 = fields.Float(string='kg CH4/TJ', default=3.9, readonly=True)
	kg_N2O = fields.Float(string='kg N2O/TJ', default=3.9, readonly=True)
	co2 = fields.Float(string='tn CO2', compute='_compute_amount', store=True, readonly=True, digits=(15,4))
	ch4 = fields.Float(string='tn CH4', compute='_compute_amount', store=True, readonly=True, digits=(15,4))
	n2O = fields.Float(string='tn N2O', compute='_compute_amount', store=True, readonly=True, digits=(15,4))
	co2e_co2 = fields.Float(string='CO2e(CO2)', compute='_compute_amount', store=True, readonly=True)
	co2e_ch4 = fields.Float(string='CO2e(CH4)', compute='_compute_amount', store=True, readonly=True)
	co2e_n20 = fields.Float(string='CO2e(N20)', compute='_compute_amount', store=True, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Гэрээт тээвэр).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


	@api.depends('total_km','fuel_amount','mining_location')
	def _compute_amount(self):
		for item in self:
			if item.total_km:
				item.tj = item.fuel_amount*0.0000342
				item.co2 = item.tj*item.kg_CO2/10**3
				item.ch4 = item.tj*item.kg_CH4/10**3
				item.n2O = item.tj*item.kg_N2O/10**3
				item.co2e_co2 = item.co2*1
				item.co2e_ch4 = item.ch4*21
				item.co2e_n20 = item.n2O*310
			else:
				item.tj = 0
				item.co2 = 0
				item.ch4 = 0
				item.n2O = 0
				item.co2e_co2 = 0
				item.co2e_ch4 = 0
				item.co2e_n20 = 0
		

	@api.depends('shipping_way_km','res','technic_id')
	def _compute_total_km(self):
		for item in self:
			if item.shipping_way_km and item.res:
				item.total_km = item.shipping_way_km * item.res
			else:
				item.total_km = 0

	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	branch_id = fields.Many2one('res.branch', 'Салбар', default=lambda self: self.env.user.branch_id, readonly=True)
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id, readonly=True)


class EnvAirflight(models.Model):
	_name = 'env.airflight'
	_description = "Environmental Airflight"
	_inherit = ['mail.thread','mail.activity.mixin']
	_rec_name = 'mining_location'


	def default_location(self):
		location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
		if location:
			return location.id
		else:
			return False

	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", defautl=default_location, readonly=True, states={'draft':[('readonly',False)]})
	date_from = fields.Date("Эхлэх огноо", default=time.strftime('%Y-%m-01'), required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date_to = fields.Date("Дуусах огноо",  tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	flight_from = fields.Char('Чиглэл/Хаанаас/', readonly=True, states={'draft':[('readonly',False)]})
	flight_to = fields.Char('Чиглэл/Хүртэл/', readonly=True, states={'draft':[('readonly',False)]})
	km = fields.Float(string='Нийт км', readonly=True, states={'draft':[('readonly',False)]})
	reply = fields.Char('Утга', readonly=True, states={'draft':[('readonly',False)]})
	airflight_category = fields.Selection([
		('eonomy', 'Энгийн'),
		('business', 'Бизнес'),
	], string=' Нислэгийн ангилал', readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', 'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user, readonly=True)
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id, required=True, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})

	def action_to_done(self):
		if not self.attachment_ids:
			raise  UserError('Хавсралт оруулна уу!!!(Бизнес уулзалт).')
		else: 
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})