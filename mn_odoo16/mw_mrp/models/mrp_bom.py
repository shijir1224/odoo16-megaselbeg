# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

class MrpBomLine(models.Model):
	_inherit = 'mrp.bom.line'

	bom_location_id = fields.Many2one('stock.location', "ТЭМ татах байрлал", domain="[('usage', '=', 'internal')]")
		
		