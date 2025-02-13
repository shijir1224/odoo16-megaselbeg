# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class  HrDepartment(models.Model):
	_inherit = "hr.department"

	planned_employees = fields.Integer('Батлагдсан тоо')
	vacancies = fields.Integer('Захиалгат тоо',compute='_compute_applicant_employee_count',store=True)
	registered_employees = fields.Integer('Бүртгэлтэй ажилчдын тоо')
	working_employee_count = fields.Integer(compute='_compute_working_employee_count', string='Одоо ажиллаж буй',store=True)
	basic_employees = fields.Integer(compute='_compute_basic_employees', string='Үндсэн',store=True)
	trial_employees = fields.Integer(compute='_compute_trial_employees', string='Туршилтын',store=True)
	trainee_employees = fields.Integer('Дагалдан')
	maternity_employees = fields.Integer(compute='_compute_maternity_employees', string='Эхчүүд',store=True)
	annual_leave_employees = fields.Integer(compute='_compute_annual_leave_employees', string='Чөлөөтэй',store=True)
	resigned_employees = fields.Integer(compute='_compute_resigned_employees', string='Ажлаас гарсан',store=True)
	contract_workers = fields.Integer(compute='_compute_contract_workers', string='Гэрээт',store=True)
	job_ids = fields.One2many('hr.job', 'department_id','Ажлын байрууд')
	
	def _compute_total_employee(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', '!=', 'resigned')], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.total_employee = result.get(department.id, 0)
			
	def _compute_applicant_employee_count(self):
		current_year = fields.Date.today().year
		# Query to get applicant data grouped by request_department_id
		applicant_data = self.env['hr.applicant.request']._read_group(
			[('request_department_id', 'in', self.ids), ('state_type', '=', 'done'), 
			('create_date', '>=', f'{current_year}-01-01'), ('create_date', '<=', f'{current_year}-12-31')],
			['request_department_id', 'employee_count'],  # Include employee_count in the fields
			['request_department_id']  # Group by request_department_id
		)

		# Create a dictionary where the key is department ID and the value is employee count
		result = {data['request_department_id'][0]: data['employee_count'] for data in applicant_data}

		# Assign the vacancies count to each department
		for department in self:
			department.vacancies = result.get(department.id, 0)


	def _compute_working_employee_count(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),
			('employee_type', 'in', ('employee','student','contractor','trainee'))], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.working_employee_count = result.get(department.id, 0)

	def _compute_basic_employees(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', '=', 'employee')], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.basic_employees = result.get(department.id, 0)

	def _compute_trial_employees(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', '=', 'trainee')], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.trial_employees = result.get(department.id, 0)

	def _compute_maternity_employees(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', 'in', ('pregnant_leave','maternity'))], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.maternity_employees = result.get(department.id, 0)

	def _compute_annual_leave_employees(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', '=', 'longleave')], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.annual_leave_employees = result.get(department.id, 0)
	
	def _compute_resigned_employees(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', '=', 'resigned')], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.resigned_employees = result.get(department.id, 0)

	def _compute_contract_workers(self):
		emp_data = self.env['hr.employee']._read_group([('department_id', 'in', self.ids),('employee_type', '=', 'contractor')], ['department_id'], ['department_id'])
		result = dict((data['department_id'][0], data['department_id_count']) for data in emp_data)
		for department in self:
			department.contract_workers = result.get(department.id, 0)

class  HrJob(models.Model):
	_inherit = "hr.job"

	planned_employees = fields.Integer('Батлагдсан тоо')
	vacancies = fields.Integer('Захиалгат тоо', compute='_compute_applicant_employee_count',store=True)
	registered_employees = fields.Integer('Бүртгэлтэй ажилчдын тоо')
	total_employee = fields.Integer('Бүтргэлтэй ажилчдын тоо')
	working_employee_count = fields.Integer('Одоо ажиллаж буй')
	basic_employees = fields.Integer('Үндсэн',compute='_compute_employees',store=True)
	trial_employees = fields.Integer('Туршилтын',compute='_compute_employees',store=True)
	trainee_employees = fields.Integer('Дагалдан')
	maternity_employees = fields.Integer('Эхчүүд',compute='_compute_employees',store=True)
	annual_leave_employees = fields.Integer('Чөлөөтэй',compute='_compute_employees',store=True)
	contract_workers = fields.Integer('Гэрээт',compute='_compute_employees',store=True)
	resigned_employees = fields.Integer(compute='_compute_employees', string='Ажлаас гарсан',store=True)

	@api.depends('no_of_recruitment', 'employee_ids.job_id', 'employee_ids.active','employee_ids.employee_type')
	def _compute_employees(self):
		employee_data = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', 'in', ('employee','student','contractor','trainee'))], ['job_id'], ['job_id'])
		result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
		
		total_employee_data = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', '!=', 'resigned')], ['job_id'], ['job_id'])
		result2 = dict((total['job_id'][0], total['job_id_count']) for total in total_employee_data)
		
		basic_employee = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', '=', 'employee')], ['job_id'], ['job_id'])
		result3 = dict((basic['job_id'][0], basic['job_id_count']) for basic in basic_employee)
		
		trial_employee = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', '=', 'trainee')], ['job_id'], ['job_id'])
		result4 = dict((trial['job_id'][0], trial['job_id_count']) for trial in trial_employee)
		
		contract_employee = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', '=', 'contractor')], ['job_id'], ['job_id'])
		result5 = dict((contract['job_id'][0], contract['job_id_count']) for contract in contract_employee)
		
		longleave_employee = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', '=', 'longleave')], ['job_id'], ['job_id'])
		result6 = dict((longleave['job_id'][0], longleave['job_id_count']) for longleave in longleave_employee)
		
		maternity_employee = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', 'in', ('pregnant_leave','maternity'))], ['job_id'], ['job_id'])
		result7 = dict((maternity['job_id'][0], maternity['job_id_count']) for maternity in maternity_employee)
		
		resigned_employee = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', '=', 'resigned')], ['job_id'], ['job_id'])
		result8 = dict((resigned['job_id'][0], resigned['job_id_count']) for resigned in resigned_employee)
		
		for job in self:
			job.no_of_employee = result.get(job.id, 0)
			job.expected_employees = result2.get(job.id, 0)
			job.basic_employees = result3.get(job.id, 0)
			job.trial_employees = result4.get(job.id, 0)
			job.contract_workers = result5.get(job.id, 0)
			job.maternity_employees = result7.get(job.id, 0)
			job.annual_leave_employees = result6.get(job.id, 0)
			job.resigned_employees = result8.get(job.id, 0)
			
	
	def _compute_applicant_employee_count(self):
		current_year = fields.Date.today().year
		applicant_data = self.env['hr.applicant.request']._read_group(
			[('job_id', 'in', self.ids), ('state_type', '=', 'done'), 
			('create_date', '>=', f'{current_year}-01-01'), ('create_date', '<=', f'{current_year}-12-31')],
			['job_id', 'employee_count'],  # Include employee_count in the fields
			['job_id']  # Group by request_department_id
		)
		result = {data['job_id'][0]: data['employee_count'] for data in applicant_data}
		for job in self:
			job.vacancies = result.get(job.id, 0)
class  HrOrgStructure(models.Model):
	_name = "hr.org.structure"
	_description = "Organization Structure"
	_inherit = ['mail.thread']

	name = fields.Char('Нэр', states={'confirmed': [('readonly', True)]})
	year = fields.Char('Жил', states={'confirmed': [('readonly', True)]})
	state = fields.Selection([('draft','Ноорог'),
				('confirmed','Батлагдсан')],default='draft')
	company_id = fields.Many2one('res.company', 'Компани', states={'confirmed': [('readonly', True)]})
	description = fields.Text('Тайлбар')
	line_ids = fields.One2many('hr.org.structure.dep.line','struct_id', 'Lines')
	sum_count = fields.Integer('Төлөвлөгдсөн тоо хэмжээ', readonly=True, store=True, compute='_compute_sum_count')

	@api.depends('line_ids.dep_count')
	def _compute_sum_count(self):
		sum_count = 0
		for l in self.line_ids:
			sum_count+=l.dep_count
		self.sum_count=sum_count

	def confirm_action(self):
		for l in self.line_ids:
			dep_id = self.env['hr.department'].search([('id','=',l.department_id.id)])
			dep_id.update({'planned_employees': l.dep_count})
			for ll in l.line_line_ids:
				job_id = self.env['hr.job'].search([('id','=',ll.job_id.id)])
				job_id.update({'no_of_recruitment': ll.job_count})
				job_id.update({'planned_employees': ll.job_count})

		return self.write({'state': 'confirmed'})

	def action_draft(self):
		return self.write({'state': 'draft'})

	def action_copy(self):
		org_pool = self.env['hr.org.structure']
		org_line_pool = self.env['hr.org.structure.dep.line']
		org_position_pool = self.env['hr.org.structure.position.line']
		for obj in self:
			org_id = org_pool.create({
				'name': obj.name,
				'year': obj.year,
				'company_id': obj.company_id.id,
				'description': obj.description,
				'state': 'draft',
			})
			line_obj=org_pool.browse(org_id)
			for lo in line_obj:
				for l in obj.line_ids:
					org_line_id = org_line_pool.create({
						'department_id': l.department_id.id,
						'struct_id': lo.id.id,
						'state': 'draft',
					})
				line_line_obj=org_line_pool.browse(org_line_id)
				for llo in line_line_obj:
					for ll in l.line_line_ids:
						org_positione_id = org_position_pool.create({
							'job_id': ll.job_id.id,
							'struct_dep_id': llo.id.id,
							'state': 'draft',
							})

class  HrOrgStructureDepLine(models.Model):
	_name = "hr.org.structure.dep.line"
	_description = "Organization Structure Dep Line"

	department_id = fields.Many2one('hr.department','Газар, нэгж')
	struct_id = fields.Many2one('hr.org.structure', string='Organization Structure')
	line_line_ids = fields.One2many('hr.org.structure.position.line','struct_dep_id','lines')
	state = fields.Selection([('draft','Draft'),
				('confirmed','Confirmed')],default='draft')

	dep_count = fields.Integer('Төлөвлөгдсөн тоо хэмжээ', readonly=True, compute='_compute_dep_count')

	@api.depends('line_line_ids','line_line_ids.job_count')
	def _compute_dep_count(self):
		for obj in self:
			dep_count = 0
			for line in obj.line_line_ids:
				dep_count += line.job_count
			obj.update({"dep_count": dep_count,})
		# for obj in self:
		# dep_count = 0
		# for ll in self.line_line_ids:
		# 	dep_count+=ll.job_count
		# self.dep_count=dep_count

class  HrOrgStructurePositionLine(models.Model):
	_name = "hr.org.structure.position.line"
	_description = "Organization Structure position Line"

		
	job_id = fields.Many2one('hr.job','Албан тушаал')
	avail_job_ids = fields.Many2many('hr.job','Албан тушаал', compute='get_job_id_domain')
	department_id = fields.Many2one('hr.department','Газар, нэгж',related ='job_id.department_id',store = True)

	job_count = fields.Integer('Төлөвлөгдсөн тоо хэмжээ')
	struct_dep_id = fields.Many2one('hr.org.structure.dep.line', string='Organization Structure')
	state = fields.Selection([('draft','Draft'),
				('confirmed','Confirmed')],default='draft')

	@api.depends('struct_dep_id.department_id')
	def get_job_id_domain(self):
		for item in self:
			if item.struct_dep_id.department_id:
				item.avail_job_ids = item.env['hr.job'].search([('department_id', '=', item.struct_dep_id.department_id.id)]).ids
			else:
				item.avail_job_ids = False


