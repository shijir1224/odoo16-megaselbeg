# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	move_many_ids = fields.Many2many('stock.move', 'purchase_order_line_create_stock_move_rel', 'stock_move_id',
									 'purchase_line_id', string='Хүсэлтийн мөрүүд')


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	is_salbar_zahialga = fields.Boolean('Салбарын захиалга', default=False, copy=False)

	@api.model
	def create(self, vals):
		if vals.get('location_id', False):
			wh_id = self.env['stock.location'].browse(vals.get('location_id', False)).set_warehouse_id
			if wh_id.is_salbar_zahialga:
				vals['is_salbar_zahialga'] = True
		return super(StockPicking, self).create(vals)

class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'

	is_salbar_zahialga = fields.Boolean('Салбарын захиалга авдаг агуулах', default=False, copy=False)

class StockMove(models.Model):
	_inherit = 'stock.move'

	is_over = fields.Boolean('Дахиж авахгүй', default=False, copy=False)
	qty_created_po = fields.Float('QTY PO created', default=0.0, copy=False)
	po_l_ids = fields.Many2many('purchase.order.line', 'purchase_order_line_create_stock_move_rel', 'purchase_line_id',
								'stock_move_id', string='PO Мөрүүд')
	po_qty = fields.Float('PO Үүссэн Тоо', compute='_compute_po_diff_qty', default=0, copy=False, store=True)
	po_diff_qty = fields.Float('PO Үүсгэх Тоо', compute='_compute_po_diff_qty', copy=False, store=True)
	product_residual = fields.Float('Хангамжийн агуулахын үлдэгдэл', compute='_compute_product_residual', copy=False,
									store=True)

	@api.depends('picking_id.location_id', 'location_id', 'product_id')
	def _compute_product_residual_without_res(self):
		for item in self:
			location_id = item.picking_id.location_id or item.location_id
			if location_id.usage == 'internal' and item.product_id.type == 'product' and item.state not in ['done', 'cancel']:
				qty = sum(item.product_id.stock_quant_ids.filtered(lambda r: r.location_id.id == location_id.id).mapped('quantity'))
				item.product_residual_without_res = qty
			else:
				item.product_residual_without_res = 0

	@api.depends('location_id', 'product_id')
	def _compute_product_residual(self):
		quant = self.env['stock.quant']
		for item in self:
			item.product_residual = sum(quant.sudo().search([('location_id', '=', item.location_id.id), ('product_id', '=', item.product_id.id)]).mapped('quantity'))

	@api.depends('po_l_ids.product_qty', 'product_uom_qty', 'po_l_ids.state')
	def _compute_po_diff_qty(self):
		for item in self:
			po_created_qty = item.product_uom_qty - sum(
				item.po_l_ids.filtered(lambda r: r.state != 'cancel').mapped('product_qty'))
			item.po_qty = sum(item.po_l_ids.filtered(lambda r: r.state != 'cancel').mapped('product_qty'))
			item.po_diff_qty = po_created_qty if po_created_qty > 0 else 0

