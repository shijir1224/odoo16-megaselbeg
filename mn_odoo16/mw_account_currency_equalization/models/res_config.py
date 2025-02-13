# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    exchange_equation_journal_id = fields.Many2one('account.journal', related='company_id.exchange_equation_journal_id', string='Journal of Exchange Equations',
                                                   readonly=False, domain="[('company_id', '=', company_id), ('type', '=', 'general')]")
    exchange_equation_cashflow_id = fields.Many2one('account.cash.move.type', related='company_id.exchange_equation_cashflow_id', string='Cashflow Type of Exchange Equations',
                                                    readonly=False)
    exchange_equation_analytic_account_id = fields.Many2one('account.analytic.account', related='company_id.exchange_equation_analytic_account_id',
                                                            string='Analytic Account of Exchange Equations', readonly=False)
    unperformed_exchange_gain_account_id = fields.Many2one('account.account', related='company_id.unperformed_exchange_gain_account_id',
                                                           string='Unperformed Rate Exchange Gain Account', readonly=False, domain=[('deprecated', '=', False), ('internal_group', '=', 'income')],
                                                           help="This account will be used when compute currency rate exchange unperformed gain or loss.")
    unperformed_exchange_loss_account_id = fields.Many2one('account.account', related='company_id.unperformed_exchange_loss_account_id',
                                                           string='Unperformed Rate Exchange Loss Account', readonly=False, domain=[('deprecated', '=', False),('internal_group', '=', 'expense')],
                                                           help="This account will be used when compute currency rate exchange unperformed gain or loss.")