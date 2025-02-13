# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class TechnicInspectionPivotReport(models.Model):
	_name = "technic.inspection.pivot.report"
	_description = "technic_inspection_pivot_report"
	_auto = False
	_order = 'technic_id'

	inpection_id = fields.Many2one('technic.inspection', 'Inspection', readonly=True,  )
	inspection_type = fields.Selection([
			('daily', u'Өдөр дутмын'),
			('pm', u'PM-ын үзлэг'),], 
			string=u'Үзлэгийн төрөл', readonly=True, )
	date_inspection = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	technic_id = fields.Many2one('technic.equipment', 'Technic', readonly=True,  )

	category = fields.Selection([
		('ground','Ground'),
		('engine','Engine'),
		('cab','Cab'),
		('operating','Operating')], string='Category', readonly=True, )
	name = fields.Char("Үзлэг", readonly=True, )
	is_check = fields.Selection([
		('no',u'Асуудалтай'),
		('yes',u'Хэвийн')], string=u'Хэвийн эсэх', readonly=True, )

	description = fields.Text("Maintenance's note", readonly=True, )
	is_important = fields.Selection([
		('no',u'Үгүй'),
		('yes',u'Тийм')], string=u'Чухал үзлэг', readonly=True, )

	user_id = fields.Many2one('res.users', 'User', readonly=True,  )
	operator_id = fields.Many2one('hr.employee', 'Operator', readonly=True,  )

	operator_note = fields.Char("Operator's note", readonly=True, )
	maintenance_note = fields.Char("Maintenance's note", readonly=True, )
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				til.id as id,
				ti.id as inpection_id,
				ti.inspection_type as inspection_type,
				ti.date_inspection as date_inspection,
				ti.technic_id as technic_id,

				til.category as category,
				item.name as name,
				(CASE WHEN til.is_check='t' THEN 'yes' ELSE 'no' END) as is_check,
				til.description as description,
				(CASE WHEN item.is_important='t' THEN 'yes' ELSE 'no' END) as is_important,
				
				ti.user_id as user_id,
				ti.operator_id as operator_id,
				ti.operator_note as operator_note,
				ti.maintenance_note as maintenance_note
			FROM technic_inspection_line as til
			LEFT JOIN technic_inspection as ti on (til.parent_id = ti.id)
			LEFT JOIN technic_inspection_item as item on item.id = til.item_id
		)""" % self._table)
