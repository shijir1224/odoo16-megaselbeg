
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.http import request
import requests
import logging
import json
import odoo.http as http
_logger = logging.getLogger(__name__)


class PreliminaryNotice(models.Model):
	_name = 'preliminary.notice'
	_description =  'Preliminary notice'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_email(self):
		if self.env.context.get('warning_page',True):
			ii = self.env['email.send.users'].search([('is_first','=',True)])
			return ii.ids
		
	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('reliminary.notice')
		return name

	name = fields.Char(string='Дугаар', readonly=True, default=_default_name)
	state = fields.Selection([('draft', 'Ноорог'),('sent', 'Илгээсэн'),('done', 'Дууссан')], 'Төлөв', readonly=True, default='draft')
	date = fields.Datetime('Осол гаргасан огноо', readonly=True, required=True, states={'draft':[('readonly',False)]})
	part = fields.Selection([('day', 'Өдөр'),('nigth', 'Шөнө')], 'Ээлж', readonly=True, required=True, states={'draft':[('readonly',False)]})
	injury_desc = fields.Text(string='Ослын тодорхойлт', readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True, default=lambda self: self.env.user.branch_id, states={'draft':[('readonly',False)]}, domain="[('company_id','=',company_id)]")
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	action_ids = fields.Many2many('hse.notice.action.config', 'parent_act_id', string='Газар дээр авсан арга хэмжээ', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	approved_by = fields.Many2one('hr.employee', string='Зөвшөөрсөн', readonly=True)
	approved_position = fields.Many2one('hr.job', related='approved_by.job_id', string='Албан тушаал', readonly=True)
	approved_by_date = fields.Datetime('Зөвшөөрсөн огноо', readonly=True)
	notf_type = fields.Selection([
		('email', 'Имэйл'),
		('sms', 'Смс'),
	], 'Мэдэгдэл илгээх төрөл', default='email', required=True,  readonly=True, states={'draft':[('readonly',False)]})
	mail_send_user_ids = fields.Many2many('email.send.users', string='Мэдэгдэл хүргэх имэйл', default=_default_email, readonly=True, states={'draft':[('readonly',False)]})
	template_id = fields.Many2one('text.template', string='Смс утга', readonly=True, states={'draft':[('readonly',False)]}, domain="[('type','=','notice')]")
	sms_text = fields.Char(related='template_id.name', string='CMC Утга', readonly=True, states={'draft':[('readonly',False)]})
	employee_ids = fields.Many2many('hr.employee', 'preliminary_notice_employee_rel', 'notice_id', 'employee_id', string='Ажилтанууд', readonly=True, states={'draft':[('readonly',False)]})
	sms_state = fields.Selection([
		('success','Aмжилттай'),
		('unsuccess','Амжилттгүй')], string='СМС Төлөв', readonly=True, tracking=True)
	result = fields.Char('Result', readonly=True, tracking=True)
		
	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_sent(self):
		self.write({'state': 'sent'})

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
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse', 'action_hse_preliminary_notice_action')[1]
		html = u'<b>Урьдчилсан мэдэгдэл ирлээ!!! Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=preliminary.notice&action=%s>%s</a></b>,Урьдчилсан мэдэгдэл ирлээ!!!"""% (base_url,self.id,action_id,self.date)		
		# for item in self.mail_send_user_ids:
			# if item.name:
				# self.env.user.send_emails(html, [item.partner_id], with_mail=True, attachment_ids=self.attachment_ids.ids, email_from=self.env.user.company_id.email)
		self.send_emails(partner_mails=self.mail_send_user_ids.mapped('name'), subject='Урьдчилсан мэдэгдэл', body=html, attachment_ids=self.attachment_ids.ids)

	def send_sms_sent(self):
		url = self.env['ir.config_parameter'].sudo().get_param('message_pro_url', False)
		for item in self.employee_ids:
			if url and item.mobile_phone:
				url = url.replace("UTAS", item.mobile_phone)
				url = url.replace("UTGA", self.sms_text or ' ')
				base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
				_logger.info('message_pro_url %s'%(url))
				_logger.error('CHAT http.request.httprequest.host_url %s'%(str(http.request.httprequest.host_url )))
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
					_logger.error('LOCAL UCHIRAAS ILGEEGEEGUI ')

	def action_to_done(self):
		self.write({'state': 'done'})
		x = self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).id
		self.write({'approved_by': x})
		self.write({'approved_by_date': datetime.now()})
		if self.notf_type == 'sms':
			self.send_sms_sent()
		else:
			self.sent_mail()