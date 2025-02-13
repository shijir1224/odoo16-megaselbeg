#  -*- coding: utf-8 -*-
from odoo import fields, models, api ,_
from  datetime import date
from odoo.exceptions import UserError



class HrEvaluationPlan(models.Model):
	_name = "hr.evaluation.plan"
	_descrition = 'Hr Evaluation Plan'
	_inherit = ['mail.thread']


	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)


	name = fields.Char(string='Нэр')
	year = fields.Char(string='Жил')
	month = fields.Integer(string='Сар')
	department_id = fields.Many2one('hr.department',string='Хэлтэс')
	company_id = fields.Many2one('res.company',default=lambda self: self.env.user.company_id,string='Компани')
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('done','Үнэлсэн')],default='draft',string='Төлөв', tracking=True)
	line_ids = fields.One2many('hr.evaluation.plan.line','parent_id',string='')
	kpi_head = fields.Float('Төлөвлөгөөт ажлын үнэлгээний дүн удирдлага',compute='_compute_kpi',store=True, digits=(2, 0))
	kpi_head_own = fields.Float('Төлөвлөгөөт ажлын үнэлгээний дүн өөрийн',compute='_compute_kpi',store=True, digits=(2, 0))
	kpi_daily = fields.Float('Өдөр тутмын ажлын гүйцэтгэл өөрийн', digits=(2, 0),store=True,compute=False)
	kpi_daily_head = fields.Float('Өдөр тутмын ажлын гүйцэтгэл удирдлагын', digits=(2, 0))
	kpi_team = fields.Float('Багийн гүйцэтгэлийн үнэлгээний дүн',compute='_compute_kpi',store=True, digits=(2, 0))
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	employee_id =  fields.Many2one('hr.employee', 'Ажилтан',default=_default_employee)
	num_employee_id =  fields.Many2one('hr.employee', 'Удирлага')

# 
	@api.depends('line_ids','line_ids.kpi_head','line_ids.kpi','kpi_daily_head')
	def _compute_kpi(self):
		for obj in self:
			sum_amount=0
			kpi_team=0
			avj_kpi=0
			avj_own_kpi=0
			len_line = len(obj.line_ids)
			sum_amount = sum(obj.line_ids.filtered(lambda line: line.is_true==True).mapped('kpi_head'))
			sum_amount_own = sum(obj.line_ids.filtered(lambda line: line.is_true==True).mapped('kpi'))
			if sum_amount>0 and len_line>0:
				avj_kpi = sum_amount/len_line
			if sum_amount_own>0 and len_line>0:
				avj_own_kpi = sum_amount_own/len_line
			if obj.kpi_daily_head + avj_kpi > 0:
				kpi_team = (obj.kpi_daily_head +avj_kpi)/2
			obj.kpi_head = avj_kpi
			obj.kpi_head_own = avj_own_kpi
			obj.kpi_team = kpi_team

	def compute_daily(self):
		for item in self:
			if item.department_id:
				avg_amount =0
				avg_amount_own=0
				lines = self.env['hr.evaluation.line'].search([('department_id','=',item.department_id.id),('state','=','done'),('month','=',item.month),('year','=',item.year)])
				lens = len(lines)
				
				amount = sum(lines.filtered(lambda line: line.state=='done').mapped('sum_amount'))
				amount_own = sum(lines.filtered(lambda line: line.state=='done').mapped('own_score'))
				print('\n\====',lens,amount,amount_own)
				if lens>0 and amount>0:
					avg_amount = amount/lens
				if lens>0 and amount_own>0:
					avg_amount_own = amount_own/lens
				item.kpi_daily = avg_amount_own
				item.kpi_daily_head = avg_amount
	
	def line_create(self):
		if self.line_ids:
			self.line_ids.unlink()
		if self.department_id:
			line_obj = self.env['hr.evaluation.plan.line']
			records = self.env['hr.evaluation.year.plan.line.line'].search([('parent_id.department_id','=',self.department_id.id),('month','=',self.month),('parent_id.year','=',self.year)])
			for record in records:
				line_id = line_obj.create({
					'parent_id':self.id,
					'conf_kpi_id':record.conf_kpi_id.id,
					'task':record.task,
					'r_employee_ids':record.r_employee_ids.mapped('id'),
					'a_employee_ids':record.a_employee_ids.mapped('id'),
					'ts_employee_ids':record.ts_employee_ids.mapped('id'),
					's_employee_ids':record.s_employee_ids.mapped('id'),
					'i_employee_ids':record.i_employee_ids.mapped('id'),
				})
		
	def line_create_employee(self):
		emps = self.line_ids.mapped('ts_employee_ids').ids
		emp_obj = self.env['hr.evaluation.emp']
		
		line_emp_obj = self.env['hr.evaluation.emp.line']
		for emp in emps:
			emp_eval = self.env['hr.evaluation.emp'].search([('year','=',self.year),('month','=',self.month),('employee_id','=',emp)])
			if emp_eval:
				raise UserError('%s ажилтны сарын үнэлгээ үүссэн давхардаж байна' % emp_eval.employee_id.name)
			else:
				emp_id = emp_obj.create({
					'year':self.year,      
					'month': self.month,
					'department_id': self.department_id.id,
					'company_id': self.company_id.id,
					'work_location_id':self.work_location_id.id,
					'work_location_id':1,
					'create_date': date.today(),
					'employee_id':emp,
				})
				
			

			plan_line = self.env['hr.evaluation.plan.line'].search([('ts_employee_ids','in',emp),('parent_id','=',self.id)])
			for line in plan_line:
				line_emp_id = line_emp_obj.create({
					'line_parent_id':emp_id.id,
					'conf_kpi_id':line.conf_kpi_id.id,
					'task':line.task,
				})

	
	def action_send(self):
		self.write({'state':'sent'})
		
	def action_done(self):
		self.write({'state':'done'})
		
	def action_draft(self):
		self.write({'state':'draft'})
