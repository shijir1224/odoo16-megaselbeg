# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.models import check_method_name
from odoo.addons.web.controllers.utils import clean_action
from odoo.tools import html2plaintext
from odoo.tools.misc import formatLang
from odoo.addons.mw_base.verbose_format import verbose_format
from odoo.addons.mw_base.verbose_format import verbose_format_china
from odoo.addons.mw_base.verbose_format import num2cn2
import logging
from odoo.addons.mw_base.verbose_format import verbose_format




class AccountBankStatementLine(models.Model):
    # _inherit = "account.bank.statement.line"

    _name = 'account.bank.statement.line'
    _inherit = ["account.bank.statement.line", "analytic.mixin"]

    account_id = fields.Many2one('account.account', 'Данс')
    import_aml_ids = fields.One2many('account.aml.bank.statement','bsl_id', string='Lines reconcile')
    bank_ref = fields.Char(string='Банк утга')
    
    tmp_ids = fields.One2many('account.bank.statement.tmp.line','statement_line_id', string='Lines tmp')
    amount_str_mw = fields.Char(string="Amount str", compute="get_amount_str", store=True)
    amount_abs = fields.Float(string='ABS amount', compute="compute_amount_mnt_mw", store=True)
    res_bank = fields.Many2one('res.bank', string='Банк')
    @api.depends('amount')
    def get_amount_str(self):
        for report_id in self:
            if report_id.amount:
                currency_name = 'MNT'
                if self.journal_id.currency_id:
                    currency_name =self.journal_id.currency_id
                    report_id.amount_str_mw = verbose_format(abs(report_id.amount),currency_name)
                else:
                    report_id.amount_str_mw = verbose_format(abs(report_id.amount))
            else:
                report_id.amount_str_mw = False
    amount_mnt = fields.Float(string='Дүн /Төг/', compute="compute_amount_mnt_mw", store=True)
    @api.depends('amount')
    def compute_amount_mnt_mw(self):
        for item in self:
            if item.currency_id == 108:
                item.amount_mnt = self.amount
                item.amount_abs= abs(item.amount)
            else:
                # if item.move_id:
                    # move = self.env['account.move'].search([('id','=',item.move_id.id)], limit=1)
                ratio = self.env['res.currency']._get_conversion_rate(item.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, item.date)
                item.amount_mnt = item.amount * ratio
                item.amount_abs= abs(item.amount)
                # else:
                #     item.amount_mnt = item.amount
            
    def button_validate_line(self):
        moves = self.env['account.move']
        context = dict(self.env.context or {})
        ctx = dict(self._context, force_price_include=False)
        for st_line in self:
        #тулгах
            new_aml_id=False
            if self.analytic_distribution:
                st_line.move_id.line_ids.write({'analytic_distribution': st_line.analytic_distribution})
            if self.branch_id:
                st_line.move_id.line_ids.write({'branch_id': st_line.branch_id.id})
                st_line.move_id.write({'branch_id': st_line.branch_id.id})
            if self.payment_ref:
                st_line.move_id.write({'ref': st_line.payment_ref})
            if st_line.import_aml_ids:
                    if st_line.move_id.line_ids.filtered(lambda l: l.account_id.reconcile):
                        new_aml_id=st_line.move_id.line_ids.filtered(lambda l: l.account_id.reconcile)
                    rac_banch=False
                    for imp in st_line.import_aml_ids:
                        imort_lines=False
                        if imp.import_aml_id:
                            aml=imp.import_aml_id
                            if imp.import_aml_id.branch_id:
                                rac_banch=imp.import_aml_id.branch_id.id
                            if not imort_lines:
                                imort_lines=aml
                            else:
                                imort_lines+=aml
                    if new_aml_id and len(new_aml_id)>1:
                        if len(new_aml_id)>1:
                            new_aml_id=new_aml_id.filtered(lambda m: m.account_id.internal_type in ('receivable','payable'))
                            if new_aml_id and len(new_aml_id)>1:
                                new_aml_id=new_aml_id[0]
