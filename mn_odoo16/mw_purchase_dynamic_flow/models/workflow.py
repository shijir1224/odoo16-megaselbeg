# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields, models

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	po_id = fields.Many2one('purchase.order', 'Purchase order', ondelete='cascade', index=True)
