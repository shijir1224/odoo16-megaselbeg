# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

from collections import defaultdict
from itertools import groupby
import json

class AutomaticEntryWizard(models.TransientModel):
    _name = 'account.automatic.entry.wizard'
    _inherit = ["account.automatic.entry.wizard", "analytic.mixin"]

    def _get_move_dict_vals_change_account(self):
        line_vals = []
 
        # Group data from selected move lines
        counterpart_balances = defaultdict(lambda: defaultdict(lambda: 0))
        grouped_source_lines = defaultdict(lambda: self.env['account.move.line'])
 
        for line in self.move_line_ids.filtered(lambda x: x.account_id != self.destination_account_id):
            counterpart_currency = line.currency_id
            counterpart_amount_currency = line.amount_currency
 
            if self.destination_account_id.currency_id and self.destination_account_id.currency_id != self.company_id.currency_id:
                counterpart_currency = self.destination_account_id.currency_id
                counterpart_amount_currency = self.company_id.currency_id._convert(line.balance, self.destination_account_id.currency_id, self.company_id, line.date)
 
            counterpart_balances[(line.partner_id, counterpart_currency)]['amount_currency'] += counterpart_amount_currency
            counterpart_balances[(line.partner_id, counterpart_currency)]['balance'] += line.balance
            grouped_source_lines[(line.partner_id, line.currency_id, line.account_id)] += line
 
        # Generate counterpart lines' vals
        for (counterpart_partner, counterpart_currency), counterpart_vals in counterpart_balances.items():
            source_accounts = self.move_line_ids.mapped('account_id')
            counterpart_label = len(source_accounts) == 1 and _("Transfer from %s", source_accounts.display_name) or _("Transfer counterpart")
 
            if not counterpart_currency.is_zero(counterpart_vals['amount_currency']):
                analytic_distribution = False
                if self.destination_account_id.check_analytic == True:
                    analytic_distribution = self.analytic_distribution or False
                else:
                    analytic_distribution = False
                line_vals.append({
                    'name': self.desc_name or '',# or aml.name or '',
                    'debit': counterpart_vals['balance'] > 0 and self.company_id.currency_id.round(counterpart_vals['balance']) or 0,
                    'credit': counterpart_vals['balance'] < 0 and self.company_id.currency_id.round(-counterpart_vals['balance']) or 0,
                    'account_id': self.destination_account_id.id,
                    'analytic_distribution':analytic_distribution,
                    'partner_id': self.partner_ids.id or counterpart_partner.id or None,
                    'amount_currency': counterpart_currency.round((counterpart_vals['balance'] < 0 and -1 or 1) * abs(counterpart_vals['amount_currency'])) or 0,
                    'currency_id': counterpart_currency.id,
                })
 
        # Generate change_account lines' vals
        for (partner, currency, account), lines in grouped_source_lines.items():
            account_balance = sum(line.balance for line in lines)
            if not self.company_id.currency_id.is_zero(account_balance):
                analytic_distribution = False
                if account.check_analytic == True:
                    analytic_distribution = self.analytic_distribution or False
                else:
                    analytic_distribution = False
                account_amount_currency = currency.round(sum(line.amount_currency for line in lines))
                line_vals.append({
#                     'name': _('Transfer to %s', self.destination_account_id.display_name or _('[Not set]')),
                    'name': self.desc_name or '',
                    'analytic_distribution':analytic_distribution,
                    'debit': account_balance < 0 and self.company_id.currency_id.round(-account_balance) or 0,
                    'credit': account_balance > 0 and self.company_id.currency_id.round(account_balance) or 0,
                    'account_id': account.id,
                    'partner_id': partner.id or None,
                    'currency_id': currency.id,
                    'amount_currency': (account_balance > 0 and -1 or 1) * abs(account_amount_currency),
                })
 
        return [{
            'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': fields.Date.to_string(self.date),
            'ref': self.desc_name or '',
            'line_ids': [(0, 0, line) for line in line_vals],
        }]

    def _get_move_dict_vals_change_period(self):
        # set the change_period account on the selected journal items
        accrual_account = self.revenue_accrual_account if self.account_type == 'income' else self.expense_accrual_account

        move_data = {'new_date': {
            'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
            'move_type': 'entry',
            'line_ids': [],
            'ref': self.desc_name or '',
            'date': fields.Date.to_string(self.date),
            'journal_id': self.journal_id.id,
        }}
        # complete the account.move data
        for date, grouped_lines in groupby(self.move_line_ids, lambda m: m.move_id.date):
            grouped_lines = list(grouped_lines)
            amount = sum(l.balance for l in grouped_lines)
            move_data[date] = {
                'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
                'move_type': 'entry',
                'line_ids': [],
                'ref': self.desc_name or '',
                'date': fields.Date.to_string(date),
                'journal_id': self.journal_id.id,
            }

        # compute the account.move.lines and the total amount per move
        for aml in self.move_line_ids:
            # account.move.line data
            reported_debit = aml.company_id.currency_id.round((self.percentage / 100) * aml.debit)
            reported_credit = aml.company_id.currency_id.round((self.percentage / 100) * aml.credit)
            reported_amount_currency = aml.currency_id.round((self.percentage / 100) * aml.amount_currency)
            analytic_distribution = False
            if aml.account_id.check_analytic == True:
                analytic_distribution = self.analytic_distribution or False
            else:
                analytic_distribution = False
            next_analytic_distribution = False
            if accrual_account.check_analytic == True:
                next_analytic_distribution = self.next_analytic_distribution or False
            else:
                next_analytic_distribution = False
            move_data['new_date']['line_ids'] += [
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
                    'analytic_distribution':analytic_distribution,
                    'debit': reported_debit,
                    'credit': reported_credit,
                    'amount_currency': reported_amount_currency,
                    'currency_id': aml.currency_id.id,
                    'account_id': aml.account_id.id,
                    'partner_id': aml.partner_id.id,
                }),
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
                    'analytic_distribution':next_analytic_distribution,
                    'debit': reported_credit,
                    'credit': reported_debit,
                    'amount_currency': -reported_amount_currency,
                    'currency_id': aml.currency_id.id,
                    'account_id': accrual_account.id,
                    'partner_id': aml.partner_id.id,
                }),
            ]
            move_data[aml.move_id.date]['line_ids'] += [
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
                    'analytic_distribution':analytic_distribution,
                    'debit': reported_credit,
                    'credit': reported_debit,
                    'amount_currency': -reported_amount_currency,
                    'currency_id': aml.currency_id.id,
                    'account_id': aml.account_id.id,
                    'partner_id': aml.partner_id.id,
                }),
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
                    'analytic_distribution':next_analytic_distribution,
                    'debit': reported_debit,
                    'credit': reported_credit,
                    'amount_currency': reported_amount_currency,
                    'currency_id': aml.currency_id.id,
                    'account_id': accrual_account.id,
                    'partner_id': aml.partner_id.id,
                }),
            ]

        move_vals = [m for m in move_data.values()]
        return move_vals

