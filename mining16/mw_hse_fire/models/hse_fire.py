from email.policy import default
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class hse_fire(models.Model):
	_name ='hse.fire'
	_description = 'hse fire'
	_inherit = ["mail.thread", "mail.activity.mixin"]


	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.fire')
   
	name = fields.Char(string='Гал түймрийн дугаар', default=_default_name, copy=False, readonly=True)
	date = fields.Datetime(string='Гал түймэр гарсан огноо', default=datetime.now(), tracking=True,  readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Гал түймэр гарсан байршил',  readonly=True, states={'draft':[('readonly',False)]})
	affected_equipment_materials = fields.Char(string='Шатлагад өртсөн техник, эд материал',  readonly=True, states={'draft':[('readonly',False)]})
	hours_worked = fields.Float(string='Ажилласан цаг', readonly=True, states={'draft':[('readonly',False)]})
	water_consumed = fields.Float(string='Зарцуулсан ус(м3)', readonly=True, states={'draft':[('readonly',False)]})
	call_type_id = fields.Many2one('call.type', string='Дуудлагын төрөл', required=True, readonly=True, states={'draft':[('readonly',False)]})
	saved_people = fields.Integer(string='Аварсан хүн', default=0, readonly=True, states={'draft':[('readonly',False)]})
	saved_material = fields.Float(string='Эд материал, сая/төг', readonly=True, states={'draft':[('readonly',False)]})
	damage_died = fields.Integer('Нас барсан', default=0, readonly=True, states={'draft':[('readonly',False)]})
	damage_injured = fields.Char('Гэмтэж бэртсэн', readonly=True, states={'draft':[('readonly',False)]})
	damage_material = fields.Float('Эд материал, сая/төг', readonly=True, states={'draft':[('readonly',False)]})
	fire_extinguisher_ids = fields.One2many('fire.extinguisher.consumed', 'fire_id', string='Зарцуулсан гал унтраагуур', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Галын тохиолдлын тайлан', readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: self.env.user.company_id)
	employee_id = fields.Many2one('hr.employee', string="Бүртгэл хийсэн ажилтан", default=lambda self: self.env.user.id, readonly=True, states={'draft':[('readonly',False)]})
	state = fields.Selection([
     	('draft', 'Ноорог'), 
		('done', 'Батлагдсан')], 
    string='Төлөв', readonly=True, default='draft', tracking=True)
	review = fields.Text(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})
	
	def unlink(self):
		if self.state == 'done':
			raise UserError(_('Батлагдсан төлөвтэй тул устгаж болохгүй! (Ноорог төлөвт оруулна уу))!!!'))
		return super(hse_fire, self).unlink()


	def action_draft(self):
		self.write({'state': 'draft'})

	def action_done(self):
		self.write({'state': 'done'})


class fire_extinguisher_consumed(models.Model):
	_name ='fire.extinguisher.consumed'
	_description = 'fire extinguisher consumed'
   
	switch_id = fields.Many2one('fire.switch', string='Гал унтраагуур')
	quantity = fields.Float(string="Тоо хэмжээ", )
	fire_id = fields.Many2one('hse.fire', string='Fire ID', )

class call_type(models.Model):
	_name ='call.type'
	_description = 'patient type'
   
	name = fields.Char(string='Нэр', required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
 
	# @api.model
	# def name_search(self, name, args=None, operator='ilike', limit=100):
	# 	if args is None:
	# 		args = []
	# 	recs = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
	# 	return recs.name_get()
 
class fire_switch(models.Model):
	_name ='fire.switch'
	_description = 'fire switch'
   
	name = fields.Char(string='Нэр')
	size = fields.Char(string='Хэмжээ')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if args is None:
			args = []
		recs = self.search(['|', ('name', operator, name), ('size', operator, name)] + args, limit=limit)
		return recs.name_get()

	def name_get(self):
		res = []
		for item in self:
			name = item.name or ''
			if item.name:
				name = ('[%s] %s')%(item.name, item.size)
			# elif item.size:
				# name = ('%s')%(item.name)
				
			res.append((item.id, name))
		return res