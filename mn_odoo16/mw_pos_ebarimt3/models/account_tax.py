# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTaxEbarimt(models.Model):
    _inherit = "account.tax"

    name = fields.Char(translate=True)
    ebarimt_tax_type_id = fields.Many2one('ebarimt.tax.type', string="EBarimt Tax Type", help="The 'EBarimt Tax Type' is used for features available on different types of tax types of Mongolian EBarimt system.")


class AccountJournal(models.Model):
    _inherit = "account.journal"


    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")