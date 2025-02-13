# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    auto_create_return_invoice = fields.Boolean("Буцаалтын нэхэмжлэлийг автомат үүсгэх", default=False)
    auto_validate_return_invoice = fields.Boolean("Үүсгэсэн буцаалтын нэхэмжлэхийг автомат батлах", default=False)
