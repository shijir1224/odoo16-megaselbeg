# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, tools
# from odoo.exceptions import UserError, ValidationError
# from datetime import datetime, time, timedelta
# from dateutil.relativedelta import relativedelta

class maintenanceWorkorder(models.Model):
	_inherit = 'maintenance.workorder'
	equipment_id = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж')
	# first_hour = fields.Float(string='Тоног төхөөрөмжийн засвар хийх үеийн цаг')
	# last_hour = fields.Float(string='Тоног төхөөрөмжийн засвар дууссан үеийн цаг')
	equipment_status = fields.Boolean('Тоног төхөөрөмжийн төлөвт нөлөөлөх эсэх')
	damaged_type_ids = fields.Many2one('maintenance.damaged.type', string=u'Эвдэрсэн эд анги', copy=False,
		states={'closed': [('readonly', True)]})
class MaintenanceCall(models.Model):
	_inherit = 'maintenance.call'

	equipment_call = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж')

class maintenancePmMaterialConfig(models.Model):
	_inherit = 'maintenance.pm.material.config'

	equipment_setting_id = fields.Many2one('factory.equipment.setting', string="Equipment setting")

	@api.depends('technic_setting_id','technic_setting_id.odometer_unit','equipment_setting_id','equipment_setting_id.odometer_unit','equipment_setting_id.is_plan_by_time')
	def _compute_interval_uom(self):
		for item in self:
			if item.technic_setting_id:
				item.interval_uom = dict(item.equipment_setting_id._fields['odometer_unit'].selection).get(item.equipment_setting_id.odometer_unit)
			else:
				item.interval_uom = False
			if item.equipment_setting_id:
				item.interval_uom = dict(item.equipment_setting_id._fields['odometer_unit'].selection).get(item.equipment_setting_id.odometer_unit)
			else:
				item.interval_uom = False
			if item.equipment_setting_id.is_plan_by_time:
				item.interval_uom = 'Хоног'

class MaintenancePartsWaiting(models.Model):
	_inherit = 'maintenance.parts.waiting'

	equipment_parts_waiting = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж')


class MaintenanceEmployeeTimesheetLineinherit(models.Model):
	_inherit = 'maintenance.employee.timesheet.line'

	# Columns
	equipment_id = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж')
	employee_ids = fields.Many2many('hr.employee','employee_ids_partner', string=u'Засварчин', required=True, )

class MaintenanceEmployeeOtherTimesheet(models.Model):
	_inherit = 'maintenance.employee.other.timesheet'

	# Columns
	equipment_id = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж')
	damaged_type_ids = fields.Many2one('maintenance.damaged.type', string=u'Эвдэрсэн эд анги', copy=False,
		states={'closed': [('readonly', True)]})