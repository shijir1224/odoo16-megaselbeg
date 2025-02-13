# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_is_zero

import logging

_logger = logging.getLogger(__name__)

class productTemplate(models.Model):
	_inherit = 'product.template'

	def _search_taslal(self, operator, value):
		domain = []
		if self.env.context.get('taslal_haih',False):
			try:
				value = value
				value_taslal = value.split(',')
				value_taslal = [x.strip().upper() for x in value_taslal]
				domain = ['|','|',('default_code', 'in', value_taslal),('product_code', 'in', value_taslal),('name', 'in', value_taslal)]
		#                 domain = [('name', 'in', value_taslal)]
			except Exception as e:
				pass
		return domain

	name_haih = fields.Char('Таслал Хайх', readonly=True, search='_search_taslal', store=False)

class multiStockMoveResolvePriceUnit(models.Model):
	_name = "multi.stock.move.resolve.price.unit"
	_description = "multi.stock.move.resolve.price.unit"
	
	def get_domain_product(self):
		stock_moves = self.env['stock.move'].search([('company_id','=',self.env.user.company_id.id)])
		products = list(set(stock_moves.mapped('product_id.id')))
		return [('id','in',products)]

	product_ids = fields.Many2many('product.product', string="Products", required=True, domain=get_domain_product)
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id, required=True)
	resolve_ids = fields.One2many('stock.move.resolve.price.unit','parent_id', string="Lines")
	cost_method = fields.Selection(related="product_ids.cost_method", readonly=True)
	count_product = fields.Integer('Нийт бараа', compute="_compute_count", readonly=True)

	@api.constrains('product_ids')
	def _check_limit(self):
		if len(self.product_ids)>100:
			raise ValidationError("Max number of products")

	@api.depends('product_ids')
	def _compute_count(self):
		self.count_product = len(self.product_ids)

	@api.onchange('product_ids')
	def onchange_products(self):
		self.count_product = len(self.product_ids)
		# print('self.count_product', self.count_product)
		self._check_limit()



	def generate_stock_move_resolve_price(self):
		self.ensure_one()
		vals_list = []
		for product in self.product_ids:
			cost_resolve_obj = self.env['stock.move.resolve.price.unit']
			vals = (0, 0, {
				'product_id': product.id,
				'company_id': self.company_id.id,
			})
			vals_list.append(vals)
		self.resolve_ids = vals_list

	def view_reslove_lines(self):
		action = self.env.ref('mw_stock_account.action_stock_move_resolve_price_unit').read()[0]
		action['domain'] = [('ids','in', self.resolve_ids.ids)]
		return action

	# 1.
	def calc_input(self):
		if not self.resolve_ids:
			raise UserError('Угаалтын мөр хоосон байна!\nGenerate товч дарна уу')
		for resolve in self.resolve_ids:
			# print(resolve,)
			resolve.calc_input()
	
	# 2.
	def calc_first(self):
		for resolve in self.resolve_ids:
			resolve.calc_first()
   
	# 3.
	def calc_update(self):
		for resolve in self.resolve_ids:
			resolve.calc_update()
   
	# 4.
	def calc_stock_move_find(self):
		for resolve in self.resolve_ids:
			resolve.calc_stock_move_find()
   
	# 5.
	def calc_stock_move_price_unit_resolve(self):
		for resolve in self.resolve_ids:
			resolve.calc_stock_move_price_unit_resolve()

	def delete_all_line(self):
		for resolve in self.resolve_ids:
			resolve.delete_all_line()
		self.resolve_ids.unlink()
	
	def delete_account_move(self):
		for resolve in self.resolve_ids:
			resolve.delete_account_move()
   
	def create_account_move(self):
		for resolve in self.resolve_ids:
			resolve.create_account_move()

	# 1. calc_input
	# 2. calc_first
	# 3. calc_update
	# 4. calc_stock_move_find
	# 5. calc_stock_move_price_unit_resolve
	# - z delete_all_line

class StockMoveChangePriceUnit(models.Model):
	_name = "stock.move.change.price.unit"
	_description = "Stock move change price.unit"
	_order = "create_date desc"

	change_price_unit = fields.Float("Өөрчлөх Үнэ", required=True, copy=False)
	stock_move_ids = fields.Char("Барааны хөдөлөгөөний IDs", required=True, copy=False)
	change_desc = fields.Char("Өөрлчлөлтийн Тайлбар", readonly=True, copy=False)

	def set_change_price_unit_force(self):
		self.with_context(force_update=True).set_change_price_unit()

	def set_change_price_unit(self):
		move_ids = self.stock_move_ids.split(",")
		move_obj = self.env["stock.move"]
		desc = ""
		if self.change_desc:
			raise UserError("Шинээр үүсгэнэ үү ")
		if self.change_price_unit < 0:
			raise UserError("0-ээс их байна ")

		for item in move_ids:

			move_id = move_obj.browse(int(item))
			if move_id:
				if not self.env.context.get("force_update", False):
					if (
						move_id.location_id.usage == "supplier"
						and move_id.product_id.cost_method != "standard"
					):
						raise UserError(
							"Орлогын хөдөлгөөний нэгж өртөг өөрчлөхгүй1 %s "
							% (move_id.name)
						)
				desc += (
					"Хөдөлгөөний ID %s Бараа %s Хуучин Өртөг %s Шинэ Өртөг %s \n\n"
					% (
						move_id.id,
						move_id.product_id.display_name,
						abs(move_id.price_unit),
						self.change_price_unit,
					)
				)
				move_id.price_unit = self.change_price_unit
				# turdee haav 13 deer buh price unit hasah bolgohgui
				# move_id.price_unit = self.change_price_unit if move_id.price_unit>0 else -1*self.change_price_unit

				stock_valuation_layers = move_id.stock_valuation_layer_ids
				if len(stock_valuation_layers.filtered(lambda r: not r.account_move_id)) > 1:
					raise UserError(
						"Valuation layer 1-ees olon bn %s move_id=%s. sanhvv  biciltgui baina!"
						% (move_id.display_name, move_id.id)
					)
				for svl in stock_valuation_layers.filtered(lambda r: r.quantity != 0):
					svl.value = move_id.price_unit * svl.quantity
					svl.unit_cost = svl.value / svl.quantity
					change_amount = abs(svl.value)
					account_move_id = svl.account_move_id
					# print(account_move_id)
					if account_move_id:
						if sum(account_move_id.invoice_line_ids.mapped('debit')) == 0 or sum(account_move_id.invoice_line_ids.mapped('credit')) == 0:
							sql_query = """
							DELETE FROM account_move where id ={0};
								""".format(account_move_id.id)
							self.env.cr.execute(sql_query)
						else:
							sql_query = """
							UPDATE account_move_line set debit='{0}',amount_currency='{0}' where move_id={1} and debit!=0;
							UPDATE account_move_line set credit='{0}',amount_currency='-{0}' where move_id={1} and credit!=0;
							UPDATE account_move_line set balance=debit-credit where move_id={1};
							UPDATE account_analytic_line set amount=aml.credit-aml.debit
								FROM account_move_line aml
								WHERE account_analytic_line.move_line_id=aml.id and  aml.move_id={1};
							UPDATE account_move set amount_total_signed='{0}', amount_total_in_currency_signed='{0}' where id ={1};
								""".format(
								change_amount, account_move_id.id
							)
							self.env.cr.execute(sql_query)
			else:
				raise UserError("%s id тай stock move олдсонгүй  " % (item))
		if move_ids:
			self.change_desc = desc


