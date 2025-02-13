# -*- coding: utf-8 -*-
from odoo import fields, models

class StockMove(models.Model):
	_inherit = 'stock.move'

	def _get_price_unit(self):
		""" Returns the unit price for the move"""
		self.ensure_one()
		if self.purchase_line_id:
			return self.purchase_line_id.price_unit_stock_move
		return super(StockMove, self)._get_price_unit()

	price_unit = fields.Float(
		'Unit Price', help="Technical field used to record the product cost set by the user during a picking confirmation (when costing method used is 'average price' or 'real'). Value given in company currency and in product uom.", copy=False, digits='Product Price')

	def _action_done(self, cancel_backorder=False):
		res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
		for move in self.filtered(lambda move: move.sudo().purchase_line_id and move._is_in()):
			if move.sudo().purchase_line_id and move.price_unit!=move.sudo().purchase_line_id.price_unit_stock_move:
				move.price_unit = move.sudo().purchase_line_id.price_unit_stock_move
		return res
