# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError

# Бялууны борлуулалт
class SalesPlanDashboard02(models.TransientModel):
	_name = 'sales.plan.dashboard.02'
	_description = 'Cake dashboard'

	@api.model
	def _get_year(self):
		return datetime.date.today().year

	@api.model
	def _get_month(self):
		return datetime.date.today().month

	# Columns
	year = fields.Selection([
			(2015, u'2015 он'), 
			(2016, u'2016 он'), 
			(2017, u'2017 он'), 
			(2018, u'2018 он'), 
			(2019, u'2019 он'), 
			(2020, u'2020 он'), 
		], default=_get_year, required=True, string=u'Он')
	month = fields.Selection([
			(1, u'1 сар'), 
			(2, u'2 сар'), 
			(3, u'3 сар'), 
			(4, u'4 сар'), 
			(5, u'5 сар'), 
			(6, u'6 сар'), 
			(7, u'7 сар'), 
			(8, u'8 сар'), 
			(9, u'9 сар'), 
			(10, u'10 сар'), 
			(11, u'11 сар'), 
			(12, u'12 сар'), 
			(13, u'1-р улирал'),
			(14, u'2-р улирал'),
			(15, u'3-р улирал'),
			(16, u'4-р улирал'),
			(17, u'Эхний хагас'), 
			(18, u'Сүүлийн хагас'), 
			(19, u'Жилээр'), 
		], default=_get_month, required=True, string=u'Сар')
	inch_sizes = fields.Many2many('product.type.size', string=u'Бялууны инч', 
		domain=[('is_inch','=',True)], 
		help=u"Тухайн сонгосон бялууны хэмжээгээр тайланд гаргах")
	type_names = fields.Many2many('product.type.size', string=u'Бялууны загвар', 
		domain=[('is_template','=',True)], 
		help=u"Тухайн сонгосон бялууны загвараар тайланд гаргах")
	with_slice_cake = fields.Boolean(string=u'Хэрчмийн бялууг харах', default=False,
		help=u"Хэрэв хэрчмийн бялуутай хамт харах бол сонгоно уу")

	warehouse_id = fields.Many2one('stock.warehouse', string=u'Салбар',)
	date_start = fields.Date(u'Эхлэх огноо')
	date_end = fields.Date(u'Дуусах огноо')

	
	def get_datas_days(self, warehouse_id, date_start, date_end, sizes, types, with_slice_cake, context=None):
		datas = {}
		if date_start and date_end:
			if  date_start > date_end:
				return datas

			where_pts_ptt = self._get_type_size_condition(sizes, types, with_slice_cake)

			before_date_start = str(int(date_start[0:4])-1)+date_start[4:]
			before_date_end = str(int(date_end[0:4])-1)+date_end[4:]

			where_warehouse = ""
			if warehouse_id:
				where_warehouse = " swp.id = %d and " % warehouse_id
				wh_name = self.env['stock.warehouse'].browse(warehouse_id).name
				datas['title'] = wh_name+u' салбарын борлуулалт'
			else:
				datas['title'] = u'Компаны борлуулалт'

			# Энэ оны борлуулалт
			query_sales_days = """
				SELECT code, order_date, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						pc.code as code,
						so.validity_date as order_date,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and
						  so.validity_date >= '%s' and
						  so.validity_date <= '%s' and 
						   %s
						  pc.code in ('71','72')
						   %s
					UNION ALL
					SELECT 
						pc.code as code,
						(po.date_order + interval '8 hour')::date as order_date,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE (po.date_order + interval '8 hour')::date >= '%s' and  
					      (po.date_order + interval '8 hour')::date <= '%s' and  
						   %s
						  pc.code in ('71','72')
						   %s
					) as temp
				GROUP BY code, order_date
				ORDER BY code, order_date
			"""
			query0 = query_sales_days % (date_start, date_end, where_warehouse, where_pts_ptt, date_start, date_end, where_warehouse, where_pts_ptt)
			# print '================', query0
			self.env.cr.execute(query0)
			query_result_days = self.env.cr.dictfetchall()

			series_brand = []
			series_happy = []
			series_brand_qty = []
			series_happy_qty = []

			total_brand_amount = 0
			total_brand_qty = 0
			total_happy_amount = 0
			total_happy_qty = 0

			for line in query_result_days:
				dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]
				if line['code'] == '71':
					temp = {
						'name': line['order_date'],
						'drilldown': dddd+'_now_happy',
						'y': line['amount'],
					}
					temp_qty = {
						'name': line['order_date'],
						'drilldown': dddd+'_now_happy_qty',
						'y': line['qty'],
					}
					series_happy.append(temp)
					series_happy_qty.append(temp_qty)
					total_happy_amount += temp['y']
					total_happy_qty += temp_qty['y']
				else:
					temp = {
						'name': line['order_date'],
						'drilldown': dddd+'_now_brand',
						'y': line['amount'],
					}
					temp_qty = {
						'name': line['order_date'],
						'drilldown': dddd+'_now_brand_qty',
						'y': line['qty'],
					}
					series_brand.append(temp)
					series_brand_qty.append(temp_qty)
					total_brand_amount += temp['y']
					total_brand_qty += temp_qty['y']

			# Брэнд, Хаппи
			series = []
			series_qty = []
			temp_dict_brand = {
				'type':'column',
				'name': u'Брэнд',
				'data': series_brand,
			}
			temp_dict_happy = {
				'type':'column',
				'name': u'Аз жаргал',
				'data': series_happy,
			}
			temp_dict_brand_qty = {
				'type':'column',
				'name': u'Брэнд',
				'data': series_brand_qty,
			}
			temp_dict_happy_qty = {
				'type':'column',
				'name': u'Аз жаргал',
				'data': series_happy_qty,
			}

			# Өмнөх он
			query1 = query_sales_days % (before_date_start, before_date_end, where_warehouse, where_pts_ptt, before_date_start, before_date_end, where_warehouse, where_pts_ptt)
			self.env.cr.execute(query1)
			query_result_before_days = self.env.cr.dictfetchall()
			series_brand = []
			series_happy = []
			series_brand_qty = []
			series_happy_qty = []
			for line in query_result_before_days:
				dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]
				if line['code'] == '71':
					temp = {
						'name': dddd,
						'drilldown': dddd+'_before_happy',
						'y': line['amount'],
					}
					temp_qty = {
						'name': dddd,
						'drilldown': dddd+'_before_happy_qty',
						'y': line['qty'],
					}
					series_happy.append(temp)
					series_happy_qty.append(temp_qty)
				else:
					temp = {
						'name': dddd,
						'drilldown': dddd+'_before_brand',
						'y': line['amount'],
					}
					temp_qty = {
						'name': dddd,
						'drilldown': dddd+'_before_brand_qty',
						'y': line['qty'],
					}
					series_brand.append(temp)
					series_brand_qty.append(temp_qty)

			# Брэнд, Хаппи
			temp_dict_brand_before = {
				'type':'column',
				'name': u'Өмнөх брэнд',
				'data': series_brand,
			}
			temp_dict_happy_before = {
				'type':'column',
				'name': u'Өмнөх аз жаргал',
				'data': series_happy,
			}
			temp_dict_brand_before_qty = {
				'type':'column',
				'name': u'Өмнөх брэнд',
				'data': series_brand_qty,
			}
			temp_dict_happy_before_qty = {
				'type':'column',
				'name': u'Өмнөх аз жаргал',
				'data': series_happy_qty,
			}

			# SET datas
			series.append(temp_dict_brand_before)
			series.append(temp_dict_brand)
			series.append(temp_dict_happy_before)
			series.append(temp_dict_happy)
			datas['cake_days_amount_chart'] = series
			# 
			series_qty.append(temp_dict_brand_before_qty)
			series_qty.append(temp_dict_brand_qty)
			series_qty.append(temp_dict_happy_before_qty)
			series_qty.append(temp_dict_happy_qty)
			datas['cake_days_qty_chart'] = series_qty
			# 
			datas['total_brand_amount'] = total_brand_amount
			datas['total_brand_qty'] = total_brand_qty
			datas['total_happy_amount'] = total_happy_amount
			datas['total_happy_qty'] = total_happy_qty
			# 

			# Drilldown SET xiix
			# QUERY бэлдэх - Brand
			query_sales_days_drill = """
				SELECT order_date, name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						so.validity_date as order_date,
						ptt.name as name,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and
						  so.validity_date >= '%s' and
						  so.validity_date <= '%s' and 
						   %s
						  pc.code = '72'
						   %s
					UNION ALL
					SELECT 
						(po.date_order + interval '8 hour')::date as order_date,
						ptt.name as name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE (po.date_order + interval '8 hour')::date >= '%s' and  
					      (po.date_order + interval '8 hour')::date <= '%s' and  
						   %s
						  pc.code = '72'
						   %s
					) as temp
				GROUP BY order_date, name
				ORDER BY order_date, name
			"""
			query_now = query_sales_days_drill % (date_start, date_end, where_warehouse, where_pts_ptt, date_start, date_end, where_warehouse, where_pts_ptt)
			query_before = query_sales_days_drill % (before_date_start, before_date_end, where_warehouse, where_pts_ptt, before_date_start, before_date_end, where_warehouse, where_pts_ptt)
			# Өмнөх оны Brand
			self.env.cr.execute(query_before)
			query_cat_drill_before_result = self.env.cr.dictfetchall()
			# VARs
			drilldown = {}
			series_drilldown = []
			drilldown_qty = {}
			series_drilldown_qty = []

			temp_data = []
			temp_data_qty = []
			day_name = ''
			dddd = ''
			first = True
			for line in query_cat_drill_before_result:
				if first:
					day_name = line['order_date']
					first = False
					dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]

					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)
				else:
					if day_name != line['order_date']:
						temp_dict = {
							'name': u'Өмнөх brand',
							'type':'column',
							'id': dddd+'_before_brand',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Өмнөх brand',
							'type':'column',
							'id': dddd+'_before_brand_qty',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						day_name = line['order_date']

						dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]
					
					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)

			temp_dict = {
				'name': u'Өмнөх brand',
				'type':'column',
				'id': dddd+'_before_brand',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Өмнөх brand',
				'type':'column',
				'id': day_name+'_before_brand_qty',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)

			# Энэ оны Brand
			self.env.cr.execute(query_now)
			query_cat_drill_now_result = self.env.cr.dictfetchall()
			# VARs
			temp_data = []
			temp_data_qty = []
			day_name = ''
			dddd = ''
			first = True
			for line in query_cat_drill_now_result:
				if first:
					day_name = line['order_date']
					first = False
					dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]

					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)
				else:
					if day_name != line['order_date']:
						temp_dict = {
							'name': u'Энэ он brand',
							'type':'column',
							'id': dddd+'_now_brand',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Энэ он brand',
							'type':'column',
							'id': dddd+'_now_brand_qty',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						day_name = line['order_date']

						dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]
					
					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)

			temp_dict = {
				'name': u'Энэ он brand',
				'type':'column',
				'id': dddd+'_now_brand',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Энэ он brand',
				'type':'column',
				'id': day_name+'_now_brand_qty',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)

			# QUERY бэлдэх - Happy
			query_sales_days_drill = """
				SELECT order_date, name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						so.validity_date as order_date,
						pts.name as name,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and
						  so.validity_date >= '%s' and
						  so.validity_date <= '%s' and 
						   %s
						  pc.code = '71'
						   %s
					UNION ALL
					SELECT 
						(po.date_order + interval '8 hour')::date as order_date,
						pts.name as name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE (po.date_order + interval '8 hour')::date >= '%s' and  
					      (po.date_order + interval '8 hour')::date <= '%s' and  
						   %s
						  pc.code = '71'
						   %s
					) as temp
				GROUP BY order_date, name
				ORDER BY order_date, name
			"""
			query_now = query_sales_days_drill % (date_start, date_end, where_warehouse, where_pts_ptt, date_start, date_end, where_warehouse, where_pts_ptt)
			query_before = query_sales_days_drill % (before_date_start, before_date_end, where_warehouse, where_pts_ptt, before_date_start, before_date_end, where_warehouse, where_pts_ptt)

			# Өмнөх оны хаппи
			self.env.cr.execute(query_before)
			query_cat_drill_before_result = self.env.cr.dictfetchall()
			# VARs
			temp_data = []
			temp_data_qty = []
			day_name = ''
			dddd = ''
			first = True
			for line in query_cat_drill_before_result:
				if first:
					day_name = line['order_date']
					first = False
					dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]

					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)
				else:
					if day_name != line['order_date']:
						temp_dict = {
							'name': u'Өмнөх happy',
							'type':'column',
							'id': dddd+'_before_happy',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Өмнөх happy',
							'type':'column',
							'id': dddd+'_before_happy_qty',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						day_name = line['order_date']

						dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]
					
					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)

			temp_dict = {
				'name': u'Өмнөх happy',
				'type':'column',
				'id': dddd+'_before_happy',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Өмнөх happy',
				'type':'column',
				'id': day_name+'_before_happy_qty',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)

			# Энэ оны хаппи
			self.env.cr.execute(query_now)
			query_cat_drill_now_result = self.env.cr.dictfetchall()
			# VARs
			temp_data = []
			temp_data_qty = []
			day_name = ''
			dddd = ''
			first = True
			for line in query_cat_drill_now_result:
				if first:
					day_name = line['order_date']
					first = False
					dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]

					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)
				else:
					if day_name != line['order_date']:
						temp_dict = {
							'name': u'Энэ он happy',
							'type':'column',
							'id': dddd+'_now_happy',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Энэ он happy',
							'type':'column',
							'id': dddd+'_now_happy_qty',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						day_name = line['order_date']

						dddd = str(int(line['order_date'][0:4])+1)+line['order_date'][4:]
					
					val1 = (line['name'], line['amount'])
					val2 = (line['name'], line['qty'])
					temp_data.append(val1)
					temp_data_qty.append(val2)

			temp_dict = {
				'name': u'Энэ он happy',
				'type':'column',
				'id': dddd+'_now_happy',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Энэ он happy',
				'type':'column',
				'id': day_name+'_now_happy_qty',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)

			# 
			drilldown['series'] = series_drilldown
			datas['cake_days_amount_drill'] = drilldown

			drilldown_qty['series'] = series_drilldown_qty
			datas['cake_days_qty_drill'] = drilldown_qty
			# 
		return datas

	
	def get_datas(self, year, month, sizes, types, with_slice_cake, context=None):
		# Компаны нийт борлуулалт харах эрхтэй эсэх
		query = """
			SELECT 
				u.id as user_id
			from res_users as u 
			LEFT JOIN res_groups_users_rel as rel on (rel.uid = u.id)
			LEFT JOIN res_groups as g on (g.id = rel.gid)
			LEFT JOIN ir_model_data as ir on (ir.res_id = g.id)
			WHERE ir.name = 'group_company_sales_user' and u.id = %d 
		""" % self.env.user.id
		self.env.cr.execute(query)

		# Агуулахын шүүлт
		where_user_wh = ''
		query_user = self.env.cr.dictfetchall()
		if not query_user:
			# Хэрэглэгчийн зөвшөөрөгдсөн агуулахыг авах
			user_wh_ids = self.env.user.warehouse_ids.mapped('id')
			if user_wh_ids:
				if user_wh_ids > 1:
					where_user_wh = " and swp.id in "+str(tuple(user_wh_ids))
				else:
					where_user_wh = " and swp.id in ("+str(user_wh_ids[0])+") "
			else:
				where_user_wh = " and swp.id = -1 "
		
		datas = {}
		where_pts_ptt = self._get_type_size_condition(sizes, types, with_slice_cake)

		current_date = str(year)
		before_date = str(year-1)
		before_date2 = str(year-2)

		current_date_end = str(year)
		before_date_end = str(year-1)
		before_date2_end = str(year-2)
		months = ""

		# Сараар
		if 9 < month and month < 13:
			current_date += '-'+str(month)+'%'
			before_date += '-'+str(month)+'%'
			before_date2 += '-'+str(month)+'%'
			months = str(month)
		elif month < 10:
			current_date += '-0'+str(month)+'%'
			before_date += '-0'+str(month)+'%'
			before_date2 += '-0'+str(month)+'%'
			months = str(month)
		# Улирал, хагас жилээр
		elif month == 13:
			current_date += '-01-01'
			before_date += '-01-01'
			before_date2 += '-01-01'
			months = "1,2,3"
			current_date_end += '-03-31'
			before_date_end += '-03-31'
			before_date2_end += '-03-31'
		elif month == 14:
			current_date += '-04-01'
			before_date += '-04-01'
			before_date2 += '-04-01'
			months = "4,5,6"
			current_date_end += '-06-30'
			before_date_end += '-06-30'
			before_date2_end += '-06-30'
		elif month == 15:
			current_date += '-07-01'
			before_date += '-07-01'
			before_date2 += '-07-01'
			months = "7,8,9"
			current_date_end += '-09-30'
			before_date_end += '-09-30'
			before_date2_end += '-09-30'
		elif month == 16:
			current_date += '-10-01'
			before_date += '-10-01'
			before_date2 += '-10-01'
			months = "10,11,12"
			current_date_end += '-12-31'
			before_date_end += '-12-31'
			before_date2_end += '-12-31'
		elif month == 17:
			current_date += '-01-01'
			before_date += '-01-01'
			before_date2 += '-01-01'
			months = "1,2,3,4,5,6"
			current_date_end += '-06-30'
			before_date_end += '-06-30'
			before_date2_end += '-06-30'
		elif month == 18:
			current_date += '-07-01'
			before_date += '-07-01'
			before_date2 += '-07-01'
			months = "7,8,9,10,11,12"
			current_date_end += '-12-31'
			before_date_end += '-12-31'
			before_date2_end += '-12-31'
		elif month == 19:
			current_date += '-01-01'
			before_date += '-01-01'
			before_date2 += '-01-01'
			months = "1,2,3,4,5,6,7,8,9,10,11,12"
			current_date_end += '-12-31'
			before_date_end += '-12-31'
			before_date2_end += '-12-31'

		# Category бэлдэх
		# Салбар буюу тасгийн нэрс
		category_names = ()
		query_categ = """
			SELECT 
				sw.id as id, 
				sw.name as warehouse_name
			FROM stock_warehouse as sw
			WHERE sw.parent_id is null and 
				  sw.is_branch = 't'
			ORDER BY sw.name
		"""
		self.env.cr.execute(query_categ)
		query_result = self.env.cr.dictfetchall()
		for line in query_result:
			category_names += (line['warehouse_name'],)

		# Нийт компаний хэмжээний дата авах
		query_sales_company = ""
		query_sales_company_period = ""
		query0 = ""
		query0_before = ""

		if month < 13:
			query_sales_company = """
				SELECT categ_name, code, size, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						pc.name as categ_name,
						pc.code as code,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						  and pc.code in ('71','72')
						   %s
						   %s
					UNION ALL
					SELECT 
						pc.name as categ_name,
						pc.code as code,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  swp.id is not null and 
						  pc.code in ('71','72')
						   %s
						   %s
					) as temp
				GROUP BY categ_name, code, size
				ORDER BY categ_name, code, size
			"""
			query0 = query_sales_company % (current_date, where_pts_ptt, where_user_wh, current_date, where_pts_ptt, where_user_wh)
		else:
			query_sales_company_period = """
				SELECT categ_name, code, size, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						pc.name as categ_name,
						pc.code as code,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date >= '%s' 
						  and so.validity_date <= '%s' 
						  and pc.code in ('71','72')
						   %s
						   %s
					UNION ALL
					SELECT 
						pc.name as categ_name,
						pc.code as code,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date >= '%s' and  
						  (po.date_order + interval '8 hour')::date <= '%s' and  
						  swp.id is not null and 
						  pc.code in ('71','72')
						   %s
						   %s
					) as temp
				GROUP BY categ_name, code, size
				ORDER BY categ_name, code, size 
			"""
			query0 = query_sales_company_period % (current_date, current_date_end, where_pts_ptt, where_user_wh, current_date, current_date_end, where_pts_ptt, where_user_wh)

		# print '------company---------', query0
		self.env.cr.execute(query0)
		query_result_company = self.env.cr.dictfetchall()

		series_brand_happy = []
		series_brand = []
		series_happy = []
		total_brand_amount = 0
		total_happy_amount = 0

		for line in query_result_company:
			size_name = u'Бусад'
			if line['size']:
				size_name = line['size']
			temp = {
				'name': size_name,
				'y': line['qty'],
			}
			if line['code'] == '71':
				series_happy.append(temp)
				total_happy_amount += line['qty']
			else:
				series_brand.append(temp)
				total_brand_amount += line['qty']

		# Брэнд Хаппи хамтдаа
		datas['brand_happy_inch_chart'] = [
			{'name': u'Brand', 'y': total_brand_amount},
			{'name': u'Happy', 'y': total_happy_amount}
		]
		# Drill
		datas['brand_happy_drill_chart'] = series_brand + series_happy
		datas['total_brand_happy'] = total_brand_amount + total_happy_amount

		# Брэнд, Хаппи тусдаа
		temp_dict_brand = {
			'name': u'Брэнд',
			'colorByPoint': True,
			'data': series_brand,
		}
		temp_dict_happy = {
			'name': u'Аз жаргал',
			'colorByPoint': True,
			'data': series_happy,
		}
		datas['brand_pie_chart'] = [temp_dict_brand]
		datas['happy_pie_chart'] = [temp_dict_happy]
		datas['total_brand_amount'] = total_brand_amount
		datas['total_happy_amount'] = total_happy_amount
		# ===------------------
		
		# Цуцрал дата
		series = []
		series_qty = []

		percent_categ = []
		percent_amount_qty = []

		# Энэ оны борлуулалт Нийт
		query_sales_size = ""
		query_sales_size_period = ""
		query1 = ""
		query1_before = ""

		if month < 13:
			query_sales_size = """
				SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						swp.name as warehouse_name,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						   %s
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  swp.id is not null 
						   %s
						   %s 
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name  
			"""
			query1 = query_sales_size % (current_date, where_pts_ptt, where_user_wh, current_date, where_pts_ptt, where_user_wh)
		else:
			query_sales_size_period = """
				SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						swp.name as warehouse_name,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date >= '%s'
						  and so.validity_date <= '%s'  
						   %s
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date >= '%s' and  
						  (po.date_order + interval '8 hour')::date <= '%s' and  
						  swp.id is not null 
						   %s
						   %s 
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name  
			"""
			query1 = query_sales_size_period % (current_date, current_date_end, where_pts_ptt, where_user_wh, current_date, current_date_end, where_pts_ptt, where_user_wh)

		# print '---------------', query1
		self.env.cr.execute(query1)
		query_result_total = self.env.cr.dictfetchall()
		
		# Company total
		total_before_amount = 0
		total_before_qty = 0
		total_amount = 0
		total_qty = 0
		# VARs
		temp_amount = []
		temp_qty = []
		for line in query_result_total:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
				'drilldown': line['warehouse_name'],
			}
			temp_amount.append(temp)
			total_amount += line['amount']
			# qty
			temp_d_qty = {
				'name': line['warehouse_name'],
				'y': line['qty'],
				'drilldown': line['warehouse_name'],
			}
			temp_qty.append(temp_d_qty)
			total_qty += line['qty']

			percent_categ.append(line['warehouse_name'])
			percent_amount_qty.append([line['amount'],line['qty']])
		
		temp_dict_now = {
			'name': 'Борлуулалт',
			'type':'column',
			'data': temp_amount,
		}
		temp_dict_qty_now = {
			'name': 'Борлуулалт',
			'type':'column',
			'data': temp_qty,
		}

		# Өмнөх он
		query1_before = ""
		if month < 13:
			query1_before = query_sales_size % (before_date, where_pts_ptt, where_user_wh, before_date, where_pts_ptt, where_user_wh)
		else:
			query1_before = query_sales_size_period % (before_date, before_date_end, where_pts_ptt, where_user_wh, before_date, before_date_end, where_pts_ptt, where_user_wh)

		self.env.cr.execute(query1_before)
		query_result_before = self.env.cr.dictfetchall()
		
		temp_amount = []
		temp_qty = []
		for line in query_result_before:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
				'drilldown': line['warehouse_name']+'_before',
			}
			temp_amount.append(temp)
			total_before_amount += line['amount']
			# 
			temp_d_qty = {
				'name': line['warehouse_name'],
				'y': line['qty'],
				'drilldown': line['warehouse_name']+'_before',
			}
			temp_qty.append(temp_d_qty)
			total_before_qty += line['qty']
		
		temp_dict_before = {
			'name': 'Өмнөх',
			'type':'column',
			'data': temp_amount,
		}
		temp_dict_qty_before = {
			'name': 'Өмнөх',
			'type':'column',
			'data': temp_qty,
		}

		# 
		series.append(temp_dict_before)
		series_qty.append(temp_dict_qty_before)
		
		# Ингчээр drilldown хийх
		# Инч тэй
		query_sales_size = ""
		query_sales_size_period = ""
		query2 = ""

		if month < 13:
			query_sales_size = """
				SELECT warehouse_name, size, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						swp.name as warehouse_name,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						   %s 
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  swp.id is not null 
						   %s 
						   %s 
					) as temp
				GROUP BY warehouse_name, size
				ORDER BY warehouse_name, size  
			"""
			query2 = query_sales_size % (current_date, where_pts_ptt, where_user_wh, current_date, where_pts_ptt, where_user_wh)
		else:
			query_sales_size_period = """
				SELECT warehouse_name, size, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						swp.name as warehouse_name,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date >= '%s' 
						  and so.validity_date <= '%s' 
						   %s 
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date >= '%s' and  
						  (po.date_order + interval '8 hour')::date <= '%s' and 
						  swp.id is not null 
						   %s 
						   %s 
					) as temp
				GROUP BY warehouse_name, size
				ORDER BY warehouse_name, size  
			"""
			query2 = query_sales_size_period % (current_date, current_date_end, where_pts_ptt, where_user_wh, current_date, current_date_end, where_pts_ptt, where_user_wh)

		# print '---------------', query1
		self.env.cr.execute(query2)
		query_result_sizes = self.env.cr.dictfetchall()

		wh_name = '-1'
		first = True
		temp_data = []
		drilldown = {}
		drilldown_series = []
		# 
		temp_data_qty = []
		drilldown_qty = {}
		drilldown_series_qty = []

		data_drill_this_qty = {}
		data_drill_this_amount = {}

		for line in query_result_sizes:
			if line['size'] in data_drill_this_qty:
				qty = data_drill_this_qty[ line['size'] ]
				amount = data_drill_this_amount[ line['size'] ]
				data_drill_this_qty[ line['size'] ] = qty+line['qty']
				data_drill_this_amount[ line['size'] ] = amount+line['amount']
			else:
				data_drill_this_qty[ line['size'] ] = line['qty']
				data_drill_this_amount[ line['size'] ] = line['amount']

			if first:
				val = (line['size'],line['amount'])
				temp_data.append(val)
				# 
				val = (line['size'],line['qty'])
				temp_data_qty.append(val)
				first = False
				wh_name = line['warehouse_name']
			else:
				if wh_name != line['warehouse_name']:
					temp_dict = {
						'id': wh_name,
						'name': u'Энэ он',
						'data': temp_data,
					}
					drilldown_series.append(temp_dict)
					temp_data = []
					# 
					temp_dict_qty = {
						'id': wh_name,
						'name': u'Энэ он',
						'data': temp_data_qty,
					}
					drilldown_series_qty.append(temp_dict_qty)
					temp_data_qty = []

					wh_name = line['warehouse_name']

				val = (line['size'],line['amount'])
				temp_data.append(val)
				# 
				val = (line['size'],line['qty'])
				temp_data_qty.append(val)

		temp_dict_drill = {
			'id': wh_name,
			'name': u'Энэ он',
			'data': temp_data,
		}
		# 
		temp_dict_qty_drill = {
			'id': wh_name,
			'name': u'Энэ он',
			'data': temp_data_qty,
		}

		# Өмнөх оны drilldown
		query2_before = ""
		if month < 13:
			query2_before = query_sales_size % (before_date, where_pts_ptt, where_user_wh, before_date, where_pts_ptt, where_user_wh)
		else:
			query2_before = query_sales_size_period % (before_date, before_date_end, where_pts_ptt, where_user_wh, before_date, before_date_end, where_pts_ptt, where_user_wh)
		self.env.cr.execute(query2_before)
		query_result_sizes_before = self.env.cr.dictfetchall()

		wh_name = '-1'
		first = True
		temp_data = []
		temp_data_qty = []

		data_drill_before_qty = {}
		data_drill_before_amount = {}

		for line in query_result_sizes_before:
			if line['size'] in data_drill_before_qty:
				qty = data_drill_before_qty[ line['size'] ]
				amount = data_drill_before_amount[ line['size'] ]
				data_drill_before_qty[ line['size'] ] = qty+line['qty']
				data_drill_before_amount[ line['size'] ] = amount+line['amount']
			else:
				data_drill_before_qty[ line['size'] ] = line['qty']
				data_drill_before_amount[ line['size'] ] = line['amount']

			if first:
				val = (line['size'],line['amount'])
				temp_data.append(val)
				# 
				val = (line['size'],line['qty'])
				temp_data_qty.append(val)
				first = False
				wh_name = line['warehouse_name']
			else:
				if wh_name != line['warehouse_name']:
					temp_dict = {
						'id': wh_name+'_before',
						'name': u'Өмнөх',
						'data': temp_data,
					}
					drilldown_series.append(temp_dict)
					temp_data = []
					# 
					temp_dict_qty = {
						'id': wh_name+'_before',
						'name': u'Өмнөх',
						'data': temp_data_qty,
					}
					drilldown_series_qty.append(temp_dict_qty)
					temp_data_qty = []

					wh_name = line['warehouse_name']

				val = (line['size'],line['amount'])
				temp_data.append(val)
				# 
				val = (line['size'],line['qty'])
				temp_data_qty.append(val)

		temp_dict_before_drill = {
			'id': wh_name+'_before',
			'name': u'Өмнөх',
			'data': temp_data,
		}
		# 
		temp_dict_qty_before_drill = {
			'id': wh_name+'_before',
			'name': u'Өмнөх',
			'data': temp_data_qty,
		}
		# 
		drilldown_series.append(temp_dict_before_drill)
		drilldown_series.append(temp_dict_drill)
		drilldown['series'] = drilldown_series
		# 
		drilldown_series_qty.append(temp_dict_qty_before_drill)
		drilldown_series_qty.append(temp_dict_qty_drill)
		drilldown_qty['series'] = drilldown_series_qty

		# Мастер төлөвлөгөө татах
		# Нийт
		query_plans = """
			SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
				SELECT  
					swp.name as warehouse_name,
					(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount,
					(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_sold
					-- smpl.amount as amount,
					-- smpl.qty as qty_sold
				FROM sales_master_plan_line as smpl
				LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
				LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
				LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
				LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
				LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
				WHERE smp.state != 'draft' and 
					  (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
					  smp.year = %d and
					  smp.month in (%s) 
					   %s 
					   %s 
				) as temp
			GROUP BY warehouse_name
			ORDER BY warehouse_name
		"""
		query3 = query_plans % (year, months, where_pts_ptt, where_user_wh)
		# print '------------', query3
		self.env.cr.execute(query3)
		query_result_plan_total = self.env.cr.dictfetchall()
		# VARs
		temp_amount = []
		temp_qty = []

		total_plan_amount = 0
		total_plan_qty = 0

		percent_data_amount = []
		percent_data_qty = []

		for line in query_result_plan_total:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
				'drilldown': line['warehouse_name']+'_plan',
			}
			temp_amount.append(temp)
			total_plan_amount += line['amount']
			# 
			temp = {
				'name': line['warehouse_name'],
				'y': line['qty'],
				'drilldown': line['warehouse_name']+'_qty',
			}
			temp_qty.append(temp)
			total_plan_qty += line['qty']

			# Percent
			per = 0
			if line['warehouse_name'] in percent_categ:
				idx = percent_categ.index(line['warehouse_name'])
				s_amount = percent_amount_qty[idx][0]
				per = s_amount*100/line['amount']
			temp = {
				'name': line['warehouse_name'],
				'y': round(per,2),
			}
			percent_data_amount.append(temp)
			# 
			if line['warehouse_name'] in percent_categ:
				s_qty = percent_amount_qty[idx][1]
				per = s_qty*100/line['qty']
			temp = {
				'name': line['warehouse_name'],
				'y': round(per,2),
			}
			percent_data_qty.append(temp)
		# 

		temp_dict = {
			'name': 'Төлөвлөгөө',
			'type': 'column',
			'data': temp_amount,
		}
		temp_dict_percent = {
			'type':'scatter',
			'yAxis': 1,
			'name': 'Гүйцэтгэлийн %',
			'data': percent_data_amount,
			'marker': {
				'radius': 5,
                'states': {
                    'hover': {
                        'enabled': True,
                        'lineColor': 'rgb(100,100,100)'
                    }
                }
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': '{point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		series.append(temp_dict)
		series.append(temp_dict_now)
		series.append(temp_dict_percent)
		# 
		temp_dict_qty = {
			'name': 'Төлөвлөгөө',
			'type': 'column',
			'data': temp_qty,
		}
		temp_dict_percent_qty = {
			'type':'scatter',
			'yAxis': 1,
			'name': 'Гүйцэтгэлийн %',
			'data': percent_data_qty,
			'marker': {
				'radius': 5,
                'states': {
                    'hover': {
                        'enabled': True,
                        'lineColor': '#B9C4C9'
                    }
                }
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': '{point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		series_qty.append(temp_dict_qty)
		series_qty.append(temp_dict_qty_now)
		series_qty.append(temp_dict_percent_qty)

		# Мастер төлөвлөгөө инчээр - Drilldown
		query_plans_inch = """
			SELECT warehouse_name, size, sum(amount) as amount, sum(qty_sold) as qty FROM (
				SELECT  
					swp.name as warehouse_name,
					(CASE WHEN pc.code = '71' THEN pts.name ELSE ptt.name END) as size,
					(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount,
					(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_sold
					-- smpl.amount as amount,
					-- smpl.qty as qty_sold
				FROM sales_master_plan_line as smpl
				LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
				LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
				LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
				LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
				LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
				LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
				WHERE smp.state != 'draft' and 
				      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
					  smp.year = %d and
					  smp.month in (%s) 
					   %s 
					   %s 
				) as temp
			GROUP BY warehouse_name, size
			ORDER BY warehouse_name, size
		"""
		query4 = query_plans_inch % (year, months, where_pts_ptt, where_user_wh)
		# print '-----------------', query2
		self.env.cr.execute(query4)
		query_result_plan_inch = self.env.cr.dictfetchall()

		wh_name = '-1'
		first = True
		temp_data = []
		temp_data_qty = []

		data_drill_plan_qty = {}
		data_drill_plan_amount = {}
		for line in query_result_plan_inch:
			if line['size'] in data_drill_plan_qty:
				qty = data_drill_plan_qty[ line['size'] ]
				amount = data_drill_plan_amount[ line['size'] ]
				data_drill_plan_qty[ line['size'] ] = qty+line['qty']
				data_drill_plan_amount[ line['size'] ] = amount+line['amount']
			else:
				data_drill_plan_qty[ line['size'] ] = line['qty']
				data_drill_plan_amount[ line['size'] ] = line['amount']

			if first:
				val = (line['size'],line['amount'])
				temp_data.append(val)
				# 
				val = (line['size'],line['qty'])
				temp_data_qty.append(val)

				first = False
				wh_name = line['warehouse_name']
			else:
				if wh_name != line['warehouse_name']:
					temp_dict = {
						'id': wh_name+'_plan',
						'name': u'Төлөвлөгөө',
						'data': temp_data,
					}
					drilldown_series.append(temp_dict)
					# 
					temp_dict_qty = {
						'id': wh_name+'_qty',
						'name': u'Төлөвлөгөө',
						'data': temp_data_qty,
					}
					drilldown_series_qty.append(temp_dict_qty)

					first = False
					wh_name = line['warehouse_name']
					temp_data = []
					temp_data_qty = []

				val = (line['size'],line['amount'])
				temp_data.append(val)
				# 
				val = (line['size'],line['qty'])
				temp_data_qty.append(val)

		temp_dict = {
			'id': wh_name+'_plan',
			'data': temp_data,
		}
		drilldown_series.append(temp_dict)
		drilldown['series'] = drilldown_series
		# 
		temp_dict_qty = {
			'id': wh_name+'_qty',
			'data': temp_data_qty,
		}
		drilldown_series_qty.append(temp_dict_qty)
		drilldown_qty['series'] = drilldown_series_qty

		datas['cake_amount_performance_chart'] = series
		datas['cake_amount_drilldown'] = drilldown
		# 
		datas['cake_qty_performance_chart'] = series_qty
		datas['cake_qty_drilldown'] = drilldown_qty

		datas['categ_names'] = category_names

		# Компаний нийт ==========================================================
		series_total = []
	 	# Өмнөх он
	 	temp_dict_qty_before = {
			'name': 'Өмнөх тоо',
			'color': 'rgba(65,170,217,1)',
			'data': [{'name':u'Компаний нийт', 'y': total_before_qty, 'drilldown':'total_before_qty' }],
			'tooltip': {
	 			'valueSuffix': ' ш'
	 		},
			'pointPadding': 0.4,
			'pointPlacement': -0.3,
		}
		temp_dict_amount_before = {
			'name': 'Өмнөх',
			'yAxis': 1,
			'color': 'rgba(26,86,134,.9)',
			'data': [{'name':u'Компаний нийт', 'y': total_before_amount, 'drilldown':'total_before_amount' }],
			'tooltip': {
	 			'valueSuffix': ' ₮'
	 		},
			'pointPadding': 0.45,
			'pointPlacement': -0.3,
		}
		# Төлөвлөгөө
		temp_dict_plan_qty = {
	 		'name': 'Тоо хэмжээ',
	 		'color': 'rgba(248,161,63,1)',
	 		'data': [{'name':u'Компаний нийт', 'y': total_plan_qty, 'drilldown':'total_plan_qty' }],
	 		'tooltip': {
	 			'valueSuffix': ' ш'
	 		},
	 		'pointPadding': 0.4,
	 		'pointPlacement': 0,
	 	} 
	 	temp_dict_plan_amount = {
	 		'name': 'Төлөвлөгөө',
	 		'color': 'rgba(186,60,61,.9)',
	 		'data': [{'name':u'Компаний нийт', 'y': total_plan_amount, 'drilldown':'total_plan_amount' }],
	 		'tooltip': {
	 			'valueSuffix': ' ₮'
	 		},
	 		'pointPadding': 0.45,
	 		'pointPlacement': 0,
	 		'yAxis': 1
	 	}
		# Энэ он
		temp_dict_qty = {
			'name': 'Тоо хэмжээ',
			'color': 'rgba(165,170,217,1)',
			'data': [{'name':u'Компаний нийт', 'y':  total_qty, 'drilldown':'total_qty'}],
			'tooltip': {
	 			'valueSuffix': ' ш'
	 		},
			'pointPadding': 0.4,
			'pointPlacement': 0.3,
		}
		temp_dict_amount = {
			'name': 'Борлуулалт',
			'yAxis': 1,
			'color': 'rgba(126,86,134,.9)',
			'data': [{'name':u'Компаний нийт', 'y': total_amount, 'drilldown':'total_amount' }],
			'tooltip': {
	 			'valueSuffix': ' ₮'
	 		},
			'pointPadding': 0.45,
			'pointPlacement': 0.3,
		}
		series_total.append(temp_dict_qty_before)
		series_total.append(temp_dict_amount_before)
		series_total.append(temp_dict_plan_qty)
		series_total.append(temp_dict_plan_amount)
		series_total.append(temp_dict_qty)
		series_total.append(temp_dict_amount)
		datas['cake_total_chart'] = series_total

		# Drilldown company
		temp_data = []
		temp_data_qty = []
		drilldown_series = []
		drilldown = {}

		# Өмнөх он
		temp_data = []
		temp_data_qty = []
		for key in data_drill_before_amount:
			val = (key,data_drill_before_amount[key])
			temp_data.append(val)
		temp_dict = {
			'id': 'total_before_amount', 
			'name': u'Өмнөх',
			'type':'column',
			'data': temp_data,
		}
		drilldown_series.append(temp_dict)
		temp_data = []
		temp_data_qty = []
		for key in data_drill_before_qty:
			val = (key,data_drill_before_qty[key])
			temp_data_qty.append(val)
		temp_dict_qty = {
			'id': 'total_before_qty',
			'name': u'Өмнөх',
			'type':'column',
			'data': temp_data_qty,
		}
		drilldown_series.append(temp_dict_qty)

		# Мастер
		temp_data = []
		temp_data_qty = []
		for key in data_drill_plan_amount:
			val = (key,data_drill_plan_amount[key])
			temp_data.append(val)
		temp_dict = {
			'id': 'total_plan_amount',
			'name': u'Төлөвлөгөө',
			'type':'column',
			'data': temp_data,
		}
		drilldown_series.append(temp_dict)
		temp_data = []
		temp_data_qty = []
		for key in data_drill_plan_qty:
			val = (key,data_drill_plan_qty[key])
			temp_data_qty.append(val)
		temp_dict_qty = {
			'id': 'total_plan_qty',
			'name': u'Төлөвлөгөө',
			'type':'column',
			'data': temp_data_qty,
		}
		drilldown_series.append(temp_dict_qty)

		# Энэ оны drill
		temp_data = []
		temp_data_qty = []
		for key in data_drill_this_amount:
			val = (key,data_drill_this_amount[key])
			temp_data.append(val)
		temp_dict = {
			'id': 'total_amount',
			'name': u'Энэ он',
			'type':'column',
			'data': temp_data,
		}
		drilldown_series.append(temp_dict)
		temp_data = []
		temp_data_qty = []
		for key in data_drill_this_qty:
			val = (key,data_drill_this_qty[key])
			temp_data_qty.append(val)
		temp_dict_qty = {
			'id': 'total_qty',
			'name': u'Энэ он',
			'type':'column',
			'data': temp_data_qty,
		}
		drilldown_series.append(temp_dict_qty)
		
		# 
		drilldown['series'] = drilldown_series
		datas['cake_total_chart_drill'] = drilldown

		return datas

	def _get_type_size_condition(self, sizes, types, with_slice_cake):
		# Хэмжээ загвар шүүлт
		size_ids = []
		type_ids = []
		if not sizes and not types:
			size_ids = self.env['product.type.size'].search([('is_inch','=',True)]).mapped('id')
			type_ids = self.env['product.type.size'].search([('is_template','=',True)]).mapped('id')
		if sizes:
			size_ids = sizes[0][2]
		if types:
			type_ids = types[0][2]

		# Хэрчмийн хэмжээтэй бялууг хасах ID = 73
		if not with_slice_cake and 73 in size_ids:
			size_ids.remove(73)

		if len(size_ids) > 1:
			size_ids = tuple(size_ids)
		elif len(size_ids) == 1:
			size_ids = '('+str(size_ids[0])+')'

		if len(type_ids) > 1:
			type_ids = tuple(type_ids)
		elif len(type_ids) == 1:
			type_ids = '('+str(type_ids[0])+')'

		where_size_ids = ''
		where_type_ids = ''
		if size_ids:
			where_size_ids = " pts.id in " +str(size_ids)
		if type_ids:
			where_type_ids = " ptt.id in " +str(type_ids)

		where_pts_ptt = ''
		if where_size_ids:
			where_pts_ptt = " and "+where_size_ids
		if where_type_ids:
			where_pts_ptt = " and "+where_type_ids
		if where_size_ids and where_type_ids:
			where_pts_ptt = " and ("+where_size_ids+" or "+where_type_ids+")"
		
		return where_pts_ptt