class StockMoveWarning(models.Model):
    _name = "stock.move.warning"
    _description = "Stock move warning"
    
    parent_id = fields.Many2one('stock.move.resolve.price.unit', string="Parent")
    name = fields.Char(string="Warning")

class StockMoveResolvePriceUnit(models.Model):
	_name = "stock.move.resolve.price.unit"
	_description = "Stock move resolve price.unit"

	parent_id = fields.Many2one('multi.stock.move.resolve.price.unit', string="Parent")
	product_id = fields.Many2one("product.product", "Бараа", required=True)
	# product_ids = fields.Many2many("product.product", string="Бараанууд", required=True)
	cost_method = fields.Selection(related="product_id.cost_method", readonly=True)
	move_id = fields.Many2one("stock.move", "Барааны хөдөлгөөн")
	picking_id = fields.Many2one(
		"stock.picking", related="move_id.picking_id", store=True
	)
	warning_line_ids = fields.One2many('stock.move.warning','parent_id', string="Warnings")
	# change_price_unit = fields.Float('Өөрчлөх Үнэ', required=True, copy=False)
	# stock_move_ids = fields.Char('Барааны хөдөлөгөөний IDs', required=True, copy=False)
	# change_desc = fields.Char('Өөрлчлөлтийн Тайлбар', readonly=True, copy=False)
	line_in_ids = fields.One2many(
		"stock.move.resolve.price.unit.line", "parent_id", string="Орлогын баримтууд"
	)
	stock_move_ids = fields.One2many(
		"stock.move.resolve.price.unit.stock.move",
		"parent_id",
		string="Засах Хөдөлгөөн",
	)
	stock_move_fisrt_ids = fields.One2many(
		"stock.move.resolve.price.unit.stock.move",
		"first_uld_id",
		string="Засах Хөдөлгөөн",
	)
	st_start_date = fields.Date(
		string="СТ эхлэх огноо", default=fields.Date.context_today
	)
	st_end_date = fields.Date(
		string="СТ дуусах огноо", default=fields.Date.context_today
	)
	company_id = fields.Many2one(
		"res.company", "Компани", default=lambda self: self.env.user.company_id
	)

	def update_svl(self):
		obj = self.env["stock.valuation.layer"]

		query1 = """
			select
				svl.id
			from
				stock_valuation_layer svl
				left join stock_move sm on (sm.id = svl.stock_move_id)
				left join stock_location sl2 on (sl2.id = sm.location_dest_id)
			where
				sl2.usage != 'internal'
				and svl.value > 0
				and svl.product_id =%s
			"""

		query1 = query1 % (self.product_id.id)
		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		# print(query1)

		# for item in query_result:
		# 	print("item", item)
			# stock_valuation_layers = item
			# # if stock_valuation_layers.value>0:
			# stock_valuation_layers.value = -stock_valuation_layers.value
			# stock_valuation_layers.unit_cost = abs(stock_valuation_layers.unit_cost)
			# stock_valuation_layers.value = -stock_valuation_layers.value

	# 1. Тооцоолох
	def calc_input(self):
		if self.line_in_ids:
			raise UserError("Line bn")
		line_obj = self.env["stock.move.resolve.price.unit.line"]
		move_obj = self.env["stock.move"]

		# Бүх орлого
		move_ids = move_obj.search(
			[
				("product_id", "=", self.product_id.id),
				("state", "=", "done"),
				("location_id.usage", "in", ["supplier", "production"]),
				("company_id", "=", self.company_id.id),
			]
		)
		for item in move_ids:
			# if not float_is_zero(
			# 	item.product_uom_qty
			# 	- sum(
			# 		item.move_dest_ids.filtered(lambda l: l.state == "done").mapped(
			# 			"product_uom_qty"
			# 		)
			# 	),
			# 	2,
			# ):
			line_obj.create(
				{
					"parent_id": self.id,
					"stock_move_id_in": item.id,
				}
			)
		self.calc_input_niiluuleh()

	def get_tuple(self, obj):
		if len(obj) > 1:
			return str(tuple(obj))
		else:
			return " (" + str(obj[0]) + ") "

	def calc_input_niiluuleh(self):
		self._cr.commit()
		query1 = """
				SELECT date, max(id) as id from  stock_move_resolve_price_unit_line
				where parent_id=%s
				group by date
			""" % (
			self.id
		)
		self._cr.execute(query1)
		query_result = self._cr.dictfetchall()
		ustgahgui_line = []
		for item in query_result:
			ustgahgui_line.append(item["id"])

		if len(ustgahgui_line) != len(self.line_in_ids):
			ustgah_line = []
			for no_ust in ustgahgui_line:
				obj_id = self.line_in_ids.browse(no_ust)
				tentsuu_nuhduud = self.line_in_ids.filtered(
					lambda r: r.date == obj_id.date and r.id != obj_id.id
				)
				if tentsuu_nuhduud:
					nemeh = 1
					for ttt in tentsuu_nuhduud:
						ssss = ttt.stock_move_id_in.date + timedelta(seconds=nemeh)
						nemeh += 1
						# print("--------", ssss)
						query1 = """
					   update stock_move set date='{0}' where id={1};
					   update stock_move_line set date='{0}' where move_id={1};
					""".format(
							str(ssss), ttt.stock_move_id_in.id
						)
						self.env.cr.execute(query1)
						ttt.date = ssss

						# ttt.stock_move_id_in
						# tentsuu_nuhduud
					# niit = obj_id + tentsuu_nuhduud
		#             niit_urtug = sum([x.price_unit*x.product_uom_qty for x in tentsuu_nuhduud])+ obj_id.price_unit*obj_id.product_uom_qty
		#             niit_too_hemjee = sum([x.product_uom_qty for x in tentsuu_nuhduud])+ obj_id.product_uom_qty

		#             obj_id.price_unit = niit_urtug/niit_too_hemjee
		#             obj_id.product_uom_qty = niit_too_hemjee
		#             ustgah_line += tentsuu_nuhduud.ids
		#             # tentsuu_nuhduud.unlink()

		#     if ustgah_line:
		#         self.ustsan_moves = self.get_tuple(self.line_in_ids.browse(ustgah_line).mapped('stock_move_id_in').ids)
		#         self.line_in_ids.browse(ustgah_line).unlink()
		# print ('ustgahgui_line',ustgahgui_line)

	# 2. Эхний үлдэгдлийн өртөгийг тооцоолох
	def calc_first(self):
		i = 0
		before = False
		# print("self.line_in_ids ", self.line_in_ids)
		if len(self.line_in_ids) > 1:
			first_line = self.line_in_ids[0]
		else:
			first_line = self.line_in_ids
		# print("first_line1 ", first_line)
		if first_line and self.product_id.cost_method == "average":
			end_date = first_line.stock_move_id_in.date
			product_id = first_line.stock_move_id_in.product_id
			company_id = self.company_id.id
			query1 = """
				SELECT product_id, sum(amount) as amount, sum(qty) as qty,price_unit FROM (
					SELECT 
						abs(sm.price_unit)::text as price_unit,
						sm.product_id as product_id,
						(sm.product_uom_qty * abs(sm.price_unit)) as amount,
						sm.product_uom_qty as qty
					FROM stock_move as sm
					LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					LEFT JOIN stock_location as sl on (sm.location_dest_id = sl.id)
					LEFT JOIN stock_location as sl2 on (sm.location_id = sl2.id)
					WHERE sm.state = 'done'
						and sl2.usage not in ('internal')
						  and (sl.usage != 'internal' or sl2.usage != 'internal') 
						  and sm.date < '%s'
						  and sm.product_id=%s
						 and sm.company_id=%s
					UNION ALL
					SELECT 
						abs(sm.price_unit)::text as price_unit,
						sm.product_id as product_id,
						-abs(sm.product_uom_qty * abs(sm.price_unit)) as amount,
						-sm.product_uom_qty as qty
					FROM stock_move as sm
					LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					LEFT JOIN stock_location as sl on (sm.location_id = sl.id)
					LEFT JOIN stock_location as sl2 on (sm.location_dest_id = sl2.id)
					WHERE sm.state = 'done'
						  and sl2.usage not in ('internal')
						  and (sl.usage != 'internal' or sl2.usage != 'internal') 
						  and sm.date < '%s'
						  and sm.product_id=%s
						  and sm.company_id=%s
				) as temp GROUP BY  product_id,price_unit
			"""

			query1 = query1 % (
				end_date,
				product_id.id,
				company_id,
				end_date,
				product_id.id,
				company_id,
			)
			# print("-------------query1 ", query1)
			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			if query_result:
				print('query_result', len(query_result), query_result)
				if len(query_result) == 1:
					first_line.umnuh_price_unit_all = float(query_result[0]["amount"])
					# Eniig zasna
					if float(query_result[0]["qty"]) == 0:
						first_line.umnuh_price_unit = 0
					elif float(query_result[0]["qty"]) < 0:
						raise UserError(
							"%s барааны Эхний үлдэгдэл  %s ХАСАХ болоод байна янзална уу."
							% (product_id.display_name, float(query_result[0]["qty"]))
						)
					else:
						first_line.umnuh_price_unit = float(
							query_result[0]["amount"]
						) / float(query_result[0]["qty"])
					first_line.umnuh_qty = float(query_result[0]["qty"])
					if first_line.parent_id.product_id.cost_method == "fifo":
						first_line.shinechleh_price_unit = first_line.price_unit
					else:
						# print(first_line.umnuh_price_unit_all)
						first_line.shinechleh_price_unit = (
							first_line.umnuh_price_unit_all
							+ first_line.price_unit * first_line.product_uom_qty
						) / (first_line.umnuh_qty + first_line.product_uom_qty)
				else:
					str_name_price_unit = []
					first_qty = 0
					for item in query_result:
						str_name_price_unit.append(item["price_unit"])
						first_qty += float(item["qty"])
					if first_qty < 0:
						raise UserError(
							"%s барааны Эхний үлдэгдэл  %s ХАСАХ болоод байна янзална уу. Өртөг олон"
							% (product_id.display_name, first_qty)
						)

					# print("end_date", end_date)
					first_move_id = self.env["stock.move"].search(
						[
							("date", "<", end_date),
							("state", "=", "done"),
							("location_id.usage", "not in", ["internal", "transit"]),
							("location_dest_id.usage", "in", ["internal", "transit"]),
							("product_id", "=", product_id.id),
						],
						limit=1,
						order="date asc, id desc",
					)
					# print("first_move_id", first_move_id)
					if not first_move_id:
						raise UserError(
							"%s барааны Эхний үлдэгдэл  орлого Байхгүй байна1 "
							% (product_id.display_name)
						)
					self.calc_stock_move_find_first(
						product_id, abs(first_move_id.price_unit), end_date
					)
					# print('!@!@!@!@!@!@!@!@@!@!!!@!@!@!@!@!!@!!@!@!@!')
					try:
						self.calc_first()
					except Exception as e:
						_logger.info("2. Calc_first алдаа: Бараа={0}\n{1}}".format(self.product_id.name, str(self.product_id), e))
					# raise UserError('%s барааны Эхний үлдэгдэл  {%s} өөр өртөгтэй байна'%(product_id.display_name,', '.join(str_name_price_unit)))

			else:
				print('first_line.shinechleh_price_unit', first_line.price_unit)
				first_line.shinechleh_price_unit = first_line.price_unit
		elif first_line and self.product_id.cost_method == "fifo":
			end_date = first_line.stock_move_id_in.date
			product_id = first_line.stock_move_id_in.product_id
			query1 = """
				SELECT product_id, sum(amount) as amount, sum(qty) as qty,price_unit FROM (
					SELECT 
						abs(sm.price_unit)::text as price_unit,
						sm.product_id as product_id,
						(sm.product_uom_qty * abs(sm.price_unit)) as amount,
						sm.product_uom_qty as qty
					FROM stock_move as sm
					LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					LEFT JOIN stock_location as sl on (sm.location_dest_id = sl.id)
					LEFT JOIN stock_location as sl2 on (sm.location_id = sl2.id)
					WHERE sm.state = 'done'
						and sl2.usage not in ('internal')
						  and (sl.usage != 'internal' or sl2.usage != 'internal') 
						  and sm.date < '%s'
						  and sm.product_id=%s
						   
					UNION ALL
					SELECT 
						abs(sm.price_unit)::text as price_unit,
						sm.product_id as product_id,
						-abs(sm.product_uom_qty * abs(sm.price_unit)) as amount,
						-sm.product_uom_qty as qty
					FROM stock_move as sm
					LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					LEFT JOIN stock_location as sl on (sm.location_id = sl.id)
					LEFT JOIN stock_location as sl2 on (sm.location_dest_id = sl2.id)
					WHERE sm.state = 'done'
						  and sl2.usage not in ('internal')
						  and (sl.usage != 'internal' or sl2.usage != 'internal') 
						  and sm.date < '%s'
						  and sm.product_id=%s
						
				) as temp GROUP BY  product_id,price_unit
			"""

			query1 = query1 % (end_date, product_id.id, end_date, product_id.id)
			# print '-------------', query1,'  ++++++++++'
			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			if query_result:
				if len(query_result) == 1:
					first_line.umnuh_price_unit_all = float(query_result[0]["amount"])
					# Eniig zasna
					if float(query_result[0]["qty"]) == 0:
						first_line.umnuh_price_unit = 0
					elif float(query_result[0]["qty"]) < 0:
						raise UserError(
							"%s барааны Эхний үлдэгдэл  %s ХАСАХ болоод байна янзална уу."
							% (product_id.display_name, float(query_result[0]["qty"]))
						)
					else:
						first_line.umnuh_price_unit = float(
							query_result[0]["amount"]
						) / float(query_result[0]["qty"])
					first_line.umnuh_qty = float(query_result[0]["qty"])
					if first_line.parent_id.product_id.cost_method == "fifo":
						first_line.shinechleh_price_unit = first_line.price_unit
					else:
						first_line.shinechleh_price_unit = round(
							(
								first_line.umnuh_price_unit_all
								+ first_line.price_unit * first_line.product_uom_qty
							)
							/ (first_line.umnuh_qty + first_line.product_uom_qty),
							2,
						)
				else:
					str_name_price_unit = []
					first_qty = 0
					for item in query_result:
						str_name_price_unit.append(item["price_unit"])
						first_qty += float(item["qty"])
					if first_qty < 0:
						raise UserError(
							"%s барааны Эхний үлдэгдэл  %s ХАСАХ болоод байна янзална уу. Өртөг олон"
							% (product_id.display_name, first_qty)
						)

					# print 'end_date',end_date
					first_move_id = self.env["stock.move"].search(
						[
							("date", "<", end_date),
							("state", "=", "done"),
							("location_id.usage", "not in", ["internal", "transit"]),
							("location_dest_id.usage", "in", ["internal", "transit"]),
							("product_id", "=", product_id.id),
						],
						limit=1,
						order="date asc, id desc",
					)
					# print 'first_move_id',first_move_id
					if not first_move_id:
						raise UserError(
							"%s барааны Эхний үлдэгдэл  орлого Байхгүй байна2 "
							% (product_id.display_name)
						)
					self.calc_stock_move_find_first(
						product_id, abs(first_move_id.price_unit), end_date
					)

					self.calc_first()

					# raise UserError('%s барааны Эхний үлдэгдэл  {%s} өөр өртөгтэй байна'%(product_id.display_name,', '.join(str_name_price_unit)))

			else:
				first_line.shinechleh_price_unit = first_line.price_unit

	def calc_stock_move_find_first(self, product_id, shine_price_unit, end_date):
		line_obj = self.env["stock.move.resolve.price.unit.stock.move"]
		# print("self.stock_move_fisrt_ids ", self.stock_move_fisrt_ids)
		if self.stock_move_fisrt_ids:
			print(
				"self.stock_move_fisrt_ids.stock_move_id ",
				self.stock_move_fisrt_ids.stock_move_id,
			)
		if self.stock_move_fisrt_ids:
			self.stock_move_fisrt_ids.unlink()
		query1 = """
				SELECT 
					sm.id
				FROM stock_move as sm
				WHERE sm.state = 'done'
					and sm.date <'{0}'
					and sm.product_id={1}
					and abs(sm.price_unit)!={2} and company_id={3}
		""".format(
			end_date, product_id.id, shine_price_unit, self.company_id.id
		)
		# print("query1---calc_stock_move_find_first", query1)
		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		# print("query_result3+++++++++: ", query_result)
		for mv in query_result:
			# print 'mv',mv
			line_id = line_obj.create(
				{
					"first_uld_id": self.id,
					"stock_move_id": mv["id"],
					"new_price_unit": shine_price_unit,
				}
			)
			line_id.action_update()

	# 3. Шалгах
	def calc_update(self):
		if len(self.line_in_ids) > 1:
			first_line = self.line_in_ids[0]
		else:
			first_line = self.line_in_ids
		before = first_line
		for item in self.line_in_ids.filtered(lambda r: r.id != first_line.id):
			end_date = item.stock_move_id_in.date
			start_date = before.date
			shine_price_unit = before.shinechleh_price_unit
			# ehniii uldegdel
			query1 = """
				SELECT product_id, sum(amount) as amount, sum(qty) as qty FROM (
					SELECT 
						sm.product_id as product_id,
						(sm.product_uom_qty * abs({3})) as amount,
						sm.product_uom_qty as qty
					FROM stock_move as sm
					LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					LEFT JOIN stock_location as sl on (sm.location_dest_id = sl.id)
					LEFT JOIN stock_location as sl2 on (sm.location_id = sl2.id)
					WHERE sm.state = 'done'
						and sl2.usage not in ('internal')
						and (sl.usage != 'internal' or sl2.usage != 'internal') 
						and sm.date >= '{0}'
						and sm.date <= '{1}'
						and sm.product_id={2}
						and sm.id!={4}
						and sm.company_id={5}
					UNION ALL
					SELECT 
						sm.product_id as product_id,
						-abs(sm.product_uom_qty * abs({3})) as amount,
						-sm.product_uom_qty as qty
					FROM stock_move as sm
					LEFT JOIN product_product as pp on (pp.id = sm.product_id)
					LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
					LEFT JOIN stock_location as sl on (sm.location_id = sl.id)
					LEFT JOIN stock_location as sl2 on (sm.location_dest_id = sl2.id)
					WHERE sm.state = 'done'
						and sl2.usage not in ('internal')
						and (sl.usage != 'internal' or sl2.usage != 'internal') 
						and sm.date >= '{0}'
						and sm.date <= '{1}'
						and sm.product_id={2}
						and sm.id!={4}
						and sm.company_id={5}
				) as temp GROUP BY  product_id
			""".format(
				start_date,
				end_date,
				item.stock_move_id_in.product_id.id,
				shine_price_unit,
				item.stock_move_id_in.id,
				self.company_id.id,
			)
			print('ehnii vldegdel', query1)
			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			_logger.info("query_result: %s" % (query_result))
			if query_result:
				item.umnuh_qty = float(query_result[0]["qty"]) + before.umnuh_qty
				item.umnuh_price_unit = before.shinechleh_price_unit
				item.umnuh_price_unit_all = item.umnuh_price_unit * item.umnuh_qty
				# if (item.umnuh_qty+item.product_uom_qty)<=0:
				#     raise UserError('%s барааны Шинэчлэх өртөг 0-ээс бага байна'%(item.stock_move_id_in.product_id.display_name))
				if self.product_id.cost_method == "fifo":
					item.shinechleh_price_unit = 0
				elif (item.umnuh_qty + item.product_uom_qty) != 0:
					item.shinechleh_price_unit = (
						item.umnuh_price_unit_all
						+ item.price_unit * item.product_uom_qty
					) / (item.umnuh_qty + item.product_uom_qty)
				else:
					item.shinechleh_price_unit = 0
			before = item

	# 4. Зөрүүтэй хөдөлгөөнийг олох
	def calc_stock_move_find(self):
		line_obj = self.env["stock.move.resolve.price.unit.stock.move"]
		if self.stock_move_ids:
			self.stock_move_ids.unlink()
		fifo_orloguud = []
		if self.product_id.cost_method == "standard":
			shine_price_unit = self.product_id.standard_price
			query1 = """
					SELECT 
						sm.id
					FROM stock_move as sm
					WHERE sm.state = 'done'
						and sm.product_id={0}
						and abs(coalesce(sm.price_unit,0))!={1}::float
						and (sm.date + interval '8 hour')::date>='{2}'
						and (sm.date + interval '8 hour')::date<='{3}' 
						and sm.company_id={4}
			""".format(
				self.product_id.id,
				shine_price_unit,
				self.st_start_date,
				self.st_end_date,
				self.company_id.id,
			)
			print("query1", query1)
			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			for mv in query_result:
				line_obj.create(
					{
						"parent_id": self.id,
						"stock_move_id": mv["id"],
						"new_price_unit": shine_price_unit,
					}
				)
		elif self.product_id.cost_method == "fifo":
			query1 = """
						SELECT 
							sm.id,
							sm.product_qty,
							case when sl.usage in ('production','supplier') and sl2.usage='internal' then 'orlogo' 
							when sl.usage in ('inventory') and sl2.usage='internal' then 'inv_orlogo' 
							when sl.usage in ('customer') and sl2.usage='internal' then 'customer_orlogo' 
							when sl.usage in ('supplier') and sl2.usage='internal' then 'supplier_orlogo' 
							when sl.usage='internal'  and sl2.usage not in ('internal') then 'zarlaga'
							else 'internal' end transfer_type,
							abs(coalesce(sm.price_unit,0)) as price_unit
						FROM stock_move as sm
						left join stock_location sl on (sl.id=sm.location_id)
						left join stock_location sl2 on (sl2.id=sm.location_dest_id)
						WHERE sm.state = 'done'
							and sm.product_id={0} and sm.product_qty!=0 and sm.product_uom_qty!=0
							and sm.company_id={1}
						order by date
				""".format(
				self.product_id.id, self.company_id.id
			)
			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			last_price_unit = False
			for item in query_result:
				if item["transfer_type"] in ["orlogo"]:
					last_price_unit = abs(item["price_unit"])
					break
			# print ('last_price_unit',last_price_unit)
			if not last_price_unit:
				raise UserError("ymarch orlogo algaa ene baraand")
			for item in query_result:
				if item["transfer_type"] == "orlogo":
					last_price_unit = item["price_unit"]
					fifo_orloguud.append(
						{"qty": item["product_qty"], "price_unit": item["price_unit"]}
					)
				else:
					new_price_unit_sum = 0
					save_qty = item["product_qty"]
					if item["transfer_type"] in [
						"inv_orlogo",
						"customer_orlogo",
						"supplier_orlogo",
					]:
						fifo_orloguud.append(
							{"qty": item["product_qty"], "price_unit": last_price_unit}
						)
						new_price_unit_sum = last_price_unit * item["product_qty"]
					elif fifo_orloguud and item["transfer_type"] in ["zarlaga"]:
						l_line = len(fifo_orloguud)
						for i in range(0, l_line):
							if (fifo_orloguud[i]["qty"] - save_qty) > 0:
								fifo_orloguud[i]["qty"] = (
									fifo_orloguud[i]["qty"] - save_qty
								)
								new_price_unit_sum += (
									save_qty * fifo_orloguud[i]["price_unit"]
								)
								break
							else:
								new_price_unit_sum += (
									fifo_orloguud[i]["qty"]
									* fifo_orloguud[i]["price_unit"]
								)
								save_qty = save_qty - fifo_orloguud[i]["qty"]
								fifo_orloguud[i]["qty"] = 0
						woow = list(filter(lambda x: x["qty"] != 0, fifo_orloguud))
						fifo_orloguud = woow
						if not fifo_orloguud:
							new_price_unit_sum += last_price_unit * save_qty
					else:
						new_price_unit_sum = last_price_unit * item["product_qty"]
					p_unit = new_price_unit_sum / item["product_qty"]
					if p_unit == 0 and self.product_id.cost_method != "fifo":
						raise UserError(
							"Shinechleh urtug 0 baina move_id %s %s p_unit: %s "
							% (item["id"], self.product_id.display_name, p_unit)
						)
					if round(abs(item["price_unit"]), 2) != round(abs(p_unit), 2):
						line_obj.create(
							{
								"parent_id": self.id,
								"stock_move_id": item["id"],
								"new_price_unit": p_unit,
							}
						)
		elif self.product_id.cost_method == "average":
			line_in_ids = self.line_in_ids
			l_line = len(line_in_ids)
			for i in range(0, l_line):
				item = line_in_ids[i]
				start_date = item.date
				if i < l_line - 1:
					next_line = line_in_ids[i + 1]
					end_date = " and sm.date<'%s' " % (next_line.date)
				else:
					end_date = "  "
				shine_price_unit = item.shinechleh_price_unit
				# Нэгж өртөг тэнцүү биш агуулахын хөдөлгөөн олох
				query1 = """
						SELECT 
							sm.id
						FROM stock_move as sm
						LEFT JOIN stock_location as sl on sm.location_id=sl.id
						WHERE sm.state = 'done'
							and sm.date > '{0}'
							{1}
							and sm.product_id={2}
							and abs(coalesce(sm.price_unit,0))!=({3})::float
							and sm.company_id={4}
							and sl.usage not in ('supplier','production')
				""".format(
					start_date,
					end_date,
					item.stock_move_id_in.product_id.id,
					shine_price_unit,
					self.company_id.id,
				)
				# print 'query1',query1
				self.env.cr.execute(query1)
				query_result = self.env.cr.dictfetchall()
				
				##########
				# Нэгж өртөг тэнцүү боловч санхүү бичилтгүй бол олж санхүү үүсгэх
				query_match_moves = """
						SELECT 
							sm.id
						FROM stock_move as sm
						LEFT JOIN stock_location as sl on sm.location_id=sl.id
						WHERE sm.state = 'done'
							and sm.date > '{0}'
							{1}
							and sm.product_id={2}
							and abs(coalesce(sm.price_unit,0))=({3})::float
							and sm.company_id={4}
							and sl.usage not in ('supplier','production')
				""".format(
					start_date,
					end_date,
					item.stock_move_id_in.product_id.id,
					shine_price_unit,
					self.company_id.id,
				)
				# print 'query1',query1
				self.env.cr.execute(query_match_moves)
				match_query_result = self.env.cr.dictfetchall()
				match_ids = [int(qq['id']) for qq in match_query_result]
				match_move_ids = self.env['stock.move'].browse(match_ids)
				# Агуулах түгжээтэй хөдөлгүүнийдийг алгасах
				for move_id in match_move_ids:
					result_lock, result_lock_wh = self.env["stock.move.lock"].get_stock_move_is_lock(move_id)
					if result_lock:
						match_move_ids -= move_id
				if match_move_ids.filtered(lambda r: not r.account_move_ids):
					match_move_ids.create_account_move_hand()
				##########

				if not query_result:
					query1 = """
							SELECT 
								sm.id
							FROM stock_move as sm
							LEFT JOIN stock_location as sl on sm.location_id=sl.id
							LEFT JOIN stock_valuation_layer svl on svl.stock_move_id = sm.id
							WHERE sm.state = 'done'
								and sm.date > '{0}'
								{1}
								and sm.product_id={2}
								and (abs(coalesce(sm.price_unit,0))!=({3})::float or abs(coalesce(svl.value,0))!=({3})::float)
								and sm.company_id={4}
								and sl.usage not in ('supplier','production')
					""".format(
						start_date,
						end_date,
						item.stock_move_id_in.product_id.id,
						shine_price_unit,
						self.company_id.id,
					)
					self.env.cr.execute(query1)
					query_result = self.env.cr.dictfetchall()
					print('\n\nITS U.\n\n\n',query_result,'\n')
				for mv in query_result:
					print('\n\nmv mv mv mv: ',mv)
					if mv.get("picking_id"):
						picking = self.env["stock.picking"].browse(mv["picking_id"])
						if picking.purchase_id:
							continue
					line_obj.create(
						{
							"parent_id": self.id,
							"stock_move_id": mv["id"],
							"new_price_unit": item.shinechleh_price_unit,
						}
					)

	# 5. Зөрүүтэй хөдөлгөөнийг нэгж өртөг засах
	def calc_stock_move_price_unit_resolve(self):
		i = len(self.stock_move_ids)
		for item in self.stock_move_ids.filtered(lambda r: not r.is_updated):
			item.action_update()
			_logger.info(
				"%s Нэгж Өртөг засах үлдсэн %s " % (item.stock_move_id.name, i)
			)
			i -= 1
		# return False
		if self.product_id.cost_method == "fifo" and self.stock_move_ids:
			change_price = self.stock_move_ids[
				len(self.stock_move_ids) - 1
			].new_price_unit
			self.product_id.with_context(disable_auto_svl=True).write(
				{"standard_price": change_price}
			)
		elif self.line_in_ids:
			change_price = self.line_in_ids[
				len(self.line_in_ids) - 1
			].shinechleh_price_unit
			self.product_id.with_context(disable_auto_svl=True).write(
				{"standard_price": change_price}
			)

	def unlink(self):
		if self.stock_move_ids.filtered(lambda r: r.is_updated):
			raise UserError("Өртөг Шинэчлэгдсэн байна устгах боломжгүй3")
		return super(StockMoveResolvePriceUnit, self).unlink()

	# Бүх мөр устгах
	def delete_all_line(self):
		self.stock_move_fisrt_ids.unlink()
		self.line_in_ids.unlink()
		self.stock_move_ids.unlink()

	# Санхүү бичилтүүд устгах
	def delete_account_move(self):
		return False
		# i = len(self.stock_move_ids)
		# for item in self.stock_move_ids:
		# 	item.action_delete_am()
		# 	_logger.info(
		# 		"%s Санүү бичилт устгаж үүсгэх %s " % (item.stock_move_id.name, i)
		# 	)
		# 	i -= 1

	# Санхүү бичилтүүд дахин үүсгэх

	def create_account_move(self):
		return False
		# i = len(self.stock_move_ids)
		# for item in self.stock_move_ids:
		# 	item.action_create_am()
		# 	_logger.info(
		# 		"%s Санүү бичилт устгаж үүсгэх %s " % (item.stock_move_id.name, i)
		# 	)
		# 	i -= 1


