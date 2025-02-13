# -*- coding: utf-8 -*-

from odoo import models

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def _action_done(self):
		res = super(StockPicking, self)._action_done()
		for picking in self:
			# Нэмэлт зардлын Нэхэмжлэх үүсгэх
			if picking.picking_type_id.code == 'incoming':
				purchase_id = picking.purchase_id
				if purchase_id and purchase_id.company_id.auto_create_vendor_bill:
					purchase_id.make_expenses()
					purchase_id.create_expense_invoice()
					if purchase_id.company_id.auto_validate_vendor_bill:
						for obj in purchase_id.invoice_ids.filtered(lambda i: i.state == 'draft'):
							try:
								obj.action_post()
							except:
								pass
		return res