class HrEvaluationPlan(models.Model):
	_name = "hr.evaluation.plan.line"
	_descrition = 'Hr Evaluation Plan Line'

	conf_id = fields.Many2one('hr.performance',string='KPI')
	conf_kpi_id = fields.Many2one('ev.kpi.conf',string='KPI')
	task = fields.Char('Хийгдэх ажлууд')
	r_employee_ids = fields.Many2many('hr.employee','hr_temp_month_rel','hr_temp_month_id', 'employee_id',string= 'R: хянах')
	a_employee_ids = fields.Many2many('hr.employee','hr_aemp_month_rel','hr_aemp_month_id', 'employee_id',string= 'A: батлах, шийдвэрлэх')
	t_employee_ids = fields.Many2many('hr.employee','hr_temp_month_rel','hr_temp_month_id', 'employee_id',string= 'T: гүйцэтгэх, боловсруулах')
	ts_employee_ids = fields.Many2many('hr.employee','hr_ts_month_rel','hr_ts_month_id', 'employee_id',string= 'T: гүйцэтгэх, боловсруулах')
	s_employee_ids = fields.Many2many('hr.employee','hr_semp_month_rel','hr_semp_month_id', 'employee_id',string= 'S: дэмжих, зөвлөлдөх')
	i_employee_ids = fields.Many2many('hr.employee','hr_iemp_month_rel','hr_iemp_month_id', 'employee_id',string= 'I: мэдээлэлтэй байх')

	r_employee_id = fields.Many2one('hr.employee','R: хянах')
	a_employee_id = fields.Many2one('hr.employee','A: батлах, шийдвэрлэх')
	t_employee_id = fields.Many2one('hr.employee','T: гүйцэтгэх, боловсруулах')
	s_employee_id = fields.Many2one('hr.employee','S: дэмжих, зөвлөлдөх')
	i_employee_id = fields.Many2one('hr.employee','I: мэдээлэлтэй байх')
	name = fields.Char('Өөрийн тайлбар')
	kpi = fields.Float('Өөрийн үнэлгээ')
	kpi_head = fields.Float('Удирдагын үнэлгээ')
	result = fields.Char('Удирдлагын тайлбар')
	parent_id = fields.Many2one('hr.evaluation.plan',string='Parent')
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('done','Үнэлсэн')],default='draft',string='Төлөв',related='parent_id.state',store=True)
	is_true= fields.Boolean('Үнэлгээнд нөлөөлөх эсэх?',default=True)
	

# ==========
	employee_ids = fields.Many2many('hr.employee',string='Хариуцах албан тушаалтан')
	
