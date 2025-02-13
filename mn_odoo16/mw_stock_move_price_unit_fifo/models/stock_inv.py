# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class stock_inventory_line(models.Model):
    _inherit = 'stock.inventory.line'
    
    mw_price_unit = fields.Float(string='Гараар Оруулах Өртөг')
    cost_method = fields.Selection(related="product_id.cost_method", readonly=True)

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        self.ensure_one()
        res = super(stock_inventory_line, self)._get_move_values(qty, location_id, location_dest_id, out)
        if self.mw_price_unit:
            res['price_unit'] = self.mw_price_unit
        return res
