# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.mw_purchase_expense.models.purchase_order_expenses import PORTION_SELECTION

PORTION_SELECTION.append(('qty', 'Unit Quantity'))

class PurchaseOrderInherit(models.Model):
	_inherit = 'purchase.order.line'

	unit_weight = fields.Float('Unit weight')
	subtotal_weight = fields.Float('Subtotal weight', compute="_weight_compute", store=True, digits=(16, 2))
	total_weight = fields.Float('Total weight', digits=(16, 2))

	@api.model
	def create(self, vals):
		res = super(PurchaseOrderInherit, self).create(vals)
		for item in res:
			item.on_prod_weight()
		return res

	@api.onchange('product_id')
	def on_prod_weight(self):
		self.unit_weight = self.product_id.weight

	@api.onchange('unit_weight')
	def onchage_unit_weight(self):
		self.product_id.sudo().weight = self.unit_weight

	@api.depends('product_id', 'product_qty', 'product_uom', 'unit_weight')
	def _weight_compute(self):
		for item in self:
			if item.product_id and item.product_qty and item.product_uom:
				product_qty_main_uom = item.product_uom._compute_quantity(item.product_qty, item.product_id.uom_id,
																		  rounding_method='HALF-UP')
				tot = (product_qty_main_uom * item.unit_weight)
				item.subtotal_weight = tot
			else:
				item.subtotal_weight = 0

# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
#
#     def make_portion(self, method, lines, amount, date_current, expenses_line_id):
#         if method == 'qty':
#             portion_dict = {}
#             # Зардлыг хуваарилах
#             tot_w = sum(lines.mapped('product_uom_qty'))
#             for line in lines:
#                 tot_w_amount = 0
#                 if tot_w > 0:
#                     tot_w_amount = expenses_line_id.current_amount * line.product_uom_qty / tot_w
#                 portion_dict[line.id] = tot_w_amount
#             return portion_dict
#         else:
#             return super(PurchaseOrder, self).make_portion(method, lines, amount, date_current, expenses_line_id)
