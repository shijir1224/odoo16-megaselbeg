# -*- coding: utf-8 -*-
from odoo import api, fields, _
from odoo.models import TransientModel
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class PurchaseRequestPOCreate(TransientModel):
	_name = 'purchase.request.line.po.create'
	_description = 'Purchase Order Create'

	@api.model
	def _default_line_ids(self):
		obj = self.env['purchase.request.line'].browse(self._context['active_ids'])
		line_ids = []
		for item in obj:
			line_ids.append((0, 0, {'pr_line_id': item.id, 'product_id': item.product_id.id, 'qty': item.qty,
									'po_qty': item.po_qty}))
		return line_ids

	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	partner_ids = fields.Many2many('res.partner', 'purchase_request_line_create_res_partner_rel', 'pur_id', 'par_id',
								   'Харилцагчид')
	is_comparison = fields.Boolean('Харьцуулалттай эсэх', default=False)
	is_internal = fields.Boolean('Дотоод хөдөлгөөн үүсгэх', default=False)
	is_po_qty_edit = fields.Boolean('Худалдан авалтын тоог өөрчлөх', default=False)
	date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
	user_id = fields.Many2one('res.users', string='Оноох Хангамжийн Ажилтан')
	flow_id = fields.Many2one('dynamic.flow', string='Худалдан авалтын урсгал тохиргоо',
							  domain="[('model_id.model', '=', 'purchase.order')]")

	comparison_flow_id = fields.Many2one('dynamic.flow', string='Харьцуулалтын урсгал тохиргоо',
										 domain="[('model_id.model', '=', 'purchase.order.comparison')]")
	warehouse_id = fields.Many2one('stock.warehouse', string='Худалдан авах агуулах')
	to_warehouse_id = fields.Many2one('stock.warehouse', string='Дотоод хөдөлгөөнөөр явуулах')
	picking_date = fields.Datetime(string='Дотоод хөдөлгөөн үүсгэх огноо', default=fields.Datetime.now)
	line_ids = fields.One2many('purchase.request.line.po.create.line', 'parent_id', 'Мөр', default=_default_line_ids)
	purchase_sub_id = fields.Many2one('purchase.order', 'Нэмэгдэх PO')
	is_sub_po = fields.Boolean('Худалдан авалтын захиалганд нэгтгэх', default=False)

	@api.onchange('is_comparison')
	def onchange_is_comparison(self):
		for obj in self:
			if obj.is_comparison:
				obj.is_internal = False

	def get_po_vals(self):
		search_domain = [('flow_id', '=', self.flow_id.id)]
		flow_line_id = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
		return {
			'date_order': self.date,
			'flow_id': self.flow_id.id,
			'picking_type_id': self.warehouse_id.in_type_id.id,
			'date_planned': self.date,
			'flow_line_id': flow_line_id,
			'state': 'draft',
		}

	def action_done(self):
		obj = self.env['purchase.request.line'].browse(self._context['active_ids'])
		if obj.filtered(lambda r: r.request_id.state_type != 'done'):
			raise ValidationError(_('Дууссан төлөвт ороогүй хүсэлтийн мөр сонгогдсон байна.'))

		if obj.filtered(lambda r: r.po_line_ids and r.po_diff_qty <= 0):
			raise ValidationError(_('ХА захиалга үүссэн байна!'))

		if obj.filtered(lambda r: not r.product_id):
			raise ValidationError('Бараа сонгогдоогүй Хүсэлт байна Бараагаа үүсгэнэ үү')
		
		if obj.filtered(lambda r: not r.user_id):
			raise ValidationError('ХА ажилтанд оноогоогүй мөр байна!')

		desc = obj.mapped('request_id.name') + obj.filtered(lambda r: r.request_id.desc is not False).mapped(
			'request_id.desc') + obj.filtered(lambda r: r.request_id.desc_done is not False).mapped(
			'request_id.desc_done')

		user_ids = obj.mapped('user_id')

		if not self.is_comparison:
			if not self.is_sub_po:
				vals = self.get_po_vals()
				vals['origin'] = ','.join(desc) if len(desc) > 0 else '',
				if user_ids:
					vals['user_id'] = user_ids[0].id
				vals['partner_id'] = self.partner_id.id
				po_id = self.env['purchase.order'].with_context(from_request=True).create(vals)
			else:
				po_id = self.purchase_sub_id

			for item in self.line_ids:
				po_line_vals = item.get_pr_po_line(po_id)
				self.env['purchase.order.line'].with_context(from_request=True).create(po_line_vals)

			for item in po_id.order_line:
				if item.product_id.type != 'service':
					item._compute_price_unit_and_date_planned_and_name()
			try:
				po_id.onchange_taxes_id()
			except Exception as e:
				_logger.info('---------------', e)

			# chat ilgeeh
			for item in po_id.sudo().order_line.mapped('pr_line_many_ids.request_id.partner_id'):
				po_id.send_chat_employee(item)

			# + activity onoodog bolgov
			for item in po_id.filtered(lambda r: r.user_id):
				self.env['dynamic.flow.history'].create_activity('', item.user_id, 'purchase.order', item.id)
			# = activity onoodog bolgov

			if self.is_internal:
				picking_obj = self.env['stock.picking']
				move_obj = self.env['stock.move']
				if self.to_warehouse_id:
					int_wh_ids = self.to_warehouse_id
				else:
					int_wh_ids = obj.filtered(lambda r: r.request_id.warehouse_id.id != self.warehouse_id.id).mapped(
						'request_id.warehouse_id')
				for item in int_wh_ids:
					if not self.is_sub_po:
						warehouse_id = self.warehouse_id
					else:
						warehouse_id = po_id.picking_type_id.warehouse_id

					location_id = warehouse_id.lot_stock_id
					picking_type_id = warehouse_id.int_type_id
					location_dest_id = item.lot_stock_id

					if self.to_warehouse_id:
						req_ids = obj
					else:
						req_ids = obj.filtered(lambda r: r.request_id.warehouse_id.id == item.id)

					desc = [x.name + u' ' + x.sudo().partner_id.name + u' ' + (x.desc or '') for x in
							req_ids.mapped('request_id')]
					name = ','.join(desc)

					picking_id = picking_obj.create({
						'picking_type_id': picking_type_id.id,
						'location_id': location_id.id,
						'location_dest_id': location_dest_id.id,
						'scheduled_date': self.picking_date,
						'move_ids': [],
						'origin': name,
					})
					for line in req_ids:
						move = {
							'name': name + u' ' + line.product_id.name,
							'product_id': line.product_id.id,
							'product_uom': line.product_id.uom_id.id,
							'product_uom_qty': line.po_qty if self.is_po_qty_edit else line.qty,
							'picking_type_id': picking_type_id.id,
							'location_id': location_id.id,
							'location_dest_id': location_dest_id.id,
							'date': self.picking_date,
							'picking_id': picking_id.id,
						}
						stock_move_id = move_obj.create(move)
						stock_move_id._action_confirm()
						line.internal_stock_move_id = stock_move_id.id
			return obj
		else:
			comparison = self.env['purchase.order.comparison'].create(self.get_comparison_lines())
			for obj in self.line_ids:
				vals = obj.get_comparison_line(comparison)
				self.env['purchase.order.comparison.line'].create(vals)
			self.line_ids.mapped('pr_line_id')._compute_po_diff_qty()
			# self.line_ids.mapped('pr_line_id').write({'comp_line_ids': [(4, [comparison.id])]})

	def get_comparison_lines(self):
		return {'flow_id': self.comparison_flow_id.id,
				'date_order': self.date,
				'partner_ids': [
					[6, False, self.partner_ids.ids]],
				'picking_type_id': self.warehouse_id.in_type_id.id}


