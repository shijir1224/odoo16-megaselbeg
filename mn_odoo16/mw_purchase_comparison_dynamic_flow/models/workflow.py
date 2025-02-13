# -*- coding: utf-8 -*-
from odoo import fields, models, _

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	comparison_id = fields.Many2one('purchase.order.comparison', 'Purchase comparison', ondelete='cascade', index=True)

class DynamicFlowLine(models.Model):
	_inherit = 'dynamic.flow.line'

	state_type = fields.Selection(selection_add=[
		('start_vote', 'Start vote'),
		('vote', 'Vote'),
		('vote_ended', 'Vote ended'),
		('ended', 'Ended')])
