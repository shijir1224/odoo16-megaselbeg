# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date

class PurchaseInitialInvoiceLine(models.Model):
	_name = 'purchase.initial.invoice.line'
	_description = 'Purchase initial invoice line'

	def default_date(self):
		return date.today()
	payment_state = fields.Selection([
        ('draft', 'Үүсээгүй'),
        ('created', 'Үүссэн'),
    ], string="Line state", default='draft')
	order_id = fields.Many2one('purchase.order', string='Order', ondelete='cascade', required=True)
	name = fields.Char(string='Description', required=True)
	date = fields.Date(string='Date', required=True, default=default_date)
	currency_rate = fields.Float(string='Currency rate')
	amount = fields.Float(string='Currency amount')
	amount_total = fields.Float(string='amount total', compute='compute_amount_total')
	tulugdsun_dun = fields.Float(related='payment_request_id.tulugdsun_dun', string='Төлөгдсөн дүн')
	state = fields.Char(string="Төлөв", compute='compute_state')
	payment_request_id = fields.Many2one('payment.request', string='Payment request', ondelete='restrict',
										 readonly=True)
	request_state = fields.Char(related='payment_request_id.state')
	account_id = fields.Many2one(related='payment_request_id.ex_account_id', string='Төлбөрийн хүсэлтийн харьцсан данс')
	payment_move_id = fields.Many2one(related='payment_request_id.bank_statement_line_id.move_id',
									  string='Хүсэлтийн бичилт')
	rel_move_id = fields.Many2one('account.move', string='Хүсэлт нэхэмжлэх хоорондын бичилт')
	invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade')
	invoice_status = fields.Selection(related='invoice_id.state', string='Invoice status')
	currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
	company_id = fields.Many2one(related='order_id.company_id')
	purchase_order_line_id = fields.Many2one('purchase.order.line', string='PO line', ondelete='restrict')
	color_info = fields.Text(string='Сануулга', readonly=True, default='Огноо нь засагдахгүй бөгөөд төлбөр гарсан огноогоор шинэчлэгдэж валют өөрчлөгдөнө шүү')
	partner_id = fields.Many2one('res.partner', string="Харилцагч", related='order_id.partner_id')
	@api.depends('payment_request_id')
	def compute_state(self):
		for expense in self:
			expense.state  = expense.payment_request_id.flow_line_id.stage_id.name

	@api.depends('date', 'currency_id')
	@api.onchange('date', 'currency_id')
	def change_currency_rate(self):
		for obj in self:
			date_order = obj.date or date.today()
			current_currency = obj.currency_id or obj.order_id.currency_id
			obj.currency_rate = self.env['res.currency']._get_conversion_rate(current_currency,
																			  obj.company_id.currency_id,
																			  obj.company_id, date_order)

	@api.onchange('amount', 'currency_rate')
	@api.depends('amount', 'currency_rate')
	def compute_amount_total(self):
		for obj in self:
			obj.amount_total = obj.currency_rate * obj.amount

	def prepare_invoice_vals(self):
		invoice_vals = self.order_id._prepare_invoice()
		invoice_vals.update({'date': date.today(),
							 'ref': self.name,
							 'invoice_date_due': date.today(),
							 'invoice_date': date.today(),
							 'currency_id': self.currency_id.id})
		# if self.currency_id.id != self.company_id.currency_id.id:
		# 	invoice_vals.update({'rate_manual': True,
		# 						 'rate_manual_amount': self.currency_rate})
		return invoice_vals

	def to_cancel(self):
		return self.write({'state': 'cancelled'})

	def to_invoice_created(self):
		return self.write({'state': 'invoice_created'})

	def check_initial_invoice_line(self):
		self.ensure_one()
		if self.order_id.possible_invoice_amount_currency < self.amount:
			raise UserError(_('Prepayment amount total has exceeded PO amount total'))
		if not self.company_id.purchase_down_payment_product_id:
			raise UserError(_('Please choose Down payment product on purchase settings'))
		if self.amount_total <= 0:
			raise UserError(_('Amount total is required'))

	def button_create_payment_request(self):
		self.check_initial_invoice_line()
		# create order line
		# order_line_initial = self.env['purchase.order.line'].with_context(from_comparison=True).create(self.get_purchase_order_line_vals())
		# order_line_initial.product_qty = 0  # Тоо хэмжээ 0 бол үүсэхгүй байсан
		payment_request_id = self.env['payment.request'].create(self.get_payment_request_vals())
		self.env['payment.request.desc.line'].create(self.get_payment_request_line_vals(payment_request_id))
		self.write({'payment_request_id': payment_request_id.id,
					'payment_state': 'created'})

	def get_payment_request_vals(self):
		if self.amount > self.order_id.possible_invoice_amount_currency:
			raise UserError('Төлбөр хүсэх дүн их байх боломжгүй.')
		return {
			'flow_id': self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request')], order='sequence', limit=1).id,
			'amount': self.amount,
			'currency_id': self.currency_id.id,
			'partner_id': self.order_id.partner_id.id,
			'purchase_ids': [(4, self.order_id.id)],
			'purchase_initial_invoice_line': self.id,
		}

	def get_payment_request_line_vals(self, payment_request_id):
		return {
			'payment_request_id': payment_request_id.id,
			'name': self.order_id.name + ' ' + self.name,
			'qty': 1,
			'price_unit': self.amount
		}

	def get_purchase_order_line_vals(self):
		product = self.company_id.purchase_down_payment_product_id
		return {'order_id': self.order_id.id,
				'product_id': product.id,
				'price_unit_without_discount': self.amount,
				'price_unit': self.amount,
				'is_invoice_line': True,
				'initial_invoice_line_id': self.id,
				'product_uom': product.uom_id.id,
				'name': product.name,
				'display_type': False,
				'date_planned': self.order_id.date_planned,
				'product_qty': 1}

	# def action_create_invoice(self):
	# 	self.ensure_one()
	# 	if self.invoice_id:
	# 		return
	# 	# create invoice
	# 	invoice_vals = self.prepare_invoice_vals()
	# 	for line_id in self:
	# 		line_vals = line_id.purchase_order_line_id._prepare_account_move_line()
	# 	line_vals['name'] = self.name
	# 	line_vals['quantity'] = 1
	# 	invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
	# 	invoice_vals['purchase_initial_invoice_line_id'] = self.id
	# 	invoice_id = self.env['account.move'].create(invoice_vals)
	# 	invoice_id.action_post()
	# 	# create payment request
	# 	self.write({'invoice_id': invoice_id.id})
	# 	self.link_pre_payment_and_invoice()
	# 	self.to_invoice_created()

	def link_pre_payment_and_invoice(self):
		self.ensure_one()
		if self.request_state not in ['accountant', 'done']:
			raise UserError('{0} ХА-н {1} урьдчилгаа төлбөр төлөгдөөгүй байна'.format(self.order_id.name, self.name))
		self.payment_request_id.move_id = self.invoice_id
		account_move = self.env['account.move'].create(self.get_link_rel_move_vals())
		account_move.action_post()
		self.invoice_id.js_assign_outstanding_line(account_move.line_ids.filtered(lambda l: l.debit > 0)[0].id)
		self.rel_move_id = account_move

	def get_link_rel_move_vals(self):
		name = '{0} ХА-н {1} урьдчилгаанаас үүссэн'.format(self.order_id.name, self.name)
		res = {'line_ids': [(0, 0, {'name': name,
									'account_id': self.invoice_id.partner_id.property_account_payable_id.id,
									'currency_id': self.currency_id.id,
									'amount_currency': self.amount,
									'partner_id': self.order_id.partner_id.id,
									'debit': self.amount_total}),
							(0, 0, {'name': name,
									'account_id': self.account_id.id,
									'amount_currency': -self.amount,
									'currency_id': self.currency_id.id,
									'partner_id': self.order_id.partner_id.id,
									'credit': self.amount_total})],
			   'move_type': 'entry',
			   'partner_id': self.order_id.partner_id.id,
			   'journal_id': self.invoice_id.journal_id.id,
			   'currency_id': self.currency_id.id,
			   }
		# if self.currency_id.id != self.company_id.currency_id.id:
		# 	res.update({'rate_manual': True,
		# 				'rate_manual_amount': self.currency_rate})
		return res

	def unlink(self):
		for obj in self:
			if obj.state == 'invoice_created' and obj.invoice_id:
				raise UserError(_('Cannot delete record when invoice is created'))
			if (obj.state == 'payment_request_created' and obj.payment_request_id.state in ['accountant', 'done']) or obj.payment_request_id.tulugdsun_dun != 0:
				raise UserError('Төлбөрийн хүсэлтийн гүйлгээ хийгдсэн байна.')
			super(PurchaseInitialInvoiceLine, obj).unlink()
		return True
