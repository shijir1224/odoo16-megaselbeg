# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	pr_line_many_ids = fields.Many2many(related='order_line.pr_line_many_ids')

	def get_view_purchase_request(self):
		tree_view_id = self.env.ref('mw_purchase_request.purchase_request_line_tree_view').id
		form_view_id = self.env.ref('mw_purchase_request.purchase_request_line_form_view').id
		action = {
			'name': u'Хүсэлт',
			'view_mode': 'tree',
			'res_model': 'purchase.request.line',
			'domain': [('id', 'in', self.order_line.mapped('pr_line_many_ids').ids)],
			'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
			'view_id': tree_view_id,
			'type': 'ir.actions.act_window',
			'target': 'current'
		}
		return action


class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	pr_line_many_ids = fields.Many2many('purchase.request.line', 'purchase_order_line_purchase_request_line_rel',
										'po_line_id', 'pr_line_id', string='Хүсэлтийн мөрүүд')

	def unlink(self):
		for this in self:
			if (this.order_id.state not in ['cancel', 'draft']):
				raise UserError(u'Ноорог, цуцалсан төлөв дээр устгана уу!')
		return super(PurchaseOrderLine, self).unlink()
