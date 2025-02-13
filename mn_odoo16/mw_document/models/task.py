#  -*- coding: utf-8 -*-
import datetime
from datetime import datetime

from odoo import api, fields, models, _

# import odoo.netsvc, decimal, os, xlrd



class TaskRegister(models.Model):
	_name = 'task.register'
	_description = 'Task register'
	_inherit = ['mail.thread']
	
	
	def default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	
	name = fields.Char(string='Үүрэг даалгаврын утга')
	number = fields.Char('Дугаар', readonly=True)
	employee = fields.Many2one('hr.employee','Үүрэг даалгаврыг үүсгэсэн хэрэглэгч',required=True, default = default_employee)
	date = fields.Date('Үүрэг даалгавар өгсөн огноо',default= fields.Date.context_today)
	send_date = fields.Date('ҮД тайлагнасан хугацаа')
	end_date = fields.Date('ҮД-ын хугацаа')
	# employee_ids = fields.Many2many('hr.employee',string=' Үүрэг даалгаврыг биелүүлэх ажилтнууд')
	arrived_task = fields.Char('Надад ирсэн үүрэг даалгавар')
	send_task = fields.Char('Миний илгээсэн үүрэг даалгавар')
	
	# name = fields.Many2one('task.value', 'ҮД-ын утга')
	# task_description = fields.Many2one('task.description','ҮД-ын ангилал')

	num_employee_id = fields.Many2one('hr.employee','Хөндлөнгийн үнэлгээ өгөх ажилтан')
	num_job_id = fields.Many2one('hr.job','Хөндлөнгийн үнэлгээ өгөх ажилтны албан тушаал')
	num_department_id = fields.Many2one('hr.department','Хөндлөнгийн үнэлгээ өгөх ажилтны алба хэлтэс')
	task_value = fields.Char('ҮД-ын утга чиглэл')
	mark =  fields.Float('Хөндлөнгийн үнэлгээ')
	mark_date = fields.Date('Хөндлөнгийн үнэлгээ өгсөн огноо')
	mark_description = fields.Text('Хөндлөнгийн үнэлгээний тайлбар')

	assignment_lines = fields.One2many('assignment.create','assignment_note',string = 'Даалгавар')
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	minute_id = fields.Many2one('minute.note',string='Хурал')

	# @api.model
	# def create(self,vals):
	# 	res = super(TaskRegister, self).create(vals)
	# 	if self.res_company_id:
	# 		if not self.number:
	# 			self.number = self.env['ir.sequence'].with_context(force_company=int(self.res_company_id)).next_by_code('task.register',self.res_company_id.id)
	# 	return res

	def assignment_mark_notification_send(self):

		partner_ids = []
		for receiver in self.num_employee_id:
			if receiver.partner_id:
				partner_ids.append(receiver.partner_id.id)
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('mw_document', 'action_task_register')[1]
		html = u'<b>ҮД.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=task.register&action=%s>%s</a></b>,- Хөндлөнгийн үнэлгээ өгөх үүрэг даалгавар ирсэн байна !"""% (base_url,self.id,action_id,self.employee.name)
		self._send_chat(html, self.env['res.partner'].browse(partner_ids))

   

	def _update_task_change(self):
		today = datetime.now()
		notification_date = self.env['task.register'].search([('end_date', '=', today)])
		for item in notification_date:
			item.task_notification_send()
		
	@api.onchange('num_employee_id')
	def onchange_num_employee_id(self):
		self.num_job_id = self.num_employee_id.job_id.id
		self.num_department_id = self.num_employee_id.department_id.id
	
	@api.onchange('task_employee_id')
	def onchange_task_employee(self):
		self.task_job_id = self.task_employee_id.job_id.id
		self.task_department_id = self.task_employee_id.department_id.id


class AssigmentCreate(models.Model):
	_name = 'assignment.create'
	_description = 'Assignment create'

	assignment_note = fields.Many2one('task.register', string= "Assignment")
	assignment_employee_id = fields.Many2one('hr.employee','Даалгавар гүйцэтгэх ажилтан')
	assignment_end_date = fields.Date('Даалгавар хийж дууссан огноо')
	performance_percent = fields.Float('Гүйцэтгэлийн хувь')
	description = fields.Text('Гүйцэтгэлийн явцын тэмдэглэл')
	num_description = fields.Text('Гүйцэтгэлийн бүрэн тайлбар')



# class TaskValue(models.Model):
# 	_name = 'task.value'
# 	_description = 'Task value'

# 	name = fields.Char('ҮД-ын утга')
	


# class TaskDescription(models.Model):
# 	_name = 'task.description'
# 	_description = 'Task description'

# 	name = fields.Char('ҮД-ын ангилал')
