# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class StockQuantReport(models.Model):
    _inherit = "stock.quant.report"
    
    brand_id = fields.Many2one('product.brand', 'Брэнд', readonly=True)

    def _select(self):
        select_str = super(StockQuantReport, self)._select()
        select_str += """
            ,pt.brand_id
        """
        return select_str
