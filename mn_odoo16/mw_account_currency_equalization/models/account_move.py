# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo import api, fields, models, Command, _
from datetime import date, timedelta

class AccountMove(models.Model):
    _inherit = "account.move"

    currency_equalized = fields.Boolean('Currency Equalized', default=False)

    def button_draft(self):
        for move in self:
            # if move.currency_equalized:
            #     raise UserError(_('You cannot delete currency equalized move.'))
            for line in move.line_ids:
                eline = self.env['account.currency.equalization.line'].search([('partner_id', '=', line.partner_id.id),('account_id', '=', line.account_id.id), ('state', '!=', 'draft')], order='date DESC', limit=1)
                if eline and eline.equalization_id.date > line.date:
                    raise UserError(_("'%s' account is already equalized. \nFirst you must delete currency equalizations on this account which equalized after %s.")
                                    % (line.account_id.name, line.date))

        return super(AccountMove, self).button_draft()

    def unlink(self):
        for move in self:
            if move.currency_equalized:
                raise UserError(_('You cannot delete currency equalized move.'))
        return super(AccountMove, self).unlink()
    

    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse REAL ханш бол болиулах
        '''
        
        reverse_moves = self.env['account.move']
        # if moves_to_reverse:
        if self.journal_id.not_reverse:
            if cancel:
                lines = self.mapped('line_ids')
                # Avoid maximum recursion depth.
                if lines:
                    lines.remove_move_reconcile()
            return reverse_moves
        else:
            rslt = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
            return rslt #super()._reverse_moves(default_values_list=None, cancel=False)
        
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"    
    
    def get_equalization_balance(self, date, currency, company, select, where, group_by):
        # Ханш тэгшитгэлийн query
        # self.env.cr.execute("SELECT ml.account_id AS account_id, SUM(ml.debit) AS debit, SUM(ml.credit) AS credit, "
        #                             "SUM(ml.amount_currency) AS amount_currency " + select + " "
        #                     "FROM account_move_line ml "
        #                     "JOIN account_move m ON (ml.move_id = m.id) "
        #                     "JOIN account_account a ON (ml.account_id = a.id) "
        #                     "WHERE m.state = 'posted' AND ml.date <= %s AND ml.currency_id = %s AND ml.company_id = %s " + where + " "
        #                     "GROUP BY ml.account_id " + group_by + " "
        #                     "ORDER BY ml.account_id ", (date, currency.id, company.id))
        #авлага өглөг, group by хийх шаардлагагүй
        print('where 2', where )
        print('datreeeee', date )
        self.env.cr.execute("SELECT   " + select + " "
                            "FROM account_move_line ml "
                            "JOIN account_move m ON (ml.move_id = m.id) "
                            "JOIN account_account a ON (ml.account_id = a.id) "
                            "WHERE m.state = 'posted' AND ml.date <= %s AND ml.currency_id = %s AND ml.company_id = %s " + where + " "
                            " " + group_by + " "
                            "ORDER BY ml.account_id ", (date, currency.id, company.id))     

        # mss =self.env.cr.dictfetchall()
        # print('sdsasda',mss)   
        return self.env.cr.dictfetchall()
    

    def _prepare_exchange_difference_move_vals(self, amounts_list, company=None, exchange_date=None):
        """ Prepare values to create later the exchange difference journal entry.
        The exchange difference journal entry is there to fix the debit/credit of lines when the journal items are
        fully reconciled in foreign currency.
        :param amounts_list:    A list of dict, one for each aml.
        :param company:         The company in case there is no aml in self.
        :param exchange_date:   Optional date object providing the date to consider for the exchange difference.
        :return:                A python dictionary containing:
            * move_vals:    A dictionary to be passed to the account.move.create method.
            * to_reconcile: A list of tuple <move_line, sequence> in order to perform the reconciliation after the move
                            creation.
        """
        company = self.company_id or company
        if not company:
            return
        # print ('amounts_list----------------33 ',amounts_list)
        journal = company.currency_exchange_journal_id
        expense_exchange_account = company.expense_currency_exchange_account_id
        income_exchange_account = company.income_currency_exchange_account_id

        move_vals = {
            'move_type': 'entry',
            'date': max(exchange_date or date.min, company._get_user_fiscal_lock_date() + timedelta(days=1)),
            'journal_id': journal.id,
            'line_ids': [],
            'always_tax_exigible': True,
        }
        to_reconcile = []

        for line, amounts in zip(self, amounts_list):
            move_vals['date'] = max(move_vals['date'], line.date)
            # if amounts.get('is_exchange_refund',False):
            #     expense_exchange_account = company.unperformed_exchange_loss_account_id
            #     income_exchange_account = company.unperformed_exchange_gain_account_id
            if 'amount_residual' in amounts:
                amount_residual = amounts['amount_residual']
                amount_residual_currency = 0.0
                if line.currency_id == line.company_id.currency_id:
                    amount_residual_currency = amount_residual
                amount_residual_to_fix = amount_residual
                if line.company_currency_id.is_zero(amount_residual):
                    continue
            elif 'amount_residual_currency' in amounts:
                amount_residual = 0.0
                amount_residual_currency = amounts['amount_residual_currency']
                amount_residual_to_fix = amount_residual_currency
                if line.currency_id.is_zero(amount_residual_currency):
                    continue
            else:
                continue

            if amount_residual_to_fix > 0.0:
                exchange_line_account = expense_exchange_account
            else:
                exchange_line_account = income_exchange_account

            sequence = len(move_vals['line_ids'])
            move_vals['line_ids'] += [
                Command.create({
                    'name': _('Currency exchange rate difference'),
                    'debit': -amount_residual if amount_residual < 0.0 else 0.0,
                    'credit': amount_residual if amount_residual > 0.0 else 0.0,
                    'amount_currency': -amount_residual_currency,
                    'account_id': line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'partner_id': line.partner_id.id,
                    'sequence': sequence,
                }),
                Command.create({
                    'name': _('Currency exchange rate difference'),
                    'debit': amount_residual if amount_residual > 0.0 else 0.0,
                    'credit': -amount_residual if amount_residual < 0.0 else 0.0,
                    'amount_currency': amount_residual_currency,
                    'account_id': exchange_line_account.id,
                    'currency_id': line.currency_id.id,
                    'partner_id': line.partner_id.id,
                    'sequence': sequence + 1,
                }),
            ]
            to_reconcile.append((line, sequence))
            expense_exchange_account = company.expense_currency_exchange_account_id
            income_exchange_account = company.income_currency_exchange_account_id

        return {'move_vals': move_vals, 'to_reconcile': to_reconcile}
    

    @api.model
    def _prepare_reconciliation_single_partial(self, debit_vals, credit_vals):
        """ Prepare the values to create an account.partial.reconcile later when reconciling the dictionaries passed
        as parameters, each one representing an account.move.line.
        :param debit_vals:  The values of account.move.line to consider for a debit line. ТУЛГАЖ БУЙ ГҮЙЛГЭЭНИЙ ДТ ДҮНТЭЙ МӨРҮҮД
        :param credit_vals: The values of account.move.line to consider for a credit line.
        :param debit_vals:  ТУЛГАЖ БУЙ ГҮЙЛГЭЭНИЙ ДТ ДҮНТЭЙ МӨРҮҮД
        :param credit_vals: ТУЛГАЖ БУЙ ГҮЙЛГЭЭНИЙ КР ДҮНТЭЙ МӨРҮҮД
        
        remaining_debit_amount_curr ДТ мөр валютаар үлдэгдэл
        remaining_credit_amount_curr КР мөр валютаар үлдэгдэл
        remaining_debit_amount  ДТ мөр төгрөг үлдэгдэл
        remaining_credit_amount  КР мөр төгрөг үлдэгдэл
        has_debit_zero_residual, has_credit_zero_residual ДТ, КР төгрөгийн үлдэгдэл 0 эсэх
        has_debit_zero_residual_currency, has_credit_zero_residual_currency  ДТ, КР валютын үлдэгдэл 0 эсэх
        min_recon_amount Бүтэн төлөгдөөгүй бол аль бага дүн
        partial_debit_amount аль багыг ДТ ийн түүхэн ханшаар тооцох
        partial_credit_amount аль багыг КТ ийн түүхэн ханшаар тооцох
        
        get_accounting_rate түүхэн ханш буюу төгрөг дүн/валют дүн
        get_odoo_rate ханшийн өдрөөрх тухайн валютын ханш
        :return:            A dictionary:
            * debit_vals:   None if the line has nothing left to reconcile.
            * credit_vals:  None if the line has nothing left to reconcile.
            * partial_vals: The newly computed values for the partial.
            Дараах 2 мөр дарсан
            # partial_debit_amount = min(partial_debit_amount, remaining_debit_amount)
            # partial_credit_amount = min(partial_credit_amount, -remaining_credit_amount)
        """

        def get_odoo_rate(vals):
            if vals.get('record') and vals['record'].move_id.is_invoice(include_receipts=True):
                exchange_rate_date = vals['record'].move_id.invoice_date
            else:
                exchange_rate_date = vals['date']
            return recon_currency._get_conversion_rate(company_currency, recon_currency, vals['company'], exchange_rate_date)

        def get_accounting_rate(vals):
            if company_currency.is_zero(vals['balance']) or vals['currency'].is_zero(vals['amount_currency']):
                return None
            else:
                return abs(vals['amount_currency']) / abs(vals['balance'])
        # print ('self=====: ',self)
        # ==== Determine the currency in which the reconciliation will be done ====
        # In this part, we retrieve the residual amounts, check if they are zero or not and determine in which
        # currency and at which rate the reconciliation will be done.
        res = {
            'debit_vals': debit_vals,
            'credit_vals': credit_vals,
        }
        matched_debit_ids = self.filtered(lambda line: line.matched_debit_ids).matched_debit_ids
        matched_credit_ids = self.filtered(lambda line: line.matched_debit_ids).matched_credit_ids
        
        # reconciled_partials = matched_debit_ids.debit_move_id.move_id._get_all_reconciled_invoice_partials()
        # print ('reconciled_partials ',reconciled_partials)
        # print ('matched_debit_ids ',matched_debit_ids)
        # print ('matched_credit_ids0 ',matched_credit_ids)
        # print ('matched_credit_ids2 ',matched_debit_ids.debit_move_id)
        # print ('matched_credit_ids3 ',matched_debit_ids.credit_move_id)
        debit_exch_id=self.env['account.partial.reconcile'].search([('id','in',matched_debit_ids.ids),
                                                                     ('exchange_move_id','!=',False),
                                                                     ('exchange_move_id.currency_equalized','=',True),
                                                                     ],order='max_date',limit=1) 
        # matched_debit_ids.filtered(lambda line: line.exchange_move_id and line.exchange_move_id.currency_equalized).sorted(key=lambda r: r.max_date)
        # print ('debit_exch_iddebit_exch_id ',debit_exch_id)
        remaining_debit_amount_curr = debit_vals['amount_residual_currency']
        remaining_credit_amount_curr = credit_vals['amount_residual_currency']
        remaining_debit_amount = debit_vals['amount_residual']
        remaining_credit_amount = credit_vals['amount_residual']
        # print ('remaining_credit_amount111 ',remaining_credit_amount)
        # print ('remaining_debit_amount111 ',remaining_debit_amount)
        company_currency = debit_vals['company'].currency_id
        has_debit_zero_residual = company_currency.is_zero(remaining_debit_amount)
        has_credit_zero_residual = company_currency.is_zero(remaining_credit_amount)
        has_debit_zero_residual_currency = debit_vals['currency'].is_zero(remaining_debit_amount_curr)
        has_credit_zero_residual_currency = credit_vals['currency'].is_zero(remaining_credit_amount_curr)
        is_rec_pay_account = debit_vals.get('record') \
                             and debit_vals['record'].account_type in ('asset_receivable', 'liability_payable')
        if debit_vals['currency'] == credit_vals['currency'] == company_currency \
                and not has_debit_zero_residual \
                and not has_credit_zero_residual: #Компаний валютаар
            # Everything is expressed in company's currency and there is something left to reconcile.
            recon_currency = company_currency
            debit_rate = credit_rate = 1.0
            recon_debit_amount = remaining_debit_amount
            recon_credit_amount = -remaining_credit_amount
        elif debit_vals['currency'] == company_currency \
                and is_rec_pay_account \
                and not has_debit_zero_residual \
                and credit_vals['currency'] != company_currency \
                and not has_credit_zero_residual_currency:#АВЛАГА ӨГЛӨГ ДТ КОМПАНИЙН ВАЛЮТТАЙ ТЭНЦҮҮ КР  КОМПАНИЙН ВАЛЮТТАЙ ТЭНЦҮҮ БИШ
            # The credit line is using a foreign currency but not the opposite line.
            # In that case, convert the amount in company currency to the foreign currency one.
            recon_currency = credit_vals['currency']
            debit_rate = get_odoo_rate(debit_vals)
            credit_rate = get_accounting_rate(credit_vals)
            recon_debit_amount = recon_currency.round(remaining_debit_amount * debit_rate)
            recon_credit_amount = -remaining_credit_amount_curr
        elif debit_vals['currency'] != company_currency \
                and is_rec_pay_account \
                and not has_debit_zero_residual_currency \
                and credit_vals['currency'] == company_currency \
                and not has_credit_zero_residual: #АВЛАГА ӨГЛӨГ КР КОМПАНИЙН ВАЛЮТТАЙ ТЭНЦҮҮ БИШ ДТ КОМПАНИЙ ВАЛЮТ
            # The debit line is using a foreign currency but not the opposite line.
            # In that case, convert the amount in company currency to the foreign currency one.
            recon_currency = debit_vals['currency']
            debit_rate = get_accounting_rate(debit_vals)
            credit_rate = get_odoo_rate(credit_vals)
            recon_debit_amount = remaining_debit_amount_curr
            recon_credit_amount = recon_currency.round(-remaining_credit_amount * credit_rate)
            # print ('recon_debit_amount123 ',recon_debit_amount)
            # print ('recon_credit_amount ',recon_credit_amount)
            # print ('111111111111111111111111113')
        elif debit_vals['currency'] == credit_vals['currency'] \
                and debit_vals['currency'] != company_currency \
                and not has_debit_zero_residual_currency \
                and not has_credit_zero_residual_currency: #Компаний биш валютаар үлдэгдэл ДТ КР 2 уулаа #Компаний биш валютаар үлдэгдэл валют тэгээс ялгаатай
                                                            # ИЖИЛ ВАЛЮТ ЭНД ЭХНИЙ УДААД ЗӨВ БОЛГОХ 
            # Both lines are sharing the same foreign currency.
            recon_currency = debit_vals['currency']
            debit_rate = get_accounting_rate(debit_vals)
            credit_rate = get_accounting_rate(credit_vals)
            recon_debit_amount = remaining_debit_amount_curr
            recon_credit_amount = -remaining_credit_amount_curr
            # print ('111111111111111111111111116')
        elif debit_vals['currency'] == credit_vals['currency'] \
                and debit_vals['currency'] != company_currency \
                and (has_debit_zero_residual_currency or has_credit_zero_residual_currency): #Компаний биш валютаар үлдэгдэл валют тэгээс аль нэг ялгаатай
            # Special case for exchange difference lines. In that case, both lines are sharing the same foreign
            # currency but at least one has no amount in foreign currency.
            # In that case, we don't want a rate for the opposite line because the exchange difference is supposed
            # to reduce only the amount in company currency but not the foreign one.
            # print ('remaining_debit_amountllllllllllllllllll ',remaining_debit_amount)
            recon_currency = company_currency
            debit_rate = None
            credit_rate = None
            recon_debit_amount = remaining_debit_amount
            recon_credit_amount = -remaining_credit_amount
            # print ('111111111111111111111111114')
        else:
            # Multiple involved foreign currencies. The reconciliation is done using the currency of the company.
            # print ('remaining_debit_amountmmmmmmmmmmmmmmmm ',remaining_debit_amount)
            recon_currency = company_currency
            debit_rate = get_accounting_rate(debit_vals)
            credit_rate = get_accounting_rate(credit_vals)
            recon_debit_amount = remaining_debit_amount
            recon_credit_amount = -remaining_credit_amount
            # print ('111111111111111111111111115')

        # Check if there is something left to reconcile. Move to the next loop iteration if not.
        skip_reconciliation = False
        if recon_currency.is_zero(recon_debit_amount):
            res['debit_vals'] = None
            skip_reconciliation = True
        if recon_currency.is_zero(recon_credit_amount):
            res['credit_vals'] = None
            skip_reconciliation = True
        if skip_reconciliation:
            return res

        # ==== Match both lines together and compute amounts to reconcile ====

        # Determine which line is fully matched by the other.
        compare_amounts = recon_currency.compare_amounts(recon_debit_amount, recon_credit_amount)
        min_recon_amount = min(recon_debit_amount, recon_credit_amount)
        debit_fully_matched = compare_amounts <= 0
        credit_fully_matched = compare_amounts >= 0
        # ==== Computation of partial amounts ====
        if recon_currency == company_currency:
            # print ('111111')
            # Compute the partial amount expressed in company currency.
            partial_amount = min_recon_amount

            # Compute the partial amount expressed in foreign currency.
            if debit_rate:
                # print ('debit_rate ',debit_rate)
                partial_debit_amount_currency = debit_vals['currency'].round(debit_rate * min_recon_amount)
                partial_debit_amount_currency = min(partial_debit_amount_currency, remaining_debit_amount_curr)
            else:
                partial_debit_amount_currency = 0.0
            if credit_rate:
                partial_credit_amount_currency = credit_vals['currency'].round(credit_rate * min_recon_amount)
                partial_credit_amount_currency = min(partial_credit_amount_currency, -remaining_credit_amount_curr)
            else:
                partial_credit_amount_currency = 0.0
        else:
            # recon_currency != company_currency
            # Compute the partial amount expressed in company currency.
            if debit_rate:
                # print ('debit_rate ',debit_rate)
                partial_debit_amount = company_currency.round(min_recon_amount / debit_rate)
                # partial_debit_amount = min(partial_debit_amount, remaining_debit_amount)
            else:
                partial_debit_amount = 0.0
            # print ('credit_rate ',credit_rate)
            if credit_rate:
                partial_credit_amount = company_currency.round(min_recon_amount / credit_rate)
                # partial_credit_amount = min(partial_credit_amount, -remaining_credit_amount)
            else:
                partial_credit_amount = 0.0
            # print ('partial_debit_amount00 ',partial_debit_amount)
            # print ('partial_credit_amount0 ',partial_credit_amount)
            partial_amount = min(partial_debit_amount, partial_credit_amount)
            # rec_line=len(self.filtered(lambda line: line.account_id.account_type in ('asset_receivable')))>0 and True or False
            # print ('rec_line======== ',rec_line)
            # partial_amount = rec_line and partial_debit_amount or partial_credit_amount # ӨГЛӨГ БОЛ КР

            # print ('partial_amount22222 ',partial_amount)
            # Compute the partial amount expressed in foreign currency.
            # Take care to handle the case when a line expressed in company currency is mimicking the foreign
            # currency of the opposite line.
            if debit_vals['currency'] == company_currency:
                partial_debit_amount_currency = partial_amount
            else:
                partial_debit_amount_currency = min_recon_amount
            if credit_vals['currency'] == company_currency:
                partial_credit_amount_currency = partial_amount
            else:
                partial_credit_amount_currency = min_recon_amount

        # Computation of the partial exchange difference. You can skip this part using the
        # `no_exchange_difference` context key (when reconciling an exchange difference for example).
        if not self._context.get('no_exchange_difference'):
            exchange_lines_to_fix = self.env['account.move.line']
            amounts_list = []
            if recon_currency == company_currency:
                if debit_fully_matched:
                    debit_exchange_amount = remaining_debit_amount_curr - partial_debit_amount_currency
                    if not debit_vals['currency'].is_zero(debit_exchange_amount):
                        if debit_vals.get('record'):
                            exchange_lines_to_fix += debit_vals['record']
                        amounts_list.append({'amount_residual_currency': debit_exchange_amount})
                        # print ('amounts_list1 ',amounts_list)
                        remaining_debit_amount_curr -= debit_exchange_amount
                if credit_fully_matched:
                    credit_exchange_amount = remaining_credit_amount_curr + partial_credit_amount_currency
                    if not credit_vals['currency'].is_zero(credit_exchange_amount):
                        if credit_vals.get('record'):
                            exchange_lines_to_fix += credit_vals['record']
                        amounts_list.append({'amount_residual_currency': credit_exchange_amount})
                        # print ('amounts_list2 ',amounts_list)
                        remaining_credit_amount_curr += credit_exchange_amount

            else:
                # print ('debit_fully_matched1 ',debit_fully_matched)
                if debit_fully_matched:
                    rec_line=len(self.filtered(lambda line: line.account_id.account_type in ('asset_receivable')))>0 and True or False                    
                    if debit_exch_id and rec_line:
                        amounts_list.append({'amount_residual': debit_exch_id.amount,
                                                     'is_exchange_refund':True})                
                    
                    # Create an exchange difference on the remaining amount expressed in company's currency.
                    # print ('remaining_debit_amount ',remaining_debit_amount)
                    # print ('partial_amount122121 ',partial_amount)
                    debit_exchange_amount = remaining_debit_amount - partial_amount
                    if not company_currency.is_zero(debit_exchange_amount):
                        if debit_vals.get('record'):
                            exchange_lines_to_fix += debit_vals['record']
                        amounts_list.append({'amount_residual': debit_exchange_amount,
                                             'is_exchange_refund':True})
                        # print ('amounts_list3 ',amounts_list)
                        remaining_debit_amount -= debit_exchange_amount
                        if debit_vals['currency'] == company_currency:
                            remaining_debit_amount_curr -= debit_exchange_amount
                else:
                    # Create an exchange difference ensuring the rate between the residual amounts expressed in
                    # both foreign and company's currency is still consistent regarding the rate between
                    # 'amount_currency' & 'balance'.
                    debit_exchange_amount = partial_debit_amount - partial_amount
                    if company_currency.compare_amounts(debit_exchange_amount, 0.0) > 0:
                        if debit_vals.get('record'):
                            exchange_lines_to_fix += debit_vals['record']
                        amounts_list.append({'amount_residual': debit_exchange_amount,
                                             'is_exchange_refund':True})
                        # print ('amounts_list4 ',amounts_list)
                        remaining_debit_amount -= debit_exchange_amount
                        if debit_vals['currency'] == company_currency:
                            remaining_debit_amount_curr -= debit_exchange_amount
                # print ('credit_fully_matched2 ',credit_fully_matched)
                if credit_fully_matched:
                    rec_line=len(self.filtered(lambda line: line.account_id.account_type in ('asset_receivable')))>0 and True or False                    
                    if debit_exch_id and not rec_line:
                        amounts_list.append({'amount_residual': debit_exch_id.amount,
                                                     'is_exchange_refund':True})                
                    
                    # Create an exchange difference on the remaining amount expressed in company's currency.
                    # print ('remaining_credit_amount ',remaining_credit_amount)
                    # print ('partial_amount=======: ',partial_amount)
                    credit_exchange_amount = remaining_credit_amount + partial_amount
                    # print ('credit_exchange_amount ',credit_exchange_amount)
                    if not company_currency.is_zero(credit_exchange_amount):
                        if credit_vals.get('record'):
                            exchange_lines_to_fix += credit_vals['record']
                        amounts_list.append({'amount_residual': credit_exchange_amount,
                                             'is_exchange_refund':True})
                        # print ('amounts_list5 ',amounts_list)
                        remaining_credit_amount -= credit_exchange_amount
                        if credit_vals['currency'] == company_currency:
                            remaining_credit_amount_curr -= credit_exchange_amount
                else:
                    # Create an exchange difference ensuring the rate between the residual amounts expressed in
                    # both foreign and company's currency is still consistent regarding the rate between
                    # 'amount_currency' & 'balance'.
                    credit_exchange_amount = partial_amount - partial_credit_amount
                    if company_currency.compare_amounts(credit_exchange_amount, 0.0) < 0:
                        if credit_vals.get('record'):
                            exchange_lines_to_fix += credit_vals['record']
                        amounts_list.append({'amount_residual': credit_exchange_amount,
                                             'is_exchange_refund':True})
                        # print ('amounts_list6 ',amounts_list)
                        remaining_credit_amount -= credit_exchange_amount
                        if credit_vals['currency'] == company_currency:
                            remaining_credit_amount_curr -= credit_exchange_amount

            if exchange_lines_to_fix:
                # print ('amounts_listamounts_list ',amounts_list)
                # print ('exchange_lines_to_fix ',exchange_lines_to_fix)
                res['exchange_vals'] = exchange_lines_to_fix._prepare_exchange_difference_move_vals(
                    amounts_list,
                    exchange_date=max(debit_vals['date'], credit_vals['date']),
                )

        # ==== Create partials ====

        remaining_debit_amount -= partial_amount
        remaining_credit_amount += partial_amount
        remaining_debit_amount_curr -= partial_debit_amount_currency
        remaining_credit_amount_curr += partial_credit_amount_currency

        res['partial_vals'] = {
            'amount': partial_amount,
            'debit_amount_currency': partial_debit_amount_currency,
            'credit_amount_currency': partial_credit_amount_currency,
            'debit_move_id': debit_vals.get('record') and debit_vals['record'].id,
            'credit_move_id': credit_vals.get('record') and credit_vals['record'].id,
        }

        debit_vals['amount_residual'] = remaining_debit_amount
        debit_vals['amount_residual_currency'] = remaining_debit_amount_curr
        credit_vals['amount_residual'] = remaining_credit_amount
        credit_vals['amount_residual_currency'] = remaining_credit_amount_curr

        if debit_fully_matched:
            res['debit_vals'] = None
        if credit_fully_matched:
            res['credit_vals'] = None
        # print ('res=== ',res)
        return res    