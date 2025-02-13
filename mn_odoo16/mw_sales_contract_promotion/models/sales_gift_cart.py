# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class MWSalesGiftCart(models.Model):
	_name = 'mw.sales.gift.cart'
	_description = 'Sales gift cart'
	_inherit = 'mail.thread'
	_order = 'date_start desc, partner_id'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	name = fields.Char(u'Дугаар', required=True, copy=True,
		states={'confirmed': [('readonly', True)]})
	date = fields.Datetime(u'Үүсгэсэн огноо', readonly=True, default=fields.Datetime.now(), copy=False)
	date_start = fields.Date(u'Эхлэх огноо', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)
	date_end = fields.Date(u'Дуусах огноо', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)

	partner_id = fields.Many2one('res.partner', u'Харилцагч', required=True,
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	description = fields.Char(u'Тайлбар', copy=True, required=True, 
		states={'confirmed': [('readonly', True)]})
	
	user_id = fields.Many2one('res.users', string=u'Үүсгэсэн', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string=u'Баталгаажуулсан', readonly=True)

	bonus_amount = fields.Float(string=u'Үнийн дүн', required=True, help=u'Хөнгөлөлтийн дүн',
		tracking=True)
	readonly_amount = fields.Boolean(string=u'Засагдахгүй', readonly=True, copy=False)
	state = fields.Selection([
			('draft', u'Ноорог'), 
			('confirmed', u'Батлагдсан'),
			('done', u'Дууссан'),
		], default='draft', required=True, string=u'Төлөв', tracking=True)

	# --------- OVERRIDED ----------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог бичлэг устгах боломжтой!'))
		return super(MWSalesGiftCart, self).unlink()

	# ---------- CUSTOM ------------
	def action_to_draft(self):
		self.state = 'draft'
		self.readonly_amount = False

	def action_to_confirm(self):
		if self.bonus_amount <= 0:
			raise UserError(_(u'Үнийн дүнг оруулна уу!'))
		self.state = 'confirmed'
		self.readonly_amount = True
		self.validator_id = self.env.user.id
		self.message_post(body=u"Баталсан %s" % self.validator_id.name)
