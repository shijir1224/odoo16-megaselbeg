# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class purchase_order(models.Model):

    _inherit = "purchase.order"

    auto_generated = fields.Boolean(string='Auto Generated Purchase Order', copy=False)
    auto_sale_order_id = fields.Many2one('sale.order', string='Source Sales Order', readonly=True, copy=False)
