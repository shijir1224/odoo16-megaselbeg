# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenanceYearOtherExpense(models.Model):
	_name = 'maintenance.year.other.expense'
	_description = 'maintenance.year.other.expense'
	_order = 'date_year desc'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	name = fields.Char(string=u'Тайлбар', copy=False, required=True,
		states={'confirmed':[('readonly', True)]} )
	date = fields.Datetime(string=u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_year = fields.Date(string=u'Жил', required=True, 
		states={'confirmed':[('readonly', True)]})
	line_ids = fields.One2many('maintenance.year.other.expense.line', 'parent_id',
		string=u'Lines', copy=False,
		states={'confirmed':[('readonly', True)]})
	
	validator_id = fields.Many2one('res.users', string=u'Төлөвлөгч', readonly=True, copy=False,)
	state = fields.Selection([
		('draft', u'Draft'),
		('confirmed', u'Confirmed'),], 
		default='draft', string=u'Төлөв', tracking=True)

	@api.depends('line_ids')
	def _compute_total_amount(self):
		for obj in self:
			obj.total_amount = sum(obj.line_ids.mapped('amount'))
	total_amount = fields.Float(string='Нийт дүн', store=True, compute='_compute_total_amount')
	
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(MaintenanceYearOtherExpense, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		if not self.line_ids:
			raise UserError(_(u'Зарлагын мэдээллийг оруулна уу!'))
		self.state = 'confirmed'
		self.validator_id = self.env.user.id

class MaintenanceYearOtherExpenseLine(models.Model):
	_name = 'maintenance.year.other.expense.line'
	_description = 'maintenance.year.other.expense.line'

	parent_id = fields.Many2one('maintenance.year.other.expense', 'Parent ID', ondelete='cascade')
	name = fields.Char(string=u'Зарлагын нэр', required=True,)
	qty = fields.Float(string=u'Тоо хэмжээ', default=1, required=True,)
	amount = fields.Float(string=u'Дүн', default=0, required=True,)
