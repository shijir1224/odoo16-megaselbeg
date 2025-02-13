# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import time

class WizardSalesPlan(models.TransientModel):
	_name = "wizard.sales.plan.report"
	_description = "wizard sales plan report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	branch_ids = fields.Many2many('res.branch', string='Салбар',)
	partner_ids = fields.Many2many('res.partner', string=u'Харилцагч', help=u"Харилцагчаар шүүх")
	partner_category_ids = fields.Many2many('res.partner.category', string=u'Харилцагчийн ангилал')
	product_ids = fields.Many2many('product.product', string=u'Бараанууд', help=u"Тайланд гарах барааг сонгоно")
	categ_ids = fields.Many2many('product.category', string=u'Барааны ангилал', help=u"Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
	
	tz = fields.Integer(u'Цагийн бүсийн зөрүү', required=True, default=8)

	def open_analyze_view(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			search_res = mod_obj.get_object_reference('mw_sales_master_plan', 'sale_plan_pivot_report_search')
			search_id = search_res and search_res[1] or False
			pivot_res = mod_obj.get_object_reference('mw_sales_master_plan', 'sale_plan_pivot_report_pivot')
			pivot_id = pivot_res and pivot_res[1] or False
			domain = [('year','>=',self.date_start.year),
					  ('year','<=',self.date_end.year),
					  ('month','>=',int(self.date_start.month)),
					  ('month','<=',int(self.date_end.month))]

			if self.branch_ids:
				wh_ids = self.branch_ids.mapped('id')
				domain.append(('branch_id','in',wh_ids))
			if self.product_ids:
				p_ids = self.product_ids.mapped('id')
				domain.append(('product_id','in',p_ids))
			if self.partner_ids:
				partner_ids = self.partner_ids.mapped('id')
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
				'res_model': 'sale.plan.pivot.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}

	# Гүйцэтгэл харах
	# OVERRIDE IT
	def open_performance_view(self):
		return