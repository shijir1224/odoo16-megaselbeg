# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class TechnicLogStatusPivotReport(models.Model):
	_name = "technic.log.status.pivot.report"
	_description = "technic.log.status.pivot.report"
	_auto = False
	_order = 'technic_id'

	date_time = fields.Datetime(string=u'Эхэлсэн цаг', readonly=True, )
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, )
	odometer = fields.Float(string=u'Гүйлт', readonly=True, )
	work_time = fields.Float(string=u'Ажилласан цаг', readonly=True, )
	status_type = fields.Selection([
			('waiting_for_spare','Сэлбэг хүлээж зогссон'),
			('waiting_for_tire','Дугуй хүлээж зогссон'),
			('working','Ажиллаж байгаа'),
			('repairing','Засварт орсон'),
			('inspection','Үзлэг хийж байгаа'),
			('parking','Паркласан')], 
		string='Status', readonly=True, )

	current_status = fields.Selection([
			('current','Сүүлийн статус'),
			('not_current','Өмнөх')], 
		string='Сүүлийн статус', readonly=True, )

	note = fields.Text(string='Дэлгэрэнгүй тайлбар', readonly=True, )
	user_id = fields.Many2one('res.users', string=u'Бүртгэсэн', readonly=True,)
	before_id = fields.Many2one('technic.equipment.log.status', string=u'Өмнөх бүртгэл', )
	spend_time = fields.Float(string='Зарцуулсан цаг', readonly=True, digits=(16,2))
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				ll.id as id,
				ll.date_time as date_time,
				ll.technic_id as technic_id,
				ll.odometer as odometer,
				ll.work_time as work_time,
				ll.status_type as status_type,
				(CASE WHEN ll.is_last = 't' THEN 'current' ELSE 'not_current' END) as current_status,
				ll.before_id as before_id,
				before_ll.spend_time as spend_time,
				ll.user_id as user_id,
				ll.note as note
			FROM technic_equipment_log_status as ll
			LEFT JOIN technic_equipment_log_status as before_ll on (before_ll.id = ll.before_id)
			WHERE ll.state = 'confirmed'
		)""" % self._table)
