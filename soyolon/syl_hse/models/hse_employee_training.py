from odoo import  api, fields, models, _
from datetime import datetime, timedelta

from odoo.http import request
import json


class HseEmployeeTraining(models.Model):
	_inherit ='hse.employee.training'

	next_training_employee_id = fields.Many2one('hr.employee', string='Анхан шатны зааварчилгаа өгөх ажилтан')

	def send_emails(self, subject, body, attachment_ids):
		mail_obj = self.env['mail.mail'].sudo().create({
			'email_from': self.company_id.email,
			'email_to': self.next_training_employee_id.work_email,
			'subject': subject,
			'body_html': '%s' % body,
			'attachment_ids': attachment_ids
		})
		mail_obj.send()

	def action_to_next_training_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse_employee_training', 'action_hse_employee_training_core')[1]
		action2_id = self.env['ir.model.data'].check_object_reference('mw_hse_employee_training', 'action_hse_employee_training_core')[1]
		html = u'<b>ХАБ Шинэ ажилтны сургалтанд хамрагдсан ажилчдын мэдээлэл ирлээ Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.employee.training&action=%s>%s</a> дугаартай Сургалтын мэдээлэл ирлээ!<br/>"""% (base_url, self.id, action_id, self.name)
		html += u'<b> Анхан шатны зааварчилгааг доорх линкээр орж бүртгэнэ үү.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#action=%s&model=hse.employee.training&view_type=list&cids=1&me>%s</a></b>"""% (base_url, action2_id, 'Энэ дээр дарж бүртгэлээ үүсгэнэ үү!!!')
		if not self.next_training_employee_id.work_email:
			self.env.user.send_chat(html, [self.env.user.partner_id], with_mail=True, subject_mail=False, attachment_ids=False)
		else:
			self.send_emails(subject=False, body=html, attachment_ids=False)

	# def action_to_next_training_mail(self):
	# 	base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
	# 	action_id = self.env['ir.model.data'].check_object_reference('mw_hse_employee_training', 'action_hse_employee_training_core')[1]
	# 	action2_id = self.env['ir.model.data'].check_object_reference('mw_hse_employee_training', 'action_hse_employee_training_core')[1]
	# 	html = u'<b>ХАБ Шинэ ажилтны сургалтанд хамрагдсан ажилчдын мэдээлэл ирлээ Доорх линкээр орно уу.</b><br/>'
	# 	html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.employee.training&action=%s>%s</a> дугаартай Сургалтын мэдээлэл ирлээ!<br/>"""% (base_url, self.id, action_id, self.name)
	# 	html += u'<b> Анхан шатны зааварчилгааг доорх линкээр орж бүртгэнэ үү.</b><br/>'
	# 	html += u"""<b><a target="_blank" href=%s/web#action=%s&model=hse.employee.training&view_type=list&cids=1&me>%s</a></b>"""% (base_url, action2_id, 'Энэ дээр дарж бүртгэлээ үүсгэнэ үү!!!')
	# 	if self.next_training_employee_id.partner_id:
	# 		self.env.user.send_chat(html,[self.next_training_employee_id.partner_id], with_mail=True)

	def action_to_sent_mail(self):
		self.action_to_next_training_mail()
		res = super(HseEmployeeTraining, self).action_to_sent_mail()
		return res


	def action_to_download(self):
		training_line =  self.env['hse.employee.training.line']
		if self.training_line:
			self.training_line.unlink()
		time_obj = self.env['hr.timetable.line.line'].search([
			('date','=',self.date),
			('is_work_schedule','in',['day','night']),
			('parent_id.department_id.branch_id','=',self.branch_id.id),
			('hour_to_work','>=',0),
			('shift_plan_id.is_work','=','day'),
			])
		for time in time_obj:
			line_conf = training_line.create({
				'training_id': self.id,
				'employee_id': time.employee_id.id,
				'job_id': time.job_id.id,
				'date': self.date,
				'is_instruction': False,
			})