class StockMovePoCreate(models.TransientModel):
	_name = 'stock.move.po.create'
	_description = 'Purchase Order Create'

	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	partner_ids = fields.Many2many('res.partner', 'stock_move_po_create_res_partner_rel', 'move_id', 'par_id', 'Харилцагчид')
	is_comparison = fields.Boolean('Харьцуулалттай эсэх', default=False)
	is_po_qty_edit = fields.Boolean('Худалдан авалтын тоог өөрчлөх', default=False)
	date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
	user_id = fields.Many2one('res.users', string='Оноох Хангамжийн Ажилтан')
	flow_id = fields.Many2one('dynamic.flow', string='Худалдан авалтын урсгал тохиргоо',
							  domain="[('model_id.model', '=', 'purchase.order')]")
	warehouse_id = fields.Many2one('stock.warehouse', string='Худалдан авах агуулах')
	to_warehouse_id = fields.Many2one('stock.warehouse', string='Дотоод хөдөлгөөнөөр явуулах')
	line_ids = fields.One2many('stock.move.po.create.line', 'parent_id', 'Мөр')
	purchase_sub_id = fields.Many2one('purchase.order', 'Нэмэгдэх PO')
	is_sub_po = fields.Boolean('Худалдан авалтын захиалганд нэгтгэх', default=False)

	@api.onchange('is_po_qty_edit', 'partner_id', 'flow_id', 'date')
	def onch_is_po_qty_edit(self):
		obj = self.env['stock.move'].browse(self._context['active_ids'])
		line_ids = []
		quant = self.env['stock.quant']

		for item in obj:
			product_residual = sum(quant.sudo().search(
				[('location_id', '=', item.location_id.id), ('product_id', '=', item.product_id.id)]).mapped(
				'quantity'))
			line_ids.append({'sm_id': item.id, 'product_id': item.product_id.id, 'qty': item.product_uom_qty,
							 'po_qty': item.po_diff_qty, 'product_residual': product_residual})
		if not self.line_ids and line_ids:
			self.line_ids = self.env['stock.move.po.create.line'].create(line_ids)

	def get_sm_po_line(self, product_id, re_lines, date, po_id, uom_id):
		return {
			'product_id': product_id.id,
			'name': '1',
			'date_planned': date,
			'product_qty': sum(re_lines.mapped('po_qty')) if self.is_po_qty_edit else sum(re_lines.mapped('qty')),
			'price_unit': 1,
			'product_uom': uom_id.id,
			'order_id': po_id.id,
			'move_many_ids': [(6, 0, re_lines.mapped('sm_id').ids)],
		}

	def action_done(self):
		obj = self.line_ids
		obj_sm_ids = obj.mapped('sm_id')
		if obj_sm_ids.filtered(lambda r: r.po_l_ids and r.po_diff_qty <= 0):
			raise ValidationError(_('Purchase order created!'))

		if obj.filtered(lambda r: not r.product_id):
			raise ValidationError('Бараа сонгогдоогүй Хүсэлт байна Бараагаа үүсгэнэ үү')

		if not self.is_sub_po:
			search_domain = [('flow_id', '=', self.flow_id.id)]
			flow_line_id = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
			vals = {
				'date_order': self.date,
				'flow_id': self.flow_id.id,
				'picking_type_id': self.warehouse_id.in_type_id.id,
				'date_planned': self.date,
				'flow_line_id': flow_line_id,
				'state': 'draft',
			}
			if self.is_comparison:
				vals['partner_id'] = self.partner_ids[0].id
				vals['is_comparison'] = True
			else:
				vals['partner_id'] = self.partner_id.id
			po_id = self.env['purchase.order'].create(vals)
		else:
			po_id = self.purchase_sub_id
		res = []
		linevals = []
		product_ids = obj.mapped('product_id')
		for item in product_ids:
			re_lines = obj.filtered(lambda r: r.product_id.id == item.id)
			found_po_line_id = False
			if self.is_sub_po:
				found_po_line_id = po_id.order_line.filtered(lambda r: r.product_id.id == item.id)
				if found_po_line_id:
					if len(found_po_line_id) > 1:
						found_po_line_id = found_po_line_id[0]
					add_prline_qty = sum(re_lines.mapped('po_qty')) if self.is_po_qty_edit else sum(
						re_lines.mapped('sm_id.product_uom_qty'))
					add_prline_qty += found_po_line_id.product_qty
					move_many_ids = [(6, 0, found_po_line_id.move_many_ids.ids + re_lines.mapped('sm_id').ids)]
					found_po_line_id.write({
						'product_qty': add_prline_qty,
						'move_many_ids': move_many_ids
					})
				else:
					po_line_vals = self.get_sm_po_line(item, re_lines, self.date, po_id, item.uom_id)
					po_line_id = self.env['purchase.order.line'].create(po_line_vals)
			else:
				po_line_vals = self.get_sm_po_line(item, re_lines, self.date, po_id, item.uom_id)
				po_line_id = self.env['purchase.order.line'].create(po_line_vals)

		for item in po_id.order_line:
			if item.product_id.type != 'service':
				item._onchange_quantity()

		if self.is_comparison:
			po_id.onchange_is_comparison()
			for item in self.partner_ids:
				con = dict(self._context)
				con['active_id'] = po_id.id
				self.env['purchase.comparison.create'].create({'partner_id': item.id}).with_context(con).action_done()

		return obj

class StockMovePoCreateLine(models.TransientModel):
	_name = 'stock.move.po.create.line'
	_description = 'Purchase Order Create'

	parent_id = fields.Many2one('stock.move.po.create', ondelete='cascade', string='Parent')
	sm_id = fields.Many2one('stock.move', string='Захиалгын мөр')
	product_id = fields.Many2one('product.product', related='sm_id.product_id', readonly=True)
	qty = fields.Float(related='sm_id.product_uom_qty', string='Хүссэн тоо хэмжээ', readonly=True)
	po_qty = fields.Float(string="PO үүсгэх тоо")
	product_residual = fields.Float('Хангамжийн агуулахын үлдэгдэл')

class StockquantMoreReport(models.Model):
	_name = 'stockquant.more.report'
	_description = 'Агуулахын үлдэгдэл дэлгэрэнгүй'
	_auto = False
	_order = 'date_expected, product_id'

	product_id = fields.Many2one('product.product', string=u'Бараа')
	location_id = fields.Many2one('stock.location', string=u'Эх байрлал')
	location_dest_id = fields.Many2one('stock.location', string=u'Хүрэх байрлал')
	date_expected = fields.Datetime(string=u'Огноо')
	product_uom_qty = fields.Float(string=u'Эхний шаардлага')
	reserved_qty = fields.Float(string=u'Нөөцлөгдсөн')
	product_quant = fields.Float(string=u'Хангамжын агуулахын үлдэгдэл')
	without_reserverd_qty = fields.Float(string=u'Нөөцлөлт хассан')
	state = fields.Selection([('draft', 'Шинэ'),
							  ('cancel', 'Шинэ'),
							  ('waiting', 'Шинэ'),
							  ('confirmed', 'Шинэ'),
							  ('partially_available', 'Шинэ'),
							  ('assigned', 'Шинэ'),
							  ('done', 'Шинэ')], string=u'Төлөв')

