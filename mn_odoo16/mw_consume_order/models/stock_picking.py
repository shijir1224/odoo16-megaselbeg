# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	def button_validate(self):
		res = super(StockPicking, self).button_validate()
		for item in self:
			if item.other_expense_id:
				item.other_expense_id.action_to_consumable()
		return res
