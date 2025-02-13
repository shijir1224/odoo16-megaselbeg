# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning,UserError
from odoo.tools import float_compare, float_is_zero, float_round
from calendar import monthrange
from odoo.tools import float_compare
from math import copysign

class accountAssetContinue(models.TransientModel):
	_name = 'account.asset.continue'
	_description = 'Account asset continue'

	date = fields.Date(string='Огноо', required=True, default=date.today())
	account_id = fields.Many2one('account.account', string='Алдагдалын данс', required=True)
	journal_id = fields.Many2one('account.journal', string='Журнал', required=True)
	asset_ids = fields.Many2many('account.asset.asset', string='Consumable materials', default=lambda self: self.env.context.get('active_ids', []))
	info_message = fields.Text(string='Мэдээлэл')
	tax_id = fields.Many2one('account.tax', string='Татвар', required=True)

	def doned_asset_create_move(self):
		# if self.env.context.get("active_ids") and self.env.context.get("active_model") == "consumable.material.in.use":
		# 	active_ids = self.env['consumable.material.in.use'].browse(self.env.context.get("active_ids"))
		for item in self.asset_ids.filtered(lambda r: r.state in ['depreciated'] and r.value_residual == 0):
			move_obj = self.env['account.move']
			asset_amount = item.value_residual
			line_ids = [(0,0,{
				'name': item.name and item.name or (item.code and item.code)+':'+str(item.id),
				'ref': item.code,
				'account_id': item.category_id.account_asset_id.id,
				'debit': 1,
				'credit': 0.0,
				'journal_id': self.journal_id.id,
				'date': self.date,
			}),(0,0,{
				'name': item.code and item.code or (item.name and item.name)+':'+str(item.id),
				'ref': item.code,
				'account_id': self.account_id.id,
				'debit': 0.0,
				'credit': 1,
				'journal_id': self.journal_id.id,
				'date': self.date,
				'tax_ids': [(4,self.tax_id.id)],
			})]
			move_vals = {
				'name': item.code and item.code or (item.name and item.name)+':'+str(item.id),
				'date': self.date,
				'ref': item.code,
				'journal_id': self.journal_id.id,
				'line_ids': line_ids
			}
			move_id = move_obj.create(move_vals)
			move_id._post()
		if self.asset_ids.filtered(lambda r: r.state not in ['depreciated'] or r.value_residual != 0):
			self.info_message = '\t|\t'.join(self.asset_ids.filtered(lambda r: r.state not in ['progresss'] or r.value_residual != 0)) + ' \nэдгээр АБХМ дахин ашиглах болоогүй байна!'
		action = self.env.ref('mw_account_asset.action_doned_asset_continue').read()[0]
		action['target'] = 'new'
		action['res_id'] = self.id
		return action