# -*- coding: utf-8 -*-

from odoo import api, models, fields

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	maintenance_workorder_id = fields.Many2one('maintenance.workorder', string=u'WorkOrder', )
	technic_id = fields.Many2one('technic.equipment', 
		related="maintenance_workorder_id.technic_id", string=u'Холбоотой техник', readonly=True, )

	def action_done(self):
		res = super(StockPicking, self).action_done()
		# Хэрэв picking дуусгаж байгаа бол
		# Холбоотой WO ийг Processing болгох
		for obj in self:
			if obj.maintenance_workorder_id:
				not_done = obj.maintenance_workorder_id.wo_move_lines.filtered(lambda l: l.state not in ['done','cancel'])
				if not not_done:
					obj.maintenance_workorder_id.sudo().action_to_ready()
		return res

	def action_cancel(self):
		res = super(StockPicking, self).action_cancel()
		# Хэрэв picking цуцлаж байгаа бол
		# Холбоотой WO ийг Processing болгох
		for obj in self:
			if obj.maintenance_workorder_id:
				not_done = obj.maintenance_workorder_id.wo_move_lines.filtered(lambda l: l.state not in ['done','cancel'])
				if not not_done:
					obj.maintenance_workorder_id.sudo().action_to_ready()
		return res

class StockMove(models.Model):
	_inherit = 'stock.move'

	# Columns
	maintenance_workorder_id = fields.Many2one('maintenance.workorder', readonly=True, store=True,
		related="picking_id.maintenance_workorder_id", string=u'Холбоотой WO', )
	technic_id2 = fields.Many2one('technic.equipment', readonly=True, string=u'Холбоотой техник 2')
	@api.depends('technic_id2','maintenance_workorder_id')
	def _compute_set_technic(self):
		for obj in self:
			if obj.maintenance_workorder_id and obj.maintenance_workorder_id.technic_id:
				obj.technic_id = obj.maintenance_workorder_id.technic_id.id
			elif obj.technic_id2:
				obj.technic_id = obj.technic_id2.id
			else:
				obj.technic_id = False
	technic_id = fields.Many2one('technic.equipment', readonly=True, store=True,
		compute="_compute_set_technic", string=u'Холбоотой техник')
	vin_number = fields.Char(related='technic_id.vin_number', string='Техникийн сериал')
	technic_type = fields.Selection(related='technic_id.technic_type', string='Техникийн төрөл')

	@api.depends('maintenance_workorder_id')
	def _compute_set_component(self):
		for obj in self:
			if obj.maintenance_workorder_id and obj.maintenance_workorder_id.repair_component_id:
				obj.component_id = obj.maintenance_workorder_id.repair_component_id.id
	component_id = fields.Many2one('technic.component.part', readonly=True, store=True,
		compute="_compute_set_component", string=u'Холбоотой компонент', )

	# Тухайн сэлбэгийг яг техникт суурьлуулсан эсэх
	is_used = fields.Boolean(u'Суурьлуулсан эсэх', default=False)
	
	def set_used_it(self):
		if self.state == 'done' and self.maintenance_workorder_id and self.maintenance_workorder_id.state in ['waiting_part','processing','ready']:
			self.is_used = True

	def get_nemelt_talbar_technic(self):
		if self.technic_id:
			return self.technic_id.display_name
		else:
			return super(StockMove, self).get_nemelt_talbar_technic()

class StockMoveLinePicking(models.Model):
	_inherit = "stock.move.line"

	def get_nemelt_talbar_technic(self):
		if self.move_id.technic_id:
			return self.move_id.technic_id.display_name
		else:
			return super(StockMoveLinePicking, self).get_nemelt_talbar_technic()

# class NewProductRequest(models.Model):
# 	_inherit = 'new.product.request'

# 	part_number = fields.Char(u'Эдийн дугаар',
# 		states={'sent': [('readonly', True)],'created': [('readonly', True)],
# 				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
# 	system_id = fields.Many2one('maintenance.damaged.type', string=u'Систем', 
# 		states={'sent': [('readonly', True)],'created': [('readonly', True)],
# 				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
# 	technic_model_id = fields.Many2one('technic.model.model', string=u'Техникийн модел', 
# 		states={'sent': [('readonly', True)],'created': [('readonly', True)],
# 				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
# 	converted_part_number = fields.Char(u'Хөрвөсөн код', 
# 		states={'sent': [('readonly', True)],'created': [('readonly', True)],
# 				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
# 	# 
# 	get_old_parts = fields.Boolean(u'Хуучин сэлбэг авах эсэх', 
# 		states={'sent': [('readonly', True)],'created': [('readonly', True)],
# 				'done': [('readonly', True)],'cancelled': [('readonly', True)]})

# class newProductRequestLine(models.Model):
# 	_inherit = 'new.product.request.line'

# 	system_id = fields.Many2one('maintenance.damaged.type', string=u'Систем')
# 	technic_model_id = fields.Many2one('technic.model.model', string=u'Таарах модел')
# 	get_old_parts = fields.Boolean(u'Хуучин сэлбэг авах эсэх')
