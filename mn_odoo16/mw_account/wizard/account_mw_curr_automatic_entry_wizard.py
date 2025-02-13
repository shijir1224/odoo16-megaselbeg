# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

from collections import defaultdict
from itertools import groupby
import json

class AutomaticEntryWizardMWCurrr(models.TransientModel):
    _name = 'account.automatic.entry.mw.curr'
    _description = 'Create Automatic Entries'



    @api.model
    def _default_dest_acc(self):
        if self.env.context.get('active_model') != 'account.move.line' or not self.env.context.get('active_ids'):
            raise UserError(_('This can only be used on journal items'))
        move_line_ids = self.env['account.move.line'].browse(self.env.context['active_ids'])
        max_amount=0
        self.destination_account_id=False
        max_acc = False
        if len(move_line_ids) >1:
            for line in move_line_ids:
                close_credit=line.debit>0 and abs(line.amount_residual)or 0
                close_debit=line.credit>0 and abs(line.amount_residual) or 0
                if max_amount<close_credit:
                    max_amount=close_credit
                    max_acc=line.account_id and line.account_id.id
                if max_amount<close_debit:
                    max_amount=close_debit
                    max_acc=line.account_id and line.account_id.id
                if max_acc:
                    self.destination_account_id = max_acc
                else:
                    self.destination_account_id =False
        else:
            self.destination_account_id=False

    @api.model
    def _default_lines(self):
        context = self._context
        statement_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        statement_id = statement_ids[0]
        max_date = None
        last_line_id = None
        last_line_amout=None
        statement=self.env['account.bank.statement'].browse(statement_id)
        vals= []
        payment_id=False
        ins_payment_id=False
        if self.env.context.get('active_model') != 'account.move.line' or not self.env.context.get('active_ids'):
            raise UserError(_('This can only be used on journal items'))
        move_line_ids = self.env['account.move.line'].browse(self.env.context['active_ids'])
        vals= []
        self._default_dest_acc()
        sum_debit = 0
        sum_credit = 0
        sum_currency = 0
        for line in move_line_ids:
            close_credit=line.debit>0 and abs(line.amount_residual)or 0
            close_debit=line.credit>0 and abs(line.amount_residual) or 0
            amount_currency_res = line.amount_residual_currency or 0
            sum_debit+=close_debit
            sum_credit+=close_credit
            sum_currency+=amount_currency_res
            if sum_debit>sum_credit:
                if max_date is None or line.date > max_date:
                    max_date = line.date
                    last_line_id = line.id
                    last_line_amout = line.debit
                if line.id == last_line_id:
                    total_amountdd = abs(sum_debit)-abs(sum_credit)
                    total_amount = line.credit - total_amountdd
                    # total_currency_rate = line.credit/line.amount_currency
                    # total_currency = total_amount/total_currency_rate
                    total_currency = abs(sum_currency)-abs(line.amount_residual_currency)

                    vals.append((0,0,{
                    'debit':line.debit,
                    'credit':line.credit,
                    'account_id':line.account_id and line.account_id.id or False,
                    'name':line.name,
                    'partner_id':line.partner_id and line.partner_id.id or False,
                    'move_line_id':line.id,
                    'close_credit':close_credit,
                    'close_debit':total_amount,
                    'residual':line.amount_residual,
                    'currency_id':line.currency_id.id if line.currency_id else 108,
                    'analytic_distribution':line.analytic_distribution if line.analytic_distribution else False,
                    'amount_currency':total_currency           }))
            # elif sum_debit<sum_credit:
            #     if max_date is None or line.date > max_date:
            #         max_date = line.date
            #         last_line_id = line.id
            #         last_line_amout = line.debit
            #     if line.id == last_line_id:
            #         total_amountdd = abs(sum_credit)-abs(sum_debit)
            #         total_amount = line.debit - total_amountdd
            #         # total_currency_rate = line.credit/line.amount_currency
            #         # total_currency = total_amount/total_currency_rate
            #         total_currency = abs(sum_currency)-abs(line.amount_residual_currency)

            #         # print('ssadsadasdasd',total_amountdd)
            #         # print('safsafsafasfasfasfsa',line.credit)
            #         vals.append((0,0,{
            #         'debit':line.debit,
            #         'credit':line.credit,
            #         'account_id':line.account_id and line.account_id.id or False,
            #         'name':line.name,
            #         'partner_id':line.partner_id and line.partner_id.id or False,
            #         'move_line_id':line.id,
            #         'close_credit':total_amount,
            #         'close_debit':close_debit,
            #         'residual':line.amount_residual,
            #         'currency_id':line.currency_id.id if line.currency_id else 108,
            #         'analytic_distribution':line.analytic_distribution if line.analytic_distribution else False,
            #         'amount_currency':total_currency           }))
            else:
                vals.append((0,0,{
                'debit':line.debit,
                'credit':line.credit,
                'account_id':line.account_id and line.account_id.id or False,
                'name':line.name,
                'partner_id':line.partner_id and line.partner_id.id or False,
                'move_line_id':line.id,
                'close_credit':close_credit,
                'close_debit':close_debit,
                'residual':line.amount_residual,
                'currency_id':line.currency_id.id if line.currency_id else 108,
                'analytic_distribution':line.analytic_distribution if line.analytic_distribution else False,
                'amount_currency':amount_currency_res
                }))
        # print('----1-1--1-1-11-1--',vals)
        # sum_debit.append({'vals': close_debit})
        # sum_credit.append({'vals': close_credit})
        return vals
    
    @api.model
    def _default_action(self):
        # print ('aaaaaaaaaaa')
        return 'change_account'
        
    action = fields.Selection([('change_account', 'Change Account'),('change_period', 'Change Period')], required=True, default='change_account')
    move_data = fields.Text(compute="_compute_move_data", help="JSON value of the moves to be created")
    preview_move_data = fields.Text(compute="_compute_preview_move_data", help="JSON value of the data to be displayed in the previewer")
    move_line_ids = fields.Many2many('account.move.line')
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    company_id = fields.Many2one('res.company', required=True, readonly=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    percentage = fields.Float("Percentage", compute='_compute_percentage', readonly=False, store=True, help="Percentage of each line to execute the action on.")
    total_amount = fields.Monetary(compute='_compute_total_amount', store=True, readonly=False, currency_field='company_currency_id', help="Total amount impacted by the automatic entry.")
    journal_id = fields.Many2one('account.journal', required=True, readonly=False, string="Journal",
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
        help="Journal where to create the entry.")

    # change period
    account_type = fields.Selection([('income', 'Revenue'), ('expense', 'Expense')], compute='_compute_account_type', store=True)
    expense_accrual_account = fields.Many2one('account.account', readonly=False,
        domain="[('company_id', '=', company_id),"
               "('account_type', 'not in', ('asset_receivable', 'liability_payable')),"
               "('is_off_balance', '=', False)]",
        compute="_compute_expense_accrual_account",
        inverse="_inverse_expense_accrual_account",
    )
    revenue_accrual_account = fields.Many2one('account.account', readonly=False,
        domain="[('company_id', '=', company_id),"
               "('account_type', 'not in', ('asset_receivable', 'liability_payable')),"
               "('is_off_balance', '=', False)]",
        compute="_compute_revenue_accrual_account",
        inverse="_inverse_revenue_accrual_account",
    )

    # change account
    destination_account_id = fields.Many2one(string="Данс", comodel_name='account.account', help="Account to transfer to.") #default=_default_dest_acc)
    display_currency_helper = fields.Boolean(string="Currency Conversion Helper", compute='_compute_display_currency_helper',
        help="Technical field. Used to indicate whether or not to display the currency conversion tooltip. The tooltip informs a currency conversion will be performed with the transfer.")

    self_line_ids = fields.One2many('account.automatic.entry.mw.curr.line', 'parent_id', string='Lines',default=_default_lines)

    @api.depends('company_id')
    def _compute_expense_accrual_account(self):
        for record in self:
            record.expense_accrual_account = record.company_id.expense_accrual_account_id

    def _inverse_expense_accrual_account(self):
        for record in self:
            record.company_id.sudo().expense_accrual_account_id = record.expense_accrual_account

    @api.depends('company_id')
    def _compute_revenue_accrual_account(self):
        for record in self:
            record.revenue_accrual_account = record.company_id.revenue_accrual_account_id

    def _inverse_revenue_accrual_account(self):
        for record in self:
            record.company_id.sudo().revenue_accrual_account_id = record.revenue_accrual_account

    @api.depends('company_id')
    def _compute_journal_id(self):
        for record in self:
            record.journal_id = record.company_id.automatic_entry_default_journal_id

    def _inverse_journal_id(self):
        for record in self:
            record.company_id.sudo().automatic_entry_default_journal_id = record.journal_id

    @api.constrains('percentage', 'action')
    def _constraint_percentage(self):
        for record in self:
            if not (0.0 < record.percentage <= 100.0) and record.action == 'change_period':
                raise UserError(_("Percentage must be between 0 and 100"))

    @api.depends('percentage', 'move_line_ids')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = (record.percentage or 100) * sum(record.move_line_ids.mapped('balance')) / 100

    @api.depends('total_amount', 'move_line_ids')
    def _compute_percentage(self):
        for record in self:
            total = (sum(record.move_line_ids.mapped('balance')) or record.total_amount)
            if total != 0:
                record.percentage = min((record.total_amount / total) * 100, 100)  # min() to avoid value being slightly over 100 due to rounding error
            else:
                record.percentage = 100

    @api.depends('move_line_ids')
    def _compute_account_type(self):
        for record in self:
            record.account_type = 'income' if sum(record.move_line_ids.mapped('balance')) < 0 else 'expense'

    @api.depends('destination_account_id')
    def _compute_display_currency_helper(self):
        for record in self:
            record.display_currency_helper = bool(record.destination_account_id.currency_id)

    @api.constrains('date', 'move_line_ids')
    def _check_date(self):
        for wizard in self:
            if wizard.move_line_ids.move_id._get_violated_lock_dates(wizard.date, False):
                raise ValidationError(_("The date selected is protected by a lock date"))

            if wizard.action == 'change_period':
                for move in wizard.move_line_ids.move_id:
                    if move._get_violated_lock_dates(move.date, False):
                        raise ValidationError(_("The date of some related entries is protected by a lock date"))

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

        allowed_actions = set(dict(self._fields['action'].selection))
        if self.env.context.get('default_action'):
            allowed_actions = {self.env.context['default_action']}
        if any(line.account_id.account_type != move_line_ids[0].account_id.account_type for line in move_line_ids):
            allowed_actions.discard('change_period')
        if not allowed_actions:
            raise UserError(_('No possible action found with the selected lines.'))
        res['action'] = allowed_actions.pop()
        return res
    
#     @api.onchange('amount_currency', 'tax_id')
#     def _onchange_mark_recompute_taxes(self):
#         ''' Recompute the dynamic onchange based on taxes.
#         If the edited line is a tax line, don't recompute anything as the user must be able to
#         set a custom value.
#         '''
#         for line in self:
#             if line.tax_id:
#                 self._move_autocomplete_invoice_lines_write()


    @api.onchange('action','destination_account_id')
    def _onchange_destination_account_id(self):
        lines =[]
        if self.action=='change_account' and self.destination_account_id:
            sum_debit=0
            sum_credit=0
            currency_amount = 0
            partner_id=False
            analytic_distribution=False
            for l in self.self_line_ids:
                sum_debit+=l.close_debit
                sum_credit+=l.close_credit
                if not partner_id and l.partner_id:
                    partner_id=l.partner_id
                if not analytic_distribution and l.analytic_distribution:
                    analytic_distribution=l.analytic_distribution
            balance=sum_credit-sum_debit
            # print('12313',balance)
            currency_amount_line =0
            if balance!=0:
                currency_amount_line = abs(balance)
            else:
                currency_amount_line = 0
            if balance!=0:
                a=(0,0,{
                    'name': self.destination_account_id.name,
                    'parent_id': self.id,
                    'account_id':self.destination_account_id.id,
                    'close_debit':balance>0 and abs(balance) or 0,
                    'close_credit':balance<0 and abs(balance) or 0,
                    'partner_id':partner_id,
                    'analytic_distribution':analytic_distribution,
                    'currency_id':self.destination_account_id.currency_id.id if self.destination_account_id.currency_id else 108,
                    'amount_currency':currency_amount_line
                })
                lines.append(a)                
            return {'value': {'self_line_ids': lines}}        
        
        
    @api.onchange('self_line_ids')
    def _onchange_self_line_ids(self):
        lines =[]
        for l in self.self_line_ids:
            if l.tax_id:
                tax_acc=l.tax_id.invoice_repartition_line_ids.filtered(lambda x: x.account_id).account_id.id
                if tax_acc: 
                    tax_line=self.self_line_ids.filtered(lambda x: x.account_id and x.account_id.id==tax_acc)
                    if tax_line:
                        continue
                taxes_res = l.tax_id._origin.with_context(force_sign=1).compute_all(l.close_debit>0 and l.close_debit or l.close_credit,
                    quantity=1, currency=l.currency_id, product=False, partner=l.partner_id or False, is_refund=False)
                partner_id=self.self_line_ids.filtered(lambda x:x.partner_id !=False).partner_id.id
                # analytic_distribution=self.self_line_ids.filtered(lambda x:x.analytic_distribution !=False).analytic_distribution
                for t in taxes_res['taxes']:
                    debit=l.close_debit>0 and t['amount'] or 0
                    credit=l.close_credit>0 and t['amount'] or 0
                    curr_amount = 0 
                    if debit >0:
                        curr_amount = debit
                    else:
                        curr_amount = credit
                    # print('currency_amount_line222',l.amount_currency)
                    a=(0,0,{
                        'name': l.tax_id.name,
                        'parent_id': self.id,
                        'account_id':l.tax_id.invoice_repartition_line_ids.filtered(lambda x: x.account_id).account_id.id,
                        'close_debit':debit,
                        'close_credit':credit,
                        'partner_id':partner_id,
                        # 'analytic_distribution':analytic_distribution,
                        'amount_currency': curr_amount,
                        'currency_id' : l.currency_id.id if l.currency_id else False
                    })
                    lines.append(a)                
                a=(1,l.id,{
                    'close_debit': l.close_debit>0 and taxes_res['total_excluded'] or 0,
                    'close_credit':l.close_credit>0 and taxes_res['total_excluded'] or 0,
                    'amount_currency' :taxes_res['total_excluded'] or 0
                })
                lines.append(a)        
        return {'value': {'self_line_ids': lines}}        
        

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
                    'name': counterpart_label,
                    'debit': counterpart_vals['balance'] > 0 and self.company_id.currency_id.round(counterpart_vals['balance']) or 0,
                    'credit': counterpart_vals['balance'] < 0 and self.company_id.currency_id.round(-counterpart_vals['balance']) or 0,
                    'account_id': self.destination_account_id.id,
                    'partner_id': counterpart_partner.id or None,
                    'amount_currency': counterpart_currency.round((counterpart_vals['balance'] < 0 and -1 or 1) * abs(counterpart_vals['amount_currency'])) or 0,
                    'currency_id': counterpart_currency.id if counterpart_currency else 108,
                })

        # Generate change_account lines' vals
        for (partner, currency, account), lines in grouped_source_lines.items():
            account_balance = sum(line.balance for line in lines)
            if not self.company_id.currency_id.is_zero(account_balance):
                account_amount_currency = currency.round(sum(line.amount_currency for line in lines))
                line_vals.append({
                    'name': _('Transfer to %s', self.destination_account_id.display_name or _('[Not set]')),
                    'debit': account_balance < 0 and self.company_id.currency_id.round(-account_balance) or 0,
                    'credit': account_balance > 0 and self.company_id.currency_id.round(account_balance) or 0,
                    'account_id': account.id,
                    'partner_id': partner.id or None,
                    'currency_id': currency.id if currency else 108,
                    'amount_currency': (account_balance > 0 and -1 or 1) * abs(account_amount_currency),
                })
        return [{
            'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': fields.Date.to_string(self.date),
            'ref': self.destination_account_id.display_name and _("Transfer entry to %s", self.destination_account_id.display_name or ''),
            'line_ids': [(0, 0, line) for line in line_vals],
        }]

    @api.depends('move_line_ids', 'journal_id', 'revenue_accrual_account', 'expense_accrual_account', 'percentage', 'date', 'account_type', 'action', 'destination_account_id')
    def _compute_move_data(self):
        for record in self:
            if record.action == 'change_period':
                if any(line.account_id.account_type != record.move_line_ids[0].account_id.account_type for line in record.move_line_ids):
                    raise UserError(_('All accounts on the lines must be of the same type.'))
            if record.action == 'change_period':
