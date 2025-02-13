# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	po_type = fields.Selection([('internal', 'Дотоод'), ('foreign', 'Гадаад')], 'Төрөл', default='internal')
	date_currency = fields.Date('Currency rate date', states={'done': [('readonly', True)]}, default=fields.Datetime.now())
	current_rate = fields.Float('Current rate', readonly=False, store=True)
	expenses_line = fields.One2many('purchase.order.expenses', 'order_id', 'Expenses line',
									states={'done': [('readonly', True)]}, copy=False)
	amount_expenses = fields.Monetary(string='Total expenses', store=True, readonly=True,
									  compute='_amount_expenses_all', currency_field='company_currency_id',
									  tracking=True)
	amount_expenses_in = fields.Monetary(string='Total expenses allocated', readonly=True, store=True,
										 compute='_amount_expenses_all', currency_field='company_currency_id',
										 tracking=True)
	company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
										  help='Utility field to express amount currency')
	amount_expenses_po_tot2 = fields.Monetary(string='Total expenses', store=True, readonly=True,
											  compute='_amount_expenses_all', currency_field='company_currency_id',
											  tracking=True)

	@api.depends('currency_id', 'date_currency', 'state')
	@api.onchange('currency_id', 'date_currency', 'state')
	def _compute_current_rate(self):
		for item in self:
			date_order = item.date_currency or fields.Datetime.now()
			rr = self.env['res.currency']._get_conversion_rate(item.currency_id, item.company_id.currency_id,
															   item.company_id, date_order)
			item.current_rate = rr

	# @api.onchange('date_currency')
	# def onchange_date_currency(self):
	#     for item in self.expenses_line:
	#         item.date_cur = self.date_currency
	#     self.make_expenses()

	def button_approve(self, force=False):
		self.make_expenses()
		return super(PurchaseOrder, self).button_approve(force)

	@api.depends('order_line.invoice_lines.move_id', 'expenses_line.invoice_id')
	def _compute_invoice(self):
		for order in self:
			super(PurchaseOrder, order)._compute_invoice()
			invoices = order.expenses_line.mapped('invoice_id')
			order.invoice_ids = order.invoice_ids | invoices
			order.invoice_count = len(order.invoice_ids)

	@api.depends('expenses_line.amount')
	def _amount_expenses_all(self):
		for order in self:
			amount_expenses = 0.0
			amount_expenses_in = 0.0
			for line in order.expenses_line:
				from_currency = line.currency_id
				to_currency = order.company_currency_id
				if from_currency == to_currency:
					current_amount = line.amount
				else:
					current_amount = line.amount * line.current_cur
				line.sudo().current_amount = line.taxes_id.compute_all(current_amount, currency=to_currency, quantity=1.0)['total_excluded']
				amount_expenses += line.current_amount
				if not line.is_without_cost:
					amount_expenses_in += line.current_amount

			order.update({
				'amount_expenses': order.currency_id.round(amount_expenses),
				'amount_expenses_in': order.currency_id.round(amount_expenses_in),
				'amount_expenses_po_tot2': sum(order.order_line.mapped('total_cost_unit')),
			})

	# def make_portion(self, method, lines, amount, date_current, expenses_line_id):
	#     portion_dict = {}
	#     total = 0.0
	#     # Зардлыг хуваарилах
	#     from_currency = self.currency_id
	#     to_currency = self.company_currency_id
	#
	#     currency_obj = self.env['res.currency']
	#
	#     # if method == 'price':
	#     #     for line in lines:
	#     #         total += line.price_unit
	#     #     coff = 0
	#     #     if total:
	#     #         coff = (amount / total)
	#     #     for line in lines:
	#     #         product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
	#     #         if from_currency and to_currency:
	#     #             cur_price_unit = currency_obj.with_context(date=date_current)._compute(from_currency, to_currency, line.price_unit)
	#     #         else:
	#     #             cur_price_unit = line.price_unit
	#     #         portion_dict[line.id] = round((cur_price_unit * coff) / product_uom_qty, 2)
	#     current_amount = expenses_line_id.current_amount
	#     if method == 'price':
	#         tot_w = sum(lines.mapped('price_unit'))
	#         for line in lines:
	#             tot_w_amount = 0
	#             if tot_w > 0:
	#                 tot_w_amount = current_amount * line.price_unit / tot_w
	#             portion_dict[line.id] = tot_w_amount
	#
	#     elif method == 'subtotal':
	#         for line in lines:
	#             product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
	#             price_unit = line._get_stock_move_price_unit_unit()
	#             price_total = product_uom_qty * price_unit
	#
	#             cost_unit = current_amount
	#             coff = 0
	#             if price_total:
	#                 coff = (price_total / amount)
	#             portion_dict[line.id] = cost_unit * coff
	#
	#     elif method == 'volume':
	#         for line in lines:
	#             product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
	#             total += (line.product_id.volume or 1) * product_uom_qty
	#
	#         for line in lines:
	#             product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
	#             line_res = ((current_amount / total) * (
	#                         (line.product_id.volume or 1) * product_uom_qty)) / product_uom_qty
	#             portion_dict[line.id] = line_res * product_uom_qty
	#     elif method == 'weight':  # weight
	#         tot_w = sum(lines.mapped('subtotal_weight'))
	#         for line in lines:
	#             tot_w_amount = 0
	#             if tot_w > 0:
	#                 tot_w_amount = current_amount * line.subtotal_weight / tot_w
	#             portion_dict[line.id] = tot_w_amount
	#     else:
	#         # Зардлыг өртөгт хуваарилахгүй
	#         pass
	#
	#     return portion_dict

	def _prepare_invoice_line_from_expense_line(self, line):
		qty = 1
		taxes = line.taxes_id
		po_id = line.get_po_id() or line.order_id
		invoice_line_tax_ids = po_id.fiscal_position_id.map_tax(taxes)
		invoice_line = self.env['account.move.line']
		journal_obj = self.env['account.journal']
		journal_id = journal_obj.search([('type', '=', 'purchase'), ('company_id', '=', po_id.company_id.id)], limit=1)
		if not journal_id:
			raise UserError(_('There is no purchase journal defined for this company: "%s" (id:%d)') % (po_id.company_id.name, po_id.company_id.id))
		data = {
			'name': po_id.name + ': Expense ' + line.portion_method,
			'product_uom_id': line.product_id.uom_id.id,
			'product_id': line.product_id.id,
			'price_unit': line.amount,  # tuhain valutaar uusgeh
			'quantity': qty,
			'discount': 0.0,
			'tax_ids': invoice_line_tax_ids.ids
		}
		return 0, False, data

	def create_expense_invoice(self):
		self.create_expense_invoice_hand(self.expenses_line, self.company_id, self.name)

	def create_expense_invoice_hand(self, expenses_line, company_id, name):
		expense_to_invoice = expenses_line.filtered(lambda r: not r.invoice_id or r.invoice_id.state == 'cancel')
		journal_id = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', company_id.id)],
														limit=1, order='id')
		n = 1
		for partner in list(set(expense_to_invoice.mapped('partner_id'))):
			partner_expense = expense_to_invoice.filtered(lambda r: r.partner_id.id == partner.id)
			for currency in list(set(partner_expense.mapped('currency_id'))):
				p_currency_expense = partner_expense.filtered(lambda r: r.currency_id.id == currency.id)
				for cur_date in list(set(p_currency_expense.mapped('date_cur'))):
					cur_expenses = p_currency_expense.filtered(lambda r: r.date_cur == cur_date)
					inv_vals = cur_expenses.get_invoice_values(journal_id, partner, company_id, currency, n)
					n += 1
					created_invoice = self.env['account.move'].create(inv_vals)
					for inv_line in created_invoice.invoice_line_ids:
						for expense_line in cur_expenses:
							if expense_line.is_without_cost:
								prod_accounts = inv_line.product_id.product_tmpl_id.with_company(self.company_id)._get_product_accounts()
								account = prod_accounts['expense']
								if account:
									inv_line.account_id = account
								else:
									raise UserError('Өртөгд оруулахгүй барааны дансны тохиргоо байхгүй байна.')
							else:
								prod_accounts = inv_line.product_id.product_tmpl_id.with_company(self.company_id)._get_product_accounts()
								account = prod_accounts['expense']
								if account:
									inv_line.account_id = account
								else:
									raise UserError('Бараа ангилал дээр данс байхгүй байна.')
					created_invoice.action_post()
					cur_expenses.write({'invoice_id': created_invoice.id})

	def make_expenses(self):
		self.order_line.update({'cost_unit': 0})
		for line in self.order_line.filtered(lambda l: l.product_qty > 0):
			# Урвуу хэлбэрээр өртөг тооцоолох хэсгийг шинэчлэв
			self.expense_per_line(line)
		self._amount_expenses_all()

	def expense_per_line(self, line):
		portion_methods = list(set(self.expenses_line.mapped('portion_method')))
		sum_for_line = 0
		product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
		for method in portion_methods:
			method_lines = self.expenses_line.filtered(lambda r: not r.is_without_cost and r.portion_method == method and (not r.purchase_lines or line.id in r.purchase_lines.ids))
			for expense_line in method_lines:
				current_amount = expense_line.current_amount
				lines = expense_line.purchase_lines if expense_line.purchase_lines else self.order_line
				if method == 'price':
					sum_for_line += current_amount * line.price_unit / sum(lines.mapped('price_unit'))
				elif method == 'subtotal':
					sum_for_line += (current_amount / self.get_total_amount_currency(lines)) * self.get_total_amount_currency(line)
				elif method == 'volume':
					total_volume = sum([(line.product_id.volume or 1) * line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) for line in lines])
					line_res = ((current_amount / total_volume) * ((line.product_id.volume or 1) * product_uom_qty)) / product_uom_qty
					sum_for_line += line_res * product_uom_qty
				elif method == 'weight':  # weight
					tot_w = sum(lines.mapped('subtotal_weight'))
					tot_w_amount = current_amount * line.subtotal_weight / tot_w if tot_w else 1
					sum_for_line += tot_w_amount
				elif method == 'qty':
					sum_for_line += expense_line.current_amount * line.product_uom_qty / sum(lines.mapped('product_uom_qty'))
		line.cost_unit = sum_for_line / product_uom_qty

	def get_total_amount_currency(self, lines):
		sum_amount = 0
		for line in lines.filtered(lambda l: l.product_qty > 0):
			price_unit = line.price_unit
			if self.currency_id != self.company_id.currency_id:
				price_unit *= self.current_rate
			sum_amount += price_unit * line.product_qty
		return sum_amount

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	cost_unit = fields.Float(string='Amount of expenses', readonly=True, copy=False, digits=dp.get_precision('Product Price'))
	total_cost_unit = fields.Float(string='Total Expenses', readonly=True, digits=dp.get_precision('Product Price'),
								   compute='_compute_total_cost_unit')
	price_unit_product = fields.Float(string='Basic cost of product', compute='compute_price_unit_stock_move',
									  readonly=True, digits=dp.get_precision('Product Price'))
	price_unit_stock_move = fields.Float(string='Нэгж өртөг', compute='compute_price_unit_stock_move', readonly=True,
										 digits=dp.get_precision('Product Price'))
	company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
										  help='Utility field to express amount currency')

	def name_get(self):
		res = []
		string_name = ''
		for item in self:
			if item.product_id.default_code:
				string_name = '[' + item.product_id.default_code + '] ' + item.name
			res.append((item.id, string_name))
		return res

	@api.depends('cost_unit', 'product_qty', 'product_uom')
	def _compute_total_cost_unit(self):
		for item in self:
			item.total_cost_unit = item.cost_unit * item.product_uom_qty

	@api.depends('price_unit', 'product_id', 'taxes_id', 'order_id.date_currency', 'order_id.currency_id', 'cost_unit',
				 'order_id.current_rate')
	@api.onchange('price_unit', 'product_id', 'taxes_id', 'order_id.date_currency', 'order_id.currency_id', 'cost_unit',
				  'order_id.current_rate')
	def compute_price_unit_stock_move(self):
		for line in self:
			line.price_unit_stock_move = line._get_stock_move_price_unit()
			line.price_unit_product = line.price_unit_stock_move - line.cost_unit

	def get_date_currency(self):
		# return self.order_id.date_currency
		if self.add_cost_ids:
			return self.add_cost_ids[0].current_rate
		return self.order_id.current_rate

	def _get_stock_move_price_unit(self, rate=False):
		self.ensure_one()
		line = self[0]
		order = line.order_id
		price_unit = line.price_unit
		if line.taxes_id:
			price_unit = \
			line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id,
																quantity=1.0, product=line.product_id,
																partner=line.order_id.partner_id)['total_excluded']
		if line.product_uom.id != line.product_id.uom_id.id:
			if line.product_id.uom_id.factor != 0:
				price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
		if order.currency_id != order.company_id.currency_id:
			# from_currency = order.currency_id
			# to_currency = order.company_currency_id
			# price_unit = self.env['res.currency'].with_context(date=self.get_date_currency())._compute(from_currency, to_currency, price_unit, round=False)
			# price_unit = price_unit * (rate if rate else order.current_rate)
			price_unit = price_unit * self.get_date_currency()
		if line.cost_unit:
			price_unit = price_unit + line.cost_unit
		return price_unit

	# def _get_stock_move_price_unit_unit(self):
	#     self.ensure_one()
	#     line = self[0]
	#     order = line.order_id
	#     price_unit = line.price_unit
	#     if line.taxes_id:
	#         price_unit = line.taxes_id.with_context(round=False).compute_all(
	#             price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id,
	#             partner=line.order_id.partner_id
	#         )['total_excluded']
	#     if line.product_uom.id != line.product_id.uom_id.id:
	#         price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
	#     if order.currency_id != order.company_id.currency_id:
	#         from_currency = order.currency_id
	#         to_currency = order.company_currency_id
	#         price_unit = self.env['res.currency'].with_context(date=self.get_date_currency())._compute(from_currency,
	#                                                                                                    to_currency,
	#                                                                                                    price_unit,
	#                                                                                                    round=False)
	#
	#     return price_unit
