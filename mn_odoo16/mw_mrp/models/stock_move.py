# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, OrderedSet

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
	_inherit = "stock.picking"

	def action_create_account_entry(self):
		i = 1
		for res in self.move_ids.filtered(lambda r: r.state == 'done'):
			# if res.filtered(lambda m: m.product_id.valuation == 'real_time' and (m._is_in() or m._is_out() or m._is_mrp_in() or m._is_mrp_out() or m._is_dropshipped())):
			# 	print(tttt)
			# else:
			# 	print(rrrrrr)
			for move in res.filtered(lambda m: m.product_id.valuation == 'real_time' and (m._is_in() or m._is_out() or m._is_mrp_in() or m._is_mrp_out() or m._is_dropshipped())):
				move.create_account_move_hand()
			i += 1

class StockMove(models.Model):
	_inherit = "stock.move"

	def _is_mrp_in(self):
		"""Check if the move should be considered as a production move so that the cost method
		will be able to apply the correct logic.

		:returns: True if the move is a production one else False
		:rtype: bool
		"""
		self.ensure_one()
		return self.location_id.usage == 'production' and self.location_dest_id.usage == 'internal'
	
	def _is_mrp_out(self):
		"""Check if the move should be considered as a production move so that the cost method
		will be able to apply the correct logic.

		:returns: True if the move is a production one else False
		:rtype: bool
		"""
		self.ensure_one()
		return self.location_id.usage == 'internal' and self.location_dest_id.usage == 'production'
	
	def _get_mrp_svl_vals(self, forced_quantity):
		svl_vals_list = []
		for move in self:
			move = move.with_company(move.company_id)
			valued_move_lines = move._get_in_move_lines()
			valued_quantity = 0
			for valued_move_line in valued_move_lines:
				valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
			unit_cost = move.product_id.standard_price
			if move.product_id.cost_method != 'standard':
				unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
			svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
			svl_vals.update(move._prepare_common_svl_vals())
			# if forced_quantity:
			#     svl_vals['description'] = 'Correction of %s (modification of past move)' % (move.picking_id.name or move.name)
			svl_vals_list.append(svl_vals)
		return svl_vals_list
	
	def _create_mrp_svl(self, forced_quantity=None):
		"""Create a `stock.valuation.layer` from `self`.

		:param forced_quantity: under some circunstances, the quantity to value is different than
			the initial demand of the move (Default value = None)
		"""
		svl_vals_list = self._get_mrp_svl_vals(forced_quantity)
		return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

	def create_account_move_hand(self):
		for item in self:
			if not item.stock_valuation_layer_ids:
				move = item
				rounding = move.product_id.uom_id.rounding
				# diff = move.product_qty
				diff = move.product_uom._compute_quantity(move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
				if float_is_zero(diff, precision_rounding=rounding):
					continue
				self.env['stock.move.line'].sudo()._create_correction_svl(move, diff)
			if not self.env['account.move'].search([('stock_move_id','=',item.id)]) and item.product_id.valuation == 'real_time' and (item._is_in() or item._is_out() or item._is_dropshipped() or item._is_mrp_in() or item._is_mrp_out()):
				stock_valuation_layers = item.stock_valuation_layer_ids
				for svl in stock_valuation_layers:
					if not svl.product_id.valuation == 'real_time' or svl.account_move_id:
						pass
					else:
						vals = svl.stock_move_id.sudo()._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
						if vals:
							account_moves = self.env['account.move'].sudo().create(vals)
							account_moves.sudo().write({'date': item.date.date()})
							account_moves.sudo().action_post()
	
	def _account_entry_move(self, qty, description, svl_id, cost):
		""" Accounting Valuation Entries """
		self.ensure_one()
		am_vals = []
		if self.product_id.type != 'product':
			# no stock valuation for consumable products
			return am_vals
		if self.restrict_partner_id and self.restrict_partner_id != self.company_id.partner_id:
			# if the move isn't owned by the company, we don't make any valuation
			return am_vals

		company_from = (self._is_out() or self._is_mrp_out()) and self.mapped('move_line_ids.location_id.company_id') or False
		company_to = (self._is_in() or self._is_mrp_out()) and self.mapped('move_line_ids.location_dest_id.company_id') or False

		journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
		# Create Journal Entry for products arriving in the company; in case of routes making the link between several
		# warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
		if self._is_mrp_in():
			# if self._is_returned(valued_type='in'):
			# 	am_vals.append(self.with_company(company_to).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
			# else:
			am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))
		elif self._is_in():
			if self._is_returned(valued_type='in'):
				am_vals.append(self.with_company(company_to).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
			else:
				am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))

		# Create Journal Entry for products leaving the company
		if self._is_mrp_out():
			cost = -1 * cost
			# if self._is_returned(valued_type='out'):
			# 	am_vals.append(self.with_company(company_from).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
			# else:
			am_vals.append(self.with_company(company_from)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))
		elif self._is_out():
			cost = -1 * cost
			if self._is_returned(valued_type='out'):
				am_vals.append(self.with_company(company_from).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
			else:
				am_vals.append(self.with_company(company_from)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))

		if self.company_id.anglo_saxon_accounting:
			# Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
			if self._is_dropshipped():
				if cost > 0:
					am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))
				else:
					cost = -1 * cost
					am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))
			elif self._is_dropshipped_returned():
				if cost > 0:
					am_vals.append(self.with_company(self.company_id).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
				else:
					cost = -1 * cost
					am_vals.append(self.with_company(self.company_id).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))

		return am_vals