# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ebarimt_url = fields.Char(related='company_id.ebarimt_url', string='Ebarimt url', readonly=False)
    is_ebarimt_offline = fields.Boolean(related='company_id.is_ebarimt_offline', string='Is offline', readonly=False)

    is_with_ebarimt = fields.Boolean(related='company_id.is_with_ebarimt', string='Ebarimt олгох?', readonly=False)

