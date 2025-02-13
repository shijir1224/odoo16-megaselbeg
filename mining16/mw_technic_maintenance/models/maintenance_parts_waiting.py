# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class maintenancePartsWaitingLine(models.Model):
	_name = 'maintenance.parts.waiting.line'
	_description = 'Maintenance parts waiting line'

	parent_id = fields.Many2one('maintenance.parts.waiting', string='Parent ID')	
	product_id = fields.Many2one('product.product', string=u'Сэлбэг/Parts', required=True,)
	uom_id = fields.Many2one(related="product_id.uom_id", string=u'Хэмжих нэгж', readonly=True)
	qty = fields.Integer(string=u'Тоо ширхэг', required=True,)


class MaintenancePartsWaiting(models.Model):
	_name = 'maintenance.parts.waiting'
	_description = 'maintenance.parts.waiting'
	_order = 'date_start desc'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'confirmed':[('readonly', True)]})

	name = fields.Text(string=u'Тайлбар', copy=False, required=True,
		states={'confirmed':[('readonly', True)]} )
	
	date = fields.Datetime(string=u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_start = fields.Date(string=u'Эхлэх огноо', required=True, 
		states={'confirmed':[('readonly', True)]})
	date_end = fields.Date(string=u'Дуусах огноо', required=True, tracking=True, 
		states={'confirmed':[('readonly', True)]})
	
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,
		states={'confirmed':[('readonly', True)]})

	state = fields.Selection([
		('draft', u'Ноорог'),
		('confirmed', u'Баталсан'),], 
		default='draft', string=u'Төлөв', tracking=True)
	
	line_ids = fields.One2many('maintenance.parts.waiting.line', 'parent_id', string='Lines', copy=False,
		states={'confirmed': [('readonly', True)]})
	user_id = fields.Many2one('res.users', string=u'Хэрэглэгч', default=_get_user, readonly=True)

	technic_status = fields.Selection([
		('working', u'Ажиллаж хүлээх'),
		('stopped', u'Зогсож хүлээх'),], 
		default='working', string=u'Техникийн төлөв', tracking=True, required=True,
		states={'confirmed':[('readonly', True)]})

	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт')

	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(MaintenancePartsWaiting, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		self.state = 'draft'
	
	def action_to_confirm(self):
		self.user_id = self.env.user.id
		self.state = 'confirmed'