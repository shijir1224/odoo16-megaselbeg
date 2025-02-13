# -*- coding: utf-8 -*-

from odoo import models

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def action_done(self):
		res = super(StockPicking, self).action_done()
		for picking in self:
			# Нэхэмжлэх үүсгэх
			if picking.picking_type_id.code == 'incoming' and picking.purchase_id and picking.partner_id.purchase_receive_invoice and picking.partner_id.purchase_method:
				invoice = picking.purchase_id.create_auto_invoice(picking.partner_id.purchase_method, picking=picking)
				if invoice:
					invoice.action_post()
		return res

	def get_purchase_method(self, purchase_method):
		res = super(StockPicking, self).get_purchase_method(purchase_method)
		if self.partner_id.purchase_method:
			res = self.partner_id.purchase_method
		return res
