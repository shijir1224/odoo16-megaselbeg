# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
import time
from odoo.addons.mw_base.verbose_format import verbose_format
from odoo.addons.mw_base.verbose_format import verbose_format_china
from odoo.addons.mw_base.verbose_format import num2cn2
import logging
from odoo.addons.mw_base.verbose_format import verbose_format
from datetime import timedelta, date

_logger = logging.getLogger(__name__)


class PaymentRequest(models.Model):

    _inherit = 'payment.request'
    
    def get_bank_statement_line(self, request, amount, form):
        mnt = self.env['res.currency'].search([('name','=','MNT')], limit=1)
        if self.currency_id==mnt:
            vals = {
                # 'payment_ref': ref,
				'date':  form.date and form.date or time.strftime('%Y-%m-%d'),
                # 'date': request.date_currency or request.date_currency.strftime('%Y-%m-%d'),
                'amount': amount ,
                'partner_id': request.partner_id.id,
                'account_id': form.account_id.id or request.ex_account_id and request.ex_account_id.id,
                'journal_id': form.journal_id.id,
                'bank_ref':form.bank_ref or '',
                'payment_ref': form.payment_ref or str(request.display_name)+ " / " + str(request.description),
                'foreign_currency_id': self.currency_id.id,
                # 'amount_currency': self.currency_id.id,
                # 'note': '%s :\n %s' % (request.narration_id.name, request.narration_id.description or ''),
                'analytic_distribution': request.analytic_distribution  or False,
                # 'bank_account_id': request.dans_id and request.dans_id.id or False,
                'cash_type_id': (request.cash_type_id and request.cash_type_id.id) or (form.cash_type_id and form.cash_type_id.id) or False
            }
        else:
            vals = {
                # 'payment_ref': ref,
				'date':  form.date and form.date or time.strftime('%Y-%m-%d'),
                # 'date': request.date_currency or request.date_currency.strftime('%Y-%m-%d'),
                'amount': -(amount),
                'partner_id': request.partner_id.id,
                'bank_ref':form.bank_ref or '',
                'account_id': form.account_id.id or request.ex_account_id and request.ex_account_id.id,
                'analytic_distribution': request.analytic_distribution  or False,
                'journal_id': form.journal_id.id,
                'payment_ref': form.payment_ref or str(request.display_name)+ " / " + str(request.description),
                'foreign_currency_id': self.currency_id.id,
                'cash_type_id': (request.cash_type_id and request.cash_type_id.id) or (form.cash_type_id and form.cash_type_id.id) or False
            }

        return vals
    
class AccountPaymentExpense(models.TransientModel):
    _inherit = "account.payment.expense"


    bank_ref = fields.Char (string='Банкны гүйлгээний утга')