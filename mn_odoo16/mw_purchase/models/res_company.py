# -*- coding: utf-8 -*-

from odoo import fields, models

class Company(models.Model):
	_inherit = 'res.company'

	is_change_po_uom_to_uom = fields.Boolean("Change purchase uom to main uom", default=False)
	auto_create_vendor_bill = fields.Boolean("Auto-create invoice", default=False)
	auto_validate_vendor_bill = fields.Boolean("Auto-validate invoice", default=False)
