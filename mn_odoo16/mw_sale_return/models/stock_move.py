# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_return_line_id = fields.Many2one('sale.return.line', 'Үүсгэсэн Бор-н буцаалтын мөр')

    @api.depends('sale_line_id.price_unit','sale_return_line_id.price_unit','product_id', 'product_uom_qty', 'quantity_done', 'state')
    def _compute_price_unit_sale(self):
        for item in self:
            price_unit = 0
            if item.sale_line_id:
                price_unit = item.sale_line_id.price_unit
            elif item.sale_return_line_id:
                price_unit = item.sale_return_line_id.price_unit
            else:
                item.price_unit_sale = 0
                item.sub_total_sale = 0
                continue
            item.price_unit_sale = price_unit
            if item.state in ['done', 'cancel']:
                item.sub_total_sale = price_unit * item.quantity_done
            elif item.state == 'assigned':
                item.sub_total_sale = price_unit * item.reserved_availability
            else:
                item.sub_total_sale = price_unit * item.product_uom_qty