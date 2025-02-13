# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta

class mw_feedback(models.Model):
	_name = 'mw.feedback'
	_inherit = ['mail.thread','mail.activity.mixin']
	_description = 'Санал гомдол'
	
	name = fields.Char('Нэр', tracking=True)
	desc = fields.Text('Тайлбар', tracking=True)
	partner_name = fields.Char('Харилцагчийн нэр', tracking=True)
	partner_phone = fields.Char('Утас', tracking=True)
	user_id = fields.Many2one('res.users', string='Гомдол хүлээн авах ажилтан')
	priority = fields.Integer('Урьтамж', default=1)
	state = fields.Selection([
		('draft','Шинэ'),
		('processing','Хүлээгдэж буй'),
		('done','Шийдвэрлэгдсэн'),
		('cancel','Цуцлагдсан')
	], string='Төлөв', default='draft', tracking=True )
	type = fields.Selection([
		('lavlagaa','Лавлагаа'),
		('sanal','Санал'),
		('gomdol','Гомдол')
	], string='Төлөв', default='lavlagaa', tracking=True, required=True)
	date_start = fields.Date(string='Хаагдах огноо', tracking=True)
	is_done = fields.Boolean('Шийдвэрлэгдсэн эсэх', default=False)
	date_end = fields.Date(string='Шийдвэрлэгдсэн огноо', tracking=True)
	date_return = fields.Date(string='Эргэж холбоо барих огноо', tracking=True)
	type_id = fields.Many2one('mw.feedback.type', string='Гомдлын төрөл')
	cause_id = fields.Many2one('mw.feedback.cause', string='Шалтгаан')
	priority_id = fields.Many2one('mw.feedback.priority', string='Гомдлын зэрэглэл')
	partner_id = fields.Many2one('res.partner', string="Харилцагч")
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт')



	def action_draft(self):
		self.write({'state':'draft'})

	def action_processing(self):
		self.write({'state':'processing'})

	def action_done(self):
		self.date_end = datetime.now()
		self.write({'state':'done'})

class mw_feedback_type(models.Model):
	_name = 'mw.feedback.type'
	_description = 'Санал гомдол төрөл'
	_order = 'name'
	name = fields.Char('Төрөл', required=True)

class mw_feedback_cause(models.Model):
	_name = 'mw.feedback.cause'
	_description = 'Санал гомдол шалтгаан'
	_order = 'name'
	name = fields.Char('Шалтгаан',  required=True)

class mw_feedback_priority(models.Model):
	_name = 'mw.feedback.priority'
	_description = 'Санал гомдол Урьтамж'
	_order = 'name'

	name = fields.Char('Урьтамж',  required=True)
