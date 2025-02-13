# -*- coding: utf-8 -*-

from multiprocessing.connection import wait
from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import time
import base64
import xlsxwriter
from io import BytesIO
import pdfkit

class MaintenanceDashboard03(models.TransientModel):
	_name = 'maintenance.dashboard.03'
	_description = 'Maintenance dashboard 03'

	@api.model
	def _get_default_branch(self):
		if self.env.user.branch_id:
			return self.env.user.branch_id.id or self.env.user.branch_ids[
				0].id if self.env.user.branch_ids.filtered(
					lambda r: r.company_id == self.env.user.company_id) else 1
		else:
			return False

	# Columns
	date_start = fields.Date(required=True,
							 string=u'Эхлэх огноо',
							 default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True,
						   string=u'Дуусах огноо',
						   default=fields.Date.context_today)

	branch_id = fields.Many2one('res.branch',
								string=u'Салбар',
								default=_get_default_branch)

	if_send_mail = fields.Boolean(string='Мэйл явуулах эсэх', default=False)
	partner_id = fields.Many2one('res.partner', string='Мэйл хүүлэн авах харилцагч')

	def get_datas(self, date_start, date_end, branch_id, context=None):
		datas = {}
		if date_start and date_end and date_start <= date_end:
			sd = datetime.strptime(date_start, "%Y-%m-%d")
			ed = datetime.strptime(date_end, "%Y-%m-%d")
			days = (ed - sd).days + 1
			plan_lines = []
			# Төлөвлөгөө ===============================
			query = """
				SELECT
					tt.report_order as report_order,
					tt.technic_type as technic_type,
					tt.technic_name as technic_name,
					tt.technic_id as technic_id,
					tt.model_id,
					tt.modelname,
					tt.park_number,
					tt.vin_number,
					tt.state as state,
					tt.dddd as dddd,
					min(tt.plan_id) as plan_id,
					array_agg(tt.description) as description,
					sum(tt.work_time) as work_time
				FROM (
					SELECT
						t.report_order as report_order,
						t.technic_type as technic_type,
						t.id as technic_id,
						t.name as technic_name,
						t.model_id,
						mm.modelname,
						t.park_number,
						t.vin_number,
						t.state as state,
						plan.date_required as dddd,
						plan.description as description,
						--wo.performance_description as description,
						plan.id as plan_id,
						plan.work_time as work_time
					FROM maintenance_plan_line as plan
					LEFT JOIN technic_equipment as t on (t.id = plan.technic_id)
					LEFT JOIN technic_model_model as mm on t.model_id = mm.id
					--LEFT JOIN maintenance_workorder as wo on (wo.technic_id = t.id) 
					WHERE
						  plan.date_required >= '%s' and
						  plan.date_required <= '%s' and
						  plan.state not in ('draft','cancelled') and
						  t.branch_id = %d
					UNION ALL
					SELECT
						t.report_order as report_order,
						t.technic_type as technic_type,
						t.id as technic_id,
						t.name as technic_name,
						t.model_id,
						mm.modelname,
						t.park_number,
						t.vin_number,
						t.state as state,
						null as dddd,
						'' as description,
						null as plan_id,
						0.5 as work_time
					FROM technic_equipment as t
					LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
					LEFT JOIN technic_model_model as mm on t.model_id = mm.id
					WHERE
						  t.state in ('working','repairing','stopped','parking') and
						  --t.owner_type = 'own_asset' and
						  t.branch_id = %d and
						  t.is_tbb_report
				) as tt
				GROUP BY tt.report_order, tt.technic_type, tt.technic_name, tt.technic_id, tt.dddd, tt.state, tt.model_id, tt.modelname, tt.park_number, tt.vin_number
				ORDER BY tt.report_order, tt.technic_type, tt.technic_name, tt.dddd
			""" % (date_start, date_end, branch_id, branch_id)
			self.env.cr.execute(query)
			plans = self.env.cr.dictfetchall()
			if plans:
				# Өдрийн дүүргэлт
				query_dates = """
					SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
				""" % (date_start, date_end)
				self.env.cr.execute(query_dates)
				dates_result = self.env.cr.dictfetchall()
				temp_lines = []
				line_dict_idx = {}
				idx = 0
				for ll in dates_result:
					tt = {
						'plan_date': ll['dddd'].strftime("%Y-%m-%d"),
						'work_time': 0,
					}
					temp_lines.append(tt)
					line_dict_idx[ll['dddd'].strftime("%Y-%m-%d")] = idx
					idx += 1

				technic_dict = {}
				for line in plans:
					if line['technic_id'] not in technic_dict:
						technic = self.env['technic.equipment'].browse(
							line['technic_id'])
						norm = technic.technic_setting_id.work_time_per_day or 1
						tt = temp_lines.copy()
						technic_dict[line['technic_id']] = {
							'technic_id': line['technic_id'],
							'technic_name': technic.name,
							'model_id': technic.model_id.id,
							'model_name': technic.model_id.name,
							'park_number': technic.park_number,
							'vin_number': technic.vin_number,
							'norm_motoh': days * norm,
							'plans': tt,
							'total_work_time': 0,
							'planned_time': 0,
							'unplanned_time': days * 1.5,
							'parts_waiting_time': 0,
							'description': technic.state + ': ' + str(technic.total_odometer),
						}
					plan = self.env['maintenance.plan.line'].browse(
						line['plan_id'])
					# ---
					if line['dddd']:
						idx = line_dict_idx[line['dddd'].strftime("%Y-%m-%d")]
						temp_plan = technic_dict[line['technic_id']]['plans'][idx].copy()
						temp_plan['plan_id'] = plan.id
						temp_plan['plan_number'] = plan.name
						temp_plan['state'] = plan.state
						temp_plan['maintenance_name'] = plan.maintenance_type_id.name
						temp_plan['shift'] = plan.shift
						temp_plan['work_time'] += line['work_time']
						temp_plan['description'] = set(line['description'])
						temp_plan['color'] = plan.maintenance_type_id.color
						technic_dict[line['technic_id']]['plans'][idx] = temp_plan
						technic_dict[line['technic_id']]['total_work_time'] += line['work_time']
						technic_dict[line['technic_id']]['planned_time'] += line['work_time'] if plan.maintenance_type_id.is_pm else 0
						technic_dict[line['technic_id']]['parts_waiting_time'] += line['work_time'] if plan.maintenance_type_id.is_waiting_part or plan.maintenance_type_id == False else 0
						technic_dict[line['technic_id']]['unplanned_time'] -= 1.5

				# DATA бэлдэх
				for key in technic_dict:
					tbbk = round((100 - ((technic_dict[key]['planned_time']+technic_dict[key]['parts_waiting_time']+technic_dict[key]['unplanned_time']) * 100) / technic_dict[key]['norm_motoh']), 2) or 0
					temp = {
						'description': technic_dict[key]['description'],
						'technic_id': key,
						'technic_name': technic_dict[key]['technic_name'],
						'model_id': technic_dict[key]['model_id'],
						'model_name': technic_dict[key]['model_name'],
						'park_number': technic_dict[key]['park_number'],
						'vin_number': technic_dict[key]['vin_number'],
						'plans': technic_dict[key]['plans'],
						'norm_motoh': technic_dict[key]['norm_motoh'],
						'total_work_time': technic_dict[key]['total_work_time'],
						'planned_time': technic_dict[key]['planned_time'],
						'unplanned_time': technic_dict[key]['unplanned_time'],
						'parts_waiting_time': technic_dict[key]['parts_waiting_time'],
						'tbbk': tbbk
					}
					plan_lines.append(temp)
			datas['plan_lines'] = plan_lines or False

		# Daily info ===================================================
		# Мото цагийн мэдээллээс авах
		ed = datetime.strptime(date_end, "%Y-%m-%d")
		before_date = ed - relativedelta(months=1)
		query = """
			SELECT
				t.report_order as report_order,
				t.technic_type as technic_type,
				t.id as technic_id,
				--tm.name as model_name,
				min(per.first_odometer_value) as start,
				max(per.last_odometer_value) as finish,
				sum(per.repair_time) as repair_time,
				sum(per.work_time) as work_time,
				--t.state as state,
				--CASE WHEN per.work_time > 0 THEN 'Working' 
					 --WHEN per.date < '%s' THEN 'Parking'
					 --ELSE 'Down'   
				--END
				null::char as state,
				null::char as daily_jobs
			FROM mining_motohour_entry_line as per
			LEFT JOIN mining_daily_entry as parent on parent.id = per.motohour_id
			LEFT JOIN technic_equipment as t on (t.id = per.technic_id)
			--LEFT JOIN technic_model_model as tm on tm.id = t.model_id
			LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
			--LEFT JOIN maintenance_workorder as wo on (wo.technic_id = t.id)
			WHERE
				  per.date = '%s' and
				  parent.branch_id = %d and
				  t.owner_type ='own_asset'
			GROUP BY t.report_order, t.technic_type, t.name, t.id
			--ORDER BY t.state
			--ORDER BY CASE WHEN technic_type in ('excavator') THEN 1
			--  WHEN model_name like ('%s') THEN 2
			--  WHEN model_name like ('%s') THEN 3
			--  WHEN model_name like ('%s') THEN 4
			--  WHEN model_name like ('%s') THEN 5
			--  WHEN technic_type in ('dump') THEN 10
			--  WHEN technic_type in ('grader') THEN 20
			--  ELSE 30 END
		""" % (before_date.date(), date_end, branch_id, '%T264%', '%MT3300%',
		 '%MT4400%', '%TR60%')
		self.env.cr.execute(query)
		performances = self.env.cr.dictfetchall()
		performance_lines = []
		technic_ids = []
		for line in performances:
			technic = self.env['technic.equipment'].browse(line['technic_id'])
			log_status_obj = self.env['technic.equipment.log.status']
			wo_obj = self.env['maintenance.workorder']
			res = wo_obj._get_daily_status(technic, date_end)
			norm_hours = 24
			moto_lines = self.env['mining.motohour.entry.line'].sudo().search([
				('technic_id', '=', technic.id), ('date', '=', date_end)
			])
			if moto_lines:
				if 'working' in moto_lines.mapped('daily_state'):
					line['state'] = 'Working'
					line['daily_jobs'] = ', '.join(
						moto_lines.filtered(lambda r: r.daily_desc).mapped(
							'daily_desc'))
				elif 'long_down' in moto_lines.mapped('daily_state'):
					line['state'] = 'Down'
					line['daily_jobs'] = ', '.join(
						moto_lines.filtered(lambda r: r.daily_desc).mapped(
							'daily_desc'))
				else:
					line['state'] = 'Parking'
					line['daily_jobs'] = ', '.join(
						moto_lines.filtered(lambda r: r.daily_desc).mapped(
							'daily_desc'))
			else:
				line['state'] = 'Parking'
				line['daily_jobs'] = ''
			seq = 0
			if technic.technic_type == 'excavator':
				seq = 1
			# elif 'T264' in technic.model_id.name:
			# 	seq = 2
			# elif 'MT3300' in technic.model_id.name:
			# 	seq = 3
			# elif 'MT4400' in technic.model_id.name:
			# 	seq = 4
			# elif 'TR60' in technic.model_id.name:
			# 	seq =exca 5
			elif technic.technic_type == 'dump':
				seq = 6
			elif technic.technic_type == 'loader':
				seq = 7
			elif technic.technic_type == 'grader':
				seq = 8
			elif technic.technic_type == 'dozer':
				seq = 9
			else:
				seq = 10
			temp = {
				'park_number': technic.park_number,
				'type': technic.model_id.name,
				'serial': technic.vin_number,
				'technic_type': line['technic_type'],
				'start': line['start'],
				'finish': line['finish'],
				'work_hours': norm_hours,
				'down_hours': line['repair_time'],
				'worked_hours': line['work_time'],
				'tbbk': round((line['work_time'] * 100) / norm_hours, 2),
				'state': line['state'],
				'daily_jobs': line['daily_jobs'],
				'sequence': seq,
				# 'cell_type':'normal',
				# 'desc':'',
			}
			performance_lines.append(temp)
			technic_ids.append(technic.id)
		# Техникийн статус логоос авах ===============================
		# query = """
		# 	SELECTs report_order,
		# 		t.technic_type a
		# 		t.report_order as technic_type,
		# 		t.id as technic_id,
		# 		max(ll.id) as id
		# 	FROM technic_equipment_log_status as ll
		# 	LEFT JOIN technic_equipment as t on (t.id = ll.technic_id)
		# 	LEFT JOIN technic_equipment_setting as ts on ts.id = t.technic_setting_id
		# 	WHERE
		# 		  (ll.date_time+interval '8 hour')::date <= '%s' and
		# 		  ll.state = 'confirmed'
		# 	GROUP BY t.report_order, t.technic_type, t.name, t.id
		# 	ORDER BY t.report_order, t.technic_type, t.name
		# """ % (date_end)
		# self.env.cr.execute(query)
		# status_logs = self.env.cr.dictfetchall()
		# for line in status_logs:
		# 	if line['id'] not in technic_ids:
		# 		technic = self.env['technic.equipment'].browse(line['technic_id'])
		# 		log = self.env['technic.equipment.log.status'].browse(line['id'])
		# 		norm_hours = 24
		# 		temp = {
		# 			'park_number': technic.park_number,
		# 			'type': technic.model_id.name,
		# 			'serial': technic.vin_number,
		# 			'start': technic.total_odometer if log.state == 'working' else log.odometer,
		# 			'finish': technic.total_odometer if log.state == 'working' else log.odometer,
		# 			'work_hours': norm_hours,
		# 			'down_hours': 0,
		# 			'worked_hours': log.work_time,
		# 			'tbbk': round((log.work_time*100)/norm_hours, 2),
		# 			'state': log.status_type,
		# 			'daily_jobs': log.note,
		# 		}
		# 		performance_lines.append(temp)
		# performance_lines.sort(key=lambda x: x.get('technic_type'))
		# performance_lines.sort(key=lambda x: x.get('type'))
		performance_lines.sort(key=lambda x: x.get('park_number'))
		performance_lines.sort(key=lambda x: x.get('sequence'))
		performance_lines.sort(key=lambda x: x.get('state'), reverse=True)
		performance_lines = list(performance_lines)
		work_count = 0
		work_tbbk = 0
		park_count = 0
		park_tbbk = 0
		down_count = 0
		down_tbbk = 0
		for idx, val in enumerate(performance_lines):
			if performance_lines[idx]['state'] == 'Working':
				work_tbbk += int(performance_lines[idx]['tbbk'])
				work_count += 1
			if performance_lines[idx]['state'] == 'Parking':
				park_tbbk += int(performance_lines[idx]['tbbk'])
				park_count += 1
			if performance_lines[idx]['state'] == 'Down':
				down_tbbk += int(performance_lines[idx]['tbbk'])
				down_count += 1
		if work_count > 0:
			summary = {
				'desc': 'Тухайн өдөр ажилласан техникийн бэлэн байдал, %',
				'tbbk': round(work_tbbk / work_count, 2),
				'cell_type': 'working'
			}
			performance_lines.insert(work_count, summary)
			work_count += 1
			park_count = work_count + park_count
		if park_count > 0:
			summary = {
				'desc':
				'Тухайн өдрийн түр зогсолттой техникүүдийн бэлэн байдал, %',
				'tbbk': round(park_tbbk / park_count, 2),
				'cell_type': 'parking'
			}
			performance_lines.insert(park_count, summary)
			park_count += 1
			down_count = park_count + down_count
		if down_count > 0:
			summary = {
				'desc': 'Удаан зогсолттой техникийн бэлэн байдал, %',
				'tbbk': round(down_tbbk / down_count, 2),
				'cell_type': 'down'
			}
			performance_lines.insert(down_count, summary)
		total_summary = work_tbbk + park_tbbk + down_tbbk
		total_tbbk = total_summary / len(
			performance_lines) if total_summary > 0 else 0
		summary = {
			'desc': 'Тухайн өдрийн нийт техникийн бэлэн байдал, %',
			'tbbk': round(total_tbbk, 2),
			'cell_type': 'total'
		}
		performance_lines.insert(len(performance_lines), summary)
		datas['performance_lines'] = performance_lines or False
		return datas

	def excel_report(self):
		datas = self.get_datas(self.date_start.strftime("%Y-%m-%d"),
							   self.date_end.strftime("%Y-%m-%d"),
							   self.branch_id)
		datas = datas['plan_lines']
		if datas:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Төлөвлөгөө %s-аас %s.xlsx' % (self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#00cc99')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			contest_work = workbook.add_format()
			contest_work.set_text_wrap()
			contest_work.set_font_size(9)
			contest_work.set_align('center')
			contest_work.set_align('vcenter')
			contest_work.set_border(style=1)
			contest_work.set_bg_color('#339966')

			contest_short = workbook.add_format()
			contest_short.set_text_wrap()
			contest_short.set_font_size(9)
			contest_short.set_align('center')
			contest_short.set_align('vcenter')
			contest_short.set_border(style=1)
			contest_short.set_bg_color('#ff9933')

			contest_long = workbook.add_format()
			contest_long.set_text_wrap()
			contest_long.set_font_size(9)
			contest_long.set_align('center')
			contest_long.set_align('vcenter')
			contest_long.set_border(style=1)
			contest_long.set_bg_color('#ac3939')

			contest_total = workbook.add_format()
			contest_total.set_text_wrap()
			contest_total.set_font_size(9)
			contest_total.set_align('center')
			contest_total.set_align('vcenter')
			contest_total.set_border(style=1)
			contest_total.set_bg_color('#808080')

			yellow_bg = workbook.add_format()
			yellow_bg.set_bg_color('#fcba03')
			yellow_bg.set_text_wrap()
			yellow_bg.set_font_size(9)
			yellow_bg.set_align('center')
			yellow_bg.set_align('vcenter')
			yellow_bg.set_border(style=1)

			green_bg = workbook.add_format()
			green_bg.set_bg_color('#17fc03')
			green_bg.set_text_wrap()
			green_bg.set_font_size(9)
			green_bg.set_align('center')
			green_bg.set_align('vcenter')
			green_bg.set_border(style=1)
			
			red_bg = workbook.add_format()
			red_bg.set_bg_color('#f0390c')
			red_bg.set_text_wrap()
			red_bg.set_font_size(9)
			red_bg.set_align('center')
			red_bg.set_align('vcenter')
			red_bg.set_border(style=1)
			
			blue_bg = workbook.add_format()
			blue_bg.set_bg_color('#030dfc')
			blue_bg.set_text_wrap()
			blue_bg.set_font_size(9)
			blue_bg.set_align('center')
			blue_bg.set_align('vcenter')
			blue_bg.set_border(style=1)
			
			pink_bg = workbook.add_format()
			pink_bg.set_bg_color('#ff17c1')
			pink_bg.set_text_wrap()
			pink_bg.set_font_size(9)
			pink_bg.set_align('center')
			pink_bg.set_align('vcenter')
			pink_bg.set_border(style=1)

			purple_bg = workbook.add_format()
			purple_bg.set_bg_color('#872b7e')
			purple_bg.set_text_wrap()
			purple_bg.set_font_size(9)
			purple_bg.set_align('center')
			purple_bg.set_align('vcenter')
			purple_bg.set_border(style=1)

			none_bg = workbook.add_format()
			none_bg.set_bg_color('#FFFFFF')
			none_bg.set_text_wrap()
			none_bg.set_font_size(9)
			none_bg.set_align('center')
			none_bg.set_align('vcenter')
			none_bg.set_border(style=1)

			waiting_bg = workbook.add_format()
			waiting_bg.set_bg_color('#611db8')
			waiting_bg.set_text_wrap()
			waiting_bg.set_font_size(9)
			waiting_bg.set_align('center')
			waiting_bg.set_align('vcenter')
			waiting_bg.set_border(style=1)

			worksheet = workbook.add_worksheet(u'Төлөвлөгөө')
			worksheet.set_zoom(80)
			row = 1
			col = 4
			worksheet.write(0, 2, u"Төлөвлөгөө", h1)
			worksheet.set_row(1, 30)
			worksheet.write(row, 0, u'Загвар', header_wrap)
			worksheet.set_column(0, 0, 30)
			worksheet.write(row, 1, u'Парк дугаар',header_wrap)
			worksheet.set_column(1, 1, 20)
			worksheet.write(row, 2, u'Сериал', header_wrap)
			worksheet.set_column(2, 2, 20)
			row = 2
			col = 3
			count = []
			for line in datas:
				worksheet.write(row, 0, line['model_name'], contest_center)
				worksheet.write(row, 1, line['park_number'],contest_center)
				worksheet.write(row, 2, line['vin_number'], contest_center)
				for key in line['plans']:
					if key['plan_date'] not in count:
						worksheet.write(1, col, key['plan_date'], header_wrap)
						count.append(key['plan_date'])
						col += 1
				col = 3
				for aa in line['plans']:
					main_cont = contest_center
					if 'color' in aa.keys():
						if aa['color'] == False:
							main_cont = pink_bg
						elif aa['color'] == '#fcba03' or aa['color'] == '#ebc660' or aa['color'] == 'rgba(252,227,3,1)':
							main_cont = yellow_bg
						elif aa['color'] == '#f0390c':
							main_cont = red_bg
						elif aa['color'] == 'rgba(3,252,59,1)' or aa['color'] == '#17fc03' or aa['color'] == 'rgba(252,186,3,1)' or aa['color'] == 'rgba(252,227,3,1)':
							main_cont = green_bg
						elif aa['color'] == '#030dfc':
							main_cont = blue_bg
						elif aa['color'] == '#872b7e':
							main_cont = purple_bg
						elif aa['color'] == '#611db8':
							main_cont = waiting_bg
					else:
						main_cont = none_bg
					worksheet.write(row, col, aa['work_time'] or '', main_cont)
					col += 1
				row += 1
			col += 1
			row = 1
			worksheet.write(row, col-1, u'Ажиллавал зохих цаг', header_wrap)
			worksheet.write(row, col, u'Төлөвлөгөөт засварын цаг', header_wrap)
			worksheet.write(row, col+1, u'Сэлбэг эд анги, дугуй хүлээлтийн цаг', header_wrap)
			worksheet.write(row, col+2, u'Төлөвлөгөөт бус засварын цаг', header_wrap)
			worksheet.write(row, col+3, u'ТББК', header_wrap)
			row += 1
			for line in datas:
				worksheet.write(row, col-1, line['norm_motoh'], contest_center)
				worksheet.write(row, col, line['planned_time'], contest_center)
				worksheet.write(row, col+1, line['parts_waiting_time'], contest_center)
				worksheet.write(row, col+2, line['unplanned_time'], contest_center)
				worksheet.write(row, col+3, line['tbbk'], contest_center)
				row += 1
			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({
				'data': out,
				'name': file_name
			})
			return {
				'type':
				'ir.actions.act_url',
				'url':
				"web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"
				% (excel_id.id, excel_id.name),
				'target':
				'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))
		
	def export_report(self):
		datas = self.get_datas(self.date_start.strftime("%Y-%m-%d"),
							   self.date_end.strftime("%Y-%m-%d"),
							   self.branch_id)
		datas = datas['performance_lines']
		if datas:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Daily info %s.xlsx' % (
				self.date_end.strftime('%Y-%m-%d'))

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#00cc99')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			contest_work = workbook.add_format()
			contest_work.set_text_wrap()
			contest_work.set_font_size(9)
			contest_work.set_align('center')
			contest_work.set_align('vcenter')
			contest_work.set_border(style=1)
			contest_work.set_bg_color('#339966')

			contest_short = workbook.add_format()
			contest_short.set_text_wrap()
			contest_short.set_font_size(9)
			contest_short.set_align('center')
			contest_short.set_align('vcenter')
			contest_short.set_border(style=1)
			contest_short.set_bg_color('#ff9933')

			contest_long = workbook.add_format()
			contest_long.set_text_wrap()
			contest_long.set_font_size(9)
			contest_long.set_align('center')
			contest_long.set_align('vcenter')
			contest_long.set_border(style=1)
			contest_long.set_bg_color('#ac3939')

			contest_total = workbook.add_format()
			contest_total.set_text_wrap()
			contest_total.set_font_size(9)
			contest_total.set_align('center')
			contest_total.set_align('vcenter')
			contest_total.set_border(style=1)
			contest_total.set_bg_color('#808080')

			worksheet = workbook.add_worksheet(u'Daily Info')
			worksheet.set_zoom(80)
			worksheet.write(
				0, 2, u"%s оны %s-р сарын %s-ний өдрийн засварын мэдээ" %
				(self.date_end.year, self.date_end.month, self.date_end.day),
				h1)

			row = 1
			worksheet.set_row(1, 30)
			worksheet.merge_range(row, 0, row + 1, 0,
								  u'Parking number'.upper(), header_wrap)
			worksheet.set_column(0, 0, 10)
			# worksheet.write(row, 0, u'Parking number', header_wrap)
			worksheet.merge_range(row, 1, row + 1, 1, u'Type'.upper(),
								  header_wrap)
			worksheet.set_column(1, 1, 30)
			# worksheet.write(row, 1, u'Type', header_wrap)
			worksheet.merge_range(row, 2, row + 1, 2, u'Serial'.upper(),
								  header_wrap)
			worksheet.set_column(2, 2, 20)
			# worksheet.write(row, 2, u'Serial', header_wrap)
			worksheet.merge_range(row, 3, row, 4, u'Moto hours'.upper(),
								  header_wrap)
			# worksheet.set_column(3, 4, 20)
			# worksheet.write(row, 3, u'Moto hours', header_wrap)
			# worksheet.merge_range(row+1, 3,row+1, 3, u'Start', header_wrap)
			worksheet.write(row + 1, 3, u'Start'.upper(), header_wrap)
			# worksheet.set_column(3, 3, 10)
			# worksheet.merge_range(row+1, 4,row+1, 4, u'Finish', header_wrap)
			worksheet.write(row + 1, 4, u'Finish'.upper(), header_wrap)
			# worksheet.set_column(4, 4, 10)
			# worksheet.write(row, 4, u'Finish', header_wrap)
			worksheet.merge_range(row, 5, row + 1, 5, u'Work hours'.upper(),
								  header_wrap)
			worksheet.set_column(5, 5, 10)
			# worksheet.write(row, 5, u'Work hours', header_wrap)
			worksheet.merge_range(row, 6, row + 1, 6, u'Down hours'.upper(),
								  header_wrap)
			worksheet.set_column(6, 6, 10)
			# worksheet.write(row, 6, u'Down hours', header_wrap)
			worksheet.merge_range(row, 7, row + 1, 7, u'Worked hours'.upper(),
								  header_wrap)
			worksheet.set_column(7, 7, 10)
			# worksheet.write(row, 7, u'Worked hours', header_wrap)
			worksheet.merge_range(row, 8, row + 1, 8,
								  u'Daily availability'.upper(), header_wrap)
			worksheet.set_column(8, 8, 10)
			# worksheet.write(row, 8, u'Daily availability', header_wrap)
			worksheet.merge_range(row, 9, row + 1, 9, u'Status'.upper(),
								  header_wrap)
			worksheet.set_column(9, 9, 10)
			# worksheet.write(row, 9, u'Status', header_wrap)
			worksheet.merge_range(row, 10, row + 1, 10, u'Daily jobs'.upper(),
								  header_wrap)
			worksheet.set_column(10, 10, 60)
			# worksheet.write(row, 10, u'Daily jobs', header_wrap)
			col = 8
			rr = row + 2
			for line in datas:
				if 'park_number' not in line.keys():
					contest_summary = contest_center
					if line['cell_type'] == 'working':
						contest_summary = contest_work
						worksheet.merge_range(rr, 0, rr, 7, line['desc'],
											  contest_summary)
						worksheet.write(rr, 8,
										str(line['tbbk']) + '%',
										contest_summary)
						# worksheet.merge_range(rr, 8,rr, 8, str(line['tbbk'])+'%', contest_summary)
						worksheet.merge_range(rr, 9, rr, 10, '',
											  contest_summary)
						# worksheet.set_column(0, 7, 10)
					elif line['cell_type'] == 'down':
						contest_summary = contest_long
						worksheet.merge_range(rr, 0, rr, 6, line['desc'],
											  contest_summary)
						# worksheet.write(rr, 7, str(line['tbbk'])+'%', contest_summary)
						worksheet.merge_range(rr, 7, rr, 8,
											  str(line['tbbk']) + '%',
											  contest_summary)
						worksheet.merge_range(rr, 9, rr, 10, '',
											  contest_summary)
					elif line['cell_type'] == 'total':
						contest_summary = contest_total
						worksheet.merge_range(rr, 0, rr, 6, line['desc'],
											  contest_summary)
						# worksheet.write(rr, 7, str(line['tbbk'])+'%', contest_summary)
						worksheet.merge_range(rr, 7, rr, 8,
											  str(line['tbbk']) + '%',
											  contest_summary)
						worksheet.merge_range(rr, 9, rr, 10, '',
											  contest_summary)
					else:
						contest_summary = contest_short
						worksheet.merge_range(rr, 0, rr, 6, line['desc'],
											  contest_summary)
						# worksheet.write(rr, 7, str(line['tbbk'])+'%', contest_summary)
						worksheet.merge_range(rr, 7, rr, 8,
											  str(line['tbbk']) + '%',
											  contest_summary)
						worksheet.merge_range(rr, 9, rr, 10, '',
											  contest_summary)
					# worksheet.write(rr, 0, line['desc'], contest_summary)
					# worksheet.write(rr, 1, line['tbbk'], contest_summary)
					rr += 1
					continue
				worksheet.write(rr, 0, line['park_number'], contest_center)
				worksheet.write(rr, 1, line['type'], contest_center)
				worksheet.write(rr, 2, line['serial'], contest_center)
				worksheet.write(rr, 3, line['start'], contest_center)
				worksheet.write(rr, 4, line['finish'], contest_center)
				if line['state'] == 'Working':
					worksheet.write(rr, 5, line['work_hours'], contest_center)
					worksheet.write(rr, 6, line['down_hours'], contest_center)
					worksheet.write(rr, 7, line['worked_hours'],
									contest_center)
					worksheet.write(rr, 8, line['tbbk'], contest_center)
				else:
					worksheet.merge_range(rr, 5, rr, 6, line['work_hours'],
										  contest_center)
					worksheet.merge_range(rr, 7, rr, 8,
										  str(line['tbbk']) + '%',
										  contest_center)
				worksheet.write(rr, 9, line['state'], contest_center)
				worksheet.write(rr, 10, line['daily_jobs'], contest_center)
				rr += 1
			# =============================
			# pdf = workbook.save("xlsx-to-pdf.pdf", SaveFormat.PDF)
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({
				'data': out,
				'name': file_name
			})
			return {
				'type':
				'ir.actions.act_url',
				'url':
				"web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"
				% (excel_id.id, excel_id.name),
				'target':
				'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))

	def export_report_pdf(self):
		html = self.export_report_html_value()
		file_name = u"%s оны %s-р сарын %s-ний өдрийн засварын мэдээ" % (
			self.date_end.year, self.date_end.month, self.date_end.day)
		options = {
			'margin-top': '0mm',
			'margin-right': '0mm',
			'margin-bottom': '0mm',
			'margin-left': '0mm',
			'encoding': "UTF-8",
			'header-spacing': 5,
			'orientation': 'Portrait',
		}
		output = BytesIO(pdfkit.from_string(html, False, options=options))
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({
			'data': out,
			'name': file_name
		})
		return {
			'type':'ir.actions.act_url',
			'url':"web/content/?model=report.excel.output&id=" + str(excel_id.id) +"&filename_field=filename&download=true&field=data&filename=" +excel_id.name,
			'target':'new',
		}

	def export_report_html_value(self):
		datas = self.get_datas(self.date_start.strftime("%Y-%m-%d"), self.date_end.strftime("%Y-%m-%d"), self.branch_id)
		datas = datas['performance_lines']
		rows_work = ""
		rows_short = ""
		rows_long = ""
		for item in datas:
			if item.get('state', False) == 'Working':
				data = """<tr>
				<td style="border: 1px solid #000000;" align="center" valign="middle" height="20"><span style="color: #000000;">{0}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{1}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{2}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{3}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{4}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{5}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{6}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{7}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{8}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{9}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{10}</span></td></tr>
				""".format(item['park_number'], item['type'], item['serial'], item['start'], item['finish'], item['work_hours'], item['down_hours'], item['worked_hours'], item['tbbk'], item['state'], item['daily_jobs'])
				rows_work += data
			if item.get('state', False) == 'Parking':
				data = """<tr>
				<td style="border: 1px solid #000000;" align="center" valign="middle" height="20"><span style="color: #000000;">{0}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{1}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{2}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{3}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{4}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{5}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{6}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{7}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{8}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{9}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{10}</span></td></tr>
				""".format(item['park_number'], item['type'], item['serial'], item['start'], item['finish'], item['work_hours'], item['down_hours'], item['worked_hours'], item['tbbk'], item['state'], item['daily_jobs'])
				rows_short += data
			if item.get('state', False) == 'Down':
				data = """<tr>
				<td style="border: 1px solid #000000;" align="center" valign="middle" height="20"><span style="color: #000000;">{0}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{1}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{2}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{3}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{4}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{5}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{6}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{7}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{8}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{9}</span></td>
				<td style="border: 1px solid #000000;" align="center" valign="middle"><span style="color: #000000;">{10}</span></td></tr>
				""".format(item['park_number'], item['type'], item['serial'], item['start'], item['finish'], item['work_hours'], item['down_hours'], item['worked_hours'], item['tbbk'], item['state'], item['daily_jobs'])
				rows_long += data
		html = """
		<!DOCTYPE HTML>
				<html lang="en-US">
				<body><table style="font-family: Calibri; font-size: x-small;" border="0" cellspacing="0">
						<colgroup width="100"></colgroup>
						<colgroup width="287"></colgroup>
						<colgroup width="193"></colgroup>
						<colgroup span="2" width="80"></colgroup>
						<colgroup span="5" width="100"></colgroup>
						<colgroup width="567"></colgroup>
						<tbody><tr>
							<td colspan="2" align="left" valign="bottom" height="20"><span style="color: #000000;">&nbsp;</span></td>
							<td colspan="8" align="left" valign="bottom"><strong><span style="color: #000000; font-size: medium;">{3} оны {4}-р сарын {5}-ний өдрийн засварын мэдээ</span></strong></td>
							<td colspan="1" align="left" valign="bottom"><span style="color: #000000;">&nbsp;</span></td></tr>
							<tr>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99" height="60">
									<strong>PARKING NUMBER</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>TYPE</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>SERIAL</strong>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>MOTO HOURS</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>WORK HOURS</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>DOWN HOURS</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>WORKED HOURS</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>DAILY AVAILABILITY</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>STATUS</strong>
								</td>
								<td style="border: 1px solid #000000;" rowspan="2" align="center" valign="middle" bgcolor="#00CC99">
									<strong>DAILY JOBS</strong>
								</td>
							</tr>
							<tr>
								<td style="border: 1px solid #000000;" align="center" valign="middle" bgcolor="#00CC99">
									<strong>START</strong>
								</td>
								<td style="border: 1px solid #000000;" align="center" valign="middle" bgcolor="#00CC99">
									<strong>FINISH</strong>
								</td>
							</tr>
							{0}
							<tr>
								<td style="border: 1px solid #000000;" colspan="8" align="center" valign="middle" bgcolor="#339966" height="20">
									<span style="color: #000000;">Тухайн өдөр ажилласан техникийн бэлэн байдал, %</span>
								</td>
								<td style="border: 1px solid #000000;" align="center" valign="middle" bgcolor="#339966">
									<span style="color: #000000;">71.11%</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#339966">
									<span style="color: #000000;">&nbsp;</span>
								</td>
							</tr>
							{1}
							<tr>
								<td style="border: 1px solid #000000;" colspan="7" align="center" valign="middle" bgcolor="#FF9933" height="20">
									<span style="color: #000000;">Тухайн өдрийн түр зогсолттой техникүүдийн бэлэн байдал, %</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#FF9933">
									<span style="color: #000000;">0.0%</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#FF9933">
									<span style="color: #000000;">&nbsp;</span>
								</td>
							</tr>
							{2}
							<tr>
								<td style="border: 1px solid #000000;" colspan="7" align="center" valign="middle" bgcolor="#AC3939" height="20">
									<span style="color: #000000;">Удаан зогсолттой техникийн бэлэн байдал, %</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#AC3939">
									<span style="color: #000000;">0.0%</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#AC3939">
									<span style="color: #000000;">&nbsp;</span>
								</td>
							</tr>
							<tr>
								<td style="border: 1px solid #000000;" colspan="7" align="center" valign="middle" bgcolor="#808080" height="20">
									<span style="color: #000000;">Тухайн өдрийн нийт техникийн бэлэн байдал, %</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#808080">
									<span style="color: #000000;">10.67%</span>
								</td>
								<td style="border: 1px solid #000000;" colspan="2" align="center" valign="middle" bgcolor="#808080">
									<span style="color: #000000;">&nbsp;</span>
								</td>
							</tr>
						</tbody>
					</table>
				</body>
			</html>
		""".format(rows_work, rows_short, rows_long, self.date_end.year, self.date_end.month, self.date_end.day)
		return html

	def send_mail(self, html=False):
		html = self.export_report_html_value()
		file_name = u"%s оны %s-р сарын %s-ний өдрийн засварын мэдээ" % (self.date_end.year, self.date_end.month, self.date_end.day)
		options = {
			'margin-top': '0mm',
			'margin-right': '0mm',
			'margin-bottom': '0mm',
			'margin-left': '0mm',
			'encoding': "UTF-8",
			'header-spacing': 5,
			'orientation': 'Portrait',
		}
		output = BytesIO(pdfkit.from_string(html, False, options=options))
		out = base64.encodebytes(output.getvalue())
		# excel_id = self.env['report.excel.output'].create({
		# 	'data': out,
		# 	'name': file_name
		# })
		att_id = self.env['ir.attachment'].create({
			'name': file_name,
			'type': 'binary',
			'datas': out,
			'res_model':'maintenance.dashboard.03',
			'res_id': self.id,
		})
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_dashboard_03')[2]
		html = u"""<b><a target="_blank" href=%s/web#id=%s&action=%s&model=maintenance.dashboard.03&view_type=form&cids=&menu_id=253></a>%s-аас %s дахь Daily info</b>"""%(base_url,self.id,action_id,self.date_start,self.date_end)
		if self.partner_id:
			# self.env.user.send_chat(html, self.partner_id, True, attachment_ids=[att_id.id])
			self.env.user.send_emails(partners=partner_id, body=html, attachment_ids=[att_id.id])