from email.policy import default
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class HseFoodInspection(models.Model):
	_name ='hse.food.hygiene.inspection'
	_description = 'HSE Food Inspection'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.food.hygiene.inspection')
   
	name = fields.Char(string='Дугаар', default=_default_name, copy=False, readonly=True)
	state = fields.Selection([
     	('draft', 'Ноорог'), 
		('done', 'Батлагдсан')], 
    string='Төлөв', readonly=True, default='draft', tracking=True)
	inspection_type = fields.Selection([
     	('Төлөвлөгөөт', 'Төлөвлөгөөт'), 
		('Хяналт', 'Хяналт')
	], string='Үзлэгийн төрөл', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	date = fields.Datetime(string='Огноо', default=datetime.now(), tracking=True,  readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар',  readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', string="Бүртгэл хийсэн ажилтан", default=lambda self: self.env.user.id, readonly=True, states={'draft':[('readonly',False)]})
	review = fields.Text(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})

	contral_ids = fields.One2many('hse.food.internal.contral', 'inspection_id', 'Дотоод хяналт', readonly=True, states={'draft':[('readonly',False)]})
	material_ids = fields.One2many('hse.food.raw.materials', 'inspection_id', 'Түүхий эд', readonly=True, states={'draft':[('readonly',False)]})
	processing_ids = fields.One2many('hse.food.processing', 'inspection_id', 'Боловсруулалт', readonly=True, states={'draft':[('readonly',False)]})
	clean_ids = fields.One2many('hse.food.clean', 'inspection_id', 'Цэвэрлэгээ', readonly=True, states={'draft':[('readonly',False)]})

	qualified_type = fields.Selection([
     	('yes', 'Шаардлага хангасан'), 
		('no', 'Шаардлага хангаагүй')
	], string='Шаардлага хангасан эсэх', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	total_evaluation = fields.Integer(string='Нийт оноо', compute='_compute_evaluation', store=True, readonly=True)

	evaluation_type = fields.Selection([
     	('A', 'A үнэлгээ'), 
		('B', 'B үнэлгээ'),
		('C', 'C үнэлгээ'),
		('D', 'D үнэлгээ')
	], string='Үнэлгээ', tracking=True, readonly=True, compute='_compute_evaluation_calculate', store=True)

	evaluation_percent = fields.Selection([
     	('90', '90-100'),
		 ('80', '80-89'),
		 ('70', '70-79'),
		 ('69', '69-доош')
	], string='Хувь', tracking=True, readonly=True, compute='_compute_evaluation_calculate', store=True)

	evaluation_review = fields.Selection([
     	('1', 'Хангалттай сайн'),
		 ('2', 'Үйл ажиллагаа хэвийн хэдий ч илэрсэн зөрчлийг арилгаж сайжруулах хэрэгтэй'),
		 ('3', 'Үйл ажиллагаа хэвийн бус үйлчилгээндээ анхаарч илэрсэн зөрчил, дутагдлыг засаж залруулж сайжруулах шаардлагатай'),
		 ('4', 'Хангалтгүй')
	], string='Үнэлгээний тайлбар', tracking=True, readonly=True, compute='_compute_evaluation_calculate', store=True)

	conclusion = fields.Text(string='Дүгнэлт', readonly=True, states={'draft':[('readonly',False)]})
	advice = fields.Text(string='Зөвлөмж', readonly=True, states={'draft':[('readonly',False)]})

	@api.depends('contral_ids','material_ids','processing_ids','clean_ids')
	def _compute_evaluation(self):
		for item in self:
			k = 0
			if item.contral_ids:
				control_amount = sum(item.contral_ids.mapped('evaluation'))
				k+= control_amount
			if item.material_ids:
				material_amount = sum(item.material_ids.mapped('evaluation'))
				k+= material_amount
			if item.processing_ids:
				process_amount = sum(item.processing_ids.mapped('evaluation'))
				k+= process_amount
			if item.clean_ids:
				clean_amount = sum(item.clean_ids.mapped('evaluation'))
				k+= clean_amount
			item.total_evaluation = k
			if item.total_evaluation > 100:
				raise UserError(_('Нийт дүн 100%-с илүү байна !!!'))
	
	@api.depends('contral_ids','material_ids','processing_ids','clean_ids')
	def _compute_evaluation_calculate(self):
		for item in self:
			if item.total_evaluation and item.total_evaluation<69:
				item.evaluation_type = 'D'
				item.evaluation_percent = '69'
				item.evaluation_review = '1'
			if item.total_evaluation and item.total_evaluation<79 and item.total_evaluation>70:
				item.evaluation_type = 'C'
				item.evaluation_percent = '69'
				item.evaluation_review = '2'
			if item.total_evaluation and item.total_evaluation<89 and item.total_evaluation>80:
				item.evaluation_type = 'B'
				item.evaluation_percent = '80'
				item.evaluation_review = '3'
			if item.total_evaluation and item.total_evaluation<100 and item.total_evaluation>90:
				item.evaluation_type = 'A'
				item.evaluation_percent = '90'
				item.evaluation_review = '4'

	
	def unlink(self):
		if self.state == 'done':
			raise UserError(_('Батлагдсан төлөвтэй тул устгаж болохгүй! (Ноорог төлөвт оруулна уу))!!!'))
		return super(HseFoodInspection, self).unlink()

	def action_draft(self):
		self.write({'state': 'draft'})

	def action_done(self):
		self.write({'state': 'done'})
	
	
	def line_clear(self):
		if self.state=='done':
			raise UserError(_('Батлагдсан төлөвтэй тул устгаж болохгүй! (Ноорог төлөвт оруулна уу))!!!'))
		else:
			self.contral_ids.unlink()
			self.material_ids.unlink()
			self.processing_ids.unlink()
			self.clean_ids.unlink()

	def action_to_download(self):
		control_obj = self.env['hse.food.internal.contral']
		materials_obj = self.env['hse.food.raw.materials']
		processing_obj = self.env['hse.food.processing']
		clean_obj = self.env['hse.food.clean']
		obj = self.env['food.hygiene.conf']
		controls = obj.sudo().search([('type','=','workplace_inspection'),('sub_categ','=','internal_control')])
		materials = obj.sudo().search([('type','=','workplace_inspection'),('sub_categ','=','material')])
		process = obj.sudo().search([('type','=','workplace_inspection'),('sub_categ','=','processing')])
		cleans = obj.sudo().search([('type','=','workplace_inspection'),('sub_categ','=','clean')])
		if controls:
			for item in controls:
				vals = {
					'inspection_id': self.id,
					'name': item.name,
					'evaluation': 0,
				}
				control_obj.create(vals)
		
		if materials:
			for item in materials:
				vals = {
					'inspection_id': self.id,
					'name': item.name,
					'evaluation': 0,
				}
				materials_obj.create(vals)
	
		if process:
			for item in process:
				vals = {
					'inspection_id': self.id,
					'name': item.name,
					'evaluation': 0,
				}
				processing_obj.create(vals)
		
		if cleans:
			for item in cleans:
				vals = {
					'inspection_id': self.id,
					'name': item.name,
					'evaluation': 0,
				}
				clean_obj.create(vals)

class HseFoodSeasonEvaluation(models.Model):
	_name ='hse.food.season.evaluation'
	_description = 'HSE Food Season Evaluation'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.food.season.evaluation')
   
	name = fields.Char(string='Дугаар', default=_default_name, copy=False, readonly=True)
	state = fields.Selection([
     	('draft', 'Ноорог'), 
		('done', 'Батлагдсан')
	], string='Төлөв', readonly=True, default='draft', tracking=True)
	date = fields.Datetime(string='Огноо', default=datetime.now(), tracking=True,  readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар',  readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', string="Бүртгэл хийсэн", default=lambda self: self.env.user.id, readonly=True, states={'draft':[('readonly',False)]})
	review = fields.Text(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})

	food_safety_ids = fields.One2many('hse.food.safety', 'evaluation_id', 'Хүнсний аюулгүй байдал', readonly=True, states={'draft':[('readonly',False)]})
	clean_ids = fields.One2many('hse.food.clean', 'evaluation_id', 'Цэвэрлэгээ', readonly=True, states={'draft':[('readonly',False)]})
	qualified_type = fields.Selection([
     	('yes', 'Шаардлага хангасан'), 
		('no', 'Шаардлага хангаагүй')
	], string='Шаардлага хангасан эсэх', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	total_evaluation = fields.Integer(string='Нийт оноо', compute='_compute_evaluation', store=True, readonly=True)

	evaluation_type = fields.Selection([
     	('A', 'A үнэлгээ'), 
		('B', 'B үнэлгээ'),
		('C', 'C үнэлгээ'),
		('D', 'D үнэлгээ')
	], string='Үнэлгээ', tracking=True, readonly=True, compute='_compute_evaluation_calculate', store=True)

	evaluation_percent = fields.Selection([
     	('90', '90-100'),
		 ('80', '80-89'),
		 ('70', '70-79'),
		 ('69', '69-доош')
	], string='Хувь', tracking=True, readonly=True, compute='_compute_evaluation_calculate', store=True)

	evaluation_review = fields.Selection([
     	('1', 'Хангалттай сайн'),
		 ('2', 'Үйл ажиллагаа хэвийн хэдий ч илэрсэн зөрчлийг арилгаж сайжруулах хэрэгтэй'),
		 ('3', 'Үйл ажиллагаа хэвийн бус үйлчилгээндээ анхаарч илэрсэн зөрчил, дутагдлыг засаж залруулж сайжруулах шаардлагатай'),
		 ('4', 'Хангалтгүй')
	], string='Үнэлгээний тайлбар', tracking=True, readonly=True, compute='_compute_evaluation_calculate', store=True)

	conclusion = fields.Text(string='Дүгнэлт', readonly=True, states={'draft':[('readonly',False)]})
	advice = fields.Text(string='Зөвлөмж', readonly=True, states={'draft':[('readonly',False)]})

	@api.depends('food_safety_ids','clean_ids')
	def _compute_evaluation(self):
		for item in self:
			k = 0
			if item.food_safety_ids:
				food_safety_amount_amount = sum(item.food_safety_ids.mapped('evaluation'))
				k+= food_safety_amount_amount
			if item.clean_ids:
				clean_amount = sum(item.clean_ids.mapped('evaluation'))
				k+= clean_amount
			item.total_evaluation = k
			if item.total_evaluation > 100:
				raise UserError(_('Нийт дүн 100%-с илүү байна !!!'))
	
	@api.depends('food_safety_ids','clean_ids')
	def _compute_evaluation_calculate(self):
		for item in self:
			if item.total_evaluation and item.total_evaluation<69:
				item.evaluation_type = 'D'
				item.evaluation_percent = '69'
				item.evaluation_review = '1'
			if item.total_evaluation and item.total_evaluation<79 and item.total_evaluation>70:
				item.evaluation_type = 'C'
				item.evaluation_percent = '69'
				item.evaluation_review = '2'
			if item.total_evaluation and item.total_evaluation<89 and item.total_evaluation>80:
				item.evaluation_type = 'B'
				item.evaluation_percent = '80'
				item.evaluation_review = '3'
			if item.total_evaluation and item.total_evaluation<100 and item.total_evaluation>90:
				item.evaluation_type = 'A'
				item.evaluation_percent = '90'
				item.evaluation_review = '4'

	
	def unlink(self):
		if self.state == 'done':
			raise UserError(_('Батлагдсан төлөвтэй тул устгаж болохгүй! (Ноорог төлөвт оруулна уу))!!!'))
		return super(HseFoodInspection, self).unlink()

	def action_draft(self):
		self.write({'state': 'draft'})

	def action_done(self):
		self.write({'state': 'done'})
	
	
	def line_clear(self):
		if self.state=='done':
			raise UserError(_('Батлагдсан төлөвтэй тул устгаж болохгүй! (Ноорог төлөвт оруулна уу))!!!'))
		else:
			self.food_safety_ids.unlink()
			self.clean_ids.unlink()

	def action_to_download(self):
		safety_obj = self.env['hse.food.safety']
		clean_obj = self.env['hse.food.clean']
		obj = self.env['food.hygiene.conf']
		safetys = obj.sudo().search([('type','=','season_evalution'),('sub_categ','=','food_safety')])
		cleans = obj.sudo().search([('type','=','season_evalution'),('sub_categ','=','clean')])
		if safetys:
			for item in safetys:
				vals = {
					'evaluation_id': self.id,
					'name': item.name,
					'evaluation': 0,
				}
				safety_obj.create(vals)
		
		if cleans:
			for item in cleans:
				vals = {
					'evaluation_id': self.id,
					'name': item.name,
					'evaluation': 0,
				}
				clean_obj.create(vals)

class HseFoodSafety(models.Model):
	_name ='hse.food.safety'
	_description = 'food safety'
   
	evaluation_id = fields.Many2one('hse.food.season.evaluation', string='Evaluation ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')
	review = fields.Char(string='Тайлбар')

class HseFoodInternalContracl(models.Model):
	_name ='hse.food.internal.contral'
	_description = 'food internal contral'
   
	inspection_id = fields.Many2one('hse.food.hygiene.inspection', string='Inspection ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')
	review = fields.Char(string='Тайлбар')

class HseFoodRawMaterials(models.Model):
	_name ='hse.food.raw.materials'
	_description = 'food raw materials'
   
	inspection_id = fields.Many2one('hse.food.hygiene.inspection', string='Inspection ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')
	review = fields.Char(string='Тайлбар')

class HseFoodProcessing(models.Model):
	_name ='hse.food.processing'
	_description = 'food processing'
   
	inspection_id = fields.Many2one('hse.food.hygiene.inspection', string='Inspection ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')
	review = fields.Char(string='Тайлбар')

class HseFoodClean(models.Model):
	_name ='hse.food.clean'
	_description = 'food clean'
   
	inspection_id = fields.Many2one('hse.food.hygiene.inspection', string='Inspection ID', index=True)
	evaluation_id = fields.Many2one('hse.food.season.evaluation', string='Evaluation ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')
	review = fields.Char(string='Тайлбар')

class HseFoodHygieneConf(models.Model):
	_name ='food.hygiene.conf'
	_description = 'Food Hygiene Conf'
   
	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
     	('workplace_inspection', 'Ажлын байрны үзлэг'), 
		('season_evalution', 'Улиралын үнэлгээ')
	], string='Төлөв')

	sub_categ = fields.Selection([
		('food_safety', 'Хүнсний аюулгүй байдал'),
		('internal_control', 'Дотоод хяналт'),
		('material', 'Түүхий эд материал'),
		('processing', 'Боловсруулалт'),
		('clean', 'Цэвэрлэгээ'),
	], string='Дэд ангилал')