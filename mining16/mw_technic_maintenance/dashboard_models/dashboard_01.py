# -*- coding: utf-8 -*-


from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time

class MaintenanceDashboard01(models.TransientModel):
	_name = 'maintenance.dashboard.01'
	_description = 'Maintenance dashboard 01'

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

	def get_datas(self, date_start, date_end, branch_id=False, context=None):
		print ('===maintenance.dashboard.01', date_start, date_end)
		datas = {}
		if date_start and date_end and date_start <= date_end:
			# Төлөвлөгөө авах
			all_technics = self.env['technic.equipment'].search([
				('is_tbb_report','=',True),
				('state','in',['working','repairing','stopped']),
				('branch_id','=',branch_id),
				('owner_type','=','own_asset')], order='report_order')
			# Ирэх 7 хоногийн ТББК авах
			date1 = datetime.strptime(date_end, "%Y-%m-%d")
			date1 = date1 + timedelta(days=1)
			date1 = date1.strftime('%Y-%m-%d')
			#
			date2 = datetime.strptime(date_end, "%Y-%m-%d")
			date2 = date2 + timedelta(days=7)
			date2 = date2.strftime('%Y-%m-%d')

			temp_dict_plan = {}
			temp_dict_per = {}
			temp_dict_week_plan = {}
			key_list = []
			for technic in all_technics:
				p_tbbk = technic.get_technic_planned_tbbk(date_start, date_end)['tbbk'] or 0
				tbbk = technic.get_technic_tbbk(date_start, date_end)['tbbk'] or 0
				p_week_tbbk = technic.get_technic_planned_tbbk(date1, date2)['tbbk'] or 0



				if technic.technic_type in temp_dict_plan:
					temp_dict_plan[technic.technic_type].append(p_tbbk)
					temp_dict_per[technic.technic_type].append(tbbk)
					temp_dict_week_plan[technic.technic_type].append(p_week_tbbk)
				else:
					key_list.append(technic.technic_type)
					temp_dict_plan[technic.technic_type] = [p_tbbk]
					temp_dict_per[technic.technic_type] = [tbbk]
					temp_dict_week_plan[technic.technic_type] = [p_week_tbbk]

			temp_plan = []
			temp_week_plan = []
			temp_perf = []
			series = []

			total_plan = []
			total_per = []
			total_week = []
			for key in key_list:
				temp = {
					'name': key,
					'y': round(sum(temp_dict_plan[key])/len(temp_dict_plan[key]),2),
				}
				temp_plan.append(temp)
				total_plan += temp_dict_plan[key]
				#
				temp = {
					'name': key,
					'y': round(sum(temp_dict_week_plan[key])/len(temp_dict_week_plan[key]),2),
				}
				temp_week_plan.append(temp)
				total_week += temp_dict_week_plan[key]
				#
				temp = {
					'name': key,
					'y': round(sum(temp_dict_per[key])/len(temp_dict_per[key]),2),
				}
				temp_perf.append(temp)
				total_per += temp_dict_per[key]

			temp_dict_plan = {
				'type':'column',
				'name': u'Төлөвлөгөө',
				'data': temp_plan,
			}
			temp_dict_perf = {
				'type':'column',
				'name': u'Гүйцэтгэл',
				'data': temp_perf,
			}
			temp_dict_week_plan = {
				'type':'column',
				'name': u'Ирэх 7 хоног',
				'data': temp_week_plan,
			}

			series.append(temp_dict_plan)
			series.append(temp_dict_perf)
			series.append(temp_dict_week_plan)

			datas['by_technic_type'] = series
			title = u"Төлөвлөгөө: <b>"+str(round(sum(total_plan)/len(total_plan) if total_plan else 0,1))
			title += u"%</b>,  Гүйцэтгэл: <b>"+str(round(sum(total_per)/len(total_per) if total_per else 0,1))
			title += u"%</b>,  Ирэх 7 хоног: <b>"+str(round(sum(total_week)/len(total_week) if total_week else 0,1))+"%</b>"
			datas['by_technic_type_title'] = title

			# ==== WO performance ==========================================
			# Нийт тоог авах
			query = """
				SELECT
					wo.date_required as dddd,
					count(*) as qty
				FROM maintenance_workorder as wo
				WHERE wo.state != 'draft' and
					  wo.date_required >= '%s' and
					  wo.date_required <= '%s' and
					  wo.branch_id = %d
				GROUP BY wo.date_required
				ORDER BY wo.date_required
			""" % (date_start, date_end, branch_id)
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
					wo.date_required as dddd,
					count(*) as qty
				FROM maintenance_workorder as wo
				WHERE wo.state in ('done','closed') and
					  wo.date_required >= '%s' and
					  wo.date_required <= '%s' and
					  wo.branch_id = %d
				GROUP BY wo.date_required
				ORDER BY wo.date_required
			""" % (date_start, date_end, branch_id)
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
					wo.date_required as dddd,
					count(*) as qty
				FROM maintenance_workorder as wo
				WHERE wo.state not in ('draft','cancelled','done','closed') and
					  wo.date_required >= '%s' and
					  wo.date_required <= '%s' and
					  wo.branch_id = %d
				GROUP BY wo.date_required
				ORDER BY wo.date_required
			""" % (date_start, date_end, branch_id)
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
			datas['wo_performance_div'] = series
			# ----------------------------------

			# Засварчдын ажлын цагийн гүйцэтгэл
			# Нийт цагийг авах
			query = """
				SELECT
					ll.planned_date as dddd,
					sum(ll.planned_time * wo.planned_mans) as qty
				FROM wo_planned_time_line as ll
				LEFT JOIN maintenance_workorder as wo on wo.id = ll.parent_id
				WHERE wo.state in ('done','closed') and
					  ll.planned_date >= '%s' and
					  ll.planned_date <= '%s' and
					  wo.branch_id = %d
				GROUP BY ll.planned_date
				ORDER BY ll.planned_date
			""" % (date_start, date_end, branch_id)
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
					(ll.date_start + interval '8 hour')::date as dddd,
					sum(ll.spend_time) as qty
				FROM maintenance_employee_timesheet_line as ll
				LEFT JOIN maintenance_workorder as wo on wo.id = ll.parent_id
				WHERE wo.state in ('done','closed') and
					  (ll.date_start + interval '8 hour')::date >= '%s' and
					  (ll.date_start + interval '8 hour')::date <= '%s' and
					  wo.branch_id = %d
				GROUP BY dddd
				ORDER BY dddd
			""" % (date_start, date_end, branch_id)
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
						print('===', dl['y'], tl['y'])
						if dl['y'] and tl['y'] != 0 and tl['y']:
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
			datas['employee_performance_div'] = series

			# Засварын цаг - Системээр
			query = """
				SELECT
					(CASE WHEN reason.id is null THEN 'Empty' ELSE reason.name END) as r_name,
					sum(ll.diff_time) as work_time
				FROM mining_motohour_entry_cause_line as ll
				LEFT JOIN mining_motohour_entry_line as per on per.id = ll.motohour_cause_id
				LEFT JOIN mining_motohours_cause as cause on cause.id = ll.cause_id
				LEFT JOIN mining_daily_entry as daily on (daily.id = per.motohour_id)
				LEFT JOIN maintenance_damaged_type as reason on (reason.id = ll.repair_system_id)
				LEFT JOIN technic_equipment as t on t.id = per.technic_id
				LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
				WHERE cause.is_repair = 't' and
					  daily.date >= '%s' and
					  daily.date <= '%s' and
					  daily.state = 'approved' and
					  t.owner_type = 'own_asset' and
					  t.is_tbb_report = 't' and
					  daily.branch_id = %d
				GROUP BY r_name
				ORDER BY r_name
			""" % (date_start, date_end, branch_id)
			self.env.cr.execute(query)
			print ('===system===', query)
			reasons = self.env.cr.dictfetchall()

			temp_data = []
			series = []
			for line in reasons:
				temp = {
					'name': line['r_name'],
					'y': line['work_time'],
				}
				temp_data.append(temp)
			temp_dict = {
				'type':'column',
				'name': u'Системийн нэр',
				'data': temp_data,
			}
			series.append(temp_dict)
			datas['repairtime_by_system'] = series

			# **************************************************************
		return datas
