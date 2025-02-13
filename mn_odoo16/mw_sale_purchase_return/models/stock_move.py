# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    delivered_sale_return_line_ids = fields.One2many('sale.return.line', 'purchase_return_stock_move_line', string='Хүлээн авсан бор-н буцаалтын мөр')
