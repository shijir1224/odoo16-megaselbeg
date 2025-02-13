# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from psycopg2 import Error
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
import logging
_logger = logging.getLogger(__name__)

class stock_quant_find(models.Model):
	_name = "stock.quant.find"
	_description = 'stock quant find'

	name = fields.Char('Нэр', required=True)
	state = fields.Selection([('draft','Draft'),('done','Засагдсан')], 'State', default='draft')
	line_ids = fields.One2many('stock.quant.find.line', 'parent_id', 'Мөрүүд')
	no_move_line_ids = fields.One2many('stock.quant.find.no.move.line', 'parent_id', 'Stock move-гүй Мөрүүд')
	location_ids = fields.Many2many('stock.location', string='Байрлалууд', domain="[('usage','=','internal')]")
	line_dup_ids = fields.One2many('stock.quant.find.line', 'parent_dup_id', 'Мөрүүд')

	def unlink(self):
		if self.state=='draft':
			raise UserError('Төлөв ноорог биш байна!')
		return super(stock_quant_find, self).unlink()

	def action_done(self):
		if not self.line_ids:
			raise UserError('Мөр хоосон байна!')
		lines = self.env['stock.quant.find.line'].search([('parent_id','=',self.id), ('update_quant','=',False)], limit=100)
		for item in lines:
			item.update_quant_set()
		
		if len(self.line_ids.filtered(lambda r: r.update_quant)) == len(self.line_ids) and len(self.no_move_line_ids.filtered(lambda r: r.update_quant)) == len(self.no_move_line_ids):
			self.state = 'done'

	def action_no_stock_move_line_update(self):
		if not self.no_move_line_ids:
			raise UserError('Мөр хоосон байна!')
		no_move_lines = self.env['stock.quant.find.no.move.line'].search([('parent_id','=',self.id), ('update_quant','=',False)], limit=100)
		for line in no_move_lines:
			line.update_quant_no_move_lines()

		if len(self.line_ids.filtered(lambda r: r.update_quant)) == len(self.line_ids) and len(self.no_move_line_ids.filtered(lambda r: r.update_quant)) == len(self.no_move_line_ids):
			self.state = 'done'

	def action_done_dup(self):
		self.env['stock.quant']._merge_quants()
		try:
			for item in self.env['stock.quant'].search([('location_id.usage','=','internal'),('company_id','=',self.env.company.id)]):
				item.sudo().before_qty = item.quantity
		except Exception:
			_logger.info('before_qty talbar agloo')
			
		self.state='done'
		# if not self.line_dup_ids:
		#     raise UserError('Mur hooson bn dup')
		# lines = self.env['stock.quant.find.line'].search([('parent_dup_id','=',self.id), ('update_quant','=',False)], limit=100)
		# for item in lines:
		#     item.update_quant_set()
		# if self.line_dup_ids.filtered(lambda r: not r.update_quant):
		#     print ('not')
		# else:
		#     self.state='done'

	def action_draft(self):
		self.state = 'draft'

	def remove_line(self):
		self.line_ids.unlink()

	def remove_no_stock_move_line(self):
		self.no_move_line_ids.unlink()

	def remove_line_dup(self):
		self.line_dup_ids.unlink()

	def get_movees_qty(self, location_id):
		query = """select product_id,lot_id,sum(qty) as qty from (
				SELECT
				sml.product_id,
				sml.lot_id,
				sum(sml.qty_done/uu.factor) as qty

				FROM stock_move_line as sml
				LEFT JOIN product_product as pp on (pp.id = sml.product_id)
				LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
				LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)

				WHERE sml.state = 'done' and sml.location_dest_id={0} and pt.type='product'
				GROUP BY sml.product_id,sml.lot_id

				UNION ALL

				SELECT 
				sml.product_id,
				sml.lot_id,
				-sum(sml.qty_done/uu.factor) as qty

				FROM stock_move_line as sml
				LEFT JOIN product_product as pp on (pp.id = sml.product_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
				LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)

				WHERE sml.state = 'done' and sml.location_id={0} and pt.type='product'
				GROUP BY sml.product_id,sml.lot_id
				)as ttt
				GROUP BY product_id,lot_id
		""".format( location_id.id)
		self.env.cr.execute(query)
		fetched = self.env.cr.dictfetchall()
		return fetched

	def get_main_uom(self, uom_id):
		return self.env['uom.uom'].search([('category_id','=',uom_id.category_id.id),('uom_type','=','reference')], limit=1)
		
	def action_import(self):
		if self.line_ids:
			raise UserError('Мөр хоосон биш байна!')
		# quant_ids = self.env['stock.quant'].search([('location_id','in',self.location_ids.ids)])
		result = []
		for loc in self.location_ids:
			for item in self.get_movees_qty(loc):
				dom = [('product_id','=',item['product_id']), ('location_id','=',loc.id)]
				if item['lot_id']:
					dom.append(('lot_id','=',item['lot_id']))
				quants = self.env['stock.quant'].search(dom)
				pp_id = self.env['product.product'].browse(item['product_id'])
				move_qty = item['qty']
				if pp_id.uom_id.uom_type!='reference':
					main_uom_id = self.get_main_uom(pp_id.uom_id)
					move_qty = main_uom_id._compute_quantity(item['qty'], pp_id.uom_id, round=False)
				if quants:
					for quant in quants:
						quantity = quant.quantity/pp_id.uom_id.factor
						if pp_id.uom_id.uom_type!='reference':
							quantity = quant.quantity
	
						if not float_is_zero(quantity-move_qty, precision_digits=2):
							vals = {
								'quant_id': quant.id,
								'quant_int_id': quant.id,
								'location_id': loc.id,
								# 'lot_id': quant.lot_id.id,
								'product_id': item['product_id'],
								'quantity': quant.quantity,
								'quantity_move': move_qty,
							}
							result.append((0, 0, vals))
				else:
					if not float_is_zero(0-move_qty, precision_digits=2):
						vals = {
							'location_id': loc.id,
							'product_id': item['product_id'],
							'quantity': 0,
							'quantity_move': move_qty,
						}
						result.append((0, 0, vals))
		if result:
			self.write({'line_ids': result})
	
	def get_qty_dup(self):
		query = """
			select min(sq.id) as quant_id,sq.product_id,sq.location_id,sq.lot_id,sum(sq.quantity) as qty,count(sq.id) from stock_quant sq
			left join stock_location sl on (sl.id=sq.location_id)
			where sl.usage='internal'
			group by sq.product_id,sq.location_id,sq.lot_id
			having count(sq.id)>1
		"""
		self.env.cr.execute(query)
		fetched = self.env.cr.dictfetchall()
		return fetched

	def get_tuple(self, obj):
		if len(obj) > 1:
			return str(tuple(obj))
		else:
			return " ("+str(obj[0])+") "

	def delete_quant(self, ids):
		query = """
			delete from stock_quant where id in {0}
		""".format(self.get_tuple(ids))
		self.env.cr.execute(query)
	
	def action_import_dup(self):
		if self.line_dup_ids:
			raise UserError('Мөр хоосон биш байна!')
		# quant_ids = self.env['stock.quant'].search([('location_id','in',self.location_ids.ids)])
		result = []
		for item in self.get_qty_dup():
			quant_del = self.env['stock.quant'].search([('id','!=',item['quant_id']),('product_id','=',item['product_id']), ('location_id','=',item['location_id']), ('lot_id','=',item['lot_id'])]).ids
			# self.delete_quant(quant_del)
			quantity = item['qty']
			if not float_is_zero(quantity, precision_digits=2):
				vals = {
					'quant_id': item['quant_id'],
					'quant_int_id': item['quant_id'],
					'location_id': item['location_id'],
					'lot_id': item['lot_id'],
					'product_id': item['product_id'],
					'quantity': self.env['stock.quant'].browse(item['quant_id']).quantity,
					'quantity_move': quantity,
				}
				result.append((0, 0, vals))
			# else:
			#     self.delete_quant([item['quant_id']])
		if result:
			self.write({'line_dup_ids': result})

	@api.model
	def merge_quants(self):
		self.sudo()._merge_quants_mw()
		try:
			self.env['stock.quant'].sudo()._unlink_zero_quants()
		except Error as e:
			_logger.info('_unlink_zero_quants: %s', e.pgerror)

	def _merge_quants_mw(self):
		""" In a situation where one transaction is updating a quant via
		`_update_available_quantity` and another concurrent one calls this function with the same
		argument, we’ll create a new quant in order for these transactions to not rollback. This
		method will find and deduplicate these quants.
		"""
		query = """WITH
						dupes AS (
							SELECT min(id) as to_update_quant_id,
								(array_agg(id ORDER BY id))[2:array_length(array_agg(id), 1)] as to_delete_quant_ids,
								SUM(reserved_quantity) as reserved_quantity,
								SUM(quantity) as quantity
							FROM stock_quant
							GROUP BY product_id, company_id, location_id, lot_id, package_id, owner_id
							HAVING count(id) > 1
						),
						_up AS (
							UPDATE stock_quant q
								SET quantity = d.quantity,
									reserved_quantity = d.reserved_quantity
							FROM dupes d
							WHERE d.to_update_quant_id = q.id
						)
				   DELETE FROM stock_quant WHERE id in (SELECT unnest(to_delete_quant_ids) from dupes)
		"""
		try:
			# with self.env.cr.savepoint():
			self.env.cr.execute(query)
		except Error as e:
			_logger.info('an error occured while merging quants: %s', e.pgerror)

	def merge_quants_hand(self):
		self.env['stock.quant'].sudo()._merge_quants()
		self.env['stock.quant'].sudo()._unlink_zero_quants()

	def get_no_movees_qty(self, location_id, product_ids):
		# print('000000', product_ids.ids)
		# print('====================', tuple(product_ids.ids))

		if product_ids:
			if len(product_ids) > 1:
				query = """
					SELECT
					sq.id as id,
					sq.product_id,
					sum(sq.quantity) as qty

					FROM stock_quant as sq
					LEFT JOIN product_product as pp on (pp.id = sq.product_id)
					LEFT JOIN stock_location as sl on (sl.id = sq.location_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)

					WHERE sq.location_id = {0} and pt.type='product' and pp.id not in {1}
					GROUP BY sq.product_id, sq.id
				""".format(location_id.id, tuple(product_ids.ids))
			else:
				query = """
					SELECT
					sq.id as id,
					sq.product_id,
					sum(sq.quantity) as qty

					FROM stock_quant as sq
					LEFT JOIN product_product as pp on (pp.id = sq.product_id)
					LEFT JOIN stock_location as sl on (sl.id = sq.location_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)

					WHERE sq.location_id = {0} and pt.type='product' and pp.id != {1}
					GROUP BY sq.product_id, sq.id
				""".format(location_id.id, product_ids[0].id)
		else:
			query = """
				SELECT
				sq.id,
				sq.product_id,
				sum(sq.quantity) as qty

				FROM stock_quant as sq
				LEFT JOIN product_product as pp on (pp.id = sq.product_id)
				LEFT JOIN stock_location as sl on (sl.id = sq.location_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)

				WHERE sq.location_id = {0} and pt.type='product'
				GROUP BY sq.product_id, sq.id
			""".format(location_id.id)
		# print('--------------', query)
		self.env.cr.execute(query)
		result = self.env.cr.dictfetchall()
		return result

	def action_no_stock_move_import(self):
		if self.no_move_line_ids:
			raise UserError('Мөр хоосон биш байна!')
		result = []
		for loc in self.location_ids:
			products = self.line_ids.filtered(lambda r: r.location_id.id == loc.id).mapped('product_id')
			for item in self.get_no_movees_qty(loc, products):
				# print('-=-=-', item)
				sml = self.env['stock.move.line'].search([('product_id','=',item['product_id']),'|',('location_dest_id','=',loc.id),('location_id','=',loc.id)])
				if not sml:
					vals = {
						'quant_id': item['id'],
						'product_id': item['product_id'],
						'location_id': loc.id,
						'quantity': item['qty'],
					}
					result.append((0, 0, vals))
		if result:
			self.write({'no_move_line_ids': result})

