# -*- coding: utf-8 -*-
from logging import Logger
from venv import logger
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"



class HrApplicantRequest(models.Model):
	_inherit = "hr.applicant.request"

	request_level = fields.Selection([('normal','Энгийн /60 хоног/'),('urgent','Яаралтай /21 хоног/'),('need','Нэн яаралтай /7 хоног/')],string='Зэрэглэл')
	company_id =  fields.Many2one('res.company','Компани',default=lambda self: self.env.user.company_id, readonly=True)
	def action_next_stage(self):
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id,'applicant_id', self)	
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id,False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
	
	def send_chat_next_users(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_applicant.action_hr_applicant_request').id
		html = u'<b>Хүний нөөцийн захиалга</b><br/><i style="color: red">%s</i> ажилтаны үүсгэсэн </br>'%(self.sudo().employee_id.name)
		html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.applicant.request&action=%s>%s</a></b> - Хүний нөөцийн захиалга хүсэлт  <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.employee_id.name,state)
		self.flow_line_id.send_chat(html, partner_ids)
			



class UtmSource(models.Model):
	_inherit = 'utm.source'	

	address = fields.Char(string='Хаяг')
	phone = fields.Char(string='Утас')

class  HrDepartment(models.Model):
	_inherit = "hr.department"

	free_position = fields.Integer('Сул орон тоо',compute='_count_employees_position',store=True)
	over_employee = fields.Integer('Илүү орон тоо',compute='_count_employees_position',store=True)

	@api.depends('working_employee_count','planned_employees')
	def _count_employees_position(self):
		for dep in self:
			if dep.working_employee_count and dep.planned_employees:
				if dep.working_employee_count > dep.planned_employees:
					dep.over_employee = dep.working_employee_count - dep.planned_employees
					dep.free_position = 0
				else:
					dep.free_position = dep.planned_employees - dep.working_employee_count
					dep.over_employee = 0
			else:
				dep.free_position = 0
				dep.over_employee = 0

class HrOpenJob(models.Model):
	_inherit = "hr.open.job"

	stage_one = fields.Integer('Анхны шалгаруулалт') 
	stage_two = fields.Integer('Эхний ярилцлага') 
	stage_three = fields.Integer('2 дахь ярилцлага') 
	done_date = fields.Date('Хангагдсан огноо')
	line_ids = fields.One2many('hr.open.job.line','parent_id',string='Мөр')
	no_of_employee = fields.Integer(string="Хангагдсан тоо",compute='_compute_lens',store=True)
	period = fields.Integer('Зарцуулсан хугацаа',compute='_compute_period',store=True)

	def daterange(self, date_from, date_to):
		for n in range(int((date_to - date_from).days)):
			yield date_from + timedelta(n)

	@api.depends('line_ids.done_date')
	def _compute_period(self):
		for i in self:
			day_too=1
			done_date=None
			if i.line_ids and i.date:
				st_d = datetime.strptime(str(i.date + timedelta(hours=8)), DATE_FORMAT).date()
				en_d = datetime.strptime(str(i.line_ids[0].done_date +timedelta(hours=8)), DATE_FORMAT).date()
				for single_date in i.daterange(st_d, en_d):
					day_too += 1 if single_date.weekday() < 5 else 0
				done_date=i.line_ids[0].done_date
			i.period=day_too
			i.done_date=done_date
			
			


	@api.depends('line_ids')
	def _compute_lens(self):
		for i in self:
			lens = len(i.line_ids)
			if lens:
				i.no_of_employee = lens
			else:
				i.no_of_employee =0


class HrOpenJobLine(models.Model):
	_name = "hr.open.job.line"
	_order ='done_date'


	done_date = fields.Date('Хангагдсан огноо',required=1)
	emp_id = fields.Many2one('hr.employee','Ажилтан')
	parent_id = fields.Many2one('hr.open.job','Parent')



class HrApplicant(models.Model):
	_inherit = "hr.applicant"

	is_test = fields.Boolean(string='Тесттэй эсэх',default=False)
	test_amount = fields.Float(string='Тестийн дүн')
	school_app_line_ids = fields.One2many('hr.school', 'appl_id', string='Төгссөн сургууль')
	employment_app_ids = fields.One2many(
		'hr.employment', 'appl_id', string='Ажлын туршлага', tracking=True, copy=True)
	gender = fields.Selection([('male', 'Эрэгтэй'), ('female', 'Эмэгтэй'),('other', 'Бусад')], string='Хүйс')
	emergency_contact = fields.Char("Яаралтай үед холбоо барих хүн",tracking=True)
	emergency_phone = fields.Char("Яаралтай үед холбоо барих утас",tracking=True)
	age = fields.Integer('Нас')

class HrSchool(models.Model):
	_inherit = 'hr.school'
	_description = 'school'

	appl_id = fields.Many2one('hr.applicant', 'Employee')


class HrEmployment(models.Model):
	_inherit = 'hr.employment'

	appl_id = fields.Many2one('hr.applicant', 'Employee')
	desc = fields.Char('Компанийн үйл ажиллагаа')
   