#                 record.move_data = json.dumps(record._get_move_dict_vals_change_period())
                return True
            elif record.action == 'change_account':
                ddd=json.dumps(record._get_move_dict_vals_change_account())
                record.move_data = ddd

    @api.depends('move_data')
    def _compute_preview_move_data(self):
        for record in self:
            preview_columns = [
                {'field': 'account_id', 'label': _('Account')},
                {'field': 'name', 'label': _('Label')},
                {'field': 'debit', 'label': _('Debit'), 'class': 'text-right text-nowrap'},
                {'field': 'credit', 'label': _('Credit'), 'class': 'text-right text-nowrap'},
            ]
            if record.action == 'change_account':
                preview_columns[2:2] = [{'field': 'partner_id', 'label': _('Partner')}]

            move_vals = json.loads(record.move_data)
            preview_vals = []
            for move in move_vals[:4]:
                preview_vals += [self.env['account.move']._move_dict_to_preview_vals(move, record.company_id.currency_id)]
            preview_discarded = max(0, len(move_vals) - len(preview_vals))

            record.preview_move_data = json.dumps({
                'groups_vals': preview_vals,
                'options': {
                    'discarded_number': _("%d moves", preview_discarded) if preview_discarded else False,
                    'columns': preview_columns,
                },
            })

    def do_action(self):
        move_vals = json.loads(self.move_data)
        if self.action == 'change_period':
