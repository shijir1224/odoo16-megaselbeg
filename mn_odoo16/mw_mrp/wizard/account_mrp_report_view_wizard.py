# -*- coding: utf-8 -*-

import time
from odoo.exceptions import UserError
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models

class AccountMRPReport(models.TransientModel):
	_name = "account.mrp.view.wizard"
	_description = "account mrp report view wizard"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
	state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], default='posted', string='Status')

	account_ids = fields.Many2many('account.account', 'account_account_mrp_report_rel', 'account_id', 'transaction_id', string="Accounts", copy=False,
                                   # domain=[('account_type','in',('expense', 'income', 'income_other', 'expense_direct_cost'))]
                                   )
	
	analytic_account_ids = fields.Many2many('account.analytic.account', 'account_analytic_mrp_report_rel', 'analytic_account_id', 'transaction_id', string='Analytic Accounts')

	branch_ids = fields.Many2many('res.branch', 'account_mrp_report_branch_rel', 'branch_id', 'transaction_id', string='Branch')

	def open_analyze_view(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		

# 			# INIT query
# 		try:
# 			if self.env.context.get('send_rfq', False):
# 				template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
# 			else:
# 				template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase_done')[2]

# 			# Орлого зарлага хамтдаа
			search_res = mod_obj._xmlid_lookup('mw_mrp.account_mrp_view_report_search')[2]
			print ('search_res ',search_res)
			search_id = search_res
			pivot_res = mod_obj._xmlid_lookup('mw_mrp.account_mrp_view_report_pivot2')[2]
			pivot_id = pivot_res
			domain= [('date','>=',self.date_start),
						   ('date','<=',self.date_end),
						   ('account_id.company_id','=',self.company_id.id),
         # ('state','=',self.state),
						   ]
			if self.account_ids and self.branch_ids:
				domain= [('date','>=',self.date_start),
						   ('date','<=',self.date_end),
						   ('account_id.company_id','=',self.company_id.id),
         # ('state','=',self.state),
         					('branch_id','in',self.branch_ids.ids),
						   ('account_id','in',self.account_ids.ids),
						   ]
			if self.branch_ids and not self.account_ids:
				domain= [('date','>=',self.date_start),
						   ('date','<=',self.date_end),
						   ('account_id.company_id','=',self.company_id.id),
         # ('state','=',self.state),
						   ('branch_id','in',self.branch_ids.ids),
						   ]
			return {
				'name': _('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'account.mrp.view.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain':domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