#                             raise UserError((u'Нэг гүйлгээнд олон авлага өглөгийн тулгалтыг импортлосон байна!!! {}'.format(st_line.payment_ref)))                        
                    if imort_lines and new_aml_id and not new_aml_id.reconciled and not imort_lines.filtered(lambda m: m.reconciled):
                        if rac_banch:
                            new_aml_id.move_id.line_ids.write({'branch_id':rac_banch})
                        imort_lines.filtered(lambda r:r.move_id.state!='posted').move_id._post()
                        
                        if new_aml_id.move_id.state!='posted':
                            new_aml_id.move_id._post()
                        (new_aml_id | imort_lines).reconcile()
            else:
                if st_line.tax_id and st_line.amount<0 and st_line.move_id.state=='draft':
                    zardal_line=st_line.move_id.line_ids.filtered(lambda l: l.debit>0
                                                                             )
                    zardal_line.with_context(check_move_validity=False).write({'tax_ids':[(6,0,[st_line.tax_id.id])],
                                       'debit':round(zardal_line.debit/1.1,2)})
                    st_line.move_id.with_context(tax_incl_check=True,check_move_validity=False)._onchange_recompute_dynamic_lines()
                m = st_line._prepare_move_line_default_vals()
                wizard = self.env['bank.rec.widget'].with_context(default_st_line_id=st_line.id,name=st_line.name).new({})
                for line in wizard.line_ids:
                    if line.flag in ('aml', 'new_aml', 'liquidity', 'exchange_diff'):
                        line.account_id = line.source_aml_id.account_id
                    else:
                        line.account_id = st_line.account_id.id
                wizard.button_validate()            
                st_line.write({'state': 'posted'})
                if st_line.account_id and st_line.move_id:
                    bsline=st_line.move_id.line_ids.filtered(lambda l: l.account_id != st_line.account_id and \
                                                                l.account_id != st_line.move_id.journal_id.default_account_id \
                                                                and not l.matched_debit_ids \
                                                                and not l.matched_credit_ids)
                    
                    if self.statement_id.journal_id.suspense_account_id \
                        and self.statement_id.journal_id.suspense_account_id ==bsline.account_id:
                        bsline.write({'account_id':st_line.account_id.id})
                    if st_line.move_id.state!='posted':
                        st_line.move_id._post(soft=False)
                    if st_line.move_id.state!='posted':
                        st_line.move_id._post(soft=False)
                    
        named_line = self.move_id.invoice_line_ids.filtered(lambda r: r.name).mapped('name')
        self.move_id.invoice_line_ids.filtered(lambda r: not r.name).write({'name': named_line})
        return True


    def button_draft_line(self):
        moves = self.env['account.move']
        for st_line in self:
            st_line.move_id.button_draft()
            wizard = self.env['bank.rec.widget'].with_context(default_st_line_id=self.id).new({})
            wizard.button_reset()                   
        return True

    move_state = fields.Selection(string="Move state", related= "move_id.state")

    @api.model
    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        res = super(AccountBankStatementLine, self)._prepare_move_line_default_vals(counterpart_account_id)
        if self.env.context.get('no_create_aml', False):
            return []
        if not self._context.get('from_reset',False):
            if self.account_id and res[1]['account_id'] != self.account_id.id:
                res[1]['account_id'] = self.account_id.id
        if self.analytic_distribution:# and res[1]['account_id'] != self.account_id.id:
            res[1]['analytic_distribution'] = self.analytic_distribution
            res[0]['analytic_distribution'] = self.analytic_distribution
            
            
        return res
    
    @api.model
    def _prepare_liquidity_move_line_vals(self):
        res = super(AccountBankStatementLine, self)._prepare_liquidity_move_line_vals()
        if self.account_id and res[1]['account_id'] != self.account_id.id:
            res[1]['account_id'] = self.account_id.id
        return res

    def print_bank_order(self):
#     def print_bank_order(self, cr, uid, ids, context=None):
        ''' Төлбөрийн даалгаврын баримт хэвлэх, Касс зарлагын баримт хэвлэх
        '''
        model_id = self.env['ir.model'].sudo().search([('model','=','account.bank.statement.line')], limit=1)
        if self.journal_id.type=='bank':
            template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','tulburiin_daalgavar')], limit=1)
        else:
#             return self.env['report'].get_action(self, 'mn_account.report_cash_income_receipt')
            if self.amount<0:
                template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_expense')], limit=1)
            else:
                template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_income')], limit=1)

        if template:
            res = template.sudo().print_template(self.id)
            return res
        else:
            raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))



