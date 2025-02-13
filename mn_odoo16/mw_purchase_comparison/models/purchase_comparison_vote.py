# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields
from odoo.models import Model

class PurchaseOrderComparisonVote(Model):
	_name = 'purchase.order.comparison.vote'
	_description = 'Vote for purchase comparison'

	comparison_id = fields.Many2one('purchase.order.comparison', required=True, readonly=True, ondelete='cascade')
	user_id = fields.Many2one('res.users', string='User')
	is_voted = fields.Boolean('Is voted')
	vote_date = fields.Datetime('Vote date')
	partner_id = fields.Many2one('res.partner', string='Choosing partner')
	comment = fields.Char('Comment')

	_sql_constraints = [('Comparison_user_id_unique', 'unique(comparison_id,user_id)', 'Partner already exists')]

	def _check_previous_vote(self):
		if self.partner_id:
			result = self.comparison_id.vote_result_ids.filtered(lambda l: l.partner_id == self.partner_id)
			if result and result.vote_points > 0:
				result.vote_points -= 1

	def _add_vote(self):
		result = self.comparison_id.vote_result_ids.filtered(lambda l: l.partner_id == self.partner_id)
		if result:
			result.vote_points += 1

	def vote(self, partner_id, comment):
		self.ensure_one()
		self._check_previous_vote()
		self.write({'partner_id': partner_id.id,
					'comment': comment,
					'is_voted': True,
					'vote_date': datetime.now()})
		self._add_vote()

class PurchaseOrderComparisonVoteResult(Model):
	_name = 'purchase.order.comparison.vote.result'
	_description = 'Vote result of purchase comparison'
	_order = 'vote_points desc'

	comparison_id = fields.Many2one('purchase.order.comparison', required=True, readonly=True, ondelete='cascade')
	partner_id = fields.Many2one('res.partner', string='Partner')
	vote_points = fields.Integer('Vote points', default=0)

	_sql_constraints = [('Comparison_partner_id_unique', 'unique(comparison_id,partner_id)', 'Partner already exists')]
