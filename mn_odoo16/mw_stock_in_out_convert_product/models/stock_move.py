# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)
import pytz
from datetime import datetime

class ProductProduct(models.Model):
	_inherit = 'product.product'

	# def name_search(self, name, args=None, operator='ilike', limit=100):
	# 	# Get the product_tmpl_id from the context if available
	# 	product_tmpl_id = self._context.get('product_tmpl_id')

	# 	# Add filter by product_tmpl_id if it's in the context
	# 	if product_tmpl_id:
	# 		args += [('product_tmpl_id', '=', product_tmpl_id)]

	# 	args = args or []
	# 	domain = []
	# 	# Perform the search based on the name and other args
	# 	if name:
	# 		domain = ['|', '|', ('product_code', operator, name), ('default_code', operator, name), ('name', operator, name)]
	# 	domain += args
	# 	products = self.search(domain, limit=limit)
	# 	# Return the results using name_get() to format the display
	# 	return products.name_get()


class StockMove(models.Model):
	_inherit = "stock.move"
	
	def action_change_product_move(self):
		self.ensure_one()
		if self.state not in ['draft','confirmed']:
			raise UserError(u'Хөдөлгөөний Төлөв "Хүлээгдэж буй", "Ноорог" төлөвт байх ёстой')
		view = self.env.ref('mw_stock_in_out_convert_product.stock_move_product_change_form')
		product_id = self.env['product.product'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id),('id','!=',self.product_id.id)], limit=1)
		change_id = self.env['stock.move.product.change'].create({
			'stock_move_id': self.id,
			})
		change_id.product_id.name_search(name='123', operator='not ilike')
		context = dict(self.env.context)
		context.update({'default_product_id': product_id.id})
		return {
			'name': _('Орлогын бараа солих'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.move.product.change',
			'views': [(view.id, 'form')],
			'view_id': view.id,
			'target': 'new',
			'res_id': change_id.id,
			'context': context,
		}

	def action_change_location_move(self):
		self.ensure_one()
		if self.state not in ['draft','confirmed'] and self.picking_id.picking_type_code!='incoming':
			raise UserError(u'Хөдөлгөөний Төлөв "Хүлээгдэж буй", "Ноорог" төлөвт байх ёстой')

		view = self.env.ref('mw_stock_in_out_convert_product.stock_move_location_change_form')
		change_id = self.env['stock.move.product.change'].create({
			'stock_move_id': self.id
			})
		return {
			'name': _('Орлогын бараа солих'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.move.product.change',
			'views': [(view.id, 'form')],
			'view_id': view.id,
			'target': 'new',
			'res_id': change_id.id,
			'context': dict(self.env.context),
		}

class stock_move_product_change(models.TransientModel):
	_name = "stock.move.product.change"
	_description = "Stock move product change"

	stock_move_id = fields.Many2one('stock.move', 'Хөдөлгөөн', readonly=True)
	base_product_id = fields.Many2one('product.product', related='stock_move_id.product_id',string='Бараа Үндсэн', readonly=True)
	base_location_id = fields.Many2one('stock.location', related='stock_move_id.location_id',string='Байрлал Үдсэн', readonly=True)
	base_product_tmpl_id = fields.Many2one('product.template', related='base_product_id.product_tmpl_id', string='Бараа темплати', readonly=True)
	product_id = fields.Many2one('product.product', 'Солих Бараа', domain="[('product_tmpl_id','=',base_product_tmpl_id)]")
	location_id = fields.Many2one('stock.location', 'Солих Байрлал')
	base_warehouse_id = fields.Many2one('stock.warehouse', related='base_location_id.set_warehouse_id', readonly=True)

	@api.onchange('product_id')
	def onchange(self):
		for item in self:
			if item.product_id.product_tmpl_id.id != item.base_product_tmpl_id.id:
				raise UserError("Таарахгүй бараа байна!")

	def action_done(self):
		if self.stock_move_id.move_line_ids:
			self.stock_move_id.move_line_ids.write({'product_id': self.product_id.id})
		self.stock_move_id.product_id = self.product_id.id

	def action_done_location(self):
		if self.stock_move_id.move_line_ids:
			self.stock_move_id.move_line_ids.write({'location_id': self.location_id.id})
		self.stock_move_id.location_id = self.location_id.id
