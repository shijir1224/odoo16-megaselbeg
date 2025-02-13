# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	initial_invoice_ids = fields.One2many('purchase.initial.invoice.line', 'order_id', string='Initial invoice lines')
	initial_invoice_amount_total_currency_invoiced = fields.Monetary(string='Нийт нэхэмжлэх/нэхэмжлэсэн дүн валютаар',
																	 compute='compute_initial_invoice_amount_total')
	initial_invoice_amount_total_invoiced = fields.Monetary(string='Нийт нэхэмжлэх/нэхэмжлэсэн дүн',
															compute='compute_initial_invoice_amount_total')
	possible_invoice_amount_currency = fields.Monetary(string='Боломжит урьдчилгаа дүн',
													   compute='compute_initial_invoice_amount_total')

	

	@api.depends('initial_invoice_ids')
	def compute_initial_invoice_amount_total(self):
		for obj in self:
			initial_invoice = obj.initial_invoice_ids.filtered(lambda l: l.state == 'payment_request_created')
			obj.initial_invoice_amount_total_currency_invoiced = sum(initial_invoice.mapped('amount'))
			obj.initial_invoice_amount_total_invoiced = sum(initial_invoice.mapped('amount_total'))
			obj.possible_invoice_amount_currency = obj.amount_total - sum(initial_invoice.mapped('amount'))
			for move in self:
				if move.initial_invoice_ids:
					mm_amount=0
					pr_id = self.env['payment.request'].search([('id', '=', move.initial_invoice_ids.payment_request_id.ids)])
					for pr_ids in pr_id:
						# print('==============',pr_ids.amount)
						mm_amount += pr_ids.amount
						move.possible_invoice_amount_currency = move.amount_total - mm_amount
			# self.amount=self.invoice_amount_residual if self.amount == 0 else self.amount
	# def create_invoice_hand(self):
	# 	for initial in self.mapped('initial_invoice_ids').filtered(lambda l: l.state != 'draft'):
	# 		initial.action_create_invoice()
	# 	return super(PurchaseOrder, self).create_invoice_hand()

	def action_cancel_stage(self):
		res = super(PurchaseOrder, self).action_cancel_stage()
		if self.initial_invoice_ids.filtered(lambda r: r.tulugdsun_dun > 0):
			raise UserError('Урьдчилгаа төлбөр төлөгдсөн байна!')
		return res

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	is_invoice_line = fields.Boolean(default=False)
	is_line_invoiced = fields.Boolean(default=False)
	initial_invoice_line_id = fields.Many2one('purchase.initial.invoice.line', string='Initial invoice line',
											  ondelete='cascade', copy=False)

	def compute_price_unit_stock_move(self):
		order_ids = self.mapped('order_id')
		for order_id in order_ids:
			if order_id.initial_invoice_amount_total_currency_invoiced:
				lines = self.filtered(lambda l: not l.is_invoice_line and l.order_id == order_id)
				if len(lines):
					per_line_total = order_id.initial_invoice_amount_total_invoiced
					per_line_total_curr = order_id.initial_invoice_amount_total_currency_invoiced
				else:
					per_line_total = 0
					per_line_total_curr = 0
				real_total = (order_id.amount_total - per_line_total_curr) * order_id.current_rate + per_line_total
				rate = real_total / order_id.amount_total if order_id.amount_total else 1
				for line in self.filtered(lambda l: l.order_id == order_id):
					if line.id in lines.ids:
						line.price_unit_stock_move = line._get_stock_move_price_unit(rate)
						line.price_unit_product = line.price_unit_stock_move - line.cost_unit
					else:
						line.price_unit_stock_move = 0
						line.price_unit_product = 0
			else:
				super(PurchaseOrderLine, self).compute_price_unit_stock_move()

	@api.ondelete(at_uninstall=False)
	def _unlink_except_purchase_or_done(self):
		for line in self:
			if line.product_id.id != line.company_id.purchase_down_payment_product_id.id:
				return super(PurchaseOrderLine, self)._unlink_except_purchase_or_done()

	def get_payment_request_line_data(self):
		res = super(PurchaseOrderLine, self).get_payment_request_line_data()
		if self.product_id.id == self.company_id.purchase_down_payment_product_id.id:
			res['qty'] = -1
		return res

	@api.model
	def create(self, vals):
		"""
		Худалдан авалтын мөрийн бараа урьдчилгаа төлбөртэй бараа бол хуулбарлан үүсэхгүй байх
		"""
		if vals.get('product_id') == self.env.company.purchase_down_payment_product_id.id and not vals.get('initial_invoice_line_id'):
			return self.env[self._name]
		return super(PurchaseOrderLine, self).create(vals)
