# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE

class RepaimanPivotReport(models.Model):
	_name = "repaiman.pivot.report"
	_description = "Repairman report"
	_auto = False
	_order = 'employee_id'

	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True,  )
	date = fields.Date(u'WO огноо', readonly=True, )
	date_start = fields.Datetime(u'Эхэлсэн цаг', readonly=True, )
	date_end = fields.Datetime(u'Дууссан цаг', readonly=True, )

	employee_id = fields.Many2one('hr.employee', string=u'Засварчин', readonly=True,  )
	notes = fields.Char(string=u'Тайлбар', readonly=True, )
	spend_time = fields.Float(string=u'Зарцуулсан цаг', readonly=True, )
	workorder_id = fields.Many2one('maintenance.workorder', string=u'Холбоотой WO', readonly=True, )
	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
			string=u'Засварын төрөл', readonly=True, )
	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Эвдрэлийн Төрөл')
	work_type = fields.Selection([
			('call', u'Дуудлагын ажил'),
			('wo', u'WorkOrder'),
			('other', u'Бусад ажил')],
			string=u'Төрөл', readonly=True, )
	is_rework = fields.Selection([
		('normal', u'Хэвийн'),
		('rework', u'ReWork'),],
		string='ReWork эсэх', readonly=True, )
	mechanic_cause = fields.Selection([('shift_swap','Ээлж солилцох'),
										('break_time','Цайны цаг'),
										('naryd','Наряд'),
										('tire','Дугуй'),
										('welding','Гагнуур'),
										('inspection','Үзлэг'),
										('lubrication','Тосолгоо'),
										('training','Сургалт'),
										('site_cleaning','Талбайн цэвэрлэгээ'),
										('other_work','Бусад ажил')], string=u"Засварчны ажлын шалтгаан")
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, )
	status = fields.Char(string=u'Ажилтны статус', readonly=True, )

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
				SELECT
					wo.branch_id as branch_id,
					ll.id as id,
					wo.date_required as date,
					ll.employee_id as employee_id,
					(ll.date_start) as date_start,
					(ll.date_end) as date_end,
					(CASE WHEN ll.notes is not null THEN ll.notes ELSE wo.performance_description END) as notes,
					ll.spend_time as spend_time,
					ll.parent_id as workorder_id,
					null as call_id,
					wo.maintenance_type as maintenance_type,
					wo.damaged_type_id as damaged_type_id,
					wo.technic_id as technic_id,
					'wo' as work_type,
					(CASE WHEN wo.is_rework = 't' THEN 'rework' ELSE 'normal' END) as is_rework,
					null as mechanic_cause,
					''::varchar as status
				FROM maintenance_employee_timesheet_line as ll
				LEFT JOIN hr_employee as emp on emp.id = ll.employee_id
				LEFT JOIN maintenance_workorder as wo on wo.id = ll.parent_id
				WHERE wo.state not in ('draft','cancel')
				UNION ALL
				SELECT
					cl.branch_id as branch_id,
					ll.id as id,
					cl.date_required as date,
					ll.employee_id as employee_id,
					(ll.date_start) as date_start,
					(ll.date_end) as date_end,
					(CASE WHEN ll.notes is not null THEN ll.notes ELSE cl.performance_description END) as notes,
					ll.spend_time as spend_time,
					null as workorder_id,
					ll.parent_id_2 as call_id,
					'not_planned' as maintenance_type,
					cl.damaged_type_id as damaged_type_id,
					cl.technic_id as technic_id,
					'call' as work_type,
					null as is_rework,
					null as mechanic_cause,
					''::varchar as status
				FROM maintenance_employee_timesheet_line as ll
				LEFT JOIN hr_employee as emp on emp.id = ll.employee_id
				LEFT JOIN maintenance_call as cl on cl.id = ll.parent_id_2
				WHERE cl.state in ('closed')
				UNION ALL
				SELECT
					ru.branch_id as branch_id,
					ll.id as id,
					ll.date_start::date as date,
					ll.employee_id as employee_id,
					(ll.date_start) as date_start,
					(ll.date_end) as date_end,
					ll.notes as notes,
					ll.spend_time as spend_time,
					null as workorder_id,
					null as call_id,
					'daily_works' as maintenance_type,
					null as damaged_type_id,
					ll.technic_id as technic_id,
					'other' as work_type,
					null as is_rework,
					ll.mechanic_cause as mechanic_cause,
					''::varchar as status
				FROM maintenance_employee_timesheet_line as ll
				LEFT JOIN hr_employee as emp on emp.id = ll.employee_id
				LEFT JOIN res_users as ru on ru.id = emp.user_id
				WHERE ll.state2 in ('confirmed')
			)""" % self._table)
