# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError


class PurchaseReturn(models.Model):
	_name = 'purchase.return'
	_description = 'PO return'
	_order = 'date DESC'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char(string='Number', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)  # Дугаар
	date = fields.Date(required=True, copy=False, default=fields.Date.context_today, string="Date")
	partner_id = fields.Many2one('res.partner', 'Vendor', required=True)  # Нийлүүлэгч
	warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True)
	in_type_id = fields.Many2one('stock.picking.type', related="warehouse_id.in_type_id")
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id)
	currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id.id)
	amount_untaxed = fields.Monetary(string='Untaxed amount', store=True, readonly=True, compute='_amount_all', tracking=True)
	amount_tax = fields.Monetary(string='Tax amount', store=True, readonly=True, compute='_amount_all')
	amount_total = fields.Monetary(string='Total amount', store=True, readonly=True, compute='_amount_all')
	taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	state = fields.Selection([
		('draft', 'Draft'),
		('calculated', 'Checked'),
		('cancelled', 'Cancelled'),
		('confirmed', 'Confirmed'),
		('done', 'Done'),
	], 'State', default='draft', copy=False, tracking=True)
	return_line = fields.One2many('purchase.return.line', 'return_id', string='Return lines', copy=True)
	purchase_ids = fields.Many2many('purchase.order', 'purchase_return_po_rel', 'return_id', 'purchase_id', string='Return purchase orders', copy=False) # Буцаах худалдан авалтууд
	show_import_button = fields.Boolean('Show import', default=False, copy=False, store=True)  # Импортлохыг харуулах
	picking_count = fields.Integer(compute='_picking_count', string='Transfer count')  # Шилжүүлгийн тоо
	picking_ids = fields.One2many('stock.picking', 'purchase_return_id', string='Transfers')  # Шилжүүлгүүд
	invoice_count = fields.Integer(compute='_invoice_count', string='Invoice count')
	invoice_ids = fields.One2many('account.move', 'purchase_return_id', string='Invoice')  # Нэхэмжлэлүүд
	need_create_stock_move = fields.Boolean('Stock move creation needed', compute='_compute_need_create_stock_move', default=False)  # Зарлага үүсгэх шаардлагатай
	fully_sent = fields.Boolean('Fully sent', compute='_compute_fully_sent', default=False, store=True)  # Зарлагадаж дууссан

	@api.depends('return_line.not_stock_move_created_qty')
	def _compute_need_create_stock_move(self):
		for ret in self:
			ret.need_create_stock_move = any(ret.return_line.mapped('not_stock_move_created_qty'))

	@api.depends('return_line.not_sent_qty')
	def _compute_fully_sent(self):
		for ret in self:
			if any(ret.return_line.mapped('not_sent_qty')):
				ret.fully_sent = False
			else:
				ret.fully_sent = True

	@api.onchange('taxes_id')
	def onchange_taxes_id(self):
		for line in self.return_line:
			line.taxes_id = self.taxes_id

	@api.onchange('purchase_ids')
	def onchange_purchase_ids(self):
		if self.purchase_ids:
			self.show_import_button = True
		else:
			self.show_import_button = False

	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('purchase.return') or _('New')
		else:
			vals['name'] = self.env['ir.sequence'].next_by_code('purchase.return') or _('New')
		return super(PurchaseReturn, self).create(vals)

	def import_lines(self):
		self.return_line.unlink()
		for po in self.purchase_ids:
			for line in po.order_line:
				move_lines = self.env['stock.move.line']
				moves = self.env['stock.move'].search([
					('purchase_line_id', '=', line.id),
					('picking_type_id', '=', self.warehouse_id.in_type_id.id)
				])
				move_lines |= moves.move_line_ids
				for move_line in move_lines:
					qty = move_line.qty_done
					if line.product_uom != move_line.product_uom_id:
						qty = move_line.product_uom_id._compute_quantity(qty, line.product_uom, round=False)
					self.env['purchase.return.line'].create({
						'return_id': self.id,
						'product_id': line.product_id.id,
						'qty': qty,
						'product_uom': line.product_uom.id,
						'taxes_id': [(6, 0, line.taxes_id.ids)],
						'purchase_line_id': line.id
					})

	@api.depends('return_line.price_total')
	def _amount_all(self):
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.return_line:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
			order.update({
				'amount_untaxed': order.currency_id.round(amount_untaxed),
				'amount_tax': order.currency_id.round(amount_tax),
				'amount_total': amount_untaxed + amount_tax,
			})

	def _picking_count(self):
		for rec in self:
			rec.picking_count = len(rec.picking_ids)

	def _invoice_count(self):
		for rec in self:
			rec.invoice_count = len(rec.invoice_ids.filtered(lambda x: x.type == 'in_refund'))
		   
	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise Warning(_('You can only delete the record when its in draft state'))  # Зөвхөн ноорог буцаалтыг устгах боломжтой
		return super(PurchaseReturn, self).unlink()

	def action_view_pickings(self):
		self.ensure_one()
		action = self.env.ref('stock.action_picking_tree_all').read()[0]
		action['domain'] = [('purchase_return_id', '=', self.id)]
		action['context'] = dict(self._context, default_purchase_return_id=self.id, create=False)
		return action

	def action_view_invoices(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_in_refund_type').read()[0]
		action['domain'] = [('purchase_return_id', '=', self.id), ('type', '=', 'in_refund')]
		action['context'] = dict(self._context, default_purchase_return_id=self.id, create=False)
		return action

	def calculate(self):
		self.ensure_one()
		order = self
		if not order.return_line:
			raise Warning(_('Please choose returning products'))  # Буцаах бараануудаа сонгоно уу
		check_line_qty = False
		for line in order.return_line:
			if line.qty > 0:
				check_line_qty = True
				break
		if not check_line_qty:
			raise Warning(_('Please enter amount of returning products'))  # Буцаах барааны тоог оруулна уу
		for line in order.return_line:
			if line.qty > 0:
				if line.lot_id:
					self.env.cr.execute("""
						SELECT sum(quantity) as qty
						FROM stock_quant
						WHERE company_id = %s
						AND product_id = %s
						AND location_id = %s
						AND lot_id = %s
						group by product_id
						""", (order.company_id.id, line.product_id.id, order.warehouse_id.lot_stock_id.id, line.lot_id.id))
				else:
					self.env.cr.execute("""
						SELECT sum(quantity) as qty
						FROM stock_quant
						WHERE company_id = %s
						AND product_id = %s
						AND location_id = %s
						group by product_id
						""", (order.company_id.id, line.product_id.id, order.warehouse_id.lot_stock_id.id))
				quants = self.env.cr.dictfetchall()
				if quants:
					qty = quants[0]['qty']
					if line.product_uom != line.product_id.uom_id:
						qty = line.product_id.uom_id._compute_quantity(qty, line.product_uom, round=False)
					line.available_qty = qty
		order.state = 'calculated'

	def confirm(self):
		order = self
		location_src_id = order.warehouse_id.in_type_id.return_picking_type_id.default_location_src_id.id
		location_dest = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
		if not location_dest:
			raise Warning(_('Vendor location not found'))  # Нийлүүлэгчийн байрлал олдсонгүй
		location_dest_id = location_dest.id
		picking_type_id = order.warehouse_id.out_type_id.id

		new_picking = self.env['stock.picking'].create({
			'company_id': order.company_id.id,
			'location_id': location_src_id,
			'location_dest_id': location_dest_id,
			'picking_type_id': picking_type_id,
			'partner_id': order.partner_id.id,
			'origin': order.name,
			'purchase_return_id': order.id
		})

		for line in order.return_line:
			line_qty = line.qty
			if line.product_uom != line.product_id.uom_id:
				line_qty = line.product_uom._compute_quantity(line_qty, line.product_id.uom_id, round=False)
			if line_qty > 0:
				name = line.product_id.name_get()[0][1]
				new_move = self.env['stock.move'].create({
					'company_id': order.company_id.id,
					'product_id': line.product_id.id,
					'name': name,
					'product_uom_qty': line_qty,
					'product_uom': line.product_id.uom_id.id,
					'picking_id': new_picking.id,
					'location_id': location_src_id,
					'location_dest_id': location_dest_id,
					'picking_type_id': picking_type_id,
					'warehouse_id': order.warehouse_id.id,
					'procure_method': 'make_to_stock',
					'state': 'draft',
					'origin': order.name,
					'purchase_return_line_id': line.id
				})
		new_picking.action_confirm()  
		# Зурвас үүсгэх
		new_picking.message_post_with_view(
			'mail.message_origin_link',
			values={'self': new_picking, 'origin': order},
			subtype_id=self.env.ref('mail.mt_note').id
		)

		# Нэхэмжлэл буцаах
		refund_invoice = self.env['account.move'].with_context({'default_type': 'in_refund'}).create({
			'currency_id': order.currency_id.id,
			'type': 'in_refund',
			'partner_id': order.partner_id.id,
			'ref': order.name
		})
		for line in order.return_line:
			fiscal_position = refund_invoice.fiscal_position_id
			accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
			refund_invoice.write({
				'invoice_line_ids': [(0, 0, {
					'move_id': refund_invoice.id,
					'product_id': line.product_id.id,
					'account_id': accounts['expense'].id,
					'quantity': line.qty,
					'product_uom_id': line.product_uom.id,
					'price_unit': line.price_unit,
					'tax_ids': [(6, 0, line.taxes_id.ids)]
				})]
			})
		refund_invoice.purchase_return_id = order
		refund_invoice.action_post()

		order.state = 'confirmed'

	def create_move(self):
		order = self
		location_src_id = order.warehouse_id.in_type_id.return_picking_type_id.default_location_src_id.id
		location_dest = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
		if not location_dest:
			raise Warning(_('Vendor location not found'))  # Нийлүүлэгчийн байрлал олдсонгүй
		location_dest_id = location_dest.id
		picking_type_id = order.warehouse_id.out_type_id.id

		new_picking = self.env['stock.picking'].create({
			'location_id': location_src_id,
			'location_dest_id': location_dest_id,
			'picking_type_id': picking_type_id,
			'partner_id': order.partner_id.id,
			'origin': order.name,
			'purchase_return_id': order.id
		})

		for line in order.return_line:
			if line.not_stock_move_created_qty > 0:
				line_qty = line.not_stock_move_created_qty
				if line.product_uom != line.product_id.uom_id:
					line_qty = line.product_uom._compute_quantity(line_qty, line.product_id.uom_id, round=False)
				if line_qty > 0:
					name = line.product_id.name_get()[0][1]
					new_move = self.env['stock.move'].create({
						'product_id': line.product_id.id,
						'name': name,
						'product_uom_qty': line_qty,
						'product_uom': line.product_id.uom_id.id,
						'picking_id': new_picking.id,
						'location_id': location_src_id,
						'location_dest_id': location_dest_id,
						'picking_type_id': picking_type_id,
						'warehouse_id': order.warehouse_id.id,
						'procure_method': 'make_to_stock',
						'state': 'draft',
						'origin': order.name,
						'purchase_return_line_id': line.id
					})
		# Зурвас үүсгэх
		new_picking.message_post_with_view(
			'mail.message_origin_link',
			values={'self': new_picking, 'origin': order},
			subtype_id=self.env.ref('mail.mt_note').id
		)

	def to_draft(self):
		self.write({'state': 'draft'})

	def finish(self):
		self.ensure_one()
		for line in self.return_line:
			not_stock_move_created_qty = line.not_stock_move_created_qty
			line.not_stock_move_created_qty = 0
			qty = line.qty - not_stock_move_created_qty
			if qty > 0:
				line.qty = qty
			else:
				line._compute_sent_qty()
		self.state = 'done'


class PurchaseReturnLine(models.Model):
	_name = 'purchase.return.line'
	_description = 'Purchase Batch Return Line'

	return_id = fields.Many2one('purchase.return', 'PO return', ondelete='cascade')  # ХА-н буцаалт
	product_id = fields.Many2one('product.product', 'Product', ondelete='restrict', required=True)  # Бараа
	qty = fields.Float('Unit of measure', digits='Product Unit of Measure', default=1.0)
	product_uom = fields.Many2one('uom.uom', 'UOM', required=True)  # Хэмжих нэгж
	price_unit = fields.Float(compute='_compute_price_unit', default=0.0, string='Price unit', required=True, digits='Product Price', store=True, copy=False)  # Нэгж үнэ
	price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal amount', store=True)  # Дэд дүн
	price_total = fields.Float(compute='_compute_amount', string='Total amount', store=True)  # Нийт дүн
	price_tax = fields.Float(compute='_compute_amount', string='Tax amount', store=True)  # Татварын дүн
	taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])  # Татварууд
	lot_id = fields.Many2one('stock.production.lot', 'Lot')  # Цуврал
	purchase_line_id = fields.Many2one('purchase.order.line', 'PO lines')  # ХА-н мөр
	available_qty = fields.Float('Remaining Qty', digits='Product Unit of Measure')  # Үлдэгдэл
	stock_moves = fields.One2many('stock.move', 'purchase_return_line_id', 'Return stock moves')  # Буцаасан барааны хөдөлгөөнүүд
	not_sent_qty = fields.Float('Not sent qty', digits='Product Unit of Measure', compute='_compute_sent_qty', store=True)  # Илгээгээгүй тоо хэмжээ
	sent_qty = fields.Float('Sent qty', digits='Product Unit of Measure', compute='_compute_sent_qty', store=True)  # Илгээсэн тоо хэмжээ
	not_stock_move_created_qty = fields.Float(
		'Not created stock moves',
		digits='Product Unit of Measure',
		compute='_compute_not_stock_move_created_qty', store=True)  # Зарлага үүсээгүй тоо хэмжээ

	@api.constrains('qty')
	def _check_qty(self):
		for line in self:
			if line.qty <= 0:
				raise ValidationError(_("%s product's qty must be higher than 0") % line.product_id.name)  # барааны хувьд тоо хэмжээ нь 0-с их байх ёстой

	@api.depends('stock_moves', 'stock_moves.state', 'stock_moves.quantity_done', 'product_uom', 'qty')
	def _compute_sent_qty(self):
		for line in self:
			sent_qty = sum(line.stock_moves.filtered(lambda x: x.state == 'done').mapped('quantity_done'))
			if line.product_uom != line.product_id.uom_id:
				sent_qty = line.product_id.uom_id._compute_quantity(sent_qty, line.product_uom, round=False)
			line.sent_qty = sent_qty
			line.not_sent_qty = line.qty - sent_qty

	@api.depends('stock_moves', 'stock_moves.product_uom_qty', 'stock_moves.state', 'stock_moves.quantity_done', 'product_uom', 'qty')
	def _compute_not_stock_move_created_qty(self):
		for line in self:
			not_done_qty = sum(line.stock_moves.filtered(lambda x: x.state != 'done').mapped('product_uom_qty'))
			done_qty = sum(line.stock_moves.filtered(lambda x: x.state == 'done').mapped('quantity_done'))
			if line.product_uom != line.product_id.uom_id:
				not_done_qty = line.product_id.uom_id._compute_quantity(not_done_qty, line.product_uom, round=False)
				done_qty = line.product_id.uom_id._compute_quantity(done_qty, line.product_uom, round=False)
			line.not_stock_move_created_qty = line.qty - (not_done_qty + done_qty)

	@api.depends('product_id', 'taxes_id', 'purchase_line_id', 'product_uom')
	def _compute_price_unit(self):
		for line in self:
			if line.purchase_line_id:
				price_unit = line.purchase_line_id.price_unit
				if line.purchase_line_id.taxes_id:
					price_unit = line.purchase_line_id.taxes_id.with_context(round=False).compute_all(
						price_unit,
						currency=line.purchase_line_id.order_id.currency_id,
						quantity=1.0)['total_excluded']
				if line.purchase_line_id.currency_id != line.return_id.currency_id:
					price_unit = line.purchase_line_id.currency_id._convert(price_unit, line.return_id.currency_id, line.return_id.company_id, fields.Date.context_today(self), round=False)
			else:
				price_unit = line.get_current_cost()

			if line.purchase_line_id:
				if line.product_uom and line.product_uom != line.purchase_line_id.product_uom:
					price_unit *= line.purchase_line_id.product_uom.factor / line.product_uom.factor
			else:
				if line.product_uom and line.product_uom != line.product_id.uom_id:
					price_unit *= line.product_id.uom_id.factor / line.product_uom.factor

			if line.taxes_id:
				price_unit = line.taxes_id.with_context(round=False).compute_all(
					price_unit,
					currency=line.return_id.currency_id,
					quantity=1.0,
					handle_price_include=False)['total_included']
			line.price_unit = price_unit

	def get_current_cost(self):
		self.ensure_one()
		cost = self.product_id.standard_price
		if self.product_id.cost_method == 'fifo':
			svl = self.env['stock.valuation.layer'].search([
				('product_id', '=', self.product_id.id),
				('company_id', '=', self.return_id.company_id.id),
				('remaining_qty', '>', 0)
			], limit=1, order='create_date, id')
			if svl:
				cost = svl.unit_cost
		return cost

	@api.depends('qty', 'price_unit', 'taxes_id')
	def _compute_amount(self):
		for line in self:
			vals = line._prepare_compute_all_values()
			taxes = line.taxes_id.compute_all(
				vals['price_unit'],
				vals['currency_id'],
				vals['qty'],
				vals['product'],
				vals['partner'])
			line.update({
				'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})

	def _prepare_compute_all_values(self):
		self.ensure_one()
		return {
			'price_unit': self.price_unit,
			'currency_id': self.return_id.currency_id,
			'qty': self.qty,
			'product': self.product_id,
			'partner': self.return_id.partner_id,
		}

	@api.onchange('product_id')
	def onchange_product_id(self):
		for line in self:
			if line.product_id:
				line.product_uom = line.product_id.uom_id
			line.taxes_id = line.return_id.taxes_id
