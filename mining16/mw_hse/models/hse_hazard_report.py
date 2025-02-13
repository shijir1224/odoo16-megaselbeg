
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
import pytz
from odoo.exceptions import UserError


class HseHazardReport(models.Model):
	_name ='hse.hazard.report'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Hazard report'
	_order = 'datetime desc'

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.hazard.report')
		return name

	state = fields.Selection([
		('draft', 'Ноорог'),
		('sent_mail', 'илгээгдсэн'),
		('to_assign', 'Хувиарласан'),
		('repaired', 'Засагдсан'),
		('done', 'Дууссан')], 'Төлөв', readonly=True, default='draft')
	name = fields.Char(string='Дугаар', readonly=True, default=_default_name)
	datetime = fields.Datetime('Бүртгэсэн огноо', required=True, readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True, readonly=True, domain="[('company_id','=',company_id)]", default=lambda self: self.env.user.branch_id)
	location_id = fields.Many2one('hse.location','Байрлал', required=True, readonly=True, store=True, states={'draft':[('readonly',False)]}, domain="[('branch_id','=',branch_id)]")
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	hazard_type = fields.Selection([
		('minor', 'Бага'),
		('medium', 'Дунд'),
		('many', 'Их'),
		('seriuos', 'Маш их')], 'Аюулын түвшин', required=True, readonly=True, states={'draft':[('readonly',False)]})
	notify_emp_id = fields.Many2one('hr.employee', string='Үүсгэсэн ажилтан', readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: self.env.user.employee_id)
	hazard_identification = fields.Text('Аюулын тодорхойлолт', required=True, readonly=True, states={'draft':[('readonly',False)]})
	corrective_action_to_be_taken = fields.Text('Авах арга хэмжээ', required=True, readonly=True, states={'draft':[('readonly',False)]})
	corrective_action_taken = fields.Text('Авагдсан арга хэмжээ', states={'to_assign':[('readonly',False)]}, readonly=True)
	taken_attachment_ids = fields.Many2many('ir.attachment', 'hazard_report_taken_attachment_rel', 'hazard_report_id_1', string='Арга хэмжээ авсан/Хавсралт/', states={'done':[('readonly',False)]})
	employee_id = fields.Many2one('hr.employee', string='Хариуцагч', required=False, readonly=True, states={'sent_mail':[('readonly',False)]})
	mail_line = fields.One2many('hse.hazard.report.mail.line', 'hazard_id', 'Майлын мөр')
	mail_text = fields.Text('Майл текст')
	taken_employee_id = fields.Many2one('hr.employee', string='Арга хэмжээ авсан ажилтан', readonly=True)
	taken_datetime = fields.Datetime('Арга хэмжээ авсан огноо', readonly=True)
	hazard_category_id = fields.Many2one('hse.hazard.category', string='Аюулын ангилал', states={'draft':[('readonly',False)],'sent_mail':[('readonly',False)]}, readonly=True)
	is_hazard_control = fields.Boolean('Аюулыг хяналтанд авах шаардлагатай эсэх', default=False, states={'draft':[('readonly',False)]}, readonly=True)
	control_description = fields.Text('Аюулыг хэрхэн хянаж үнэлсэн тайлбар', states={'draft':[('readonly',False)]}, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', 'hazard_report_attachment_rel', 'hazard_report_id', string='Зураг', readonly=True, states={'draft':[('readonly',False),('required',True)]})
	hse_employee_id = fields.Many2one('res.users', string='ХАБ Ажилтан', required=False, domain="[('is_hse_emp','=',True),('branch_id','=',branch_id)]", states={'draft':[('readonly',False)]}, readonly=True)

	def unlink(self):
		for item in self:
			if item.state !='draft':
				raise UserError(_('Төлөв Ноорог биш байна.'))
			
		return super(HseHazardReport, self).unlink()
		
	def _get_email_employee(self, employee_id, user_mails):
		emp_mail = False
		if 'hr.employee' in str(employee_id):
			if employee_id.work_email:
				if employee_id.work_email not in user_mails:
					emp_mail = employee_id.work_email
			else:
				if employee_id.parent_id.work_email and employee_id.parent_id.work_email not in user_mails:
					emp_mail = employee_id.parent_id.work_email
		else:
			if employee_id.email not in user_mails:
				emp_mail = employee_id.work_email
		if emp_mail:
			return {'email': emp_mail}
		return False
	
	def _get_email_hse_employee(self, hse_employee_id, user_mails):
		emp_mail = False
		if 'hr.employee' in str(hse_employee_id):
			if hse_employee_id.work_email:
				if hse_employee_id.work_email not in user_mails:
					emp_mail = hse_employee_id.work_email
			else:
				if hse_employee_id.parent_id.work_email and hse_employee_id.parent_id.work_email not in user_mails:
					emp_mail = hse_employee_id.parent_id.work_email
		else:
			if hse_employee_id.email not in user_mails:
				emp_mail = hse_employee_id.work_email
		if emp_mail:
			return {'email': emp_mail}
		return False

	def send_emails(self, subject, body):
		html = body or ''
		for item in self.mail_line:
			if self.state=='repaired':
				mail = self.env['mail.mail'].sudo().create({
					'body_html': html,
					'subject': subject,
					'email_to': item.mail,
					'email_from': self.company_id.email,
					'attachment_ids': self.taken_attachment_ids
				})
			else:
				mail = self.env['mail.mail'].sudo().create({
					'body_html': html,
					'subject': subject,
					'email_to': item.mail,
					'email_from': self.company_id.email,
					'attachment_ids': self.attachment_ids
				})
			mail.send()
			if mail.state=='sent':
				print('success')

	def _get_mail(self, obj):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		# action_id = self.env['ir.model.data'].check_object_reference('mw_hse', 'view_hse_hazard_report_form')[1]
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse', 'action_hse_hazard_report')[1]
		body = u'<b>Дараах Аюулыг мэдээлэх хуудас </b><br/>'
		body += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.hazard.report&action=%s>%s</a></b>"""%(base_url, obj.id, action_id, obj.name)
		if obj.state =='draft':
			body += u' таньд ирлээ.</p>'
		if obj.state =='sent_mail':
			body += u' таньд хувиарлагдан ирлээ.</p>'
		if obj.state =='to_assign':
			body += u' засагдсан төлөвт орлоо.</p>'
		date_time = obj.datetime
		timezone = pytz.timezone(self.env.user.tz)
		date_time = (date_time.replace(tzinfo=pytz.timezone('UTC'))).astimezone(timezone)
		if obj.state =='draft':
			body += u'<table> <tr> <td>Огноо</td><td style="font-weight: bold;">'+str(date_time)+u'</td></tr><tr><td>Төсөл</td>'
			body += u'<td style="font-weight: bold;">'+(obj.branch_id.name if obj.branch_id else '')+u'</td></tr><tr><td>Аюулын түвшин</td>'
			body += u'<td style="font-weight: bold;">'+(dict(obj._fields['hazard_type'].selection).get(obj.hazard_type) if obj.hazard_type else '')+u'</td></tr><tr><td>Байрлал</td>'
			body += u'<td style="font-weight: bold;">'+(obj.location_id.name if obj.location_id else '')+u'</td></tr><tr><td>Мэдээлсэн ажилтан</td>'
			body += u'<td style="font-weight: bold;">'+(obj.notify_emp_id.name if obj.notify_emp_id else '')+u'</td></tr>'
			body += u'<table cellspacing="1" border="1" cellpadding="4"><tr style="background-color: #4CAF50; color: white;">'
			body += u'<th>Аюулын тодорхойлолт</th><th>Авсан арга хэмжээ</th></tr><tr style="color: red;">'
			body += u'<td>'+obj.hazard_identification+'</td><td>'+obj.corrective_action_to_be_taken+'</td></tr></table>'
		elif obj.state =='sent_mail':
			body += u'<table> <tr> <td>Огноо</td><td style="font-weight: bold;">'+str(date_time)+u'</td></tr><tr><td>Төсөл</td>'
			body += u'<td style="font-weight: bold;">'+(obj.branch_id.name if obj.branch_id else '')+u'</td></tr><tr><td>Аюулын түвшин</td>'
			body += u'<td style="font-weight: bold;">'+(dict(obj._fields['hazard_type'].selection).get(obj.hazard_type) if obj.hazard_type else '')+u'</td></tr><tr><td>Байрлал</td>'
			body += u'<td style="font-weight: bold;">'+(obj.location_id.name if obj.location_id else '')+u'</td></tr><tr><td>Мэдээлсэн ажилтан</td>'
			body += u'<td style="font-weight: bold;">'+(obj.notify_emp_id.name if obj.notify_emp_id else '')+u'</td></tr>'
			body += u'<table cellspacing="1" border="1" cellpadding="6"><tr style="background-color: #4CAF50; color: white;">'
			body += u'<th>Аюулын тодорхойлолт</th><th>Авсан арга хэмжээ</th><th>Аюулын ангилал</th></tr><tr style="color: red;">'
			body += u'<td>'+obj.hazard_identification+'</td><td>'+obj.corrective_action_to_be_taken+'</td><td>'+obj.hazard_category_id.name if obj.hazard_category_id else 'Байхгүй'+'</td></tr></table>'
		elif obj.state =='to_assign':
			taken_employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).id
			self.write({
					'state':'repaired', 
					'taken_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
					'taken_employee_id':taken_employee_id})
			body += u'<br/><span style="font-weight: bold;">Авагдсан арга хэмжээ: </span>  <span>'+obj.corrective_action_taken if obj.corrective_action_taken else '' +'</span>'
			body += u'<br/><span style="font-weight: bold;">Арга хэмжээ авсан ажилтан: </span>  <span>'+obj.taken_employee_id.name if obj.taken_employee_id else '' +'</span>'
			body += u'<br/><span style="font-weight: bold;">Арга хэмжээ авсан огноо: </span>  <span>'+obj.taken_datetime.strftime('%Y-%m-%d %H:%m') if obj.taken_datetime else '' +'</span>'
		print('body=======', body)
		mail_text=''
		if obj.mail_text:
			mail_text=obj.mail_text
		self.send_emails(u'Аюулыг мэдээлэх хуудас '+(obj.name or ''), body+u'<br/>'+(mail_text))
		sent_mail_users = ''
		send_partners = False
		# Хялбар апп дээр аюулыг мэдээлэх үүсгэх email илгээж байгаа
		for item in obj.mail_line:
			sent_mail_users += item.mail+'<br/>'
		if not obj.mail_line:
			user_ids = self.env['res.users'].sudo().search([('is_hse_emp','=',True), ('branch_id','=',obj.branch_id.id)])
			if not user_ids:
				user_ids = self.env['res.users'].sudo().search([('is_hse_emp','=',True)],limit=1)
			send_partners = user_ids.mapped('partner_id')
			for user in user_ids:
				sent_mail_users += user.employee_id.work_email or user.login
		message_post = u'Хариу арга хэмжээ авах'
		if obj.state =='repaired':
			message_post = u'Засагдсан'
		try:
			# _logger.info(sent_mail_users)
			# email_from = 'hse@mak.mn'
			email_from = self.env.user.company_id.email
			
			obj.message_post(body=(message_post+u':<br/>Дараах хүмүүст майл илгээгдэв:<br/>'+sent_mail_users), message_type='notification', subtype_xmlid="mail.mt_comment", email_from=email_from, partner_ids=send_partners, parent_id=False)
		except:
			return False
		return True


	def mail_sent(self):
		obj = self
		self._get_mail(obj)
		if obj.state=='draft':
			self.write({'state': 'sent_mail'})
		elif obj.state=='sent_mail':
			self.write({'state': 'to_assign'})
		elif obj.state=='to_assign':
			self.write({'state': 'repaired'})
		else: ''


	def action_to_sent_mail(self):
		if not self.attachment_ids:
			raise UserError(_('Хавсралт Зураг заавал оруулна уу.!!!'))
		obj = self
		obj.mail_line = False
		user_mails = []
		if obj.state=='draft':
			user_obj = self._get_email_hse_employee(obj.hse_employee_id, user_mails)
			if user_obj:
				user_mails.append(user_obj['email'])
		user_obj = self._get_email_employee(obj.hse_employee_id, user_mails)
		if user_obj:
			user_mails.append(user_obj['email'])
		for item in user_mails:
			data = { 
					'hazard_id': obj.id,
					'mail': item,
					}
			line_id = self.env['hse.hazard.report.mail.line'].create( data)
		view_id = self.env['ir.ui.view'].search([('model','=','hse.hazard.report'), ('name','=','hse.hazard.report.mail.form')])
		return {
			'name':_("Дараах хүмүүст майл илгээж мэдэгдэх"),
			'view_mode': 'form',
			'view_id': view_id.id,
			'view_type': 'form',
			'res_model': 'hse.hazard.report',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj.id,
			'context': self._context
		}
	
	def _get_sent_email_hse_employee(self, hse_employee_id, user_mails):
		emp_mail = False
		if self.state=='draft' or 'to_assign':
			if str(hse_employee_id):
				if hse_employee_id.work_email:
					if hse_employee_id.work_email not in user_mails:
						emp_mail = hse_employee_id.work_email
				else:
					if hse_employee_id.employee_id.work_email and hse_employee_id.employee_id.work_email not in user_mails:
						emp_mail = hse_employee_id.employee_id.work_email
		else:
			if hse_employee_id.email not in user_mails:
				emp_mail = hse_employee_id.email
		if emp_mail:
			return {'email': emp_mail}
		return False
	
	def _get_sent_email_employee(self, employee_id, user_mails):
		emp_mail = False
		if self.state=='sent_mail':
			if str(employee_id):
				if employee_id.work_email:
					if employee_id.work_email not in user_mails:
						emp_mail = employee_id.work_email
				else:
					if employee_id.parent_id.work_email and employee_id.parent_id.work_email not in user_mails:
						emp_mail = employee_id.parent_id.work_email
		else:
			if employee_id.email not in user_mails:
				emp_mail = employee_id.email
		if emp_mail:
			return {'email': emp_mail}
		return False

	def action_to_repaired(self):
		if not self.taken_attachment_ids:
			raise UserError(_('Авсан арга хэмжээний зураг заавал оруулна уу.!!!'))
		obj = self
		obj.mail_line = False
		user_mails = []	
		user_obj = self._get_sent_email_hse_employee(obj.hse_employee_id, user_mails)
		if user_obj:
			user_mails.append(user_obj['email'])
		user_obj = self._get_sent_email_hse_employee(obj.hse_employee_id, user_mails)
		if user_obj:
			user_mails.append(user_obj['email'])
		for item in user_mails:
			data = { 
				'hazard_id': obj.id,
				'mail': item,
			}
			line_id = self.env['hse.hazard.report.mail.line'].create( data)
		for item in self:
			view_id = self.env['ir.ui.view'].search([('model','=','hse.hazard.report'),('name','=','hse.hazard.report.mail.form')])
			return {
				'name':_("Дараах хүмүүст майл илгээж мэдэгдэх"),
				'view_mode': 'form',
				'view_id': view_id.id,
				'view_type': 'form',
				'res_model': 'hse.hazard.report',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': item.id,
				'context': self._context
			}
	
	def action_to_assign(self):
		obj = self
		obj.mail_line = False
		user_mails = []
		user_obj = self._get_sent_email_employee(obj.employee_id, user_mails)
		if user_obj:
			user_mails.append(user_obj['email'])
			for item in user_mails:
				data = { 
						'hazard_id': obj.id,
						'mail': item,
						}
				line_id = self.env['hse.hazard.report.mail.line'].create(data)
			for item in self:
				view_id = self.env['ir.ui.view'].search([('model','=','hse.hazard.report'),('name','=','hse.hazard.report.mail.form')])
			return {
					'name':_("Дараах хүмүүст майл илгээж мэдэгдэх"),
					'view_mode': 'form',
					'view_id': view_id.id,
					'view_type': 'form',
					'res_model': 'hse.hazard.report',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'res_id': item.id,
					'context': self._context
				}

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_done(self):
		self.write({'state': 'done'})

	'''Аюулыг мэдээлэх хуудас засагдаагүйг автоматаар мэдэгдэх'''
	def get_mail_notice_hazard_report(self):
		uid = False
		# context = {}
		hazard_ids = self.env['hse.hazard.report'].search([('state','=','sent_mail')])
		for item in self.env['hse.hazard.report'].browse(hazard_ids):
			self._get_mail( item.id, item
				#   context=context
				  )
		return True

class HseHazardReportMailLine(models.Model):
	_name ='hse.hazard.report.mail.line'
	_description = 'Mail line'
   
	hazard_id = fields.Many2one('hse.hazard.report', 'Hazard ID', required=True, ondelete='cascade')
	mail = fields.Char('Майл', required=True)

class ResUsers(models.Model):
	_inherit ='res.users'
	_description = 'Res Users'

	is_hse_emp = fields.Boolean('ХАБ ажилтан эсэх', default=False)