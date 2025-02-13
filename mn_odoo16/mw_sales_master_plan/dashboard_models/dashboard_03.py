# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError

# Бүтээгдэхүүний борлуулалт ангилалаар
class SalesPlanDashboard03(models.TransientModel):
	_name = 'sales.plan.dashboard.03'
	_description = 'Product dashboard'

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

	categ_id = fields.Many2one('product.category', string=u'Бүтээгдэхүүний ангилал',)
	warehouse_id = fields.Many2one('stock.warehouse', string=u'Салбар',
		domain=[('is_branch','=',True),('parent_id','=',False)])
	
	# Бүтээглхүүний задаргаа
	product_id = fields.Many2one('product.product', string=u'Бүтээгдэхүүн',
		domain=[('sale_ok','=',True)], )
	day_date = fields.Date(u'Цагаар харах өдөр')
	warehouse_id2 = fields.Many2one('stock.warehouse', string=u'Салбар',
		domain=[('is_branch','=',True),('parent_id','=',False)])

	
	def get_datas(self, year, month, categ_id, warehouse_id, context=None):
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
		# print '-user wh ids--', where_user_wh

		datas = {}
		warehouse_ids = []

		# Dates
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

		# Ангилал нэр авах
		if not categ_id:
			datas['product_chart'] = False
			return datas

		# Тасгийн Name, IDS авах
		query_warehouse_name = """
			SELECT sw.name as name, sw.id as id
			FROM stock_warehouse as sw
			WHERE sw.is_branch = 't' and sw.parent_id is null 
			ORDER BY sw.name  
		"""
		self.env.cr.execute(query_warehouse_name)
		query_result_wh = self.env.cr.dictfetchall()
		category_names = []
		w_ids = ()
		for line in query_result_wh:
			w_ids += (line['id'],)

		# Дэд ангилал авах
		c_ids = self.env['product.category'].search([('id','child_of',categ_id)]).mapped('id')
		if len(c_ids) > 1:
			c_ids = str(tuple(c_ids))
		elif len(c_ids) == 1:
			c_ids = '('+str(c_ids[0])+')'

		
		# Бүтээгдэхүүн авах
		query_sales_categ = ""
		query_sales_categ_period = ""

		query_company_categ = ""
		query_sales_categ_company = ""
		query_sales_categ_company_period = ""
		query1 = ""
		if month < 13:
			query_sales_categ = """
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
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						  and swp.id in """+str(w_ids)+""" 
						  and pt.categ_id in %s
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
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  swp.id in """+str(w_ids)+""" and
						  pt.categ_id in %s
						   %s
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name  
			"""
			query1 = query_sales_categ % (current_date, c_ids, where_user_wh, current_date, c_ids, where_user_wh)
			# Company
			query_sales_categ_company = """
				SELECT categ_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT 
						pc.name as categ_name,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						  and pt.categ_id in %s
					UNION ALL
					SELECT 
						pc.name as categ_name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  pt.categ_id in %s
					) as temp
				GROUP BY categ_name
				ORDER BY categ_name  
			"""
			query_company_categ = query_sales_categ_company % (current_date, c_ids, current_date, c_ids)
		else:
			query_sales_categ_period = """
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
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date >= '%s'
						  and so.validity_date <= '%s'  
						  and swp.id in """+str(w_ids)+""" 
						  and pt.categ_id in %s
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
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date >= '%s' and  
						  (po.date_order + interval '8 hour')::date <= '%s' and  
						  swp.id in """+str(w_ids)+""" and
						  pt.categ_id in %s 
						   %s 
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name  
			"""
			query1 = query_sales_categ_period % (current_date, current_date_end, c_ids, where_user_wh, current_date, current_date_end, c_ids, where_user_wh)
			# Company
			query_sales_categ_company_period = """
				SELECT categ_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT 
						pc.name as categ_name,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date >= '%s'
						  and so.validity_date <= '%s'  
						  and pt.categ_id in %s
					UNION ALL
					SELECT 
						pc.name as categ_name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date >= '%s' and  
						  (po.date_order + interval '8 hour')::date <= '%s' and  
						  pt.categ_id in %s 
					) as temp
				GROUP BY categ_name
				ORDER BY categ_name  
			"""
			query_company_categ = query_sales_categ_company_period % (current_date, current_date_end, c_ids, current_date, current_date_end, c_ids)

		# Компаны ангилалаар ----------------------------------------------------------
		self.env.cr.execute(query_company_categ)
		query_result_categ_company = self.env.cr.dictfetchall()
		series_company = []
		temp_data = []
		percent_amount_qty = []
		for line in query_result_categ_company:
			temp = {
				'name': line['categ_name'],
				'y': line['amount'],
			}
			temp_data.append(temp)
			percent_amount_qty.append([line['amount'],line['qty']])

		temp_dict_com = {
			'name': 'Борлуулалт',
			'type': 'column',
			'tooltip': {'valueSuffix': ' ₮'},
			'data': temp_data,
		}

		# Өмнөх оны борлуулалт
		query2_before = ""
		if month < 13:
			query2_before = query_sales_categ_company % (before_date, c_ids, before_date, c_ids)
		else:
			query2_before = query_sales_categ_company_period % (before_date, before_date_end, c_ids, before_date, before_date_end, c_ids)
		
		self.env.cr.execute(query2_before)
		query_result_categ_company_before = self.env.cr.dictfetchall()

		temp_data = []
		for line in query_result_categ_company_before:
			temp = {
				'name': line['categ_name'],
				'y': line['amount'],
			}
			temp_data.append(temp)

		temp_dict_com_before = {
			'name': 'Өмнөх',
			'type': 'column',
			'tooltip': {'valueSuffix': ' ₮'},
			'data': temp_data,
		}

		series_company.append(temp_dict_com_before)

		# Мастер төлөвлөгөө ангилалаар
		query_plans_categ_company = """
			SELECT categ_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
				SELECT  
					pc.name as categ_name,
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
				LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
				WHERE smp.state != 'draft' and 
				      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
					  pt.categ_id in %s and 
					  smp.year = %d and
					  smp.month in (%s) 
				) as temp
			GROUP BY categ_name
			ORDER BY categ_name
		"""
		query3 = query_plans_categ_company % (c_ids, year, months)
		# print '----------cat plan-------', query2
		self.env.cr.execute(query3)
		query_result_plan_categ_company = self.env.cr.dictfetchall()
		
		temp_data = []
		percent_data_amount = []
		idx = 0
		for line in query_result_plan_categ_company:
			temp = {
				'name': line['categ_name'],
				'y': line['amount'],
			}
			temp_data.append(temp)
			# Percent
			# per = 0
			# if line['categ_name'] in category_names:
			# 	idx = category_names.index(line['categ_name'])
			# 	s_amount = percent_amount_qty[idx][0]
			# 	per = s_amount*100/line['amount']
			# temp = {
			# 	'name': line['warehouse_name'],
			# 	'y': round(per,2),
			# }
			# percent_data_amount.append(temp)

		temp_dict_plan_com = {
			'name': 'Төлөвлөгөө',
			'type': 'column',
			'tooltip': {'valueSuffix': ' ₮'},
			'data': temp_data,
		}
		# 
		# temp_dict_percent = {
		# 	'type':'scatter',
		# 	'yAxis': 1,
		# 	'name': 'Гүйцэтгэлийн %',
		# 	'data': percent_data_amount,
		# 	'marker': {
		# 		'lineWidth': 3,
		# 	},
		# 	'dataLabels': {
		# 		'enabled': True,
		# 		'color': '#FFFFFF',
		# 		'align': 'center',
		# 		'format': '{point.y:.1f}%',
		# 		'style': {
		# 			'fontSize': '13px',
		# 			'fontFamily': 'Verdana, sans-serif'
		# 		}
		# 	},
		# }
		series_company.append(temp_dict_plan_com)
		series_company.append(temp_dict_com)
		datas['company_category_chart'] = series_company

		# Ангилал салбараар -----------------------------------------------------------
		self.env.cr.execute(query1)
		# print '======cat======', query1
		query_result_sales = self.env.cr.dictfetchall()

		# Цуврал дата
		series = []
		temp_data = []
		percent_amount_qty = []
		for line in query_result_sales:
			category_names.append(line['warehouse_name'])
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_data.append(temp)

			percent_amount_qty.append([line['amount'],line['qty']])

		temp_dict_current = {
			'name': 'Борлуулалт',
			'type': 'column',
			'tooltip': {'valueSuffix': ' ₮'},
			'data': temp_data,
		}

		# Өмнөх оны борлуулалт
		query1_before = ""
		if month < 13:
			query1_before = query_sales_categ % (before_date, c_ids, where_user_wh, before_date, c_ids, where_user_wh)
		else:
			query1_before = query_sales_categ_period % (before_date, before_date_end, c_ids, where_user_wh, before_date, before_date_end, c_ids, where_user_wh)
		
		self.env.cr.execute(query1_before)
		query_result_sales_before = self.env.cr.dictfetchall()

		temp_data = []
		for line in query_result_sales_before:
			# category_names.append(line['warehouse_name'])
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_data.append(temp)

		temp_dict_before = {
			'name': 'Өмнөх',
			'type': 'column',
			'tooltip': {'valueSuffix': ' ₮'},
			'data': temp_data,
		}

		series.append(temp_dict_before)

		# Мастер төлөвлөгөө ангилалаар
		query_plans_categ = """
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
				LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
				WHERE smp.state != 'draft' and 
				      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
					  swp.id in """+str(w_ids)+""" and 
					  pt.categ_id in %s and 
					  smp.year = %d and
					  smp.month in (%s) 
					   %s 
				) as temp
			GROUP BY warehouse_name
			ORDER BY warehouse_name
		"""
		query2 = query_plans_categ % (c_ids, year, months, where_user_wh)
		# print '----------cat plan-------', query2
		self.env.cr.execute(query2)
		query_result_plan_categ = self.env.cr.dictfetchall()
		
		temp_data = []
		percent_data_amount = []
		idx = 0

		for line in query_result_plan_categ:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_data.append(temp)
			# Percent
			per = 0
			if line['warehouse_name'] in category_names:
				idx = category_names.index(line['warehouse_name'])
				s_amount = percent_amount_qty[idx][0]
				per = s_amount*100/line['amount']
			temp = {
				'name': line['warehouse_name'],
				'y': round(per,2),
			}
			percent_data_amount.append(temp)

		temp_dict = {
			'name': 'Төлөвлөгөө',
			'type': 'column',
			'tooltip': {'valueSuffix': ' ₮'},
			'data': temp_data,
		}
		# 
		temp_dict_percent = {
			'type':'scatter',
			'yAxis': 1,
			'name': 'Гүйцэтгэлийн %',
			'data': percent_data_amount,
			'marker': {
				'lineWidth': 3,
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
		series.append(temp_dict_current)
		series.append(temp_dict_percent)

		datas['product_chart'] = series
		datas['category_name'] = self.env['product.category'].browse(categ_id).name
		datas['categ_names'] = category_names

		# --------------------------------------------------

		# Задаргаа харуулах
		# Тухайн ангилалын тухайн агуулах дээрх барааны задаргааг харуудах
		# Энэ он
		if warehouse_id:
			series_product = []
			query3 = ""
			query_product = ""
			query_product_period = ""
			if month < 13:
				query_product = """
					SELECT product_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT 
							pt.name as product_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0
							  and so.validity_date::text ilike '%s' 
							  and swp.id = %d
							  and pt.categ_id in %s
							   %s 
						UNION ALL
						SELECT 
							pt.name as product_name,
							pol.price_unit * pol.qty as amount,
							pol.qty as qty_sold
						FROM pos_order_line as pol
						LEFT JOIN pos_order as po on (po.id = pol.order_id)
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						LEFT JOIN product_product as pp on (pp.id = pol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
						WHERE po.state in ('paid','done','invoiced') and   
							  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
							  swp.id = %d and
							  pt.categ_id in %s
							   %s 
						) as temp
					GROUP BY product_name
					ORDER BY product_name
				"""
				query3 = query_product % (current_date, warehouse_id, c_ids, where_user_wh, current_date, warehouse_id, c_ids, where_user_wh)
			else:
				query_product = """
					SELECT product_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT 
							pt.name as product_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0
							  and so.validity_date >= '%s' 
							  and so.validity_date <= '%s' 
							  and swp.id = %d
							  and pt.categ_id in %s
							   %s 
						UNION ALL
						SELECT 
							pt.name as product_name,
							pol.price_unit * pol.qty as amount,
							pol.qty as qty_sold
						FROM pos_order_line as pol
						LEFT JOIN pos_order as po on (po.id = pol.order_id)
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						LEFT JOIN product_product as pp on (pp.id = pol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
						WHERE po.state in ('paid','done','invoiced') and   
							  (po.date_order + interval '8 hour')::date >= '%s' and
							  (po.date_order + interval '8 hour')::date <= '%s' and  
							  swp.id = %d and
							  pt.categ_id in %s 
							   %s 
						) as temp
					GROUP BY product_name
					ORDER BY product_name
				"""
				query3 = query_product_period % (current_date, current_date_end, warehouse_id, c_ids, where_user_wh, current_date, current_date_end, warehouse_id, c_ids, where_user_wh)

			self.env.cr.execute(query3)
			# print '==========', query3
			query_result_product = self.env.cr.dictfetchall()
			temp_data = []
			total_product_amount = 0
			for line in query_result_product:
				temp = {
					'name': line['product_name'],
					'y': line['amount'],
				}
				temp_data.append(temp)
				total_product_amount += line['amount']

			temp_dict = {
				'name': 'Борлуулалт',
				'type': 'column',
				'tooltip': {'valueSuffix': ' ₮'},
				'yAxis': 1,
				'data': temp_data,
			}

			# Өмнөх он
			query4 = ""
			if month < 13:
				query4 = query_product % (before_date, warehouse_id, c_ids, where_user_wh, before_date, warehouse_id, c_ids, where_user_wh)
			else:
				query4 = query_product_period % (before_date, before_date_end, warehouse_id, c_ids, where_user_wh, before_date, before_date_end, warehouse_id, c_ids, where_user_wh)

			self.env.cr.execute(query4)
			query_result_product = self.env.cr.dictfetchall()
			temp_data = []
			before_total_product_amount = 0
			for line in query_result_product:
				temp = {
					'name': line['product_name'],
					'y': line['amount'],
				}
				temp_data.append(temp)
				before_total_product_amount += line['amount']

			temp_dict_before = {
				'name': 'Өмнөх он',
				'type': 'column',
				'tooltip': {'valueSuffix': ' ₮'},
				'yAxis': 1,
				'data': temp_data,
			}
			series_product.append(temp_dict_before)
			series_product.append(temp_dict)

			datas['warehouse_name'] = self.env['stock.warehouse'].browse(warehouse_id).name
			datas['total_product_amount'] = round(total_product_amount,2)
			datas['before_total_product_amount'] = round(before_total_product_amount,2)
			datas['product_by_categ_chart'] = series_product
		else:
			datas['product_by_categ_chart'] = False

		return datas

	
	def get_datas_detailed(self, year, month, product_id, day_date, warehouse_id, context=None):
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
		# print '-user wh ids--', where_user_wh

		datas = {}
		# Dates
		current_date = str(year)
		before_date = str(year-1)
		before_date2 = str(year-2)
		if month > 9:
			current_date += '-'+str(month)+'%'
			before_date += '-'+str(month)+'%'
			before_date2 += '-'+str(month)+'%'
		else:
			current_date += '-0'+str(month)+'%'
			before_date += '-0'+str(month)+'%'
			before_date2 += '-0'+str(month)+'%'

		w_ids = ()
		branch_where = ""
		if not warehouse_id:
			# Тасгийн Name, IDS авах
			query_warehouse_name = """
				SELECT sw.name as name, sw.id as id
				FROM stock_warehouse as sw
				WHERE sw.is_branch = 't' and sw.parent_id is null 
				ORDER BY sw.name  
			"""
			self.env.cr.execute(query_warehouse_name)
			query_result_wh = self.env.cr.dictfetchall()
			category_names = ()
			
			for line in query_result_wh:
				# category_names += (line['name'],)
				w_ids += (line['id'],)
		else:
			w_ids = '('+str(warehouse_id)+')'
			branch_where = " swp.id = %d and " % warehouse_id

		# Сонгосон Бүтээгдэхүүний задаргааг харуулах
		if product_id:
			# Сонгосон Бүтээгдэхүүний 12 сараар
			# Энэ он ---------
			current_year = str(year)+'-%'
			query_product_monthly = """
				SELECT order_date, mm, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						to_char(so.validity_date,'YYYY/MM') as order_date,
						EXTRACT(month from so.validity_date) as mm,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
						  sol.product_id = %d and
						   %s
						  so.validity_date::text ilike '%s'
						   %s
					UNION ALL
					SELECT 
						to_char((po.date_order + interval '8 hour')::date, 'YYYY/MM') as order_date,
						EXTRACT(month from (po.date_order + interval '8 hour')::date) as mm,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  pol.product_id = %d and
						   %s 
						  (po.date_order + interval '8 hour')::date::text ilike '%s'
						   %s 
					) as temp
				GROUP BY order_date, mm
				ORDER BY order_date, mm
			"""
			query_now = query_product_monthly % (product_id, branch_where, current_year, where_user_wh, product_id, branch_where, current_year, where_user_wh)
			self.env.cr.execute(query_now)
			query_result = self.env.cr.dictfetchall()

			series_qty_monthly = []
			for line in query_result:
				temp = {
						'name': line['mm'],
						'y': line['qty'],
					}
				series_qty_monthly.append(temp)
			temp_dict_qty_sale = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': series_qty_monthly,
			}
			# Өмнөх он -----
			before_year = str(year-1)+'-%'
			query_before = query_product_monthly % (product_id, branch_where, before_year, where_user_wh, product_id, branch_where, before_year, where_user_wh)
			self.env.cr.execute(query_before)
			query_result_before = self.env.cr.dictfetchall()

			series_qty_monthly_before = []
			for line in query_result_before:
				temp = {
						'name': line['mm'],
						'y': line['qty'],
					}
				series_qty_monthly_before.append(temp)
			temp_dict_qty_before = {
				'type':'column',
				'name': 'Өмнөх',
				'data': series_qty_monthly_before,
			}
			# Өмнөх он 2 -----
			before_year_2 = str(year-2)+'-%'
			query_before_2 = query_product_monthly % (product_id, branch_where, before_year_2, where_user_wh, product_id, branch_where, before_year_2, where_user_wh)
			self.env.cr.execute(query_before_2)
			query_result_before_2 = self.env.cr.dictfetchall()

			series_qty_monthly_before_2 = []
			for line in query_result_before_2:
				temp = {
						'name': line['mm'],
						'y': line['qty'],
					}
				series_qty_monthly_before_2.append(temp)
			temp_dict_qty_before_2 = {
				'type':'column',
				'name': 'Өмнөх 2',
				'data': series_qty_monthly_before_2,
			}
			# Төлөвлөгөө -----------
			query_plans = """
				SELECT mm, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						smp.month as mm,
						(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_sold
						-- smpl.amount as amount,
						-- smpl.qty as qty_sold
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
					      smpl.product_id = %d and 
					       %s 
						  (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
						   smp.year = %d 
						   %s 
					) as temp
				GROUP BY mm
				ORDER BY mm
			"""
			query5 = query_plans % (product_id, branch_where, year, where_user_wh)
			self.env.cr.execute(query5)
			query_result_plan = self.env.cr.dictfetchall()
			series_qty_monthly_plan = []
			for line in query_result_plan:
				temp = {
						'name': line['mm'],
						'y': line['qty'],
					}
				series_qty_monthly_plan.append(temp)

			temp_dict_qty_plan = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': series_qty_monthly_plan,
			}
			# Өгөгдөл цэнэглэх - qty
			series2 = []
			series2.append(temp_dict_qty_before_2)
			series2.append(temp_dict_qty_before)
			series2.append(temp_dict_qty_plan)
			series2.append(temp_dict_qty_sale)
			datas['product_monthly_chart'] = series2

			# Өдрөөр -------------------------------------------------------
			drilldown = {}
			category_names = ()
			query_sales_by_product = """
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
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						  and swp.id in """+str(w_ids)+""" 
						  and sol.product_id = %d
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
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  swp.id in """+str(w_ids)+""" and
						  pol.product_id = %d 
						   %s
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name  
			"""
			query1 = query_sales_by_product % (current_date, product_id, where_user_wh, current_date, product_id, where_user_wh)
			self.env.cr.execute(query1)
			query_result_sales = self.env.cr.dictfetchall()

			# Цуцрал дата
			series = []
			temp_data = []
			for line in query_result_sales:
				category_names += (line['warehouse_name'],)
				temp = {
					'name': line['warehouse_name'],
					'y': line['qty'],
					'drilldown': line['warehouse_name']+'_drl',
				}
				temp_data.append(temp)

			temp_dict = {
				'name': 'Борлуулалт',
				'type': 'column',
				'colorByPoint': True,
				'tooltip': {'valueSuffix': ' ₮'},
				'data': temp_data,
			}
			series.append(temp_dict)

			# Drilldown бэлдэх
			query_by_product_drilldown = """
				SELECT warehouse_name, dddd, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT 
						swp.name as warehouse_name,
						so.validity_date as dddd,
						sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
						(sol.qty_delivered-sol.return_qty) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0
						  and so.validity_date::text ilike '%s' 
						  and swp.id in """+str(w_ids)+""" 
						  and sol.product_id = %d
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						(po.date_order + interval '8 hour')::date as dddd,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and   
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
						  swp.id in """+str(w_ids)+""" and
						  pol.product_id = %d 
						   %s 
					) as temp
				GROUP BY warehouse_name, dddd
				ORDER BY warehouse_name, dddd 
			"""
			query2 = query_by_product_drilldown % (current_date, product_id, where_user_wh, current_date, product_id, where_user_wh)
			self.env.cr.execute(query2)
			query_result_sales_drilldown = self.env.cr.dictfetchall()

			drilldown_series = []
			wh_name = '-1'
			first = True
			temp_data = []
			for line in query_result_sales_drilldown:
				if first:
					val = (line['dddd'],line['qty'])
					temp_data.append(val)
					first = False
					wh_name = line['warehouse_name']
				else:
					if wh_name != line['warehouse_name']:
						temp_dict = {
							'id': wh_name+'_drl',
							'data': temp_data,
						}
						drilldown_series.append(temp_dict)
						first = False
						wh_name = line['warehouse_name']
						temp_data = []

					val = (line['dddd'],line['qty'])
					temp_data.append(val)
			temp_dict = {
				'id': wh_name+'_drl',
				'data': temp_data,
			}
			drilldown_series.append(temp_dict)

			drilldown['series'] = drilldown_series

			datas['by_product_chart'] = series
			datas['by_product_name'] = self.env['product.product'].browse(product_id).name
			datas['by_product_drilldown_chart'] = drilldown

			# Цагаар задлаж харуулах
			if day_date:
				qry = ""
				if warehouse_id:
					qry = """
						SELECT warehouse_name, day_time, sum(amount) as amount, sum(qty_sold) as qty FROM (
							SELECT 
								swp.name as warehouse_name,
								EXTRACT(hour from po.date_order)+8 as day_time,
								pol.price_unit * pol.qty as amount,
								pol.qty as qty_sold
							FROM pos_order_line as pol
							LEFT JOIN pos_order as po on (po.id = pol.order_id)
							LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
							LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
							--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
							WHERE po.state in ('paid','done','invoiced') and   
								  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
								  pol.product_id = %d and
								  swp.id in """+str(w_ids)+"""
								   %s 
							  ) as temp
						GROUP BY warehouse_name, day_time
						ORDER BY warehouse_name, day_time 
					"""
				else:
					qry = """
						SELECT warehouse_name, day_time, sum(amount) as amount, sum(qty_sold) as qty FROM (
							SELECT 
								swp.name as warehouse_name,
								EXTRACT(hour from po.date_order)+8 as day_time,
								pol.price_unit * pol.qty as amount,
								pol.qty as qty_sold
							FROM pos_order_line as pol
							LEFT JOIN pos_order as po on (po.id = pol.order_id)
							LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
							LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
							--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
							WHERE po.state in ('paid','done','invoiced') and   
								  (po.date_order + interval '8 hour')::date::text ilike '%s' and  
								  pol.product_id = %d 
								   %s 
							  ) as temp
						GROUP BY warehouse_name, day_time
						ORDER BY warehouse_name, day_time 
					"""

				# Катег цаг бэлдэх
				time_range = []
				for line in range(8, 24):
					time_range.append(line)
				
				# ДАТА бэлдэх
				query2 = qry % (day_date, product_id, where_user_wh)
				self.env.cr.execute(query2)
				query_result_sales = self.env.cr.dictfetchall()

				wh_name = ''
				first = True
				temp_amount = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				series_0 = []
				temp_dict = {}
				for line in query_result_sales:
					if first:
						wh_name = line['warehouse_name']
						first = False

					if wh_name != line['warehouse_name']:
						temp_dict = {
							'name': wh_name,
							'data': temp_amount,
						}
						series_0.append(temp_dict)
						wh_name = line['warehouse_name']
						temp_amount = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
					
					idx = time_range.index(line['day_time'])
					del temp_amount[idx]
					temp_amount.insert(idx, line['qty'])
				
				if warehouse_id:
					temp_dict = {
						'name': wh_name,
						'data': temp_amount,
					}
				series_0.append(temp_dict)

				# print '----------------', series_0
				datas['by_product_time_chart'] = series_0
			else:
				datas['by_product_time_chart'] = False
		else:
			datas['by_product_chart'] = False
			return datas
	
		return datas
