	# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class PodonLineInUse(models.Model):
	_name = 'podon.line.in.use'
	_desctiption = 'Ашиглалт буй поддон'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		seq = self.env['ir.sequence'].next_by_code('podon.line.in.use')
		return seq

	name = fields.Char(string='Дугаар', readonly=True, copy=False, default=_default_name)
	state = fields.Selection([('use', 'Ашиглалтанд байгаа'),('act', 'Актласан')], 'Төлөв', readonly=True, tracking=True, default='use')
	date = fields.Date('Огноо', readonly=True)
	product_id = fields.Many2one('product.product', string='Бараа' , required=True)
	partner_id = fields.Many2one('res.partner', string='Эзэмшигч', readonly=True)
	company_id = fields.Many2one('res.company', string='Компани', required=True, default=lambda self: self.env.user.company_id, readonly=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', readonly=True)
	other_expense_id = fields.Many2one('stock.product.other.expense', string='Шаардахын дугаар', ondelete='cascade', readonly=True)
	location = fields.Char('Байрлал')
	quantity_available = fields.Float('Боломжтой тоо хэмжээ', readonly=True)
	cost_price = fields.Float('Өртөг')
	amount = fields.Float('Барьцаа дүн')
	note = fields.Char('Тэмдэглэл')
	account_move_id = fields.Many2one('account.move', string='Санхүү бичилт', readonly=True)
	# account_move_ids = fields.One2many(related='podon_id.other_expense_id.move_ids', string='Санхүү бичилт', readonly=True)

	podon_id = fields.Many2one('mw.podon', string='Поддон ID', readonly=True, index=True)
	# podon_line_user_change_ids = fields.One2many('podon.line.use.transfer', 'podon_line_in_use_id', string='Шилжүүлэгүүд', readonly=True)	

	def action_to_act(self):
		self.write({'state': 'act'})

	def action_to_use(self):
		self.write({'state': 'use'})

class PodonUseTransfer(models.Model):
	_name = 'podon.use.transfer'
	_description = 'Podon Use Transfer'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	name = fields.Char(string='Нэр', readonly=True)
	stock_picking_id = fields.Many2one('stock.picking', string='Агуулахын баримт', ondelete='cascade', readonly=True)
	podon_line_use_transfer_ids = fields.One2many('podon.line.use.transfer', 'parent_id', string='Шилжүүлэгүүд', readonly=True)
	payment_id = fields.Many2one('payment.request', string='Холбоотой Төлбөрийн хүсэлт', readonly=True, index=True)
	payment_count = fields.Integer('Төлбөрийн хүсэлт тоо', compute='_compute_payment_count')


	def view_payment(self):
		self.ensure_one()
		action = self.env.ref('mw_account_payment_request.action_view_payment_request_my').read()[0]
		action['domain'] = [('id','=',self.payment_id.id)]
		return action

	def _compute_payment_count(self):
		qty = 0
		for line in self:
			qty = len(line.payment_id)
		self.payment_count = qty or 0


	def unlink(self):
		for item in self:
			if item.payment_id:
				raise UserError('Төлбөрийн хүсэлт үүссэн тул устгах боломжгүй!!!.')
		return super(PodonUseTransfer, self).unlink()

	def action_to_payment(self):
		if self.payment_id:
			raise UserError(u'Төлбөрийн хүсэлт үүссэн байна.')
		else:
			flow_id = self.env['dynamic.flow'].search([('model_id.model','=','payment.request')], order='sequence', limit=1)
			total_amount = sum(self.podon_line_use_transfer_ids.mapped('amount'))
			if not flow_id:
				raise UserError(u'Урсгал тохиргоо олдсонгүй.')
			for item in self:
				vals = {
					'flow_id': flow_id.id,
					'paid_date': datetime.now(),
					'description': 'Поддоны хүсэлт',
					'company_id': item.env.user.company_id.id,
					'amount': total_amount,
				}
				item.payment_id = item.env['payment.request'].create(vals)


class PodonLineUseTransfer(models.Model):
	_name = 'podon.line.use.transfer'
	_description = 'Podon Line Use Partner Change'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	name = fields.Char(string='Нэр', readonly=True)
	parent_id = fields.Many2one('podon.use.transfer', string='Поддоны шилжүүлэг', ondelete='cascade', readonly=True)
	podon_line_in_use_id = fields.Many2one('podon.line.in.use', string='Ашиглалтанд буй поддон', ondelete='cascade', readonly=True)
	product_id = fields.Many2one('product.product', string='Бараа', index=True, readonly=True)
	partner_id = fields.Many2one('res.partner', string='Одоогийн эзэмшигч', readonly=True)
	pre_partner_id = fields.Many2one('res.partner', string='Өмнөх эзэмшигч', readonly=True)
	date = fields.Date('Шилжүүлсэн огноо', readonly=True)
	company_id = fields.Many2one('res.company', string='Компани', required=True, readonly=True)
	amount = fields.Float('Барьцаа дүн')
	count = fields.Integer('Шилжүүлсэн поддоны тоо')


class PaymentRequest(models.Model):
	_inherit = 'payment.request'

	podon_ids = fields.One2many('podon.use.transfer', 'payment_id', string='Поддон бүртгэлүүд', copy=True)
	is_transfer = fields.Boolean(string='Шилжүүлсэн эсэх', default=False, compute='_compute_tranfer')


	@api.depends('bank_statement_line_id','tulugdsun_dun')
	def _compute_tranfer(self):
		for item in self.podon_ids:
			for line in item.podon_line_use_transfer_ids:
				line.podon_line_in_use_id.partner_id = line.pre_partner_id.id
				self.is_transfer = True

class AccountPaymentExpense(models.TransientModel):
	_inherit = 'account.payment.expense'


	# def action_create(self):
	# 	for item in self.payment_request_id.podon_ids:
	# 		for line in item.podon_line_use_transfer_ids:
	# 			line.podon_line_in_use_id.partner_id = line.pre_partner_id.id
	# 			self.is_transfer = True
	# 	res = super(AccountPaymentExpense, self).action_create()
	# 	return res


class StockPickingPodonLine(models.Model):
	_name = 'stock.picking.podon.line'
	_description = 'stock picking podon line'
	_rec_name = 'podon_line_in_use_id'

	podon_line_in_use_id = fields.Many2one('podon.line.in.use', string='Ашиглалтанд буй поддон', index=True, domain=[('state','=','use')])
	product_id = fields.Many2one(related='podon_line_in_use_id.product_id', string='Бараа', store=True)
	partner_id = fields.Many2one(related='podon_line_in_use_id.partner_id', string='Эзэмшигч', store=True)
	amount = fields.Float(related='podon_line_in_use_id.amount', string='Барьцаа дүн', store=True)
	stock_picking_id = fields.Many2one('stock.picking', string='Агуулахын баримт', ondelete='cascade', index=True)
	count = fields.Integer('Тоо хэмжээ', default=1, readonly=True)
	is_transfer = fields.Boolean(related='stock_picking_id.is_transfer', string='Шилжүүлэг хийгдсэн эсэх', readonly=True)

class StockPicking(models.Model):
	_inherit = "stock.picking"

	podon_use_transfer_count = fields.Integer('Поддон шилжүүлгийн тоо', compute='_compute_podon_use_transfer_count')
	podon_use_transfer_id = fields.Many2one('podon.use.transfer', string='Шилжүүлэг', readonly=True)
	stock_picking_podon_line_ids = fields.One2many('stock.picking.podon.line', 'stock_picking_id', string='Ашиглалтанд буй поддонүүд', copy=False, readonly=False, states={'done':[('readonly',True)]})
	is_transfer = fields.Boolean('Поддон Шилжүүлэг хийгдсэн эсэх', default=False, readonly=True)
	poddon_count = fields.Integer(string='Поддоны тоо', compute='_compute_poddon_count', readonly=True)

	

	@api.depends('stock_picking_podon_line_ids')
	def _compute_poddon_count(self):
		for item in self:
			item.poddon_count = len(item.stock_picking_podon_line_ids)

	def unlink(self):
		for item in self:
			if item.is_transfer:
				raise UserError('Шилжүүлэг хийгдсэн байна.!!!.')
		res = super(StockPicking, self).unlink()
		return res

	def action_change_partner(self):
		if self.podon_use_transfer_id:
				raise UserError(u'Поддон шилжүүлэг хийгдсэн байна\n Шилжүүлэг нь %s' % self.name)
		else:
			line_ids = []
			for item in self.stock_picking_podon_line_ids:
				line_vals = {
					'name': 'Поддон шилжүүлэг' + ' '+ self.name +' '+ 'Баримт',
					'podon_line_in_use_id': item.podon_line_in_use_id and item.podon_line_in_use_id.id,
					'product_id': item.podon_line_in_use_id.product_id and item.podon_line_in_use_id.product_id.id,
					'amount': item.amount if item.amount else 0,
					'company_id': item.env.user.company_id.id,
					'partner_id': item.stock_picking_id.partner_id and item.stock_picking_id.partner_id.id,
					'pre_partner_id': item.podon_line_in_use_id.partner_id and item.podon_line_in_use_id.partner_id.id,
					'date': datetime.now(),
					'count': item.count
				}
				line_ids.append((0, 0, line_vals))
				vals = {
					'stock_picking_id': self.id,
					'name': 'Поддон шилжүүлэг' + ' '+ self.name +' '+ 'Баримт',
					'podon_line_use_transfer_ids': line_ids,
				}
			transfer = self.env['podon.use.transfer'].create(vals)
			self.write({'podon_use_transfer_id': transfer.id})


	@api.depends('podon_use_transfer_id')
	def _compute_podon_use_transfer_count(self):
		for item in self:
			item.podon_use_transfer_count = len(item.podon_use_transfer_id)

	def view_podon_use_tranfser(self):
		self.ensure_one()
		action = self.env.ref('mw_podon.action_podon_use_transfer').read()[0]
		action['domain'] = [('id','=',self.podon_use_transfer_id.id)]
		return action