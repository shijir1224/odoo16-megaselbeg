# -*- coding: utf-8 -*-

from odoo import api, models, fields

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	equipment_id = fields.Many2one('factory.equipment', related="maintenance_workorder_id.equipment_id", string=u'Холбоотой тоног төхөөрөмж', readonly=True, )

class StockMove(models.Model):
	_inherit = 'stock.move'

	# Columns
	equipment_id2 = fields.Many2one('factory.equipment', readonly=True, store=True, string=u'Холбоотой тоног төхөөрөмж #2')
	maintenance_workorder_id = fields.Many2one('maintenance.workorder', readonly=True, store=True,
		related="picking_id.maintenance_workorder_id", string=u'Холбоотой WO', )

	@api.depends('equipment_id2','maintenance_workorder_id')
	def _compute_set_equipment(self):
		for obj in self:
			if obj.maintenance_workorder_id and obj.maintenance_workorder_id.equipment_id:
				obj.equipment_id = obj.maintenance_workorder_id.equipment_id.id
			elif obj.equipment_id2:
				obj.equipment_id = obj.equipment_id2.id
			else:
				obj.equipment_id = False
	equipment_id = fields.Many2one('factory.equipment', readonly=True, store=True,
		compute="_compute_set_equipment", string=u'Холбоотой тоног төхөөрөмж')


	def get_nemelt_talbar_technic(self):
		if self.technic_id:
			return self.technic_id.display_name
		if self.equipment_id:
			return self.equipment_id.display_name
		else:
			return super(StockMove, self).get_nemelt_talbar_technic()

class StockMoveLinePicking(models.Model):
	_inherit = "stock.move.line"

	def get_nemelt_talbar_technic(self):
		if self.move_id.equipment_id:
			return self.move_id.equipment_id.display_name
		else:
			return super(StockMoveLinePicking, self).get_nemelt_talbar_technic()
