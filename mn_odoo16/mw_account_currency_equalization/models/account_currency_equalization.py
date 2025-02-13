# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from PIL.ImageChops import difference


class AccountCurrencyEqualization(models.Model):
    _name = "account.currency.equalization"
    _inherit = ['mail.thread']
    _description = "Equalize Currency Rate"
    # Гадаад валютаар хийгдсэн журналын бичилтүүдэд ханшийн тэгшитгэл хийнэ.

    def _default_journal(self):
        # Санхүүгийн тохиргоонд тохируулсан Ханшийн тэгшитгэлийн журнал автоматаар дуудагдана
        if self.env.company and self.env.company.exchange_equation_journal_id:
            return self.env.company.exchange_equation_journal_id

    def _defaut_cashflow(self):
        # Санхүүгийн тохиргоонд тохируулсан Валютын мөнгөн гүйлгээний төрөл автоматаар дуудагдана
        if self.env.company and self.env.company.exchange_equation_cashflow_id:
            return self.env.company.exchange_equation_cashflow_id

    name = fields.Char('Name', required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    date = fields.Date('Date', required=True, default=lambda self: fields.datetime.now(), readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, default=_default_journal, tracking=True,
                                 readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, states={'approved': [('readonly', True)]})
    rate = fields.Float('Currency rate', digits=(4, 2), required=True, tracking=True, readonly=True,
                        states={'draft': [('readonly', False)]})
    rate_date = fields.Date('Rate Date', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    cashflow_id = fields.Many2one('account.cash.move.type', 'Cashflow Type', default=_defaut_cashflow, 
                                  readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('liquidity', 'Liquidity Accounts'),
                             ('partner', 'Partner Balances')], string='Currency Equation Type', default='liquidity', required=True, readonly=True, states={'draft': [('readonly', False)]})
    entry_count = fields.Integer(compute='_entry_count', string='# Entries')
    line_ids = fields.One2many('account.currency.equalization.line', 'equalization_id', 'Lines')
    state = fields.Selection([('draft', 'Draft'),
                              ('started', 'Started'),
                              ('equalized', 'Equalized')], string='State', default='draft', required=True, tracking=True)
    description = fields.Text('Description')
    partner_id = fields.Many2one('res.partner', 'Partner')
    account_id = fields.Many2one('account.account', 'Account')
    
    @api.depends('line_ids.move_id')
    def _entry_count(self):
        for obj in self:
            res = self.env['account.currency.equalization.line'].search_count([('equalization_id', '=', obj.id), ('move_id', '!=', False)])
            obj.entry_count = res or 0

    @api.onchange('date', 'type', 'currency_id')
    def onchange_name(self):
        # Огноо, төрөл болон валютаар нэр талбарыг бөглөх
        self.rate = self.set_currency()
        name = ''
        if self.date:
            name += _('%s - ') % self.date
        if self.type:
            if self.type == 'liquidity':
                name += _('Liquidity Accounts ')
            else:
                name += _('Partner Balances ')
        if self.currency_id:
            name += _('%s ') % self.currency_id.name
        name += _('equalize currency rate')
        self.name = name

    @api.onchange('company_id')
    def onchange_domain(self):
        # Компанийн үндсэн валютыг харагдуулахгүй болгох
        return {'domain': {'currency_id': [('id', '!=', self.company_id.currency_id.id)]}}

    def open_entries(self):
        move_ids = []
        for obj in self:
            for line in obj.line_ids:
                if line.move_id:
                    move_ids.append(line.move_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }

    def set_currency(self):
        # Тухайн огноо болон вальютанд харгалзах ханш гарч ирнэ, тухайн огнооны өмнөх хаалтын ханшаар тэгшитгэл хийгдэнэ.
        if self.date and self.currency_id:
            rate = self.env['res.currency']._get_conversion_rate(self.currency_id, self.company_id.currency_id,
                                                               self.company_id, self.date)
            # if rate_id:
            #     rate = rate_id[0].rate
            #     self.rate_date = rate_id[0].name
            return rate

    def unlink(self):
        if self.state != 'draft':
            raise UserError(_('Delete only draft in state'))
        return super(AccountCurrencyEqualization, self).unlink()

    def action_start(self):
        self._unlink_account_move()
        self.line_ids.unlink()
        precision = self.env['decimal.precision'].precision_get('Account')
        line_obj = self.env['account.currency.equalization.line']
        move_line_obj = self.env['account.move.line']
        where = ''
        select = ''
        group_by = ''
        
        if self.type == 'liquidity':
            select += 'SUM(ml.debit) AS debit, SUM(ml.credit) AS credit, \
                sum(ml.amount_currency) AS amount_residual_currency,sum(ml.amount_currency) AS amount_currency, ml.account_id,ml.currency_id '
            where += "AND a.account_type = 'asset_cash' and a.currency_id={} ".format(self.currency_id.id)
            if self.account_id:
                where += " AND ml.account_id={} ".format(self.account_id.id)

            group_by="GROUP BY ml.account_id,ml.currency_id"
        else:
            where += "AND a.account_type in ('liability_payable', 'asset_receivable') "
            select += 'ml.account_id AS account_id, ml.debit AS debit, ml.credit AS credit, \
                        ml.amount_currency AS amount_currency,ml.amount_residual_currency, ml.partner_id AS partner_id, ml.id as line_id '
            if self.partner_id:
                where += " AND ml.partner_id={}".format(self.partner_id.id)
            if self.account_id:
                where += " AND ml.account_id={}".format(self.account_id.id)
            # group_by += ', ml.partner_id, m.id '
                # 51017
        # print ('where ',where)
        # print ('select ',select)
        # print ('group_by ',group_by)
        lines = move_line_obj.get_equalization_balance(self.date, self.currency_id, self.company_id, select, where, group_by)
        # print ('lines ',lines)
        for line in lines:
            # print ('line ',line)
            if line['amount_residual_currency']==0: # валютаар үлдэгдэл 0 бол уншихгүй байх
                continue
            amount_currency = float_round(line['amount_currency'], precision_digits=precision)
            # if amount_currency != 0:
            debit = float_round(line['debit'], precision_digits=precision)
            credit = float_round(line['credit'], precision_digits=precision)
            diff = debit - credit
            if amount_currency != 0:
                rate = float_round(diff / amount_currency, precision_digits=precision)
                difference=amount_currency*self.rate - (diff)
                difference=amount_currency*self.rate - (diff)
            else:
                rate=0
                if diff > 0:
                    difference=-1*diff
                else:
                    difference=diff
            #Мөнгөн хөрөнгө д difference
            # difference=amount_currency*self.rate - (diff)
            if rate != self.rate:
                vals={'equalization_id': self.id,
                                    'account_id': line['account_id'],
                                    'partner_id': line['partner_id'] if self.type == 'partner' else False,
                                    'debit': diff if diff > 0 else 0,
                                    'credit': abs(diff) if diff < 0 else 0,
                                    'amount_currency': amount_currency,
                                    'difference':difference,
                                    'old_rate': rate,
                                    'amount_residual_currency':line['amount_residual_currency']
                                    }
                if line.get('line_id',False):
                    vals.update({'rec_pay_move_id':line['line_id']})
                line_obj.create(vals)
        self.write({'state': 'started'})

    def get_analytic_account(self):
        return self.company_id.exchange_equation_analytic_account_id.id if self.company_id.exchange_equation_analytic_account_id else False

    def _get_equalization_move_line_vals(self, description, name, diff_amount, gain_loss_account, account, partner, cashflow_id, analytic_account_id):
        self.ensure_one()
        # print ('diff_amount111 ',diff_amount)
        # diff_amount  = account.account_type == 'liability_payable' and diff_amount or -diff_amount
        # if account.account_type == 'liability_payable':
        #     diff_amount = diff_amount 
        # elif account.account_type == 'asset_receivable':
        #     diff_amount = diff_amount
        # print ('diff_amount000 ',diff_amount)
        return [(0, 0, {'name': _('%s - %s') % (description, name),
                        'debit': diff_amount < 0 and -diff_amount or 0.0,
                        'credit': diff_amount > 0 and diff_amount or 0.0,
                        'account_id': gain_loss_account,
                        'partner_id': partner,
                        # 'analytic_account_id': analytic_account_id,
                        'company_id': self.company_id.id,
                        'date': self.date,
                        'journal_id': self.journal_id.id,
                        'currency_id': self.currency_id.id,
                        'amount_currency': 0, }),
                (0, 0, {'name': description,
                        'debit': diff_amount > 0 and diff_amount or 0.0,
                        'credit': diff_amount < 0 and -diff_amount or 0.0,
                        'account_id':  account.id,
                        'partner_id': partner,
                        # 'cashflow_id': cashflow_id if self.type == 'liquidity' else False,
                        'company_id': self.company_id.id,
                        'currency_id': self.currency_id.id,
                        'date': self.date,
                        'journal_id': self.journal_id.id,
                        'amount_currency': 0, })]

    def action_equalize(self):
        # Батлан ханшийн тэгшитгэлийн журналын бичилт үүсгэнэ
        precision = self.env['decimal.precision'].precision_get('Account')
        amove_obj = self.env['account.move']
        analytic_account_id = self.get_analytic_account()
        cashflow_id = False
        if self.cashflow_id:
            cashflow_id = self.cashflow_id.id
        for line in self.line_ids:
            added_debit = added_credit = 0
            partner = False
            description = u'%s, %s %s' % (self.date, line.account_id.code, line.account_id.name)
            if line.partner_id:
                partner = line.partner_id.id
                description += u', %s' % (line.partner_id.name)
            balance = line.debit - line.credit
            # converted_amount = float_round(self.rate * line.amount_currency, precision_digits=precision)
            # diff_amount = float_round(converted_amount - balance, precision_digits=precision)
            converted_amount = float_round(self.rate * line.rec_pay_move_id.amount_residual_currency, precision_digits=precision)
            print ('converted_amount123 ',converted_amount)
            print ('line.rec_pay_move_id.amount_residual ',line.rec_pay_move_id.amount_residual)
            if self.type=='partner':
                diff_amount = float_round(converted_amount - line.rec_pay_move_id.amount_residual, precision_digits=precision)
            else:
                diff_amount = line.difference
            print ('diff_amount12 ',diff_amount)
            if self.company_id.currency_id.is_zero(diff_amount):
                # Ханшийн зөрүү үүсээгүй болно.
                continue
            if diff_amount > 0 :
                # Ханшийн зөрүүний ашиг
                if self.company_id.unperformed_exchange_gain_account_id:
                    gain_loss_account = self.company_id.unperformed_exchange_gain_account_id.id
                else:
                    raise UserError(_('There is no unperformed rate exchange gain account defined this company.'))
                name = _("Unperformed Rate Exchange Gain")  # Валютын ханшийн зөрүүгийн  хэрэгжээгүй ашиг
                added_debit = diff_amount
            else:
                # Ханшийн зөрүүний алдагдал
                if self.company_id.unperformed_exchange_loss_account_id:
                    gain_loss_account = self.company_id.unperformed_exchange_loss_account_id.id
                else:
                    raise UserError(_('There is no unperformed rate exchange loss account defined this company.'))
                name = _("Unperformed Rate Exchange Loss")  # Валютын ханшийн зөрүүгийн  хэрэгжээгүй  зардал
                added_credit = abs(diff_amount)
            # Ханшийн зөрүүг журналд бичих
            line_ids = self._get_equalization_move_line_vals(description, name, diff_amount, gain_loss_account, line.account_id, partner, cashflow_id, analytic_account_id)
            print ('line_ids=== ',line_ids)
            move_id = amove_obj.create({
                'journal_id': self.journal_id.id,
                'date': self.date,
                'narration': line.rec_pay_move_id and line.rec_pay_move_id.name or description,
                'currency_equalized': True,
                'line_ids': line_ids
            })
            move_id.action_post()
            print ('move_id ',move_id)
            rec_line=move_id.line_ids.filtered(lambda line: line.account_id.account_type in ('liability_payable','asset_receivable'))
            print ('rec_line123: ',rec_line)
            if self.type=='partner' and rec_line and line.rec_pay_move_id:
                amount=rec_line.credit and -rec_line.credit or rec_line.debit
                partials_vals_list={'amount':amount,
                                    'debit_amount_currency':0,
                                    'credit_amount_currency':0,
                                    'debit_move_id':rec_line.id,
                                    'exchange_move_id':rec_line.move_id.id,
                                    'credit_move_id':line.rec_pay_move_id.id}
                # (rec_line+line.rec_pay_move_id).reconcile()
                partials = self.env['account.partial.reconcile'].create(partials_vals_list)
            diff = line.debit + added_debit - line.credit - added_credit
            line.write({'move_id': move_id.id,
                            'added_debit': added_debit,
                            'added_credit': added_credit,
                            'total_debit': diff if diff > 0 else 0,
                            'total_credit': abs(diff) if diff < 0 else 0
                            })
        self.write({'state': 'equalized'})

    def _unlink_account_move(self):
        # Үүссэн журналын бичилтүүдийг устгах
        for obj in self:
            for line in obj.line_ids:
                if line.move_id:
                    line.move_id.currency_equalized = False
                    line.move_id.button_cancel()
                    line.move_id.with_context(force_delete=True).unlink()
        return True

    def action_to_draft(self):
        # Ноороглох
        self._unlink_account_move()
        self.line_ids.unlink()
        self.write({'state': 'draft'})


class AccountCurrencyEqualizationLine(models.Model):
    _name = "account.currency.equalization.line"
    _description = "Equalize Currency Rate Line"

    equalization_id = fields.Many2one('account.currency.equalization', 'Equalization', ondelete="cascade")
    account_id = fields.Many2one('account.account')
    partner_id = fields.Many2one('res.partner', 'Partner')
    currency_id = fields.Many2one('res.currency', related='equalization_id.currency_id', string='Currency')
    date = fields.Date(related='equalization_id.date', string='Date')
    debit = fields.Float('Debit', default=0)
    credit = fields.Float('Credit', default=0)
    amount_currency = fields.Float('Amount Currency', default=0)
    old_rate = fields.Float('Old Currency rate', default=0)
    new_rate = fields.Float('New Currency rate', related='equalization_id.rate')
    move_id = fields.Many2one('account.move', 'Account Move')
    rec_pay_move_id = fields.Many2one('account.move.line', 'Payable Move')
    added_debit = fields.Float('Added Debit', default=0)
    added_credit = fields.Float('Added Credit', default=0)
    total_debit = fields.Float('Total Debit', default=0)
    total_credit = fields.Float('Total Credit', default=0)
    difference = fields.Float('Total difference', default=0)
    state = fields.Selection(related="equalization_id.state")
    amount_residual_currency  = fields.Float('Residual currency', default=0)





class AccountJournal(models.Model):
    _inherit = 'account.journal'

    not_reverse = fields.Boolean('Эсрэг бичихгүй?',  default=False)
