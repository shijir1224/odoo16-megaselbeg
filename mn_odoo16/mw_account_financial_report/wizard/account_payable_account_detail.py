# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#    $Id:  $
#
#    Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#
#
############################################################################################

import base64
import time
import datetime
from datetime import datetime

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

from datetime import timedelta
from lxml import etree
from odoo.tools.translate import _

import xlwt
from xlwt import *
from operator import itemgetter
import collections
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.addons.mw_base.verbose_format import verbose_format
import logging
import base64

try:
    # Python 2 support
    from base64 import encodebytes
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodebytes
    
_logger = logging.getLogger(__name__)

class account_payable_account_detail(models.TransientModel):
    """
        Өглөгийн дансны дэлгэрэнгүй бүртгэл
    """
    
#     _inherit = "abstract.report.excel"
    # _inherit = "account.common.report"
    _name = "account.payable.account.detail"
    _description = "Payable Account Detail Report"
    
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    account_id = fields.Many2one('account.account', 'Account', 
                                 domain=['|', ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                                         ('is_recpay', '=', True)])
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))
    target_move = fields.Selection([('all', 'All Entries'),
                                    ('posted', 'All Posted Entries')], 'Target Moves', required=True,default='posted')
    partner_id = fields.Many2one('res.partner', 'Partner', help="If empty, display all partners")

#     type = fields.Selection([('all', 'All'),('payable', 'Payable'),
#                                     ('receivable', 'Receivable')], 'Type',default='all')
    is_currency = fields.Boolean('Is currency',default=False)
    is_date = fields.Boolean('Is Date',default=False)
    is_from_invoice = fields.Boolean('Is from invoice',default=False)
    state_invoice = fields.Selection([('open',u'Нээлттэй'),('paid',u'Төлөгдсөн'),('all',u'Бүгд')], 'Төлөв', required=True,default='all')    

    is_open = fields.Boolean('Only open?',default=False)
    is_invoice_open = fields.Boolean('Only open?',default=False)

    is_warehouse = fields.Boolean('Warehouse?',default=False)
    is_tag = fields.Boolean('Is tag')
    
    tag_id = fields.Many2one('res.partner.category', 'Category')

    is_tootsoo = fields.Boolean('Тооцоо нийлсэн аттай?',default=False)
    is_group = fields.Boolean('Гүйлгээгээр бүлэглэх?',default=False)
    is_group_account = fields.Boolean('Дансаар бүлэглэх?',default=False)
    
    def _build_contexts(self, data):
        result = {}
#         print "data ",data
        if not data['form']['date_from'] or not data['form']['date_to']:
            raise UserError((u'Эхлэх дуусах огноо сонгоно уу.'))
        elif data['form']['date_from'] > data['form']['date_to']:
            raise UserError((u'Эхлэх огноо дуусах огнооноос бага байх ёстой.'))
            
#         result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
 
        return result

    def prepare_data(self, context=None):
        
        data = {}
        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
#         data = self.pre_print_report(data)
        data['form']['company_id'] = form['company_id'][0]
        
        return data
    
    def print_report(self,context=None):
        if context is None:
            context = {}
        
        data = self.prepare_data(context=context)
        
        context.update({'report_type':'payable'})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.payable.account.detail',
            'datas': data,
            'context': context,
            'nodestroy': True,
        }
    
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to',  'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, )
        return self.with_context(discard_logo_check=True)._print_report(data)    

    def _print_report(self, data):
        form = self.read()[0]
        data['form'] = form
        data['form'].update(self._build_contexts(data))
