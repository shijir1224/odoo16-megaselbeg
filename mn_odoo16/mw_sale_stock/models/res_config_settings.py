# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_create_return_invoice = fields.Boolean(related="company_id.auto_create_return_invoice", readonly=False)
    auto_validate_return_invoice = fields.Boolean(related="company_id.auto_validate_return_invoice", readonly=False)
