# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api, _


class StockMoveInherit(models.Model):
	_inherit = 'stock.move'

	@api.depends('partner_id', 'picking_id.partner_id')
	def _methods_compute(self):
		for obj in self:
			obj.partner_id = obj.picking_id.partner_id.id
	
	@api.depends('sale_line_id.price_unit')
	def _methods_compute_so_price_unit(self):
		for obj in self:
			obj.so_price_unit = obj.sale_line_id.price_unit

	partner_id_non_store = fields.Many2one('res.partner', string='Харилцагч Баримтын', related='picking_id.partner_id', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")
	so_id = fields.Many2one('sale.order', string='SO', related='sale_line_id.order_id', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")
	po_id = fields.Many2one('purchase.order', string='PO', related='purchase_line_id.order_id', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")

	so_price_unit = fields.Float(string="SO Зарах үнэ", compute='_methods_compute_so_price_unit', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")

class StockMoveLineInherit(models.Model):
	_inherit = 'stock.move.line'

	partner_id = fields.Many2one('res.partner', string='Харилцагч Баримтын', related='move_id.partner_id_non_store', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")
	so_id = fields.Many2one('sale.order', string='SO', related='move_id.so_id', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")
	po_id = fields.Many2one('purchase.order', string='PO', related='move_id.po_id', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")

	price_unit_move = fields.Float(related='move_id.price_unit', string="Нэгж Өртөг", readonly=True, groups="mw_stock_partner_so.group_move_partner_view")
	so_price_unit = fields.Float(related='move_id.so_price_unit', readonly=True, groups="mw_stock_partner_so.group_move_partner_view")
	
