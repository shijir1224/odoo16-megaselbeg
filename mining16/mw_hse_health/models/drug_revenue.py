from urllib.parse import uses_fragment
from odoo import  api, fields, models, _
from datetime import datetime, timedelta

class HseDrugRevenue(models.Model):
	_name ='hse.drug.revenue'
	_description = 'Health drug revenue'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_rec_name='number'
   
	number = fields.Char(string='Дугаар', required=True)
	employee_id = fields.Many2one('hr.employee', string='Хүлээн авсан ажилтан', required=True)
	date = fields.Date(string='Хүлээн авсан огноо', )
	
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал')
	user_company_id = fields.Many2one('res.company', string=u'Өөрийн компани', readonly=True, default=lambda self: self.env.user.company_id)
	company_id = fields.Many2one('res.company', string='Компани')
	line_ids = fields.One2many('hse.drug.revenue.line', 'drug_id', string="Мөр", )
	state = fields.Selection([
		('draft', 'Ноорог'),
		('revenued', 'Орлого авсан')
	], 'Төлөв', copy=False, default='draft', required=True)
 
	def action_revenued(self):
		self.write({'state':'revenued'})


class HseDrugRevenue_line(models.Model):
	_name ='hse.drug.revenue.line'
	_description = 'hse drug revenue line'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Many2one('drug.registration', string='Нэр')
	drug_id = fields.Many2one('hse.drug.revenue', string='Parent ID')
	balance = fields.Float(string="Үлдэгдэл") 
	income_count = fields.Float(string='Орлого тоо хэмжээ',)
	uom_id = fields.Many2one(related='name.uom_id', string='Хэмжих нэгж',)

	@api.onchange('name')
	def _onch_drug_balance(self):
		drug_revenue = sum(self.env['hse.drug.revenue.line'].search([('name','=',self.name.id)]).mapped('income_count'))
		drug_expenditure =sum(self.env['hse.drug.expenditure.line'].search([('name','=',self.name.id)]).mapped('expenditure_count'))
		if drug_revenue!=0 and drug_expenditure!=0:
			self.balance = drug_revenue - self.drug_expenditure - self.expenditure_count
		elif drug_revenue!=0 and drug_expenditure==0:
			self.balance = drug_revenue - self.expenditure_count
		else:
			self.balance = 0

class hse_drug_expenditure(models.Model):
	_name ='hse.drug.expenditure'
	_description = 'Health drug expenditure'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_rec_name = 'number'
   
	number = fields.Char(string='Дугаар', required=True)
	employee_id = fields.Many2one('hr.employee', string='Зарлага гаргасан ажилтан', required=True)
	date = fields.Date(string='Зарлага гаргасан огноо', )
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал')
	company_id = fields.Many2one('res.company', string='Компани')
	line_ids = fields.One2many('hse.drug.expenditure.line', 'drug_id', string="Мөр", )
	state = fields.Selection([
		('draft', 'Ноорог'),
		('expenditured', 'Зарлага гарсан')
		], 'Төлөв', copy=False, default='draft', required=True)

	def action_expenditured(self):
		self.write({'state':'expenditured'})

class HseDrugExpenditureLine(models.Model):
	_name ='hse.drug.expenditure.line'
	_description = 'hse drug expenditure line'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Many2one('drug.registration', string='Эм')
	drug_id = fields.Many2one('hse.drug.expenditure', string='Parent ID')
	expenditure_detail_id = fields.Many2one('drug.expenditure.detail', string='Амбулаторын эмийн зарлага', ondelete='cascade', index=True)
	# employee_id = fields.Many2one(related='ambulance_line_id.employee_id', string='Ажилтан', store=True)
	balance = fields.Float(string="Үлдэгдэл", readonly=True)
	expenditure_count = fields.Float(string='Зарлага тоо хэмжээ')
	uom_id = fields.Many2one(related='name.uom_id', string='Хэмжих нэгж', readonly=True)


	@api.onchange('name')
	def _onch_drug_balance(self):
		drug_revenue = sum(self.env['hse.drug.revenue.line'].search([('name','=',self.name.id)]).mapped('income_count'))
		drug_expenditure =sum(self.env['hse.drug.expenditure.line'].search([('name','=',self.name.id)]).mapped('expenditure_count'))
		if drug_revenue!=0 and drug_expenditure!=0:
			self.balance = drug_revenue - drug_expenditure - self.expenditure_count
		elif drug_revenue!=0 and drug_expenditure==0:
			self.balance = drug_revenue - self.expenditure_count
		else:
			self.balance = 0

class DrugRegistration(models.Model):
	_name ='drug.registration'
	_description = 'drug registration'

	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Эмийн нэр давхардаж болохгүй!')
	]

	name = fields.Char(string='Эмийн нэр')
	uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж',)
	balance = fields.Float(string="Үлдэгдэл", readonly=True, compute='_compute_balance', store=True)


	# @api.onchange('name')
	# def _compute_balance(self):
	# 	drug_revenue = sum(self.env['hse.drug.revenue.line'].search([('name','=',self.id)]).mapped('income_count'))
	# 	drug_expenditure =sum(self.env['hse.drug.expenditure.line'].search([('name','=',self.id)]).mapped('expenditure_count'))
	# 	if drug_revenue!=0 and drug_expenditure!=0:
	# 		self.balance = drug_revenue - self.drug_expenditure
	# 	elif drug_revenue!=0 and drug_expenditure==0:
	# 		self.balance = drug_revenue
	# 	else:
	# 		self.balance = 0