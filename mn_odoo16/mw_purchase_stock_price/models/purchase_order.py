# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockPicking(models.Model):
	_inherit = "stock.picking"

	amount_total_purchase = fields.Float(string=u'PO Нийт дүн', compute='_compute_price_unit_purchase')

	@api.depends('move_ids.sub_total_purchase')
	def _compute_price_unit_purchase(self):
		for item in self:
			if not item.purchase_id:
				item.amount_total_purchase = 0
				continue
			item.amount_total_purchase = sum(item.move_ids.mapped('sub_total_purchase'))
	
	def update_price_unit_purchase(self):
		print ('self.purchase_id',self.purchase_id)
		purchase_id = self.move_ids.filtered(lambda r: r.purchase_line_id)
		if purchase_id:
			purchase_id = purchase_id[0].purchase_line_id.order_id
			for item in self.move_ids.filtered(lambda r: not r.purchase_line_id):
				ppp = purchase_id.order_line.filtered(lambda r: r.product_id==item.product_id)
				if ppp:
					item.purchase_line_id = ppp[0].id

class StockMove(models.Model):
	_inherit = "stock.move"

	price_unit_purchase = fields.Float(string=u'PO нэгж үнэ', compute='_compute_price_unit_purchase')
	sub_total_purchase = fields.Float(string=u'PO Нийт дүн', compute='_compute_price_unit_purchase')

	@api.depends('purchase_line_id.price_unit', 'product_id', 'product_uom_qty', 'quantity_done', 'state')
	def _compute_price_unit_purchase(self):
		for item in self:
			price_unit = 0
			po_uom_id = False
			if item.purchase_line_id:
				price_unit = -1*abs(item.purchase_line_id.price_unit) if item.location_dest_id.usage=='supplier' else abs(item.purchase_line_id.price_unit)
				po_uom_id = item.purchase_line_id
			else:
				item.price_unit_purchase = 0
				item.sub_total_purchase = 0
				continue
			item.price_unit_purchase = price_unit
			if item.state in ['done', 'cancel']:
				qty = item.product_uom._compute_quantity(item.quantity_done, po_uom_id.product_uom, round=False)
				item.sub_total_purchase = price_unit * qty
			elif item.state == 'assigned':
				qty = item.product_uom._compute_quantity(item.reserved_availability, po_uom_id.product_uom, round=False)
				item.sub_total_purchase = price_unit * qty
			else:
				qty = item.product_uom._compute_quantity(item.product_uom_qty, po_uom_id.product_uom, round=False)
				item.sub_total_purchase = price_unit * qty
