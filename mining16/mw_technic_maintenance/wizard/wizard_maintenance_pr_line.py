# -*- coding: utf-8 -*-

from odoo import api, models, fields
import time

class WizardMaintenancePrLine(models.TransientModel):
	_name = "wizard.maintenance.pr.line"  
	_description = "wizard.maintenance.pr.line"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	
	def open_pr_line_report(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			search_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_pr_line_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_pr_line_report_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			domain = [('date','>=',self.date_start.strftime("%Y-%m-%d")),
					  ('date','<=',self.date_end.strftime("%Y-%m-%d"))]
			return {
				'name': ('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'maintenance.pr.line.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}
