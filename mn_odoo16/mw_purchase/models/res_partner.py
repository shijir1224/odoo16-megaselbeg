# -*- coding: utf-8 -*-

from odoo import fields, models

class ResPartner(models.Model):
	_inherit = 'res.partner'

	discount_percent = fields.Float("PO discount (%)", default=0.0)
