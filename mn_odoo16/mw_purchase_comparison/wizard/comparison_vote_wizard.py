# -*- coding: utf-8 -*-
from odoo import fields
from odoo.models import TransientModel

class PurchaseOrderComparisonVoteWizard(TransientModel):
	_name = 'purchase.order.comparison.vote.wizard'
	_description = 'Vote wizard for purchase comparison'

	def _get_user_domain(self):
		domain = self.env.context.get('user_domain')
		if domain:
			return domain
		return []

	def _get_partner_domain(self):
		domain = self.env.context.get('partner_domain')
		if domain:
			return domain
		return []

	comparison_id = fields.Many2one('purchase.order.comparison', required=True, readonly=True, ondelete='cascade')
	wizard_type = fields.Selection([('start', 'Start vote'), ('primary', 'Primary vote')], required=True)
	partner_id = fields.Many2one('res.partner', string='Choosing partner', domain=_get_partner_domain)
	comment = fields.Char('Comment')
	user_ids = fields.Many2many('res.users', string='Voting users', domain=_get_user_domain)

	def submit_start(self):
		for obj in self.user_ids:
			self.env['purchase.order.comparison.vote'].create({'comparison_id': self.comparison_id.id, 'user_id': obj.id})
		if self.comparison_id.state == 'rfq_created':
			self.comparison_id.start_vote()

	def submit_primary(self):
		vote_id = self.comparison_id.vote_ids.filtered(lambda v: v.user_id == self.env.user)
		vote_id.vote(self.partner_id, self.comment)