#         data = self.pre_print_report(data)
        if self.is_invoice_open:
            return self._make_excel_open(data)
        return self._make_excel(data)
        

    def _amount_residual(self,lines):
        """ Computes the residual amount of a move line from a reconciliable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconciliable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
#         print 'lines ',lines
        for line in lines:
            if not line.account_id.reconcile:
                line.reconciled = False
                line.amount_residual = 0
                line.amount_residual_currency = 0
                continue
            #amounts in the partial reconcile table aren't signed, so we need to use abs()
            amount = abs(line.debit - line.credit)
            other_amount=0
#             print 'amount1 ',amount
            amount_residual_currency = abs(line.amount_currency) or 0.0
            sign = 1 if (line.debit - line.credit) > 0 else -1
            if not line.debit and not line.credit and line.amount_currency and line.currency_id:
                #residual for exchange rate entries
                sign = 1 if float_compare(line.amount_currency, 0, precision_rounding=line.currency_id.rounding) == 1 else -1
#             print 'line.matched_debit_ids ',line.matched_debit_ids
#             print 'line.matched_credit_ids ',line.matched_credit_ids
            for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
                # If line is a credit (sign = -1) we:
                #  - subtract matched_debit_ids (partial_line.credit_move_id == line)
                #  - add matched_credit_ids (partial_line.credit_move_id != line)
                # If line is a debit (sign = 1), do the opposite.
                sign_partial_line = sign if partial_line.credit_move_id == line else (-1 * sign)
#                 if line.id==84496:
#                     print 'partial_line.amount______________ ',partial_line.amount
#     #                 print 'partial_line ',partial_line
#                     print 'partial_line.max_date> ',partial_line.max_date
#                     print 'self.date_to ',self.date_to
                if partial_line.max_date<self.date_from or partial_line.max_date>self.date_to:
#                     if line.id==84496:
#                         print 'partial_line-------: ',partial_line
                    other_amount+=sign_partial_line * partial_line.amount
                amount += sign_partial_line * partial_line.amount
                #getting the date of the matched item to compute the amount_residual in currency
                if line.currency_id:
                    if partial_line.currency_id and partial_line.currency_id == line.currency_id:
                        amount_residual_currency += sign_partial_line * partial_line.amount_currency
                    else:
                        if line.balance and line.amount_currency:
                            rate = line.amount_currency / line.balance
                        else:
                            date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                            rate = line.currency_id.with_context(date=date).rate
                        amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)

            #computing the `reconciled` field.
            reconciled = False
            digits_rounding_precision = line.company_id.currency_id.rounding
            if float_is_zero(amount, precision_rounding=digits_rounding_precision):
#                 print 'amount ',amount
                if line.currency_id and line.amount_currency:
#                     print 'amount_residual_currency ',amount_residual_currency
                    if float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding):
                        reconciled = True
                else:
                    reconciled = True
            line.reconciled = reconciled
        return amount,other_amount
#             lineamount_residual = line.company_id.currency_id.round(amount * sign)
#             line.amount_residual_currency = line.currency_id and line.currency_id.round(amount_residual_currency * sign) or 0.0

        
    def get_report_data(self, data,partner):
        ''' Харилцагчийн өглөг авлагын гүйлгээг эхний үлдэгдэлийн хамтаар
            боловсруулж бэлтгэнэ.
        '''
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        check_bal=0
        partner_ids = []
#         if data['partner_id']:
#             partner_ids = [data['partner_id'][0]]
        partner_ids = [partner.id]
#             child_ids = partner_obj.search([('parent_id','=',data['partner_id'][0])])
#             if child_ids :
#                 partner_ids = partner_ids + child_ids
        account_ids = []
        if data['account_id']:
#             account_ids = [data['account_id'][0]]
            account_ids = account_obj.search([('id','=',data['account_id'][0])])
        else:
            account_ids = account_obj.search(
                                 domain=['|', ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                                         ('is_recpay', '=', True)])

        if not data['account_id']:
            add_account_ids = account_obj.search([('is_recpay','=',True)])
            account_ids+=add_account_ids
        date_where = ""
        date_where = " m.date < '%s' " % data['date_from']
        open_where=""
        if self.is_open:
            open_where =" AND l.amount_residual<>0 " #and amount_residual_currency<>0 
        state_where = ""
        if data['target_move'] != 'all':
            state_where = " AND m.state = '%s' " % data['target_move']
        partner_where = " AND l.partner_id is not null "
        if partner_ids :
            partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        if self.company_id:
            partner_where += " AND l.company_id = {0}".format(self.company_id.id)        
        
        a = []
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                        state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        init_wheres = [""]
        
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        filters = filters.replace('l__account_id', 'a')
        for account in account_ids.ids:
#Эхний үлдэгдэл
    #         move_lines = dict(map(lambda x: (x, []), accounts.ids))
    #         print "data context ",data
            if self.is_open:
                cr.execute("SELECT coalesce(sum(l.amount_residual),0.0), coalesce(sum(l.amount_residual_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "left join account_account a on a.id=l.account_id "
                       "WHERE "
                       " state='posted' "+partner_where+" " 
                       " "+filters+" "
                       " AND l.account_id = " + str(account) + 
                       " GROUP BY l.account_id ",tuple(init_where_params))
                fetched = cr.fetchone()
#                 print "fetched::::::",fetched
                sresidual, samount_currency = fetched or (0,0)
                account_str = account_obj.browse(account)
                acc=account_str.code + ' ' + account_str.name
#                 if data['account_type'] == 'payable':
                if account_str.account_type== 'liability_payable':
                    initial_amount = -sresidual
                    initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
                else :
                    initial_amount = sresidual
                    initial_amount_currency = samount_currency
            
            else:
                cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "left join account_account a on a.id=l.account_id "
                       "WHERE "
                       " state='posted' "+partner_where+" " 
                       " "+filters+" "
                       " AND l.account_id = " + str(account) + 
                       " GROUP BY l.account_id ",tuple(init_where_params))
    #             AND l.state <> 'draft' 
                fetched = cr.fetchone()
    #             print "fetched::::::",fetched
    #             if fetched:
    #                 q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
    #                            FROM account_move_line l \
    #                            LEFT JOIN account_move m ON (m.id=l.move_id) \
    #                            LEFT JOIN account_period p ON (p.id=l.period_id) \
    #                            WHERE "+date_where+" "+state_where \
    #                            + partner_where+" AND l.account_id = " + str(account) + " \
    #                            GROUP BY l.account_id "
    #                 print 'Query;       ', q
    #                 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
                sdebit, scredit, samount_currency = fetched or (0,0,0)
                account_str = account_obj.browse(account)
                acc=account_str.code + ' ' + account_str.name
#                 if data['account_type'] == 'payable':
                if account_str.account_type== 'liability_payable':
                    initial_amount = scredit - sdebit
                    initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
                else :
                    initial_amount = sdebit - scredit
                    initial_amount_currency = samount_currency
            
            balance, balance_currency = initial_amount, initial_amount_currency
            #balance, balance_currency = 0, 0
            move_line_obj = self.env['account.move.line']
            date_where1 = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
            # if initial_bal_journal:
            #     date_where1 += "AND l.journal_id <> %s " % initial_bal_journal
#             and (j.special is null or j.special='f') 
            cr.execute("SELECT l.id  "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "LEFT JOIN res_partner r ON (l.partner_id=r.id) "
                       "LEFT JOIN account_journal j ON (j.id=l.journal_id) "
                       "WHERE "+date_where1+"  "
                       " "+state_where+partner_where+"  " #+open_where+" "
                       " AND l.account_id =  " + str(account)+" "
                       "ORDER BY l.date, r.name")
#             data['fiscalyear_id'], AND p.fiscalyear_id = %s
#                        "LEFT JOIN account_period p ON (p.id=l.period_id) "
            fetched = cr.fetchall()
            result = []
            number = 1
            if fetched or initial_amount!=0:
                q1 = "SELECT l.id  FROM account_move_line l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN res_partner r ON (l.partner_id=r.id) \
                           LEFT JOIN account_journal j ON (j.id=l.journal_id) \
                           WHERE "+date_where1+" \
                            "+state_where+partner_where+"  "+open_where+" AND l.account_id = " + str(account) + " and (j.special is null or j.special='f') \
                           ORDER BY l.date, r.name"
#                            LEFT JOIN account_period p ON (p.id=l.period_id) \
# AND p.fiscalyear_id = " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
#                 print 'Q1 :  ', q1
                line_ids = [x[0] for x in fetched]
#                 print 'line_idslen::::::::',len(line_ids)               
#                print ('line_ids::::::::',line_ids)
                if self.is_group: #2 давтана
                    group_row={}
                    for line in move_line_obj.browse(line_ids):
                        row = {}
                        row['number'] = str(number)
                        row['date'] = line.date
                        row['name'] = line.move_id.ref or line.move_id.name
                        row['account'] = account_str.code + ' ' + account_str.name
                        debit_lines = []
                        credit_lines = []
                        if self.is_open:
                            if line.debit>0:
    #                             debit = line.amount_residual
                                ch_debit,other_amount=self._amount_residual([line])
                                debit=abs(ch_debit)+abs(other_amount)
                                credit = 0
                            else:
    #                             credit = abs(line.amount_residual)
                                ch_credit,other_amount = self._amount_residual([line])
                                credit=abs(ch_credit)+abs(other_amount)
                                debit = 0
                        else:
                            debit = line.debit
                            credit = line.credit
                        sale_line_ids=False
                        for other_line in line.move_id.line_ids :
                            if other_line.id != line.id :
                                if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                    debit_lines.append(u'Дт:'+other_line.account_id.code)
                                elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                    credit_lines.append(u'Кт:'+other_line.account_id.code)
                                if other_line.sale_line_ids:
                                    sale_line_ids=other_line.sale_line_ids
                        row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                        row['partner'] = line.partner_id.name
                        
    
                        sale_child_partner=''
    #                     print ('line.sale_line_ids ',sale_line_ids)
                        so_id=False
                        if sale_line_ids:
                            so_id=sale_line_ids[0].order_id
                            if so_id.partner_id.id != so_id.partner_invoice_id.id:
                                sale_child_partner = ' - '+so_id.partner_id.name
                        if hasattr(line.move_id, 'sale_return_id') and line.move_id.sale_return_id:
                            sale_child_partner=line.move_id.sale_return_id.partner_id.name
                            if not line.name:
                                line.name=line.move_id.name
                        narration =(line.name or '') + (sale_child_partner or '') + (so_id and ' '+so_id.name or '')  
                        if not narration:
#                             if line.move_id.type in ('in_invoice','in_refund') and line.move_id.invoice_origin:
                                narration=line.move_id.name
                        row['narration'] = narration                 
                        row['currency'] = (line.currency_id and line.currency_id.name) or ''
                        if group_row.get(line.move_id,False):
                            group_row[line.move_id]['debit'] += debit
                            group_row[line.move_id]['debit_currency'] += (line.debit > 0 and line.amount_currency) or 0
                            group_row[line.move_id]['credit_currency'] += (line.credit > 0 and abs(line.amount_currency)) or 0
                            group_row[line.move_id]['credit'] += credit
                        else:
                            row['debit'] = debit
                            row['debit_currency'] = (line.debit > 0 and line.amount_currency) or 0
                            row['credit_currency'] = (line.credit > 0 and abs(line.amount_currency)) or 0
                            row['credit'] = credit
                            
                        
                        row['so_id']=so_id
                        row['branch']=line.branch_id and line.branch_id.name or ''
                        if account_str.account_type== 'liability_payable':
                            balance = balance + credit - debit
                            if line.amount_currency!=0:
                                if line.credit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
                        else :
                            balance = balance + debit - credit
                            if line.amount_currency!=0:
                                if line.debit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
    
                        if group_row.get(line.move_id,False):
#                             row['balance_currency'] += balance_currency
#                             row['balance'] += balance
#                             number += 1
                            group_row[line.move_id]['balance_currency']=balance_currency
                            group_row[line.move_id]['balance']=balance
                        else:
                            row['balance_currency'] = balance_currency
                            row['balance'] = balance
                            number += 1
                            group_row[line.move_id]=row
                    for gr in group_row:                       
                        if self.is_open:
                            if debit!=0 or credit!=0:
                                result.append(group_row[gr])
                        else:
                            result.append(group_row[gr])
                else:                    
                    for line in move_line_obj.browse(line_ids):
                        row = {}
                        row['number'] = str(number)
                        row['date'] = line.date
                        row['name'] = line.move_id.ref or line.move_id.name
                        row['account'] = account_str.code + ' ' + account_str.name
                        debit_lines = []
                        credit_lines = []
                        if self.is_open:
                            if line.debit>0:
    #                             debit = line.amount_residual
                                ch_debit,other_amount=self._amount_residual([line])
                                debit=abs(ch_debit)+abs(other_amount)
                                credit = 0
                            else:
    #                             credit = abs(line.amount_residual)
                                ch_credit,other_amount = self._amount_residual([line])
                                credit=abs(ch_credit)+abs(other_amount)
                                debit = 0
                        else:
                            debit = line.debit
                            credit = line.credit
                        sale_line_ids=False
                        for other_line in line.move_id.line_ids :
                            if other_line.id != line.id :
                                if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                    debit_lines.append(u'Дт:'+other_line.account_id.code)
                                elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                    credit_lines.append(u'Кт:'+other_line.account_id.code)
                                if other_line.sale_line_ids:
                                    sale_line_ids=other_line.sale_line_ids
                        row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                        row['partner'] = line.partner_id.name
                        
    
                        sale_child_partner=''
    #                     print ('line.sale_line_ids ',sale_line_ids)
                        so_id=False
                        if sale_line_ids:
                            so_id=sale_line_ids[0].order_id
                            if so_id.partner_id.id != so_id.partner_invoice_id.id:
                                sale_child_partner = ' - '+so_id.partner_id.name
                        if hasattr(line.move_id, 'sale_return_id') and line.move_id.sale_return_id:
                            sale_child_partner=line.move_id.sale_return_id.partner_id.name
                            if not line.name:
                                line.name=line.move_id.name
                        narration =(line.name or '') + (sale_child_partner or '') + (so_id and ' '+so_id.name or '')  
                        if not narration:
#                             if line.move_id.type in ('in_invoice','in_refund') and line.move_id.invoice_origin:
                                narration=line.move_id.name
                        row['narration'] = narration                 
    #                     row['narration'] = line.name 
                        row['currency'] = (line.currency_id and line.currency_id.name) or ''
                        row['debit_currency'] = (line.debit > 0 and line.amount_currency) or 0
                        row['debit'] = debit
                        row['credit_currency'] = (line.credit > 0 and abs(line.amount_currency)) or 0
                        row['credit'] = credit
                        
                        row['so_id']=so_id
                        row['branch']=line.branch_id and line.branch_id.name or ''
    #                     if data['account_type'] == 'payable':
                        # if account_str.user_type_id.type== 'payable':
                        if account_str.account_type== 'liability_payable':

                            balance = balance + credit - debit
    #                         balance_currency += line.amount_currency if line.credit == 0 else line.amount_currency
                            if line.amount_currency!=0:
                                if line.credit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
                        else :
                            balance = balance + debit - credit
    #                         balance_currency += line.amount_currency if line.debit == 0 else line.amount_currency
                            if line.amount_currency!=0:
                                if line.debit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
    
                        row['balance_currency'] = balance_currency
                        row['balance'] = balance
                        row['create_uid'] = line.move_id.create_uid.name
                        row['create_date'] = line.move_id.create_date
                        number += 1
                        if self.is_open:
                            if debit!=0 or credit!=0:
                                result.append(row)
                        else:
                            result.append(row)
                        
                a.append([initial_amount, initial_amount_currency, result,acc])
                check_bal=1
        #return initial_amount, initial_amount_currency, result
        return a,check_bal
    
    def get_report_data_account(self, data,account,partners):
        ''' Харилцагчийн өглөг авлагын гүйлгээг эхний үлдэгдэлийн хамтаар
            боловсруулж бэлтгэнэ.
        '''
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        check_bal=0
        partner_ids = []
#         if data['partner_id']:
#             partner_ids = [data['partner_id'][0]]
        partner_ids = partners
#             child_ids = partner_obj.search([('parent_id','=',data['partner_id'][0])])
#             if child_ids :
#                 partner_ids = partner_ids + child_ids
        account_ids = [account.id]

        date_where = ""
        date_where = " m.date < '%s' " % data['date_from']
        open_where=""
        if self.is_open:
            open_where =" AND l.amount_residual<>0 " #and amount_residual_currency<>0 
        state_where = ""
        if data['target_move'] != 'all':
            state_where = " AND m.state = '%s' " % data['target_move']
        partner_where = " "
        # if partner_ids :
        #     partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        # if self.company_id:
        #     partner_where += " AND l.company_id = {0}".format(self.company_id.id)        
        
        a = []
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                        state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        init_wheres = [""]
        
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        filters = filters.replace('l__account_id', 'a')
        for partner in partner_ids:
#Эхний үлдэгдэл
    #         move_lines = dict(map(lambda x: (x, []), accounts.ids))
    #         print "data context ",data
            partner_where = " AND l.company_id = {0} and l.partner_id={1} ".format(self.company_id.id,partner.id)
            if self.is_open:
                cr.execute("SELECT coalesce(sum(l.amount_residual),0.0), coalesce(sum(l.amount_residual_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "left join account_account a on a.id=l.account_id "
                       "WHERE "
                       " state='posted' "+partner_where+" " 
                       " "+filters+" "
                       " AND l.account_id = " + str(account.id) + 
                       " GROUP BY l.account_id ",tuple(init_where_params))
                fetched = cr.fetchone()
#                 print "fetched::::::",fetched
                sresidual, samount_currency = fetched or (0,0)
                account_str = partner
                acc=account_str.ref + ' ' + account_str.name
#                 if data['account_type'] == 'payable':
                if account.account_type== 'liability_payable':
                    initial_amount = -sresidual
                    initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
                else :
                    initial_amount = sresidual
                    initial_amount_currency = samount_currency
            
            else:
                cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "left join account_account a on a.id=l.account_id "
                       "WHERE "
                       " state='posted' "+partner_where+" " 
                       " "+filters+" "
                       " AND l.account_id = " + str(account.id) + 
                       " GROUP BY l.account_id ",tuple(init_where_params))
    #             AND l.state <> 'draft' 
                fetched = cr.fetchone()
    #             print "fetched::::::",fetched
    #             if fetched:
    #                 q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
    #                            FROM account_move_line l \
    #                            LEFT JOIN account_move m ON (m.id=l.move_id) \
    #                            LEFT JOIN account_period p ON (p.id=l.period_id) \
    #                            WHERE "+date_where+" "+state_where \
    #                            + partner_where+" AND l.account_id = " + str(account) + " \
    #                            GROUP BY l.account_id "
    #                 print 'Query;       ', q
    #                 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
                sdebit, scredit, samount_currency = fetched or (0,0,0)
                account_str = partner
                acc=account_str.ref + ' ' + account_str.name
#                 if data['account_type'] == 'payable':
                if account.account_type== 'liability_payable':
                    initial_amount = scredit - sdebit
                    initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
                else :
                    initial_amount = sdebit - scredit
                    initial_amount_currency = samount_currency
            
            balance, balance_currency = initial_amount, initial_amount_currency
            #balance, balance_currency = 0, 0
            move_line_obj = self.env['account.move.line']
            date_where1 = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
            # if initial_bal_journal:
            #     date_where1 += "AND l.journal_id <> %s " % initial_bal_journal
#             and (j.special is null or j.special='f') 
            cr.execute("SELECT l.id  "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "LEFT JOIN res_partner r ON (l.partner_id=r.id) "
                       "LEFT JOIN account_journal j ON (j.id=l.journal_id) "
                       "WHERE "+date_where1+"  "
                       " "+state_where+partner_where+"  " #+open_where+" "
                       " AND l.account_id =  " + str(account.id)+" "
                       "ORDER BY l.date, r.name")
#             data['fiscalyear_id'], AND p.fiscalyear_id = %s
#                        "LEFT JOIN account_period p ON (p.id=l.period_id) "
            fetched = cr.fetchall()
            result = []
            number = 1
            if fetched or initial_amount!=0:
                q1 = "SELECT l.id  FROM account_move_line l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN res_partner r ON (l.partner_id=r.id) \
                           LEFT JOIN account_journal j ON (j.id=l.journal_id) \
                           WHERE "+date_where1+" \
                            "+state_where+partner_where+"  "+open_where+" AND l.account_id = " + str(account.id) + " and (j.special is null or j.special='f') \
                           ORDER BY l.date, r.name"
#                            LEFT JOIN account_period p ON (p.id=l.period_id) \
# AND p.fiscalyear_id = " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
#                 print 'Q1 :  ', q1
                line_ids = [x[0] for x in fetched]
#                 print 'line_idslen::::::::',len(line_ids)               
#                print ('line_ids::::::::',line_ids)
                if self.is_group: #2 давтана
                    group_row={}
                    for line in move_line_obj.browse(line_ids):
                        row = {}
                        row['number'] = str(number)
                        row['date'] = line.date
                        row['name'] = line.move_id.ref or line.move_id.name
                        row['account'] = account_str.ref + ' ' + account_str.name
                        debit_lines = []
                        credit_lines = []
                        if self.is_open:
                            if line.debit>0:
    #                             debit = line.amount_residual
                                ch_debit,other_amount=self._amount_residual([line])
                                debit=abs(ch_debit)+abs(other_amount)
                                credit = 0
                            else:
    #                             credit = abs(line.amount_residual)
                                ch_credit,other_amount = self._amount_residual([line])
                                credit=abs(ch_credit)+abs(other_amount)
                                debit = 0
                        else:
                            debit = line.debit
                            credit = line.credit
                        sale_line_ids=False
                        for other_line in line.move_id.line_ids :
                            if other_line.id != line.id :
                                if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                    debit_lines.append(u'Дт:'+other_line.account_id.code)
                                elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                    credit_lines.append(u'Кт:'+other_line.account_id.code)
                                if other_line.sale_line_ids:
                                    sale_line_ids=other_line.sale_line_ids
                        row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                        row['partner'] = line.partner_id.name
                        
    
                        sale_child_partner=''
    #                     print ('line.sale_line_ids ',sale_line_ids)
                        so_id=False
                        if sale_line_ids:
                            so_id=sale_line_ids[0].order_id
                            if so_id.partner_id.id != so_id.partner_invoice_id.id:
                                sale_child_partner = ' - '+so_id.partner_id.name
                        if hasattr(line.move_id, 'sale_return_id') and line.move_id.sale_return_id:
                            sale_child_partner=line.move_id.sale_return_id.partner_id.name
                            if not line.name:
                                line.name=line.move_id.name
                        narration =(line.name or '') + (sale_child_partner or '') + (so_id and ' '+so_id.name or '')  
                        if not narration:
#                             if line.move_id.type in ('in_invoice','in_refund') and line.move_id.invoice_origin:
                                narration=line.move_id.name
                        row['narration'] = narration                 
                        row['currency'] = (line.currency_id and line.currency_id.name) or ''
                        if group_row.get(line.move_id,False):
                            group_row[line.move_id]['debit'] += debit
                            group_row[line.move_id]['debit_currency'] += (line.debit > 0 and line.amount_currency) or 0
                            group_row[line.move_id]['credit_currency'] += (line.credit > 0 and abs(line.amount_currency)) or 0
                            group_row[line.move_id]['credit'] += credit
                        else:
                            row['debit'] = debit
                            row['debit_currency'] = (line.debit > 0 and line.amount_currency) or 0
                            row['credit_currency'] = (line.credit > 0 and abs(line.amount_currency)) or 0
                            row['credit'] = credit
                            
                        
                        row['so_id']=so_id
                        row['branch']=line.branch_id and line.branch_id.name or ''
                        if account.account_type== 'liability_payable':
                            balance = balance + credit - debit
                            if line.amount_currency!=0:
                                if line.credit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
                        else :
                            balance = balance + debit - credit
                            if line.amount_currency!=0:
                                if line.debit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
    
                        if group_row.get(line.move_id,False):
#                             row['balance_currency'] += balance_currency
#                             row['balance'] += balance
#                             number += 1
                            group_row[line.move_id]['balance_currency']=balance_currency
                            group_row[line.move_id]['balance']=balance
                        else:
                            row['balance_currency'] = balance_currency
                            row['balance'] = balance
                            number += 1
                            group_row[line.move_id]=row
                    for gr in group_row:                       
                        if self.is_open:
                            if debit!=0 or credit!=0:
                                result.append(group_row[gr])
                        else:
                            result.append(group_row[gr])
                else:                    
                    for line in move_line_obj.browse(line_ids):
                        row = {}
                        row['number'] = str(number)
                        row['date'] = line.date
                        row['name'] = line.move_id.ref or line.move_id.name
                        row['account'] = account_str.ref + ' ' + account_str.name
                        debit_lines = []
                        credit_lines = []
                        if self.is_open:
                            if line.debit>0:
    #                             debit = line.amount_residual
                                ch_debit,other_amount=self._amount_residual([line])
                                debit=abs(ch_debit)+abs(other_amount)
                                credit = 0
                            else:
    #                             credit = abs(line.amount_residual)
                                ch_credit,other_amount = self._amount_residual([line])
                                credit=abs(ch_credit)+abs(other_amount)
                                debit = 0
                        else:
                            debit = line.debit
                            credit = line.credit
                        sale_line_ids=False
                        for other_line in line.move_id.line_ids :
                            if other_line.id != line.id :
                                if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                    debit_lines.append(u'Дт:'+other_line.account_id.code)
                                elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                    credit_lines.append(u'Кт:'+other_line.account_id.code)
                                if other_line.sale_line_ids:
                                    sale_line_ids=other_line.sale_line_ids
                        row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                        row['partner'] = line.partner_id.name
                        
    
                        sale_child_partner=''
    #                     print ('line.sale_line_ids ',sale_line_ids)
                        so_id=False
                        if sale_line_ids:
                            so_id=sale_line_ids[0].order_id
                            if so_id.partner_id.id != so_id.partner_invoice_id.id:
                                sale_child_partner = ' - '+so_id.partner_id.name
                        if hasattr(line.move_id, 'sale_return_id') and line.move_id.sale_return_id:
                            sale_child_partner=line.move_id.sale_return_id.partner_id.name
                            if not line.name:
                                line.name=line.move_id.name
                        narration =(line.name or '') + (sale_child_partner or '') + (so_id and ' '+so_id.name or '')  
                        if not narration:
#                             if line.move_id.type in ('in_invoice','in_refund') and line.move_id.invoice_origin:
                                narration=line.move_id.name
                        row['narration'] = narration                 
    #                     row['narration'] = line.name 
                        row['currency'] = (line.currency_id and line.currency_id.name) or ''
                        row['debit_currency'] = (line.debit > 0 and line.amount_currency) or 0
                        row['debit'] = debit
                        row['credit_currency'] = (line.credit > 0 and abs(line.amount_currency)) or 0
                        row['credit'] = credit
                        
                        row['so_id']=so_id
                        row['branch']=line.branch_id and line.branch_id.name or ''
    #                     if data['account_type'] == 'payable':
                        # if account_str.user_type_id.type== 'payable':
                        if account.account_type== 'liability_payable':

                            balance = balance + credit - debit
    #                         balance_currency += line.amount_currency if line.credit == 0 else line.amount_currency
                            if line.amount_currency!=0:
                                if line.credit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
                        else :
                            balance = balance + debit - credit
    #                         balance_currency += line.amount_currency if line.debit == 0 else line.amount_currency
                            if line.amount_currency!=0:
                                if line.debit>0 :
                                    balance_currency += abs(line.amount_currency)
                                else:
                                    balance_currency -= abs(line.amount_currency)
    
                        row['balance_currency'] = balance_currency
                        row['balance'] = balance
                        row['create_uid'] = line.move_id.create_uid.name
                        row['create_date'] = line.move_id.create_date
                        number += 1
                        if self.is_open:
                            if debit!=0 or credit!=0:
                                result.append(row)
                        else:
                            result.append(row)
                        
                a.append([initial_amount, initial_amount_currency, result,acc])
                check_bal=1
        #return initial_amount, initial_amount_currency, result
        return a,check_bal    
            
    def get_report_data_inv(self, data):
        ''' Харилцагчийн өглөг авлагын гүйлгээг эхний үлдэгдэлийн хамтаар
            боловсруулж бэлтгэнэ.
        '''
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        
        partner_ids = []
        if data['partner_id']:
            partner_ids = [data['partner_id'][0]]
#             child_ids = partner_obj.search([('parent_id','=',data['partner_id'][0])])
#             if child_ids :
#                 partner_ids = partner_ids + child_ids
        account_ids = []
        if data['account_id']:
#             account_ids = [data['account_id'][0]]
            account_ids = account_obj.search([('id','=',data['account_id'][0])])
        elif data['account_type'] == 'payable':
            account_ids = account_obj.search([('account_type','=','liability_payable')])
        elif data['account_type'] == 'receivable':
            account_ids = account_obj.search([('account_type','=','asset_receivable')])

        date_where = ""
        
        date_where = " m.date < '%s' " % data['date_from']
        state_where = ""
        state_invoice_where=""
        if data['state_invoice']=='all':
            state_invoice_where=" AND l.state in ('open','paid')"
        else:
            state_invoice_where=" AND l.state ='{0}'".format(data['state_invoice'])
        if data['target_move'] != 'all':
            state_where = " AND m.state = '%s' " % data['target_move']
        partner_where = " AND l.partner_id is not null "
        if partner_ids :
            partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        if self.company_id:
            partner_where += " AND l.company_id = {0}".format(self.company_id.id)        
        a = []
        for account in account_ids.ids:
            cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "WHERE "+date_where+
                       " "+state_where+partner_where+" "
                       " AND l.account_id = " + str(account) +
                       " GROUP BY l.account_id ")
#             AND l.state <> 'draft' 
            fetched = cr.fetchone()
#             print "fetched::::::",fetched
            if fetched:
                q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
                           FROM account_move_line l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN account_period p ON (p.id=l.period_id) \
                           WHERE "+date_where+" "+state_where \
                           + partner_where+"  AND l.account_id = " + str(account) + " GROUP BY l.account_id "
#                 print 'Query;       ', q
#                 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
            sdebit, scredit, samount_currency = fetched or (0,0,0)
            account_str = account_obj.browse(account)
            acc=account_str.code + ' ' + account_str.name
            if data['account_type'] == 'payable':
                initial_amount = scredit - sdebit
                initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
            else :
                initial_amount = sdebit - scredit
                initial_amount_currency = samount_currency
            
            balance, balance_currency = initial_amount, initial_amount_currency
            #balance, balance_currency = 0, 0
            invoice_obj = self.env['account.invoice']
            date_where1 = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
            # if initial_bal_journal:
            #     date_where1 += "AND l.journal_id <> %s " % initial_bal_journal
            cr.execute("SELECT l.id  FROM account_invoice l "
                        "   LEFT JOIN account_move m ON (m.id=l.move_id) "
                        "   LEFT JOIN res_partner r ON (l.partner_id=r.id) "
                       "WHERE "+date_where1+"  "
                       " "+state_where+partner_where+" "
                       " AND l.account_id =  " + str(account)+ " "
                       " "+state_invoice_where+" "
                       "ORDER BY l.date, r.name")
#             data['fiscalyear_id'], AND p.fiscalyear_id = %s
#                        "LEFT JOIN account_period p ON (p.id=l.period_id) "
            fetched = cr.fetchall()
            result = []
            number = 1
            if fetched or initial_amount!=0:
                q1 = "SELECT l.id  FROM account_invoice l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN res_partner r ON (l.partner_id=r.id) \
                           WHERE "+date_where1+" \
                           \ "+state_where+partner_where+" AND l.account_id = " + str(account) + " \
                           "+state_invoice_where+" \
                           ORDER BY m.date, r.name"
#                            LEFT JOIN account_period p ON (p.id=l.period_id) \
# AND p.fiscalyear_id = " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
#                 print 'Q1 :  ', q1
                line_ids = [x[0] for x in fetched]
                for line in invoice_obj.browse(line_ids):
                    row = {}
                    row['number'] = str(number)
                    row['date'] = line.move_id.date
                    row['name'] = line.move_id.ref or line.move_id.name
                    row['account'] = account_str.code + ' ' + account_str.name
                    debit_lines = []
                    credit_lines = []
                    for other_line in line.move_id.line_ids :
                        if other_line.id != line.id :
                            if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                debit_lines.append(u'Дт:'+other_line.account_id.code)
                            elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                credit_lines.append(u'Кт:'+other_line.account_id.code)
                    row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                    row['partner'] = line.partner_id.name
                    row['narration'] = line.name or line.narration
                    row['currency'] = (line.currency_id and line.currency_id.name) or ''
                    row['debit_currency'] = 0#(line.amount > 0 and line.amount_currency) or 0
                    if line.type=='out_refund':
                        row['credit'] =line.amount_total
                        row['debit'] = 0#line.amount_total
                    else:
                        row['credit'] = 0#line.amount_total
                        row['debit'] = line.amount_total
                    row['credit_currency'] = 0#(line.credit > 0 and abs(line.amount_currency)) or 0
#                     balance = balance + line.amount_total
                    balance = balance + row['debit'] - row['credit']

                    row['balance_currency'] = balance_currency
                    row['balance'] = balance
                    number += 1
                    result.append(row)
                    
                a.append([initial_amount, initial_amount_currency, result,acc])
        return a
                

    def _get_partners(self):
        partners=[]
        if self.partner_id:
            partners = [self.partner_id]
        elif self.tag_id:
            partners = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])
        return partners
    
#         if data['partner_id']:
#             partners = [self.env['res.partner'].browse(data['partner_id'][0])]
#         elif self.tag_id:
#             partners = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])


    def _get_accounts(self,partners):
        account_ids = []
        account_obj = self.env['account.account']
        if self.account_id:
#             account_ids = [data['account_id'][0]]
            account_ids = self.account_id
        else:
            account_ids = account_obj.search(
                                 domain=['|', ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                                         ('is_recpay', '=', True)])

        if self.account_id:
            add_account_ids = account_obj.search([('is_recpay','=',True)])
            account_ids+=add_account_ids        
        return account_ids
    
                            
    def _make_excel(self, data):
        account_obj = self.env['account.account']
        styledict = self.env['abstract.report.excel'].get_easyxf_styles()
        
        ezxf = xlwt.easyxf
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet(u'Payable Receivable Detail')

        data = data['form']
        if self.is_group_account:
            partners=self._get_partners()
            accounts=self._get_accounts(partners)
    #         
            title = ''
            report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
            sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
            rowx = 5
            total_rec=0
            total_pay=0
            for account in accounts:
                
                date_str = '%s-%s' % (
        #             datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
        #             datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
                        data['date_from'],
                         data['date_to']
                )
                '''
                if context['report_type'] == 'payable' :
                    title = u'Маягт ӨГ-2'
                    report_name = u'Өглөгийн дансны дэлгэрэнгүй бүртгэл'
                else :
                    title = u'Маягт АВ-2'
                    report_name = u'Авлагын дансны дэлгэрэнгүй бүртгэл'
                '''
                check_bal=1
                # self.get_report_data_account(accounts)
                datas,check_bal = self.get_report_data_account(data,account,partners)
                if check_bal==0:
                    continue
    #             title = ''
    #             report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
    #             sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
    #             sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
    #             sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
                sheet.write(rowx, 8, u'Тайлант хугацаа: %s' % date_str, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
                sheet.write(rowx, 0, u"Дансны код: %s" % ((account and (account.code or '')) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
                sheet.write(rowx+1, 0, u"Дансны нэр: %s" % ((account and account.name) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
                sheet.write(rowx+1, 8, time.strftime('%Y-%m-%d %H:%M'), xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
                rowx+=3
    #             rowx = 8
                
                reports = ['receivable','payable']
                
                total_amount=[0,0,0,0,0,0]
                tmp_amount = [0,0,0,0,0,0]
                report_num = 0
    #             for report in reports:
    #                 data['account_type'] = report
                if data['account_id']:
                    acc = account_obj.browse(data['account_id'][0])
    #                 if acc.user_type_id.type != report: continue
                if self.is_currency:
                    sheet.write_merge(rowx, rowx+2, 0, 0, u'№', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 1, 1, u'Огноо', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 3, 3, u'Данс', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 6, 9, u'Гүйлгээний дүн', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 10, 11, u'Үлдэгдэл', styledict['heading_xf'])
                    rowx += 1
                    sheet.write_merge(rowx, rowx, 6, 7, u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 8, 9, u'Кредит', styledict['heading_xf'])
                    #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 10, 11, '', styledict['heading_xf']) #(report == 'payable' and u'Кредит') or u'Дебет'
                    sheet.write_merge(rowx-1, rowx+1, 12, 12, u'Харьцсан данс', styledict['heading_xf'])
                    rowx += 1
                    sheet.write(rowx, 6, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
                    sheet.write(rowx, 8, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
                    sheet.write(rowx, 10, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
                    sheet.panes_frozen = True
                    sheet.horz_split_pos = 11  # freeze the first row
                    rowx += 1
                else:
                    sheet.write_merge(rowx, rowx+1, 0, 0, u'№', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 1, 1, u'Огноо', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 3, 3, u'Данс', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
    #                 sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 5, 6, u'Гүйлгээний дүн', styledict['heading_xf'])
                    sheet.write(rowx, 7, u'Үлдэгдэл', styledict['heading_xf'])
                    rowx += 1
                    sheet.write(rowx, 5, u'Дебет', styledict['heading_xf'])
                    sheet.write(rowx, 6, u'Кредит', styledict['heading_xf'])
                    #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write(rowx, 7, '', styledict['heading_xf']) #(report == 'payable' and u'Кредит') or u'Дебет'
                    sheet.write_merge(rowx-1, rowx, 8, 8, u'Харьцсан данс', styledict['heading_xf'])
                    sheet.panes_frozen = True
                    sheet.horz_split_pos = 10  # freeze the first row
                    if self.is_warehouse and not data['is_from_invoice']:
                        sheet.write_merge(rowx-1, rowx, 9, 9, u'Агуулах', styledict['heading_xf'])
                        sheet.write_merge(rowx-1, rowx, 10, 10, u'Салбар', styledict['heading_xf'])
                    else:
                        sheet.write_merge(rowx-1, rowx, 9, 9, u'Салбар', styledict['heading_xf'])
    #                 rowx += 1
                    rowx += 1            
                totals = [0,0,0,0,0,0]
                for d in datas:
    #                     print ('dddddd',d)
                    if self.is_currency:
                        sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                        sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                        sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                        sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 7, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
                #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
                        sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
                        sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
                        sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
                        rowx += 1
                        number = 0
                        balance = 0
                        balance_currency =0
                        for line in d[2]:
                            
                            sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                            sheet.row(rowx).height = 370
                            sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                            sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                            sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                            sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
                            sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
                            sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['debit'], styledict['number_xf'])
                            sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 9, line['credit'], styledict['number_xf'])
                            sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                            sheet.write(rowx, 11, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 12, line['other'], styledict['text_xf'])
                            totals[0] += line['debit_currency']
                            totals[1] += line['debit']
                            totals[2] += line['credit_currency']
                            totals[3] += line['credit']
                            balance_currency = line['balance_currency']
                            balance = line['balance']
                            number = int(line['number'])
                            rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance
                    else:
                        sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                        sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                        sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                        sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 7, d[0], styledict['heading_xf-grey'])
                        sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                        if self.is_warehouse and not data['is_from_invoice']:
                            sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                            sheet.write(rowx, 10, 'x', styledict['heading_xf-grey'])
                        else:
                            sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                        if not d[2]:#Гүйлгээгүй бол
                            totals[5]+=d[0]#20210322 эцсийн үлдэгдэлд эхний үлд орох
                        
                        rowx += 1
                        
                        number = 0
                        balance = 0
                        balance_currency =0
                        d_dict={}
                        if self.is_date:
                            for line in d[2]:
                                if line['date'] in d_dict:
                                # if d_dict.has_key(line['date']):
                                    d_dict[line['date']]['debit']+=line['debit']
                                    d_dict[line['date']]['credit']+=line['credit']
                                else:
                                    d_dict[line['date']]={'debit':line['debit'],
                                                          'credit':line['credit'],
                                                          'account':line['account'],
                                                          'balance':line['balance'],
                                                          }
                            od = collections.OrderedDict(sorted(d_dict.items()))
                            m=1
                            for i in od:
    #                            print 'ii ',d_dict
                                sheet.write(rowx, 0, m, styledict['text_center_xf'])
                                sheet.row(rowx).height = 370
                                sheet.write(rowx, 1, i, styledict['text_center_xf'])
                                sheet.write(rowx, 2, '', styledict['text_xf'])
                                sheet.write(rowx, 3, od[i]['account'], styledict['text_xf'])
                                sheet.write(rowx, 4, '', styledict['text_xf'])
                                sheet.write(rowx, 5, od[i]['debit'], styledict['number_xf'])
                                sheet.write(rowx, 6, od[i]['credit'], styledict['number_xf'])
    #                             sheet.write(rowx, 7, d_dict[i]['balance'], styledict['number_xf'])
    #                             sheet.add_formula(rowx, 7, 
    #                                 '=H'+rowx-1+'+F'+rowx+'-G'+rowx+'', styledict['number_xf'])
    #                             sheet.write(rowx, 7, xlwt.Formula('H'+`rowx`+'+F'+`rowx+1`+'-G'+`rowx+1`+''), styledict['number_xf'])
                                
                                sheet.write(rowx, 8, '', styledict['text_xf'])
                                
                                m+=1
                                rowx+=1
                        else:
                            for line in d[2]:
                                sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                                sheet.row(rowx).height = 370
                                sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                                sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                                sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                                sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
        #                         sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
        #                         sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                                sheet.write(rowx, 5, line['debit'], styledict['number_xf'])
        #                         sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                                sheet.write(rowx, 6, line['credit'], styledict['number_xf'])
        #                         sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                                sheet.write(rowx, 7, line['balance'], styledict['number_xf'])
                                sheet.write(rowx, 8, line['other'], styledict['text_xf'])
                                branch=line['branch']
                                if self.is_warehouse and not data['is_from_invoice']:
                                    wh=''
                                    if line['so_id']:
                                        if line['so_id'].warehouse_id:
                                            wh=line['so_id'].warehouse_id.name
                                    sheet.write(rowx, 9, wh, styledict['text_xf'])
                                    sheet.write(rowx, 10, branch, styledict['text_xf'])
                                else:
                                    sheet.write(rowx, 9, branch, styledict['text_xf'])
                                
                                rowx+=1
                                totals[0] += line['debit_currency']
                                totals[1] += line['debit']
                                totals[2] += line['credit_currency']
                                totals[3] += line['credit']
                                balance_currency = line['balance_currency']
                                balance = line['balance']
                                number = int(line['number'])
                            rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance  
    #                     print ('totals====: ',totals)      
                    if self.is_currency:
                        sheet.write_merge(rowx, rowx, 0, 5, u'ДЭД ДҮН', styledict['heading_xf-1'])
                        sheet.write(rowx, 6, totals[0], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 7, totals[1], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 8, totals[2], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 9, totals[3], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 10, totals[4], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 11, totals[5], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 12, '', styledict['heading_xf-1'])
                        rowx += 1
                        if report_num == 0:
                            sheet.write_merge(rowx, rowx+1, 0, 12, '', styledict['text_xf'])
                            rowx += 2
                        report_num += 1
                        total_amount[0] += totals[0]
                        total_amount[1] += totals[1]
                        total_amount[2] += totals[2]
                        total_amount[3] += totals[3]
                        total_amount[4] += totals[4]
                        total_amount[5] += totals[5]
                    else:
                        sheet.write_merge(rowx, rowx, 0, 4, u'ДЭД ДҮН', styledict['heading_xf-1'])
                        sheet.write(rowx, 5, totals[1], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 6, totals[3], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 7, totals[5], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 8, '', styledict['heading_xf-1'])
                        if self.is_warehouse and not data['is_from_invoice']:
                            sheet.write(rowx, 9, '', styledict['heading_xf-1'])
                            sheet.write(rowx, 10, '', styledict['heading_xf-1'])
                        else:
                            sheet.write(rowx, 9, '', styledict['heading_xf-1'])
                        
                        rowx += 1
                        if report_num == 0:
                            sheet.write_merge(rowx, rowx+1, 0, 8, '', styledict['text_xf'])
                            rowx += 2
                        report_num += 1
                        total_amount[0] += totals[0]
                        total_amount[1] += totals[1]
                        total_amount[2] += totals[2]
                        total_amount[3] += totals[3]
                        total_amount[4] += totals[4]
                        total_amount[5] += totals[5]
                if self.is_currency:
                    if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
                    else: total_amount[0] = -total_amount[0]
                    if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
                    else: total_amount[1] = -total_amount[1]
                    if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
                    else: total_amount[2] = -total_amount[2]
                    if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
                    else: total_amount[3] = -total_amount[3]
                    if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
                    else: total_amount[4] = -total_amount[4]
                    if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
                    else: total_amount[5] = -total_amount[5]
                    
                    sheet.write_merge(rowx, rowx, 0, 5, u'ДЭД ДҮН', styledict['heading_xf'])
                    sheet.write(rowx, 6, total_amount[0], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 7, total_amount[1], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 8, total_amount[2], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 12, '', styledict['heading_xf'])
                    inch = 60
                    sheet.col(0).width = 12*inch
                    sheet.col(1).width = 37*inch
                    sheet.col(2).width = 38*inch
                    sheet.col(3).width = 75*inch
                    sheet.col(4).width = 80*inch
                    sheet.col(5).width = 36*inch
                    sheet.col(6).width = 40*inch
                    sheet.col(7).width = 55*inch
                    sheet.col(8).width = 40*inch
                    sheet.col(9).width = 55*inch
                    sheet.col(10).width = 40*inch
                    sheet.col(11).width = int(59.5*inch)
                    sheet.col(12).width = 42*inch
                else:
                    if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
                    else: total_amount[0] = -total_amount[0]
                    if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
                    else: total_amount[1] = -total_amount[1]
                    if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
                    else: total_amount[2] = -total_amount[2]
                    if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
                    else: total_amount[3] = -total_amount[3]
                    if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
                    else: total_amount[4] = -total_amount[4]
                    if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
                    else: total_amount[5] = -total_amount[5]
    #                 print ('total_amount=======: ',total_amount)
                    sheet.write_merge(rowx, rowx, 0, 4, u'НИЙТ ДҮН /бүгд/', styledict['heading_xf'])
                    sheet.write(rowx, 5, total_amount[1], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 6, total_amount[3], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 7, total_amount[5], styledict['number_boldtotal_xf'])
        #             sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
        #             sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
        #             sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 8, '', styledict['heading_xf'])
                    if self.is_warehouse and not data['is_from_invoice']:
                        sheet.write(rowx, 9, '', styledict['heading_xf'])
                        sheet.write(rowx, 10, '', styledict['heading_xf'])
                    else:
                        sheet.write(rowx, 9, '', styledict['heading_xf'])
                    
                    inch = 60
                    sheet.col(0).width = 12*inch
                    sheet.col(1).width = 37*inch
                    sheet.col(2).width = 42*inch
                    sheet.col(3).width = 85*inch
                    sheet.col(4).width = 85*inch
                    sheet.col(5).width = 36*inch
                    sheet.col(6).width = 40*inch
                    sheet.col(7).width = 55*inch
                    sheet.col(8).width = 55*inch
    #             if report=='receivable':
                total_rec+=total_amount[5]
                rowx+=3
            sheet.write(rowx+4, 3, u"Зөвшөөрсөн: Эд хариуцагч ......................................... /                                         /", 
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write(rowx+6, 3, u"Боловсруулсан: Нягтлан бодогч ......................................... /                                         /", 
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write(rowx+8, 3, u"Хянасан: Ерөнхий нягтлан бодогч .............................................../                                         /", 
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        else:
            partner = False
            partners=self._get_partners()
    #         
            title = ''
            report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
            sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
            rowx = 5
            total_rec=0
            total_pay=0
            for partner in partners:
                
                date_str = '%s-%s' % (
        #             datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
        #             datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
                        data['date_from'],
                         data['date_to']
                )
                '''
                if context['report_type'] == 'payable' :
                    title = u'Маягт ӨГ-2'
                    report_name = u'Өглөгийн дансны дэлгэрэнгүй бүртгэл'
                else :
                    title = u'Маягт АВ-2'
                    report_name = u'Авлагын дансны дэлгэрэнгүй бүртгэл'
                '''
                check_bal=1
                if data['is_from_invoice']:
                    datas = self.get_report_data_inv(data)
                else:
                    datas,check_bal = self.get_report_data(data,partner)
                if check_bal==0:
                    continue
    #             title = ''
    #             report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
    #             sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
    #             sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
    #             sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
                sheet.write(rowx, 8, u'Тайлант хугацаа: %s' % date_str, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
                sheet.write(rowx, 0, u"Харилцагчийн код: %s" % ((partner and (partner.ref or '')) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
                sheet.write(rowx+1, 0, u"Харилцагчийн нэр: %s" % ((partner and partner.name) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
                sheet.write(rowx+1, 8, time.strftime('%Y-%m-%d %H:%M'), xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
                rowx+=3
    #             rowx = 8
                
                reports = ['receivable','payable']
                
                total_amount=[0,0,0,0,0,0]
                tmp_amount = [0,0,0,0,0,0]
                report_num = 0
    #             for report in reports:
    #                 data['account_type'] = report
                if data['account_id']:
                    acc = account_obj.browse(data['account_id'][0])
    #                 if acc.user_type_id.type != report: continue
                if self.is_currency:
                    sheet.write_merge(rowx, rowx+2, 0, 0, u'№', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 1, 1, u'Огноо', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 3, 3, u'Данс', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 6, 9, u'Гүйлгээний дүн', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 10, 11, u'Үлдэгдэл', styledict['heading_xf'])
                    rowx += 1
                    sheet.write_merge(rowx, rowx, 6, 7, u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 8, 9, u'Кредит', styledict['heading_xf'])
                    #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 10, 11, '', styledict['heading_xf']) #(report == 'payable' and u'Кредит') or u'Дебет'
                    sheet.write_merge(rowx-1, rowx+1, 12, 12, u'Харьцсан данс', styledict['heading_xf'])
                    rowx += 1
                    sheet.write(rowx, 6, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
                    sheet.write(rowx, 8, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
                    sheet.write(rowx, 10, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
                    sheet.panes_frozen = True
                    sheet.horz_split_pos = 11  # freeze the first row
                    rowx += 1
                else:
                    sheet.write_merge(rowx, rowx+1, 0, 0, u'№', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 1, 1, u'Огноо', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 3, 3, u'Данс', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
    #                 sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 5, 6, u'Гүйлгээний дүн', styledict['heading_xf'])
                    sheet.write(rowx, 7, u'Үлдэгдэл', styledict['heading_xf'])
                    rowx += 1
                    sheet.write(rowx, 5, u'Дебет', styledict['heading_xf'])
                    sheet.write(rowx, 6, u'Кредит', styledict['heading_xf'])
                    #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write(rowx, 7, '', styledict['heading_xf']) #(report == 'payable' and u'Кредит') or u'Дебет'
                    sheet.write_merge(rowx-1, rowx, 8, 8, u'Харьцсан данс', styledict['heading_xf'])
                    sheet.panes_frozen = True
                    sheet.horz_split_pos = 10  # freeze the first row
                    if self.is_warehouse and not data['is_from_invoice']:
                        sheet.write_merge(rowx-1, rowx, 9, 9, u'Агуулах', styledict['heading_xf'])
                        sheet.write_merge(rowx-1, rowx, 10, 10, u'Салбар', styledict['heading_xf'])
                    else:
                        sheet.write_merge(rowx-1, rowx, 9, 9, u'Салбар', styledict['heading_xf'])
    #                 rowx += 1
                    rowx += 1            
                totals = [0,0,0,0,0,0]
                for d in datas:
    #                     print ('dddddd',d)
                    if self.is_currency:
                        sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                        sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                        sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                        sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 7, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
                #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
                        sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
                        sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
                        sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
                        rowx += 1
                        number = 0
                        balance = 0
                        balance_currency =0
                        for line in d[2]:
                            
                            sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                            sheet.row(rowx).height = 370
                            sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                            sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                            sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                            sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
                            sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
                            sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['debit'], styledict['number_xf'])
                            sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 9, line['credit'], styledict['number_xf'])
                            sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                            sheet.write(rowx, 11, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 12, line['other'], styledict['text_xf'])
                            totals[0] += line['debit_currency']
                            totals[1] += line['debit']
                            totals[2] += line['credit_currency']
                            totals[3] += line['credit']
                            balance_currency = line['balance_currency']
                            balance = line['balance']
                            number = int(line['number'])
                            rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance
                    else:
                        sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                        sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                        sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                        sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 7, d[0], styledict['heading_xf-grey'])
                        sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                        if self.is_warehouse and not data['is_from_invoice']:
                            sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                            sheet.write(rowx, 10, 'x', styledict['heading_xf-grey'])
                        else:
                            sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                        if not d[2]:#Гүйлгээгүй бол
                            totals[5]+=d[0]#20210322 эцсийн үлдэгдэлд эхний үлд орох
                        
                        rowx += 1
                        
                        number = 0
                        balance = 0
                        balance_currency =0
                        d_dict={}
                        if self.is_date:
                            for line in d[2]:
                                if line['date'] in d_dict:
                                # if d_dict.has_key(line['date']):
                                    d_dict[line['date']]['debit']+=line['debit']
                                    d_dict[line['date']]['credit']+=line['credit']
                                else:
                                    d_dict[line['date']]={'debit':line['debit'],
                                                          'credit':line['credit'],
                                                          'account':line['account'],
                                                          'balance':line['balance'],
                                                          }
                            od = collections.OrderedDict(sorted(d_dict.items()))
                            m=1
                            for i in od:
    #                            print 'ii ',d_dict
                                sheet.write(rowx, 0, m, styledict['text_center_xf'])
                                sheet.row(rowx).height = 370
                                sheet.write(rowx, 1, i, styledict['text_center_xf'])
                                sheet.write(rowx, 2, '', styledict['text_xf'])
                                sheet.write(rowx, 3, od[i]['account'], styledict['text_xf'])
                                sheet.write(rowx, 4, '', styledict['text_xf'])
                                sheet.write(rowx, 5, od[i]['debit'], styledict['number_xf'])
                                sheet.write(rowx, 6, od[i]['credit'], styledict['number_xf'])
    #                             sheet.write(rowx, 7, d_dict[i]['balance'], styledict['number_xf'])
    #                             sheet.add_formula(rowx, 7, 
    #                                 '=H'+rowx-1+'+F'+rowx+'-G'+rowx+'', styledict['number_xf'])
    #                             sheet.write(rowx, 7, xlwt.Formula('H'+`rowx`+'+F'+`rowx+1`+'-G'+`rowx+1`+''), styledict['number_xf'])
                                
                                sheet.write(rowx, 8, '', styledict['text_xf'])
                                
                                m+=1
                                rowx+=1
                        else:
                            for line in d[2]:
                                sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                                sheet.row(rowx).height = 370
                                sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                                sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                                sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                                sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
        #                         sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
        #                         sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                                sheet.write(rowx, 5, line['debit'], styledict['number_xf'])
        #                         sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                                sheet.write(rowx, 6, line['credit'], styledict['number_xf'])
        #                         sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                                sheet.write(rowx, 7, line['balance'], styledict['number_xf'])
                                sheet.write(rowx, 8, line['other'], styledict['text_xf'])
                                branch=line['branch']
                                if self.is_warehouse and not data['is_from_invoice']:
                                    wh=''
                                    if line['so_id']:
                                        if line['so_id'].warehouse_id:
                                            wh=line['so_id'].warehouse_id.name
                                    sheet.write(rowx, 9, wh, styledict['text_xf'])
                                    sheet.write(rowx, 10, branch, styledict['text_xf'])
                                else:
                                    sheet.write(rowx, 9, branch, styledict['text_xf'])
                                
                                rowx+=1
                                totals[0] += line['debit_currency']
                                totals[1] += line['debit']
                                totals[2] += line['credit_currency']
                                totals[3] += line['credit']
                                balance_currency = line['balance_currency']
                                balance = line['balance']
                                number = int(line['number'])
                            rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance  
    #                     print ('totals====: ',totals)      
                    if self.is_currency:
                        sheet.write_merge(rowx, rowx, 0, 5, u'ДЭД ДҮН', styledict['heading_xf-1'])
                        sheet.write(rowx, 6, totals[0], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 7, totals[1], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 8, totals[2], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 9, totals[3], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 10, totals[4], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 11, totals[5], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 12, '', styledict['heading_xf-1'])
                        rowx += 1
                        if report_num == 0:
                            sheet.write_merge(rowx, rowx+1, 0, 12, '', styledict['text_xf'])
                            rowx += 2
                        report_num += 1
                        total_amount[0] += totals[0]
                        total_amount[1] += totals[1]
                        total_amount[2] += totals[2]
                        total_amount[3] += totals[3]
                        total_amount[4] += totals[4]
                        total_amount[5] += totals[5]
                    else:
                        sheet.write_merge(rowx, rowx, 0, 4, u'ДЭД ДҮН', styledict['heading_xf-1'])
                        sheet.write(rowx, 5, totals[1], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 6, totals[3], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 7, totals[5], styledict['grey_number_bold_xf'])
                        sheet.write(rowx, 8, '', styledict['heading_xf-1'])
                        if self.is_warehouse and not data['is_from_invoice']:
                            sheet.write(rowx, 9, '', styledict['heading_xf-1'])
                            sheet.write(rowx, 10, '', styledict['heading_xf-1'])
                        else:
                            sheet.write(rowx, 9, '', styledict['heading_xf-1'])
                        
                        rowx += 1
                        if report_num == 0:
                            sheet.write_merge(rowx, rowx+1, 0, 8, '', styledict['text_xf'])
                            rowx += 2
                        report_num += 1
                        total_amount[0] += totals[0]
                        total_amount[1] += totals[1]
                        total_amount[2] += totals[2]
                        total_amount[3] += totals[3]
                        total_amount[4] += totals[4]
                        total_amount[5] += totals[5]
                if self.is_currency:
                    if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
                    else: total_amount[0] = -total_amount[0]
                    if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
                    else: total_amount[1] = -total_amount[1]
                    if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
                    else: total_amount[2] = -total_amount[2]
                    if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
                    else: total_amount[3] = -total_amount[3]
                    if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
                    else: total_amount[4] = -total_amount[4]
                    if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
                    else: total_amount[5] = -total_amount[5]
                    
                    sheet.write_merge(rowx, rowx, 0, 5, u'ДЭД ДҮН', styledict['heading_xf'])
                    sheet.write(rowx, 6, total_amount[0], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 7, total_amount[1], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 8, total_amount[2], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 12, '', styledict['heading_xf'])
                    inch = 60
                    sheet.col(0).width = 12*inch
                    sheet.col(1).width = 37*inch
                    sheet.col(2).width = 38*inch
                    sheet.col(3).width = 75*inch
                    sheet.col(4).width = 80*inch
                    sheet.col(5).width = 36*inch
                    sheet.col(6).width = 40*inch
                    sheet.col(7).width = 55*inch
                    sheet.col(8).width = 40*inch
                    sheet.col(9).width = 55*inch
                    sheet.col(10).width = 40*inch
                    sheet.col(11).width = int(59.5*inch)
                    sheet.col(12).width = 42*inch
                else:
                    if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
                    else: total_amount[0] = -total_amount[0]
                    if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
                    else: total_amount[1] = -total_amount[1]
                    if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
                    else: total_amount[2] = -total_amount[2]
                    if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
                    else: total_amount[3] = -total_amount[3]
                    if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
                    else: total_amount[4] = -total_amount[4]
                    if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
                    else: total_amount[5] = -total_amount[5]
    #                 print ('total_amount=======: ',total_amount)
                    sheet.write_merge(rowx, rowx, 0, 4, u'НИЙТ ДҮН /бүгд/', styledict['heading_xf'])
                    sheet.write(rowx, 5, total_amount[1], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 6, total_amount[3], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 7, total_amount[5], styledict['number_boldtotal_xf'])
        #             sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
        #             sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
        #             sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
                    sheet.write(rowx, 8, '', styledict['heading_xf'])
                    if self.is_warehouse and not data['is_from_invoice']:
                        sheet.write(rowx, 9, '', styledict['heading_xf'])
                        sheet.write(rowx, 10, '', styledict['heading_xf'])
                    else:
                        sheet.write(rowx, 9, '', styledict['heading_xf'])
                    
                    inch = 60
                    sheet.col(0).width = 12*inch
                    sheet.col(1).width = 37*inch
                    sheet.col(2).width = 42*inch
                    sheet.col(3).width = 85*inch
                    sheet.col(4).width = 85*inch
                    sheet.col(5).width = 36*inch
                    sheet.col(6).width = 40*inch
                    sheet.col(7).width = 55*inch
                    sheet.col(8).width = 55*inch
    #             if report=='receivable':
                total_rec+=total_amount[5]
                rowx+=3
            sheet.write(rowx+4, 3, u"Зөвшөөрсөн: Эд хариуцагч ......................................... /                                         /", 
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write(rowx+6, 3, u"Боловсруулсан: Нягтлан бодогч ......................................... /                                         /", 
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
            sheet.write(rowx+8, 3, u"Хянасан: Ерөнхий нягтлан бодогч .............................................../                                         /", 
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
                        
        # Тооцоо нийлсэн акт
        if self.is_tootsoo:
            sheet = book.add_sheet(u'Act')
    
            partner = False
            partners=[]
            if not data['partner_id']:
                raise UserError((u'Тооцоо нийлсэн акт хэвлэх бол харилцагч заавал сонгоно уу.'))
            else:
                partners = [self.env['res.partner'].browse(data['partner_id'][0])]
                
            sheet.write_merge(1, 1, 0, 3, self.env.user.company_id.name, xlwt.easyxf('font:height 200;align:wrap off,vert centre,horiz right;'))
            rowx = 2
            report_name = u'ТООЦОО НИЙЛСЭН АКТ'
            sheet.write_merge(3, 3, 0, 3, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
            rowx = 5
            sheet.write_merge(5, 5, 0, 3, '%s' % (data['date_to']), xlwt.easyxf('font:height 200;align:wrap off,vert centre,horiz right;'))
            rowx = 7
            for partner in partners:
                date_str = '%s-%s' % (
                        data['date_from'],
                         data['date_to']
                )

                rowx+=1
                amstr=''
                list=verbose_format(abs(total_rec-total_pay)) 
#                 print ('list ',list)
                if abs(total_rec)>abs(total_pay):
                    rep=u' авлагатайгаар '
                    amstr='%s'%(str(total_rec-total_pay))
                else:
                    rep=u' өглөгтэйгээр '
                    amstr='%s'%(str(total_pay-total_rec))
                sheet.write_merge(7, 11, 0, 3,  u"Нэг талаас : %s ХХК нягтлан бодогч ажилтай ............................. нөгөө талаас : %s нягтлан бодогч ажилтай %s нар тус хоёр байгууллагын хооронд %s -ний өдрийг дуусталх  хугацаанд өгч авалцсан зүйлээ хоёр байгууллагад хөтлөгдөж буй нягтлан бодох бүртгэлийн дэлгэрэнгүй ба хураангуй бүртгэлээр нэг бүрчлэн нийлж үзэхэд  %s төгрөгийн %s гарсаныг харилцан батлав." % ((partner and (partner.name or '')) or '',self.env.user.company_id.name,self.create_uid.name, date_str,amstr,rep), xlwt.easyxf('align:wrap on,vert centre,horiz left;'))
                rowx+=1
#                 sheet.write(rowx, 8, time.strftime('%Y-%m-%d %H:%M'), xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
                            
                sheet.col(0).width = 140*inch
                sheet.col(1).width = 80*inch
                sheet.col(2).width = 80*inch
                sheet.col(3).width = 140*inch
                rowx+=3
                amstr=''
                list=verbose_format(abs(total_rec-total_pay)) 
#                 print ('list ',list)
                sheet.write_merge(12, 13, 0, 3, list,
                                   xlwt.easyxf('align:wrap on,vert centre,horiz centre; pattern: pattern solid, fore_colour gray25'))
                rowx+=2                
                sheet.write(rowx, 0, u"Тооцоо нийлсэн байгууллагууд:", xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                rowx+=2
                sheet.write(rowx, 0, partner.name, xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                sheet.write(rowx, 1, u"Нягтлан бодогч: ............................................ /........................../", xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                rowx+=1 
                sheet.write(rowx, 0, u"Тамга: ", xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                rowx+=2
                sheet.write(rowx, 0, self.env.user.company_id.name, xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                sheet.write(rowx, 1, u"Нягтлан бодогч: ............................................ /%s/ "%(self.create_uid.name), xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                rowx+=1 
                sheet.write(rowx, 0, u"Тамга: ", xlwt.easyxf('align:wrap off,vert centre,horiz left;'))
                rowx+=4
    #             rowx = 8
                
                reports = ['receivable','payable']
                
                total_amount=[0,0,0,0,0,0]
                tmp_amount = [0,0,0,0,0,0]
                report_num = 0
                sheet.write(rowx, 0, u'Огноо', xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left; borders: top thin, left thin, bottom thin, right thin, '))
                sheet.write(rowx, 1, u'Авлага', xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left; borders: top thin, left thin, bottom thin, right thin, '))
                sheet.write(rowx, 2, u'Өглөг', xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left; borders: top thin, left thin, bottom thin, right thin, '))
                sheet.write(rowx, 3, u'Гүйлгээний утга', xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left; borders: top thin, left thin, bottom thin, right thin, '))
                rowx += 1
                sheet.write(rowx, 0, '%s' % (data['date_to']), styledict['text_xf'])
                sheet.write(rowx, 1, abs(total_rec), styledict['number_xf'])
                sheet.write(rowx, 2, abs(total_pay), styledict['number_xf'])
                sheet.write(rowx, 3, u'Хоорондын тооцоо', styledict['text_xf'])

                rowx += 1
                sheet.write(rowx, 0, '', styledict['text_xf'])
                sheet.write(rowx, 1, '', styledict['number_xf'])
                sheet.write(rowx, 2, '', styledict['number_xf'])
                sheet.write(rowx, 3, '', styledict['number_xf'])
                rowx += 1
                sheet.write(rowx, 0, '', styledict['text_xf'])
                sheet.write(rowx, 1, '', styledict['number_xf'])
                sheet.write(rowx, 2, '', styledict['number_xf'])
                sheet.write(rowx, 3, '', styledict['number_xf'])
                rowx += 1
                sheet.write(rowx, 0, u'ДҮН', styledict['text_xf'])
                sheet.write(rowx, 1, abs(total_rec), styledict['number_xf'])
                sheet.write(rowx, 2, abs(total_pay), styledict['number_xf'])
                sheet.write(rowx, 3, '', styledict['text_xf'])
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)
        
        filename = "partner_balance_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
#         out = base64.encodebytes(buffer.getvalue())
        out = encodebytes(buffer.getvalue())
        buffer.close()
        
        excel_id = self.env['report.excel.output'].create({
                                'data':out,
                                'name':filename
        })
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }    

    def print_report_html(self):
        print ('aaaaaa123')
        self.ensure_one()
        result_context=dict(self._context or {})
        self.ensure_one()
        result_context=dict(self._context or {})
        
#         data['form'].update(self._build_contexts(data))
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
         
        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
        data['account_id']=self.account_id and self.account_id.id or False
        data['partner_id']=self.partner_id and [self.partner_id.id] or []
        
        data['date_from']=self.date_from
        data['date_to']=self.date_to
        data['target_move']=self.target_move
        reports = ['receivable','payable']
        
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        
        
        total_amount=[0,0,0,0,0,0]
        tmp_amount = [0,0,0,0,0,0]
        all_datas=[]
        report_num = 0
        partners=[]
#         if data['partner_id']:
#             partners = [self.env['res.partner'].browse(data['partner_id'][0])]
#         elif self.tag_id:
#             partners = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])
        partners=self._get_partners()
            
        title = ''
        rowx = 5
        check_bal=1
        for partner in partners:
            totals = [0,0,0,0,0,0]
#             for report in reports:
#                 data['account_type'] = report
#             print 'data[] ',data['account_id']
            if data['account_id']:
                acc = account_obj.browse(data['account_id'][0])
                # if acc.user_type_id.type != report: continue
#             if False:#self.is_currency:
#                 rowx += 1            
            datas,check_bal = self.get_report_data(data,partner)
            if check_bal==0:
                continue

            row_data={
                        'Dd':'x',
                        'Date':'',
                        'Number':'',
                        'Account':u'Харилцагч',
                        'Name':partner.name,
                        'Debit':0,
                        'Credit':0,
                        'C2':'',
                        'CAccount':'x',
                        'Branch':'x',
                        'Createuid':'x',
                        'Createdate':''
                        }
            all_datas.append(row_data)              
#                 print ('datas0000 ',datas)
            for d in datas:
                if False:#self.is_currency:#DAraa
                    for line in d[2]:
#                         
                        balance_currency = line['balance_currency']
                        balance = line['balance']
#                         number = int(line['number'])
#                         rowx += 1
                    totals[4] += balance_currency
                    totals[5] += balance
                else:
                    
                    row_data={
                                'Dd':'x',
                                'Date':'',
                                'Number':'',
                                'Account':d[3],
                                'Name':u'Эхний үлдэгдэл',
                                'Debit':0,
                                'Credit':0,
                                'C2':d[0],
                                'CAccount':'x',
                                'Branch':'x',
                                'Createuid':'x',
                                'Createdate':''
                                }
                    all_datas.append(row_data)
                    number = 0
                    balance = 0
                    balance_currency =0
                    d_dict={}
                    if self.is_date:
                        for line in d[2]:
                            if line['date'] in d_dict:
                            # if d_dict.has_key(line['date']):
                                d_dict[line['date']]['debit']+=line['debit']
                                d_dict[line['date']]['credit']+=line['credit']
                            else:
                                d_dict[line['date']]={'debit':line['debit'],
                                                      'credit':line['credit'],
                                                      'account':line['account'],
                                                      'balance':line['balance'],
                                                      }
                        od = collections.OrderedDict(sorted(d_dict.items()))
                        m=1
                        for i in od:
                            row_data={
                                        'Dd':m,
                                        'Date':i,
                                        'Number':'',
                                        'Account':od[i]['account'],
                                        'Name':'',
                                        'Debit':od[i]['debit'],
                                        'Credit':od[i]['credit'],
                                        'C2':'',
                                        'CAccount':'',
                                        'Branch':'x',
                                        'Createuid':'x',
                                        'Createdate':''
                                        }
                            all_datas.append(row_data)                            
                            m+=1
                    else:
                        for line in d[2]:
                            branch=line['branch']
#                             print ('line ',line)
                            row_data={
                                        'Dd':line['number'],
                                        'Date':line['date'],
                                        'Number':line['name'],
                                        'Account':line['account'],
                                        'Name':line['narration'],
                                        'Debit':line['debit'],
                                        'Credit':line['credit'],
                                        'C2':line['balance'],
                                        'CAccount':line['other'],
                                        'Branch':branch,
                                        'Createuid': line.get('create_uid',False) and line['create_uid'] or '',
                                        'Createdate':line.get('create_date',False) and line['create_date'] or ''
                                        }
                            all_datas.append(row_data)  
                            
                            totals[0] += line['debit_currency']
                            totals[1] += line['debit']
                            totals[2] += line['credit_currency']
                            totals[3] += line['credit']
                            balance_currency = line['balance_currency']
                            balance = line['balance']
                            number = int(line['number'])
                    totals[4] += balance_currency
                    totals[5] += balance             


                row_data={
                            'Dd':'',
                            'Date':'',
                            'Number':'',
                            'Account':'',
                            'Name':'',
                            'Debit':0,
                            'Credit':0,
                            'C2':0,
                            'CAccount':'',
                            'Branch':'',
                            'Createuid':'',
                            'Createdate':''
                            }
                all_datas.append(row_data) 
            row_data={
                        'Dd':'x',
                        'Date':'',
                        'Number':'',
                        'Account':'',
                        'Name':u'НИЙТ ДҮН',
                        'Debit':totals[1],
                        'Credit':totals[3],
                        'C2':totals[5],
                        'CAccount':'',
                        'Branch':'',
                        'Createuid':'',
                        'Createdate':''
                        }
            all_datas.append(row_data)
            total_amount[0] += totals[0]
            total_amount[1] += totals[1]
            total_amount[2] += totals[2]
            total_amount[3] += totals[3]
            total_amount[4] += totals[4]
            total_amount[5] += totals[5]
            if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
            else: total_amount[0] = -total_amount[0]
            if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
            else: total_amount[1] = -total_amount[1]
            if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
            else: total_amount[2] = -total_amount[2]
            if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
            else: total_amount[3] = -total_amount[3]
            if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
            else: total_amount[4] = -total_amount[4]
            if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
            else: total_amount[5] = -total_amount[5]
#             if total_amount[1]>0 or total_amount[3] or total_amount[5]:
#                 row_data={
#                         'Dd':'x',
#                         'Date':'',
#                         'Number':'',
#                         'Account':'',
#                         'Name':u'НИЙТ ДҮН БҮГД',
#                         'Debit':total_amount[1],
#                         'Credit':total_amount[3],
#                         'C2':total_amount[5],
#                         'CAccount':'',
#                         'Branch':''
#                         }
#                 all_datas.append(row_data)        
                    
        print ('all_datas ',all_datas)
        data_obj = self.env['ir.model.data']
        view = data_obj._xmlid_to_res_id('mw_account.view_mw_account_report_partner_detail_mn')
        report_id = self.env['mw.account.report'].with_context(data=all_datas).create({'name':'Харилцагчийн дэвтэр',
        #                                                                     'account_id':self.account_id.id,
                                                                    'date_from':self.date_from,
                                                                    'date_to':self.date_to
                                                                    })
        result_context.update({'data':all_datas})
#         model, action_id = ir_model_obj.get_object_reference('mw_account', 'action_mw_account_partner_detail_report')
#         [action] = self.env[model].browse(action_id).read()
#         #         print ('result_context ',result_context)
#         action['context'] = result_context
#         action['res_id'] = report_id.id
#         #         print ('action ',action)
#         return action                
        context = dict(self._context)
        context.update(result_context)
        return {
             'name': (u'Харилцагчийн дэвтэр'),
             'type': 'ir.actions.act_window',
             'view_type': 'form',
             'view_mode': 'form',
             'res_model': 'mw.account.report',
             'views': [(view, 'form')],
             'view_id': view,
             'target': 'inline',
             'res_id': report_id.id,
            'context': context,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
