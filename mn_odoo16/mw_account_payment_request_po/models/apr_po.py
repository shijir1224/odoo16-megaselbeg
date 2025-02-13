# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class payment_request(models.Model):
	_inherit = 'payment.request'

	purchase_ids = fields.Many2many('purchase.order', 'payment_request_po_rel', 'request_id', 'po_id', string='Худалдан авалт')
	import_po = fields.Boolean(string='Худалдан авалтын захиалгаас оруулах', default=False)
	po_count = fields.Integer(compute="_compute_count_po", string='Худалдан авалтын Тоо')

	@api.depends('purchase_ids')
	def _compute_count_po(self):
		for item in self:
			item.po_count = len(item.sudo().purchase_ids)
	
	@api.onchange('purchase_ids')
	def onch_purchase_ids(self):
		self.amount = sum(self.purchase_ids.mapped('amount_total'))

	def view_po(self):
		action = self.env.ref('purchase.purchase_rfq')
		vals = action.read()[0]
		domain = [('id','in',self.purchase_ids.ids)]
		vals['domain'] = domain
		vals['context'] = {}
		return vals

class purchase_order(models.Model):
	_inherit = 'purchase.order'

	payment_request_ids = fields.Many2many('payment.request', 'payment_request_po_rel', 'po_id', 'request_id', string='Төлбөрийн хүсэлт', copy=False)
	pay_count = fields.Integer(compute="_compute_count_po", string='Төлбөрийн хүсэлтийн тоо')

	@api.depends('payment_request_ids')
	def _compute_count_po(self):
		for item in self:
			item.pay_count = len(item.sudo().payment_request_ids)

	def get_tulbur_tootsoo_line(self):
		vals = []
		for item in self.order_line:
			vals.append((0, 0, {
				'qty': item.product_qty,
				'name': item.name,
				'price_unit': item.price_unit,
				'taxes_id': item.taxes_id,
			}))
		return vals
	
	def create_tulbur_tootsoo(self):
		obj = self.env['payment.request']
		obj_id = obj.create({
			'flow_id': self.env['dynamic.flow'].search([('model_id.model','=','payment.request')], order='sequence', limit=1).id,
			'partner_id': self.partner_id.id,
			'currency_id': self.currency_id.id,
			'amount': self.amount_total,
			'import_po': True,
			'desc_line_ids': self.get_tulbur_tootsoo_line()
		})
		self.payment_request_ids += obj_id
		attachs = self.env['ir.attachment'].search([('res_id', '=', self.id), ('res_model', '=', self._name)])
		for item in attachs:
			copy_id = item.sudo().copy()
			copy_id.res_id = obj_id.id
			copy_id.res_model = obj_id._name

	def view_pay(self):
		action = self.env.ref('mw_account_payment_request.action_view_payment_request_all')
		vals = action.read()[0]
		domain = [('id','in',self.payment_request_ids.ids)]
		vals['domain'] = domain
		vals['context'] = {}
		return vals
