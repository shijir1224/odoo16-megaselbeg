# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class MwGratitude(models.Model):
	_name = 'mw.gratitude'
	_inherit = ['mail.thread','mail.activity.mixin']
	_description = 'Талархал'
	
	name = fields.Char('Нэр', tracking=True)
	state = fields.Selection([
		('draft','Шинэ'),
		('done','Дууссан'),
	], string='Төлөв', default='draft', tracking=True )
	date = fields.Date(string='Огноо', default=fields.Datetime.now)
	gratitude_source_id = fields.Many2one('utm.source', 'Талархал ирсэн суваг', tracking=True, index=True)
	partner_id = fields.Many2one('res.partner', string='Харилцагч', required=True, tracking=True, index=True)
	email = fields.Char('И-мэйл')
	note = fields.Char(string='Талархлын утга')
	product_type = fields.Selection([
		('block','Евроблок'),
		('cement','Евроцемент'),
		('vendoor','Евровиндоор'),
		('venti','Евровенти'),
		('solution','Евросолюшн'),
		('mak','МАК Конкрит ')
	], string='Бүтээгдэхүүний төрөл', default=False, tracking=True)
	employee_id = fields.Many2one('hr.employee', string='Талархал хүлээн авсан ажилтан')
	department_id = fields.Many2one(related='employee_id.department_id', string='Талархал хүлээн авсан газар/нэгж', store=True, readonly=True)
	is_done = fields.Boolean(string='Талархал авсан ажилтан-д мэдээлэл өгсөн эсэх', default=False, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт')
	date_done = fields.Date(string='Огноо')

	def send_chat_employee(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_crm.mw_gratitude_action').id
		html = u'<b>Талархал.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=mw.gratitude&action=%s>%s</a></b>,- Таньд талархал ирлээ :D"""% (base_url, self.id, action_id, self.employee_id.name)
		self.env.user.send_chat(html, self.employee_id.partner_id)

	def unlink(self):
		for item in self:
			if item.state!='draft':
				raise UserError(('Ноорог төлөв дээр устгана.'))
		return super(MwGratitude, self).unlink()
	
	def action_draft(self):
		self.write({'state':'draft'})

	def action_done(self):
		self.is_done = True
		self.date_done = datetime.now()
		self.send_chat_employee()
		self.write({'state':'done'})	