# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

from collections import defaultdict
from itertools import groupby
import json

class AutomaticEntryWizard(models.TransientModel):
    _inherit = 'account.automatic.entry.wizard'



    @api.model
    def _default_dest_acc(self):
        if self.env.context.get('active_model') != 'account.move.line' or not self.env.context.get('active_ids'):
            raise UserError(_('This can only be used on journal items'))
        move_line_ids = self.env['account.move.line'].browse(self.env.context['active_ids'])
        max_amount=0
        max_acc=False
        for line in move_line_ids:
            close_credit=line.debit>0 and abs(line.amount_residual)or 0
            close_debit=line.credit>0 and abs(line.amount_residual) or 0
            if max_amount<close_credit:
                max_amount=close_credit
                max_acc=line.account_id and line.account_id.id
            if max_amount<close_debit:
                max_amount=close_debit
                max_acc=line.account_id and line.account_id.id
        return max_acc


    @api.model
    def _default_dest_acc_ref(self):
        if self.env.context.get('active_model') != 'account.move.line' or not self.env.context.get('active_ids'):
            raise UserError(_('This can only be used on journal items'))
        move_line_ids = self.env['account.move.line'].browse(self.env.context['active_ids'])
        max_amount=0
        max_acc=''
        for line in move_line_ids:
            close_credit=line.debit>0 and abs(line.amount_residual)or 0
            close_debit=line.credit>0 and abs(line.amount_residual) or 0
            if max_amount<close_credit:
                max_amount=close_credit
                max_acc=line.name or ''
            if max_amount<close_debit:
                max_amount=close_debit
                max_acc=line.name or ''
        return max_acc

    # General
    destination_account_id = fields.Many2one(string="To", comodel_name='account.account', help="Account to transfer to.", default=_default_dest_acc)
    action = fields.Selection([('change_account', 'Change Account')],default='change_account', required=True)
    desc_name = fields.Char('Утга', default=_default_dest_acc_ref)
    partner_ids = fields.Many2one('res.partner', string="Харилцагч")
    journal_id = fields.Many2one('account.journal', required=True, readonly=False, string="Journal",
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
        help="Journal where to create the entry.")    
    new_journal_id = fields.Many2one('account.journal', readonly=False, string="Journal",
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
        help="Journal where to create the entry.")    
    @api.depends('company_id')
    def _compute_journal_id(self):
        for record in self:
            record.journal_id = record.company_id.automatic_entry_default_journal_id
    def _inverse_journal_id(self):
        for record in self:
            record.company_id.sudo().automatic_entry_default_journal_id = record.journal_id
        # return
    @api.onchange('new_journal_id')
    def _onchange_new_journal_id(self):
        for record in self:
            record.journal_id = record.new_journal_id.id
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not set(fields) & set(['move_line_ids', 'company_id']):
            return res

        if self.env.context.get('active_model') != 'account.move.line' or not self.env.context.get('active_ids'):
            raise UserError(_('This can only be used on journal items'))
        move_line_ids = self.env['account.move.line'].browse(self.env.context['active_ids'])
        res['move_line_ids'] = [(6, 0, move_line_ids.ids)]

        if any(move.state != 'posted' for move in move_line_ids.mapped('move_id')):
            raise UserError(_('You can only change the period/account for posted journal items.'))
        if any(move_line.reconciled for move_line in move_line_ids):
            raise UserError(_('You can only change the period/account for items that are not yet reconciled.'))
        if any(line.company_id != move_line_ids[0].company_id for line in move_line_ids):
            raise UserError(_('You cannot use this wizard on journal entries belonging to different companies.'))
        res['company_id'] = move_line_ids[0].company_id.id

        # allowed_actions = set(dict(self._fields['action'].selection))
        # if self.env.context.get('default_action'):
        #     allowed_actions = {self.env.context['default_action']}
        # if any(line.account_id.account_type != move_line_ids[0].account_id.account_type for line in move_line_ids):
        #     allowed_actions.discard('change_period')
        # if not allowed_actions:
        #     raise UserError(_('No possible action found with the selected lines.'))
        # res['action'] = allowed_actions.pop()
        return res


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
                line_vals.append({
                    'name': self.desc_name or '',# or aml.name or '',
                    'debit': counterpart_vals['balance'] > 0 and self.company_id.currency_id.round(counterpart_vals['balance']) or 0,
                    'credit': counterpart_vals['balance'] < 0 and self.company_id.currency_id.round(-counterpart_vals['balance']) or 0,
                    'account_id': self.destination_account_id.id,
                    'partner_id': self.partner_ids.id or counterpart_partner.id or None,
                    'amount_currency': counterpart_currency.round((counterpart_vals['balance'] < 0 and -1 or 1) * abs(counterpart_vals['amount_currency'])) or 0,
                    'currency_id': counterpart_currency.id,
                })
 
        # Generate change_account lines' vals
        for (partner, currency, account), lines in grouped_source_lines.items():
            account_balance = sum(line.balance for line in lines)
            if not self.company_id.currency_id.is_zero(account_balance):
                account_amount_currency = currency.round(sum(line.amount_currency for line in lines))
                line_vals.append({
#                     'name': _('Transfer to %s', self.destination_account_id.display_name or _('[Not set]')),
                    'name': self.desc_name or '',
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

            move_data['new_date']['line_ids'] += [
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
                    'debit': reported_debit,
                    'credit': reported_credit,
                    'amount_currency': reported_amount_currency,
                    'currency_id': aml.currency_id.id,
                    'account_id': aml.account_id.id,
                    'partner_id': aml.partner_id.id,
                }),
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
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
                    'debit': reported_credit,
                    'credit': reported_debit,
                    'amount_currency': -reported_amount_currency,
                    'currency_id': aml.currency_id.id,
                    'account_id': aml.account_id.id,
                    'partner_id': aml.partner_id.id,
                }),
                (0, 0, {
                    'name': self.desc_name or aml.name or '',
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

    def _format_transfer_source_log(self, balances_per_account, transfer_move):
        transfer_format = _("<li>{amount} ({debit_credit}) from <strong>%s</strong> were transferred to <strong>{account_target_name}</strong> by {link}</li>")
        content = ''
        for account, balance in balances_per_account.items():
            if account != self.destination_account_id:
                content += self._format_strings(transfer_format, transfer_move, balance)
        return content and '<ul>' + content + '</ul>' or None
    # Transfer utils
    def _format_new_transfer_move_log(self, acc_transfer_per_move):
        format = _("<li>{amount} ({debit_credit}) from {link}, <strong>%(account_source_name)s</strong></li>")
        rslt = _("This entry transfers the following amounts to <strong>%(destination)s</strong> <ul>", destination=self.destination_account_id.name)
        # for move, balances_per_account in acc_transfer_per_move.items():
        #     for account, balance in balances_per_account.items():
                # if account != self.destination_account_id:  # Otherwise, logging it here is confusing for the user
                #     rslt += self._format_strings(format, move, balance) % {'account_source_name': account.name}

        rslt += '</ul>'
        return rslt
