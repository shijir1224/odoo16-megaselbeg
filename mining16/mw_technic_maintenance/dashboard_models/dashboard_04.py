# -*- coding: utf-8 -*-


from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import time
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE

class MaintenanceDashboard04(models.TransientModel):
	_name = 'maintenance.dashboard.04'
	_description = 'Maintenance dashboard 04'

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

	def get_datas(self, date_start, date_end, branch_id, context=None):
		print ('===maintenance.dashboard.04', date_start, date_end)
		datas = {}
		if date_start and date_end and date_start <= date_end:
			# Төлөвлөгөө авах =========================
			all_technics = self.env['technic.equipment'].search([
				('is_tbb_report','=',True),
				('branch_id','=',branch_id),
				('state','in',['working','repairing','stopped','parking'])], order='report_order')

			temp_dict_plan = []
			temp_dict_per = []
			key_list = []
			for technic in all_technics:
				p_tbbk = technic.get_technic_planned_tbbk(date_start, date_end)['tbbk'] or 0
				tbbk = technic.get_technic_tbbk(date_start, date_end)['tbbk'] or 0
				temp_dict_plan.append(p_tbbk)
				temp_dict_per.append(tbbk)

			# SET
			temp_data = []
			if temp_dict_plan:
				temp_data.append(round(sum(temp_dict_plan)/len(temp_dict_plan),2))
			if temp_dict_per:
				temp_data.append(round(sum(temp_dict_per)/len(temp_dict_per),2))
			temp = {
				'name': "ТББ, Ашиглалт",
				'data': temp_data
			}
			series = []
			series.append(temp)
			datas['all_technic_data'] = series

			# Засварын цаг - Нийт =========================
			query = """
				SELECT
					cause.cause_name as cause_name,
					sum(ll.diff_time) as work_time
				FROM mining_motohour_entry_cause_line as ll
				LEFT JOIN mining_motohour_entry_line as per on per.id = ll.motohour_cause_id
				LEFT JOIN mining_motohours_cause as cause on cause.id = ll.cause_id
				LEFT JOIN mining_daily_entry as daily on (daily.id = per.motohour_id)
				LEFT JOIN technic_equipment as tt on tt.id = per.technic_id
				WHERE cause.is_repair = 't' and
					  daily.date >= '%s' and
					  daily.date <= '%s' and
					  daily.state = 'approved' and 
					  tt.is_tbb_report = 't'
				GROUP BY cause_name
				ORDER BY cause_name
			""" % (date_start, date_end)
			self.env.cr.execute(query)
			# print ('===total_repairtime_by_type===', query)
			reasons = self.env.cr.dictfetchall()

			temp_data = []
			series = []
			for line in reasons:
				temp = {
					'name': line['cause_name'],
					'y': line['work_time'],
				}
				temp_data.append(temp)
			temp_dict = {
				'name': 'Засварын цаг',
				'data': temp_data,
			}
			series.append(temp_dict)
			datas['total_repairtime_by_type'] = series

			# Засварын цаг - Exca =========================
			query = """
				SELECT
					cause.cause_name as cause_name,
					sum(ll.diff_time) as work_time
				FROM mining_motohour_entry_cause_line as ll
				LEFT JOIN mining_motohour_entry_line as per on per.id = ll.motohour_cause_id
				LEFT JOIN mining_motohours_cause as cause on cause.id = ll.cause_id
				LEFT JOIN mining_daily_entry as daily on (daily.id = per.motohour_id)
				LEFT JOIN technic_equipment as tt on tt.id = per.technic_id
				WHERE cause.is_repair = 't' and
					  daily.date >= '%s' and
					  daily.date <= '%s' and
					  daily.state = 'approved' and 
					  tt.is_tbb_report = 't' and 
					  tt.technic_type = 'excavator' and
					  tt.branch_id = %d
				GROUP BY cause_name
				ORDER BY cause_name
			""" % (date_start, date_end, branch_id)
			self.env.cr.execute(query)
			# print ('===exca_repairtime_by_type===', query)
			reasons = self.env.cr.dictfetchall()

			temp_data = []
			series = []
			for line in reasons:
				temp = {
					'name': line['cause_name'],
					'y': line['work_time'],
				}
				temp_data.append(temp)
			temp_dict = {
				'name': 'Засварын цаг',
				'data': temp_data,
			}
			series.append(temp_dict)
			datas['exca_repairtime_by_type'] = series

			# Засварын цаг - Dump =========================
			query = """
				SELECT
					cause.cause_name as cause_name,
					sum(ll.diff_time) as work_time
				FROM mining_motohour_entry_cause_line as ll
				LEFT JOIN mining_motohour_entry_line as per on per.id = ll.motohour_cause_id
				LEFT JOIN mining_motohours_cause as cause on cause.id = ll.cause_id
				LEFT JOIN mining_daily_entry as daily on (daily.id = per.motohour_id)
				LEFT JOIN technic_equipment as tt on tt.id = per.technic_id
				WHERE cause.is_repair = 't' and
					  daily.date >= '%s' and
					  daily.date <= '%s' and
					  daily.state = 'approved' and 
					  tt.is_tbb_report = 't' and 
					  tt.technic_type = 'dump' and 
					  tt.branch_id = %d
				GROUP BY cause_name
				ORDER BY cause_name
			""" % (date_start, date_end, branch_id)
			self.env.cr.execute(query)
			# print ('===dump_repairtime_by_type===', query)
			reasons = self.env.cr.dictfetchall()

			temp_data = []
			series = []
			for line in reasons:
				temp = {
					'name': line['cause_name'],
					'y': line['work_time'],
				}
				temp_data.append(temp)
			temp_dict = {
				'name': 'Засварын цаг',
				'data': temp_data,
			}
			series.append(temp_dict)
			datas['dump_repairtime_by_type'] = series

			# Засварын цаг - Support =========================
			query = """
				SELECT
					cause.cause_name as cause_name,
					sum(ll.diff_time) as work_time
				FROM mining_motohour_entry_cause_line as ll
				LEFT JOIN mining_motohour_entry_line as per on per.id = ll.motohour_cause_id
				LEFT JOIN mining_motohours_cause as cause on cause.id = ll.cause_id
				LEFT JOIN mining_daily_entry as daily on (daily.id = per.motohour_id)
				LEFT JOIN technic_equipment as tt on tt.id = per.technic_id
				WHERE cause.is_repair = 't' and
					  daily.date >= '%s' and
					  daily.date <= '%s' and
					  daily.state = 'approved' and 
					  tt.is_tbb_report = 't' and 
					  tt.technic_type in ('dozer','wheel_dozer','loader','grader') and 
					  tt.branch_id = %d
				GROUP BY cause_name
				ORDER BY cause_name
			""" % (date_start, date_end, branch_id)
			self.env.cr.execute(query)
			# print ('===support_repairtime_by_type===', query)
			reasons = self.env.cr.dictfetchall()

			temp_data = []
			series = []
			for line in reasons:
				temp = {
					'name': line['cause_name'],
					'y': line['work_time'],
				}
				temp_data.append(temp)
			temp_dict = {
				'name': 'Засварын цаг',
				'data': temp_data,
			}
			series.append(temp_dict)
			datas['support_repairtime_by_type'] = series

			# Зогсолтын мэдээлэл =========================
			query = """
				SELECT
					mt.name as description,
					array_agg(DISTINCT ll.technic_id) as technic_ids
				FROM maintenance_plan_line as ll
				LEFT JOIN maintenance_type as mt on mt.id = ll.maintenance_type_id
				LEFT JOIN technic_equipment as tt on tt.id = ll.technic_id 
				WHERE ll.state = 'confirmed' and
					  ll.maintenance_type = 'stopped' and
					  ll.date_required = '%s' and 
					  ll.maintenance_type_id is not null and
					  ((ll.is_waiting_tire = 't' and tt.rubber_tired = 't') or ll.is_waiting_part = 't') and 
					  ll.branch_id = %d
				GROUP BY mt.name
				ORDER BY mt.name
			""" % (date_end, branch_id)
			self.env.cr.execute(query)
			print ('===Stopped DB===', query)
			stopped_plans = self.env.cr.dictfetchall()
			series = []
			drilldown_series = []
			temp_stopped_technics = []
			tot = 0
			for plan in stopped_plans:
				temp = {
					'name': plan['description'],
					'y': len(plan['technic_ids']),
					'drilldown': plan['description'],
				}
				tot += len(plan['technic_ids'])
				series.append(temp)
				temp_data = []
				for t_id in plan['technic_ids']:
					technic = self.env['technic.equipment'].browse(t_id)
					temp_stopped_technics.append(technic)
					qty = 1
					pivot = self.env['technic.tire.count.pivot.report'].search([
						('technic_id','=',t_id),
						('is_less_tire','=','no'),
						('less_counts','>',0)], limit=1)
					if pivot:
						qty = pivot.less_counts
					temp_data.append([technic.display_name, qty])
				temp_drill = {
					'id': plan['description'],
					'data': temp_data
				}
				drilldown_series.append(temp_drill)

			datas['stopped_by_status_title'] = "Нийт зогсолттой %d техник" % tot
			datas['stopped_by_status'] = [{'name':'Зогсолт', 'colorByPoint': True, 'data': series}]
			datas['stopped_by_status_drill'] = {'series': drilldown_series}

			# Техникийн тоон мэдээлэл =========================
			temp_dict = {}
			for technic in temp_stopped_technics:
				if technic.technic_type in temp_dict:
					temp_dict[technic.technic_type] += 1
				else:
					temp_dict[technic.technic_type] = 1
			exca_count = 0
			dump_count = 0
			dozer_count = 0
			loader_count = 0
			grader_count = 0
			other_count = 0
			for key in temp_dict:
				if key in ['excavator','wheel_excavator']:
					exca_count += temp_dict[key]
				elif key == 'dump':
					dump_count += temp_dict[key]
				elif key in ['dozer','wheel_dozer']:
					dozer_count += temp_dict[key]
				elif key == 'loader':
					loader_count += temp_dict[key]
				elif key == 'grader':
					grader_count += temp_dict[key]
				else:
					other_count += temp_dict[key]
			datas['all_technic_info'] = {
				'production_total': exca_count+dump_count,
				'exca_count': exca_count,
				'dump_count': dump_count,
				
				'support_total': dozer_count+loader_count+grader_count,
				'dozer_count': dozer_count,
				'loader_count': loader_count,
				'grader_count': grader_count,

				'other_count': other_count,
			}

			# Нийт техникийн тоо
			worked = len(all_technics)-len(temp_stopped_technics)
			stopped = len(temp_stopped_technics)
			temp_data = []
			temp_data.append({'name': 'Ажиллаж байгаа', 'y': worked})
			temp_data.append({'name': 'Зогсож байгаа', 'y': stopped})
			temp = {
				'name': "Нийт техник",
				'data': temp_data
			}
			series = []
			series.append(temp)
			datas['total_by_status'] = series

			# Ажилтны TIMESHEET мэдээлэл =========================
			# Ажиллах цаг Ростероос авах
			query = """
				SELECT
					sum(lll.worked_hour) as spend_time
				FROM hr_timetable_line_line as lll
				LEFT JOIN hr_timetable_line as ll on ll.id = lll.parent_id
				LEFT JOIN hr_department as dep on dep.id = ll.department_id
				WHERE --ll.state != 'draft' and 
					  lll.is_work_schedule = 'worked' and 
					  lll.date >= '%s' and
					  lll.date <= '%s' and
					  dep.branch_id = %d and
					  dep.parent_id = %d 
			""" % (date_start, date_end, branch_id, self._get_parent_department())
			self.env.cr.execute(query)
			print ('===Roster DB===', query)
			rosters = self.env.cr.dictfetchall()
			planned_manhours = 0
			print('===', rosters)
			if rosters and rosters[0]['spend_time']:
				planned_manhours = rosters[0]['spend_time']

			# Ажилласан цаг авах
			query = """
				SELECT
					ll.maintenance_type as maintenance_type,
					sum(ll.spend_time) as spend_time
				FROM repaiman_pivot_report as ll
				WHERE ll.date >= '%s' and 
					  ll.work_type != 'call' and 
					  ll.date <= '%s' and 
					  ll.branch_id = %d 
				GROUP BY ll.maintenance_type
			""" % (date_start, date_end, branch_id)
			self.env.cr.execute(query)
			print ('===Timesheet DB===', query)
			timesheets = self.env.cr.dictfetchall()
			worked_manhours = 0
			temp_data_pie = []
			for ll in timesheets:
				worked_manhours += ll['spend_time']
				temp = {
					'name': self._get_maintenance_type(ll['maintenance_type']),
					'y': ll['spend_time'],
				}
				temp_data_pie.append(temp)

			# SET
			temp_data = []
			temp_data.append(round(planned_manhours,2))
			temp_data.append(round(worked_manhours,2))
			temp = {
				'name': "Цаг ашиглалт, хүн цаг",
				'data': temp_data
			}
			series = []
			series.append(temp)
			datas['total_timesheet'] = series
			# PIE
			series = []
			temp_dict = {
				'name': 'Засварын төрлөөр',
				'data': temp_data_pie,
			}
			series.append(temp_dict)
			datas['total_timesheet_pie'] = series

			# WorkOrder pie ================================
			query = """
				SELECT 
					tt.damaged_name as damaged_name,
					tt.maintenance_type as maintenance_type,
					sum(tt.count) as count
				FROM (
					SELECT
						mdt.name as damaged_name,
						ll.maintenance_type as maintenance_type,
						ll.man_hours as count
					FROM maintenance_wo_report as ll
					LEFT JOIN maintenance_damaged_type as mdt on mdt.id = ll.damaged_type_id
					WHERE ll.date >= '%s' and
						  ll.date <= '%s' and 
						  ll.branch_id = %d
				 --    UNION ALL 3.16nd xassan
				 --    SELECT
					-- 	mdt.name as damaged_name,
					-- 	'call' as maintenance_type,
					-- 	cll.man_hours as count
					-- FROM maintenance_call_report as cll
					-- LEFT JOIN maintenance_damaged_type as mdt on mdt.id = cll.damaged_type_id
					-- WHERE  
					--       cll.damaged_type_id is not null and 
					-- 	  cll.date_required >= '%s' and
					-- 	  cll.date_required <= '%s' and 
					-- 	  cll.branch_id = %d and
					-- 	  cll.state not in ('draft','cancelled')
			    ) as tt
				GROUP BY tt.damaged_name, tt.maintenance_type
			""" % (date_start, date_end, branch_id, date_start, date_end, branch_id)
			self.env.cr.execute(query)
			print ('===Workorder DB===', query)
			workorders = self.env.cr.dictfetchall()
			temp_data_planned = []
			temp_data_unplanned = []
			tot = 0
			tot2 = 0
			for ll in workorders:
				temp = {
					'name': ll['damaged_name'],
					'y': ll['count'],
				}
				if ll['maintenance_type'] in ['pm_service','planned']:
				# ['main_service','pm_service','planned','component_repair','tire_service']:
					temp_data_planned.append(temp)
					tot += ll['count']
				elif ll['maintenance_type'] in ['not_planned']:
					temp_data_unplanned.append(temp)
					tot2 += ll['count']
			temp_dict = {
				'name': 'Төлөвлөгөөт засвар',
				'data': temp_data_planned,
			}
			temp_dict_2 = {
				'name': 'Төлөвлөгөөт бус засвар',
				'data': temp_data_unplanned,
			}
			datas['work_order_planned'] = [temp_dict]
			datas['work_order_planned_title'] = 'Төлөвлөгөөт засвар, Нийт %d' % tot
			datas['work_order_unplanned'] = [temp_dict_2]
			datas['work_order_unplanned_title'] = 'Төлөвлөгөөт бус засвар, Нийт %d' % tot2
			# **************************************************************
		return datas

	def _get_parent_department(self):
		return 187

	def _get_status_name(self, status):
		test_dict = {
			'waiting_for_spare':'Сэлбэг хүлээж зогссон',
			'waiting_for_tire':'Дугуй хүлээж зогссон',
			'working':'Ажиллаж байгаа',
			'repairing':'Засварт орсон',
			'inspection':'Үзлэг хийж байгаа',
			'parking':'Паркласан',
		}
		return test_dict[status]
	def _get_technic_type_name(self, technic_type):
		test_dict = {
			'excavator':'Экскаватор',
			'dump':'Автосамосвал',
			'dozer':'Бульдозер',
			'grader':'Автогрейдер',
			'loader':'Дугуйт ачигч',
			'wheel_excavator':'Дугуйт экскаватор',
			'wheel_dozer':'Дугуйт түрэгч',
			'tank_truck':'Түлш цэнэглэх машин',
			'water_truck':'Усны машин',
			'service_car':"Тосолгооны машин",
			'fire_truck':'Галын машин',
			'ambulance_car':'Эмнэлэгийн машин',
			'mechanizm':'Өргөх механизм',
			'transportation_vehicle':"Хөнгөн тэрэг",
			'passenger_bus':"Автобус",
			'achaanii_mashin':'Ачааны машин',
			'drill':"Өрмийн машин",
			'indvv':"Индүү",
			'light_tower':'Гэрэлт цамхаг',
			'electric_generator':'Цахилгаан үүсгүүр',
			'air_compressor':'Хийн компрессор',
			'welding_machine':'Гагнуурын аппарат',
			'heater':'Халаагч',
		}
		return test_dict[technic_type]

	def _get_maintenance_type(self, maintenance_type):
		return dict(MAINTENANCE_TYPE)[maintenance_type]
	def _get_maintenance_type_wo(self, maintenance_type):
		return dict(MAINTENANCE_TYPE)[maintenance_type]