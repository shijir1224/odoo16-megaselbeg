# -*- coding: utf-8 -*-
from odoo import models

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def create_line_from_scanner(self, so_id, barcode):
		so = self.env['sale.order'].search([('id','=', so_id),('state','=','draft')],limit=1)
		product = self.env['product.product'].search([('barcode','=',barcode)],limit=1)
		if so and product:
			line = self.env['sale.order.line'].search([('order_id','=',so_id),('product_id','=',product.id)],limit=1)
			if line:
				line.product_uom_qty += 1
				return True
			else:
				vals = {
					'order_id': so_id,
					'product_id': product.id,
					'product_uom_qty': 1,
				}
				self.env['sale.order.line'].create(vals)
				return True
		return False