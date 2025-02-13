# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    is_with_ebarimt = fields.Boolean(string='Ebarimt олгох?')
    ebarimt_url = fields.Char(string='Ebarimt url')
    is_ebarimt_offline = fields.Boolean(string='Is offline?')
