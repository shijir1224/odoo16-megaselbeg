# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError

class SalesPlanDashboard01(models.TransientModel):
	_name = 'sales.plan.dashboard.01'
	_description = 'Plan and performance dashboard'

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
			(1, u'January'), 
			(2, u'February'), 
			(3, u'March'), 
			(4, u'April'), 
			(5, u'May'), 
			(6, u'June'), 
			(7, u'July'), 
			(8, u'August'), 
			(9, u'September'), 
			(10, u'October'), 
			(11, u'November'), 
			(12, u'December'), 
			(13, u'1-р улирал'),
			(14, u'2-р улирал'),
			(15, u'3-р улирал'),
			(16, u'4-р улирал'),
			(17, u'First half'), 
			(18, u'Second half'), 
			(19, u'By year'), 
		], default=_get_month, required=True, string=u'Month')

	categ_id = fields.Many2one('product.category', string=u'Category',)

	
	def get_datas(self, year, month, categ_id, context=None):
		
		where_user_wh = ''

		datas = {}
		current_date = str(year)
		before_date = str(year-1)
		before_date2 = str(year-2)

		current_date_end = str(year)
		before_date_end = str(year-1)
		before_date2_end = str(year-2)
		months = ""

		# Month
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
		# Period
		elif month == 13:
			current_date += '-01-01'
			current_date_end += '-03-31'

			before_date += '-01-01'
			before_date_end += '-03-31'

			before_date2 += '-01-01'
			before_date2_end += '-03-31'

			months = "1,2,3"
		elif month == 14:
			current_date += '-04-01'
			current_date_end += '-06-30'

			before_date += '-04-01'
			before_date_end += '-06-30'

			before_date2 += '-04-01'
			before_date2_end += '-06-30'

			months = "4,5,6"
		elif month == 15:
			current_date += '-07-01'
			current_date_end += '-09-30'

			before_date += '-07-01'
			before_date_end += '-09-30'

			before_date2 += '-07-01'
			before_date2_end += '-09-30'

			months = "7,8,9"
		elif month == 16:
			current_date += '-10-01'
			current_date_end += '-12-31'

			before_date += '-10-01'
			before_date_end += '-12-31'

			before_date2 += '-10-01'
			before_date2_end += '-12-31'

			months = "10,11,12"
		elif month == 17:
			current_date += '-01-01'
			current_date_end += '-06-30'

			before_date += '-01-01'
			before_date_end += '-06-30'

			before_date2 += '-01-01'
			before_date2_end += '-06-30'

			months = "1,2,3,4,5,6"
		elif month == 18:
			current_date += '-07-01'
			current_date_end += '-12-31'

			before_date += '-07-01'
			before_date_end += '-12-31'

			before_date2 += '-07-01'
			before_date2_end += '-12-31'

			months = "7,8,9,10,11,12"
		elif month == 19:
			current_date += '-01-01'
			current_date_end += '-12-31'

			before_date += '-01-01'
			before_date_end += '-12-31'

			before_date2 += '-01-01'
			before_date2_end += '-12-31'

			months = "1,2,3,4,5,6,7,8,9,10,11,12"

		# Get category
		where_categ_ids = ""
		if categ_id:
			c_ids = self.env['product.category'].search([('id','child_of',categ_id)]).mapped('id')
			if len(c_ids) > 1:
				c_ids = str(tuple(c_ids))
			elif len(c_ids) == 1:
				c_ids = '('+str(c_ids[0])+')'
			where_categ_ids = " pt.categ_id in "+c_ids+" and "
		else:
			where_categ_ids = " "

		series = []
		series_qty = []

		# This year sales
		query1 =""
		query_sales = ""
		query_sales_period = ""
		if month < 13:
			query_sales = """
				SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						sw.name as warehouse_name,
						sol.price_unit * (sol.qty_delivered) as amount,
						(sol.qty_delivered) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
							%s 
						  so.date_order::text ilike '%s' 
						    %s
					UNION ALL
					SELECT 
						sw.name as warehouse_name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN pos_session ps ON (po.session_id=ps.id)
                    LEFT JOIN pos_config pconf ON (ps.config_id=pconf.id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = pconf.stock_location_id)
					WHERE po.state in ('paid','done','invoiced') and   
						   %s 
						  (po.date_order + interval '8 hour')::date::text ilike '%s'
						   %s
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name
			"""
			query1 = query_sales % (where_categ_ids, current_date, where_user_wh, where_categ_ids, current_date, where_user_wh)
		else:
			query_sales_period = """
				SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
					SELECT  
						sw.name as warehouse_name,
						sol.price_unit * (sol.qty_delivered) as amount,
						(sol.qty_delivered) as qty_sold
					FROM sale_order_line as sol
					LEFT JOIN sale_order as so on (so.id = sol.order_id)
					LEFT JOIN product_product as pp on (pp.id = sol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN stock_warehouse as sw on (sw.id = so.warehouse_id)
					WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
						   %s
						  so.date_order >= '%s' and 
						  so.date_order <= '%s'  
						   %s
					UNION ALL
					SELECT 
						sw.name as warehouse_name,
						pol.price_unit * pol.qty as amount,
						pol.qty as qty_sold
					FROM pos_order_line as pol
					LEFT JOIN pos_order as po on (po.id = pol.order_id)
					LEFT JOIN product_product as pp on (pp.id = pol.product_id)
					LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN pos_session ps ON (po.session_id=ps.id)
                    LEFT JOIN pos_config pconf ON (ps.config_id=pconf.id)
					LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = pconf.stock_location_id)
					WHERE po.state in ('paid','done','invoiced') and   
						   %s 
						  (po.date_order + interval '8 hour')::date >= '%s' and
						  (po.date_order + interval '8 hour')::date <= '%s'  
						   %s
					) as temp
				GROUP BY warehouse_name
				ORDER BY warehouse_name
			"""
			query1 = query_sales_period % (where_categ_ids, current_date, current_date_end, where_user_wh, where_categ_ids, current_date, current_date_end, where_user_wh)

		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		# print '---------------', query1

		# VARs
		amount_performance_percent = {}
		qty_performance_percent = {}
		total_sale_amount = 0
		total_sale_qty = 0
		temp_amount = []
		temp_qty = []
		# Салбар буюу тасгийн нэрс
		for line in query_result:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_amount.append(temp)
			amount_performance_percent[ line['warehouse_name'] ] = line['amount']
			total_sale_amount += line['amount']
			
			temp = {
				'name': line['warehouse_name'],
				'y': line['qty'],
			}
			temp_qty.append(temp)
			qty_performance_percent[ line['warehouse_name'] ] = line['qty']
			total_sale_qty += line['qty']

		temp_dict_sales = {
			'type':'column',
			'name': 'Sales',
			'data': temp_amount,
		}
		temp_dict_sales_qty = {
			'type':'column',
			'name': 'Sales',
			'data': temp_qty,
		}

		# Өмнөх оны борлуулалт
		query2 = ""
		if month < 13:
			query2 = query_sales % (where_categ_ids, before_date, where_user_wh, where_categ_ids, before_date, where_user_wh)
		else:
			query2 = query_sales_period % (where_categ_ids, before_date, before_date_end, where_user_wh, where_categ_ids, before_date, before_date_end, where_user_wh)

		# print '----ddd------', query2
		self.env.cr.execute(query2)
		query_result = self.env.cr.dictfetchall()
		temp_amount = []
		temp_qty = []

		company_total_amount_before = 0
		company_total_qty_before = 0

		idx = 0
		for line in query_result:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_amount.append(temp)
			temp = {
				'name': line['warehouse_name'],
				'y': line['qty'],
			}
			temp_qty.append(temp)

			company_total_amount_before += line['amount']
			company_total_qty_before += line['qty']

		temp_dict_before1 = {
			'type':'column',
			'name': 'Last year',
			'data': temp_amount,
		}
		temp_dict_before1_qty = {
			'type':'column',
			'name': 'Last year',
			'data': temp_qty,
		}

		# Өсөлт amount, qty
		percent_inc_data = []
		percent_inc_data_qty = []

		for i in range(0, len(temp_dict_sales['data'])):
			temp1 = temp_dict_sales['data'][i]
			temp1_qty = temp_dict_sales_qty['data'][i]
			wh_name = temp1['name']
			for j in range(0, len(temp_dict_before1['data'])):
				if wh_name == temp_dict_before1['data'][j]['name']:
					# amount
					diff = 0
					plug = 1
					bf = temp_dict_before1['data'][j]['y']
					if bf > temp1['y']:
						diff = bf - temp1['y']
						plug = -1
					else:
						diff = temp1['y'] - bf
					# QTY
					diff_qty = 0
					plug_qty = 1
					bf_qty = temp_dict_before1_qty['data'][j]['y']
					if bf_qty > temp1_qty['y']:
						diff_qty = bf_qty - temp1_qty['y']
						plug_qty = -1
					else:
						diff_qty = temp1_qty['y'] - bf_qty
					# ---
					if bf != 0:
						per = round((diff*100)/bf,2) * plug
						percent_inc_data.append({'name':wh_name, 'y':per})
					# QTY
					if bf_qty != 0:
						per_qty = round((diff_qty*100)/bf_qty,2) * plug_qty
						percent_inc_data_qty.append({'name':wh_name, 'y':per_qty})

		# Өмнөхийн өмнөх оны борлуулалт
		query3 = ""
		if month < 13:
			query3 = query_sales % (where_categ_ids, before_date2, where_user_wh, where_categ_ids, before_date2, where_user_wh)
		else:
			query3 = query_sales_period % (where_categ_ids, before_date2, before_date2_end, where_user_wh, where_categ_ids, before_date2, before_date2_end, where_user_wh)
		self.env.cr.execute(query3)
		query_result = self.env.cr.dictfetchall()
		temp_amount = []
		temp_qty = []
		idx = 0
		for line in query_result:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_amount.append(temp)
			temp = {
				'name': line['warehouse_name'],
				'y': line['qty'],
			}
			temp_qty.append(temp)

		temp_dict_before2 = {
			'type':'column',
			'name': 'Last year2',
			'data': temp_amount,
		}
		temp_dict_before2_qty = {
			'type':'column',
			'name': 'Last year2',
			'data': temp_qty,
		}

		# Master plan
		query_plans = """
			SELECT warehouse_name, sum(amount) as amount, sum(qty_sold) as qty FROM (
				SELECT  
					sw.name as warehouse_name,
					smpl.amount as amount,
					smpl.qty as qty_sold
				FROM sales_master_plan_line as smpl
				LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
				LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
				LEFT JOIN stock_warehouse as sw on (sw.id = smp.warehouse_id)
				WHERE smp.state != 'draft' and 
				       %s
					  smp.year = %d and
					  smp.month in (%s) 
					   %s
				) as temp
			GROUP BY warehouse_name
			ORDER BY warehouse_name
		"""
		query4 = query_plans % (where_categ_ids, year, months, where_user_wh)
		print '===============PLAN======-------------', query4
		self.env.cr.execute(query4)
		query_result = self.env.cr.dictfetchall()
		temp_amount = []
		temp_qty = []
		percent_data = []
		percent_data_qty = []

		company_total_amount_plan = 0
		company_total_qty_plan = 0

		idx = 0
		for line in query_result:
			temp = {
				'name': line['warehouse_name'],
				'y': line['amount'],
			}
			temp_amount.append(temp)
			temp = {
				'name': line['warehouse_name'],
				'y': line['qty'],
			}
			temp_qty.append(temp)

			if line['warehouse_name'] in amount_performance_percent:
				s_amount = amount_performance_percent[ line['warehouse_name'] ]
				s_qty = qty_performance_percent[ line['warehouse_name'] ]
				per = round(s_amount/line['amount'],2)*100
				percent_data.append({'name':line['warehouse_name'],'y':per})
				per_qty = round(s_qty/line['qty'],2)*100
				percent_data_qty.append({'name':line['warehouse_name'],'y':per_qty})

			company_total_amount_plan += line['amount']
			company_total_qty_plan += line['qty']

		temp_dict_plan = {
			'type':'column',
			'name': 'Plan',
			'data': temp_amount,
		}
		temp_dict_plan_qty = {
			'type':'column',
			'name': 'Plan',
			'data': temp_qty,
		}

		# Гүйцэтгэл line нэмэх
		temp_dict_percent = {
			'type':'spline',
			'yAxis': 1,
			'name': 'Performance %',
			'data': percent_data,
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
		temp_dict_percent_qty = {
			'type':'spline',
			'yAxis': 1,
			'name': 'Performance %',
			'data': percent_data_qty,
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
		# Өсөлтийн хувь нэмэх
		temp_dict_inc_percent = {
			'type':'spline',
			'yAxis': 1,
			'name': 'Increase %',
			'data': percent_inc_data,
			'marker': {
				'lineWidth': 3,
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'right',
				'format': '{point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		temp_dict_inc_percent_qty = {
			'type':'spline',
			'yAxis': 1,
			'name': 'Increase %',
			'data': percent_inc_data_qty,
			'marker': {
				'lineWidth': 3,
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'left',
				'format': '{point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}

		# Company niit
		total_data = []
		for key in amount_performance_percent:
			val = amount_performance_percent[key]
			tt = {
				'name': key,
				'y': val,
			}
			total_data.append(tt)

		temp_dict3 = {
			'name': 'Amount %',
			'colorByPoint': True,
			'data': total_data,
		}
		
		# QTY
		total_data_qty = []
		for key in qty_performance_percent:
			val = qty_performance_percent[key]
			tt = {
				'name': key,
				'y': val,
			}
			total_data_qty.append(tt)

		temp_dict3_qty = {
			'name': 'Quantity %',
			'colorByPoint': True,
			'data': total_data_qty,
		}
		# 
		pie_series = [temp_dict3]
		pie_series_qty = [temp_dict3_qty]

		# Data add
		series.append(temp_dict_before2)
		series.append(temp_dict_before1)
		series.append(temp_dict_plan)
		series.append(temp_dict_sales)
		series.append(temp_dict_percent)
		series.append(temp_dict_inc_percent)
		# QTY
		series_qty.append(temp_dict_before2_qty)
		series_qty.append(temp_dict_before1_qty)
		series_qty.append(temp_dict_plan_qty)
		series_qty.append(temp_dict_sales_qty)
		series_qty.append(temp_dict_percent_qty)
		series_qty.append(temp_dict_inc_percent_qty)

		datas['amount_performance_chart'] = series
		datas['company_total_pie_chart'] = pie_series
		datas['company_total_sale'] = round(total_sale_amount, 1)
		# QTY
		datas['qty_performance_chart'] = series_qty
		datas['company_total_qty_pie_chart'] = pie_series_qty
		datas['company_total_sale_qty'] = round(total_sale_qty, 1)

		# Company total
		series_total = []
	 	# Last year
	 	temp_dict_qty_before = {
			'name': 'Last year Qty',
			'color': 'rgba(65,170,217,1)',
			'data': [{'name':u'Company total', 'y': company_total_qty_before }],
			'tooltip': {
	 			'valueSuffix': ' Qty'
	 		},
			'pointPadding': 0.4,
			'pointPlacement': -0.3,
		}
		temp_dict_amount_before = {
			'name': 'Last year',
			'yAxis': 1,
			'color': 'rgba(26,86,134,.9)',
			'data': [{'name':u'Company total', 'y': company_total_amount_before }],
			'tooltip': {
	 			'valueSuffix': ' $'
	 		},
			'pointPadding': 0.45,
			'pointPlacement': -0.3,
		}
		# Plan
		temp_dict_plan_qty = {
	 		'name': 'Plan Qty',
	 		'color': 'rgba(248,161,63,1)',
	 		'data': [{'name':u'Company total', 'y': company_total_qty_plan }],
	 		'tooltip': {
	 			'valueSuffix': ' Qty'
	 		},
	 		'pointPadding': 0.4,
	 		'pointPlacement': 0,
	 	} 
	 	temp_dict_plan_amount = {
	 		'name': 'Plan',
	 		'color': 'rgba(186,60,61,.9)',
	 		'data': [{'name':u'Company total', 'y': company_total_amount_plan }],
	 		'tooltip': {
	 			'valueSuffix': ' $'
	 		},
	 		'pointPadding': 0.45,
	 		'pointPlacement': 0,
	 		'yAxis': 1
	 	}
		# This year
		temp_dict_qty = {
			'name': 'Sales Qty',
			'color': 'rgba(165,170,217,1)',
			'data': [{'name':u'Company total', 'y':  total_sale_qty}],
			'tooltip': {
	 			'valueSuffix': ' Qty',
	 			'colorByPoint': True,
	 		},
			'pointPadding': 0.4,
			'pointPlacement': 0.3,
		}
		temp_dict_amount = {
			'name': 'Sales',
			'yAxis': 1,
			'color': 'rgba(126,86,134,.9)',
			'data': [{'name':u'Company total', 'y': total_sale_amount }],
			'tooltip': {
	 			'valueSuffix': ' $',
	 			'colorByPoint': True,
	 		},
			'pointPadding': 0.45,
			'pointPlacement': 0.3,
		}

		# Perfoenamc %
		per = 0
		if company_total_qty_plan != 0:
			per = round((total_sale_qty*100)/company_total_qty_plan,2)
		temp_dict_qty_percent = {
			'name': 'Performance Qty %',
			'type':'spline',
			'yAxis': 2,
			'color': 'rgba(30,242,69,1)',
			'data': [{'name':u'Company total', 'y': per }],
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'pointPlacement': 0.17,
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Performance Qty {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		per = 0
		if company_total_amount_plan != 0:
			per = round((total_sale_amount*100)/company_total_amount_plan,2)
			
		temp_dict_amount_percent = {
			'name': 'Performance Amount %',
			'type':'spline',
			'yAxis': 2,
			'color': 'rgba(28,164,6,.9)',
			'data': [{'name':u'Company total', 'y': per }],
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'pointPlacement': 0.17,
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Performance amnt {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}

		# Increase %
		diff = 0
		plug = 1
		per = 0
		if company_total_qty_before > total_sale_qty:
			diff = company_total_qty_before - total_sale_qty
			plug = -1
		else:
			diff = total_sale_qty - company_total_qty_before
		if company_total_qty_before != 0:
			per = round((diff*100)/company_total_qty_before,2) * plug
		else:
			per = 100
		temp_dict_qty_inc_percent = {
			'name': 'Increase Qty %',
			'type':'spline',
			'yAxis': 2,
			'color': 'rgba(30,212,69,1)',
			'data': [{'name':u'Company total', 'y': per }],
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'pointPlacement': -0.17,
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Increase Qty {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		# Amount
		diff = 0
		plug = 1
		if company_total_amount_before > total_sale_amount:
			diff = company_total_amount_before - total_sale_amount
			plug = -1
		else:
			diff = total_sale_amount - company_total_amount_before
		if company_total_amount_before != 0:
			per = round((diff*100)/company_total_amount_before,2) * plug
		else:
			per = 100
		temp_dict_amount_inc_percent = {
			'name': 'Increase Amount %',
			'type':'spline',
			'yAxis': 2,
			'color': 'rgba(30,212,69,1)',
			'data': [{'name':u'Company total', 'y': per }],
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'pointPlacement': -0.17,
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Increase amnt {point.y:.1f}%',
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

		datas['company_total_chart'] = series_total

		# Компаний 12 сарын DONUT chart
		# ЖИлийн Мастер төлөвлөгөө
		query_plans = """
			SELECT year, mm, sum(amount) as amount, sum(qty_sold) as qty FROM (
				SELECT  
					smp.year as year,
					smp.month as mm,
					smpl.amount as amount,
					smpl.qty as qty_sold
				FROM sales_master_plan_line as smpl
				LEFT JOIN sales_master_plan as smp on (smp.id = smpl.parent_id)
				LEFT JOIN product_product as pp on (pp.id = smpl.product_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN product_category as pc on (pc.id = pt.categ_id)
				WHERE smp.state != 'draft' and 
				       %s
					   smp.year = %d 
					   %s 
				) as temp
			GROUP BY year, mm
			ORDER BY year, mm
		"""
		query4 = query_plans % (where_categ_ids, year, where_user_wh)
		self.env.cr.execute(query4)
		query_result_plan = self.env.cr.dictfetchall()
		year_total_amount_plan = 0
		year_total_qty_plan = 0
		series_amount_monthly_plan = []
		series_qty_monthly_plan = []
		for line in query_result_plan:
			year_total_amount_plan += line['amount']
			year_total_qty_plan += line['qty']
			# Компаны сар сар
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

		# Борлуулалт авах
		# Энэ он
		current_year = str(year)+'-%'
		query_sales = """
			SELECT order_date, mm, sum(amount) as amount, sum(qty_sold) as qty FROM (
				SELECT  
					to_char(so.date_order,'YYYY/MM') as order_date,
					EXTRACT(month from so.date_order) as mm,
					sol.price_unit * (sol.qty_delivered) as amount,
					(sol.qty_delivered) as qty_sold
				FROM sale_order_line as sol
				LEFT JOIN sale_order as so on (so.id = sol.order_id)
				LEFT JOIN product_product as pp on (pp.id = sol.product_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				WHERE so.state in ('sale','done') and sol.qty_delivered > 0 and 
						%s 
					  so.date_order::text ilike '%s'
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
				WHERE po.state in ('paid','done','invoiced') and   
					   %s
					  (po.date_order + interval '8 hour')::date::text ilike '%s'
					   %s 
				) as temp
			GROUP BY order_date, mm
			ORDER BY order_date, mm
		"""
		query1 = query_sales % (where_categ_ids, current_year, where_user_wh, where_categ_ids, current_year, where_user_wh)
		self.env.cr.execute(query1)

		query_result = self.env.cr.dictfetchall()

		series_amount = []
		series_qty = []
		series_amount_monthly = []
		series_qty_monthly = []
		for line in query_result:
			per = round((line['amount']*100)/year_total_amount_plan, 2)
			name = str(int(line['mm']))+u' month<br>'+str(per)+u' %'
			series_amount.append([ name, line['amount'] ])
			per = round((line['qty']*100)/year_total_qty_plan, 2)
			name = str(int(line['mm']))+u' month<br>'+str(per)+u' %'
			series_qty.append([ name, line['qty'] ])
			# Компаны сар сар
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

		temp_dict = {
			'name': ' ',
			'y': 2,
			'dataLabels': {
				'enabled': True
			}
		}
		series_amount.append(temp_dict)

		temp_dict_qty = {
			'name': ' ',
			'y': 0.2,
			'dataLabels': {
				'enabled': False
			}
		}
		series_qty.append(temp_dict_qty)
		datas['amount_donut_chart'] = series_amount
		datas['qty_donut_chart'] = series_qty

		# Компаны өсөлт бууралт сараар
		# Өмнөх оны борлуулалт сараар авах
		before_year = str(year-1)+'-%'
		query2 = query_sales % (where_categ_ids, before_year, where_user_wh, where_categ_ids, before_year, where_user_wh)
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

		# Өгөгдөл цэнэглэх - amount
		temp_dict_before = {
			'type':'column',
			'name': 'Last year',
			'data': series_amount_monthly_before,
		}
		temp_dict_plan = {
			'type':'column',
			'name': 'Plan',
			'data': series_amount_monthly_plan,
		}
		temp_dict_sale = {
			'type':'column',
			'name': 'Sales',
			'data': series_amount_monthly,
		}
		series1 = []
		series1.append(temp_dict_before)
		series1.append(temp_dict_plan)
		series1.append(temp_dict_sale)
		# Өгөгдөл цэнэглэх - qty
		temp_dict_qty_before = {
			'type':'column',
			'name': 'Last year',
			'data': series_qty_monthly_before,
		}
		temp_dict_qty_plan = {
			'type':'column',
			'name': 'Plan',
			'data': series_qty_monthly_plan,
		}
		temp_dict_qty_sale = {
			'type':'column',
			'name': 'Sales',
			'data': series_qty_monthly,
		}
		series2 = []
		series2.append(temp_dict_qty_before)
		series2.append(temp_dict_qty_plan)
		series2.append(temp_dict_qty_sale)
		# Өсөлт бууралт
		series_inc_amount = []
		series_inc_qty = []
		series_per_amount = []
		series_per_qty = []
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
			# %
			plist = [ddd['y'] for ddd in temp_dict_plan['data'] if ddd['name'] == line['name']]
			if plist:
				plan = plist[0]
				if plan != 0:
					per = round((sale_amount*100)/plan,2)
					temp = {
						'name': line['name'],
						'y': per
					}
					series_per_amount.append(temp)

		temp_dict_amount_inc_percent = {
			'name': 'Increase %',
			'type':'spline',
			'yAxis': 1,
			'color': 'rgba(255,	195, 15,1)',
			'data': series_inc_amount,
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Increase {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		series1.append(temp_dict_amount_inc_percent)
		temp_dict_amount_per_percent = {
			'name': 'Performance %',
			'type':'spline',
			'yAxis': 1,
			'color': 'rgba(20,112,69,1)',
			'data': series_per_amount,
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Performance {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		series1.append(temp_dict_amount_per_percent)

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
			# %
			plist = [ddd['y'] for ddd in temp_dict_qty_plan['data'] if ddd['name'] == line['name']]
			if plist:
				plan = plist[0]
				if plan != 0:
					per = round((sale_qty*100)/plan,2)
					temp = {
						'name': line['name'],
						'y': per
					}
					series_per_qty.append(temp)

		temp_dict_qty_inc_percent = {
			'name': 'Increase %',
			'type':'spline',
			'yAxis': 1,
			'color': 'rgba(255,	195, 15,1)',
			'data': series_inc_qty,
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Increase {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		series2.append(temp_dict_qty_inc_percent)
		temp_dict_qty_per_percent = {
			'name': 'Performance %',
			'type':'spline',
			'yAxis': 1,
			'color': 'rgba(20,112,69,1)',
			'data': series_per_qty,
			'marker': {
				'radius': 8,
				'lineWidth': 3,
			},
			'dataLabels': {
				'enabled': True,
				'color': '#FFFFFF',
				'align': 'center',
				'format': 'Performance {point.y:.1f}%',
				'style': {
					'fontSize': '13px',
					'fontFamily': 'Verdana, sans-serif'
				}
			},
		}
		series2.append(temp_dict_qty_per_percent)

		datas['company_monthly_chart'] = series1
		datas['company_monthly_qty_chart'] = series2
		# 
		return datas

