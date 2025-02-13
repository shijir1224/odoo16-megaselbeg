# -*- coding: utf-8 -*-


from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import calendar
import time

class MaintenanceDashboard02(models.TransientModel):
	_name = 'maintenance.dashboard.02'
	_description = 'Maintenance dashboard 02'

	@api.model
	def _get_default_branch(self):
		if self.env.user.branch_id:
			return self.env.user.branch_id.id
		else:
			return False

	# Columns
	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо', )
	branch_id = fields.Many2one('res.branch', string=u'Салбар', default=_get_default_branch)
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', )

	
	def get_datas(self, date_start, date_end, technic_id, branch_id=False, context=None):
		datas = {}
		if date_start and date_end and date_start <= date_end:
			date1 = date_start[:7] + "-01"
			month_range = calendar.monthrange(int(date_end[:4]), int(date_end[5:7]))
			date2 = date_end[:7] +'-'+str(month_range[1])

			additional_condition = ""
			additional_condition_wo = ""
			if technic_id:
				additional_condition = " and ll.technic_id = %d " % technic_id['ref']
				additional_condition_wo = " and wo.technic_id = %d " % technic_id['ref']

			# ==== month WO performance ==========================================
			# Нийт тоог авах
			query = """
				SELECT
					to_char(wo.date_required, 'YYYY/MM') as dddd,
					count(*) as qty
				FROM maintenance_workorder as wo
				WHERE wo.state != 'draft' and
					  wo.date_required >= '%s' and
					  wo.date_required <= '%s' and
					  wo.branch_id = %d
					   %s 
				GROUP BY dddd
				ORDER BY dddd
			""" % (date1, date2, branch_id, additional_condition_wo)
			self.env.cr.execute(query)
			wos = self.env.cr.dictfetchall()
			# === DATA set
			series = []
			temp_data_total = []
			for line in wos:
				temp = {
					'name': line['dddd'],
					'y': line['qty'],
				}
				temp_data_total.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Нийт',
				'data': temp_data_total,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.0f}ш',
					'style': {
						'fontSize': '11px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			# Хийгдсэн тоог авах
			query = """
				SELECT
					to_char(wo.date_required, 'YYYY/MM') as dddd,
					count(*) as qty
				FROM maintenance_workorder as wo
				WHERE wo.state in ('done','closed') and
					  wo.date_required >= '%s' and
					  wo.date_required <= '%s' and
					  wo.branch_id = %d
					   %s 
				GROUP BY dddd
				ORDER BY dddd
			""" % (date1, date2, branch_id, additional_condition_wo)
			self.env.cr.execute(query)
			wos = self.env.cr.dictfetchall()
			# === DATA set
			temp_data_done = []
			for line in wos:
				temp = {
					'name': line['dddd'],
					'y': line['qty'],
				}
				temp_data_done.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Хийгдсэн',
				'data': temp_data_done,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.0f}ш',
					'style': {
						'fontSize': '11px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			# Хийгдээгүй тоог авах
			query = """
				SELECT
					to_char(wo.date_required, 'YYYY/MM') as dddd,
					count(*) as qty
				FROM maintenance_workorder as wo
				WHERE wo.state not in ('draft','cancelled','done','closed') and
					  wo.date_required >= '%s' and
					  wo.date_required <= '%s' and
					  wo.branch_id = %d
					   %s 
				GROUP BY dddd
				ORDER BY dddd
			""" % (date1, date2, branch_id, additional_condition_wo)
			self.env.cr.execute(query)
			wos = self.env.cr.dictfetchall()
			# === DATA set
			temp_data = []
			for line in wos:
				temp = {
					'name': line['dddd'],
					'y': line['qty'],
				}
				temp_data.append(temp)

			temp_dict = {
				'type':'column',
				'name': u'Хийгдээгүй',
				'data': temp_data,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.0f}ш',
					'style': {
						'fontSize': '11px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			# Гүйцэтгэл % бодох
			temp_data = []
			for dl in temp_data_done:
				for tl in temp_data_total:
					if dl['name'] == tl['name']:
						per = (dl['y']*100)/tl['y']
						temp = {
							'name': dl['name'],
							'y': per,
						}
						temp_data.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Гүйцэтгэл %',
				'type':'spline',
				'yAxis': 1,
				'data': temp_data,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			datas['month_wo_performance_div'] = series

			# Засварчдын ажлын цагийн гүйцэтгэл
			# Нийт цагийг авах
			query = """
				SELECT
					to_char(ll.planned_date, 'YYYY/MM') as dddd,
					sum(ll.planned_time * wo.planned_mans) as qty
				FROM wo_planned_time_line as ll
				LEFT JOIN maintenance_workorder as wo on wo.id = ll.parent_id
				WHERE wo.state in ('done','closed') and
					  ll.planned_date >= '%s' and
					  ll.planned_date <= '%s' and
					  wo.branch_id = %d
					   %s 
				GROUP BY dddd
				ORDER BY dddd
			""" % (date_start, date_end, branch_id, additional_condition_wo)
			self.env.cr.execute(query)
			wos = self.env.cr.dictfetchall()
			# === DATA set
			series = []
			temp_data_total = []
			for line in wos:
				temp = {
					'name': line['dddd'],
					'y': line['qty'],
				}
				temp_data_total.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Төлөвлөсөн х/ц',
				'data': temp_data_total,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.1f}х/ц',
					'style': {
						'fontSize': '11px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			# Гүйцэтгэсэн цагийг авах
			query = """
				SELECT
					to_char((ll.date_start + interval '8 hour')::date, 'YYYY/MM') as dddd,
					sum(ll.spend_time) as qty
				FROM maintenance_employee_timesheet_line as ll
				LEFT JOIN maintenance_workorder as wo on wo.id = ll.parent_id
				WHERE wo.state in ('done','closed') and
					  (ll.date_start + interval '8 hour')::date >= '%s' and
					  (ll.date_start + interval '8 hour')::date <= '%s' and
					  wo.branch_id = %d
					   %s 
				GROUP BY dddd
				ORDER BY dddd
			""" % (date_start, date_end, branch_id, additional_condition_wo)
			self.env.cr.execute(query)
			wos = self.env.cr.dictfetchall()
			# === DATA set
			temp_data_done = []
			for line in wos:
				temp = {
					'name': line['dddd'],
					'y': line['qty'],
				}
				temp_data_done.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Ажилласан х/ц',
				'data': temp_data_done,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.1f}х/ц',
					'style': {
						'fontSize': '11px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			# Гүйцэтгэл % бодох
			temp_data = []
			for dl in temp_data_done:
				for tl in temp_data_total:
					if dl['name'] == tl['name']:
						per = 0
						if dl['y'] and tl['y'] and tl['y'] != 0:
							per = (dl['y']*100)/tl['y']
						temp = {
							'name': dl['name'],
							'y': per,
						}
						temp_data.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Гүйцэтгэл %',
				'type':'spline',
				'yAxis': 1,
				'data': temp_data,
				'dataLabels': {
					'enabled': True,
					'align': 'center',
					'format': '{point.y:.1f}%',
					'style': {
						'fontSize': '13px',
						'fontFamily': 'Verdana, sans-serif'
					}
				},
			}
			series.append(temp_dict)
			datas['month_employee_performance_div'] = series

			# WORK ==============TBB=================
			query_work = """
				SELECT
					to_char(ll.date, 'YYYY/MM') as dddd,
					ll.technic_type as technic_type,
					tt.report_order as report_order,
					avg(ll.tbbk) as qty
				FROM report_mining_technic_analyze as ll
				LEFT JOIN technic_equipment as tt on tt.id = ll.technic_id
				WHERE ll.owner_type = 'own_asset' and
					  ll.is_tbbk = 't' and
					  ll.date >= '%s' and
					  ll.date <= '%s' and
					  ll.branch_id = %d
					   %s
				GROUP BY dddd, ll.technic_type, tt.report_order
				ORDER BY dddd, tt.report_order, ll.technic_type
			"""
			query = query_work % (date1, date2, branch_id, additional_condition)
			print ('===', query)
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			series = []
			temp_data = {}
			key_list = []
			for line in query_result:
				temp = {
					'name': line['dddd'],
					'y': round(line['qty'],2),
				}
				if line['technic_type'] in temp_data:
					temp_data[line['technic_type']].append(temp)
				else:
					temp_data[line['technic_type']] = [temp]
					key_list.append(line['technic_type'])
			for key in key_list:
				temp_dict = {
					'type':'column',
					'name': key,
					'data': temp_data[key],
				}
				series.append(temp_dict)

			# Нийт дундаж
			query_work = """
				SELECT
					to_char(ll.date, 'YYYY/MM') as dddd,
					avg(ll.tbbk) as qty
				FROM report_mining_technic_analyze as ll
				WHERE ll.owner_type = 'own_asset' and
					  ll.is_tbbk = 't' and
					  ll.date >= '%s' and
					  ll.date <= '%s' and
					  ll.branch_id = %d
					   %s
				GROUP BY dddd
				ORDER BY dddd
			"""
			query = query_work % (date1, date2, branch_id, additional_condition)
			# print ('===', query)
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()
			temp_data = []
			for line in query_result:
				temp = {
					'name': line['dddd'],
					'y': round(line['qty'],2),
				}
				temp_data.append(temp)

			total_temp_dict = {
				'type':'spline',
				'name': 'Нийт дундаж',
				'data': temp_data,
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
			series.append(total_temp_dict)
			datas['by_monthly_work_tbb'] = series

			# PLAN ====================================
			# query_plan = """
			# 	SELECT
			# 		to_char(ll.date_required, 'YYYY/MM') as dddd,
			# 		tt.technic_type as technic_type,
			# 		count(DISTINCT tt.id) * max(ts.work_time_per_day * DATE_PART('days',
			# 			DATE_TRUNC('month', ll.date_required) + '1 MONTH'::INTERVAL - '1 DAY'::INTERVAL)) as font_time,
			# 		sum(ll.work_time) as qty
			# 	FROM maintenance_plan_line as ll
			# 	LEFT JOIN technic_equipment as tt on tt.id = ll.technic_id
			# 	LEFT JOIN technic_equipment_setting as ts on ts.id = tt.technic_setting_id
			# 	WHERE tt.owner_type = 'own_asset' and
			# 		  tt.is_tbb_report = 't' and
			# 		  ll.date_required >= '%s' and
			# 		  ll.date_required <= '%s'
			# 		   %s
			# 	GROUP BY dddd, tt.technic_type
			# 	ORDER BY dddd, tt.technic_type
			# """
			# query = query_plan % (date1, date2, additional_condition)
			# print ('===', query)
			# self.env.cr.execute(query)
			# query_result = self.env.cr.dictfetchall()
			# series = []
			# temp_data = {}
			# for line in query_result:
			# 	per = 100 - (100*line['qty']) / line['font_time']
			# 	temp = {
			# 			'name': line['dddd'],
			# 			'y': per,
			# 	}
			# 	if line['technic_type'] in temp_data:
			# 		temp_data[line['technic_type']].append(temp)
			# 	else:
			# 		temp_data[line['technic_type']] = [temp]
			#
			# for key in temp_data:
			# 	temp_dict = {
			# 		'type':'line',
			# 		'name': key,
			# 		'data': temp_data[key],
			# 	}
			# 	series.append(temp_dict)
			# datas['by_monthly_plan_tbb'] = series
			# **************************************************************
		return datas
