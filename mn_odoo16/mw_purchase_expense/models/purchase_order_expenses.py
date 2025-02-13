# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from datetime import date
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

PORTION_SELECTION = [
		('weight', 'Weight'),
		('volume', 'Volume'),
		('price', 'Unit Price'),
		('subtotal', 'Total')
	]

class PurchaseOrderExpenses(models.Model):
	_name = 'purchase.order.expenses'
	_description = 'Purchase Expenses Mapping'

	order_id = fields.Many2one('purchase.order', 'Order id', ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Product of expenses', domain=[('type', '=', 'service')])
	partner_id = fields.Many2one('res.partner', 'Partner')
	amount = fields.Float('Amount of expenses', default=0.0, digits=dp.get_precision('Product Price'))
	current_amount = fields.Float('Basic total', default=0.0, digits=dp.get_precision('Product Price'))
	currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id.id)
	company_currency_id = fields.Many2one('res.currency', related='order_id.company_id.currency_id')
	is_foreign_currency = fields.Boolean(string='Гадаад валют эсэх', compute='compute_is_company_currency')
	portion_method = fields.Selection(PORTION_SELECTION, 'Allocation Method', default='subtotal')
	purchase_lines = fields.Many2many('purchase.order.line', 'po_expenses_line_rel', 'prod_id', 'line_id', 'Allocate lines')
	taxes_id = fields.Many2many('account.tax', 'po_expenses_taxes_rel', 'prod_id', 'tax_id', 'Taxes',
								domain=[('type_tax_use', '=', 'purchase')])
	notes = fields.Text('Notes')
	invoice_id = fields.Many2one('account.move', 'Invoice')
	expense_type = fields.Selection([('transport', 'Transport'), ('customs', 'Customs'), ('other', 'Other')], 'Expense type')
	is_without_cost = fields.Boolean('Not included in the cost /VAT../', default=False)
	in_cost = fields.Boolean('Costing /Foreign Transport../', default=False)
	out_cost = fields.Boolean('Exclude those included in the cost /Customs tax../', default=False)
	date_cur = fields.Date('Exchange rate date', default=fields.Date.context_today)
	invoice_ref = fields.Char('Invoice number')
	current_cur = fields.Float('Estimated exchange rate')

	@api.onchange('currency_id')
	def compute_is_company_currency(self):
		for obj in self:
			obj.is_foreign_currency = obj.currency_id != obj.company_currency_id

	# @api.onchange('currency_id')
	# def onchange_currency_id(self):
	# 	for obj in self:
	# 		obj.date_cur = False
	# 		obj.current_cur = False
	@api.onchange('date_cur')
	def onchange_currency_rate(self):
		for expense in self:
			for i in expense.currency_id:
				rate_id = expense.env["res.currency.rate"].search([("currency_id", "=", i.id),("name", "=", expense.date_cur)])
			for rate_m in rate_id:
				rate = rate_m.company_rate 
				expense.current_cur = rate
				expense.current_amount  = expense.amount * rate
	# @api.constrains('date_cur', 'is_foreign_currency', 'current_cur')
	# def check_date_cur(self):
	#	 for obj in self:
	#		 if obj.is_foreign_currency and (not obj.date_cur or not obj.current_cur):
	#			 error = '{0} ХА дээрх {1} харилцагчийн нэмэлт зардал гадаад валюттай боловч огноо эсвэл ханш байхгүй байна: Үнийн дүн: {2}'.format(
	#				 obj.order_id.name, obj.partner_id.name, obj.amount)
	#			 raise ValidationError(error)

	# @api.depends('amount', 'current_amount')
	# def _compute_current_cur(self):
	# 	for item in self:
	# 		if item.amount != 0:
	# 			item.current_cur = item.current_amount / item.amount
	# 		else:
	# 			item.current_cur = 0

	def get_po_id(self):
		if self.order_id:
			return self.order_id

	def get_invoice_values(self, journal_id, partner, company_id, currency_id, n):
		# purchase_order = self.mapped('order_id')[0]
		purchase_order = (self.order_id and self.order_id) \
			or (self.purchase_lines and self.purchase_lines[0].order_id)\
			 or (self.add_cost_id.po_line_ids and self.add_cost_id.po_line_ids[0].order_id)
			 
		invoice_line = [purchase_order._prepare_invoice_line_from_expense_line(expense_line) for expense_line in self]
		for exp in self:
			mmm_date = exp.date_cur
		# print('finally:', invoice_line)
		return {
			'name': '/',
			'ref': 'Exp: ' + currency_id.display_name + ' - ' + purchase_order.name + ':' + str(n),
			'move_type': 'in_invoice',
			'partner_id': partner.id,
			'journal_id': journal_id.id or False,
			'invoice_origin': purchase_order.name,
			'invoice_line_ids': invoice_line,
			'company_id': company_id.id,     
			'invoice_date': mmm_date or date.today(),
			'date': mmm_date or date.today(),
			'user_id': self.env.user.id,
			'currency_id': currency_id.id
		}

class AccountMove(models.Model):
	_inherit = 'account.move'

	purchase_order_expenses = fields.One2many('purchase.order.expenses', 'invoice_id', string='Additional')
	