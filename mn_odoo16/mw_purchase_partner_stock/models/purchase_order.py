# -*- coding: utf-8 -*-
from odoo import fields, models

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	for_partner_id = fields.Many2one('res.partner', string="Зориулж авах харилцагч")
