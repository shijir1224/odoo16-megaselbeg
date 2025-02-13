# -*- coding: utf-8 -*-
from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Барааны хязгаарлалт шалгах
    def action_confirm(self): 
        check_limit = self.env['sale.order.limit.setting']
        for so in self:
            setting = self.env['sale.order.limit.setting'].search(
                [('state','=','confirmed'),
                 ('warehouse_ids','in',so.warehouse_id.id)], limit=1)
            if setting:
                for line in so.order_line:   
                    result = check_limit._check_limit(so.warehouse_id, so.partner_id, line.product_id, line.product_uom_qty)
        res = super(SaleOrder, self).action_confirm()
        return res