class StockMoveResolvePriceUnitLine(models.Model):
	_name = "stock.move.resolve.price.unit.line"
	_description = "Stock move resolve price unit line"
	_order = "date asc, stock_move_id_in desc"

	parent_id = fields.Many2one(
		"stock.move.resolve.price.unit", "Resolve", ondelete="cascade"
	)
	stock_move_id_in = fields.Many2one("stock.move", "Орлогын Хөдөлгөөн")
	date = fields.Datetime("Огноо", compute="compute_stock_move_id_in", store=True)
	product_uom_qty = fields.Float(
		"Тоо хэмжээ", compute="compute_stock_move_id_in", store=True
	)
	price_unit = fields.Float(
		"Нэгж үнэ", compute="compute_stock_move_id_in", store=True
	)
	price_total = fields.Float("Нийт тоо өртөг", compute="compute_stock_move_id_in")

	umnuh_price_unit_all = fields.Float("Өмнөх нийт үнэ")
	umnuh_price_unit = fields.Float("Өмнөх нэгж өртөг")
	umnuh_qty = fields.Float("Өмнөх үлдэгдэл")
	shinechleh_price_unit = fields.Float("Шинэчлэх өртөг")

	def unlink(self):
		if self.parent_id.stock_move_ids.filtered(lambda r: r.is_updated):
			raise UserError("Өртөг Шинэчлэгдсэн байна устгах боломжгүй1")
		return super(StockMoveResolvePriceUnitLine, self).unlink()

	@api.depends("stock_move_id_in")
	def compute_stock_move_id_in(self):
		for item in self:
			item.date = item.stock_move_id_in.date
			# item.product_uom_qty = item.stock_move_id_in.product_uom_qty - sum(
			# 	item.stock_move_id_in.move_dest_ids.filtered(
			# 		lambda l: l.state == "done"
			# 	).mapped("product_uom_qty")
			# )
			item.product_uom_qty = item.stock_move_id_in.product_uom_qty
			item.price_unit = item.stock_move_id_in.price_unit
			item.price_total = item.price_unit * item.product_uom_qty


