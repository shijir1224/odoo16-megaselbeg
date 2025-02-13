# -*- coding: utf-8 -*-

from odoo import fields, models

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	invoice_number = fields.Char('Vendor invoice number', tracking=True)
	
	def _action_done(self):
		res = super(StockPicking, self)._action_done()
		for picking in self:
			# Нэхэмжлэх үүсгэх
			if picking.picking_type_id.code == 'incoming':
				purchase_id = picking.purchase_id
				if purchase_id and purchase_id.company_id.auto_create_vendor_bill:
					if picking.move_ids[0].product_id.purchase_method == 'receive':
						purchase_id.create_invoice_hand()
						if purchase_id.company_id.auto_validate_vendor_bill:
							for obj in purchase_id.invoice_ids.filtered(lambda i: i.state == 'draft'):
								obj.action_post()
		return res

	def create_invoice_po(self):
		for picking in self:
			# Нэхэмжлэх үүсгэх
			if picking.purchase_id:
				invoice = picking.purchase_id.create_auto_invoice(picking.move_ids[0].product_id.purchase_method, picking=picking)
				if invoice:
					invoice.action_post()