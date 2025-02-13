# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    allowed_uom_ids = fields.Many2many('uom.uom', 'product_template_allowed_uom_rel', 'product_id','uom_id',
        string='Зөвшөөрөгдсөн Хэмжих нэгж',
    )

class UomUom(models.Model):
    _inherit = 'uom.uom'
    
    allowed_product_ids = fields.Many2many('product.template', 'product_template_allowed_uom_rel', 'uom_id','product_id', string='Зөвшөөрөгдсөн Бараанууд',)
    product_tmpl_ids = fields.One2many('product.template', 'uom_id', string='Зөвшөөрөгдсөн Бараанууд',)
    product_tmpl_po_ids = fields.One2many('product.template', 'uom_po_id', string='Зөвшөөрөгдсөн Бараанууд',)
    
class UomCategory(models.Model):
    _inherit = 'uom.category'

    uoms_by_categ = fields.One2many('uom.uom', 'category_id', string='Зөвшөөрөгдсөн хэмжих нэгж')