class PurchaseRequestLinePOCreateline(TransientModel):
	_name = 'purchase.request.line.po.create.line'
	_description = 'Purchase Order Create Line'

	parent_id = fields.Many2one('purchase.request.line.po.create', ondelete='cascade', string='Parent')
	pr_line_id = fields.Many2one('purchase.request.line', string='Request line')
	product_id = fields.Many2one('product.product', related='pr_line_id.product_id', readonly=True, store=True)
	desc = fields.Char(related='pr_line_id.desc', readonly=True, store=True)
	qty = fields.Float(related='pr_line_id.qty', readonly=True, store=True)
	po_diff_qty = fields.Float('Боломжит тоо хэмжээ', related='pr_line_id.po_diff_qty', readonly=True, store=True)
	po_qty = fields.Float(string='Үүсгэх тоо хэмжээ')

	def get_pr_po_line(self, po_id):
		self.ensure_one()
		if self.parent_id.is_po_qty_edit and self.po_qty > self.po_diff_qty:
			raise UserError(_("‘Үүсгэх тоо хэмжээ’ ‘Боломжит тоо хэмжээ’-г давсан байна."))
		if self.parent_id.is_po_qty_edit and self.po_qty == 0:
			raise UserError(_("‘Үүсгэх тоо хэмжээ’ 0 байна."))

		vals = {
			'product_id': self.product_id.id,
			'name': '%s' % (', '.join(set(self.pr_line_id.mapped('name')))),
			'date_planned': self.parent_id.date,
			'product_qty': self.po_qty if self.parent_id.is_po_qty_edit else self.pr_line_id.po_diff_qty,
			'product_uom': self.pr_line_id.uom_id.id,
			'order_id': po_id.id,
			'pr_line_many_ids': [(6, 0, self.pr_line_id.ids)],
			'price_unit': 0,
		}
		if self.pr_line_id.request_id.use_price:
			vals.update({'taxes_id': [(6, 0, self.pr_line_id.taxes_id.ids)],
						 'currency_id': self.pr_line_id.currency_id.id,
						 'price_unit': self.pr_line_id.price_unit,
						 'price_unit_without_discount': self.pr_line_id.price_unit})
		return vals

	def get_comparison_line(self, comparison_id):
		self.ensure_one()
		if self.parent_id.is_po_qty_edit and self.po_qty > self.po_diff_qty:
			raise UserError(_("‘Үүсгэх тоо хэмжээ’ ‘Боломжит тоо хэмжээ’-г давсан байна."))
		vals = {
			'product_id': self.product_id.id,
			'name': '%s' % (', '.join(set(self.pr_line_id.mapped('name')))),
			'product_uom': self.pr_line_id.uom_id.id,
			'product_qty': self.po_qty if self.parent_id.is_po_qty_edit else self.pr_line_id.po_diff_qty,
			'comparison_id': comparison_id.id,
			'request_line_ids': [(6, 0, self.pr_line_id.ids)],
		}
		return vals

	# @api.depends('pr_line_id')
	# def com_po_qty(self):
	#     for item in self:
	#         item.po_qty = item.pr_line_id.po_diff_qty
	#
	# def _set_po_qty(self):
	#     for item in self:
	#         item.pr_line_id.po_qty = item.po_qty
