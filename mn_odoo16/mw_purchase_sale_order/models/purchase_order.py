# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

# for_partner_id

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def action_create_po(self):
		sale_order_po_obj = self.env['sale.order.po.create']
		sale_order_po_line_obj = self.env['sale.order.po.create.line']
		# obj = self.env['sale.order'].browse(self._context['active_ids'])
		is_create = False
		so_po_id = int()
		for item in self.order_line:
			if item.product_uom_qty > item.free_qty_today:
				is_create = True
				# print(self.env.context.get('active_id'), self.env.context.get('active_ids'), self.env.context.get('active_model'))
				sale_order_po_line_obj.create({
					'product_id': item.product_id.id,
					'qty': item.product_uom_qty,
					'po_qty': item.product_uom_qty - item.free_qty_today,
					'product_residual': item.free_qty_today,
				})
		if is_create:
			action = self.env.ref('mw_purchase_sale_order.sale_order_po_create_action')
			result = action.read()[0]
			# res = self.env.ref('mw_purchase_sale_order.sale_order_po_create_form', False)
			# result['views'] = [(res and res.id or False, 'form')]
			# result['res_id'] = self.id
			print('NOO')
			return result


	def action_confirm(self):
		# self.action_create_po()
		# print('working')
		# ===========================================
		res = super(SaleOrder, self).action_confirm()
		print(res)
		return res

class sale_order_po_create(models.TransientModel):
	_name='sale.order.po.create'
	_description = 'Purchase Order Create'

	date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
	user_id = fields.Many2one('res.users', string='Оноох Хангамжийн Ажилтан')
	flow_id = fields.Many2one('dynamic.flow', string='Худалдан авалтын урсгал тохиргоо', domain="[('model_id.model', '=', 'purchase.order')]")

	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	for_partner_id = fields.Many2one('res.partner', string='Зориулж авах харилцагч')

	line_ids = fields.One2many('sale.order.po.create.line', 'parent_id', 'Мөр')
	is_po_qty_edit = fields.Boolean('Худалдан авалтын тоог өөрчлөх', default=False)

	@api.onchange('for_partner_id')
	def onch_po_qty(self):
		sale_id = self.env['sale.order'].browse(self._context['active_ids'])
		so_line_obj = self.env['sale.order.line'].search([('order_id','in',self._context['active_ids'])])
		sale_order_po_line_obj = self.env['sale.order.po.create.line']
		self.line_ids = False

		obj = self.env['stock.move'].search([('picking_id.sale_id','in',self._context['active_ids'])])
		quant = self.env['stock.quant']
		line_ids = []

		for line in so_line_obj:
			print('sale_order_line', line.product_id.id, line.product_uom_qty)
			diff = line.product_uom_qty
			if diff > 0:
				# нийт үлдэгдэл
				# product_residual = sum(quant.sudo().search([('on_hand','=',False), ('product_id','=',line.product_id.id)]).mapped('quantity'))
				# байрлалаар үлдэгдэл
				locs = self.env['stock.location'].search([])
				total_qty = 0
				total_res_qty = 0
				for loc in locs:
					total_res_qty += sum(quant.sudo().search([('location_id','=',loc.id), ('product_id','=',line.product_id.id)]).mapped('reserved_quantity'))
					total_qty += sum(quant.sudo().search([('location_id','=',loc.id), ('product_id','=',line.product_id.id)]).mapped('quantity'))
				# reserved_quantity = sum(quant.sudo().search([('location_id','=',sale_id.warehouse_id.lot_stock_id.id), ('product_id','=',line.product_id.id)]).mapped('reserved_quantity'))
				# product_residual = sum(quant.sudo().search([('location_id','=',sale_id.warehouse_id.lot_stock_id.id), ('product_id','=',line.product_id.id)]).mapped('quantity'))
				sale_order_po_line_obj.create({
						'parent_id': self.id,
						'product_id': line.product_id.id,
						'qty': line.product_uom_qty,
						'po_qty': line.product_uom_qty,
						'product_residual': total_qty - total_res_qty,
					})

		if not self.line_ids and line_ids:
			self.line_ids = self.env['sale.order.po.create.line'].create(line_ids)


	def action_done(self):
		purchase_obj = self.env['purchase.order']
		po_line_obj = self.env['purchase.order.line']
		po_id = purchase_obj.create({
			'flow_id': self.flow_id.id,
			'user_id': self.user_id.id,
			'date_planned': self.date,
			'partner_id': self.partner_id.id,
		})
		for line in self.line_ids:
			print(po_id.id)
			po_line_obj.create({
				'order_id': po_id.id,
				'product_id': line.product_id.id,
				'product_qty': line.po_qty,
				'date_planned': self.date,
				'name': '1',
				'price_unit': 1,
			})
		print()

class sale_order_po_create_line(models.TransientModel):
	_name='sale.order.po.create.line'
	_description = 'Purchase Order Create'

	parent_id = fields.Many2one('sale.order.po.create', ondelete='cascade', string='Parent')
	# so_id = fields.Many2one('sale.order', string='Захиалгын мөр')
	# sm_id = fields.Many2one('stock.move', string='Захиалгын мөр')
	product_id = fields.Many2one('product.product', readonly=True)
	# desc = fields.Char(related='sm_line_id.desc', readonly=True)
	qty = fields.Float(string='Хүссэн тоо хэмжээ', readonly=True)
	po_qty = fields.Float(string="PO үүсгэх тоо")
	product_residual = fields.Float('Хангамжийн агуулахын үлдэгдэл')
