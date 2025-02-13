# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError

class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	# -------------------------------------------------------------------------
	# SVL creation helpers
	# -------------------------------------------------------------------------
	@api.model
	def _create_correction_svl(self, move, diff):
		stock_valuation_layers = self.env['stock.valuation.layer']
		if move._is_in() and diff > 0 or move._is_out() and diff < 0:
			move.product_price_update_before_done(forced_qty=diff)
			stock_valuation_layers |= move._create_in_svl(forced_quantity=abs(diff))
			if move.product_id.cost_method in ('average', 'fifo'):
				move.product_id._run_fifo_vacuum(move.company_id)
		elif move._is_in() and diff < 0 or move._is_out() and diff > 0:
			stock_valuation_layers |= move._create_out_svl(forced_quantity=abs(diff))
		elif move._is_dropshipped() and diff > 0 or move._is_dropshipped_returned() and diff < 0:
			stock_valuation_layers |= move._create_dropshipped_svl(forced_quantity=abs(diff))
		elif move._is_dropshipped() and diff < 0 or move._is_dropshipped_returned() and diff > 0:
			stock_valuation_layers |= move._create_dropshipped_returned_svl(forced_quantity=abs(diff))
		elif move._is_mrp_in() and diff != 0 or move._is_mrp_out() and diff != 0:	
			stock_valuation_layers |= move._create_mrp_svl(forced_quantity=abs(diff))
		stock_valuation_layers._validate_accounting_entries()

	def check_over_qty(self, vals):
		if vals.get('qty_done', False) and self.move_id and self.picking_id and not self.production_id:
			if vals['qty_done'] > self.move_id.product_uom_qty:
				raise UserError('Дуусгах тоо Захиалсан тооноос их байж болохгүй! %s..\n\n%s' %(self.move_id, self.product_id.display_name))