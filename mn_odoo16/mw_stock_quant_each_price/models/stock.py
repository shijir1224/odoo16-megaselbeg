# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


from odoo import api, fields, models, _
import operator
import time
from datetime import datetime
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError,Warning

class stock_quant_report_eu(models.Model):
	_inherit = 'stock.quant.report'

	standard_price = fields.Float(related='product_tmpl_id.standard_price', string=u'Нэгж өртөг')
	list_price = fields.Float(related='product_tmpl_id.list_price', string=u'Нэгж үнэ')
	total_price = fields.Float(compute='_compute_price', string=u'Үнэ')

	@api.depends('list_price','quantity')
	def _compute_price(self):
		for item in self:
			item.total_price = item.quantity * item.list_price
