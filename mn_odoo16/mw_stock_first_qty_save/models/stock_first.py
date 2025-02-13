# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class StockMove(models.Model):
    _inherit = 'stock.move'

    first_qty = fields.Float('Анхны Тоо', readonly=True)

    def create(self, vals):
        res = super(StockMove, self).create(vals)
        for item in res:
            item.first_qty = item.product_uom_qty
        return res

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        for item in self:
            if item.state=='draft' and not item.first_qty and item.product_uom_qty:
                item.first_qty = item.product_uom_qty
        return res
    
