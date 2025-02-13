# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qpay_username = fields.Char(related='company_id.qpay_username', string='Username', readonly=False)
    qpay_password = fields.Char(related='company_id.qpay_password', string='Password', readonly=False)
    qpay_invoice_code = fields.Char(related='company_id.qpay_invoice_code', string='Invoice code', readonly=False)

    qpay_login_url = fields.Char(related='company_id.qpay_login_url', string='Login url', readonly=False)
    qpay_refresh_url = fields.Char(related='company_id.qpay_refresh_url', string='Refresh url', readonly=False)
    qpay_invoice_create_url = fields.Char(related='company_id.qpay_invoice_create_url', string='Invoice create url', readonly=False)
    qpay_invoice_check_url = fields.Char(related='company_id.qpay_invoice_check_url', string='Invoice check url', readonly=False)