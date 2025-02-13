# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    emp_rec_account_id = fields.Many2one('account.account', related='company_id.emp_rec_account_id',  string='Ажилтны авлагын данс',readonly=False)
    emp_pay_account_id = fields.Many2one('account.account', related='company_id.emp_pay_account_id',string='Компани хооронд ажилтны өглөгийн данс',readonly=False)
    