# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE

# Plan material line
class MaintenanceExpenseReport(models.Model):
	_name = "maintenance.expense.report"
	_description = "Maintenance expense report on PLAN"
	_auto = False
	_order = 'product_id'

	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True,  )
	mp_id = fields.Many2one('maintenance.plan', 'Сарын төлөвлөгөө', readonly=True,  )
	mpl_id = fields.Many2one('maintenance.plan.line', u'Төлөвлөгөө', readonly=True,  )

	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
		string=u'Засварын төрөл', readonly=True, )
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, )
	technic_type = fields.Selection(TECHNIC_TYPE,
		string ='Техникийн төрөл',required=True)
	work_time = fields.Float(string='Засварын цаг', digits = (16,1), readonly=True, )
	planner_id = fields.Many2one('res.users', u'Төлөвлөгч', readonly=True, )

	contractor_type = fields.Selection([
		('internal', u'Дотооддоо засварлах'),
		('external', u'Гадны гүйцэтгэгчээр'),],
		string=u'Гүйцэтгэгч нь', default='internal', readonly=True, )

	product_id = fields.Many2one('product.product', 'Бараа', readonly=True,  )
	uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж', store=True, readonly=True, )
	categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True, )
	qty = fields.Float(u'Тоо хэмжээ', readonly=True, digits=(16,1))
	price_unit = fields.Float(u'Нэгж үнэ', readonly=True, digits=(16,1), operator='avg')
	amount = fields.Float(u'Дүн', readonly=True, digits=(16,1), )

	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('cancelled', 'Cancel'),
			('done', 'Done')
		], readonly=True, string='Төлөв')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
				SELECT
					mpl.branch_id as branch_id,
					mp.id as mp_id,
					mpl.id as mpl_id,
					rml.id as id,
					mpl.name as name,
					mpl.date_required as date,
					mpl.maintenance_type as maintenance_type,
					mpl.technic_id as technic_id,
					mpl.work_time as work_time,
					mpl.planner_id as planner_id,
					mpl.contractor_type as contractor_type,
					rml.product_id as product_id,
					rml.uom_id as uom_id,
					rml.categ_id as categ_id,
					rml.price_unit as price_unit,
					rml.qty as qty,
					rml.amount as amount,
					tt.technic_type as technic_type,
					mpl.state
				FROM required_material_line as rml
				LEFT JOIN maintenance_plan_line as mpl on (rml.parent_id = mpl.id)
				LEFT JOIN maintenance_plan as mp on (mp.id = mpl.parent_id)
				LEFT JOIN technic_equipment as tt on (tt.id = mpl.technic_id)
				WHERE mpl.state != 'draft'
			)""" % self._table)

# WO move lines
class MaintenanceWOExpenseReport(models.Model):
	_name = "maintenance.wo.expense.report"
	_description = "Maintenance WO expense report"
	_auto = False
	_order = 'product_id'

	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True, )
	plan_id = fields.Many2one('maintenance.plan.line', 'Төлөвлөгөөний дугаар', readonly=True,  )
	wo_id = fields.Many2one('maintenance.workorder', 'WO дугаар', readonly=True,  )
	picking_id = fields.Many2one('stock.picking', 'Зарлагын баримт', readonly=True,  )
	warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', readonly=True,  )

	date = fields.Date(u'Огноо/зарлага/', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	wo_date = fields.Date(u'WO Огноо', readonly=True, help=u"WO хийсэн огноо")

	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
		string=u'Засварын төрөл', readonly=True, )
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, )
	technic_type = fields.Selection(TECHNIC_TYPE,
		string ='Техникийн төрөл',required=True)
	work_time = fields.Float(string='Засварын цаг', digits = (16,1), readonly=True, )

	contractor_type = fields.Selection([
		('internal', u'Дотооддоо засварлах'),
		('external', u'Гадны гүйцэтгэгчээр'),],
		string=u'Гүйцэтгэгч нь', default='internal', readonly=True, )

	product_id = fields.Many2one('product.product', 'Бараа', readonly=True,  )
	uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж', store=True, readonly=True, )
	categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True, )
	qty = fields.Float(u'Тоо хэмжээ', readonly=True, digits=(16,1))
	price_unit = fields.Float(u'Нэгж үнэ', readonly=True, digits=(16,1), operator='avg')
	amount = fields.Float(u'Дүн', readonly=True, digits=(16,1), )

	order_qty = fields.Float(u'Захиалсан тоо', readonly=True, digits=(16,1))
	order_amount = fields.Float(u'Захиалсан дүн', readonly=True, digits=(16,1), )

	parts_user_id = fields.Many2one('res.users', u'Master name', readonly=True, copy=False,)
	senior_user_id = fields.Many2one('res.users', u'Senior name', readonly=True, copy=False,)
	engineer_user_id = fields.Many2one('res.users', u'Engineer name', readonly=True, copy=False,)
	chief_user_id = fields.Many2one('res.users', u'Chief name', readonly=True, copy=False,)

	system_id = fields.Many2one('maintenance.damaged.type', u'Систем', copy=False, )
	parent_system_id = fields.Many2one('maintenance.damaged.type', u'Толгой систем', copy=False, )

	state = fields.Selection([
			('draft', u'Ноорог'),
			('waiting', u'Хүлээгдэж байгаа'),
			('partially_available', u'Зарим нь бэлэн'),
			('cancel', u'Цуцлагдсан'),
			('confirmed', u'Бэлэнг хүлээж байгаа'),
			('assigned', u'Бэлэн'),
			('done', u'Дууссан'),
		], readonly=True, string='Төлөв')
	is_rework = fields.Selection([
		('normal', u'Хэвийн'),
		('rework', u'ReWork'),],
		string='ReWork эсэх', readonly=True, )
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
				SELECT
					wo.branch_id as branch_id,
					wo.id as wo_id,
					wo.plan_id as plan_id,
					sm.picking_id as picking_id,
					sl.set_warehouse_id as warehouse_id,
					sm.id as id,
					wo.date as wo_date,
					(sm.date + interval '8 hour')::date as date,
					wo.maintenance_type as maintenance_type,
					wo.technic_id as technic_id,
					tt.technic_type as technic_type,
					wo.total_spend_time as work_time,
					wo.contractor_type as contractor_type,
					sm.product_id as product_id,
					sm.product_uom as uom_id,
					pt.categ_id as categ_id,

					o_line.qty as order_qty,
					(o_line.qty*sm.price_unit) as order_amount,
					'used' as expense_type,
					sm.state,
					wo.parts_user_id as parts_user_id,
					wo.senior_user_id as senior_user_id,
					wo.engineer_user_id as engineer_user_id,
					wo.chief_user_id as chief_user_id,
					wo.damaged_type_id as system_id,
					sys.parent_id as parent_system_id,
					(CASE WHEN wo.is_rework = 't' THEN 'rework' ELSE 'normal' END) as is_rework,

					0 as price_unit,
					0 as qty,
					0 as amount

				FROM stock_move as sm
				LEFT JOIN maintenance_workorder as wo on (wo.id = sm.maintenance_workorder_id)
				LEFT JOIN stock_picking as sp on (sp.id = sm.picking_id)
				LEFT JOIN stock_picking_type as spt on (spt.id = sp.picking_type_id)
				LEFT JOIN stock_location as sl on (sl.id = sm.location_id)
				LEFT JOIN product_product as pp on (pp.id = sm.product_id)
				LEFT JOIN technic_equipment as tt on (tt.id = wo.technic_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN required_part_line as o_line on (o_line.move_id = sm.id)
				LEFT JOIN maintenance_damaged_type as sys on sys.id = wo.damaged_type_id
				WHERE 
					  sm.state in ('done') and
					  sm.technic_id is not null and 
					  sm.maintenance_workorder_id is not null
union all
					  SELECT
					wo.branch_id as branch_id,
					wo.id as wo_id,
					wo.plan_id as plan_id,
					sm.picking_id as picking_id,
					sl.set_warehouse_id as warehouse_id,
					sm.id as id,
					wo.date as wo_date,
					(sm.date + interval '8 hour')::date as date,
					wo.maintenance_type as maintenance_type,
					wo.technic_id as technic_id,
					tt.technic_type as technic_type,
					0 as work_time,
					wo.contractor_type as contractor_type,
					sm.product_id as product_id,
					sm.product_uom as uom_id,
					pt.categ_id as categ_id,

					0 as order_qty,
					0 as order_amount,
					'used' as expense_type,
					sm.state,
					wo.parts_user_id as parts_user_id,
					wo.senior_user_id as senior_user_id,
					wo.engineer_user_id as engineer_user_id,
					wo.chief_user_id as chief_user_id,
					wo.damaged_type_id as system_id,
					sys.parent_id as parent_system_id,
					(CASE WHEN wo.is_rework = 't' THEN 'rework' ELSE 'normal' END) as is_rework,

					sm.price_unit as price_unit,
					(case when sl.usage!='internal' then -1*sm.product_uom_qty else sm.product_uom_qty end) as qty,
					(case when sl.usage!='internal' then -1*(sm.product_uom_qty*sm.price_unit) else (sm.product_uom_qty*sm.price_unit) end) as amount

				FROM stock_move as sm
				LEFT JOIN maintenance_workorder as wo on (wo.id = sm.maintenance_workorder_id)
				LEFT JOIN stock_picking as sp on (sp.id = sm.picking_id)
				LEFT JOIN stock_picking_type as spt on (spt.id = sp.picking_type_id)
				LEFT JOIN stock_location as sl on (sl.id = sm.location_id)
				LEFT JOIN product_product as pp on (pp.id = sm.product_id)
				LEFT JOIN technic_equipment as tt on (tt.id = wo.technic_id)
				LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
				LEFT JOIN required_part_line as o_line on (o_line.move_id = sm.id)
				LEFT JOIN maintenance_damaged_type as sys on sys.id = wo.damaged_type_id
				WHERE 
					  sm.state in ('done') and
					  sm.technic_id is not null and 
					  sm.maintenance_workorder_id is not null
			)""" % self._table)