class StockquantMoreReportC(models.Model):
	_name = 'stockquant.more.report.c'
	_description = 'Агуулахын үлдэгдэл дэлгэрэнгүй'
	_order = 'date_expected, product_id'

	product_id = fields.Many2one('product.product', string=u'Бараа')
	location_id = fields.Many2one('stock.location', string=u'Эх байрлал')
	picking_id = fields.Many2one('stock.picking', string=u'Баримт')
	report_id = fields.Char(string=u'REP id')
	location_dest_id = fields.Many2one('stock.location', string=u'Хүрэх байрлал')
	date_expected = fields.Datetime(string=u'Огноо')
	product_uom_qty = fields.Float(string=u'Эхний шаардлага')
	reserved_qty = fields.Float(string=u'Нөөцлөгдсөн')
	product_quant_hangamj = fields.Float(string=u'Хангамжын агуулахын үлдэгдэл')
	product_quant = fields.Float(string=u'Бүх агуулахын үлдэгдэл')
	without_reserverd_qty = fields.Float(string=u'Нөөцлөлт хассан')
	state = fields.Char(string=u'Төлөв')

class PurchaseCreateStockMoveReport(models.TransientModel):
	_name = 'purchase.create.stock.move.report'
	_description = 'Purchase create stock move report'

	date_start = fields.Date(string=u'Эхлэх огноо', required=True)
	date_end = fields.Date(string=u'Дуусах огноо', required=True)
	picking_type_id = fields.Many2one('stock.location', string=u'Эх байрлал', domain=[('usage', '=', 'internal')], readonly=True)

	def get_domain(self, domain):
		domain = ['|', (('date_expected', '>=', self.date_start), ('date_expected', '<=', self.date_end), ('location_id', '=', self.picking_type_id.id))]
		domain.append(('|'))
		domain.append()
		if self.picking_type_id:
			domain.append(('location_id', '=', self.picking_type_id.id))
		domain.append(('date_expected', '<=', self.date_end))
		domain.append(('state', 'in', ['null_state']))
		return domain

	def see_report(self):
		domain = []
		action = self.env.ref('mw_purchase_create_stock.stockquat_more_report_c_action')
		vals = action.read()[0]
		query = """
			insert into stockquant_more_report_c (
				product_id,
				picking_id,
				report_id,
				location_id,
				location_dest_id,
				date_expected,
				product_uom_qty,
				reserved_qty,
				product_quant,
				product_quant_hangamj,
				without_reserverd_qty,
				state
			)
			SELECT * from (
			SELECT
				sm.product_id as product_id,
				sm.picking_id,
				{0},
				sm.location_id as location_id,
				sm.location_dest_id as location_dest_id,
				sm.date_expected as date_expected,
				sm.product_uom_qty as product_uom_qty,
				0 as reserved_qty,
				0 as product_quant,
				0 as product_quant_hangamj,
				0 as without_reserverd_qty,
				sm.state as state
			FROM stock_move as sm
			left join stock_picking as s on (sm.picking_id =s.id)
			left join stock_picking_type as t on (s.picking_type_id =t.id)
			WHERE sm.state in ('confirmed','waiting','partially_available','assigned') and t.code='internal' and s.is_salbar_zahialga = true
			union all
				SELECT
				sq.product_id as product_id,
				null::int as picking_id,
				{0},
				sq.location_id as location_id,
				null::int as location_dest_id,
				null as date_expected,
				0 as product_uom_qty,
				sq.reserved_quantity as reserved_qty,
				sq.quantity as product_quant,
				case when sl.id={1} then sq.quantity else 0 end as product_quant_hangamj,
				sq.quantity-sq.reserved_quantity as without_reserverd_qty,
				'null_state' as state
			FROM stock_quant as sq
			LEFT JOIN stock_location sl on (sl.id=sq.location_id)
			WHERE sl.usage='internal'
			and sq.product_id in (SELECT
				sm.product_id
			FROM stock_move as sm
			left join stock_picking as s on (sm.picking_id =s.id)
			left join stock_picking_type as t on (s.picking_type_id =t.id)
			WHERE sm.state in ('confirmed','waiting','partially_available','assigned') and t.code='internal' and s.is_salbar_zahialga = true
			)
			) as ttt
		""".format(self.id, self.picking_type_id.id)
		self.env.cr.execute(query)
		domain.append(('report_id', '=', self.id))
		vals['domain'] = domain
		return vals