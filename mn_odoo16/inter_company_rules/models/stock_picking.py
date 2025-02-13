# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class StockPicking(models.Model):

	_inherit = "stock.picking"

	auto_generated_from_sale = fields.Boolean(related="purchase_id.auto_generated", string='Борлуулалтаас автомат үүссэн')
