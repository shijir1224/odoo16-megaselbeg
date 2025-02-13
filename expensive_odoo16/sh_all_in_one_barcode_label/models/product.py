# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields,api
import base64
try:
    import qrcode
except ImportError:
    qrcode = None
from io import BytesIO

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sh_price_include_tax = fields.Float('Sales Price Include Taxes',compute='_compute_sh_price_include_tax')
    sh_cost_include_tax = fields.Float('Cost Price Include Taxes',compute='_compute_sh_cost_include_tax')
    sh_qr_code_image = fields.Binary('QR Code ')

    def _compute_sh_price_include_tax(self):
        """Compute sales price include customer taxes"""
        for rec in self:
            rec.sh_price_include_tax = 0.0
            price = rec.list_price
            if rec.product_variant_id:
                taxes = rec.taxes_id.compute_all(price, rec.currency_id or self.env.company.currency_id, 1.0, product=rec.product_variant_id, partner=self.env.user.partner_id)
                rec.sh_price_include_tax = taxes['total_included']

    def _compute_sh_cost_include_tax(self):
        """Compute cost price include vendor taxes"""
        for rec in self:
            rec.sh_cost_include_tax = 0.0
            price = rec.standard_price
            if rec.product_variant_id:
                taxes = rec.supplier_taxes_id.compute_all(price, rec.currency_id or self.env.company.currency_id, 1.0, product=rec.product_variant_id, partner=self.env.user.partner_id)
                rec.sh_cost_include_tax = taxes['total_included']

class Product(models.Model):
    _inherit = 'product.product'

    sh_price_include_tax = fields.Float('Sales Price Include Taxes ',compute='_compute_sh_price_include_tax')
    sh_cost_include_tax = fields.Float('Cost Price Include Taxes',compute='_compute_sh_cost_include_tax')
    sh_qr_code_image = fields.Binary('QR Code ')

    def _compute_sh_price_include_tax(self):
        """Compute sales price include customer taxes"""
        for rec in self:
            rec.sh_price_include_tax = 0.0
            price = rec.lst_price
            taxes = rec.taxes_id.compute_all(price, rec.currency_id or self.env.company.currency_id, 1.0, product=rec, partner=self.env.user.partner_id)
            rec.sh_price_include_tax = taxes['total_included']

    def _compute_sh_cost_include_tax(self):
        """Compute cost price include vendor taxes"""
        for rec in self:
            rec.sh_cost_include_tax = 0.0
            price = rec.standard_price
            taxes = rec.supplier_taxes_id.compute_all(price, rec.currency_id or self.env.company.currency_id, 1.0, product=rec, partner=self.env.user.partner_id)
            rec.sh_cost_include_tax = taxes['total_included']

    @api.model
    def sh_qr_code_generate(self, product_url):
        qr_code = product_url
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code)
        qr.make(fit=True)

        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_code_image = base64.b64encode(temp.getvalue())
        return qr_code_image