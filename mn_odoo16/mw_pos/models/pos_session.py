# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        """ Create account.move and account.move.line records for this session.
        """
        res=  super(PosSession, self)._create_account_move(balancing_account,amount_to_balance,bank_payment_method_diffs)
        
        journal = self.config_id.journal_id
#         account_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
#             'journal_id': journal.id,
#             'date': fields.Date.context_today(self),
#             'ref': self.name+u' хөнгөлөлт',
#         })
        self._create_discount_lines()
#         self._create_discount_lines(account_move.id)

        return res

    def _create_discount_lines(self):
        def get_income_disc_account(order_line):
            product = order_line.product_id
            income_account = product.with_company(order_line.company_id)._get_product_accounts()['income_discount']
            if not income_account:
                raise UserError(_('Please define income discount account for this product: "%s" (id:%d).')
                                % (product.name, product.id))
            return order_line.order_id.fiscal_position_id.map_account(income_account)
        def get_income_account(order_line):
            product = order_line.product_id
            income_account = product.with_company(order_line.company_id)._get_product_accounts()['income']
            print ('income_account ',income_account)
            if not income_account:
                raise UserError(_('Please define income discount account for this product: "%s" (id:%d).')
                                % (product.name, product.id))
            return order_line.order_id.fiscal_position_id.map_account(income_account)
                                
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

        orders_data = self.env['pos.order'].search([('session_id', 'in', self.ids)])

        total_disc={}
        for line in orders_data.lines:
            if line.discount:
                discount_account=get_income_disc_account(line).id,
                income_account=get_income_account(line).id,
                if discount_account and total_disc.get(discount_account,False):
                    total_disc[discount_account]['amount']+=line.qty*line.price_unit-line.price_subtotal_incl
                else:
                    total_disc[discount_account]={'name':'Хөнгөлөлт',
                                                    'amount':line.qty*line.price_unit-line.price_subtotal_incl,
                                                  'income_account':income_account,
                                                'product_id':line.product_id
                                                    }
            elif  line.discount_info:
                discount_account=get_income_disc_account(line).id,
                income_account=get_income_account(line).id,
                if discount_account and total_disc.get(discount_account,False):
                    total_disc[discount_account]['amount']+=line.qty*line.discount_info
                else:
                    total_disc[discount_account]={'name':'Хөнгөлөлт',
                                                    'amount':line.qty*line.discount_info,
                                                  'income_account':income_account,
                                                  'product_id':line.product_id
                                                  }
#         print ('total_disc ',total_disc)

        aml_vals=[]
        for d in total_disc:
            if total_disc[d]['product_id']:
                analytic_account_id = total_disc[d]['product_id'].product_brand_id.analytic_account_id.id
            else:
                analytic_account_id = False
            source_vals = self._debit_amounts({'account_id': d,
                                                'analytic_account_id':analytic_account_id,
                                               'name':total_disc[d]['name'],
                                               'move_id':self.move_id.id}, 0, total_disc[d]['amount']/1.1)
            dest_vals = self._credit_amounts({'account_id': total_disc[d]['income_account'],
                                                'analytic_account_id':analytic_account_id,
                                              'name':total_disc[d]['name'],
                                              'move_id':self.move_id.id}, 0, total_disc[d]['amount']/1.1)
            aml_vals.append(source_vals)
            aml_vals.append(dest_vals)
#         source_vals = self._debit_amounts({'account_id': 2908,'move_id':self.move_id.id}, 0, total_disc)
#         dest_vals = self._credit_amounts({'account_id': 2813,'move_id':self.move_id.id}, 0, total_disc)
        MoveLine.create(
            aml_vals
#             [source_vals,dest_vals]
        )
        return True



    def _get_combine_statement_line_vals(self, statement, amount, payment_method):
        return {
            'date': fields.Date.context_today(self),
            'amount': amount,
            'cash_type_id': statement.journal_id.cash_type_id.id or False,
            'payment_ref': self.name,
            'statement_id': statement.id,
            'journal_id': statement.journal_id.id,
            'counterpart_account_id': self._get_receivable_account(payment_method).id,
        }
#     def _create_refund_vals(self):
#         def get_income_refund_account(order_line):
#             product = order_line.product_id
#             income_account = product.with_company(order_line.company_id)._get_product_accounts()['income_refund']
#             if not income_account:
#                 raise UserError(_('Please define income discount account for this product: "%s" (id:%d).')
#                                 % (product.name, product.id))
#             return order_line.order_id.fiscal_position_id.map_account(income_account)
#         def get_re_refund_account(order_line):
#             product = order_line.product_id
#             income_account = product.with_company(order_line.company_id)._get_product_accounts()['income_refund']
#             print ('income_account ',income_account)
#             if not income_account:
#                 raise UserError(_('Please define income discount account for this product: "%s" (id:%d).')
#                                 % (product.name, product.id))
#             return order_line.order_id.fiscal_position_id.map_account(income_account)
        
#         MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

#         orders_data = self.env['pos.order'].search([('session_id', 'in', self.ids)])

#         total_disc={} 
#         for line in orders_data.lines:
#             if line.order_id.is_refunded== True:
#                 refund_account=get_income_refund_account(line).id,
#                 re_income_account=get_re_refund_account(line).id,
#                 if refund_account and total_disc.get(refund_account,False):
#                     total_disc[refund_account]['amount']+=line.qty*line.price_unit-line.price_subtotal_incl
#                 else:
#                     total_disc[refund_account]={'name':'Refund',
#                                                     'amount':line.qty*line.price_unit-line.price_subtotal_incl,
#                                                     'income_account':re_income_account,
#                                                     'product_id':line.product_id
#                                                     }
#             elif  line.discount_info:
#                 refund_account=get_income_refund_account(line).id,
#                 re_income_account=get_re_refund_account(line).id,
#                 if refund_account and total_disc.get(refund_account,False):
#                     total_disc[refund_account]['amount']+=line.qty*line.discount_info
#                 else:
#                     total_disc[refund_account]={'name':'Refund',
#                                                   'amount':line.qty*line.discount_info,
#                                                   'income_account':re_income_account,
#                                                   'product_id':line.product_id
#                                                   }
# #         print ('total_disc ',total_disc)

#         aml_vals=[]
#         for d in total_disc:
#             if total_disc[d]['product_id']:
#                 analytic_account_id = total_disc[d]['product_id'].product_brand_id.analytic_account_id.id
#             else:
#                 analytic_account_id = False
#             source_vals = self._debit_amounts({'account_id': d,
#                                                 'analytic_account_id':analytic_account_id,
#                                                'name':total_disc[d]['name'],
#                                                'move_id':self.move_id.id}, 0, total_disc[d]['amount']/1.1)
#             dest_vals = self._credit_amounts({'account_id': total_disc[d]['re_income_account'],
#                                                 'analytic_account_id':analytic_account_id,
#                                               'name':total_disc[d]['name'],
#                                               'move_id':self.move_id.id}, 0, total_disc[d]['amount']/1.1)
#             aml_vals.append(source_vals)
#             aml_vals.append(dest_vals)
# #         source_vals = self._debit_amounts({'account_id': 2908,'move_id':self.move_id.id}, 0, total_disc)
# #         dest_vals = self._credit_amounts({'account_id': 2813,'move_id':self.move_id.id}, 0, total_disc)
#         MoveLine.create(
#             aml_vals
# #             [source_vals,dest_vals]
#         )
#         return True

    def _create_bank_payment_moves(self, data):
        '''combine бичилт бичихгүй
        '''
        combine_receivables_bank = data.get('combine_receivables_bank')
        split_receivables_bank = data.get('split_receivables_bank')
        bank_payment_method_diffs = data.get('bank_payment_method_diffs')
        MoveLine = data.get('MoveLine')
        payment_method_to_receivable_lines = {}
        payment_to_receivable_lines = {}
        for payment_method, amounts in combine_receivables_bank.items():
            combine_receivable_line = MoveLine.create(self._get_combine_receivable_vals(payment_method, amounts['amount'], amounts['amount_converted']))
#             payment_receivable_line = self._create_combine_account_payment(payment_method, amounts, diff_amount=bank_payment_method_diffs.get(payment_method.id) or 0)
            payment_method_to_receivable_lines[payment_method] = combine_receivable_line #| payment_receivable_line

        for payment, amounts in split_receivables_bank.items():
            split_receivable_line = MoveLine.create(self._get_split_receivable_vals(payment, amounts['amount'], amounts['amount_converted']))
#             payment_receivable_line = self._create_split_account_payment(payment, amounts)
            payment_to_receivable_lines[payment] = split_receivable_line #| payment_receivable_line

        for bank_payment_method in self.payment_method_ids.filtered(lambda pm: pm.type == 'bank' and pm.split_transactions):
            self._create_diff_account_move_for_split_payment_method(bank_payment_method, bank_payment_method_diffs.get(bank_payment_method.id) or 0)

        data['payment_method_to_receivable_lines'] = payment_method_to_receivable_lines
        data['payment_to_receivable_lines'] = payment_to_receivable_lines
        return data