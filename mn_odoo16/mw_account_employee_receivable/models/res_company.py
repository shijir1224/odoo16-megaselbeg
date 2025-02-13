# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    emp_rec_account_id = fields.Many2one('account.account', string='Ажилтны авлагын данс',)
    emp_pay_account_id = fields.Many2one('account.account', string='Компани хооронд ажилтны өглөгийн данс',)
