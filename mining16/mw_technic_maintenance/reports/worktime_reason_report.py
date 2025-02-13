# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE

class WorktimeReasonReport(models.Model):
	_name = "worktime.reason.report"
	_description = "Worktime reason report"
	_auto = False
	_order = 'technic_id'

	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True,  )
	date = fields.Datetime(u'Огноо', readonly=True, )
	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
		string=u'Maintenance type', readonly=True, )
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, )
	wo_id = fields.Many2one('maintenance.workorder', string=u'Workorder', readonly=True, )
	reason_id = fields.Many2one('maintenance.delay.reason', string='Шалтгаан', readonly=True, )
	spend_time = fields.Float(string=u'Зарцуулсан цаг', readonly=True, )
	is_rework = fields.Selection([
		('normal', u'Хэвийн'),
		('rework', u'ReWork'),],
		string='ReWork эсэх', readonly=True, )
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				wo.branch_id as branch_id,
				ll.id as id,
				wo.id as wo_id,
				ll.date_start as date,
				wo.maintenance_type as maintenance_type,
				wo.technic_id as technic_id,
				ll.spend_time as spend_time,
				ll.delay_reason_id as reason_id,
				(CASE WHEN wo.is_rework = 't' THEN 'rework' ELSE 'normal' END) as is_rework
			FROM maintenance_work_timesheet_line as ll
			LEFT JOIN maintenance_workorder as wo on wo.id = ll.parent_id
			WHERE wo.state = 'closed'
			
		)""" % self._table)