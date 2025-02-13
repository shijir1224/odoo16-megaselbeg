# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'
    _description = 'Account settings'

    period_journal_id = fields.Many2one('account.journal', related='company_id.period_journal_id', string='Reserve & Profit/Loss Journal')
    period_account_id = fields.Many2one('account.account', related='company_id.period_account_id', string="Account")
