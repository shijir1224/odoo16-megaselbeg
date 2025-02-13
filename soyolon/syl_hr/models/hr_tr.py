# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.mw_base.verbose_format import verbose_format


class HrTr(models.Model):
	_inherit = 'hr.tr'

	company = fields.Char('Хаана')
	salary = fields.Char('Цалингийн зэрэг')
	salary_amount = fields.Float('Цалин')
	salary_skills_amount = fields.Float(' Ур чадварын нэмэгдэл')
	salary_sum = fields.Float(
		'Нийт цалин', compute='_compute_salary',store=True)
	salary_ch = fields.Char(
		'Нийт цалин /хэвлэх/', compute='_print_wage')
	salary_str = fields.Char('Цалин /үсгээр/', compute='_amount_salary_str')
	level_id = fields.Many2one('salary.level', string='Цалингийн шатлал')
	year_ch = fields.Char('year ch')
	month_ch = fields.Char('Month ch')
	day_ch = fields.Char('Day ch')
	
	@api.onchange('employee_id')
	def onchange_engagement_date(self):
		if self.employee_id:
			self.year_ch = str(self.employee_id.engagement_in_company)[:4]
			self.month_ch = str(self.employee_id.engagement_in_company).split('-')[1]
			self.day_ch = str(self.employee_id.engagement_in_company).split('-')[2]


	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			contract_id = self.env['hr.contract'].search(
				[('employee_id', '=', self.employee_id.id)], limit=1)
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id
			self.salary_amount = contract_id.level_id.amount
			self.engagement_date = self.employee_id.engagement_in_company
			self.salary = self.job_id.job_degree
			self.level_id = contract_id.level_id.id

	@api.depends('salary_sum')
	def _amount_salary_str(self):
		for line in self:
			if line.salary_sum:
				line.salary_str = verbose_format(abs(line.salary_sum))
			else:
				line.salary_str = ''

	@api.depends('salary_sum')
	def _print_wage(self):
		for line in self:
			if line.salary_sum:
				self.salary_ch = '{0:,.2f}'.format(
					line.salary_sum).split('.')[0]
			else:
				line.salary_ch = ''

	@api.depends('salary_amount', 'salary_skills_amount')
	def _compute_salary(self):
		for item in self:
			if item.salary_amount:
				item.salary_sum = (item.salary_amount * 168)//100000 * 100000
			else:
				item.salary_sum = 0