class stock_quant_find_line(models.Model):
	_name = "stock.quant.find.line"
	_description = 'stock quant find line'

	parent_dup_id = fields.Many2one('stock.quant.find', 'Parent DUP', ondelete='cascade')
	parent_id = fields.Many2one('stock.quant.find', 'Parent', ondelete='cascade')
	quant_id = fields.Many2one('stock.quant', 'Үлдэгдэл', readonly=True)
	quant_int_id = fields.Float('Үлдэгдэл ID')
	location_id = fields.Many2one('stock.location', 'Байрлал', readonly=True)
	# lot_id = fields.Many2one('stock.production.lot', 'Lot', readonly=True)
	product_id = fields.Many2one('product.product', 'Бараа', readonly=True)
	quantity = fields.Float('Тоо хэмжээ', readonly=True, digits='Product Unit of Measure')
	quantity_move = fields.Float('Тоо хэмжээ SML', readonly=True, digits='Product Unit of Measure')
	diff_qty = fields.Float('Зөрүү', readonly=True, compute='_compute_diff')
	update_quant = fields.Boolean('Шинэчлэгдсэн', readonly=True, default=False, copy=False)
	
	@api.depends('quantity','quantity_move')
	def _compute_diff(self):
		for item in self:
			item.diff_qty = item.quantity_move - item.quantity
	
	def update_quant_set(self):
		obj = self.env['stock.quant']
		for item in self:
			q_id = obj.search([('product_id','=',item.product_id.id),
			('location_id','=',item.location_id.id),
			('company_id','=',self.env.user.company_id.id),
			# ('lot_id','=',item.lot_id.id)
			])
			s_qty = q_id.quantity
			if not float_is_zero(s_qty-item.quantity, precision_rounding=item.product_id.uom_id.rounding):
				raise UserError('%s baraa uld tentsehee bsan bn %s %s '%(item.product_id.display_name, s_qty,item.quantity))
			if not q_id:
				self.env['stock.quant'].sudo().create({
					'location_id': item.location_id.id, 
					'product_id': item.product_id.id,
					'quantity': item.quantity_move,
					})
				# raise UserError('%s baraa uld tentsehee bsan bn %s %s bhguiee'%(item.product_id.display_name, s_qty,item.quantity))
			else:
				query = """
					update stock_quant set quantity={0} where id={1}
				""".format(item.quantity_move, q_id.id)
				self.env.cr.execute(query)
			item.update_quant=True

class StockQuantFindNoMoveLine(models.Model):
	_name = "stock.quant.find.no.move.line"
	_description = 'Stock quant find no move line'

	parent_id = fields.Many2one('stock.quant.find', 'Parent', ondelete='cascade')
	quant_id = fields.Many2one('stock.quant', 'Үлдэгдэл', readonly=True)
	location_id = fields.Many2one('stock.location', 'Байрлал', readonly=True)
	product_id = fields.Many2one('product.product', 'Бараа', readonly=True)
	quantity = fields.Float('Тоо хэмжээ', readonly=True, digits='Product Unit of Measure')
	update_quant = fields.Boolean('Шинэчлэгдсэн', readonly=True, default=False, copy=False)

	def update_quant_no_move_lines(self):
		obj = self.env['stock.quant']
		for item in self:
			quant_id = obj.search([('product_id','=',item.product_id.id),('location_id','=',item.location_id.id),('company_id','=',self.env.user.company_id.id)
			])
			query = """
				update stock_quant set quantity = 0 where id = {0}
			""".format(quant_id.id)
			self.env.cr.execute(query)
			item.update_quant=True