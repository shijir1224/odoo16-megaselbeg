# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE

class EquipmentWOReport(models.Model):
	_name = "equipment.wo.report"
	_description = "Maintenance WO report"
	_auto = False
	_order = 'equipment_id'

	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True, )
	plan_id = fields.Many2one('maintenance.plan.line', 'Төлөвлөгөөний дугаар', readonly=True,  )
	wo_id = fields.Many2one('maintenance.workorder', 'WO дугаар', readonly=True,  )

	date = fields.Date(u'Огноо', readonly=True, )
	origin = fields.Char(u'Эх баримт', readonly=True, )
	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
		string=u'Засварын төрөл', readonly=True, )
	equipment_id = fields.Many2one('factory.equipment', string=u'Техник', readonly=True, )
	technic_type = fields.Char(string=u'Техникийн төрөл', readonly=True,)
	model_id = fields.Many2one('technic.model.model', string=u'Модел', readonly=True,)
	workorder_rate = fields.Selection([
		('0', u'Empty'),
		('1', u'Too bad'),
		('2', u'Bad'),
		('3', u'Дунд'),
		('4', u'Good'),
		('5', u'Excellent'),],
		string=u'Rate', readonly=True, )

	contractor_type = fields.Selection([
		('internal', u'Дотооддоо засварлах'),
		('external', u'Гадны гүйцэтгэгчээр'),],
		string=u'Гүйцэтгэгч нь', default='internal', readonly=True, )

	damaged_reason_id = fields.Many2one('maintenance.damaged.reason', u'Эвдрэлийн шалтгаан', readonly=True, )
	damaged_type_id = fields.Many2one('maintenance.damaged.type', u'Эвдрэлийн төрөл', readonly=True, )
	parent_damaged_type_id = fields.Many2one('maintenance.damaged.type', u'Толгой систем', readonly=True, )

	total_expense_amount = fields.Float(string=u'Нийт зарлагадах', readonly=True, )
	total_po_amount = fields.Float(string=u'Нийт худалдан авах', readonly=True, )
	total_amount_spare = fields.Float(string=u'Сэлбэг материал нийт', readonly=True, )

	planned_time = fields.Float(string=u'Төлөвлөсөн хүн цаг', readonly=True, )
	planned_time_0 = fields.Float(string=u'Төлөвлөсөн цаг', readonly=True, )
	man_hours = fields.Float(string=u'Ажилласан хүн цаг', readonly=True, )

	total_spend_time = fields.Float(string=u'Нийт зарцуулсан цаг', readonly=True, )

	description = fields.Char(string=u'Хийгдэх ажил', readonly=True, )
	performance_description = fields.Char(string=u'Гүйцэтгэсэн ажил', readonly=True, )

	state = fields.Selection([
			('draft', u'Draft'),
			('open', u'Open'),
			('reopen', u'Reopen'),
			('analysing', u'Analysing'),
			('waiting_part', u'Waiting for parts'),
			('ready', u'Ready'),
			('processing', u'Processing'),
			('done', u'Done'),
			('closed', u'Closed'),
			('cancelled', u'Cancelled')
		], readonly=True, string='Төлөв')

	component_repair_type = fields.Selection(
			[('remove', u'Салгах'),
			 ('install', u'Угсрах'),], string=u'Компонент угсрах, салгах', )

	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
		string=u'Ээлж', readonly=True, )

	validator_id = fields.Many2one('res.users', u'Хариуцагч', readonly=True, )

	workorder_rate_percent = fields.Float(string=u'Үнэлгээний хувь', default=0, group_operator="avg")
	workorder_rate_description_id = fields.Many2one('workorder.rate.description',
		string=u'Үнэлгээний тайлбар',)
	finished_qty = fields.Integer(string=u'Дууссан', default=0, )
	unfinished_qty = fields.Integer(string=u'Дуусаагүй', default=0, )

	is_rework = fields.Selection([
		('normal', u'Хэвийн'),
		('rework', u'ReWork'),],
		string='ReWork эсэх', readonly=True, )

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
				SELECT
					wo.branch_id as branch_id,
					wo.id as id,
					wo.id as wo_id,
					wo.origin as origin,
					wo.plan_id as plan_id,
					wo.date_required as date,
					wo.maintenance_type as maintenance_type,
					wo.equipment_id as equipment_id,
					fe.technic_type as technic_type,
					fe.model_id as model_id,
					(wo.planned_time * wo.planned_mans) as planned_time,
					wo.planned_time as planned_time_0,
					wo.total_spend_time as total_spend_time,
					wo.damaged_reason_id as damaged_reason_id,
					wo.contractor_type as contractor_type,
					wo.damaged_type_id as damaged_type_id,
					(CASE WHEN mdt.parent_id is null THEN wo.damaged_type_id ELSE mdt.parent_id END) as parent_damaged_type_id,
					wo.workorder_rate as workorder_rate,
					wo.total_expense_amount as total_expense_amount,
					wo.total_po_amount as total_po_amount,
					wo.total_expense_amount as total_amount_spare,
					wo.state as state,
					wo.component_repair_type as component_repair_type,
					wo.shift as shift,
					wo.description as description,
					wo.performance_description as performance_description,
					wo.validator_id as validator_id,
					wo.worked_man_hours as man_hours,
					(wo.workorder_rate::integer*100)/5 as workorder_rate_percent,
					wo.workorder_rate_description_id as workorder_rate_description_id,
					(CASE WHEN wo.state in ('done','closed') THEN 1 ELSE 0 END) as finished_qty,
					(CASE WHEN wo.state in ('done','closed') THEN 0 ELSE 1 END) as unfinished_qty,
					(CASE WHEN wo.is_rework = 't' THEN 'rework' ELSE 'normal' END) as is_rework
				FROM maintenance_workorder as wo
				LEFT JOIN factory_equipment as fe on fe.id = wo.equipment_id
				LEFT JOIN maintenance_damaged_type as mdt on mdt.id = wo.damaged_type_id
				WHERE wo.state not in ('draft','cancelled')

			)""" % self._table)

# class EquipemtCallReport(models.Model):
# 	_name = 'equipment.call.report'
# 	_description = 'Maintenance Call Report'
# 	_auto = False
# 	# _order = 'name'

# 	# Columns
# 	branch_id = fields.Many2one('res.branch', string=u'Салбар', )

# 	call_id = fields.Many2one('maintenance.call', string=u'Дуудлага', readonly=True, copy=False )
# 	description = fields.Char(string=u'Хийгдэх ажил', )
# 	date_required = fields.Date(u'Дуудлагын огноо', )

# 	technic_id = fields.Many2one('technic.equipment', string=u'Техник', )
# 	workorder_id = fields.Many2one('maintenance.workorder', string=u'WorkOrder', readonly=True, )

# 	department_id = fields.Many2one('hr.department', u'Хэлтэс нэгж', readonly=True)
# 	validator_id = fields.Many2one('res.users', u'Баталсан хэрэглэгч', readonly=True, copy=False,)
# 	close_user_id = fields.Many2one('res.users', u'Хаасан хэрэглэгч', readonly=True, copy=False,)

# 	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Техникийн систем', )

# 	# Гүйцэтгэл
# 	perform_department_id = fields.Many2one('hr.department', string=u'Гүйцэтгэх хэлтэс нэгж', )
# 	expense_id = fields.Many2one('stock.product.other.expense', string=u'Холбоотой шаардах', readonly=True, )

# 	man_hours = fields.Float(string=u'Ажилласан хүн цаг', readonly=True, )

# 	performance_description = fields.Char(string=u'Хийгдсэн ажил', )
# 	shift = fields.Selection([
# 			('day', u'Өдөр'),
# 			('night', u'Шөнө'),],
# 			string=u'Ээлж', required=True,)

# 	call_type = fields.Selection([
# 			('technic', u'Техникийн засвар'),
# 			('grane_job', u'Краны ажил'),
# 			('welding_job', u'Гагнуурын ажил'),
# 			('other_repair', u'Аж ахуйн засвар'),],
# 			string=u'Ажлын хүсэлтийн төрөл', required=True,)

# 	state = fields.Selection([
# 			('open', u'Илгээсэн'),
# 			('to_wo', u'WO нээсэн'),
# 			('to_expense', u'Шаардах үүссэн'),
# 			('closed', u'Хаагдсан'),
# 			('cancelled', u'Цуцлагдсан'),],
# 			default='draft', string=u'Төлөв', tracking=True)

# 	def init(self):
# 		tools.drop_view_if_exists(self.env.cr, self._table)
# 		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
# 				SELECT
# 					cl.id as id,
# 					cl.branch_id as branch_id,
# 					cl.id as call_id,
# 					cl.workorder_id as workorder_id,
# 					cl.date_required as date_required,
# 					cl.description as description,
# 					cl.technic_id as technic_id,
# 					cl.department_id as department_id,
# 					cl.validator_id as validator_id,
# 					cl.close_user_id as close_user_id,
# 					cl.damaged_type_id as damaged_type_id,
# 					cl.perform_department_id as perform_department_id,
# 					cl.expense_id as expense_id,
# 					cl.performance_description as performance_description,
# 					cl.shift as shift,
# 					cl.call_type as call_type,
# 					cl.spend_time as man_hours,
# 					cl.state as state
# 				FROM maintenance_call as cl
# 				WHERE cl.state not in ('draft','cancelled')
# 			)""" % self._table)