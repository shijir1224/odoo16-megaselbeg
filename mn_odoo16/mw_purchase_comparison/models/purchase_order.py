# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError

READONLY_STATES = {
	'purchase': [('readonly', True)],
	'done': [('readonly', True)],
	'cancel': [('readonly', True)],
	'comparison': [('readonly', True)],
}

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	comparison_id = fields.Many2one('purchase.order.comparison', string='Related comparison', readonly=True,
									copy=False)
	state = fields.Selection(selection_add=[('comparison', 'Comparison')],
							 ondelete={'comparison': 'set default'})
	date_order = fields.Datetime(states=READONLY_STATES)
	partner_id = fields.Many2one(states=READONLY_STATES)
	company_id = fields.Many2one(states=READONLY_STATES)
	user_id = fields.Many2one(states=READONLY_STATES)
	origin = fields.Char(states=READONLY_STATES)
	picking_type_id = fields.Many2one(states=READONLY_STATES)

	def unlink(self):
		for obj in self:
			if obj.comparison_id and not self.env.context.get('from_comparison', False):
				raise UserError(_('Cannot delete order that is created from comparison.'))
		return super(PurchaseOrder, self).unlink()

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	comparison_line_id = fields.Many2one('purchase.order.comparison.line', string='Related comparison line',
										 readonly=True, copy=False)

	#TODO ихэнх газар мөр үүсгэдэг
	# @api.model_create_multi
	# def create(self, vals_list):
	# 	for vals in vals_list:
	# 		order_id = self.order_id.browse(vals['order_id'])
	# 		if order_id.comparison_id and not self.env.context.get('from_comparison', False):
	# 			raise UserError(_('Cannot create line in order that is created from comparison.'))
	# 	return super(PurchaseOrderLine, self).create(vals_list)

	def unlink(self):
		for obj in self:
			if obj.order_id.comparison_id and self.env.context.get('from_comparison', False):
				raise UserError(_('Cannot delete order line that is created from comparison.'))
		return super(PurchaseOrderLine, self).unlink()
