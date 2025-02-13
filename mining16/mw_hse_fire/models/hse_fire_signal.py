from email.policy import default
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

class hse_fire_signal_system(models.Model):
	_name = 'hse.fire.signal.system'
	_description = 'Hse fire signal system'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	name = fields.Many2one('camp.register', string='Объектын нэр', required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	state = fields.Selection([
		('draft', 'Ноорог'),
		('done', 'Батлагдсан')
	], 'Төлөв', readonly=True, tracking=True, default='draft')
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True, default=lambda self: self.env.user.branch_id, readonly=True, states={'draft':[('readonly',False)]})
	fire_extinguisher_signal_ids = fields.One2many('fire.extinguisher.signal', 'signal_id', string='Гал унтраагуур', readonly=True, states={'draft':[('readonly',False)]})
	signal_system_ids = fields.One2many('signal.system.line', 'parent_id', string='Дохиолллын систем', readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string='Компани', required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	check_employee_id = fields.Many2one('hr.employee', string="Бүртгэл хийсэн ажилтан", required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	employee_ids = fields.Many2many('hr.employee', 'employee_attachment_id', 'employee_id', string="Бүртгэл хийсэн ажилтан", required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	desc = fields.Text('Тайлбар')

	def action_to_done(self):
		for item in self:
			item.write({'state': 'done'})
			item.check_employee_id = item.env.user.employee_id.id

	def action_to_draft(self):
		for item in self:
			item.write({'state': 'draft'})
			item.check_employee_id = False

class camp_register(models.Model):
	_name ='camp.register'
	_description = 'camp register'
   
	name = fields.Char(string='Нэр')
	number = fields.Char(string='Дугаар',required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if args is None:
			args = []
		recs = self.search(['|', ('name', operator, name), ('number', operator, name)] + args, limit=limit)
		return recs.name_get()

class fire_extinguisher_signal(models.Model): 
	_name ='fire.extinguisher.signal'
	_description = 'fire extinguisher signal'

	signal_id = fields.Many2one('hse.fire.signal.system', string='Signal ID', )
	switch_id = fields.Many2one('fire.switch', string='Гал унтраагуур')
	switch_where_type = fields.Selection([
		('switch_technic', 'Техник'),
		('switch_place', 'Байршил'),
		], string='Төрөл сонгох',)
	place = fields.Char(string="Байршил", )
	technic_id = fields.Many2one('technic.equipment',string="Техник", )
	quantity = fields.Float(string="Тоо хэмжээ", )
	
class signal_system_line(models.Model):
	_name ='signal.system.line'
	_description = 'signal system line'

	signal_id = fields.Many2one('signal.system', string='Дохиололын мэдээлэл')
	place = fields.Char(string="Байршил", )
	quantity = fields.Float(string="Тоо хэмжээ", default=0)
	parent_id = fields.Many2one('hse.fire.signal.system', string='Signal ID', )

class signal_system(models.Model):
	_name ='signal.system'
	_description = 'signal system'

	name = fields.Char(string='Марк')
	serial = fields.Char(string='Сери дугаар')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)