# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError

# Salbar
class SalesPlanDashboard04(models.TransientModel):
	_name = 'sales.plan.dashboard.04'
	_description = 'Branch sales dashboard'

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

	warehouse_id = fields.Many2one('stock.warehouse', string=u'Салбар',
		required=True, domain=[('is_branch','=',True),('parent_id','=',False)])

	
	def get_datas(self, year, month, warehouse_id, context=None):
		datas = {}
		if warehouse_id:
			
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

			series = []
			series_qty = []

			# Бүтээгдэхүүний ангилал авах
			# Бялуу, бэйкери, шингэн Бүтээгдэхүүнүүд
			all_categ = self.env['product.category'].search([('code','in',['100'])])
			c_ids = self.env['product.category'].search([('id','child_of',all_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "

			# Энэ оны борлуулалт
			query_sales = ""
			query_plans = ""
			query1 = ""
			query1_before = ""
			query_sales_category = ""
			if month < 13:
				query_sales = """
					SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT  
							sw.name as warehouse_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and
								%s 
							  so.validity_date::text ilike '%s' and 
							  swp.id = %d
						UNION ALL
						SELECT 
							sw.name as warehouse_name,
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
						       %s
							  (po.date_order + interval '8 hour')::date::text ilike '%s' and
							  swp.id = %d
						) as temp
					GROUP BY warehouse_name
					ORDER BY warehouse_name
				"""
				query1 = query_sales % (where_categ_ids, current_date, warehouse_id, where_categ_ids, current_date, warehouse_id)
				query1_before = query_sales % (where_categ_ids, before_date, warehouse_id, where_categ_ids, before_date, warehouse_id)
				query_sales_cat = """
					SELECT warehouse_name, categ_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT  
							sw.name as warehouse_name,
							pc.name as categ_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and
						       %s
							  so.validity_date::text ilike '%s' and 
							  swp.id = %d
						UNION ALL
						SELECT 
							sw.name as warehouse_name,
							pc.name as categ_name,
							pol.price_unit * pol.qty as amount,
							pol.qty as qty_sold
						FROM pos_order_line as pol
						LEFT JOIN pos_order as po on (po.id = pol.order_id)
						LEFT JOIN product_product as pp on (pp.id = pol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
						WHERE po.state in ('paid','done','invoiced') and  
						       %s  
							  (po.date_order + interval '8 hour')::date::text ilike '%s' and
							  swp.id = %d
						) as temp
					GROUP BY warehouse_name, categ_name
					ORDER BY warehouse_name, categ_name
				"""
				query_sales_category = query_sales_cat % (where_categ_ids, current_date, warehouse_id, where_categ_ids, current_date, warehouse_id)
			else:
				query_sales = """
					SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT  
							sw.name as warehouse_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
						       %s
							  so.validity_date >= '%s' and 
							  so.validity_date <= '%s' and 
							  swp.id = %d
						UNION ALL
						SELECT 
							sw.name as warehouse_name,
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
								%s
							  (po.date_order + interval '8 hour')::date >= '%s' and 
							  (po.date_order + interval '8 hour')::date <= '%s' and 
							  swp.id = %d
						) as temp
					GROUP BY warehouse_name
					ORDER BY warehouse_name
				"""
				query1 = query_sales % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)
				query1_before = query_sales % (where_categ_ids, before_date, before_date_end, warehouse_id, where_categ_ids, before_date, before_date_end, warehouse_id)
				query_sales_cat = """
					SELECT warehouse_name, categ_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT  
							sw.name as warehouse_name,
							pc.name as categ_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
							   %s
							  so.validity_date >= '%s' and 
							  so.validity_date <= '%s' and 
							  swp.id = %d
						UNION ALL
						SELECT 
							sw.name as warehouse_name,
							pc.name as categ_name,
							pol.price_unit * pol.qty as amount,
							pol.qty as qty_sold
						FROM pos_order_line as pol
						LEFT JOIN pos_order as po on (po.id = pol.order_id)
						LEFT JOIN product_product as pp on (pp.id = pol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
						WHERE po.state in ('paid','done','invoiced') and 
						       %s 
							  (po.date_order + interval '8 hour')::date >= '%s' and 
							  (po.date_order + interval '8 hour')::date <= '%s' and 
							  swp.id = %d
						) as temp
					GROUP BY warehouse_name, categ_name
					ORDER BY warehouse_name, categ_name
				"""
				query_sales_category = query_sales_cat % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)

			self.env.cr.execute(query1)
			# print '---------------', query_sales_category
			query_result = self.env.cr.dictfetchall()
			
			categ_names = []
			series = []
			temp_data_amount = []
			temp_data_qty = []
			percent_amount_qty = []

			branch_total_amount = 0
			branch_total_qty = 0
			branch_total_amount_names = {}

			for line in query_result:
				categ_names.append(line['warehouse_name'])
				temp = {
					'name': line['warehouse_name'],
					'y': line['amount'],
				}
				temp_data_amount.append(temp)
				temp = {
					'name': line['warehouse_name'],
					'y': line['qty'],
				}
				temp_data_qty.append(temp)

				branch_total_amount += line['amount']
				branch_total_qty += line['qty']
				branch_total_amount_names[ line['warehouse_name'] ] = line['amount']
				percent_amount_qty.append([line['amount'],line['qty']])

			temp_dict_qty = {
				'name': 'Тоо хэмжээ',
				'color': 'rgba(165,170,217,1)',
				'data': temp_data_qty,
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
				'pointPadding': 0.3,
				'pointPlacement': 0.3,
			}
			temp_dict_amount = {
				'name': 'Борлуулалт',
				'yAxis': 1,
				'color': 'rgba(126,86,134,.9)',
				'data': temp_data_amount,
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
				'pointPadding': 0.4,
				'pointPlacement': 0.3,
			}

			# Өмнөх оны борлуулалт
			self.env.cr.execute(query1_before)
			query_result_before = self.env.cr.dictfetchall()
			
			temp_data_amount = []
			temp_data_qty = []

			branch_total_amount_before = 0
			branch_total_qty_before = 0

			for line in query_result_before:
				temp = {
					'name': line['warehouse_name'],
					'y': line['amount'],
				}
				temp_data_amount.append(temp)
				temp = {
					'name': line['warehouse_name'],
					'y': line['qty'],
				}
				temp_data_qty.append(temp)
				branch_total_amount_before += line['amount']
				branch_total_qty_before += line['qty']

			temp_dict_qty_before = {
				'name': 'Өмнөх тоо',
				'color': 'rgba(65,170,217,1)',
				'data': temp_data_qty,
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
				'pointPadding': 0.3,
				'pointPlacement': -0.3
			}
			temp_dict_amount_before = {
				'name': 'Өмнөх',
				'yAxis': 1,
				'color': 'rgba(26,86,134,.9)',
				'data': temp_data_amount,
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
				'pointPadding': 0.4,
				'pointPlacement': -0.3
			}
			# 
			series.append(temp_dict_qty_before)
			series.append(temp_dict_amount_before)
			# 
			series.append(temp_dict_qty)
			series.append(temp_dict_amount)

			# Мастер төлөвлөгөө инчээр
			query_plans = """
				SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						sw.name as warehouse_name,
						(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_sold
						-- smpl.amount as amount,
						-- smpl.qty as qty_sold
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
					      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
						  smp.year = %d and
						  smp.month in (%s) and
						  swp.id = %d 
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name
			"""
			query4 = query_plans % (year, months, warehouse_id)
			self.env.cr.execute(query4)
			# print '-----', query4
			query_result_plan = self.env.cr.dictfetchall()

			temp_data_amount = []
			temp_data_qty = []

			percent_data_amount = []
			percent_data_qty = []

			branch_total_amount_plan = 0
			branch_total_qty_plan = 0

			for line in query_result_plan:
				temp = {
					'name': line['warehouse_name'],
					'y': line['amount'],
				}
				temp_data_amount.append(temp)
				temp = {
					'name': line['warehouse_name'],
					'y': line['qty'],
				}
				temp_data_qty.append(temp)
				branch_total_amount_plan += line['amount']
				branch_total_qty_plan += line['qty']


				# Percent
				per = 0
				if line['warehouse_name'] in categ_names:
					idx = categ_names.index(line['warehouse_name'])
					s_amount = percent_amount_qty[idx][0]
					per = s_amount*100/line['amount']
				temp = {
					'name': line['warehouse_name'],
					'y': round(per,2),
				}
				percent_data_amount.append(temp)
				# 
				if line['warehouse_name'] in categ_names:
					s_qty = percent_amount_qty[idx][1]
					per = s_qty*100/line['qty']
				temp = {
					'name': line['warehouse_name'],
					'y': round(per,2),
				}
				percent_data_qty.append(temp)


			temp_dict_plan_qty = {
		 		'name': 'Тоо хэмжээ',
		 		'color': 'rgba(248,161,63,1)',
		 		'data': temp_data_qty,
		 		'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
		 		'pointPadding': 0.3,
		 		'pointPlacement': 0,
		 	} 
		 	temp_dict_plan_amount = {
		 		'name': 'Төлөвлөгөө',
		 		'color': 'rgba(186,60,61,.9)',
		 		'data': temp_data_amount,
		 		'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
		 		'pointPadding': 0.4,
		 		'pointPlacement': 0,
		 		'yAxis': 1
		 	}
		 	# Percent
		 	temp_dict_percent = {
				'type':'spline',
				'yAxis': 2,
				'name': 'Гүйцэтгэлийн дүн %',
				'data': percent_data_amount,
				'marker': {
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Дүн {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			temp_dict_qty_percent = {
				'type':'spline',
				'yAxis': 2,
				'name': 'Гүйцэтгэлийн тоо %',
				'data': percent_data_qty,
				'marker': {
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Тоо {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
		 	
			series.append(temp_dict_plan_qty)
			series.append(temp_dict_plan_amount)
			series.append(temp_dict_percent)
			series.append(temp_dict_qty_percent)

			datas['branch_categ_names'] = categ_names
			datas['branch_sales_chart'] = series

			# Салбарын нийт
			series_total = []
		 	# Өмнөх он
		 	temp_dict_qty_before = {
				'name': 'Өмнөх тоо',
				'color': 'rgba(65,170,217,1)',
				'data': [{'name':u'Салбарын нийт', 'y': branch_total_qty_before }],
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
				'data': [{'name':u'Салбарын нийт', 'y': round(branch_total_amount_before,2) }],
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
		 		'data': [{'name':u'Салбарын нийт', 'y': branch_total_qty_plan }],
		 		'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
		 		'pointPadding': 0.4,
		 		'pointPlacement': 0,
		 	} 
		 	temp_dict_plan_amount = {
		 		'name': 'Төлөвлөгөө',
		 		'color': 'rgba(186,60,61,.9)',
		 		'data': [{'name':u'Салбарын нийт', 'y': branch_total_amount_plan }],
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
				'data': [{'name':u'Салбарын нийт', 'y':  branch_total_qty}],
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
				'data': [{'name':u'Салбарын нийт', 'y': branch_total_amount }],
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
				'pointPadding': 0.45,
				'pointPlacement': 0.3,
			}

			# Гүйцэтгэлийн хувь
			per = 0
			if branch_total_qty_plan > 0:
				per = round((branch_total_qty*100)/branch_total_qty_plan,2)
			temp_dict_qty_percent = {
				'name': 'Гүйцэтгэл тоо %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(30,242,69,1)',
				'data': [{'name':u'Салбарын нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': 0.17,
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Гүйцэтгэл тоо {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			if branch_total_amount_plan > 0:
				per = round((branch_total_amount*100)/branch_total_amount_plan,2)
			temp_dict_amount_percent = {
				'name': 'Гүйцэтгэл дүн %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(28,164,6,.9)',
				'data': [{'name':u'Салбарын нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': 0.17,
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Гүйцэтгэл дүн {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}

			# Өсөлтийн хувь
			diff = 0
			plug = 1
			if branch_total_qty_before > branch_total_qty:
				diff = branch_total_qty_before - branch_total_qty
				plug = -1
			else:
				diff = branch_total_qty - branch_total_qty_before

			per = 0
			if branch_total_qty_before != 0:
				per = round((diff*100)/branch_total_qty_before,2) * plug

			temp_dict_qty_inc_percent = {
				'name': 'Өсөлт тоо %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(30,212,69,1)',
				'data': [{'name':u'Салбарын нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': -0.17,
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Өсөлт тоо {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			# Amount
			diff = 0
			plug = 1
			if branch_total_amount_before > branch_total_amount:
				diff = branch_total_amount_before - branch_total_amount
				plug = -1
			else:
				diff = branch_total_amount - branch_total_amount_before
			per = 0
			if branch_total_amount_before != 0:
				per = round((diff*100)/branch_total_amount_before,2) * plug
			temp_dict_amount_inc_percent = {
				'name': 'Өсөлт дүн %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(28,114,6,.9)',
				'data': [{'name':u'Салбарын нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': -0.17,
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Өсөлт дүн {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}

			series_total.append(temp_dict_qty_before)
			series_total.append(temp_dict_amount_before)
			series_total.append(temp_dict_plan_qty)
			series_total.append(temp_dict_plan_amount)
			series_total.append(temp_dict_qty)
			series_total.append(temp_dict_amount)
			series_total.append(temp_dict_qty_percent)
			series_total.append(temp_dict_amount_percent)
			series_total.append(temp_dict_qty_inc_percent)
			series_total.append(temp_dict_amount_inc_percent)

			datas['branch_total_sales_chart'] = series_total

			# PIE chart - Тасгуудын нийт борлуулалтад эзлэх хувь
			temp_data = []
			series_pie = []

			for key in branch_total_amount_names:
				# per = (branch_total_amount_names[key]*100)/branch_total_amount
				per = branch_total_amount_names[key]
				temp_dict = {
					'name': key,
					'y': per,
					'drilldown': key,
				}
				temp_data.append(temp_dict)

			temp_dict = {
				'name': 'Борлуулалт',
				'colorByPoint': True,
				'data': temp_data,
			}
			series_pie.append(temp_dict)
			datas['amount_pie_chart'] = series_pie

			self.env.cr.execute(query_sales_category)
			# print '-----sales categss---', query_sales_category
			query_result = self.env.cr.dictfetchall()

			# drilldown бэлдэх
			drilldown = {}
			series_drilldown = []
			temp_data = []
			wh_name = ''
			first = True
			for line in query_result:
				if first:
					wh_name = line['warehouse_name']
					first = False

				if wh_name != line['warehouse_name']:
					temp_dict = {
						'name': wh_name,
						'id': wh_name,
						'data': temp_data,
					}
					series_drilldown.append(temp_dict)
					temp_data = []
					wh_name = line['warehouse_name']
				
				per = 0
				try:
					# per = (line['amount']*100)/branch_total_amount_names[wh_name]
					per = line['amount']
				except Exception as e:
					per = 0

				val = (line['categ_name'], per)
				temp_data.append(val)

			temp_dict = {
				'name': wh_name,
				'id': wh_name,
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
				
			drilldown['series'] = series_drilldown
			datas['amount_drill_pie_chart'] = drilldown

			# Салбарын 12сард эзлэх борлуулалт POLAR
			# Энэ он
			current_year = str(year)+'-%'
			query_sales = """
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
							%s 
						  so.validity_date::text ilike '%s' and 
						  swp.id = %d
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
					       %s
						  (po.date_order + interval '8 hour')::date::text ilike '%s' and
						  swp.id = %d
					) as temp
				GROUP BY order_date, mm
				ORDER BY order_date, mm
			"""
			query1 = query_sales % (where_categ_ids, current_year, warehouse_id, where_categ_ids, current_year, warehouse_id)
			# print '=============', query1

			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			
			series_amount_monthly = []
			series_qty_monthly = []
			for line in query_result:
				# Салбарын 12 сар
				temp = {
						'name': line['mm'],
						'y': line['amount'],
					}
				series_amount_monthly.append(temp)
				temp = {
						'name': line['mm'],
						'y': line['qty'],
					}
				series_qty_monthly.append(temp)

			# Өмнөх оны борлуулалт сараар авах
			before_year = str(year-1)+'-%'
			query2 =  query_sales % (where_categ_ids, before_year, warehouse_id, where_categ_ids, before_year, warehouse_id)
			# print '---com b---', query2
			self.env.cr.execute(query2)
			query_result = self.env.cr.dictfetchall()

			series_amount_monthly_before = []
			series_qty_monthly_before = []
			for line in query_result:
				temp = {
						'name': line['mm'],
						'y': line['amount'],
					}
				series_amount_monthly_before.append(temp)
				temp = {
						'name': line['mm'],
						'y': line['qty'],
					}
				series_qty_monthly_before.append(temp)

			# Мастер төлөвлөгөө
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
					      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
						  smp.year = %d and
						  swp.id = %d 
					) as temp
				GROUP BY mm
				ORDER BY mm
			"""
			query4 = query_plans % (year, warehouse_id)
			self.env.cr.execute(query4)
			# print '==========', query4
			query_result_plan = self.env.cr.dictfetchall()

			series_amount_monthly_plan = []
			series_qty_monthly_plan = []
			series_per_amount = []
			series_per_qty = []
			for line in query_result_plan:
				temp = {
					'name': line['mm'],
					'y': line['amount'],
				}
				series_amount_monthly_plan.append(temp)
				temp = {
					'name': line['mm'],
					'y': line['qty'],
				}
				series_qty_monthly_plan.append(temp)
				# %
				plist = [ddd['y'] for ddd in series_amount_monthly if ddd['name'] == line['mm']]
				if plist:
					sale_amount = plist[0]
					if sale_amount != 0:
						per = round((sale_amount*100)/line['amount'],2)
						temp = {
							'name': line['mm'],
							'y': per
						}
						series_per_amount.append(temp)
				# QTY
				plist = [ddd['y'] for ddd in series_qty_monthly if ddd['name'] == line['mm']]
				if plist:
					sale_qty = plist[0]
					if sale_qty != 0:
						per = round((sale_qty*100)/line['qty'],2)
						temp = {
							'name': line['mm'],
							'y': per
						}
						series_per_qty.append(temp)

			# Өгөгдөл цэнэглэх - amount
			temp_dict_before = {
				'type':'column',
				'name': 'Өмнөх',
				'data': series_amount_monthly_before,
			}
			temp_dict_plan = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': series_amount_monthly_plan,
			}
			temp_dict_sale = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': series_amount_monthly,
			}
			series1 = []
			series1.append(temp_dict_before)
			series1.append(temp_dict_plan)
			series1.append(temp_dict_sale)
			# Өгөгдөл цэнэглэх - qty
			temp_dict_qty_before = {
				'type':'column',
				'name': 'Өмнөх',
				'data': series_qty_monthly_before,
			}
			temp_dict_qty_plan = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': series_qty_monthly_plan,
			}
			temp_dict_qty_sale = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': series_qty_monthly,
			}
			series2 = []
			series2.append(temp_dict_qty_before)
			series2.append(temp_dict_qty_plan)
			series2.append(temp_dict_qty_sale)

			# Өсөлт бууралт
			series_inc_amount = []
			series_inc_qty = []
			# amount
			for line in temp_dict_sale['data']:
				diff = 0
				plug = 1
				sale_amount = line['y']
				before = 0
				tlist = [ddd['y'] for ddd in temp_dict_before['data'] if ddd['name'] == line['name']]
				if tlist:
					before = tlist[0]
				if before > sale_amount:
					diff = before - sale_amount
					plug = -1
				else:
					diff = sale_amount - before
				if before != 0:
					per = round((diff*100)/before,2) * plug
					temp = {
						'name': line['name'],
						'y': per
					}
					series_inc_amount.append(temp)

			temp_dict_amount_inc_percent = {
				'name': 'Өсөлт %',
				'type':'spline',
				'yAxis': 1,
				'color': 'rgba(30,212,69,1)',
				'data': series_inc_amount,
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Өсөлт {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series1.append(temp_dict_amount_inc_percent)

			# qty
			for line in temp_dict_qty_sale['data']:
				diff = 0
				plug = 1
				sale_qty = line['y']
				before = 0
				tlist = [ddd['y'] for ddd in temp_dict_qty_before['data'] if ddd['name'] == line['name']]
				if tlist:
					before = tlist[0]
				if before > sale_qty:
					diff = before - sale_qty
					plug = -1
				else:
					diff = sale_qty - before
				if before != 0:
					per = round((diff*100)/before,2) * plug
					temp = {
						'name': line['name'],
						'y': per
					}
					series_inc_qty.append(temp)

			temp_dict_qty_inc_percent = {
				'name': 'Өсөлт %',
				'type':'spline',
				'yAxis': 1,
				'color': 'rgba(30,212,69,1)',
				'data': series_inc_qty,
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Өсөлт {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series2.append(temp_dict_qty_inc_percent)

			# Гүйцэтгэл нэмэх
			temp_dict_amount_per_percent = {
				'name': 'Гүйцэтгэл %',
				'type':'spline',
				'yAxis': 1,
				'color': 'rgba(20,112,59,1)',
				'data': series_per_amount,
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Гүйцэтгэл {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series1.append(temp_dict_amount_per_percent)
			# QTY
			temp_dict_qty_per_percent = {
				'name': 'Гүйцэтгэл %',
				'type':'spline',
				'yAxis': 1,
				'color': 'rgba(20,112,59,1)',
				'data': series_per_qty,
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Гүйцэтгэл {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series2.append(temp_dict_qty_per_percent)

			datas['branch_monthly_chart'] = series1
			datas['branch_monthly_qty_chart'] = series2

			# Ангилалаар COLs ====================================================
			query_sales_cat = ""
			query_sales_category = ""
			query_sales_category_before = ""
			query_plans = ""
			query_plans_drill = ""
			query_sales_cat_drill_now = ""
			query_sales_cat_drill_before = ""
			if month < 13:
				query_sales_cat = """
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
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
							   %s
							  so.validity_date::text ilike '%s' and 
							  swp.id = %d
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
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE 
						       %s 
							  (po.date_order + interval '8 hour')::date::text ilike '%s' and
							  swp.id = %d
						) as temp
					GROUP BY categ_name
					ORDER BY categ_name
				"""
				query_sales_category = query_sales_cat % (where_categ_ids, current_date, warehouse_id, where_categ_ids, current_date, warehouse_id)
				query_sales_category_before = query_sales_cat % (where_categ_ids, before_date, warehouse_id, where_categ_ids, before_date, warehouse_id)
				# Drill query
				query_sales_cat_drill = """
					SELECT categ_name, p_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT  
							pc.name as categ_name,
							(CASE WHEN pc.code = '71' THEN pts.name 
							      WHEN pc.code = '72' THEN ptt.name ELSE pt.name END) as p_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
						LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
							   %s
							  so.validity_date::text ilike '%s' and 
							  swp.id = %d
						UNION ALL
						SELECT 
							pc.name as categ_name,
							(CASE WHEN pc.code = '71' THEN pts.name 
							      WHEN pc.code = '72' THEN ptt.name ELSE pt.name END) as p_name,
							pol.price_unit * pol.qty as amount,
							pol.qty as qty_sold
						FROM pos_order_line as pol
						LEFT JOIN pos_order as po on (po.id = pol.order_id)
						LEFT JOIN product_product as pp on (pp.id = pol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
						LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE 
						       %s 
							  (po.date_order + interval '8 hour')::date::text ilike '%s' and
							  swp.id = %d
						) as temp
					GROUP BY categ_name, p_name
					ORDER BY categ_name, p_name
				"""
				query_sales_cat_drill_now = query_sales_cat_drill % (where_categ_ids, current_date, warehouse_id, where_categ_ids, current_date, warehouse_id)
				query_sales_cat_drill_before = query_sales_cat_drill % (where_categ_ids, before_date, warehouse_id, where_categ_ids, before_date, warehouse_id)
			else:
				query_sales_cat = """
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
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
							   %s
							  so.validity_date >= '%s' and 
							  so.validity_date <= '%s' and 
							  swp.id = %d
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
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
						WHERE po.state in ('paid','done','invoiced') and 
						       %s 
							  (po.date_order + interval '8 hour')::date >= '%s' and 
							  (po.date_order + interval '8 hour')::date <= '%s' and 
							  swp.id = %d
						) as temp
					GROUP BY categ_name
					ORDER BY categ_name
				"""
				query_sales_category = query_sales_cat % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)
				query_sales_category_before = query_sales_cat % (where_categ_ids, before_date, before_date_end, warehouse_id, where_categ_ids, before_date, before_date_end, warehouse_id)
				# Drill query
				query_sales_cat_drill = """
					SELECT categ_name, p_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
						SELECT  
							pc.name as categ_name,
							(CASE WHEN pc.code = '71' THEN pts.name 
							      WHEN pc.code = '72' THEN ptt.name ELSE pt.name END) as p_name,
							sol.price_unit * (sol.qty_delivered-sol.return_qty) as amount,
							(sol.qty_delivered-sol.return_qty) as qty_sold
						FROM sale_order_line as sol
						LEFT JOIN sale_order as so on (so.id = sol.order_id)
						LEFT JOIN product_product as pp on (pp.id = sol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
						LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
							   %s
							  so.validity_date >= '%s' and 
							  so.validity_date <= '%s' and 
							  swp.id = %d
						UNION ALL
						SELECT 
							pc.name as categ_name,
							(CASE WHEN pc.code = '71' THEN pts.name 
							      WHEN pc.code = '72' THEN ptt.name ELSE pt.name END) as p_name,
							pol.price_unit * pol.qty as amount,
							pol.qty as qty_sold
						FROM pos_order_line as pol
						LEFT JOIN pos_order as po on (po.id = pol.order_id)
						LEFT JOIN product_product as pp on (pp.id = pol.product_id)
						LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
						LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
						LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
						LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
						LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
						LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
						--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
						WHERE po.state in ('paid','done','invoiced') and 
						       %s 
							  (po.date_order + interval '8 hour')::date >= '%s' and 
							  (po.date_order + interval '8 hour')::date <= '%s' and 
							  swp.id = %d
						) as temp
					GROUP BY categ_name, p_name
					ORDER BY categ_name, p_name
				"""
				query_sales_cat_drill_now = query_sales_cat_drill % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)
				query_sales_cat_drill_before = query_sales_cat_drill % (where_categ_ids, before_date, before_date_end, warehouse_id, where_categ_ids, before_date, before_date_end, warehouse_id)

			# Өмнөх он
			self.env.cr.execute(query_sales_category_before)
			query_cat_result_before = self.env.cr.dictfetchall()

			series_total_cat = []
			series_total_cat_qty = []
			for line in query_cat_result_before:
				temp = {
					'name': line['categ_name'],
					'y': line['amount'],
					'drilldown': line['categ_name']+'_before',
				}
				series_total_cat.append(temp)
				temp = {
					'name': line['categ_name'],
					'y': line['qty'],
					'drilldown': line['categ_name']+'_before',
				}
				series_total_cat_qty.append(temp)

			temp_dict_sale_before = {
				'type':'column',
				'name': 'Өмнөх он',
				'data': series_total_cat,
			}
			temp_dict_sale_before_qty = {
				'type':'column',
				'name': 'Өмнөх он',
				'data': series_total_cat_qty,
			}
			series2 = []
			series2_qty = []
			series2.append(temp_dict_sale_before)
			series2_qty.append(temp_dict_sale_before_qty)

			# PLAN
			query_plans = """
				SELECT categ_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						pc.name as categ_name,
						(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_sold
						-- smpl.amount as amount,
						-- smpl.qty as qty_sold
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
					      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
					       %s 
						  smp.year = %d and
						  smp.month in (%s) and
						  swp.id = %d 
					) as temp
				GROUP BY categ_name
				ORDER BY categ_name
			"""
			query_plans = query_plans % (where_categ_ids, year, months, warehouse_id)
			self.env.cr.execute(query_plans)
			query_cat_result_plan = self.env.cr.dictfetchall()

			series_total_cat_plan = []
			series_total_cat_plan_qty = []
			for line in query_cat_result_plan:
				temp = {
					'name': line['categ_name'],
					'y': line['amount'],
					'drilldown': line['categ_name']+'_plan',
				}
				series_total_cat_plan.append(temp)
				temp = {
					'name': line['categ_name'],
					'y': line['qty'],
					'drilldown': line['categ_name']+'_plan',
				}
				series_total_cat_plan_qty.append(temp)

			temp_dict_cat_plan = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': series_total_cat_plan,
			}
			temp_dict_cat_plan_qty = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': series_total_cat_plan_qty,
			}
			series2.append(temp_dict_cat_plan)
			series2_qty.append(temp_dict_cat_plan_qty)

			# Энэ он
			self.env.cr.execute(query_sales_category)
			query_cat_result = self.env.cr.dictfetchall()

			series_total_cat = []
			series_total_cat_qty = []
			series_inc_amount = []
			series_inc_qty = []
			for line in query_cat_result:
				temp = {
					'name': line['categ_name'],
					'y': line['amount'],
					'drilldown': line['categ_name']+'_now',
				}
				series_total_cat.append(temp)
				temp = {
					'name': line['categ_name'],
					'y': line['qty'],
					'drilldown': line['categ_name']+'_now',
				}
				series_total_cat_qty.append(temp)

				# Өсөлт олох
				# amount
				tlist = [ddd['y'] for ddd in temp_dict_sale_before['data'] if ddd['name'] == line['categ_name']]
				tlist_qty = [ddd['y'] for ddd in temp_dict_sale_before_qty['data'] if ddd['name'] == line['categ_name']]
				
				sale_amount = line['amount']
				sale_qty = line['qty']
				
				diff = 0
				plug = 1
				before = 0
				diff_qty = 0
				plug_qty = 1
				before_qty = 0

				if tlist:
					before = tlist[0]
					before_qty = tlist_qty[0]
				if before > sale_amount:
					diff = before - sale_amount
					plug = -1
				else:
					diff = sale_amount - before
				if before_qty > sale_amount:
					diff_qty = before_qty - sale_qty
					plug_qty = -1
				else:
					diff_qty = sale_qty - before_qty
				if before != 0:
					per = round((diff*100)/before,2) * plug
					temp = {
						'name': line['categ_name'],
						'y': per
					}
					series_inc_amount.append(temp)
				# qty
				if before_qty != 0:
					per = round((diff_qty*100)/before_qty,2) * plug_qty
					temp = {
						'name': line['categ_name'],
						'y': per
					}
					series_inc_qty.append(temp)

			temp_dict_sale = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': series_total_cat,
			}
			series2.append(temp_dict_sale)
			temp_dict_sale_qty = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': series_total_cat_qty,
			}
			series2_qty.append(temp_dict_sale_qty)

			# Өсөлт
			# amount
			temp_dict_amount_inc_percent = {
				'name': 'Өсөлт %',
				'type':'spline',
				'yAxis': 1,
				'color': 'rgba(30,212,69,1)',
				'data': series_inc_amount,
				'marker': {
					'radius': 5,
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Өсөлт {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series2.append(temp_dict_amount_inc_percent)
			# qty
			# Өсөлт
			temp_dict_qty_inc_percent = {
				'name': 'Өсөлт %',
				'type':'spline',
				'yAxis': 1,
				'color': 'rgba(30,212,69,1)',
				'data': series_inc_qty,
				'marker': {
					'radius': 5,
					'lineWidth': 3,
				},
				'dataLabels': {
					'enabled': True,
					'color': '#FFFFFF',
					'align': 'center',
					'format': 'Өсөлт {point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series2_qty.append(temp_dict_qty_inc_percent)

			datas['by_categ_sales_chart'] = series2
			datas['by_categ_sales_qty_chart'] = series2_qty

			# Drilldown SET xiix ----------------------------------------
			# Өмнөх он
			self.env.cr.execute(query_sales_cat_drill_before)
			query_cat_drill_before_result = self.env.cr.dictfetchall()
			# VARs
			drilldown = {}
			series_drilldown = []
			drilldown_qty = {}
			series_drilldown_qty = []

			temp_data = []
			temp_data_qty = []
			cat_name = ''
			first = True
			for line in query_cat_drill_before_result:
				if first:
					cat_name = line['categ_name']
					first = False

					val = (line['p_name'], line['amount'])
					temp_data.append(val)
					# qty
					val = (line['p_name'], line['qty'])
					temp_data_qty.append(val)
				else:
					if cat_name != line['categ_name']:
						temp_dict = {
							'name': u'Өмнөх',
							'type':'column',
							'id': cat_name+'_before',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Өмнөх',
							'type':'column',
							'id': cat_name+'_before',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						cat_name = line['categ_name']
					
					val = (line['p_name'], line['amount'])
					temp_data.append(val)
					# qty
					val = (line['p_name'], line['qty'])
					temp_data_qty.append(val)

			temp_dict = {
				'name': u'Өмнөх',
				'type':'column',
				'id': cat_name+'_before',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Өмнөх',
				'type':'column',
				'id': cat_name+'_before',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)

			# PLAN drill -----------------------
			query_plans_drill = """
				SELECT categ_name, p_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						pc.name as categ_name,
						(CASE WHEN pc.code = '71' THEN pts.name 
						      WHEN pc.code = '72' THEN ptt.name ELSE pt.name END) as p_name,
				        (CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_sold
						-- smpl.amount as amount,
						-- smpl.qty as qty_sold
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN product_type_size as pts on (pts.id = pt.product_type_size)
					LEFT JOIN product_type_size as ptt on (ptt.id = pt.product_type_template)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
					      (smp.is_holiday_plan != 't' or smp.is_holiday_plan is null) and 
					       %s 
						  smp.year = %d and
						  smp.month in (%s) and
						  swp.id = %d 
					) as temp
				GROUP BY categ_name, p_name
				ORDER BY categ_name, p_name
			"""
			query_plans_drill = query_plans_drill % (where_categ_ids, year, months, warehouse_id)
			self.env.cr.execute(query_plans_drill)
			query_cat_drill_plan_result = self.env.cr.dictfetchall()
			temp_data = []
			temp_data_qty = []
			cat_name = ''
			first = True
			for line in query_cat_drill_plan_result:
				if first:
					cat_name = line['categ_name']
					first = False

					val = (line['p_name'], line['amount'])
					temp_data.append(val)
					# qty
					val = (line['p_name'], line['qty'])
					temp_data_qty.append(val)
				else:
					if cat_name != line['categ_name']:
						temp_dict = {
							'name': u'Төлөвлөгөө',
							'type':'column',
							'id': cat_name+'_plan',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Төлөвлөгөө',
							'type':'column',
							'id': cat_name+'_plan',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						cat_name = line['categ_name']
					
					val = (line['p_name'], line['amount'])
					temp_data.append(val)
					# qty
					val = (line['p_name'], line['qty'])
					temp_data_qty.append(val)

			temp_dict = {
				'name': u'Төлөвлөгөө',
				'type':'column',
				'id': cat_name+'_plan',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Төлөвлөгөө',
				'type':'column',
				'id': cat_name+'_plan',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)

			# Энэ он -----------
			self.env.cr.execute(query_sales_cat_drill_now)
			query_cat_drill_now_result = self.env.cr.dictfetchall()
			# VARs
			temp_data = []
			temp_data_qty = []
			cat_name = ''
			first = True
			for line in query_cat_drill_now_result:
				if first:
					cat_name = line['categ_name']
					first = False

					val = (line['p_name'], line['amount'])
					temp_data.append(val)
					# qty
					val = (line['p_name'], line['qty'])
					temp_data_qty.append(val)
				else:
					if cat_name != line['categ_name']:
						temp_dict = {
							'name': u'Энэ он',
							'type':'column',
							'id': cat_name+'_now',
							'data': temp_data,
						}
						series_drilldown.append(temp_dict)
						temp_data = []
						# qty
						temp_dict_qty = {
							'name': u'Энэ он',
							'type':'column',
							'id': cat_name+'_now',
							'data': temp_data_qty,
						}
						series_drilldown_qty.append(temp_dict_qty)
						temp_data_qty = []
						cat_name = line['categ_name']
					
					val = (line['p_name'], line['amount'])
					temp_data.append(val)
					# qty
					val = (line['p_name'], line['qty'])
					temp_data_qty.append(val)

			temp_dict = {
				'name': u'Энэ он',
				'type':'column',
				'id': cat_name+'_now',
				'data': temp_data,
			}
			series_drilldown.append(temp_dict)
			# qty
			temp_dict_qty = {
				'name': u'Энэ он',
				'type':'column',
				'id': cat_name+'_now',
				'data': temp_data_qty,
			}
			series_drilldown_qty.append(temp_dict_qty)
			# -----
			drilldown['series'] = series_drilldown
			datas['by_categ_sales_drill'] = drilldown
			# 
			drilldown_qty['series'] = series_drilldown_qty
			datas['by_categ_sales_qty_drill'] = drilldown_qty

		return datas