class AccountAMLBankStatement(models.Model):
    _name = 'account.aml.bank.statement'
    _description = "account aml bank statement"

    import_aml_id = fields.Many2one('account.move.line', string='Account aml', ondelete='cascade')
    bsl_id = fields.Many2one('account.bank.statement.line', 'Bank statement line', ondelete='cascade')
    date = fields.Date(string='Date')
    aml_amount = fields.Float(string='Amount', digits=(16, 2),)
    currency_amount = fields.Float(string='Currency Amount', digits=(16, 2),)
    is_mnt = fields.Boolean(string='MNT',default=False)
    currency_id = fields.Many2one('res.currency', string='currency aml')

class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    def _get_line_create_command_dict(
        self, line, i, amount_currency, balance, partner_id_to_set=None
    ):
        res = super(BankRecWidget, self)._get_line_create_command_dict(line, i, amount_currency, balance, partner_id_to_set=partner_id_to_set)
        if not res.get('name',False):
            res['name'] = line.wizard_id.st_line_id.payment_ref
        return res
        
    # @api.depends('st_line_id')
    # def _compute_line_ids(self):
    #     """ Convert the python dictionaries in 'lines_widget' to a bank.rec.edit.line recordset to ease the business
    #     computations.
    #     In case 'lines_widget' is empty, the default initial lines are generated.
    #     """
    #     for wizard in self:
    #
    #         # The wizard already has lines.
    #         if wizard.line_ids:
    #             return
    #
    #         # Protected fields by the orm like create_date should be excluded.
    #         protected_fields = set(models.MAGIC_COLUMNS + [self.CONCURRENCY_CHECK_FIELD])
    #         if wizard.lines_widget and wizard.lines_widget['lines']:
    #             # Create the `bank.rec.widget.line` from existing data in `lines_widget`.
    #             line_ids_commands = []
    #             for line_vals in wizard.lines_widget['lines']:
    #                 create_vals = {}
    #
    #                 for field_name, field in wizard.line_ids._fields.items():
    #                     if field_name in protected_fields:
    #                         continue
    #
    #                     value = line_vals[field_name]
    #                     if field.type == 'many2one':
    #                         create_vals[field_name] = value['id']
    #                     elif field.type == 'many2many':
    #                         create_vals[field_name] = value['ids']
    #                     elif field.type == 'char':
    #                         create_vals[field_name] = value['value'] or ''
    #                     else:
    #                         create_vals[field_name] = value['value']
    #                 line_ids_commands.append(Command.create(create_vals))
    #             wizard.line_ids = line_ids_commands
    #         elif wizard.st_line_id.tmp_ids:
    #             bb=wizard._lines_widget_prepare_liquidity_line()
    #             # The wizard is opened for the first time. Create the default lines.
    #             line_ids_commands = [Command.clear(), Command.create(bb)]
    #             # line_ids_commands = []
    #             for tmp_line in wizard.st_line_id.tmp_ids:
    #                 create_vals={}
    #                 create_vals['debit']=tmp_line.debit
    #                 create_vals['credit']=tmp_line.credit
    #                 create_vals['date']=tmp_line.statement_line_id.date
    #                 create_vals['name']=tmp_line.name
    #                 create_vals['amount_currency']=tmp_line.amount_currency
    #
    #                 create_vals['currency_id']=tmp_line.currency_id and tmp_line.currency_id.id or False
    #
    #                 create_vals['account_id']=tmp_line.account_id and tmp_line.account_id.id or False
    #                 create_vals['partner_id']=tmp_line.partner_id and tmp_line.partner_id.id or False
    #
    #                 line_ids_commands.append(Command.create(create_vals))
    #             wizard.line_ids = line_ids_commands
    #
    #         else:
    #             bb=wizard._lines_widget_prepare_liquidity_line()
    #             # The wizard is opened for the first time. Create the default lines.
    #             line_ids_commands = [Command.clear(), Command.create(bb)]
    #
    #             if wizard.st_line_id.is_reconciled:
    #                 # The statement line is already reconciled. We just need to preview the existing amls.
    #                 _liquidity_lines, _suspense_lines, other_lines = wizard.st_line_id._seek_for_lines()
    #                 for aml in other_lines:
    #                     aa=wizard._lines_widget_prepare_aml_line(aml)
    #                     line_ids_commands.append(Command.create(aa))
    #             wizard.line_ids = line_ids_commands
    #
    #             wizard._lines_widget_add_auto_balance_line()


    def button_reset(self):
        self.ensure_one()
        # tmp_line=self.env['account.bank.statement.tmp.line']
        # for st_line in self.st_line_id:
        #     if st_line.tmp_ids:
        #         st_line.tmp_ids.unlink()
        #     for line in st_line.move_id.line_ids:
        #         # if line.account_id.account_type == 'asset_cash':
        #         if line.account_id == st_line.journal_id.default_account_id:
        #             continue
        #         tmp_line.create({'statement_line_id':st_line.id,
        #                          'statement_id':st_line.statement_id and st_line.statement_id.id or False,
        #                         'partner_id':line.partner_id and line.partner_id.id or st_line.partner_id and st_line.partner_id.id or False,
        #                         'account_id':line.account_id and line.account_id.id or st_line.account_id and st_line.account_id.id or False,
        #                         'name':line.name,
        #                         'currency_id':st_line.foreign_currency_id and st_line.foreign_currency_id.id or line.currency_id.id, 
        #                         'payment_ref':st_line.payment_ref,
        #                         'debit':line.debit,
        #                         'credit':line.credit,
        #                         'amount_currency':line.amount_currency
        #                             })
    
        if self.state == 'reconciled':
            self.st_line_id.with_context(from_reset=True).action_undo_reconciliation()
    
            self._ensure_loaded_lines()
            self._action_trigger_matching_rules()
    
        self.next_action_todo = {'type': 'reset_form'}
        
    def _lines_widget_prepare_auto_balance_line(self):
        """ Create the auto_balance line if necessary in order to have fully balanced lines."""
        self.ensure_one()
        self._ensure_loaded_lines()
        st_line = self.st_line_id

        # Compute the current open balance.
        transaction_amount, transaction_currency, journal_amount, _journal_currency, company_amount, _company_currency \
            = self.st_line_id._get_accounting_amounts_and_currencies()
        open_amount_currency = -transaction_amount
        open_balance = -company_amount
        for line in self.line_ids:
            if line.flag in ('liquidity', 'auto_balance'):
                continue

            open_balance -= line.balance
            journal_transaction_rate = abs(transaction_amount / journal_amount) if journal_amount else 0.0
            company_transaction_rate = abs(transaction_amount / company_amount) if company_amount else 0.0
            if line.currency_id == self.transaction_currency_id:
                open_amount_currency -= line.amount_currency
            elif line.currency_id == self.journal_currency_id:
                open_amount_currency -= transaction_currency.round(line.amount_currency * journal_transaction_rate)
            else:
                open_amount_currency -= transaction_currency.round(line.balance * company_transaction_rate)

        # Create a new auto-balance line.
        account = None
        if self.partner_id:
            name = _("Open balance: %s", st_line.payment_ref)
            partner_is_customer = st_line.partner_id.customer_rank and not st_line.partner_id.supplier_rank
            partner_is_supplier = st_line.partner_id.supplier_rank and not st_line.partner_id.customer_rank
            if partner_is_customer:
                account = st_line.partner_id.with_company(st_line.company_id).property_account_receivable_id
            elif partner_is_supplier:
                account = st_line.partner_id.with_company(st_line.company_id).property_account_payable_id
            elif st_line.amount > 0:
                account = st_line.partner_id.with_company(st_line.company_id).property_account_receivable_id
            else:
                account = st_line.partner_id.with_company(st_line.company_id).property_account_payable_id

        if not account:
            name = st_line.payment_ref
            account = st_line.journal_id.suspense_account_id

        return {
            'flag': 'auto_balance',

            'account_id': account.id,
            # 'name': name,
            'amount_currency': open_amount_currency,
            'balance': open_balance,
        }
    # def _compute_lines_widget(self):
    #     """ Convert the bank.rec.widget.line recordset (line_ids fields) to a dictionary to fill the 'lines_widget'
    #     owl widget.
    #     """
    #     self._check_lines_widget_consistency()
    #
    #     # Protected fields by the orm like create_date should be excluded.
    #     protected_fields = set(models.MAGIC_COLUMNS + [self.CONCURRENCY_CHECK_FIELD])
    #
    #     for wizard in self:
    #         lines = wizard.line_ids
    #
    #         # Sort the lines.
    #         sorted_lines = []
    #         auto_balance_lines = []
    #         epd_lines = []
    #         exchange_diff_map = {x.source_aml_id: x for x in lines.filtered(lambda x: x.flag == 'exchange_diff')}
    #         for line in lines:
    #             if line.flag == 'auto_balance':
    #                 auto_balance_lines.append(line)
    #             elif line.flag == 'early_payment':
    #                 epd_lines.append(line)
    #             elif line.flag != 'exchange_diff':
    #                 sorted_lines.append(line)
    #                 if line.flag == 'new_aml' and exchange_diff_map.get(line.source_aml_id):
    #                     sorted_lines.append(exchange_diff_map[line.source_aml_id])
    #
    #         line_vals_list = []
    #         for line in sorted_lines + epd_lines + auto_balance_lines:
    #             js_vals = {}
    #
    #             for field_name, field in line._fields.items():
    #                 if field_name in protected_fields:
    #                     continue
    #
    #                 value = line[field_name]
    #                 if field.type == 'date':
    #                     js_vals[field_name] = {
    #                         'display': tools.format_date(self.env, value),
    #                         'value': fields.Date.to_string(value),
    #                     }
    #                 elif field.type == 'char':
    #                     js_vals[field_name] = {'value': value or ''}
    #                 elif field.type == 'monetary':
    #                     if line[field.currency_field]:
    #                         currency = line[field.currency_field]
    #                     else:
    #                         currency = self.env["res.currency"].search([("id", '=', 108)])
    #                     print ('==========',currency)
    #                     js_vals[field_name] = {
    #                         'display': formatLang(self.env, value, currency_obj=currency),
    #                         'value': value,
    #                         'is_zero': currency.is_zero(value),
    #                     }
    #                 elif field.type == 'many2one':
    #                     record = value._origin
    #                     js_vals[field_name] = {
    #                         'display': record.display_name or '',
    #                         'id': record.id,
    #                     }
    #                 elif field.type == 'many2many':
    #                     records = value._origin
    #                     js_vals[field_name] = {
    #                         'display': records.mapped('display_name'),
    #                         'ids': records.ids,
    #                     }
    #                 else:
    #                     js_vals[field_name] = {'value': value}
    #             line_vals_list.append(js_vals)
    #
    #         extra_notes = []
    #         bank_account = wizard.st_line_id.partner_bank_id.display_name or wizard.st_line_id.account_number
    #         if bank_account:
    #             extra_notes.append(bank_account)
    #         narration = wizard.st_line_id.narration and html2plaintext(wizard.st_line_id.narration)
    #         if narration:
    #             extra_notes.append(narration)
    #
    #         bool_analytic_distribution = False
    #         for line in wizard.line_ids:
    #             if line.analytic_distribution:
    #                 bool_analytic_distribution = True
    #                 break
    #
    #         wizard.lines_widget = {
    #             'lines': line_vals_list,
    #
    #             'display_multi_currency_column': wizard.line_ids.currency_id != wizard.company_currency_id,
    #             'display_taxes_column': bool(wizard.line_ids.tax_ids),
    #             'display_analytic_distribution_column': bool_analytic_distribution,
    #             'form_index': wizard.form_index,
    #             'state': wizard.state,
    #             'partner_name': wizard.st_line_id.partner_name,
    #             'extra_notes': ' '.join(extra_notes) if extra_notes else None,
    #         }


class AccountBankStatementTmpLine(models.Model):
    _name = "account.bank.statement.tmp.line"
    _description = "Bank Statement Tmp Line"

    statement_line_id = fields.Many2one(
        comodel_name='account.bank.statement.line',)
    statement_id = fields.Many2one(
        comodel_name='account.bank.statement',
        string='Statement',
    )

    # Payments generated during the reconciliation of this bank statement lines.
    payment_ids = fields.Many2many(
        comodel_name='account.payment',
        relation='account_payment_bank_statement_tmp_line_rel',
        string='Auto-generated Payments',
    )
    # This sequence is working reversed because the default order is reversed, more info in compute_internal_index
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')

    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account')

    payment_ref = fields.Char(string='Label')
    name = fields.Char(string='Name')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Journal Currency',
    )
    debit = fields.Monetary()
    credit = fields.Monetary()
    amount_currency = fields.Monetary(
        string="Amount in Currency",
        currency_field='currency_id',
    )
