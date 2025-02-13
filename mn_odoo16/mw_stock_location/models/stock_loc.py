# -*- coding: utf-8 -*-

from odoo import fields, models

class StockPicking(models.Model):
	_inherit = "stock.picking"

	update_location = fields.Boolean(related='picking_type_id.update_location', readonly=True)

	def get_best_parent_loc(self, location):
		while location.location_id and location.usage != 'view':
			location = location.location_id            
		return location

	def get_best_location(self, product_id, location_id):
		location_id = self.get_best_parent_loc(location_id)
		q_ids = self.env['stock.quant'].search([('quantity','>',0),('location_id','child_of',location_id.id),('product_id','=',product_id.id)])
		if q_ids:
			m_quantity = max(q_ids.mapped('quantity'))
			return q_ids.filtered(lambda r: r.quantity==m_quantity)[0].location_id
		mline_ids = self.env['stock.move.line'].search([('location_dest_id.usage','=','internal'),('state','=','done'),('qty_done','>',0),('location_dest_id','child_of',location_id.id),('product_id','=',product_id.id)])
		if mline_ids:
			m_quantity = max(mline_ids.mapped('qty_done'))
			return mline_ids.filtered(lambda r: r.qty_done==m_quantity)[0].location_dest_id

		return False

	def update_stock_location(self):
		self.ensure_one()
		if self.state not in ['done','cancel'] and self.picking_type_code!='outgoing':
			loc_id = self.location_dest_id
			for mline in self.move_line_ids:
				set_loc = self.get_best_location(mline.product_id, loc_id)
				if set_loc:
					mline.location_dest_id = set_loc.id

class StockPickingType(models.Model):
	_inherit = "stock.picking.type"

	update_location = fields.Boolean(string='Хамгийн их байрлал оруулах товч', default=False)
