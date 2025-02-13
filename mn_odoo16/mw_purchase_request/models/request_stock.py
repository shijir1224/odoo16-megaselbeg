# -*- coding: utf-8 -*-
from odoo import fields, models

class TransportTrack(models.Model):
	_name = 'transport.track'
	_description = 'transport.track'

	name = fields.Char('Name', required=True)

	_sql_constraints = [
		('name_uniq', 'unique(name)', u'Transport name exists!'),
	]

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def action_view_po_id_mw(self):
		view = self.env.ref('purchase.purchase_order_form')
		return {
			'name': 'Худалдан авалтын захиалга',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'purchase.order',
			'views': [(view.id, 'form')],
			'view_id': view.id,
			'res_id': self.purchase_id.id,
			'context': dict(
				self.env.context
			),
		}


class StockMove(models.Model):
	_inherit = 'stock.move'

	def _action_done(self, cancel_backorder=False):
		result = super(StockMove, self)._action_done(cancel_backorder)
		for item in self:
			if item.picking_type_id.code == 'incoming' and item.purchase_line_id and item.purchase_line_id.filtered(
					lambda r: r.pr_line_many_ids and r.product_id.id == item.product_id.id):
				request_ids = item.purchase_line_id.mapped('pr_line_many_ids.request_id')
				re_names = ', '.join(request_ids.mapped('name'))
				p_ids = request_ids.mapped('employee_id.user_id.partner_id')
				if p_ids:
					html = u'<b>%s дугаартай Худалдан авалтын хүсэлтийн</b><br/><i style="color: green">%s</i> Бараа орлогод авагдлаа Баримт %s SMid %s</br>' % (
						re_names, item.product_id.display_name, item.picking_id.name, item.id)
					self.env['dynamic.flow.line'].send_chat(html, p_ids)
		return result
