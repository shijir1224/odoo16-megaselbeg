# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date
from odoo import fields, models, api, _,Command
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.addons.mw_base.verbose_format import verbose_format

class AccountMove(models.Model):
    _inherit = "account.move"

    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse REAL ханш бол болиулах
        '''
        # print ('self.self._context ',self._context)
        # moves_to_reverse = self.env['account.partial.reconcile'].search([('exchange_move_id', '=', self.id)])
        # query = """
        #        select exchange_move_id,id from account_partial_reconcile where exchange_move_id in ({0}) 
        #     """.format(','.join(map(str, self.ids)))
        # print ('query ',query)
        # self.env.cr.execute(query)
        # ids = self.env.cr.dictfetchall()
        
        reverse_moves = self.env['account.move']
        # if moves_to_reverse:
        if self._context.get('is_mw_exchange',False):
            if cancel:
                lines = self.mapped('line_ids')
                # Avoid maximum recursion depth.
                if lines:
                    lines.remove_move_reconcile()
            return reverse_moves
        else:
            rslt = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
            return rslt #super()._reverse_moves(default_values_list=None, cancel=False)
        
    
    amount_str_mw = fields.Char(string='Үсгээр дүн', compute="amount_str")
    amount_total_signed_mw = fields.Float(string="Нийт дүн", compute="_compute_amount_total_signed_mw")
    @api.depends('amount_total_signed')
    def _compute_amount_total_signed_mw(self):
        for item in self:
            if item.amount_total_signed:
                item.amount_total_signed_mw = round(abs(item.amount_total_signed), 2)
            else:
                item.amount_total_signed_mw = 0 
    @api.onchange('date')
    def onchnage_invoice_date(self):
        if self.date:
            self.invoice_date = self.date

    def _get_accounting_date(self, invoice_date, has_tax):
        """Get correct accounting date for previous periods, taking tax lock date into account.
        When registering an invoice in the past, we still want the sequence to be increasing.
        We then take the last day of the period, depending on the sequence format.

        If there is a tax lock date and there are taxes involved, we register the invoice at the
        last date of the first open period.
        :param invoice_date (datetime.date): The invoice date
        :param has_tax (bool): Iff any taxes are involved in the lines of the invoice
        :return (datetime.date):
        TUR SARIIN SUULIIG DARSAN
        """
        lock_dates = self._get_violated_lock_dates(invoice_date, has_tax)
        today = fields.Date.today()
        highest_name = self.highest_name or self._get_last_sequence(relaxed=True, lock=False)
        number_reset = self._deduce_sequence_number_reset(highest_name)
        if lock_dates:
            invoice_date = lock_dates[-1][0] + timedelta(days=1)
        if self.is_sale_document(include_receipts=True):
            if lock_dates:
                if not highest_name or number_reset == 'month':
                    return min(today, date_utils.get_month(invoice_date)[1])
                elif number_reset == 'year':
                    return min(today, date_utils.end_of(invoice_date, 'year'))
        # else:
        #     if not highest_name or number_reset == 'month':
        #         if (today.year, today.month) > (invoice_date.year, invoice_date.month):
        #             return date_utils.get_month(invoice_date)[1]
        #         else:
        #             return max(invoice_date, today)
        #     elif number_reset == 'year':
        #         if today.year > invoice_date.year:
        #             return date(invoice_date.year, 12, 31)
        #         else:
        #             return max(invoice_date, today)
        # print ('invoice_dateinvoice_dateinvoice_dateinvoice_dateinvoice_dateinvoice_dateinvoice_date ',invoice_date)
        return invoice_date
    
    def unlink(self):
        for move in self:
            if not self.env.user.has_group('mw_account.group_mn_account_move_unlink') and not move.asset_id:
                raise UserError(u'({0}) Гүйлгээ устгах эрхгүй байна. Эрх бүхий нягтланд хандана уу'.format( move.name))
            elif not self.env.user.has_group('mw_asset.group_mn_asset_accountant') and move.asset_id:
                raise UserError(u'({0}) Гүйлгээ устгах эрхгүй байна. Эрх бүхий нягтланд хандана уу'.format( move.name))
        return super().unlink()
    # invoice_date = fields.Date(related='date', store=True) #ALDAA
    
    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if 'state' in vals:
            for move in self:
                if vals['state']=='draft':
                    if not self.env.user.has_group('mw_account.group_mn_account_move_draft'):
                        raise UserError(u'({0}) Гүйлгээ ноороглох эрхгүй байна. Нягтланд хандана уу'.format( move.name))
        return res
    
    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.
        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        # return partial.unlink()
        is_exchange=False
        if partial.exchange_move_id:
            is_exchange=True
        return partial.with_context(force_delete=True,is_mw_exchange=is_exchange).unlink()     
    # def write(self, vals):
    #     for move in self:
    #         for record in move.line_ids:
    #             if record.partner_id and record.partner_id.employee==True and not record.analytic_distribution:
    #                 emp_id = self.env['hr.employee'].search([('partner_id','=',record.partner_id.id)])
    #                 for emp_ids in emp_id:
    #                     if emp_ids:
    #                         des_model = self.env['account.analytic.distribution.model'].search([
    #                             ('department_id','=',emp_ids.department_id.id),
    #                             ('company_id','=',self.company_id.id),
    #                             ], limit=1)
    #                         for item in des_model:
    #                             if des_model:
    #                                 record.analytic_distribution = des_model.analytic_distribution
    #         return super(AccountMove, self).write(vals)
    @api.depends('amount_total_signed')
    def amount_str(self):
        for item in self:
            if item.amount_total_signed > 0:
                item.amount_str_mw = verbose_format(abs(item.amount_total_signed))
            elif item.amount_total_signed < 0:
                item.amount_str_mw = verbose_format(abs(item.amount_total_signed))
            else:
                item.amount_str_mw=''

    def action_draft_button_move(self):
        accounts = self.env['account.move'].browse(self._context['active_ids'])
        for account in accounts:
            account.button_draft()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    def reconcile(self):
        ''' Reconcile the current move lines all together.
        :return: A dictionary representing a summary of what has been done during the reconciliation:
                * partials:             A recorset of all account.partial.reconcile created during the reconciliation.
                * exchange_partials:    A recorset of all account.partial.reconcile created during the reconciliation
                                        with the exchange difference journal entries.
                * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
                                        in the involved lines.
                * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
                БИЧИЛТ АВТО ХААХ ДЭЭР АЛЬ ХЭДИЙН ТУЛГАГДСАНГ БОЛИУЛСАН
        '''
        results = {'exchange_partials': self.env['account.partial.reconcile']}

        if not self:
            return results

        not_paid_invoices = self.move_id.filtered(lambda move:
            move.is_invoice(include_receipts=True)
            and move.payment_state not in ('paid', 'in_payment')
        )

        # ==== Check the lines can be reconciled together ====
        company = None
        account = None
        for line in self:
            # print ('line1234: ',line)
            if line.reconciled:
                if not self._context.get('mw_auto',False):
                    raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
                # print (b)
            if not line.account_id.reconcile and line.account_id.account_type not in ('asset_cash', 'liability_credit_card'):
                raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
                                % line.account_id.display_name)
            if line.move_id.state != 'posted':
                raise UserError(_('You can only reconcile posted entries.'))
            if company is None:
                company = line.company_id
            elif line.company_id != company:
                raise UserError(_("Entries doesn't belong to the same company: %s != %s")
                                % (company.display_name, line.company_id.display_name))
            if account is None:
                account = line.account_id
            elif line.account_id != account:
                raise UserError(_("Entries are not from the same account: %s != %s")
                                % (account.display_name, line.account_id.display_name))

        if self._context.get('reduced_line_sorting'):
            sorting_f = lambda line: (line.date_maturity or line.date, line.currency_id)
        else:
            sorting_f = lambda line: (line.date_maturity or line.date, line.currency_id, line.amount_currency)
        sorted_lines = self.sorted(key=sorting_f)

        # ==== Collect all involved lines through the existing reconciliation ====

        involved_lines = sorted_lines._all_reconciled_lines()
        involved_partials = involved_lines.matched_credit_ids | involved_lines.matched_debit_ids

        # ==== Create partials ====

        partial_no_exch_diff = bool(self.env['ir.config_parameter'].sudo().get_param('account.disable_partial_exchange_diff'))
        sorted_lines_ctx = sorted_lines.with_context(no_exchange_difference=self._context.get('no_exchange_difference') or partial_no_exch_diff)
        partials = sorted_lines_ctx._create_reconciliation_partials()
        results['partials'] = partials
        involved_partials += partials
        exchange_move_lines = partials.exchange_move_id.line_ids.filtered(lambda line: line.account_id == account)
        involved_lines += exchange_move_lines
        exchange_diff_partials = exchange_move_lines.matched_debit_ids + exchange_move_lines.matched_credit_ids
        involved_partials += exchange_diff_partials
        results['exchange_partials'] += exchange_diff_partials

        # ==== Create entries for cash basis taxes ====

        is_cash_basis_needed = account.company_id.tax_exigibility and account.account_type in ('asset_receivable', 'liability_payable')
        if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
            tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
            results['tax_cash_basis_moves'] = tax_cash_basis_moves

        # ==== Check if a full reconcile is needed ====

        def is_line_reconciled(line, has_multiple_currencies):
            # Check if the journal item passed as parameter is now fully reconciled.
            return line.reconciled \
                   or (line.company_currency_id.is_zero(line.amount_residual)
                       if has_multiple_currencies
                       else line.currency_id.is_zero(line.amount_residual_currency)
                   )

        has_multiple_currencies = len(involved_lines.currency_id) > 1
        if all(is_line_reconciled(line, has_multiple_currencies) for line in involved_lines):
            # ==== Create the exchange difference move ====
            # This part could be bypassed using the 'no_exchange_difference' key inside the context. This is useful
            # when importing a full accounting including the reconciliation like Winbooks.

            exchange_move = self.env['account.move']
            caba_lines_to_reconcile = None
            if not self._context.get('no_exchange_difference'):
                # In normal cases, the exchange differences are already generated by the partial at this point meaning
                # there is no journal item left with a zero amount residual in one currency but not in the other.
                # However, after a migration coming from an older version with an older partial reconciliation or due to
                # some rounding issues (when dealing with different decimal places for example), we could need an extra
                # exchange difference journal entry to handle them.
                exchange_lines_to_fix = self.env['account.move.line']
                amounts_list = []
                exchange_max_date = date.min
                for line in involved_lines:
                    if not line.company_currency_id.is_zero(line.amount_residual):
                        exchange_lines_to_fix += line
                        amounts_list.append({'amount_residual': line.amount_residual})
                    elif not line.currency_id.is_zero(line.amount_residual_currency):
                        exchange_lines_to_fix += line
                        amounts_list.append({'amount_residual_currency': line.amount_residual_currency})
                    exchange_max_date = max(exchange_max_date, line.date)
                exchange_diff_vals = exchange_lines_to_fix._prepare_exchange_difference_move_vals(
                    amounts_list,
                    company=involved_lines[0].company_id,
                    exchange_date=exchange_max_date,
                )

                # Exchange difference for cash basis entries.
                # If we are fully reversing the entry, no need to fix anything since the journal entry
                # is exactly the mirror of the source journal entry.
                if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
                    caba_lines_to_reconcile = involved_lines._add_exchange_difference_cash_basis_vals(exchange_diff_vals)

                # Create the exchange difference.
                if exchange_diff_vals['move_vals']['line_ids']:
                    exchange_move = involved_lines._create_exchange_difference_move(exchange_diff_vals)
                    if exchange_move:
                        exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == account)

                        # Track newly created lines.
                        involved_lines += exchange_move_lines

                        # Track newly created partials.
                        exchange_diff_partials = exchange_move_lines.matched_debit_ids \
                                                 + exchange_move_lines.matched_credit_ids
                        involved_partials += exchange_diff_partials
                        results['exchange_partials'] += exchange_diff_partials

            # ==== Create the full reconcile ====
            results['full_reconcile'] = self.env['account.full.reconcile'] \
                .with_context(
                    skip_invoice_sync=True,
                    skip_invoice_line_sync=True,
                    skip_account_move_synchronization=True,
                    check_move_validity=False,
                ) \
                .create({
                    'exchange_move_id': exchange_move and exchange_move.id,
                    'partial_reconcile_ids': [Command.set(involved_partials.ids)],
                    'reconciled_line_ids': [Command.set(involved_lines.ids)],
                })

            # === Cash basis rounding autoreconciliation ===
            # In case a cash basis rounding difference line got created for the transition account, we reconcile it with the corresponding lines
            # on the cash basis moves (so that it reaches full reconciliation and creates an exchange difference entry for this account as well)

            if caba_lines_to_reconcile:
                for (dummy, account, repartition_line), amls_to_reconcile in caba_lines_to_reconcile.items():
                    if not account.reconcile:
                        continue

                    exchange_line = exchange_move.line_ids.filtered(
                        lambda l: l.account_id == account and l.tax_repartition_line_id == repartition_line
                    )

                    (exchange_line + amls_to_reconcile).filtered(lambda l: not l.reconciled).reconcile()

        not_paid_invoices.filtered(lambda move:
            move.payment_state in ('paid', 'in_payment')
        )._invoice_paid_hook()

        return results
    
    analytic_distribution = fields.Json(
        inverse="_inverse_analytic_distribution", copy=True
    ) # add the inverse function used to trigger the creation/update of the analytic lines accordingly (field originally defined in the analytic mixin)
    def action_automatic_entry_mw(self):
        action = self.env['ir.actions.act_window']._for_xml_id('mw_account.account_automatic_entry_mw_action')
        # Force the values of the move line in the context to avoid issues
        ctx = dict(self.env.context)
        ctx.pop('active_id', None)
        ctx.pop('default_journal_id', None)
        ctx['active_ids'] = self.ids
        ctx['active_model'] = 'account.move.line'
        action['context'] = ctx
        return action
    def action_automatic_entry_mw_curr(self):
        action = self.env['ir.actions.act_window']._for_xml_id('mw_account.account_automatic_entry_mw_curr_action')
        # Force the values of the move line in the context to avoid issues
        ctx = dict(self.env.context)
        ctx.pop('active_id', None)
        ctx.pop('default_journal_id', None)
        ctx['active_ids'] = self.ids
        ctx['active_model'] = 'account.move.line'
        action['context'] = ctx
        return action
    # @api.constrains('account_id','partner_id','analytic_distribution')
    # def _check_partner_paid_is(self):
    #     for item in self:
    #         if item.account_id.account_type == 'asset_receivable' and not item.partner_id :
    #             raise ValidationError(_('Авлага төрөлтэй дансны мөр дээр харилцагч сонгоогүй байна!'))
    #         if item.account_id.account_type == 'liability_payable' and not item.partner_id :
    #             raise ValidationError(_('Өглөг төрөлтэй дансны мөр дээр харилцагч сонгоогүй байна!'))
            # if item.account_id.account_type == 'income'and not item.analytic_distribution :
            #     raise ValidationError(_('Орлого төрөлтэй дансны мөр дээр Шинжилгээний данс сонгоогүй байна!'))
            # if item.account_id.account_type == 'income_other'and not item.analytic_distribution :
            #     raise ValidationError(_('Орлого төрөлтэй дансны мөр дээр Шинжилгээний данс сонгоогүй байна!'))
            # if item.account_id.account_type == 'expense' and not item.analytic_distribution :
            #     raise ValidationError(_('Зарлага төрөлтэй дансны мөр дээр Шинжилгээний данс сонгоогүй байна!'))
class AccountUnreconcile(models.TransientModel):
    _inherit = "account.unreconcile"

    def trans_unrec(self):
        context = dict(self._context or {})
        if context.get('active_ids', False):
            self.env['account.move.line'].browse(context.get('active_ids')).with_context(force_delete=True).remove_move_reconcile()
        return {'type': 'ir.actions.act_window_close'}
    
    
class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def unlink(self):
        # Зөвхөн тулгалт салгахаар салгах
        context = dict(self._context or {})
        if not self:
            return True
        # if not context.get('force_delete', False):
        #     raise UserError(('Тулгалт хийсэн бичилт ноороглохгүй .'))

        for part in self:
            # if not self.env.user.has_group('mw_account.group_remove_reconcile'):
            #     raise UserError(('Тулгалт салгах эрхгүй байна!!! .'))
            part.debit_move_id.move_id.message_post(body="Tulgalt salgsan: {}".format(self.env.user.login))
            part.credit_move_id.move_id.message_post(body="Tulgalt salgsan: {}".format(self.env.user.login))
        res = super().unlink()

        return res
