from odoo import  api, fields, models, _
from datetime import datetime, timedelta


class HseSalaryKpi(models.Model):
	_name ='hse.salary.kpi'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Hse Salary Kpi'

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.salary.kpi')

	name = fields.Char(string='Дугаар', copy=False, default=_default_name, readonly=True)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True, default=lambda self: self.env.user.branch_id)
	company_id = fields.Many2one('res.company', string="Компани", readonly=True, required=True, default=lambda self: self.env.user.company_id)
	salary_kpi_line = fields.One2many('hse.salary.kpi.line', 'kpi_id', ' Salary kpi line', readonly=True)
	start_date = fields.Date('Эхлэх огноо', default=fields.Date.context_today, tracking=True, required=True)
	end_date = fields.Date('Дуусах огноо', default=fields.Date.context_today, tracking=True, required=True)
	employee_id = fields.Many2one(related='salary_kpi_line.employee_id', string='Ажилтан')


	def action_to_done(self):
		self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})	

	def action_to_download(self):
		salary_kpi_line =  self.env['hse.salary.kpi.line']
		if self.salary_kpi_line:
			self.salary_kpi_line.unlink()

		emp_obj = self.env['hr.employee'].search([('employee_type','in',['employee','student'])])
		k=0
		l=0
		for ajiltan in emp_obj:
			conflict_pool = self.env['hse.discipline.action'].search([('employee_id','=',ajiltan.id)])
			if conflict_pool:
				k += 30
			inspection_pool = self.env['hse.hazard.report'].search([('responsible','=',ajiltan.id)])
			if inspection_pool:
				l += 10
			line_line_conf = salary_kpi_line.create({
							'kpi_id': self.id,
							# 'date': from_dt,	
							'employee_id': ajiltan.id,
							'department_id': ajiltan.department_id.id,
							'job_id': ajiltan.job_id.id,
							'emp_hse_point':ajiltan.job_id.employee_hse_point+l-k
						})
			k = 0
			l = 0

	def view_line_line(self):
		action = self.env.ref('mw_hse.action_hse_salary_kpi_line')
		vals = action.read()[0]
		vals['context'] = {}
		vals['domain'] = [('kpi_id','=',self.id)]
		return vals			

class HseSalaryKpi(models.Model):
	_name ='hse.salary.kpi.line'
	_description = 'Hse Salary Kpi line'

	kpi_id = fields.Many2one('hse.salary.kpi', string="ХАБ Үнэлгээ дугаар", ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string="Ажилтан")
	
	department_id = fields.Many2one('hr.department', 'Хэсэг')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	date = fields.Date('Өдөр', default=fields.Date.context_today)
	emp_hse_point = fields.Float('Ажилчдын ХАБ оноо')
	company_id = fields.Many2one(related='kpi_id.company_id', string='Компани', readonly=True, store=True)
	branch_id = fields.Many2one(related='kpi_id.branch_id', string='Салбар', readonly=True, store=True)

class HrJob(models.Model):
	_inherit ='hr.job'

	employee_hse_point = fields.Float(string='Ажилтны хувь')