#             return self._do_action_change_period(move_vals)
            return True
        elif self.action == 'change_account':
            return self._do_action_change_account(None)


    def _get_move_dict_vals_mw(self):
        line_vals = []

        # Group data from selected move lines
        counterpart_balances = defaultdict(lambda: defaultdict(lambda: 0))
        grouped_source_lines = defaultdict(lambda: self.env['account.move.line'])

#         for line in self.self_line_ids.filtered(lambda x: x.account_id != self.destination_account_id):
#             counterpart_currency = line.currency_id
#             counterpart_amount_currency = line.amount_currency
# 
#             if self.destination_account_id.currency_id and self.destination_account_id.currency_id != self.company_id.currency_id:
#                 counterpart_currency = self.destination_account_id.currency_id
#                 counterpart_amount_currency = self.company_id.currency_id._convert(line.balance, self.destination_account_id.currency_id, self.company_id, line.date)
# 
#             counterpart_balances[(line.partner_id, counterpart_currency)]['amount_currency'] += counterpart_amount_currency
#             counterpart_balances[(line.partner_id, counterpart_currency)]['balance'] += line.balance
#             grouped_source_lines[(line.partner_id, line.currency_id, line.account_id)] += line
# 
#         # Generate counterpart lines' vals
#         for (counterpart_partner, counterpart_currency), counterpart_vals in counterpart_balances.items():
#             source_accounts = self.move_line_ids.mapped('account_id')
#             counterpart_label = len(source_accounts) == 1 and _("Transfer from %s", source_accounts.display_name) or _("Transfer counterpart")
# 
#             if not counterpart_currency.is_zero(counterpart_vals['amount_currency']):
#                 line_vals.append({
#                     'name': counterpart_label,
#                     'debit': counterpart_vals['balance'] > 0 and self.company_id.currency_id.round(counterpart_vals['balance']) or 0,
#                     'credit': counterpart_vals['balance'] < 0 and self.company_id.currency_id.round(-counterpart_vals['balance']) or 0,
#                     'account_id': self.destination_account_id.id,
#                     'partner_id': counterpart_partner.id or None,
#                     'amount_currency': counterpart_currency.round((counterpart_vals['balance'] < 0 and -1 or 1) * abs(counterpart_vals['amount_currency'])) or 0,
#                     'currency_id': counterpart_currency.id,
#                 })

        # Generate change_account lines' vals
        for line in self.self_line_ids:#.filtered(lambda x: x.account_id != self.destination_account_id):
