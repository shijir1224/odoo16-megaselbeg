from email.policy import default
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class HseFoodInspection(models.Model):
	_name ='hse.food.inspection'
	_description = 'HSE Food Inspection'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.hygiene.inspection')
   
	name = fields.Char(string='Дугаар', default=_default_name, copy=False, readonly=True)
	state = fields.Selection([
     	('draft', 'Ноорог'), 
		('done', 'Батлагдсан')], 
    string='Төлөв', readonly=True, default='draft', tracking=True)
	inspection_type = fields.Selection([
     	('Төлөвлөгөөт', 'Төлөвлөгөөт'), 
		('Хяналт', 'Хяналт')
	], string='Төлөв', readonly=True, default='draft', tracking=True)
	date = fields.Datetime(string='Огноо', default=datetime.now(), tracking=True,  readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар',  readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: self.env.user.company_id)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	user_id = fields.Many2one('res.users', string="Бүртгэл хийсэн ажилтан", default=lambda self: self.env.user.id, readonly=True, states={'draft':[('readonly',False)]})
	review = fields.Text(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})
	
	contral_ids = fields.One2many('hse.food.internal.contral', 'inspection_id', 'Дотоод хяналт')
	material_ids = fields.One2many('hse.food.raw.materials', 'inspection_id', 'Түүхий эд')
	processing_ids = fields.One2many('hse.food.processing', 'inspection_id', 'Боловсруулалт')
	clean_ids = fields.One2many('hse.food.clean', 'inspection_id', 'Цэвэрлэгээ')
	
	def unlink(self):
		if self.state == 'done':
			raise UserError(_('Батлагдсан төлөвтэй тул устгаж болохгүй! (Ноорог төлөвт оруулна уу))!!!'))
		return super(HseFoodInspection, self).unlink()

	def action_draft(self):
		self.write({'state': 'draft'})

	def action_done(self):
		self.write({'state': 'done'})


class HseFoodInternalContracl(models.Model):
	_name ='hse.food.internal.contral'
	_description = 'food internal contral'
   
	inspection_id = fields.Many2one('hse.food.inspection', string='Parent ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')


class HseFoodRawMaterials(models.Model):
	_name ='hse.food.raw.materials'
	_description = 'food raw materials'
   
	inspection_id = fields.Many2one('hse.food.inspection', string='Parent ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')

class HseFoodProcessing(models.Model):
	_name ='hse.food.processing'
	_description = 'food processing'
   
	inspection_id = fields.Many2one('hse.food.inspection', string='Parent ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')

class HseFoodClean(models.Model):
	_name ='hse.food.clean'
	_description = 'food clean'
   
	inspection_id = fields.Many2one('hse.food.inspection', string='Parent ID', index=True)
	name = fields.Char('Нэр')
	evaluation = fields.Integer(string='Үнэлгээ')


class call_type(models.Model):
	_name ='call.type'
	_description = 'patient type'
   
	name = fields.Char(string='Нэр', required=True)
	inspection_type = fields.Selection([
     	('Төлөвлөгөөт', 'Төлөвлөгөөт'), 
		('Хяналт', 'Хяналт')
	], string='Төлөв', readonly=True, default='draft', tracking=True)