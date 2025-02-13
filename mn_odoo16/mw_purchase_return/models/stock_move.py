# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    purchase_return_line_id = fields.Many2one('purchase.return.line', 'PO return line')  # Үүсгэсэн ХА-н буцаалтын мөр

    # Boliulav Otgootoi yrij bgad
    # def write(self, vals):
    #     res = super(StockMove, self).write(vals)
    #     if vals.get('state') == 'done':
    #         return_moves = self.filtered(lambda x: x.purchase_return_line_id)
    #         return_lines = return_moves.mapped('purchase_return_line_id')
    #         for return_line in return_lines:
    #             if return_line.not_sent_qty < 0:
    #                 raise UserError('%s барааг ХА-н буцаалтын тоо хэмжээнээс илүү зарлагадаж чадахгүй.\n%s буцаалтыг шалгана уу.' % (return_line.product_id.name, return_line.return_id.name))
    #     return res
