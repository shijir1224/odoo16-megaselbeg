from odoo.models import Model
from odoo import fields

class PurchaseOrderComparison(Model):
	_inherit = 'purchase.order.comparison'

	request_line_ids = fields.Many2many('purchase.request.line', compute='compute_request_line_ids', string='Request lines')
	request_ids = fields.Many2many('purchase.request', compute='compute_request_line_ids', string='Request lines')

	def compute_request_line_ids(self):
		for obj in self:
			lines = self.line_ids.mapped('request_line_ids')
			obj.request_line_ids = lines
			obj.request_ids = lines.mapped('request_id')

class PurchaseOrderComparisonLine(Model):
	_inherit = 'purchase.order.comparison.line'

	request_line_ids = fields.Many2many('purchase.request.line', 'purchase_comparison_line_purchase_request_line_rel', 'comp_line_id', 'pr_line_id', string='Request lines', copy=False)
