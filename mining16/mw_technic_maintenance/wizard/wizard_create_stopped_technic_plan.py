# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import time

import logging
_logger = logging.getLogger(__name__)


class WizardCreateStoppedTechnicPlan(models.TransientModel):
	_name = 'wizard.create.stopped.technic.plan'
	_description = 'wizard.create.stopped.technic.plan'

	# Columns
	date_start = fields.Date(u'Эхлэх огноо', copy=False, required=True)
	date_end = fields.Date(u'Дуусах огноо', copy=False, required=True)

	technic_id = fields.Many2one('technic.equipment', string=u'Техник',
								 domain=[('state', '!=', 'draft'), ('owner_type', '=', 'own_asset')])
	stopped_time = fields.Float(
		string=u'Зогсох цаг', default=0, required=True, )

	description = fields.Char(u'Тайлбар', copy=False, )

	stop_type = fields.Selection([
		('planned_stop', u'Сэлбэг хүлээлт, зогсолт'),
		('daily_stop', u'Өдөр тутмын'),
		('create_plan', u'Төлөвлөгөө үүсгэх'), ],
		string='Зогсолтын төрөл', required=True,)
	maintenance_type_id = fields.Many2one('maintenance.type', string='Зогсолтын төрөл', copy=False,
		domain=['|',('is_waiting_part','=',True),('is_waiting_tire','=',True)], ) 
	shift = fields.Selection([
		('day', u'Өдөр'),
		('night', u'Шөнө'), ], string=u'Ээлж',)

	@api.onchange('date_start','date_end')
	def onchange_stopped_time(self):
		for item in self:
			if item.date_end and item.date_start:
				days = (item.date_end - item.date_start).days + 1
				item.stopped_time = days * 24
			else:
				item.stopped_time = 0

	def create_plans(self):
		if self.date_start <= self.date_end:
			# Төлөвлөгөөт зогсолт бол
			if self.stop_type == 'planned_stop':
				# Цаггүй бол
				stopped_time = 0
				if self.stopped_time > 0:
					stopped_time = self.stopped_time
				else:
					stopped_time = 100000

				temp_date = self.date_start
				temp = 0
				# 10 цаг буюу 1 ээлжинд багтах эсэх
				shift_hour = self.technic_id.technic_setting_id.work_time_per_day / 2
				# Дуусах огноо хүртэл давтана
				while temp_date <= self.date_end and stopped_time > 0:
					# Өдрийн ПЛАН үүсгэх
					if stopped_time >= shift_hour:
						temp = shift_hour
					else:
						temp = stopped_time
					vals = {
						'branch_id': self.technic_id.branch_id.id,
						'origin': 'Generated: Stop plan',
						'maintenance_type_id': self.maintenance_type_id.id,
						'pm_priority': 0,
						'maintenance_type': 'stopped',
						'contractor_type': 'internal',
						'date_required': temp_date,
						'technic_id': self.technic_id.id,
						'start_odometer': 0,
						'work_time': temp,
						'description': self.description if self.description else u'Зогсолт',
						'shift': 'day',
					}
					plan = self.env['maintenance.plan.line'].create(vals)
					print('====plan', plan.id)
					plan.action_to_confirm()
					stopped_time -= shift_hour
					# Техникийг зогсоох
					self.technic_id.action_to_stop()

					# Хэрэв үлдэгдэл цаг байвал шөнийн ПЛАН  үүсгэнэ
					if stopped_time > 0:
						if stopped_time >= shift_hour:
							temp = shift_hour
						else:
							temp = stopped_time

						vals = {
							'branch_id': self.technic_id.branch_id.id,
							'origin': 'Generated: Stop plan',
							'maintenance_type_id': self.maintenance_type_id.id,
							'pm_priority': 0,
							'maintenance_type': 'stopped',
							'contractor_type': 'internal',
							'date_required': temp_date,
							'technic_id': self.technic_id.id,
							'start_odometer': 0,
							'work_time': temp,
							'description': self.description if self.description else u'Зогсолт',
							'shift': 'night',
						}
						plan = self.env['maintenance.plan.line'].create(vals)
						plan.action_to_confirm()
						stopped_time -= shift_hour
						# Техникийг зогсоох
						self.technic_id.action_to_stop()
					# Next
					temp_date = self._date_increase(temp_date, 1)
			# Өдөр тутмын зогсолт бол
			elif self.stop_type == 'daily_stop':
				stopped_time = self.stopped_time if self.stopped_time else 0.5
				technics = False
				if not self.technic_id:
					technics = self.env['technic.equipment'].search([
						('state', 'in', ['working', 'repairing', 'stopped']),
						('owner_type', '=', 'own_asset'),
						('is_tbb_report', '=', True)])
				else:
					technics = [self.technic_id]

				_logger.info("---technics ====== %d", len(technics))
				for technic in technics:
					temp_date = self.date_start
					# Дуусах огноо хүртэл давтана
					while temp_date <= self.date_end:
						_logger.info("---d1 d2 ====== %s, %s ",
									 temp_date, self.date_end)
						# Төлөвлөгөө байгаа эсэхийг шалгах - Өдөр
						plans = self.env['maintenance.plan.line'].search([
							('state', '!=', 'draft'),
							('shift', '=', 'day'),
							('technic_id', '=', technic.id),
							('date_required', '=', temp_date)])
						# Хэрэв техникийн план байвал зогсолт үүсгэхгүй
						# Байхгүй бол үүсгэнэ
						if not plans:
							# Өдрийн ПЛАН үүсгэх
							vals = {
								'branch_id': technic.branch_id.id,
								'origin': 'Generated: INSPECTION',
								'pm_priority': 0,
								'maintenance_type': 'stopped',
								'contractor_type': 'internal',
								'date_required': temp_date,
								'technic_id': technic.id,
								'start_odometer': 0,
								'work_time': stopped_time,
								'description': self.description if self.description else u'INSPECTION',
								'shift': 'day',
							}
							plan = self.env['maintenance.plan.line'].create(
								vals)
							plan.action_to_confirm()

						# Төлөвлөгөө байгаа эсэхийг шалгах - Шөнө
						plans = self.env['maintenance.plan.line'].search([
							('state', '!=', 'draft'),
							('shift', '=', 'night'),
							('technic_id', '=', technic.id),
							('date_required', '=', temp_date)])
						if not plans:
							# Шөнийн ПЛАН үүсгэх
							vals = {
								'branch_id': technic.branch_id.id,
								'origin': 'Generated: INSPECTION',
								'pm_priority': 0,
								'maintenance_type': 'stopped',
								'contractor_type': 'internal',
								'date_required': temp_date,
								'technic_id': technic.id,
								'start_odometer': 0,
								'work_time': stopped_time,
								'description': self.description if self.description else u'INSPECTION',
								'shift': 'night',
							}
							plan = self.env['maintenance.plan.line'].create(
								vals)
							plan.action_to_confirm()
						# Next
						temp_date = self._date_increase(temp_date, 1)

			# Төлөвлөгөө үүсгэх бол
			elif self.stop_type == 'create_plan':
				# Цаггүй бол
				stopped_time = 0
				if self.stopped_time > 0:
					stopped_time = self.stopped_time
				else:
					stopped_time = 100000

				temp_date = self.date_start
				temp = 0
				# 10 цаг буюу 1 ээлжинд багтах эсэх
				shift_hour = self.technic_id.technic_setting_id.work_time_per_day / 2
				ref_plan = False
				start_shift = self.shift
				# Дуусах огноо хүртэл давтана
				while temp_date <= self.date_end and stopped_time > 0:
					# Өдрийн ээлжнээс эхлэх эсэх
					if start_shift == 'day':
						# Өдрийн ПЛАН үүсгэх
						if stopped_time >= shift_hour:
							temp = shift_hour
						else:
							temp = stopped_time

						# Тухайн өдөр төлөвлөгөө байгаа эсэхийг шалгах
						# Байвал үлдэгдэл цагийг олох
						plans = self.env['maintenance.plan.line'].search([
							('state', '!=', 'draft'),
							('shift', '=', 'day'),
							('technic_id', '=', self.technic_id.id),
							('date_required', '=', temp_date)])
						planned_time = sum(plans.mapped('work_time')) or 0
						if temp == shift_hour:
							temp -= planned_time
						else:
							if (temp+planned_time) > shift_hour:
								temp = shift_hour-planned_time

						vals = {
							'branch_id': self.technic_id.branch_id.id,
							'origin': 'Generated: Plan',
							'pm_priority': 0,
							'maintenance_type': 'planned',
							'contractor_type': 'internal',
							'date_required': temp_date,
							'technic_id': self.technic_id.id,
							'start_odometer': 0,
							'work_time': temp,
							'description': self.description if self.description else u'Зогсолт',
							'shift': 'day',
							'ref_plan_id': ref_plan,
						}
						plan = self.env['maintenance.plan.line'].create(vals)
						plan.action_to_confirm()
						ref_plan = plan.id
						stopped_time -= (shift_hour-planned_time)

					# Хэрэв үлдэгдэл цаг байвал шөнийн ПЛАН  үүсгэнэ
					if stopped_time > 0:
						if stopped_time >= shift_hour:
							temp = shift_hour
						else:
							temp = stopped_time

						# Тухайн өдөр төлөвлөгөө байгаа эсэхийг шалгах
						# Байвал үлдэгдэл цагийг олох
						plans = self.env['maintenance.plan.line'].search([
							('state', '!=', 'draft'),
							('shift', '=', 'night'),
							('technic_id', '=', self.technic_id.id),
							('date_required', '=', temp_date)])
						planned_time = sum(plans.mapped('work_time')) or 0
						if temp == shift_hour:
							temp -= planned_time
						else:
							if (temp+planned_time) > shift_hour:
								temp = shift_hour-planned_time

						vals = {
							'branch_id': self.technic_id.branch_id.id,
							'origin': 'Generated: Plan',
							'pm_priority': 0,
							'maintenance_type': 'planned',
							'contractor_type': 'internal',
							'date_required': temp_date,
							'technic_id': self.technic_id.id,
							'start_odometer': 0,
							'work_time': temp,
							'description': self.description if self.description else u'Зогсолт',
							'shift': 'night',
							'ref_plan_id': ref_plan,
						}
						plan = self.env['maintenance.plan.line'].create(vals)
						plan.action_to_confirm()
						ref_plan = plan.id
						stopped_time -= (shift_hour-planned_time)

					# Next
					temp_date = self._date_increase(temp_date, 1)
					start_shift = 'day'

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, add):
		return temp_date + timedelta(days=add)
		
