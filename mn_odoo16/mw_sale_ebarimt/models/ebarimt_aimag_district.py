# -*- coding: utf-8 -*-
from odoo import api, models, fields

class ebarimt_aimag_district(models.Model):
    _name = 'ebarimt.aimag.district'
    _description = 'EBarimt Aimag/District'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)

    _sql_constraints = [('code_ebarimt_aimag_district_uniq', 'unique (code)', 'The code of the ebarimt Aimag/District must be unique!')]
