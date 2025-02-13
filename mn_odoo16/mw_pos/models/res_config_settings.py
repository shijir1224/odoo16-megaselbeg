# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ebarimt_endpoint_url = fields.Char(related='company_id.ebarimt_endpoint_url', string='EBarimt URL', readonly=False)
    ebarimt_customer_check_url = fields.Char(related='company_id.ebarimt_customer_check_url', string='EBarimt Partner Check URL', readonly=False)
