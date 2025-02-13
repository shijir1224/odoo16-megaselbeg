# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class StockInventory(models.Model):
    _inherit = "stock.inventory"
    
    brand_ids = fields.Many2many('product.brand', string='Брэнд')

    @api.model
    def _selection_filter(self):
        res = super(StockInventory, self)._selection_filter()
        res.append(('brand', 'Брэндээр тооллого үүсгэх'))
        return res
    
    @api.onchange('filter_inv','many_categ_ids','brand_ids')
    def onchange_filter_inv(self):
        res = super(StockInventory, self).onchange_filter_inv()
        if self.filter_inv=='brand' and self.brand_ids:
            product_ids = self.env['product.product'].search([('type','in',['product','consu']),('brand_id','in',self.brand_ids.ids)]).ids
            self.product_ids = product_ids
        return res