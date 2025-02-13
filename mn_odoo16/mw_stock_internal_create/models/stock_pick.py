# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = "stock.picking"
	
	in_coming_picking_id = fields.Many2one('stock.picking', 'Орлогын баримт')
	internal_wh_id = fields.Many2one('stock.warehouse', 'Дотоод хөдөлгөөн үүсгэх агуулах')
	in_coming_picking_ids = fields.One2many('stock.picking', 'in_coming_picking_id', 'Орлогын баримтууд')

	def create_internal_from_incoming(self):
		location_id = False
		picking_type_id = False
		if self.picking_type_id.code=='incoming':
			location_id = self.picking_type_id.warehouse_id.lot_stock_id
			picking_type_id = self.picking_type_id.warehouse_id.int_type_id
		elif self.picking_type_id.code=='internal':
			location_id = self.location_dest_id
			picking_type_id = self.location_dest_id.set_warehouse_id.int_type_id

		location_dest_id = self.internal_wh_id.lot_stock_id

		in_coming_picking_id = self.env['stock.picking'].search([('in_coming_picking_id','=',self.id)])
		
		if not self.internal_wh_id:
			raise UserError(u'Дотоод хөдөлгөөн үүсгэх агуулахаа сонгож өгнө үү')
		if in_coming_picking_id:
			raise UserError(u'Дотоод хөдөлгөөн үүссэн байна')

		# if location_dest_id.id == location_id.id:
		#     raise UserError(u'Дотоод хөдөлгөөн үүсгэх агуулах нь ижил агуулах байна')
		sp_id = self.env['stock.picking'].create(
			{'picking_type_id': picking_type_id.id,
			 'state': 'draft',
			 'move_type': 'one',
			 'partner_id': False,
			 'scheduled_date': self.scheduled_date,
			 'location_id': location_id.id,
			 'location_dest_id': location_dest_id.id,
			 'origin': u'ДОТООД ХӨДӨЛГӨӨН ҮҮСГЭВ '+self.name+u' /'+(self.origin or '')+u'/',
			 'in_coming_picking_id': self.id,
			 'immediate_transfer': False
			 })
		vals = {}
		for line in self.move_ids:
			if line.state == 'done':
				vals = {
					'name': self.name,
					'picking_id': sp_id.id,
					'product_id': line.product_id.id,
					'product_uom': line.product_uom.id,
					'product_uom_qty': line.product_uom_qty,
					'location_id': location_id.id,
					'location_dest_id': location_dest_id.id,
					'state': 'draft',
				}
			move_id = self.env['stock.move'].create(vals)
			move_id._action_confirm(merge=False, merge_into=False)

		context = dict(self._context)
		context['create']= False
		form_view_id = self.env.ref('stock.view_picking_form').id
		action = {
				'name': self.name,
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'stock.picking',
				'view_id': form_view_id,
				'res_id': sp_id.id,
				'type': 'ir.actions.act_window',
				'context': context,
				'target': 'current'
			}
		return action
	
	def action_view_in_coming_picking(self):
		# context = dict(self._context)
		context = {}
		context['create']= False
		tree_view_id = self.env.ref('stock.vpicktree').id
		form_view_id = self.env.ref('stock.view_picking_form').id
		action = {
				'name': self.name,
				'view_type': 'form',
				'view_mode': 'tree',
				'res_model': 'stock.picking',
				'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
				'view_id': tree_view_id,
				'domain': [('id','in',self.in_coming_picking_ids.ids)],
				'type': 'ir.actions.act_window',
				'context': context,
				'target': 'current'
			}
		return action