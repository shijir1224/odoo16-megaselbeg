# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import date, datetime
from odoo.exceptions import UserError

class MwPodon(models.Model):
	_name = 'mw.podon'
	_desctiption = 'Поддон бүртгэл'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		seq = self.env['ir.sequence'].next_by_code('mw.podon')
		return seq

	name = fields.Char(string='Дугаар', readonly=True, copy=False, default=_default_name)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	other_expense_id = fields.Many2one('stock.product.other.expense', string='Шаардахын дугаар', ondelete='cascade', readonly=True, states={'draft':[('readonly',False)]}, copy=True)
	date = fields.Date('Огноо', readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string='Компани', required=True, default=lambda self: self.env.user.company_id, readonly=True, states={'draft':[('readonly',False)]})
	amount = fields.Float(string='Дүн', readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('mw.podon.line', 'podon_id', string='Поддон Lines', copy=True, readonly=True, states={'draft':[('readonly',False)]})
	podon_line_in_use_count = fields.Integer('Podon Line In Use тоо', compute='_compute_podon_line_in_use', readonly=True, states={'draft':[('readonly',False)]})
	podon_line_in_use_ids = fields.One2many('podon.line.in.use', 'podon_id', string='Podon Line Use IDs', readonly=True, states={'draft':[('readonly',False)]})
	partner_id = fields.Many2one('res.partner', string='Харилцагч', domain=[], readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар', readonly=True, states={'draft':[('readonly',False)]})
	employee_id = fields.Many2one('hr.employee', string='Нярав', readonly=True, states={'draft':[('readonly',False)]})

	def unlink(self):
		for item in self:
			if item.state=='done':
				raise UserError('Батлагдсан тул устгах боломжгүй!!!.')
		return super(MwPodon, self).unlink()

	def _compute_podon_line_in_use(self):
		qty = 0
		for line in self:
			qty = len(line.podon_line_in_use_ids)
		self.podon_line_in_use_count = qty or 0

	def view_podon_line_in_use(self):
		self.ensure_one()
		action = self.env.ref('mw_podon.action_podon_line_in_use').read()[0]
		action['domain'] = [('id','in',self.podon_line_in_use_ids.ids)]
		return action

	def action_podon_line_in_use(self):
		for item in self.line_ids:
			for row in range(int(item.quantity_available)):
				vals = {
					'podon_id': self.id,
					'product_id': item.product_id.id,
					'partner_id': item.partner_id.id,
					'date': datetime.now(),
					'quantity_available': 1,
					'company_id' : self.env.user.company_id.id,
					'branch_id': item.branch_id.id,
					'other_expense_id': item.podon_id.other_expense_id.id,
					'cost_price': item.cost_price,
					'amount': self.amount,
					# 'account_move_id': item.podon_id.other_expense_id.expense_picking_ids.move_ids and item.podon_id.other_expense_id.expense_picking_ids.move_ids.id,
				}
				item.env['podon.line.in.use'].create(vals)


	def action_to_done(self):
		self.write({'state': 'done'})
		self.action_podon_line_in_use()

	def action_to_draft(self):
		if self.podon_line_in_use_ids:
			raise UserError(u'Ашиглалт буй поддон үүссэн тул буцаах боломжгүй. Устгана уу!!!') 
		self.write({'state': 'draft'})


class MwPodonLine(models.Model):
	_name = 'mw.podon.line'
	_desctiption = 'Поддон бүртгэл line'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.onchange('product_id')
	def onchange_check_start(self):
		i = 0
		stock_quant = []
		for product in self:
			i
			stock_quant = self.env['stock.quant'].search([('product_id.name','=',self.product_id.name)])
			if stock_quant:
				for line in stock_quant:
					self.quantity_available += line.quantity
			i += 1

	name = fields.Char('Нэр')
	podon_id = fields.Many2one('mw.podon', string='Поддон ID', ondelete='cascade', readonly=True)
	state = fields.Selection(related='podon_id.state', string='Төлөв', readonly=True, store=True)
	product_id = fields.Many2one('product.product', string='Бараа', ondelete='cascade', required=True)
	quantity_available = fields.Float('Боломжтой тоо хэмжээ', readonly=True)
	uom_id = fields.Many2one(related='product_id.uom_id', string='Хэмжих нэгж', readonly=True)
	cost_price = fields.Float(string='Өртөг')
	partner_id = fields.Many2one(related='podon_id.partner_id', string='Харилцагч', store=True)
	branch_id = fields.Many2one(related='podon_id.branch_id', string='Салбар', store=True)
	employee_id = fields.Many2one(related='podon_id.employee_id', string='Нярав', store=True)


class StockProductOtherExpense(models.Model):
	_inherit = 'stock.product.other.expense'
		
	podon_id = fields.Many2one('mw.podon', string='Podon ID', copy=False, index=True)
	is_podon = fields.Boolean(related='transaction_value_id.is_podon', string='Поддон үүсгэх', store=True)
	podon_count = fields.Integer('Поддоны тоо', compute='_compute_podon')

	def _compute_podon(self):
		qty = 0
		for line in self:
			qty = len(line.podon_id)
		self.podon_count = qty or 0
	
	def view_podon(self):
		self.ensure_one()
		action = self.env.ref('mw_podon.action_mw_podon').read()[0]
		action['domain'] = [('id','=',self.podon_id.id)]
		return action
	
	def action_to_podon(self):
		if self.podon_id:
			raise UserError('Поддон үүссэн байна. Поддоны дэлгэрэнгүй дээрээс шалгана уу!!!.')
		else:
			for item in self:
				line_vals = []
				for line in item.product_expense_line:
					line_vals.append((0, None, {
						'product_id': line.product_id.id,
						'quantity_available': line.qty,
						'cost_price': line.product_standard_price,
					}))
				vals = {
					'other_expense_id': item.id,
					'date': self.date_required,
					'partner_id': self.partner_id and self.partner_id.id,
					'company_id': self.env.user.company_id.id,
					'line_ids': line_vals,
				}
				self.podon_id = self.env['mw.podon'].create(vals)

	def action_to_confirm(self):
		if self.transaction_value_id and self.transaction_value_id.is_podon:
			self.action_to_podon()
		res = super(StockProductOtherExpense, self).action_to_confirm()
		return res

class MnTransationValue(models.Model):
	_inherit = 'mn.transaction.value'

	is_podon = fields.Boolean(string='Поддон үүсгэх', default=False)