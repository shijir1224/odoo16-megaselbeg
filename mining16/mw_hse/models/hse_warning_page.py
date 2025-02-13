from odoo import  api, fields, models, _
from datetime import datetime, timedelta
import requests
import logging
import json
import odoo.http as http
_logger = logging.getLogger(__name__)



class WarningPage(models.Model):
	_name = 'hse.warning.page'
	_description =  'Сэрэмжлүүлэх хуудас'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].sudo().next_by_code('hse.warning.page')
		return name

	@api.model
	def _default_email(self):
		if self.env.context.get('warning_page',True):
			ii = self.env['email.send.users'].search([('is_first','=',True)])
			return ii.ids

	name = fields.Char(string='Дугаар', required=True, default=_default_name, readonly=True)
	state = fields.Selection([('draft', 'Ноорог'),('sent', 'Боловсруулсан'),('done','Хянасан'),('end', 'Дууссан')], 'Төлөв', readonly=True, default='draft')
	date = fields.Datetime('Осол гаргасан огноо', readonly=True, required=True, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string="Компани", readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string="Салбар", default=lambda self: self.env.user.branch_id, states={'draft':[('readonly',False)]}, domain="[('company_id','=',company_id)]")
	desc = fields.Text(string='Тодорхойлт', readonly=True, states={'draft':[('readonly',False)],'draft':[('readonly',False)]})
	Issues_consider = fields.Text(string='Анхаарах асуудал', readonly=True, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
	preventive_measures = fields.Text(string='Урьдчилан сэргийлэх арга хэмжээ', readonly=True, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
	other = fields.Text(string='Бусад', readonly=True, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Зураг, Хавсралт')
	developed_by = fields.Many2one('hr.employee', string='Боловсруулсан', readonly=True)
	developed_position = fields.Many2one('hr.job', related='developed_by.job_id', string='Боловсруулсан ажилтны АТ', readonly=True)
	developed_by_date = fields.Datetime('Боловсруулсан огноо', readonly=True)
	check_by = fields.Many2one('hr.employee', string='Хянасан', readonly=True)
	check_position = fields.Many2one('hr.job', related='check_by.job_id', string='Хянасан ажилтны АТ', readonly=True)
	check_by_date = fields.Datetime('Хянасан огноо', readonly=True)
	notf_type = fields.Selection([
		('email', 'Имэйл'),
		('sms', 'Смс'),
	], 'Мэдэгдэл илгээх төрөл', default='email', readonly=True, states={'draft':[('readonly',False)]})
	mail_send_user_ids = fields.Many2many('email.send.users', string='Мэдэгдэл хүргэх имэйл', default=_default_email, readonly=True, states={'draft':[('readonly',False)]})
	employee_ids = fields.Many2many('hr.employee', 'warning_page_employee_rel','employee_id', string='Ажилтанууд', readonly=True, states={'draft':[('readonly',False)]})
	template_id = fields.Many2one('text.template', string='Смс утга', readonly=True, states={'draft':[('readonly',False)]}, domain="[('type','=','notice')]")
	sms_text = fields.Char(related='template_id.name', string='CMC Утга', readonly=True)
	sms_state = fields.Selection([
		('success','Aмжилттай'),
		('unsuccess','Амжилттгүй')], string='СМС Төлөв', readonly=True, tracking=True)
	result = fields.Char('Result', readonly=True, tracking=True)

	def action_to_end(self):
		self.write({'state': 'end'})
		s = self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).id
		self.write({'check_by': s})
		self.write({'check_by_date': datetime.now()})
		if self.notf_type == 'sms':
			self.send_sms_sent()
		else:
			self.sent_mail()

	def action_to_done(self):
		self.write({'state': 'done'})
		x = self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).id
		self.write({'developed_by': x})
		self.write({'developed_by_date': datetime.now()})
		
	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_sent(self):
		self.write({'state': 'sent'})

	def send_sms_sent(self):
		url = self.env['ir.config_parameter'].sudo().get_param('message_pro_url', False)
		for item in self.employee_ids:
			if url and item.mobile_phone:
				url = url.replace("UTAS", item.mobile_phone)
				url = url.replace("UTGA", self.sms_text or ' ')
				base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
				_logger.info('message_pro_url %s'%(url))
				_logger.error('CHAT http.request.httprequest.host_url %s'%(str(base_url)))
				self.env['ir.config_parameter'].sudo().get_param('message_pro_url')
				if 'erp.soyolon.mn:8079' in base_url:
					resp = requests.get(url=url)
					try:
						data = json.loads(resp.text)
						if data:
							self.result = str(data)
							if 'SUCCESS' in str(data):
								self.sms_state = 'success'
							else:
								self.sms_state = 'unsuccess'
					except Exception as e:
						self.sms_state = 'unsuccess'
						_logger.error('message_pro_url Connection failed. %s'%(e))
				else:
					_logger.error('LOCAL UCHIRAAS ILGEEGEEGUI')

	
	def send_emails(self, partner_mails, subject, body, attachment_ids):
		for mail in partner_mails:
			mail_obj = self.env['mail.mail'].sudo().create({
				'email_from': self.env.user.company_id.email,
				'email_to': mail,
				'subject': subject,
				'body_html': '%s' % body,
				'attachment_ids': attachment_ids
			})
			mail_obj.send()
	
	def sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse', 'action_hse_warning_page_action')[1]
		html = u'<b>Сэрэмжлүүлгийн хуудас ирлээ!!! Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.warning.page&action=%s>%s</a></b>,Сэрэмжлүүлгийн хуудас ирлээ!!!"""% (base_url, self.id,action_id, self.date)		
		# for item in self.mail_send_user_ids:
			# if item.partner_id:
				# self.env.user.send_chat(html,[item.partner_id], with_mail=True, attachment_ids=self.attachment_ids.ids)
		self.send_emails(partner_mails=self.mail_send_user_ids.mapped('name'), subject='Сэрэмжлүүлэх хуудас', body=html, attachment_ids=self.attachment_ids.ids)