# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from odoo.tools import float_is_zero, OrderedSet
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
	_inherit = "stock.picking"
	
	change_date = fields.Datetime('Өөрчлөх Огноо', copy=False)
	is_change_date = fields.Boolean('Огноо гараар өөрчилсөн эсэх', default=False, copy=False)

	def resolve_price_unit_with(self, product_id, move_id):
		resolve_obj = self.env['stock.move.resolve.price.unit']
		resolve_id = resolve_obj.create({
			'product_id': product_id.id,
			'move_id': move_id.id
			})
		resolve_id.calc_input()
		resolve_id.calc_first()
		resolve_id.calc_update()
		resolve_id.calc_stock_move_find()
		resolve_id.calc_stock_move_price_unit_resolve()
		
	def update_change_done_date_only(self):
		self.with_context(resolve_price_unit_with=True).update_change_done_date()
		self.update_change_done_date()


	def update_change_done_date(self):
		if not self.change_date:
			change_date = self.scheduled_date
		else:
			change_date  = self.change_date
		
		scheduled_date = change_date+timedelta(hours=8)
		sched_date = scheduled_date.strftime( "%Y-%m-%d")
		
		

		self.date_done = self.change_date
		self.move_ids.write({'date': change_date})
		self.move_line_ids.write({'date': change_date})
		# self.env['account.move.line'].search([('move_id.stock_move_id','in',self.move_ids.ids)]).write({'date':sched_date})
		
		# SHUUD ongoo uurchilunguut tsaashdiin hudulguuniig zasdag bolgov
		
		for item in self.move_ids:
			if item.product_id.type=='product':
				end_date = item.date
				query1 = """
					SELECT product_id, location_id,sum(qty) as qty FROM (
					  SELECT 
						  sm.product_id as product_id,
						  sl.id as location_id,
						  sm.qty_done as qty
					  FROM stock_move_line as sm
					  LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					  LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					  LEFT JOIN stock_location as sl on (sm.location_dest_id = sl.id)
					  LEFT JOIN stock_location as sl2 on (sm.location_id = sl2.id)
					  WHERE sm.state = 'done'
							and sm.date<='{0}'
							and sm.product_id={1}
							and sm.company_id={2}
					  UNION ALL
					  SELECT 
						  sm.product_id as product_id,
						  sl.id as location_id,
						  -sm.qty_done as qty
					  FROM stock_move_line as sm
					  LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					  LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					  LEFT JOIN stock_location as sl on (sm.location_id = sl.id)
					  LEFT JOIN stock_location as sl2 on (sm.location_dest_id = sl2.id)
					  WHERE sm.state = 'done'
							and sm.date<='{0}'
							and sm.product_id={1}
							and sm.company_id={2}
						  
				  ) as temp GROUP BY  product_id,location_id
				"""
				
				query1 = query1.format(end_date, item.product_id.id, item.company_id.id)
				if not self.env.context.get('resolve_price_unit_with',False):
					self.env.cr.execute(query1)
					query_result = self.env.cr.dictfetchall()
					if query_result:
						for item_res in query_result:
							loc_id =  self.env['stock.location'].browse(item_res['location_id'])
							if float(item_res['qty'])<0 and loc_id.usage=='internal':
								raise UserError(u'%s барааг %s байрлал дээр Энэ огноогоор солиход тоо хэмжээг хасах болгож байна. %s'%(item.product_id.display_name, loc_id.display_name, float(item_res['qty'])))
				# if not self.env.context.get('resolve_price_unit_with',False):
					# self.resolve_price_unit_with(item.product_id, item)
			#Данс хаасан мөчлөг хаасан шалгах
			for am in item.account_move_ids:
				am._check_fiscalyear_lock_date(check_date=sched_date)
		
		sql_query = """
				UPDATE account_move set date='{1}' WHERE stock_move_id in (
					SELECT id FROM stock_move WHERE picking_id={0}
				);
				UPDATE account_move_line set date='{1}' WHERE move_id in (SELECT id FROM account_move WHERE stock_move_id in (
					SELECT id FROM stock_move WHERE picking_id={0}
				));
				UPDATE account_analytic_line set date='{1}'
					FROM account_move_line aml
					LEFT JOIN account_move am on am.id=aml.move_id
					LEFT JOIN stock_move sm on sm.id=am.stock_move_id
					WHERE account_analytic_line.move_line_id=aml.id and sm.picking_id = {0};
				""".format(self.id, sched_date)
		
		self.env.cr.execute(sql_query)
		account_move_id = self.env['account.move'].sudo().search([('stock_move_id.picking_id','=',self.id)])
		account_move_id.name = False
		account_move_id._compute_name()
		print(account_move_id)
		self.is_change_date = True


	def junior_date_change(self):
		if not self.change_date:
			raise UserError(u'Солих огноог оруулна уу!!!')
		else:
			scheduled_date = self.change_date+timedelta(hours=8)
			new_scheduled_date=self.scheduled_date+timedelta(hours=8)
			# print('pint2141224124124',scheduled_date)
			# print('pint2421412421421',self.scheduled_date)

			if abs(scheduled_date - new_scheduled_date) <= timedelta(hours=24) or scheduled_date == new_scheduled_date:
				# print('sadsafsafasfsaf',abs(self.change_date - self.scheduled_date) <= timedelta(hours=24) or self.change_date == self.scheduled_date)
				self.update_change_done_date()
			else:
				raise UserError(u'Солих огноо товлогдсон огнооноос 1 хоногийн зөрүүтэй байх боломжтой!!!')


	def action_create_account_entry(self):
		i = 1
		for res in self.move_ids.filtered(lambda r: r.state == 'done'):
			for move in res.filtered(lambda m: m.product_id.valuation == 'real_time' and (m._is_in() or m._is_out() or m._is_dropshipped())):
				move.create_account_move_hand()
			i += 1

