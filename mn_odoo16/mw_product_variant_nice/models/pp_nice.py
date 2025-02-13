# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons import decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    def name_get(self):
        res = []
        for obj in self:
            res_name = super(ProductProduct, obj).name_get()
            if obj.other_variant_number>1:
                res_name = str(res_name[0][1])+' ***'
                res.append((obj.id, res_name))
            else:
                res.append(res_name[0])
        return res

    other_variant_number = fields.Integer(compute='compute_other_variant_number')
    # product_variant_ids = fields.One2many('product.product', related='product_tmpl_id.product_variant_ids')

    @api.depends('product_tmpl_id.product_variant_ids')
    def compute_other_variant_number(self):
        for product in self:
            product.other_variant_number = len(product.product_tmpl_id.product_variant_ids)

# class ProductTemplate(models.Model):
#     _inherit = "product.template"
    
#     product_variant_count_mw = fields.Integer('# Product Variants', compute='_compute_product_variant_count_mw', search='_search_product_variant_mw')

#     def _compute_product_variant_count_mw(self):
#         for item in self:
#             item.product_variant_count_mw = 0
    
#     def _search_product_variant_mw(self, operator, value):
#         query ="""
#         select sm.id from product_template sm
# left OUTER  join product_product am on (am.product_tmpl_id=sm.id)
# where am.id is null
#         """
#         self.env.cr.execute(query)
#         result  = self.env.cr.dictfetchall() 
#         ids = []
#         for item in result:
#             ids.append(item['id'])
#         return [('id', 'in', ids)]