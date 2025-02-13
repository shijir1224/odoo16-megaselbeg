# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    exchange_equation_journal_id = fields.Many2one('account.journal', string='Journal of Exchange Equations')
    exchange_equation_cashflow_id = fields.Many2one('account.cash.move.type', string='Cashflow Type of Exchange Equations')
    exchange_equation_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account of Exchange Equations')
    unperformed_exchange_gain_account_id = fields.Many2one('account.account', string='Unperformed Rate Exchange Gain Account',
            help="This account will be used when compute currency rate exchange unperformed gain or loss.") #Валютын ханшийн хэрэгжээгүй олзын данс
    unperformed_exchange_loss_account_id = fields.Many2one('account.account', string='Unperformed Rate Exchange Loss Account',
            help="This account will be used when compute currency rate exchange unperformed gain or loss.") #Валютын ханшийн хэрэгжээгүй гарзын данс