class StockMode(models.Model):
	_inherit = 'stock.move'

	def _get_out_move_lines(self):
		""" Returns the `stock.move.line` records of `self` considered as outgoing. It is done thanks
		to the `_should_be_valued` method of their source and destionation location as well as their
		owner.

		:returns: a subset of `self` containing the outgoing records
		:rtype: recordset
		"""
		res = self.env['stock.move.line']
		for move_line in self.move_line_ids:
			# sanhuu bichilt uusehgui bolohoor
			# if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
			#     continue
			if move_line.location_id._should_be_valued() and not move_line.location_dest_id._should_be_valued():
				res |= move_line
		return res

	def _get_in_move_lines(self):
		""" Returns the `stock.move.line` records of `self` considered as incoming. It is done thanks
		to the `_should_be_valued` method of their source and destionation location as well as their
		owner.

		:returns: a subset of `self` containing the incoming records
		:rtype: recordset
		"""
		self.ensure_one()
		res = OrderedSet()
		for move_line in self.move_line_ids:
			# sanhuu bichilt uusehgui bolohoor
			# if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
			#     continue
			if not move_line.location_id._should_be_valued() and move_line.location_dest_id._should_be_valued():
				res.add(move_line.id)
		return self.env['stock.move.line'].browse(res)

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
			if not self.env['account.move'].search([('stock_move_id','=',item.id)]) and item.product_id.valuation == 'real_time' and (item._is_in() or item._is_out() or item._is_dropshipped()):
				stock_valuation_layers = item.stock_valuation_layer_ids
				for svl in stock_valuation_layers:
					# print('svlsvlsvlsvlsvl: ', svl)
					if not svl.product_id.valuation == 'real_time' or svl.account_move_id:
						pass
					else:
						vals = svl.stock_move_id.sudo()._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
						if vals:
							account_moves = self.env['account.move'].sudo().create(vals)
							account_moves.sudo().write({'date': item.date.date()})
							account_moves.sudo().action_post()
						# self.update_account_move_date(svl.stock_move_id, svl.stock_move_id.date)

	def update_change_done_date(self):
		if self.picking_id:
			raise UserError(u'Баримттай байна баримтаас орж огноог өөчилнө үү')

		up_date = self.env['stock.move.update.date']
		up_id = up_date.create({
			'move_id': self.id,

			})
		view_id = self.env.ref('mw_stock_account.stock_move_update_date_form')
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'stock.move.update.date',
			'res_id': up_id.id,
			'view_mode': 'form',
			'views': [(view_id.id, 'form')],
			'view_id': view_id.id,
			'target': 'new',
		}
	
	def update_account_move_date(self, stock_move_id, change_date):
		scheduled_date = change_date+timedelta(hours=8)
		sched_date = scheduled_date.strftime( "%Y-%m-%d")
		sql_query = """
		UPDATE account_move set date='{1}' where stock_move_id={0};
		update  account_move_line set date='{1}' where move_id in (select id from account_move where  stock_move_id ={0}
		);
				""".format(stock_move_id.id, sched_date)
		self.env.cr.execute(sql_query)

