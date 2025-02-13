# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta

import time

class WizardCheckPartQty(models.TransientModel):
	_name = "wizard.check.part.qty"
	_description = "wizard.check.part.qty"

	warehouse_ids = fields.Many2many('stock.warehouse', string=u'Агуулахууд')
	product_ids = fields.Many2many('product.product', string=u'Сэлбэг материалууд', required=True)
	qty_desc = fields.Html(string=u'Агуулахад...', readonly=True, )
	qtys_desc = fields.Html(string=u'Агуулахад...', readonly=True, )
	qty_pr_desc = fields.Html(string=u'Захиалсан...', readonly=True, )

	def check_part_qty(self):
		quant_obj = self.env['stock.quant']
		pr_lines = self.env['purchase.request.line']
		pr_report = self.env['pr.report']
		# self.product_ids.

		domain = [('product_id','in',self.product_ids.ids),('location_id.usage','=','internal')]
		if self.warehouse_ids:
			domain.append(('location_id.set_warehouse_id','in',self.warehouse_ids.ids))

		quant_ids = quant_obj.sudo().search(domain)
		message = u'<table style="width: 100%;"><tr><th>Байрлал</th><th>Бараа</th><th>Үлдэгдэл</th><th>Хэмжих нэгж</th></tr>'

		for item in quant_ids:
			qty = item.quantity
			css = "green" if qty > 0 else "red"
			message +=u'<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (item.location_id.complete_name,item.product_id.display_name,
			   qty, item.product_id.uom_id.name)

		message +='</table>'
		self.qty_desc = message

		product_tmpl_ids = self.product_ids.mapped('product_tmpl_id')
		domains = [('product_id','not in',self.product_ids.ids),('product_id.product_tmpl_id', 'in', product_tmpl_ids.ids), ('location_id.usage', '=', 'internal')]

		if self.warehouse_ids:
			domains.append(('location_id.set_warehouse_id', 'in', self.warehouse_ids.ids))

		quant_template_ids = quant_obj.sudo().search(domains)

		message = u'<table style="width: 100%; color: #FFA500;"><tr><th>Байрлал</th><th>Бараа</th><th>Үлдэгдэл</th><th>Хэмжих нэгж</th></tr>'
		quant_ids = quant_obj.sudo().search(domains)
		for items in quant_template_ids:
			qtys = items.quantity
			css = "green" if qtys > 0 else "red"
			message +=u'<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (items.location_id.complete_name,items.product_id.display_name,
			   qtys, items.product_tmpl_id.uom_id.name)

		message +='</table>'
		self.qtys_desc = message

		# PR шалгах
		# pr_lines = self.env['purchase.request.line'].search(
		# 	[('product_id','=',self.product_ids.ids),
		# 	 ('purchase_order_id.state','in',['sent','to approve','purchase'])])

		message = u'<table style="width: 100%;"><tr><th>Бараа</th><th>Сэлбэг захиалсан тоо</th></tr>'

		for item in self.product_ids:
			pr_domain = [('product_id','=',item.id),('qty_received','=',0)]
			pr_ids = pr_report.sudo().search(pr_domain)
			pr_lines = self.env['purchase.request.line'].sudo().search([('product_id','=',item.id)])
			pr_qty = sum(pr_lines.mapped('qty')) or 0
			po_lines = self.env['purchase.order.line'].sudo().search([('product_id','=',item.id)])
			po_qty = sum(po_lines.mapped('qty_received')) or 0

			# sm_lines = self.env['stock.move.line'].sudo().search([('product_id','=',item.id)])
			# sm_qty = sum(sm_lines.mapped('product_uom_qty')) or 0
			if pr_qty>0:
				message +=u'<tr><td><b>%s</b></td><td><b>%s</b></td></tr>'% (item.display_name, pr_qty - po_qty)

		message +='</table>'

		# WO
		message += u'<br><center><h3>Workorder дээрх нөөцлгөдсөн тоо хэмжээ</h3><center><br>'

		message += u'<table style="width: 100%;"><tr><th>WO</th><th>Нөөцлөгдсөн тоо</th><th>Нөөцлөгдсөн огноо</th></tr>'
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].sudo()._xmlid_lookup('mw_technic_maintenance.action_maintenance_workorder')[2]
		for item in self.product_ids:
			sm_lines = self.env['stock.move'].sudo().search([('product_id','=',item.id),('state','in',['assigned','partially_available']),('maintenance_workorder_id','!=',False)]).ids
			print('---+-+-+-+-+-+-+-+-+-+',sm_lines)
			if pr_lines:
				for item in sm_lines:
					sm_obj = self.env['stock.move'].sudo().browse(item)
					message += u'<tr><td><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=purchase.request&action=%s>%s</a></b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (base_url,sm_obj.maintenance_workorder_id.id,action_id, sm_obj.maintenance_workorder_id.name, sm_obj.reserved_availability, sm_obj.picking_id.scheduled_date)

		message +='</table>'

		message += u'<br><center><h3>Худалдан авалт & Худалдан авалтлын хүсэлт</h3><center><br>'

		# PR бүрээр задалж харуулах
		message += u'<table style="width: 100%;"><tr><th>PR</th><th>Тоо хэмжээ</th><th>Батлагдсан огноо</th></tr>'
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].sudo()._xmlid_lookup('mw_purchase_request.action_purchase_request_view')[2]
		for item in self.product_ids:
			pr_lines = self.env['purchase.request.line'].sudo().search([('product_id','=',item.id)])
			for pr_line in pr_lines:
				if pr_line.request_id.state_type not in ['cancel']:
					if not pr_line.po_line_ids:
						message += u'<tr><td><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=purchase.request&action=%s>%s</a></b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (base_url,pr_line.request_id.id,action_id, pr_line.request_id.name, pr_line.qty, pr_line.request_id.approved_date)
						continue
					qty_received = sum(pr_line.po_line_ids.filtered(lambda r: r.product_id == pr_line.product_id).mapped('qty_received'))
					if pr_line.po_qty > qty_received:
						message += u'<tr><td><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=purchase.request&action=%s>%s</a></b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (base_url,pr_line.request_id.id,action_id, pr_line.request_id.name, pr_line.qty, pr_line.request_id.approved_date)

		message +='</table>'
		# PO бүрээр задалж харуулах
		message += u'<table style="width: 100%;"><tr><th>PO</th><th>Тоо хэмжээ</th><th>Arrival date</th></tr>'
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		for item in self.product_ids:
			# po_lines = self.env['purchase.request.line'].search([('purchase_order_id.state','in',['sent','to approve','purchase'])]).ids
			po_lines = self.env['purchase.order.line'].sudo().search([('product_id','=',item.id)])
			for po_line in po_lines:
				if po_line.state in ['purchase','done']:
					action_id = self.env['ir.model.data'].sudo()._xmlid_lookup('purchase.purchase_form_action')[2]
				else:
					action_id = self.env['ir.model.data'].sudo()._xmlid_lookup('purchase.purchase_rfq')[2]
				# print('\t\t\tХүлээн аваагүй\t\t', self.env['purchase.order.line'].browse(item).qty_unreceived)
				# if self.env['purchase.order.line'].browse(item).qty_unreceived > 0:
				qty_unreceived = po_line.product_qty - po_line.qty_received
				message += u'<tr><td><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=purchase.order&action=%s>%s</a></b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (base_url,po_line.order_id.id,action_id, po_line.order_id.name, qty_unreceived, po_line.date_planned)


		# message = u'<b>%s</b> сэлбэгийг захиалсан тоо <font color="%s"><b>%d</b></font> байна.' % (self.product_ids.name, css, pr_qty)
		message +='</table>'

		today = date.today()
		limit_day = today - timedelta(days=30)
		for product in self.product_ids:
			query = """
				select
					te.name as technic_name,
					(sm.date + interval '8 hour')::date as dddd,
					sm.product_uom_qty as qty
				FROM stock_move as sm
				LEFT JOIN stock_picking as sp on (sp.id = sm.picking_id)
				LEFT JOIN stock_picking_type as spt on (spt.id = sp.picking_type_id)
				LEFT JOIN technic_equipment as te on (te.id = sm.technic_id)
				where sm.origin_returned_move_id is null and
					sm.state in ('done') and
					sm.technic_id is not null and
					sm.product_id = %d and
					spt.code = 'outgoing' and
					(sm.date + interval '8 hour')::date >= '%s' and
					(sm.date + interval '8 hour')::date <= '%s'
					order by sm.technic_id, dddd
			""" % (product, datetime.strftime(today, '%Y-%m-%d'), datetime.strftime(limit_day, '%Y-%m-%d'))

			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			if not records:
				continue
			message += u'<br><center><h3>%s бараа нь дээрх ашигласан техникүүд</h3><center><br>' % (product.display_name)
			message += u'<table style="width: 100%;"><tr><th>Техник</th><th>Огноо</th><th>Тоо хэмжээ</th></tr>'
			for record in records:
				message += u'<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>'% (record['technic_name'], record['dddd'], record['qty'])
			message +='</table>'

		self.qty_pr_desc = message


		action = self.env.ref('mw_technic_maintenance.action_wizard_check_part_qtysub').sudo().read()[0]
		action['res_id'] = self.id
		return action
		# return {
		# 		'name': 'Үлдэгдэл шалгах',
		# 		'view_type': 'form',
		# 		'view_mode': 'form',
		# 		'res_model': 'wizard.check.part.qty',
		# 		'res_id': self.id,
		# 		'views': [(False, 'form')],
		# 		'type': 'ir.actions.act_window',
		# 		'target': 'new',
		# 		'nodestroy': True,
		#    }
