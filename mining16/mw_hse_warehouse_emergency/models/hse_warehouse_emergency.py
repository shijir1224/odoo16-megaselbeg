from urllib.parse import uses_fragment
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning


class hse_warehouse_emergency(models.Model):
	_name ='hse.warehouse.emergency'
	_description = 'Hse warehouse.emergency'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Char(string='Агуулахын нэр')
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True)
	product_id = fields.Many2one('hse.product', string='Бараа')
	balance = fields.Integer(string="Үлдэгдэл", compute='_compute_balance', store=True)
	company_id = fields.Many2one('res.company', string='Компани')
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж',)
	total_income = fields.Float(string='Нийт орлого', compute='_compute_total_income', store=True)
	total_expenditure = fields.Float(string='Нийт зарлага', compute='_compute_total_expenditure', store=True)
	expenditure_ids = fields.One2many('hse.warehouse.expenditure.line', 'parent_id', string='Зарлага бүртгэл')
	income_ids = fields.One2many('hse.warehouse.income.line', 'parent_id', string='Орлого бүртгэл')
	# type = fields.Selection([
	# 	('emergency','Онцгой байдал'),
	# 	('health','Эрүүл мэнд')], string='Барааны төрөл')	


	def unlink(self):
		if self.income_ids or self.expenditure_ids:
			raise UserError(_('Орлого зарлагын мэдээлэлтэй байгаа тул устгаж болохгүй!!!'))
		return super(hse_warehouse_emergency, self).unlink()
	
 
	@api.depends('total_income','total_expenditure')
	def _compute_balance(self):
		for item in self:
			if item.total_income:
				item.balance = item.total_income - item.total_expenditure
			else:
				item.balance = 0
    

	@api.depends('income_ids.income_amount')
	def _compute_total_income(self):
		for item in self:
			if item.income_ids:
				item.total_income = sum(item.income_ids.mapped('income_amount'))
			else:
				item.total_income = 0
    
	@api.depends('expenditure_ids.expenditure_amount')
	def _compute_total_expenditure(self):
		for item in self:
			if item.expenditure_ids:
				item.total_expenditure = sum(item.expenditure_ids.mapped('expenditure_amount'))
			else:
				item.total_expenditure = 0


class hse_warehouse_expenditure_line(models.Model):
	_name ='hse.warehouse.expenditure.line'
	_description = 'hse warehouse expenditure line'

	parent_id = fields.Many2one('hse.warehouse.emergency', string='Parent ID', ondelete="cascade",)
	date = fields.Date(string='Өдөр',)
	expenditure_amount = fields.Integer('Зарлага хийсэн хэмжээ')
	uom_id = fields.Many2one(related='parent_id.uom_id', string='Хэмжих нэгж',)
	location_id = fields.Many2one('res.branch', string="Байршил", )
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	review = fields.Text(string='Тайлбар', )
	warehouse_name = fields.Char(related='parent_id.name', string='Агуулахын нэр', store=True)
	product_id = fields.Many2one('hse.product', related='parent_id.product_id', string='Бараа', store=True)
	balance = fields.Integer(related='parent_id.balance', string="Үлдэгдэл", store=True)
	company_id = fields.Many2one('res.company', related='parent_id.company_id', string='Компани', store=True)

class hse_warehouse_income_line(models.Model):
	_name ='hse.warehouse.income.line'
	_description = 'hse warehouse income line'

	parent_id = fields.Many2one('hse.warehouse.emergency', string='Parent ID', ondelete="cascade")
	date = fields.Date(string='Өдөр',)
	income_amount = fields.Integer('Орлого хийсэн хэмжээ')
	uom_id = fields.Many2one(related='parent_id.uom_id', string='Хэмжих нэгж',)
	location_id = fields.Many2one('res.branch', string="Байршил", )
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	review = fields.Text(string='Тайлбар', )
	warehouse_name = fields.Char(related='parent_id.name', string='Агуулахын нэр', store=True)
	product_id = fields.Many2one('hse.product', related='parent_id.product_id', string='Бараа', store=True)
	balance = fields.Integer(related='parent_id.balance', string="Үлдэгдэл", store=True)
	company_id = fields.Many2one('res.company', related='parent_id.company_id', string='Компани', store=True)