# -*- coding: utf-8 -*-

from odoo import fields, models

class ResPartner(models.Model):
	_inherit = 'res.partner'

	purchase_method = fields.Selection([
		('purchase', 'By order quantity'),
		('receive', 'By received quantity'),
	], string="Create invoice for purchase order", default="purchase")
	purchase_receive_invoice = fields.Boolean(string="Create Invoice after receipt of income", default=False)
