# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class PurchaseReturn(models.Model):
    _inherit = 'purchase.return'

    need_deliver = fields.Boolean('Хүлээж авах ёстой', compute='_compute_need_deliver', default=False, store=True)

    @api.depends('return_line.not_delivered_qty')
    def _compute_need_deliver(self):
        for ret in self:
            if any(ret.return_line.mapped('not_delivered_qty')):
                ret.need_deliver = True
            else:
                ret.need_deliver = False


class PurchaseReturnLine(models.Model):
    _inherit = 'purchase.return.line'

    sale_return_line_ids = fields.One2many('sale.return.line', 'purchase_return_line_id', 'Бор-н буцаалтын мөрүүд')
    not_delivered_qty = fields.Float('Хүлээж аваагүй тоо хэмжээ', digits='Product Unit of Measure', compute='_compute_not_delivered_qty', store=True)

    @api.depends('product_uom', 'sent_qty', 'sale_return_line_ids', 'sale_return_line_ids.product_uom', 'sale_return_line_ids.qty')
    def _compute_not_delivered_qty(self):
        for line in self:
            srl_qty = 0
            for srl in line.sale_return_line_ids:
                if line.product_uom == srl.product_uom:
                    srl_qty += srl.qty
                else:
                    srl_qty += srl.product_uom._compute_quantity(srl.qty, line.product_uom, round=False)
            line.not_delivered_qty = line.sent_qty - srl_qty
