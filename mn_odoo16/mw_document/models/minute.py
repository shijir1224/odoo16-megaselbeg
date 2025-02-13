# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Attendance(models.Model):
	_name = "attendance.register"
	_description = "attendance register"
	name = fields.Char('Хурлын ирц')
	
class MinuteNoteLine(models.Model):
	_name = "minute.note.line"
	_description = 'Minute Line'

	attendance_id = fields.Many2one('attendance.register','Ирц')
	type_id = fields.Many2one('meeting.types', string = 'Төрөл')
	employee_id = fields.Many2one('hr.employee', string = 'Ажилчид')
	minutes_id = fields.Many2one('minute.note',string = 'Minute')


class MinuteNote(models.Model):
	_name = "minute.note"
	_description = u'Minute Note'
	_inherit = ['mail.thread']

	def default_employee_1(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	number = fields.Char('Дугаар', required=True)
	name =fields.Char('Нэр')
	date = fields.Date('Огноо')
	employee_id = fields.Many2one('hr.employee','Хурлын даргалагч')
	type_id = fields.Many2one('meeting.types','Төрөл')
	ruling_ids = fields.One2many('ruling.note','minute_id','Rules')
	state = fields.Selection([('draft','Ноорог'),('send','Илгээсэн'),('confirm','Хаасан')],'Төлөв',default='draft', readonly=True)
	attendance_ids = fields.One2many('minute.note.line','minutes_id', string='Ирц ')
	create_employee_id = fields.Many2one('hr.employee','Үүсгэсэн ажилтан', default=default_employee_1)
	job_id = fields.Many2one('hr.job','Хурлын даргалагчийн албан тушаал ')
	create_job_id = fields.Many2one('hr.job','Үүсгэсэн ажилтны албан тушаал')

	description = fields.Html('Хурлын тэмдэглэл хөтлөх')
	start_time = fields.Float('Эхэлсэн цаг')
	end_time = fields.Float('Дууссан цаг')
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	task_id = fields.Many2one('task.register',string='Үүрэг даалгавар')

	def create_task(self):
		for obj in self:
			if not obj.task_id:
				task_pool=self.env['task.register']
				data_id = task_pool.create({
					'employee': obj.create_employee_id.id,
					'minute_id': obj.id,
					'name':obj.name
					# 'number': task_pool.env['ir.sequence'].with_context(force_company=int(self.res_company_id)).next_by_code('task.register',self.res_company_id.id)
				})
				self.task_id = data_id.id
			else:
				raise UserError('Үүрэг даалгавар үүссэн байна.')

	def start_time_change(self,ids):
		time = self.browse(ids)
		str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(time.start_time, {}) or '')
		return str_val

	def end_time_change(self,ids):
		time_end = self.browse(ids)
		str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(time_end.end_time, {}) or '')
		return str_val

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.job_id = self.employee_id.job_id.id

	@api.onchange('create_employee_id')
	def onchange_create_empolyee_id(self):
		self.create_job_id = self.create_employee_id.job_id.id

	@api.onchange('type_id')
	def onchange_type(self):
		if self.type_id and self.type_id.employees:
			self.attendance_ids.unlink()
			vals = []
			for emp in self.type_id.employees:
				vals.append((0, 0, {'employee_id': emp.id}))
			self.attendance_ids = vals

	# def get_ruling_lines(self, ids):
	# 	report_id = self.browse(ids)
	# 	if report_id.ruling_ids.ruling.ids != []:
	# 		headers = [
	# 			'№',
	# 			'Шийдвэр',
	# 			'Гүйцэтгэх ажилтан'
	# 		]
	# 		datas = []
	# 		report_id = self.browse(ids)
	# 		i = 1
	# 		sum1 = 0
	# 		sum2 = 0
	# 		sum3 = 0

	# 		for line in report_id.ruling_ids:
	# 			temp = [
	# 				str(i),
	# 				line.ruling.name.name,
	# 				', '.join(line.employee_ids.mapped('display_name')),
	# 			]
	# 			datas.append(temp)
	# 			i += 1
	# 		res = {'header': headers, 'data':datas}
	# 		return res

	def c(self, ids):
		report_id = self.browse(ids)
		if report_id.ruling_ids.meeting_task.ids != []:
			headers = [
				'№',
				'Үүрэг даалгавар',
				'Гүйцэтгэх ажилтан'
			]
			datas = []
			report_id = self.browse(ids)
			i = 1
			sum1 = 0
			sum2 = 0
			sum3 = 0

			for line in report_id.ruling_ids:

				temp = [
					str(i),
					line.meeting_task.name.name,
					', '.join(line.employee_ids.mapped('display_name')),
				]
				datas.append(temp)
				i += 1
			res = {'header': headers, 'data':datas}
			return res

	def get_minute_lines(self, ids):
		headers = [
			u'№',
			u'Ажилтан',
			u'Ирц',
		]
		datas = []
		report_id = self.browse(ids)
		i = 1
		sum1 = 0
		sum2 = 0
		sum3 = 0

		for line in report_id.attendance_ids:
			temp = [
				str(i),
				line.employee_id.name,
				line.attendance_id.name,
			]
			datas.append(temp)
			i += 1
		res = {'header': headers, 'data':datas}
		return res

	def action_send(self):
		self.write({'state': 'send'})


	def action_confirm(self):
		self.write({'state': 'confirm'})


	def action_draft(self):
		self.write({'state': 'draft'})

	# def action_decision(self):
	# 	decision.register


class RulingNote(models.Model):
	_name = 'ruling.note'
	_description = u'Ruling Note'
	_inherit = ['mail.thread']

	task_employee_id = fields.Many2one('hr.employee','Гүйцэтгэх ажилтан')
	employee_ids = fields.Many2many('hr.employee', string = 'Гүйцэтгэх ажилчид')
	minute_id = fields.Many2one('minute.note','Minute')
	department_id = fields.Many2one('hr.department', 'Холбогдох нэгж')

	@api.onchange('meeting_task')
	def onchange_employee_id(self):
		emp = []
		for item in self.meeting_task.meeting_assignment_lines:
			emp = emp + item.assignment_employee_id.ids
		self.employee_ids = emp


class MeetingType(models.Model):
	_name = 'meeting.types'
	_description = "meeting types"

	name = fields.Char('Төрөл')
	employees = fields.Many2many('hr.employee',string='Бүлэгт хамаарах хүмүүс')
	state = fields.Selection([('draft','Ноорог'),
				('send',u'Илгээсэн'),
				('confirm_hr_director',u'Шийдвэрлэсэн')], 'Төлөв',readonly=True, default = 'draft', tracking=True, copy=False)

	def action_cancel(self):
		self.write({'state': 'draft'})

	def action_send(self):
		self.write({'state': 'send'})
