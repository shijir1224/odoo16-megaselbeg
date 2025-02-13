# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountInvoice(models.Model):
	_inherit = 'account.move'

	purchase_return_id = fields.Many2one('purchase.return', 'Return PO')  # Үүсгэсэн ХА-н буцаалт
