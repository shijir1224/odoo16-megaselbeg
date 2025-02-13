# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError

# Баярын борлуулалт
class SalesPlanDashboard05(models.TransientModel):
	_name = 'sales.plan.dashboard.05'
	_description = 'Holidays dashboard'

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

	holiday = fields.Selection([
			('new_year', u'Шинэ жил'), 
			('valentine', u'Валентин'), 
			('mart8', u'Мартын 8'), 
			('solder18', u'Цэргийн баяр'), 
			('kids', u'Хүүхдийн баяр'), 
		], required=True, string=u'Баярын нэр')

	warehouse_id = fields.Many2one('stock.warehouse', string=u'Салбар',
		domain=[('is_branch','=',True),('parent_id','=',False)])

	product_type = fields.Selection([
			('cake', u'Бялуу'), 
			('bakery', u'Бэйкери'), 
		], string=u'Бүтээгдэхүүний төрөл')

	
	def get_datas(self, year, holiday, product_type, context=None):
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
		# Ангилалаар
		where_categ_ids = ""
		if product_type == 'cake':
			cake_categ = self.env['product.category'].search([('code','in',['75','72','71'])])
			c_ids = self.env['product.category'].search([('id','child_of',cake_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "
		elif product_type == 'bakery':
			where_categ_ids = " and "
			bakery_categ = self.env['product.category'].search([('code','=','8')], limit=1)
			c_ids = self.env['product.category'].search([('id','child_of',bakery_categ.id)]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "
		else:
			all_categ = self.env['product.category'].search([('code','in',['100'])])
			c_ids = self.env['product.category'].search([('id','child_of',all_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "

		warehouse_ids = []
		if holiday:
			current_date = str(year)
			before_date = str(year-1)
			before_date2 = str(year-2)

			current_date_end = str(year)
			before_date_end = str(year-1)
			before_date2_end = str(year-2)

			# Өдөр олох
			if holiday == 'new_year':
				current_date += '-12-28'
				current_date_end = str(year+1)+'-01-01'
				
				before_date += '-12-28'
				before_date_end = str(year)+'-01-01'

				before_date2 += '-12-28'
				before_date2_end = str(year-1)+'-01-01'
			elif holiday == 'valentine':
				current_date += '-02-14'
				current_date_end += '-02-14'

				before_date += '-02-14'
				before_date_end += '-02-14'

				before_date2 += '-02-14'
				before_date2_end += '-02-14'
			elif holiday == 'mart8':
				current_date += '-03-06'
				current_date_end += '-03-08'

				before_date += '-03-06'
				before_date_end += '-03-08'

				before_date2 += '-03-06'
				before_date2_end += '-03-08'
			elif holiday == 'solder18':
				current_date += '-03-16'
				current_date_end += '-03-18'

				before_date += '-03-16'
				before_date_end += '-03-18'

				before_date2 += '-03-16'
				before_date2_end += '-03-18'
			elif holiday == 'kids':
				current_date += '-05-30'
				current_date_end += '-06-01'

				before_date += '-05-30'
				before_date_end += '-06-01'

				before_date2 += '-05-30'
				before_date2_end += '-06-01'

			# 
			series = []
			series_qty = []
			# Салбар буюу тасгийн нэрс
			categ_names = []

			plan_percent_qty = {}
			plan_percent_amount = {}

			# Борлуулалтын төлөвлөгөө
			# Болон нийлүүлсэн тоо
			query_plans = """
				SELECT warehouse_name, 
					sum(qty_plan) as qty_plan,
					sum(amount_plan) as amount_plan,
					sum(qty_delivered) as qty_delivered,
					sum(amount_delivered) as amount_delivered
				FROM (
					SELECT  
						swp.name as warehouse_name,
						(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount_plan,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_plan
						-- smpl.qty as qty_plan,
						-- (smpl.qty * smpl.price_unit) as amount_plan,
						smpl.delivery_qty as qty_delivered,
						(smpl.delivery_qty*pt.list_price) as amount_delivered
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
						   %s
						  smp.is_holiday_plan = 't' and 
						  smp.date_plan >= '%s' and
						  smp.date_plan <= '%s'
						   %s 
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name
			"""
			query4 = query_plans % (where_categ_ids, current_date, current_date_end, where_user_wh)
			self.env.cr.execute(query4)
			# print '-------plan---05----', query4
			query_result = self.env.cr.dictfetchall()
			
			temp_qty = []
			temp_amount = []
			temp_qty_delivered = []
			temp_amount_delivered = []
			company_total_qty_plan = 0
			company_total_amount_plan = 0
			company_total_qty_delivery = 0
			company_total_amount_delivery = 0
			for line in query_result:
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_plan',
					'y': line['qty_plan'],
				}
				temp_qty.append(temp)
				company_total_qty_plan += line['qty_plan']
				plan_percent_qty[ line['warehouse_name'] ] = line['qty_plan']
				# 
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_plan',
					'y': line['amount_plan'],
				}
				temp_amount.append(temp)
				company_total_amount_plan += line['amount_plan']
				plan_percent_amount[ line['warehouse_name'] ] = line['amount_plan']
				# Нийлүүлсэн тоо
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_delivery',
					'y': line['qty_delivered'],
				}
				temp_qty_delivered.append(temp)
				company_total_qty_delivery += line['qty_delivered']
				# 
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_delivery',
					'y': line['amount_delivered'],
				}
				temp_amount_delivered.append(temp)
				company_total_amount_delivery += line['amount_delivered']

			temp_dict_plan_qty = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': temp_qty,
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
			}
			# 
			temp_dict_plan_amount = {
				'type':'column',
				'name': 'Төлөвлөгөө',
				'data': temp_amount,
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
			}
			# Delivery
			temp_dict_delivered_qty = {
				'type':'column',
				'name': 'Нийлүүлсэн',
				'data': temp_qty_delivered,
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
			}
			temp_dict_delivered_amount = {
				'type':'column',
				'name': 'Нийлүүлсэн',
				'data': temp_amount_delivered,
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
			}
			# Drilldown бэлдэх
			series_drilldown = []
			series_drilldown_qty = []

			query_plans = """
				SELECT warehouse_name, p_type, 
					sum(qty_plan) as qty_plan,
					sum(amount_plan) as amount_plan,
					sum(qty_delivered) as qty_delivered,
					sum(amount_delivered) as amount_delivered
				FROM (
					SELECT  
						swp.name as warehouse_name,
						(CASE WHEN pc.code = '72' THEN 'brand'
						      WHEN pc.code = '71' THEN 'happy' ELSE 'bakery' END) as p_type, 
				        (CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount_plan,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_plan
						-- smpl.qty as qty_plan,
						-- (smpl.qty * smpl.price_unit) as amount_plan,
						smpl.delivery_qty as qty_delivered,
						(smpl.delivery_qty*pt.list_price) as amount_delivered
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
						   %s
						  smp.is_holiday_plan = 't' and 
						  smp.date_plan >= '%s' and
						  smp.date_plan <= '%s'
						   %s 
					) as temp
				GROUP BY warehouse_name, p_type
				ORDER BY warehouse_name, p_type
			"""
			query5 = query_plans % (where_categ_ids, current_date, current_date_end, where_user_wh)
			self.env.cr.execute(query5)
			query_result_plan_drill = self.env.cr.dictfetchall()
			temp_amount = []
			temp_qty = []
			temp_del_amount = []
			temp_del_qty = []
			w_name = ''
			for line in query_result_plan_drill:
				if w_name != line['warehouse_name']:
					if temp_amount:
						# Plan
						temp_dict = {
							'name': 'Төлөвлөгөө',
							'type':'column',
							'id': w_name+'_plan',
							'data': temp_amount,
						}
						series_drilldown.append(temp_dict)
						# 
						temp_dict = {
							'name': 'Төлөвлөгөө',
							'type':'column',
							'id': w_name+'_plan',
							'data': temp_qty,
						}
						series_drilldown_qty.append(temp_dict)
						# Delivery
						temp_dict = {
							'name': 'Нийлүүлсэн',
							'type':'column',
							'id': w_name+'_delivery',
							'data': temp_del_amount,
						}
						series_drilldown.append(temp_dict)
						# 
						temp_dict = {
							'name': 'Нийлүүлсэн',
							'type':'column',
							'id': w_name+'_delivery',
							'data': temp_del_qty,
						}
						series_drilldown_qty.append(temp_dict)
						# 
						temp_amount = []
						temp_qty = []
						temp_del_amount = []
						temp_del_qty = []
				
				val = (line['p_type'], line['amount_plan'])
				temp_amount.append(val)
				val = (line['p_type'], line['qty_plan'])
				temp_qty.append(val)
				val = (line['p_type'], line['amount_delivered'])
				temp_del_amount.append(val)
				val = (line['p_type'], line['qty_delivered'])
				temp_del_qty.append(val)
				w_name = line['warehouse_name']
			# Last item
			temp_dict = {
				'name': 'Төлөвлөгөө',
				'type':'column',
				'id': w_name+'_plan',
				'data': temp_amount,
			}
			series_drilldown.append(temp_dict)
			# 
			temp_dict = {
				'name': 'Төлөвлөгөө',
				'type':'column',
				'id': w_name+'_plan',
				'data': temp_qty,
			}
			series_drilldown_qty.append(temp_dict)
			# Delivery
			temp_dict = {
				'name': 'Нийлүүлсэн',
				'type':'column',
				'id': w_name+'_delivery',
				'data': temp_del_amount,
			}
			series_drilldown.append(temp_dict)
			# 
			temp_dict = {
				'name': 'Нийлүүлсэн',
				'type':'column',
				'id': w_name+'_delivery',
				'data': temp_del_qty,
			}
			series_drilldown_qty.append(temp_dict)
			# ----------------
			# Энэ оны борлуулалт
			query1 =""
			query_sales = """
				SELECT warehouse_name, sum(qty_sold) as qty,sum(amount_sold) as amount FROM (
					SELECT  
						swp.name as warehouse_name,
						(sol.qty_delivered-sol.return_qty) as qty_sold,
						((sol.qty_delivered-sol.return_qty)*sol.price_unit) as amount_sold
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
						  swp.id is not null
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						pol.qty as qty_sold,
						(pol.qty*pol.price_unit) as amount_sold
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
						  swp.id is not null
						   %s 
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name
			"""
			query1 = query_sales % (where_categ_ids, current_date, current_date_end, where_user_wh, where_categ_ids, current_date, current_date_end, where_user_wh)

			self.env.cr.execute(query1)
			query_result = self.env.cr.dictfetchall()
			# print '---------sales------', query1

			# VARs
			percent_data_qty = []
			temp_qty = []
			percent_data_amount = []
			temp_amount = []
			company_total_qty = 0
			company_total_amount = 0
			for line in query_result:
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_sale',
					'y': line['qty'],
				}
				temp_qty.append(temp)
				company_total_qty += line['qty']
				# 
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_sale',
					'y': line['amount'],
				}
				temp_amount.append(temp)
				company_total_amount += line['amount']
				# Percent
				per = 0
				if line['warehouse_name'] in plan_percent_qty:
					p_qty = plan_percent_qty[ line['warehouse_name'] ]
					per = line['qty']*100/p_qty
					temp = {
						'name': line['warehouse_name'],
						'y': round(per,2),
					}
					percent_data_qty.append(temp)
				# 
				if line['warehouse_name'] in plan_percent_amount:
					p_amount = plan_percent_amount[ line['warehouse_name'] ]
					per = line['amount']*100/p_amount
					temp = {
						'name': line['warehouse_name'],
						'y': round(per,2),
					}
					percent_data_amount.append(temp)

			temp_dict_sales_qty = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': temp_qty,
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
			}
			# 
			temp_dict_sales_amount = {
				'type':'column',
				'name': 'Борлуулалт',
				'data': temp_amount,
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
			}
			temp_dict_percent = {
				'type':'spline',
				'yAxis': 1,
				'name': 'Гүйцэтгэлийн %',
				'data': percent_data_qty,
				'tooltip': {
		 			'valueSuffix': ' %'
		 		},
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
			# 
			temp_dict_percent_amount = {
				'type':'spline',
				'yAxis': 1,
				'name': 'Гүйцэтгэлийн %',
				'data': percent_data_amount,
				'tooltip': {
		 			'valueSuffix': ' %'
		 		},
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
			# ---------------------
			# Энэ оны drilldown
			query_sales_drilldown = """
				SELECT warehouse_name, p_type, sum(qty_sold) as qty,sum(amount_sold) as amount FROM (
					SELECT  
						swp.name as warehouse_name, 
						(CASE WHEN pc.code = '72' THEN 'brand'
						      WHEN pc.code = '71' THEN 'happy' ELSE 'bakery' END) as p_type, 
						(sol.qty_delivered-sol.return_qty) as qty_sold,
						((sol.qty_delivered-sol.return_qty)*sol.price_unit) as amount_sold
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
						  swp.id is not null
						   %s 
					UNION ALL
					SELECT 
						swp.name as warehouse_name,
						(CASE WHEN pc.code = '72' THEN 'brand'
						      WHEN pc.code = '71' THEN 'happy' ELSE 'bakery' END) as p_type, 
						pol.qty as qty_sold,
						(pol.qty*pol.price_unit) as amount_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					--LEFT JOIN product_pricelist as pro_list on (pro_list.id = po.pricelist_id)
					WHERE po.state in ('paid','done','invoiced') and  
						   %s 
						  (po.date_order + interval '8 hour')::date >= '%s' and
						  (po.date_order + interval '8 hour')::date <= '%s' and
						  swp.id is not null
						   %s 
					) as temp
				GROUP BY warehouse_name, p_type
				ORDER BY warehouse_name, p_type
			"""
			query_drilldown_now = query_sales_drilldown % (where_categ_ids, current_date, current_date_end, where_user_wh, where_categ_ids, current_date, current_date_end, where_user_wh)
			self.env.cr.execute(query_drilldown_now)
			query_result_now_drill = self.env.cr.dictfetchall()
			temp_amount = []
			temp_qty = []
			w_name = ''
			for line in query_result_now_drill:
				if w_name != line['warehouse_name']:
					if temp_amount:
						# Now
						temp_dict = {
							'name': 'Борлуулалт',
							'type':'column',
							'id': w_name+'_sale',
							'data': temp_amount,
						}
						series_drilldown.append(temp_dict)
						# 
						temp_dict = {
							'name': 'Борлуулалт',
							'type':'column',
							'id': w_name+'_sale',
							'data': temp_qty,
						}
						series_drilldown_qty.append(temp_dict)
						# 
						temp_amount = []
						temp_qty = []
				
				val = (line['p_type'], line['amount'])
				temp_amount.append(val)
				val = (line['p_type'], line['qty'])
				temp_qty.append(val)
				w_name = line['warehouse_name']
			# Last item
			temp_dict = {
				'name': 'Борлуулалт',
				'type':'column',
				'id': w_name+'_sale',
				'data': temp_amount,
			}
			series_drilldown.append(temp_dict)
			# 
			temp_dict = {
				'name': 'Борлуулалт',
				'type':'column',
				'id': w_name+'_sale',
				'data': temp_qty,
			}
			series_drilldown_qty.append(temp_dict)
			# ---------------------------
			# Өмнөх оны борлуулалт
			query2 = query_sales % (where_categ_ids, before_date, before_date_end, where_user_wh, where_categ_ids, before_date, before_date_end, where_user_wh)
			# print '----------', query2
			self.env.cr.execute(query2)
			query_result = self.env.cr.dictfetchall()
			
			temp_qty = []
			temp_amount = []
			company_total_qty_before = 0
			company_total_amount_before = 0
			for line in query_result:
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_before',
					'y': line['qty'],
				}
				temp_qty.append(temp)
				company_total_qty_before += line['qty']
				# 
				temp = {
					'name': line['warehouse_name'],
					'drilldown': line['warehouse_name']+'_before',
					'y': line['amount'],
				}
				temp_amount.append(temp)
				company_total_amount_before += line['amount']

			temp_dict_before1_qty = {
				'type':'column',
				'name': 'Өмнөх',
				'data': temp_qty,
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
			}
			# 
			temp_dict_before1_amount = {
				'type':'column',
				'name': 'Өмнөх',
				'data': temp_amount,
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
			}
			# Өмнөх оны drilldown
			query_drilldown_before = query_sales_drilldown % (where_categ_ids, before_date, before_date_end, where_user_wh, where_categ_ids, before_date, before_date_end, where_user_wh)
			self.env.cr.execute(query_drilldown_before)
			query_result_before_drill = self.env.cr.dictfetchall()
			temp_amount = []
			temp_qty = []
			w_name = ''
			for line in query_result_before_drill:
				if w_name != line['warehouse_name']:
					if temp_amount:
						# Now
						temp_dict = {
							'name': 'Өмнөх',
							'type':'column',
							'id': w_name+'_before',
							'data': temp_amount,
						}
						series_drilldown.append(temp_dict)
						# 
						temp_dict = {
							'name': 'Өмнөх',
							'type':'column',
							'id': w_name+'_before',
							'data': temp_qty,
						}
						series_drilldown_qty.append(temp_dict)
						# 
						temp_amount = []
						temp_qty = []
				
				val = (line['p_type'], line['amount'])
				temp_amount.append(val)
				val = (line['p_type'], line['qty'])
				temp_qty.append(val)
				w_name = line['warehouse_name']
			# Last item
			temp_dict = {
				'name': 'Өмнөх',
				'type':'column',
				'id': w_name+'_before',
				'data': temp_amount,
			}
			series_drilldown.append(temp_dict)
			# 
			temp_dict = {
				'name': 'Өмнөх',
				'type':'column',
				'id': w_name+'_before',
				'data': temp_qty,
			}
			series_drilldown_qty.append(temp_dict)
			# ---------------------

			# Data г нэмэх
			# QTY
			series_qty.append(temp_dict_before1_qty)
			series_qty.append(temp_dict_plan_qty)
			series_qty.append(temp_dict_delivered_qty)
			series_qty.append(temp_dict_sales_qty)
			series_qty.append(temp_dict_percent)
			# Amount
			series.append(temp_dict_before1_amount)
			series.append(temp_dict_plan_amount)
			series.append(temp_dict_delivered_amount)
			series.append(temp_dict_sales_amount)
			series.append(temp_dict_percent_amount)

			datas['holiday_sales_amount_chart'] = series
			datas['holiday_sales_chart'] = series_qty
			datas['categ_names'] = categ_names
			# Drilldown
			datas['holiday_sales_drilldown_chart'] = {'series':series_drilldown}
			datas['holiday_sales_qty_drilldown_chart'] = {'series':series_drilldown_qty}

			# Компаны нийт
			series_total = []
		 	# Өмнөх он
		 	temp_dict_qty_before_company = {
				'name': 'Өмнөх тоо',
				'color': 'rgba(65,170,217,1)',
				'data': [{'name':u'Компаны нийт', 'y': company_total_qty_before }],
				'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
				'pointPadding': 0.4,
				'pointPlacement': -0.35,
			}
			temp_dict_amount_before_company = {
				'name': 'Өмнөх',
				'yAxis': 1,
				'color': 'rgba(26,86,134,.9)',
				'data': [{'name':u'Компаны нийт', 'y': company_total_amount_before }],
				'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
				'pointPadding': 0.45,
				'pointPlacement': -0.35,
			}
			# Төлөвлөгөө
			temp_dict_plan_qty_company = {
		 		'name': 'Төлөвлөгөө тоо',
		 		'color': 'rgba(248,161,63,1)',
		 		'data': [{'name':u'Компаны нийт', 'y': company_total_qty_plan }],
		 		'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
		 		'pointPadding': 0.4,
		 		'pointPlacement': -0.15,
		 	} 
		 	temp_dict_plan_amount_company = {
		 		'name': 'Төлөвлөгөө',
		 		'color': 'rgba(186,60,61,.9)',
		 		'data': [{'name':u'Компаны нийт', 'y': company_total_amount_plan }],
		 		'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
		 		'pointPadding': 0.45,
		 		'pointPlacement': -0.15,
		 		'yAxis': 1
		 	}
		 	# Нийлүүлсэн
		 	temp_dict_delivery_qty_company = {
		 		'name': 'Нийлүүлсэн тоо',
		 		'color': 'rgba(0,255,0,1)',
		 		'data': [{'name':u'Компаны нийт', 'y': company_total_qty_delivery }],
		 		'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
		 		'pointPadding': 0.4,
		 		'pointPlacement': 0.15,
		 	} 
		 	temp_dict_delivery_amount_company = {
		 		'name': 'Нийлүүлсэн',
		 		'color': 'rgba(0,102,0,.9)',
		 		'data': [{'name':u'Компаны нийт', 'y': company_total_amount_delivery }],
		 		'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
		 		'pointPadding': 0.45,
		 		'pointPlacement': 0.15,
		 		'yAxis': 1
		 	}
			# Энэ он
			temp_dict_qty_company = {
				'name': 'Борлуулалт тоо',
				'color': 'rgba(165,170,217,1)',
				'data': [{'name':u'Компаны нийт', 'y':  company_total_qty}],
				'tooltip': {
		 			'valueSuffix': ' ш',
		 			'colorByPoint': True,
		 		},
				'pointPadding': 0.4,
				'pointPlacement': 0.35,
			}
			temp_dict_amount_company = {
				'name': 'Борлуулалт',
				'yAxis': 1,
				'color': 'rgba(126,86,134,.9)',
				'data': [{'name':u'Компаны нийт', 'y': company_total_amount }],
				'tooltip': {
		 			'valueSuffix': ' ₮',
		 			'colorByPoint': True,
		 		},
				'pointPadding': 0.45,
				'pointPlacement': 0.35,
			}
			# Percents - Гүйцэтгэл хувь
			per = 0
			if company_total_qty_plan != 0:
				per = round((company_total_qty*100)/company_total_qty_plan,2)
			temp_dict_qty_percent_company = {
				'name': 'Гүйцэтгэл тоо %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(255,87,51,.9)',
				'data': [{'name':u'Компаны нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': 0.06,
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
			per = 0
			if company_total_amount_plan != 0:
				per = round((company_total_amount*100)/company_total_amount_plan,2)
			temp_dict_amount_percent_company = {
				'name': 'Гүйцэтгэл дүн %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(199,0,57,.9)',
				'data': [{'name':u'Компаны нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': 0.02,
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
			# Percents - Өсөлт хувь
			diff = 0
			plug = 1
			per = 0
			if company_total_qty_before > company_total_qty:
				diff = company_total_qty_before - company_total_qty
				plug = -1
			else:
				diff = company_total_qty - company_total_qty_before
			if company_total_qty_before != 0:
				per = round((diff*100)/company_total_qty_before,2) * plug
			else:
				per = 100
			temp_dict_qty_inc_company = {
				'name': 'Өсөлт тоо %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(144,3,207,.9)',
				'data': [{'name':u'Компаны нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': -0.06,
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
			# ---------
			diff = 0
			plug = 1
			if company_total_amount_before > company_total_amount:
				diff = company_total_amount_before - company_total_amount
				plug = -1
			else:
				diff = company_total_amount - company_total_amount_before
			if company_total_amount_before != 0:
				per = round((diff*100)/company_total_amount_before,2) * plug
			else:
				per = 100
			temp_dict_amount_inc_company = {
				'name': 'Өсөлт дүн %',
				'type':'spline',
				'yAxis': 2,
				'color': 'rgba(88,24,69,.9)',
				'data': [{'name':u'Компаны нийт', 'y': per }],
				'marker': {
					'radius': 8,
					'lineWidth': 3,
				},
				'pointPlacement': -0.02,
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
			# Add
			series_total.append(temp_dict_qty_before_company)
			series_total.append(temp_dict_amount_before_company)
			series_total.append(temp_dict_plan_qty_company)
			series_total.append(temp_dict_plan_amount_company)
			series_total.append(temp_dict_delivery_qty_company)
			series_total.append(temp_dict_delivery_amount_company)
			series_total.append(temp_dict_qty_company)
			series_total.append(temp_dict_amount_company)
			series_total.append(temp_dict_qty_percent_company)
			series_total.append(temp_dict_amount_percent_company)
			series_total.append(temp_dict_qty_inc_company)
			series_total.append(temp_dict_amount_inc_company)
			datas['holiday_total_sales_chart'] = series_total

		return datas

	# Задаргаа
	
	def get_datas_detailed(self, year, holiday, warehouse_id, product_type, context=None):
		datas = {}
		# Ангилалаар
		where_categ_ids = ""
		if product_type == 'cake':
			cake_categ = self.env['product.category'].search([('code','in',['71','72','75'])])
			c_ids = self.env['product.category'].search([('id','child_of',cake_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "
		elif product_type == 'bakery':
			where_categ_ids = " and "
			bakery_categ = self.env['product.category'].search([('code','=','8')], limit=1)
			c_ids = self.env['product.category'].search([('id','child_of',bakery_categ.id)]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "
		else:
			# all_categ = self.env['product.category'].search([('code','in',['8','7','90','10','11'])])
			all_categ = self.env['product.category'].search([('code','in',['100'])])
			c_ids = self.env['product.category'].search([('id','child_of',all_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "

		warehouse_ids = []
		if holiday and warehouse_id:
			current_date = str(year)
			before_date = str(year-1)
			before_date2 = str(year-2)

			current_date_end = str(year)
			before_date_end = str(year-1)
			before_date2_end = str(year-2)

			# Өдөр олох
			if holiday == 'new_year':
				current_date += '-12-28'
				current_date_end = str(year+1)+'-01-01'
				
				before_date += '-12-28'
				before_date_end = str(year)+'-01-01'

				before_date2 += '-12-28'
				before_date2_end = str(year-1)+'-01-01'
			elif holiday == 'valentine':
				current_date += '-02-14'
				current_date_end += '-02-14'

				before_date += '-02-14'
				before_date_end += '-02-14'

				before_date2 += '-02-14'
				before_date2_end += '-02-14'
			elif holiday == 'mart8':
				current_date += '-03-06'
				current_date_end += '-03-08'

				before_date += '-03-06'
				before_date_end += '-03-08'

				before_date2 += '-03-06'
				before_date2_end += '-03-08'
			elif holiday == 'solder18':
				current_date += '-03-16'
				current_date_end += '-03-18'

				before_date += '-03-16'
				before_date_end += '-03-18'

				before_date2 += '-03-16'
				before_date2_end += '-03-18'
			elif holiday == 'kids':
				current_date += '-05-30'
				current_date_end += '-06-01'

				before_date += '-05-30'
				before_date_end += '-06-01'

				before_date2 += '-05-30'
				before_date2_end += '-06-01'

			# Баярын өдрөөр задлах
			# Борлуулалтын төлөвлөгөө
			categ_names = []
			series = []
			percent_plan_amount_qty = []

			query_plans = """
				SELECT order_date, 
					sum(amount_plan) as amount_plan, 
					sum(qty_plan) as qty_plan
				FROM (
					SELECT  
						smp.date_plan as order_date,
						(CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount_plan,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_plan
							-- smpl.qty * smpl.price_unit as amount_plan,
						-- smpl.qty as qty_plan
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
						   %s
						  smp.is_holiday_plan = 't' and 
						  smp.date_plan >= '%s' and
						  smp.date_plan <= '%s' and 
						  swp.id = %d 
					) as temp
				GROUP BY order_date
				ORDER BY order_date
			"""
			query4 = query_plans % (where_categ_ids, current_date, current_date_end, warehouse_id)
			self.env.cr.execute(query4)
			# print '-------plan-------', query4
			query_result = self.env.cr.dictfetchall()

			temp_data_amount = []
			temp_data_qty = []
			for line in query_result:
				categ_names.append(line['order_date'])
				temp = {
					'name': line['order_date'],
					'y': line['amount_plan'],
				}
				temp_data_amount.append(temp)
				temp = {
					'name': line['order_date'],
					'y': line['qty_plan'],
				}
				temp_data_qty.append(temp)

				percent_plan_amount_qty.append([line['amount_plan'],line['qty_plan']])

			temp_dict_plan_qty = {
		 		'name': 'Тоо хэмжээ',
		 		'color': 'rgba(248,161,63,1)',
		 		'data': temp_data_qty,
		 		'tooltip': {
		 			'valueSuffix': ' ₮'
		 		},
		 		'pointPadding': 0.3,
		 		'pointPlacement': 0,
		 	} 
		 	temp_dict_plan_amount = {
		 		'name': 'Төлөвлөгөө',
		 		'color': 'rgba(186,60,61,.9)',
		 		'data': temp_data_amount,
		 		'tooltip': {
		 			'valueSuffix': ' ш'
		 		},
		 		'pointPadding': 0.4,
		 		'pointPlacement': 0,
		 		'yAxis': 1
		 	}
		 	
			# Борлуулалт
			query_sales_by_day = """
				SELECT order_date, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						so.validity_date as order_date,
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
						(po.date_order + interval '8 hour')::date as order_date,
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
				GROUP BY order_date
				ORDER BY order_date
			"""
			query_by_day = query_sales_by_day % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)
			# print '----by day------', query_by_day
			self.env.cr.execute(query_by_day)
			query_result = self.env.cr.dictfetchall()

			temp_data_amount = []
			temp_data_qty = []
			percent_data_amount = []
			percent_data_qty = []
			for line in query_result:
				temp = {
					'name': line['order_date'],
					'y': line['amount'],
				}
				temp_data_amount.append(temp)
				temp = {
					'name': line['order_date'],
					'y': line['qty'],
				}
				temp_data_qty.append(temp)

				# Percent
				per = 0
				per2 = 0
				if line['order_date'] in categ_names:
					idx = categ_names.index(line['order_date'])
					p_amount = percent_plan_amount_qty[idx][0] or 1
					per = line['amount']*100/p_amount
					# 
					p_qty = percent_plan_amount_qty[idx][1] or 1
					per2 = line['qty']*100/p_qty

				temp = {
					'name': line['order_date'],
					'y': round(per,2),
				}
				percent_data_amount.append(temp)
				# 
				temp = {
					'name': line['order_date'],
					'y': round(per2,2),
				}
				percent_data_qty.append(temp)

				# Categ нэмэх
				if line['order_date'] not in categ_names:
					categ_names.append(line['order_date'])

			temp_dict_qty = {
				'name': 'Тоо хэмжээ',
				'color': 'rgba(165,170,217,1)',
				'data': temp_data_qty,
				'pointPadding': 0.3,
				'pointPlacement': 0.3,
			}
			temp_dict_amount = {
				'name': 'Борлуулалт',
				'yAxis': 1,
				'color': 'rgba(126,86,134,.9)',
				'data': temp_data_amount,
				'pointPadding': 0.4,
				'pointPlacement': 0.3
			}

			# Өмнөх оны борлуулалт
			query_by_day_before = query_sales_by_day % (where_categ_ids, before_date, before_date_end, warehouse_id, where_categ_ids, before_date, before_date_end, warehouse_id)
			self.env.cr.execute(query_by_day_before)
			query_result_before = self.env.cr.dictfetchall()

			temp_data_amount = []
			temp_data_qty = []
			for line in query_result_before:
				temp = {
					'name': line['order_date'],
					'y': line['amount'],
				}
				temp_data_amount.append(temp)
				temp = {
					'name': line['order_date'],
					'y': line['qty'],
				}
				temp_data_qty.append(temp)

			temp_dict_qty_before = {
				'name': 'Өмнөх тоо',
				'color': 'rgba(65,170,217,1)',
				'data': temp_data_qty,
				'pointPadding': 0.3,
				'pointPlacement': -0.3
			}
			temp_dict_amount_before = {
				'name': 'Өмнөх Борлуулалт',
				'yAxis': 1,
				'color': 'rgba(26,86,134,.9)',
				'data': temp_data_amount,
				'pointPadding': 0.4,
				'pointPlacement': -0.3
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

			# Add series
			series.append(temp_dict_qty_before)
			series.append(temp_dict_amount_before)
			# 
			series.append(temp_dict_plan_qty)
			series.append(temp_dict_plan_amount)
			# 
			series.append(temp_dict_qty)
			series.append(temp_dict_amount)
			# 
			series.append(temp_dict_percent)
			series.append(temp_dict_qty_percent)

			datas['holiday_sales_detail_chart'] = series
			datas['holiday_categ_names'] = categ_names
			datas['holiday_warehouse_name'] = self.env['stock.warehouse'].browse(warehouse_id).name

			# Бүтээгдэхүүний ангилалаар өдрөөр задлах
			query_by_categ = """
				SELECT order_date, categ_name, sum(qty_sold) as qty FROM (
					SELECT  
						so.validity_date as order_date,
						pc.name as categ_name,
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
						(po.date_order + interval '8 hour')::date as order_date,
						pc.name as categ_name,
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
				GROUP BY order_date, categ_name
				ORDER BY order_date, categ_name
			"""
			query6 = query_by_categ % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)
			# print '----by categ------', query6
			self.env.cr.execute(query6)
			query_result_by_categ = self.env.cr.dictfetchall()

			# Дата бэлдэх
			series_categ = []
			total_qtys = {}
			temp_qty = []
			temp_dict_sales_qty = {}
			# 
			first = True
			day = ''
			tot = 0
			for line in query_result_by_categ:
				if first:
					temp = {
						'name': line['categ_name'],
						'y': line['qty'],
					}
					tot += line['qty']
					temp_qty.append(temp)
					day = line['order_date']
					first = False

				if day != line['order_date']:
					temp_dict_sales_qty = {
						'type':'column',
						'name': day,
						'data': temp_qty,
					}
					total_qtys[ day ] = tot
					series_categ.append(temp_dict_sales_qty)
					temp_qty = []
					day = line['order_date']
					tot = 0

				temp = {
					'name': line['categ_name'],
					'y': line['qty'],
				}
				temp_qty.append(temp)
				tot += line['qty']

			# Last
			temp_dict_sales_qty = {
				'type':'column',
				'name': day,
				'data': temp_qty,
			}
			total_qtys[ day ] = tot
			series_categ.append(temp_dict_sales_qty)
			datas['holiday_by_categ_chart'] = series_categ

			# PIE эзлэх хувь - Ангилалаар
			series_categ_pie = []
			temp_data = []
			days_name = []
			# Дата бэлдэх
			for lll in series_categ:
				temp_dict = lll
				day = temp_dict['name']
				days_name.append(day)
				tot = total_qtys[ day ]
				for l in temp_dict['data']:
					per = (l['y']*100) /tot
					temp = {
						'name': l['name'],
						'y': per,
						'drilldown': l['name'],
					}
					temp_data.append(temp)

				temp_dict2 = {
					'name': 'Тоо хэмжээ %',
					'colorByPoint': True,
					'data': temp_data,
				}
				series_categ_pie.append(temp_dict2)
				temp_data = []

			datas['holiday_by_categ_pie_chart'] = series_categ_pie
			datas['holiday_day_names'] = days_name

			# Drilldown data
			# Баярын борлуулалт Бүтээгдэхүүнээр задрах
			query_by_categ_product = """
				SELECT order_date, categ_name, p_name, sum(qty_sold) as qty FROM (
					SELECT  
						so.validity_date as order_date,
						pc.name as categ_name,
						pt.name as p_name,
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
						(po.date_order + interval '8 hour')::date as order_date,
						pc.name as categ_name,
						pt.name as p_name,
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
				GROUP BY order_date, categ_name, p_name
				ORDER BY order_date, categ_name, p_name
			"""
			query7 = query_by_categ_product % (where_categ_ids, current_date, current_date_end, warehouse_id, where_categ_ids, current_date, current_date_end, warehouse_id)
			self.env.cr.execute(query7)
			# print '-----categ by product drill---', query7
			query_result_drill = self.env.cr.dictfetchall()

			# VARs
			day_categ_drill_series = []
			series_drilldown = []
			drilldown = {}
			temp_data = []
			# 
			first = True
			day = ''
			categ_name = ''

			for line in query_result_drill:
				if first:
					day = line['order_date']
					categ_name = line['categ_name']
					first = False

				if day != line['order_date']:
					day_categ_drill_series.append(series_drilldown)
					series_drilldown = []
					temp_data = []

				if categ_name != line['categ_name']:
					drilldown = {
						'name': categ_name,
						'id': categ_name,
						'data': temp_data,
					}
					series_drilldown.append(drilldown)
					temp_data = []

				val = (line['p_name'], line['qty'])
				temp_data.append(val)

				day = line['order_date']
				categ_name = line['categ_name']

			series_drilldown.append(drilldown)
			day_categ_drill_series.append(series_drilldown)

			datas['holiday_by_categ_pie_drill_down_chart'] = day_categ_drill_series

		return datas

	# Задаргаа - Шинэ
	
	def get_datas_new_detailed(self, year, holiday, warehouse_id, product_type, context=None):
		datas = {}
		# Ангилалаар
		where_categ_ids = ""
		if product_type == 'cake':
			cake_categ = self.env['product.category'].search([('code','in',['71','72','75'])])
			c_ids = self.env['product.category'].search([('id','child_of',cake_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "
		elif product_type == 'bakery':
			where_categ_ids = " and "
			bakery_categ = self.env['product.category'].search([('code','=','8')], limit=1)
			c_ids = self.env['product.category'].search([('id','child_of',bakery_categ.id)]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "
		else:
			# all_categ = self.env['product.category'].search([('code','in',['8','7','90','10','11'])])
			all_categ = self.env['product.category'].search([('code','in',['100'])])
			c_ids = self.env['product.category'].search([('id','child_of',all_categ.mapped('id'))]).mapped('id')
			where_categ_ids = " pt.categ_id in "+str(tuple(c_ids))+" and "

		warehouse_ids = []
		if holiday and warehouse_id:
			current_date = str(year)
			before_date = str(year-1)
			before_date2 = str(year-2)

			current_date_end = str(year)
			before_date_end = str(year-1)
			before_date2_end = str(year-2)

			# Өдөр олох
			if holiday == 'new_year':
				current_date += '-12-28'
				current_date_end = str(year+1)+'-01-01'
				
				before_date += '-12-28'
				before_date_end = str(year)+'-01-01'

				before_date2 += '-12-28'
				before_date2_end = str(year-1)+'-01-01'
			elif holiday == 'valentine':
				current_date += '-02-14'
				current_date_end += '-02-14'

				before_date += '-02-14'
				before_date_end += '-02-14'

				before_date2 += '-02-14'
				before_date2_end += '-02-14'
			elif holiday == 'mart8':
				current_date += '-03-06'
				current_date_end += '-03-08'

				before_date += '-03-06'
				before_date_end += '-03-08'

				before_date2 += '-03-06'
				before_date2_end += '-03-08'
			elif holiday == 'solder18':
				current_date += '-03-16'
				current_date_end += '-03-18'

				before_date += '-03-16'
				before_date_end += '-03-18'

				before_date2 += '-03-16'
				before_date2_end += '-03-18'
			elif holiday == 'kids':
				current_date += '-05-30'
				current_date_end += '-06-01'

				before_date += '-05-30'
				before_date_end += '-06-01'

				before_date2 += '-05-30'
				before_date2_end += '-06-01'

			# Баярын өдрөөр задлах =========================================
			# Борлуулалтын төлөвлөгөө
			series = []
			series_qty = []
			# QUERY's
			query_plans = """
				SELECT order_date, p_type,
					sum(amount_plan) as amount, 
					sum(qty_plan) as qty
				FROM (
					SELECT  
						smp.date_plan as order_date,
						(CASE WHEN pc.code = '72' THEN 'brand'
						      WHEN pc.code = '71' THEN 'happy' ELSE 'bakery' END) as p_type, 
					    (CASE WHEN smpl.fixed_amount > 0 THEN smpl.fixed_amount ELSE smpl.amount END) as amount_plan,
						(CASE WHEN smpl.fixed_qty > 0 THEN smpl.fixed_qty ELSE smpl.qty END) as qty_plan
						-- smpl.qty * smpl.price_unit as amount_plan,
						-- smpl.qty as qty_plan
					FROM sales_master_plan_line as smpl
					LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
					LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
					LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
					WHERE smp.state != 'draft' and 
						   %s
						  smp.is_holiday_plan = 't' and 
						  smp.date_plan >= '%s' and
						  smp.date_plan <= '%s' and 
						  swp.id = %d 
					) as temp
				GROUP BY order_date, p_type
				ORDER BY order_date, p_type
			"""
			query4 = query_plans % (where_categ_ids, current_date, current_date_end, warehouse_id)
			self.env.cr.execute(query4)
			# print '-------plan-------', query4
			query_result = self.env.cr.dictfetchall()
			series_happy = []
			series_brand = []
			series_bakery = []
			main_series = []
			# 
			series_happy_qty = []
			series_brand_qty = []
			series_bakery_qty = []
			main_series_qty = []
			for line in query_result:
				if line['p_type'] == 'happy':
					temp = {
						'name': line['order_date'],
						'y': line['amount'],
					}
					series_happy.append(temp)
					# 
					temp = {
						'name': line['order_date'],
						'y': line['qty'],
					}
					series_happy_qty.append(temp)
				elif line['p_type'] == 'brand':
					temp = {
						'name': line['order_date'],
						'y': line['amount'],
					}
					series_brand.append(temp)
					# 
					temp = {
						'name': line['order_date'],
						'y': line['qty'],
					}
					series_brand_qty.append(temp)
				else:
					temp = {
						'name': line['order_date'],
						'y': line['amount'],
					}
					series_bakery.append(temp)
					# 
					temp = {
						'name': line['order_date'],
						'y': line['qty'],
					}
					series_bakery_qty.append(temp)

			temp_dict_brand_plan = {
				'type':'column',
				'name': u'Брэнд/plan/',
				'data': series_brand,
			}
			temp_dict_happy_plan = {
				'type':'column',
				'name': u'Аз жаргал/plan/',
				'data': series_happy,
			}
			temp_dict_bakery_plan = {
				'type':'column',
				'name': u'Бусад/plan/',
				'data': series_bakery,
			}
			# 
			temp_dict_brand_plan_qty = {
				'type':'column',
				'name': u'Брэнд/plan/',
				'data': series_brand_qty,
			}
			temp_dict_happy_plan_qty = {
				'type':'column',
				'name': u'Аз жаргал/plan/',
				'data': series_happy_qty,
			}
			temp_dict_bakery_plan_qty = {
				'type':'column',
				'name': u'Бусад/plan/',
				'data': series_bakery_qty,
			}
			# ------------
			# Борлуулалт
			query_sales_size = """
				SELECT order_date, p_type, size, 
					sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						so.validity_date as order_date,
						(CASE WHEN pc.code = '72' THEN 'brand'
						      WHEN pc.code = '71' THEN 'happy' ELSE 'bakery' END) as p_type, 
					    (CASE WHEN pc.code = '72' THEN ptt.name 
						      WHEN pc.code = '71' THEN pts.name ELSE pc.name END) as size, 
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
						  and so.validity_date <= '%s' and 
  						   %s
						  swp.id = %d 
					UNION ALL
					SELECT 
						(po.date_order + interval '8 hour')::date as order_date,
						(CASE WHEN pc.code = '72' THEN 'brand'
						      WHEN pc.code = '71' THEN 'happy' ELSE 'bakery' END) as p_type, 
					    (CASE WHEN pc.code = '72' THEN ptt.name 
						      WHEN pc.code = '71' THEN pts.name ELSE pc.name END) as size, 
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
						   %s 
						   swp.id = %d 
					) as temp
				GROUP BY order_date, p_type, size
				ORDER BY order_date, p_type, size  
			""" 
			# Энэ оны борлуулалт
			query_sales_size_now = query_sales_size % (current_date, current_date_end, where_categ_ids, warehouse_id, current_date, current_date_end, where_categ_ids, warehouse_id)
			self.env.cr.execute(query_sales_size_now)
			query_result_so = self.env.cr.dictfetchall()
			temp_dict = {}
			temp_drill_dict = {}
			# 
			temp_dict_qty = {}
			temp_drill_dict_qty = {}
			for line in query_result_so:
				if line['order_date'] in temp_dict:
					t_amount = 0
					if line['p_type'] in temp_dict[line['order_date']]:
						t_amount = temp_dict[line['order_date']][line['p_type']]
					temp_dict[line['order_date']][line['p_type']] = t_amount+line['amount']
					# 
					t_qty = 0
					if line['p_type'] in temp_dict_qty[line['order_date']]:
						t_qty = temp_dict_qty[line['order_date']][line['p_type']]
					temp_dict_qty[line['order_date']][line['p_type']] = t_qty+line['qty']
				else:
					tt = {line['p_type']:line['amount']}
					temp_dict[line['order_date']] = tt
					# 
					tt = {line['p_type']:line['qty']}
					temp_dict_qty[line['order_date']] = tt

				# Drill бэлдэх
				val = (line['size'], line['amount'])
				val_qty = (line['size'], line['qty'])
				if line['order_date'] in temp_drill_dict:
					t_list = [val]
					t_list_qty = [val_qty]
					if line['p_type'] in temp_drill_dict[line['order_date']]:
						t_list = temp_drill_dict[line['order_date']][line['p_type']]
						t_list.append(val)
						# 
						t_list_qty = temp_drill_dict_qty[line['order_date']][line['p_type']]
						t_list_qty.append(val_qty)
					temp_drill_dict[line['order_date']][line['p_type']] = t_list
					# 
					temp_drill_dict_qty[line['order_date']][line['p_type']] = t_list_qty
				else:
					t_list = [val]
					tt = {line['p_type']:t_list}
					temp_drill_dict[line['order_date']] = tt
					# 
					t_list = [val_qty]
					tt = {line['p_type']:t_list}
					temp_drill_dict_qty[line['order_date']] = tt

			# Generate series
			series_happy = []
			series_brand = []
			series_bakery = []
			# 
			series_happy_qty = []
			series_brand_qty = []
			series_bakery_qty = []
			for day in temp_dict:
				for p_type in temp_dict[day]:
					if p_type == 'happy':
						temp = {
							'name': day,
							'drilldown': day+'_happy',
							'y': temp_dict[day][p_type],
						}
						series_happy.append(temp)
						# 
						temp = {
							'name': day,
							'drilldown': day+'_happy',
							'y': temp_dict_qty[day][p_type],
						}
						series_happy_qty.append(temp)
					elif p_type == 'brand':
						temp = {
							'name': day,
							'drilldown': day+'_brand',
							'y': temp_dict[day][p_type],
						}
						series_brand.append(temp)
						# 
						temp = {
							'name': day,
							'drilldown': day+'_brand',
							'y': temp_dict_qty[day][p_type],
						}
						series_brand_qty.append(temp)
					else:
						temp = {
							'name': day,
							'drilldown': day+'_bakery',
							'y': temp_dict[day][p_type],
						}
						series_bakery.append(temp)
						# 
						temp = {
							'name': day,
							'drilldown': day+'_bakery',
							'y': temp_dict_qty[day][p_type],
						}
						series_bakery_qty.append(temp)
			# Add columns - NOW
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
			temp_dict_bakery = {
				'type':'column',
				'name': u'Бусад',
				'data': series_bakery,
			}
			# 
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
			temp_dict_bakery_qty = {
				'type':'column',
				'name': u'Бусад',
				'data': series_bakery_qty,
			}
			# Generate Drilldown
			type_name = {
				'happy': u'Аз жаргал',
				'brand': u'Брэнд',
				'bakery': u'Бусад',
			}
			series_drilldown = []
			series_drilldown_qty = []
			for day in temp_drill_dict:
				for p_type in temp_drill_dict[day]:
					temp_dict = {
						'name': type_name[p_type],
						# 'type':'column',
						'id': day+'_'+p_type,
						'data': temp_drill_dict[day][p_type],
					}
					series_drilldown.append(temp_dict)
					# 
					temp_dict = {
						'name': type_name[p_type],
						# 'type':'column',
						'id': day+'_'+p_type,
						'data': temp_drill_dict_qty[day][p_type],
					}
					series_drilldown_qty.append(temp_dict)

			# Өмнөх оны борлуулалт --------------------------------------------------
			query_sales_size_before = query_sales_size % (before_date, before_date_end, where_categ_ids, warehouse_id, before_date, before_date_end, where_categ_ids, warehouse_id)
			self.env.cr.execute(query_sales_size_before)
			query_result_before = self.env.cr.dictfetchall()
			temp_dict_before = {}
			temp_drill_dict_before = {}
			# 
			temp_dict_qty_before = {}
			temp_drill_dict_qty_before = {}
			for line in query_result_before:
				if line['order_date'] in temp_dict_before:
					t_amount = 0
					if line['p_type'] in temp_dict_before[line['order_date']]:
						t_amount = temp_dict_before[line['order_date']][line['p_type']]
					temp_dict_before[line['order_date']][line['p_type']] = t_amount+line['amount']
					# 
					t_qty = 0
					if line['p_type'] in temp_dict_qty_before[line['order_date']]:
						t_qty = temp_dict_qty_before[line['order_date']][line['p_type']]
					temp_dict_qty_before[line['order_date']][line['p_type']] = t_qty+line['qty']
				else:
					tt = {line['p_type']:line['amount']}
					temp_dict_before[line['order_date']] = tt
					# 
					tt = {line['p_type']:line['qty']}
					temp_dict_qty_before[line['order_date']] = tt

				# Drill бэлдэх
				val = (line['size'], line['amount'])
				val_qty = (line['size'], line['qty'])
				if line['order_date'] in temp_drill_dict_before:
					t_list = [val]
					t_list_qty = [val_qty]
					if line['p_type'] in temp_drill_dict_before[line['order_date']]:
						t_list = temp_drill_dict_before[line['order_date']][line['p_type']]
						t_list.append(val)
						# 
						t_list_qty = temp_drill_dict_qty_before[line['order_date']][line['p_type']]
						t_list_qty.append(val_qty)
					temp_drill_dict_before[line['order_date']][line['p_type']] = t_list
					# 
					temp_drill_dict_qty_before[line['order_date']][line['p_type']] = t_list_qty
				else:
					t_list = [val]
					tt = {line['p_type']:t_list}
					temp_drill_dict_before[line['order_date']] = tt
					# 
					t_list = [val_qty]
					tt = {line['p_type']:t_list}
					temp_drill_dict_qty_before[line['order_date']] = tt

			# Generate series
			series_happy_before = []
			series_brand_before = []
			series_bakery_before = []
			# 
			series_happy_qty_before = []
			series_brand_qty_before = []
			series_bakery_qty_before = []
			for day in temp_dict_before:
				dddd = str(int(day[0:4])+1)+day[4:]
				for p_type in temp_dict_before[day]:
					if p_type == 'happy':
						temp = {
							'name': dddd,
							'drilldown': dddd+'_happy_before',
							'y': temp_dict_before[day][p_type],
						}
						series_happy_before.append(temp)
						# 
						temp = {
							'name': dddd,
							'drilldown': dddd+'_happy_before',
							'y': temp_dict_qty_before[day][p_type],
						}
						series_happy_qty_before.append(temp)
					elif p_type == 'brand':
						temp = {
							'name': dddd,
							'drilldown': dddd+'_brand_before',
							'y': temp_dict_before[day][p_type],
						}
						series_brand_before.append(temp)
						# 
						temp = {
							'name': dddd,
							'drilldown': dddd+'_brand_before',
							'y': temp_dict_qty_before[day][p_type],
						}
						series_brand_qty_before.append(temp)
					else:
						temp = {
							'name': dddd,
							'drilldown': dddd+'_bakery_before',
							'y': temp_dict_before[day][p_type],
						}
						series_bakery_before.append(temp)
						# 
						temp = {
							'name': dddd,
							'drilldown': dddd+'_bakery_before',
							'y': temp_dict_qty_before[day][p_type],
						}
						series_bakery_qty_before.append(temp)
			# Add columns - Before
			temp_dict_brand_before = {
				'type':'column',
				'name': u'Брэнд өмнөх',
				'data': series_brand_before,
			}
			temp_dict_happy_before = {
				'type':'column',
				'name': u'Аз жаргал өмнөх',
				'data': series_happy_before,
			}
			temp_dict_bakery_before = {
				'type':'column',
				'name': u'Бусад өмнөх',
				'data': series_bakery_before,
			}
			# 
			temp_dict_brand_qty_before = {
				'type':'column',
				'name': u'Брэнд өмнөх',
				'data': series_brand_qty_before,
			}
			temp_dict_happy_qty_before = {
				'type':'column',
				'name': u'Аз жаргал өмнөх',
				'data': series_happy_qty_before,
			}
			temp_dict_bakery_qty_before = {
				'type':'column',
				'name': u'Бусад өмнөх',
				'data': series_bakery_qty_before,
			}
			# Generate Drilldown
			for day in temp_drill_dict_before:
				dddd = str(int(day[0:4])+1)+day[4:]
				for p_type in temp_drill_dict_before[day]:
					temp_dict_before = {
						'name': type_name[p_type]+u' өмнөх',
						'id': dddd+'_'+p_type+'_before',
						'data': temp_drill_dict_before[day][p_type],
					}
					series_drilldown.append(temp_dict_before)
					# 
					temp_dict_before = {
						'name': type_name[p_type]+u' өмнөх',
						'id': dddd+'_'+p_type+'_before',
						'data': temp_drill_dict_qty_before[day][p_type],
					}
					series_drilldown_qty.append(temp_dict_before)
			# Add series
			main_series.append(temp_dict_brand_before)
			main_series.append(temp_dict_brand_plan)
			main_series.append(temp_dict_brand)
			main_series.append(temp_dict_happy_before)
			main_series.append(temp_dict_happy_plan)
			main_series.append(temp_dict_happy)
			main_series.append(temp_dict_bakery_before)
			main_series.append(temp_dict_bakery_plan)
			main_series.append(temp_dict_bakery)
			# 
			main_series_qty.append(temp_dict_brand_qty_before)
			main_series_qty.append(temp_dict_brand_plan_qty)
			main_series_qty.append(temp_dict_brand_qty)
			main_series_qty.append(temp_dict_happy_qty_before)
			main_series_qty.append(temp_dict_happy_plan_qty)
			main_series_qty.append(temp_dict_happy_qty)
			main_series_qty.append(temp_dict_bakery_qty_before)
			main_series_qty.append(temp_dict_bakery_plan_qty)
			main_series_qty.append(temp_dict_bakery_qty)
			# 
			datas['holiday_new_detail_chart'] = main_series
			datas['holiday_new_detail_drilldown_chart'] = {'series':series_drilldown}
			# 
			datas['holiday_new_detail_qty_chart'] = main_series_qty
			datas['holiday_new_detail_qty_drilldown_chart'] = {'series':series_drilldown_qty}
			# Нийлүүлсэн тоо
			# query_delivered = """
			# 	SELECT  
			# 		sum(sm.product_uom_qty) as qty_delivered,
			# 		sum(sm.product_uom_qty*pt.list_price) as amount_delivered
			# 	FROM stock_move as sm
			# 	LEFT JOIN product_product as pp on (pp.id = sm.product_id)
			# 	LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
			# 	LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = sm.location_dest_id)
			# 	LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
			# 	WHERE sm.state = 'done' and 
			# 		   %s
			# 		  (sm.date_expected + interval '8 hour')::date >= '%s' and
			# 		  (sm.date_expected + interval '8 hour')::date <= '%s' and
			# 		   swp.id = %d 
			# """ % (where_categ_ids, current_date, current_date_end, warehouse_id)
			# print '-----delivered-', query_delivered

		return datas
		
		
