# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    period_journal_id = fields.Many2one('account.journal', string="Reserve & Profit/Loss Journal")
    period_account_id = fields.Many2one('account.account', string="Account")
