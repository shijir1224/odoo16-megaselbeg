# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import float_is_zero

class StockMove(models.Model):
	_inherit = 'stock.move'

	# def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
	# 	self.ensure_one()
	# 	res = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
	# 	if self.purchase_line_id:
	# 		if self.purchase_line_id.lot_id and self.location_id.usage == 'supplier':
	# 			res.update({'lot_id': self.purchase_line_id.lot_id.id})
	# 	return super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)

	def _action_done(self, cancel_backorder=False):
		res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
		for move in self:
			# ХА-н буцаалт болон барааны өртөг дундаж эсэхийг шалгаж байна
			if move.picking_id and move.picking_id.purchase_id and move.picking_id.picking_type_id.code == 'outgoing' and move.with_company(move.company_id).product_id.cost_method == 'average':
				move.product_price_update_from_purchase_return()
		return res

	def _prepare_common_svl_vals(self):
		res = super(StockMove, self)._prepare_common_svl_vals()
		if self.picking_id and self.picking_id.purchase_id and self.picking_id.picking_type_id.code == 'outgoing' and self.with_company(self.company_id).product_id.cost_method == 'average':
			res['unit_cost'] = self.price_unit
			res['value'] = self.company_id.currency_id.round(self.price_unit * (-1 * self.product_uom_qty))
		return res

	def product_price_update_from_purchase_return(self):
		"""
			ХА буцаалт хийх үед агуулахын өртөгийг тухайн худалдан авалтгүйгээр шинэчилж байна.
			Томьёо: ((Одоогийн өртөг * Одоогийн үлдэгдэл) - (ХА үнэ * Буцаалтын тоо хэмжээ)) / (Одоогийн үлдэгдэл - Буцаалтын тоо хэмжээ)
		"""
		precision = self.env['decimal.precision'].precision_get('Product Price')
		for move in self:
			product_tot_qty_available = move.product_id.sudo().with_company(move.company_id).quantity_svl
			amount_unit = move.product_id.with_company(move.company_id).standard_price
			valued_move_lines = move._get_out_move_lines()
			qty_done = 0
			for valued_move_line in valued_move_lines:
				qty_done += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
			if float_is_zero(product_tot_qty_available, precision):
				new_std_price = 0
			else:
				new_std_price = ((amount_unit * (product_tot_qty_available + qty_done)) - (move.price_unit * qty_done)) / product_tot_qty_available
			move.product_id.with_company(move.company_id.id).with_context(disable_auto_svl=True).sudo().write({'standard_price': new_std_price})

	def _get_price_unit(self):
		"""
		OVERRIDE: Буцаалт үед одоо байгаа өртөг болон Агуулахын баримтын өртөгөө авах сонголттой болсон тул
				  түүнээс хамааран буцаалт үед заавал Агуулахын баримтын өртөгөө авахгүй болгов
		"""
		self.ensure_one()
		price_unit = self.price_unit
		precision = self.env['decimal.precision'].precision_get('Product Price')
		return price_unit if not float_is_zero(price_unit, precision) or self._should_force_price_unit() else self.product_id.standard_price
