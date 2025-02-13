# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons import decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    combination_indices = fields.Char(compute='_compute_combination_indices', store=True, index=True)
    
    @api.depends('product_template_attribute_value_ids','default_code')
    def _compute_combination_indices(self):
        for product in self:
            product.combination_indices = product.product_template_attribute_value_ids._ids2str() + str(product.id or product.default_code or '')

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    product_variant_count_mw = fields.Integer('# Product Variants', compute='_compute_product_variant_count_mw', search='_search_product_variant_mw')

    def _compute_product_variant_count_mw(self):
        for item in self:
            item.product_variant_count_mw = 0
    
    def _search_product_variant_mw(self, operator, value):
        query ="""
        select sm.id from product_template sm
left OUTER  join product_product am on (am.product_tmpl_id=sm.id)
where am.id is null
        """
        self.env.cr.execute(query)
        result  = self.env.cr.dictfetchall() 
        ids = []
        for item in result:
            ids.append(item['id'])
        return [('id', 'in', ids)]