class StockMoveResolvePriceUnitStockMove(models.Model):
	_name = "stock.move.resolve.price.unit.stock.move"
	_description = "Stock move resolve price unit stock move"
	_order = "product, date"

	first_uld_id = fields.Many2one(
		"stock.move.resolve.price.unit", "Resolve first", ondelete="cascade"
	)
	parent_id = fields.Many2one(
		"stock.move.resolve.price.unit", "Resolve", ondelete="cascade"
	)
	stock_move_id = fields.Many2one("stock.move", "Хөдөлгөөн")
	date = fields.Datetime(
		related="stock_move_id.date", compute="compute_stock_move_id_in", store=True
	)
	product_uom_qty = fields.Float(related="stock_move_id.product_uom_qty")
	price_unit = fields.Float(
		"Хуучин Нэгж Үнэ", compute="compute_stock_move_id_in", store=True
	)
	new_price_unit = fields.Float("Шинэчлэх Нэгж Үнэ")
	is_updated = fields.Boolean("Шинэчлэгдсэн Эсэх", default=False, copy=False)

	def unlink(self):
		if self.filtered(lambda r: r.is_updated):
			raise UserError("Өртөг Шинэчлэгдсэн байна устгах боломжгүй2")
		return super(StockMoveResolvePriceUnitStockMove, self).unlink()

	@api.depends("stock_move_id")
	def compute_stock_move_id_in(self):
		for item in self:
			item.price_unit = item.stock_move_id.price_unit
			item.date = item.stock_move_id.date

	def get_mrp_installed(self):
		return False

	def action_update(self):
		if not self.is_updated:
			move_id = self.stock_move_id
			result_lock, result_lock_wh = self.env[
				"stock.move.lock"
			].get_stock_move_is_lock(move_id)
			if not result_lock:
				desc = ""
				if move_id.product_id.cost_method != "standard" and (
					move_id.location_id.usage == "supplier"
					or (move_id.location_id.usage == "production" and not move_id.origin_returned_move_id)
				):
					raise UserError(
						"Орлогын хөдөлгөөний нэгж өртөг өөрчлөхгүй2 %s move_id %s"
						% (move_id.name, move_id.id)
					)
				desc += (
					"Хөдөлгөөний ID %s Бараа %s Хуучин Өртөг %s Шинэ Өртөг %s \n\n"
					% (
						move_id.id,
						move_id.product_id.display_name,
						abs(move_id.price_unit),
						self.new_price_unit,
					)
				)
				obj = self.env["stock.move.change.price.unit"]
				change = obj.create(
					{
						"stock_move_ids": move_id.id,
						"change_price_unit": self.new_price_unit,
					}
				)
				change.set_change_price_unit()
				self.is_updated = True
				if not move_id.account_move_ids or move_id.stock_valuation_layer_ids:
					try:
						move_id.create_account_move_hand()
					except UserError as error:
						vals = {
							'parent_id': self.parent_id.id,
							'name': error,
						}
						print('stock.move.warning', vals)
						print(error)
						print('UserError: ', type(error))
						aaa = self.env['stock.move.warning'].sudo().create(vals)
						print(aaa.name)
						# print(aa)
						# print('\nraise: ',UserError)
						# print(aaa)
				if self.get_mrp_installed():
					if move_id.raw_material_production_id:
						move_id.raw_material_production_id.comupte_cost_force()
						_logger.info(
							"%s ҮЗ дахиж бодов "
							% (move_id.raw_material_production_id.display_name)
						)

	def action_delete_am(self):
		move_id = self.stock_move_id
		if move_id.location_dest_id.usage == "customer":  # Зарлага бол
			if move_id.product_id.cost_method != "standard" and (
				move_id.location_id.usage == "supplier"
				or (move_id.location_id.usage == "production" and not move_id.origin_returned_move_id)
			):
				raise UserError(
					"Орлогын хөдөлгөөний нэгж өртөг өөрчлөхгүй3 %s move_id %s"
					% (move_id.name, move_id.id)
				)
			if move_id.account_move_ids:
				sql_query = """
					DELETE FROM account_partial_reconcile where id in (select acp.id acppp from account_partial_reconcile acp 
		 			LEFT JOIN account_move_line aml ON aml.id=acp.debit_move_id 
	 				LEFT JOIN account_move am ON am.id=aml.move_id 
					WHERE am.id={0});
				""".format(
					move_id.account_move_ids[0].id
				)
				_logger.info("%s sql_query " % (sql_query))
				self.env.cr.execute(sql_query)
				sql_query = """
				delete from account_move where id={0} 
					  """.format(
					move_id.account_move_ids[0].id
				)
				_logger.info("%s sql_query " % (sql_query))
				self.env.cr.execute(sql_query)

	def action_create_am(self):
		move_id = self.stock_move_id
		if move_id.location_dest_id.usage == "customer":  # Зарлага бол
			if move_id.product_id.cost_method != "standard" and (
				move_id.location_id.usage == "supplier"
				or (move_id.location_id.usage == "production" and not move_id.origin_returned_move_id)
			):
				raise UserError(
					"Орлогын хөдөлгөөний нэгж өртөг өөрчлөхгүй4 %s move_id %s"
					% (move_id.name, move_id.id)
				)
			if not move_id.account_move_ids and move_id.stock_valuation_layer_ids:
				move_id.create_account_move_hand()

	_order = "date asc"


class StockPicking(models.Model):
	_inherit = "stock.picking"

	resolve_price_unit_ids = fields.One2many(
		"stock.move.resolve.price.unit",
		"picking_id",
		string="Засагдсан мөрүүд",
		readonly=True,
	)
