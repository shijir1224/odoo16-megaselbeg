# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import time

class WizardSalesmanRoureReport(models.TransientModel):
	_name = "wizard.salesman.route.report"
	_description = "wizard salesman route report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	partner_ids = fields.Many2many('res.partner', string=u'Харилцагч', help=u"Харилцагчаар шүүх")
	user_ids = fields.Many2many('res.users', string=u'Salesman',)
	
	
	def open_analyze_view(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			search_res = mod_obj.get_object_reference('mw_salesman_route_planner', 'salesman_route_report_search')
			search_id = search_res and search_res[1] or False
			pivot_res = mod_obj.get_object_reference('mw_salesman_route_planner', 'salesman_route_report_pivot')
			pivot_id = pivot_res and pivot_res[1] or False

			domain = [('date_order','>=',self.date_start),
					  ('date_order','<=',self.date_end)]

			
			if self.user_ids:
				u_ids = self.user_ids.mapped('id')
				domain.append(('user_id','in',u_ids))
			if self.partner_ids:
				partner_ids = self.partner_ids.mapped('id')
				domain.append(('partner_id','in',partner_ids))

			return {
				'name': ('Report'),
				'view_mode': 'pivot',
				'res_model': 'salesman.route.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}
