# -*- coding: utf-8 -*-
from odoo import fields, models

class PurchaseStockReport(models.Model):
	_inherit = "purchase.stock.report"
	
	price_unit = fields.Float('Unit cost', group_operator='avg', readonly=True, groups="mw_purchase_price.group_mw_purchase_cost_view")
	sub_total = fields.Float('Subtotal', readonly=True, groups="mw_purchase_price.group_mw_purchase_cost_view")
