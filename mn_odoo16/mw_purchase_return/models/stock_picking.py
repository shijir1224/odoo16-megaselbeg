# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
class StockPicking(models.Model):
	_inherit = 'stock.picking'

	purchase_return_id = fields.Many2one('purchase.return', 'Created PO return')

	def action_done(self):
		res = super(StockPicking, self).action_done()
		for pick in self:
			if pick.purchase_return_id.fully_sent:
				pick.purchase_return_id.state = 'done'
		return res
