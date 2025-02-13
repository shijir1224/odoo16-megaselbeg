# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class product_product(models.Model):
    _inherit = 'product.product'

    tax_type = fields.Char(compute='_tax_type', string='EBarimt VAT type')

    @api.depends('taxes_id')
    def _tax_type(self):
        for product in self:
            product.tax_type = ', '.join(str(ebarimt_tax.name) for ebarimt_tax in set(product.taxes_id.mapped('ebarimt_tax_type_id')))
