# -*- coding: utf-8 -*-
import os
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class HrTurnover(models.Model):
	_name = 'hr.turnover'
	_description = 'Hr Turnover'
	_inherit = ['mail.thread']
	_order = 'e_date'

	def document_default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	employee_id = fields.Many2one(
		'hr.employee', string='Бүртгэсэн ажилтны нэр', default=document_default_employee, tracking=True)
	job_id = fields.Many2one('hr.job', string='Бүртгэсэн ажилтны албан тушаал')
	department_id = fields.Many2one(
		'hr.department', string='Бүртгэсэн ажилтны Алба хэлтэс')
	create_date = fields.Date('Бүртгэсэн огноо ')
	work_location_id = fields.Many2one('hr.work.location', string='Ажлын байршил', required=True)
	s_date = fields.Date('Эхлэх огноо')
	e_date = fields.Date('Дуусах огноо')
	resigned_emp = fields.Float('Ажлаас гарсан ажилтны тоо')
	smonth_emp = fields.Float('Сарын эхэнд байсан ажилтны тоо')
	emonth_emp = fields.Float('Сарын сүүлээрх ажилтны тоо')
	avg_emp = fields.Float('Дундаж ажилтны тоо')
	turn_over = fields.Float('Хүний нөөцийн эргэц')
	state = fields.Selection([('draft','Ноорог'), ('send','Илгээсэн'),('done','Дууссан')], default='draft', string='Төлөв')
	
	def action_done(self):
		self.write({'state':'done'})

	def action_send(self):
		self.write({'state':'send'})

	def action_draft(self):
		self.write({'state':'draft'})


	def compute_turnover(self):	
		if self.s_date and self.e_date:
			res_emp = self.env['hr.order'].search([('type','=','type6'),('starttime','>=',self.s_date),('starttime','<=',self.e_date),('work_location_id','=',self.work_location_id.id)])
			smonth_emp = self.env['hr.employee'].search([('employee_type','in',('employee','trainee','contractor')),('engagement_in_company','<=',self.s_date),('work_location_id','=',self.work_location_id.id)])
			emonth_emp = self.env['hr.employee'].search([('employee_type','in',('employee','trainee','contractor')),('engagement_in_company','<=',self.e_date),('work_location_id','=',self.work_location_id.id)])
			self.resigned_emp = len(res_emp)
			self.smonth_emp = len(smonth_emp)
			self.emonth_emp = len(emonth_emp)
			if len(smonth_emp)>0 and len(emonth_emp)>0:
				self.avg_emp = (len(smonth_emp) + len(emonth_emp))/2
			if len(res_emp)>0 and self.avg_emp>0:
				self.turn_over = len(res_emp) * 100/self.avg_emp
				
	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.department_id = self.employee_id.department_id.id
		self.job_id = self.employee_id.job_id.id
