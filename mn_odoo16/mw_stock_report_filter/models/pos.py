# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _

class StockPicking(models.Model):
    _inherit = "stock.picking"

    # pos_order_ids = fields.One2many('pos.order', 'picking_id', string='ПОС захиалгууд', readonly=True)