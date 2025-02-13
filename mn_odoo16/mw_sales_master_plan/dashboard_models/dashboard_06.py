# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError

# Баярын борлуулалт
class SalesPlanDashboard06(models.TransientModel):
	_name = 'sales.plan.dashboard.06'
	_description = 'Time analyze dashboard'

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

	warehouse_id = fields.Many2one('stock.warehouse', string=u'Салбар',
		domain=[('is_branch','=',True),('parent_id','=',False)])

	
	def get_datas(self, year, warehouse_id, context=None):
		datas = {}
		# Dates
		current_date = str(year)+'-%'
		before_date = str(year-1)+'-%'

		query = ""
		filter_type = "Компаны хэмжээнд"
		if warehouse_id:
			filter_type = self.env['stock.warehouse'].browse(warehouse_id).name + u' салбарын хэмжээнд'
			query = """
				SELECT 		
					(po.date_order + interval '8 hour')::date as day,
					EXTRACT(hour from (po.date_order + interval '8 hour')) as day_time,
					sum(pol.qty) as qty
				FROM pos_order_line as pol
				LEFT JOIN pos_order as po on (po.id = pol.order_id)
				LEFT JOIN stock_warehouse as sw on (sw.lot_stock_id = po.mw_location_id)
				LEFT JOIN stock_warehouse as swp on (swp.id = sw.parent_id)
				WHERE 
					  po.date_order::text ilike '%s' and 
					  swp.id = %d and 
					  po.state in ('paid','done','invoiced')	
			    GROUP BY day, day_time
			    ORDER BY day, day_time
			""" % (current_date, warehouse_id)
		else:
			query = """
				SELECT 		
					(po.date_order + interval '8 hour')::date as day,
					EXTRACT(hour from (po.date_order + interval '8 hour')) as day_time,
					sum(pol.qty) as qty
				FROM pos_order_line as pol
				LEFT JOIN pos_order as po on (po.id = pol.order_id)
				WHERE 
					  po.date_order::text ilike '%s' and
					  po.state in ('paid','done','invoiced')
			    GROUP BY day, day_time
			    ORDER BY day, day_time
			""" % (current_date)

		# print '---query-', query
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()

		csv_data = "<pre id='csv'>"
		max_qty = 0
		for line in query_result:
			if max_qty < line['qty']:
				max_qty = line['qty']
			temp_line = line['day']+','+str(int(line['day_time']))+','+str(line['qty'])+'\n'
			csv_data += temp_line
			
		csv_data += '</pre>'
		datas['time_analyze_data'] = csv_data
		datas['type'] = filter_type
		datas['max_qty'] = max_qty

		# --------------------
		return datas
