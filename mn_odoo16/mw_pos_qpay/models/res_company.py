# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    qpay_username = fields.Char(string='Username')
    qpay_password = fields.Char(string='Password')
    qpay_invoice_code = fields.Char(string='Invoice code')
    qpay_access_token = fields.Char(string='Qpay access token')
    qpay_refresh_token = fields.Char(string='Qpay refresh token')
    refresh_token_expire_datetime = fields.Datetime(string='Refresh token expire datetime')
    access_token_expire_datetime = fields.Datetime(string='Access token expire datetime')
    qpay_login_url = fields.Char(string='Login url')
    qpay_refresh_url = fields.Char(string='Refresh url')
    qpay_invoice_create_url = fields.Char(string='Invoice create url')
    qpay_invoice_check_url = fields.Char(string='Invoice check url')
