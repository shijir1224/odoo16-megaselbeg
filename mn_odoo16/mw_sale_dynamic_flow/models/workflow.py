# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields, models

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	so_id = fields.Many2one('sale.order', 'Sale order', ondelete='cascade', index=True)