#             account_amount_currency = currency.round(sum(line.amount_currency for line in lines))

            tmp={
                'name': line.name,#_('Transfer to %s', self.destination_account_id.display_name or _('[Not set]')),
                'debit': line.close_debit,
                'credit': line.close_credit,
                'account_id': line.account_id.id,
                'partner_id': line.partner_id and line.partner_id.id or None,
                'currency_id': line.move_line_id and line.move_line_id.currency_id.id if line.move_line_id.currency_id else 108,
                'analytic_distribution':line.analytic_distribution if line.analytic_distribution else False,
                'amount_currency': line.amount_currency*-1 if line.close_credit else abs(line.amount_currency),
                'currency_id' : line.currency_id.id if line.currency_id else False
            }
            # if line.tax_id:
            #     tmp['tax_ids']=[(6,0,[line.tax_id.id])]
            line_vals.append(tmp)
            
            
        # print ('line_valsline_vals++++++++ ',line_vals)
        return [{
            'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': fields.Date.to_string(self.date),
            'ref': line.name,
            'line_ids': [(0, 0, line) for line in line_vals],
        }]
        
    def _do_action_change_account(self, move_vals):
        move_vals=self._get_move_dict_vals_mw()
        new_move = self.env['account.move'].create(move_vals)
        new_move.action_post()

        # Group lines
        grouped_lines = defaultdict(lambda: self.env['account.move.line'])
        destination_lines = self.move_line_ids.filtered(lambda x: x.account_id == False)# bugd tulgahself.destination_account_id)
        # print ('self.move_line_ids ',self.move_line_ids)
        # print ('destination_lines ',destination_lines)
        for line in self.move_line_ids - destination_lines:
            grouped_lines[(line.partner_id, line.currency_id, line.account_id)] += line

        # Reconcile
        for (partner, currency, account), lines in grouped_lines.items():
            if account.reconcile:
                to_reconcile = lines + new_move.line_ids.filtered(lambda x: x.account_id == account and x.partner_id == partner and x.currency_id == currency)
                to_reconcile.reconcile()

            if destination_lines and self.destination_account_id.reconcile:
                to_reconcile = destination_lines + new_move.line_ids.filtered(lambda x: x.account_id == self.destination_account_id and x.partner_id == partner and x.currency_id == currency)
                to_reconcile.reconcile()

        # Log the operation on source moves
        acc_transfer_per_move = defaultdict(lambda: defaultdict(lambda: 0))  # dict(move, dict(account, balance))
        for line in self.move_line_ids:
            acc_transfer_per_move[line.move_id][line.account_id] += line.balance

        for move, balances_per_account in acc_transfer_per_move.items():
            message_to_log = self._format_transfer_source_log(balances_per_account, new_move)
            if message_to_log:
                move.message_post(body=message_to_log)

        # Log on target move as well
        new_move.message_post(body=self._format_new_transfer_move_log(acc_transfer_per_move))

        return {
            'name': _("Transfer"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': new_move.id,
        }


    # Transfer utils
    def _format_new_transfer_move_log(self, acc_transfer_per_move):
        format = _("<li>{amount} ({debit_credit}) from {link}, <strong>%(account_source_name)s</strong></li>")
        rslt = _("This entry transfers the following amounts to <strong>%(destination)s</strong> <ul>", destination=self.destination_account_id.display_name)
        for move, balances_per_account in acc_transfer_per_move.items():
            for account, balance in balances_per_account.items():
                if account != self.destination_account_id:  # Otherwise, logging it here is confusing for the user
                    rslt += self._format_strings(format, move, balance) % {'account_source_name': account.display_name}

        rslt += '</ul>'
        return rslt

    def _format_transfer_source_log(self, balances_per_account, transfer_move):
        transfer_format = _("<li>{amount} ({debit_credit}) from <strong>%s</strong> were transferred to <strong>{account_target_name}</strong> by {link}</li>")
        content = ''
        for account, balance in balances_per_account.items():
            if account != self.destination_account_id:
                content += self._format_strings(transfer_format, transfer_move, balance)
        return content and '<ul>' + content + '</ul>' or None

    def _format_move_link(self, move):
        move_link_format = "<a href=# data-oe-model=account.move data-oe-id={move_id}>{move_name}</a>"
        return move_link_format.format(move_id=move.id, move_name=move.name)

    def _format_strings(self, string, move, amount):
        return string.format(
            percent=self.percentage,
            name=move.name,
            id=move.id,
            amount=formatLang(self.env, abs(amount), currency_obj=self.company_id.currency_id),
            debit_credit=amount < 0 and _('C') or _('D'),
            link=self._format_move_link(move),
            date=format_date(self.env, move.date),
            new_date=self.date and format_date(self.env, self.date) or _('[Not set]'),
            account_target_name=self.destination_account_id.display_name,
        )



class AutomaticEntryMWCurr(models.TransientModel):
    _name = 'account.automatic.entry.mw.curr.line'
    _description = 'Create Automatic Entries'
    _inherit = "analytic.mixin"

    name = fields.Char('Name')
    move_line_id = fields.Many2one('account.move.line', string="Move",)
    account_id = fields.Many2one('account.account', readonly=False, string="Account")
    partner_id = fields.Many2one('res.partner', readonly=False, string="Partner")
    parent_id = fields.Many2one('account.automatic.entry.mw.curr', readonly=False, string="parent")
    currency_id = fields.Many2one('res.currency', string='Currency', )
    
    
    debit = fields.Float("Debit")
    credit = fields.Float("Credit")
    amount_currency = fields.Float("Amount currency")
    
    close_credit = fields.Float("Closing credit")
    close_debit = fields.Float("Closing debit")
    residual = fields.Float("Residual")
    tax_id = fields.Many2one('account.tax', tring="Tax",)
    tax_group_id = fields.Many2one(related='tax_id.tax_group_id', string='Originator tax group',
        readonly=True, store=True,
        help='technical field for widget tax-group-custom-field')
    tax_base_amount = fields.Float(string="Base Amount", store=True, readonly=True,)
    tax_repartition_line_id = fields.Many2one(comodel_name='account.tax.repartition.line',
        string="Originator Tax Distribution Line", ondelete='restrict', readonly=True,
        check_company=True,
        help="Tax distribution line that caused the creation of this move line, if any")
    

    @api.onchange('close_credit','close_debit')
    def onchange_line_amount(self):
        for item in self:
            if item.currency_id.id == 108 and item.close_credit:
                item.amount_currency = -1*item.close_credit
            elif item.currency_id.id == 108 and item.close_debit:
                item.amount_currency = item.close_debit
            
