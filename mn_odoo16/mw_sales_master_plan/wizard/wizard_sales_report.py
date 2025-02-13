# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import time

class WizardSales(models.TransientModel):
	_name = "wizard.sales.report"
	_description = "wizard sales report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	branch_ids = fields.Many2many('res.branch', string=u'Салбар',)
	warehouse_id = fields.Many2many('stock.warehouse', string=u'Агуулах',)
	user_ids = fields.Many2many('res.users', string=u'Борлуулагч',)
	partner_ids = fields.Many2many('res.partner', string=u'Харилцагч', help=u"Харилцагчаар шүүх")
	partner_category_ids = fields.Many2many('res.partner.category', string=u'Харилцагчийн ангилал')
	product_ids = fields.Many2many('product.product', string=u'Бараанууд', help=u"Тайланд гарах барааг сонгоно")
	categ_ids = fields.Many2many('product.category', string=u'Барааны ангилал', help=u"Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
	is_validity_date = fields.Boolean(u'Захиалгын огноогоор', default=True)

	tz = fields.Integer(u'Цагийн бүсийн зөрүү', required=True, default=8)

	def open_analyze_view(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			search_res = mod_obj.check_object_reference('mw_sales_master_plan', 'sale_pivot_report_search')
			search_id = search_res and search_res[1] or False
			pivot_res = mod_obj.check_object_reference('mw_sales_master_plan', 'sale_pivot_report_pivot')
			pivot_id = pivot_res and pivot_res[1] or False

			domain = [('validity_date','>=',self.date_start),
					  ('validity_date','<=',self.date_end)]
			if not self.is_validity_date:
				domain = [('picking_date','>=',self.date_start),
					  	  ('picking_date','<=',self.date_end)]

			if self.warehouse_id:
				wh_ids = []
				wh_ids = self.warehouse_id.mapped('id')
				domain.append(('warehouse_id','in',wh_ids))
			if self.product_ids:
				p_ids = self.product_ids.mapped('id')
				domain.append(('product_id','in',p_ids))
			if self.branch_ids:
				p_ids = self.branch_ids.mapped('id')
				domain.append(('branch_id','in',p_ids))
			if self.user_ids:
				u_ids = self.user_ids.mapped('id')
				domain.append(('user_id','in',u_ids))
			if self.partner_ids:
				partner_ids = self.partner_ids.mapped('id')
				partner_ids += self.env['res.partner'].search([('parent_id','in',partner_ids)]).mapped('id')
				domain.append(('partner_id','in',partner_ids))
			if self.categ_ids:
				c_ids = self.categ_ids.mapped('id')
				domain.append(('categ_id','child_of',c_ids))
			if self.partner_category_ids:
				c_ids = self.partner_category_ids.mapped('id')
				p_ids = self.env['res.partner'].search([('category_id','in',c_ids)]).mapped('id')
				domain.append(('partner_id','in',p_ids))

			return {
				'name': ('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'sale.pivot.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}

