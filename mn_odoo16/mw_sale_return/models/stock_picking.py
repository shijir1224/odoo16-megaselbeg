# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_return_id = fields.Many2one('sale.return', 'Үүсгэсэн Бор-н буцаалт')
    sale_return_invoice_id = fields.Many2one('account.move', 'Нэхэмжлэл', copy=False)