class Createaccountmovehand(models.TransientModel):
	_name = "selected.account.move.create.hand"
	_description = "selected account move create han"

	def create_move_hand(self):
		moves = self.env['stock.move'].browse(self._context['active_ids'])
		for move in moves:
			move.create_account_move_hand()

class StockModeUpdateDate(models.TransientModel):
	_name = 'stock.move.update.date'
	_description = 'stock.move.update.date'

	move_id = fields.Many2one('stock.move', 'Change move date')
	change_date = fields.Datetime('Өөрчлөх Огноо', copy=False)
	is_change_date = fields.Boolean('Огноо гараар өөрчилсөн эсэх', default=False, copy=False)

	def update_change_done_date(self):
		
		scheduled_date = self.change_date+timedelta(hours=8)
		sched_date = scheduled_date.strftime( "%Y-%m-%d")
		
		# self.date_done = self.change_date
		self.move_id.write({'date': self.change_date})
		self.move_id.move_line_ids.write({'date': self.change_date})
		# SHUUD ongoo uurchilunguut tsaashdiin hudulguuniig zasdag bolgov
		resolve_obj = self.env['stock.move.resolve.price.unit']
		for item in self.move_id:
			if item.product_id.type=='product':
				# print bllbl
				end_date = item.date
				query1 = """
					SELECT product_id, location_id, sum(amount) as amount, sum(qty) as qty FROM (
					  SELECT 
						  sm.product_id as product_id,
						  sl.id as location_id,
						  (sm.product_uom_qty * abs(sm.price_unit)) as amount,
						  sm.product_uom_qty as qty
					  FROM stock_move as sm
					  LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					  LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					  LEFT JOIN stock_location as sl on (sm.location_dest_id = sl.id)
					  LEFT JOIN stock_location as sl2 on (sm.location_id = sl2.id)
					  WHERE sm.state = 'done'
							and sm.date<='{0}'
							and sm.product_id={1}
							and sm.company_id={2}
					  UNION ALL
					  SELECT 
						  sm.product_id as product_id,
						  sl.id as location_id,
						  -abs(sm.product_uom_qty * abs(sm.price_unit)) as amount,
						  -sm.product_uom_qty as qty
					  FROM stock_move as sm
					  LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					  LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					  LEFT JOIN stock_location as sl on (sm.location_id = sl.id)
					  LEFT JOIN stock_location as sl2 on (sm.location_dest_id = sl2.id)
					  WHERE sm.state = 'done'
							and sm.date<='{0}'
							and sm.product_id={1}
							and sm.company_id={2}
						  
				  ) as temp GROUP BY  product_id,location_id
				"""
				
				query1 = query1.format(end_date, item.product_id.id, item.company_id.id)
				
				self.env.cr.execute(query1)
				query_result = self.env.cr.dictfetchall()
				if query_result:
					for item_res in query_result:
						loc_id =  self.env['stock.location'].browse(item_res['location_id'])
						if float(item_res['qty'])<0 and loc_id.usage=='internal':
							raise UserError(u'%s барааг %s байрлал дээр Энэ огноогоор солиход тоо хэмжээг хасах болгож байна. %s'%(item.product_id.display_name, loc_id.display_name, float(item_res['qty'])))

				resolve_id = resolve_obj.create({
					'product_id': item.product_id.id,
					'move_id': item.id
					})
				resolve_id.calc_input()
				resolve_id.calc_first()
				resolve_id.calc_update()
				resolve_id.calc_stock_move_find()
				resolve_id.calc_stock_move_price_unit_resolve()
				#Данс хаасан мөчлөг хаасан шалгах
				for am in self.move_id.account_move_ids:
					am._check_fiscalyear_lock_date(check_date=sched_date)


		sql_query = """
				UPDATE account_move set date='{1}' where stock_move_id={0};
				update  account_move_line set date='{1}' where move_id in (select id from account_move where  stock_move_id ={0});
				UPDATE account_analytic_line set date='{1}'
								FROM account_move_line aml
								WHERE account_analytic_line.move_line_id=aml.id and  aml.move_id={0};
					""".format(self.move_id.id, sched_date)
		
		self.env.cr.execute(sql_query)
		account_move_id = self.env['account.move'].sudo().search([('stock_move_id','=',self.move_id.id)])
		account_move_id.name = False
		account_move_id._compute_name()
		self.is_change_date = True

