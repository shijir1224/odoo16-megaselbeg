# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class MaintenancePlanPivotReport(models.Model):
	_name = 'maintenance.plan.pivot.report'
	_description = 'Maintenance Plan Pivot Report'
	_auto = False
	_order = 'technic_id'

	date = fields.Date('Огноо', readonly=True)
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
		string=u'Ээлж', readonly=True)
	branch_id = fields.Many2one('res.branch', 'Салбар', readonly=True)
	technic_id = fields.Many2one('technic.equipment', 'Техник', readonly=True)
	owner_type = fields.Selection(OWNER_TYPE, 'Эзэмшлийн төлөв',readonly=True)
	technic_type = fields.Char('Техникийн төрөл', readonly=True)
	work_time = fields.Float('Төлөвлөсөн цаг', readonly=True)

	workorder_id = fields.Many2one('maintenance.workorder', 'Work Order', readonly=True)
	wo_work_time = fields.Float('Засварын цаг', readonly=True)

	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
		string=u'Maintenance type', readonly=True)
	maintenance_type_id = fields.Many2one('maintenance.type', 'Салбар', readonly=True)
	tbbk = fields.Float('ТББ %', readonly=True, group_operator="avg")

	
	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE or REPLACE view  %s as
	   	SELECT
					plan.id as id,
					plan.maintenance_type as maintenance_type,
					plan.maintenance_type_id as maintenance_type_id,
					plan.workorder_id as workorder_id,
					plan.date_required as date,
					plan.shift as shift,
					plan.branch_id as branch_id,
					plan.technic_id as technic_id,
					plan.work_time as work_time,
					tt.technic_type as technic_type,
					tt.owner_type as owner_type,
					wo.total_spend_time as wo_work_time,
					(100 - (100*plan.work_time)/ts.work_time_per_day) as tbbk
				FROM technic_equipment as tt
				LEFT technic_equipment_setting as ts on ts.id = tt.technic_setting_id
				LEFT maintenance_plan_line as plan on tt.id = plan.technic_id
				LEFT maintenance_workorder as wo on wo.id = plan.workorder_id
				WHERE plan.state not in ('draft','cancelled') and
					  tt.owner_type = 'own_asset' and
					  tt.is_tbbk_report = 't' and
					  tt.state != 'draft'
   	"""% (self._table)
		)