# Урьдчилсан төлөвлөгөөний материал
class PlanGeneratorExpenseReport(models.Model):
	_name = "plan.generator.expense.report"
	_description = "Plan generator expense report"
	_auto = False
	_order = 'product_id'

	g_id = fields.Many2one('maintenance.plan.generator', 'Generator', readonly=True,  )
	gl_id = fields.Many2one('maintenance.plan.generator.line', 'Generator line', readonly=True,  )

	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	maintenance_type_id = fields.Many2one('maintenance.type',string=u'Засварын төрөл', readonly=True, )
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, )
	work_time = fields.Float(string='Засварын цаг', digits = (16,1), readonly=True, )
	man_hours = fields.Float(string='Хүн/цаг', digits = (16,1), readonly=True, )
	pm_odometer = fields.Char(string=u'Хийгдэх гүйлт', readonly=True, )
	planner_id = fields.Many2one('res.users', u'Төлөвлөгч', readonly=True, )

	product_id = fields.Many2one('product.product', 'Бараа', readonly=True,  )
	categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True, )
	qty = fields.Float(u'Тоо хэмжээ', readonly=True, digits=(16,1))
	price_unit = fields.Float(u'Нэгж үнэ', readonly=True, digits=(16,1), operator='avg')
	amount = fields.Float(u'Дүн', readonly=True, digits=(16,1), )

	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], readonly=True, string='Төлөв')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT
				pg.id as g_id,
				pgl.id as gl_id,
				pgll.id as id,
				pgl.date_plan as date,
				pgl.maintenance_type_id as maintenance_type_id,
				pgl.technic_id as technic_id,
				pgl.work_time/(select count(*) from maintenance_pm_material_line where generator_id = pgll.generator_id) as work_time,
				pg.planner_id as planner_id,
				pgl.pm_odometer as pm_odometer,
				pgll.material_id as product_id,
				pgll.categ_id as categ_id,
				pgll.price_unit as price_unit,
				pgll.qty as qty,
				pgll.amount as amount,
				pg.state
			FROM maintenance_pm_material_line as pgll
			LEFT JOIN maintenance_plan_generator_line as pgl on (pgl.id = pgll.generator_id)
			LEFT JOIN maintenance_plan_generator as pg on (pg.id = pgl.parent_id)
		)""" % self._table)

# PR ordered line
class MaintenancePrLineReport(models.Model):
	_name = "maintenance.pr.line.report"
	_description = "Maintenance pr line report"
	_auto = False
	_order = 'product_id'

	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True,  )
	workorder_id = fields.Many2one('maintenance.workorder', 'Workorder', readonly=True,  )
	request_id = fields.Many2one('purchase.request', 'PR', readonly=True,  )
	technic_id = fields.Many2one('technic.equipment', 'Техник', readonly=True,  )

	date = fields.Date(u'Захиалсан', readonly=True, help=u"Захиалсан огноо")
	product_id = fields.Many2one('product.product', 'Бараа', readonly=True,  )
	uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж', store=True, readonly=True, )
	categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True, )
	qty = fields.Float(u'Тоо хэмжээ', readonly=True, digits=(16,1))

	description = fields.Char(u'Тайлбар', readonly=True, )
	is_ordered = fields.Selection([
		('yes', u'Тийм'),
		('no', u'Үгүй'),],
		string=u'Захиалсан эсэх', readonly=True, )

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT
				wo.branch_id as branch_id,
				rpl.id as id,
				wo.id as workorder_id,
				wo.technic_id as technic_id,
				pr.id as request_id,
				wo.date_required as date,
				rpl.product_id as product_id,
				rpl.uom_id as uom_id,
				rpl.categ_id as categ_id,
				rpl.qty as qty,
				pr.desc as description,
				(CASE WHEN rpl.is_ordered = 't' THEN 'yes' ELSE 'no' END) as is_ordered
			FROM required_part_line as rpl
			LEFT JOIN maintenance_workorder as wo on (wo.id = rpl.parent_id_2)
			LEFT JOIN purchase_request as pr on (pr.id = rpl.request_id)
			WHERE wo.state != 'draft' and
				  rpl.parent_id_2 is not null
		)""" % self._table)
