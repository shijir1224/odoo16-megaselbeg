from odoo import  api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class hse_fire_lily(models.Model):
	_name ='hse.fire.lily'
	_description = 'hse fire lily'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	name = fields.Many2one('fire.lily.number', string='Сарааны дугаар', copy=False, tracking=True, required=True)
	location_id = fields.Many2one('hse.location', string='Байршил', tracking=True, required=True)
	company_id = fields.Many2one('res.company', string='Компани', tracking=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True, default=lambda self: self.env.user.branch_id)
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	employee_id = fields.Many2one('hr.employee', string="Бүртгэл хийсэн ажилтан", required=True)
	date = fields.Datetime(string='Тодотгосон огноо', default=datetime.now(), tracking=True, required=True)
	quantity = fields.Float(string="Сарааны тоо",)
	line_ids = fields.One2many('hse.fire.lily.line', 'lily_id', string='Сарааны бүртгэл')
	attachment_ids = fields.Many2many('ir.attachment', 'hse_fire_lily_ir_attachments_rel', 'lily_id', 'attachment_id', string=u'Сарааны зураг')

	def unlink(self):
		if self.line_ids:
			raise UserError(_('Мөрөнд бүртгэл байгаа тул устгаж болохгүй!!!!'))
		return super(hse_fire_lily, self).unlink()

class hse_fire_lily_line(models.Model):
	_name ='hse.fire.lily.line'
	_description = 'fire lily line'
   
	lily_id = fields.Many2one('hse.fire.lily', string='LiLy ID')
	name = fields.Char(string='Багаж хэрэгсэл')
	quantity = fields.Float(string="Тоо хэмжээ")

class fire_lily_number(models.Model):
	_name ='fire.lily.number'
	_description = 'fire lily number'
   
	name = fields.Char(string='Сарааны дугаар', required=True)
	quantity = fields.Float(string="Тоо хэмжээ")
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)