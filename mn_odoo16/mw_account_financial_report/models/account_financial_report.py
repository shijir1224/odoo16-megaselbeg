# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
import json

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, ustr
from odoo.exceptions import ValidationError
from odoo.osv import expression

class account_financial_report_line(models.Model):
    _name = "account.financial.report.line"
    _description = "account financial report line"

    name = fields.Char(string='Reference',required=True)
    number = fields.Char(string='Number',required=True)
    seq = fields.Integer(string='Sequence',required=True)
    report_id = fields.Many2one('account.financial.html.report', string="Report")
#     account_id = fields.Many2one('account.account', string="Account")
    account_ids = fields.Many2many('account.account', 'account_account_financial_line_report', 'report_id', 'account_id', 'Accounts')
    is_bold = fields.Boolean(string='Is bold')
    is_number = fields.Boolean(string='Is number')

    is_line = fields.Boolean(string='Is line')
    is_formula = fields.Boolean(string='Is formula')
    line_ids = fields.Many2many('account.financial.report.line', 'accountline_financial_line_report', 'report_id', 'line_id', 'Lines')
    is_equity_date = fields.Boolean(string='ӨӨТ огноо')
    acc_code = fields.Char(string='Дансны код эхлэл')
    name_en = fields.Char(string='English name')
    account_type = fields.Selection([
        ('active', u'Актив'),
        ('passive', u'Пассив'),
        ], u'мөрийн төрөл', default='active')
    formula_txt = fields.Char(string='Formula')

class ReportAccountFinancialReport(models.Model):
    _name = "account.financial.html.report"
    _description = "Account Report (HTML)"

    filter_all_entries = False
    filter_hierarchy = False

    @property
    def filter_date(self):
        if self.date_range:
            return {'mode': 'range', 'filter': 'this_year'}
        else:
            return {'mode': 'single', 'filter': 'today'}

    @property
    def filter_comparison(self):
        if self.comparison:
            return {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
        return super().filter_comparison

    @property
    def filter_unfold_all(self):
        if self.unfold_all_filter:
            return False
        return super().filter_unfold_all

    @property
    def filter_journals(self):
        if self.show_journal_filter:
            return True
        return super().filter_journals

    @property
    def filter_analytic(self):
        enable_filter_analytic_accounts = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids
        enable_filter_analytic_tags = self.env.user.id in self.env.ref('analytic.group_analytic_tags').users.ids
        if self.analytic and not enable_filter_analytic_accounts and not enable_filter_analytic_tags:
            return None
        return self.analytic or None

    @property
    def filter_ir_filters(self):
        return self.applicable_filters_ids or None

    name = fields.Char(translate=True)
    date_range = fields.Boolean('Based on date ranges', default=True, help='specify if the report use date_range or single date')
    comparison = fields.Boolean('Allow comparison', default=True, help='display the comparison filter')
    analytic = fields.Boolean('Allow analytic filters', help='display the analytic filters')
    show_journal_filter = fields.Boolean('Allow filtering by journals', help='display the journal filter in the report')
    company_id = fields.Many2one('res.company', string='Company')
    tax_report = fields.Boolean('Tax Report', help="Set to True to automatically filter out journal items that are not tax exigible.")

    is_mw = fields.Boolean('Is MW?')
    account_line_ids = fields.One2many('account.financial.report.line','report_id', 'Account lines')
    active = fields.Boolean('Active',default=True)
    branch_id = fields.Many2one('res.branch')
    report_type = fields.Selection([
        ('other', u'Бусад'),
        ('balance', u'Баланс'),
        ('is', u'Орлогын тайлан'),
        ('equity', u'Өмчийн өөрчлөлт'),
        ], u'Тайлангийн төрөл', default='is')
    
    equity_account_ids = fields.Many2many('account.account', 'account_account_financial_equity_report', 'report_id', 'account_id', u'Өмчийн данс')
    hh_account_ids = fields.Many2many('account.account', 'account_account_financial_hh_report', 'report_id', 'account_id', u'ХХувьцаа данс')
    nt_account_ids = fields.Many2many('account.account', 'account_account_financial_nt_report', 'report_id', 'account_id', u'НТКапитал данс')
    du_account_ids = fields.Many2many('account.account', 'account_account_financial_du_report', 'report_id', 'account_id', u'Дахин үнэлгээ данс')
    gv_account_ids = fields.Many2many('account.account', 'account_account_financial_gv_report', 'report_id', 'account_id', u'Гадаад валют данс')
    other_account_ids = fields.Many2many('account.account', 'account_account_financial_other_report', 'report_id', 'account_id', u'Бусад хэсэг данс')
    ha_account_ids = fields.Many2many('account.account', 'account_account_financial_ha_report', 'report_id', 'account_id', u'Хуримтлагдсан ашиг данс')


    def set_accounts(self):
        for line in self.account_line_ids:
            account_ids=[]
            if line.acc_code:
                for acc_code in line.acc_code.split(','):
                    # print ('acc_code:: ',acc_code)
                    self._cr.execute("""SELECT id FROM account_account where code like '{0}%' """.format(acc_code))
                    results = self._cr.fetchall()
                    for i in results:
                        account_ids.append(i[0])
                    if account_ids:
                        line.account_ids=[(6,0 , account_ids)]
            

    def _build_contexts(self, data):
        result = {}
        if not data['date_from'] or not data['date_to']:
            raise UserError((u'Эхлэх дуусах огноо сонгоно уу.'))
        elif data['date_from'] > data['date_to']:
            raise UserError((u'Эхлэх огноо дуусах огнооноос бага байх ёстой.'))
#         form = self.read()[0]
        result['journal_ids'] = 'journal_ids' in data and data['journal_ids'] or False
        result['state'] = 'target_move' in data and data['target_move'] or ''
        result['date_from'] = data['date_from'] or False
        result['date_to'] = data['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
#         result['report_id'] = form['report_id'][0]
        result['company_id'] = data['company_id'][0]
        result['branch_ids'] = data['branch_ids']
        if data.get('analytic_account_ids',False):
            result['analytic_account_ids'] = data['analytic_account_ids']
        
#         data['form'].update(self.read(['chart_account_ids'])[0])
#         result.update(self.read(['check_balance_method'])[0])
#         result.update(self.read(['chart_account_ids'])[0])
 
        return result
    
    def create_report_data(self, data):
        ''' Мөрийн удгуудыг тайлангийн өгөгдөлөөр буцаана.
        '''
        initial_account_ids = []
        account_dict = {}
        account_ids = None
#         reports=self.env['report.mn.account.report_financial']
#         account_report = self.env['account.financial.report'].search([('id', '=', data['report_id'])])
        resu={}
        data=self._build_contexts(data)
        # print ('data ',data)
        for line in self.account_line_ids.sorted(key=lambda r: r.seq):
            type='debit'
            if not line.is_line:
                for account in line.account_ids:
                    # if account.user_type_id.balance_type=='passive':
                    if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):

                        type='credit'
                    else:
                        type='debit'
                    account_br=account.with_context(data)
                    if resu.get(line.id,False):
                        resu[line.id]['balance'] += account_br.balance
                        resu[line.id]['balance_start'] += account_br.balance_start
                        resu[line.id]['debit'] += account_br.debit
                        resu[line.id]['credit'] += account_br.credit
                    else:
                        resu[line.id] = {'balance':account_br.balance,
                                         'balance_start':account_br.balance_start,
                                         'debit':account_br.debit,
                                         'credit':account_br.credit,
                                         'name':line.name,
                                         'name_en':line.name_en,
                                         'number':line.number,
                                         'seq':line.seq,
                                         'is_bold':line.is_bold,
                                         'is_number':line.is_number,
                                         'type':type,
                                         'line':line
                                         }
            else:
                for l in line.line_ids:
                    if l.is_line:
                        for ll in l.line_ids:
                            if ll.is_line:
                                for lll in ll.line_ids:
                                    for account in lll.account_ids:                    
                                        account_br=account.with_context(data)
                                        # if account.user_type_id.balance_type=='passive':
                                        if account.account_type in ('liability_payable',\
                                                                    'liability_credit_card',\
                                                                    'liability_current','liability_non_current',\
                                                                    'equity','equity_unaffected','income','income_other'):
                                            type='credit'
                                        else:
                                            type='debit'
                                            
                                        if resu.get(line.id,False):
                                            resu[line.id]['balance'] += account_br.balance
                                            resu[line.id]['balance_start'] += account_br.balance_start
                                            resu[line.id]['debit'] += account_br.debit
                                            resu[line.id]['credit'] += account_br.credit
                                        else:
                                            resu[line.id] = {'balance':account_br.balance,
                                                             'balance_start':account_br.balance_start,
                                                             'debit':account_br.debit,
                                                             'credit':account_br.credit,
                                                             'name':line.name,
                                                             'name_en':line.name_en,
                                                             'number':line.number,
                                                             'seq':line.seq,
                                                             'is_bold':line.is_bold,
                                                             'is_number':line.is_number,
                                                             'type':type,
                                                             'line':line
                                                             }
                            else:   
                                for account in ll.account_ids:   
                                    # if account.user_type_id.balance_type=='passive':
                                    if account.account_type in ('liability_payable',\
                                                                'liability_credit_card',\
                                                                'liability_current','liability_non_current',\
                                                                'equity','equity_unaffected','income','income_other'):
                                    
                                        type='credit'
                                    else:
                                        type='debit'
                                    
                                    account_br=account.with_context(data)
                                    if resu.get(line.id,False):
                                        resu[line.id]['balance'] += account_br.balance
                                        resu[line.id]['balance_start'] += account_br.balance_start
                                        resu[line.id]['debit'] += account_br.debit
                                        resu[line.id]['credit'] += account_br.credit
                                    else:
                                        resu[line.id] = {'balance':account_br.balance,
                                                         'balance_start':account_br.balance_start,
                                                         'debit':account_br.debit,
                                                         'credit':account_br.credit,
                                                         'name':line.name,
                                                         'name_en':line.name_en,
                                                         'number':line.number,
                                                         'seq':line.seq,
                                                         'is_bold':line.is_bold,
                                                         'is_number':line.is_number,
                                                         'type':type,
                                                         'line':line
                                                         }
                    else:
                        for account in l.account_ids:
                            # if account.user_type_id.balance_type=='passive':
                            if account.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):
                            
                                type='credit'
                            else:
                                type='debit'
                            
                            account_br=account.with_context(data)
                            if resu.get(line.id,False):
                                resu[line.id]['balance'] += account_br.balance
                                resu[line.id]['balance_start'] += account_br.balance_start
                                resu[line.id]['debit'] += account_br.debit
                                resu[line.id]['credit'] += account_br.credit
                            else:
                                resu[line.id] = {'balance':account_br.balance,
                                                 'balance_start':account_br.balance_start,
                                                 'debit':account_br.debit,
                                                 'credit':account_br.credit,
                                                 'name':line.name,
                                                 'name_en':line.name_en,
                                                 'number':line.number,
                                                 'seq':line.seq,
                                                 'is_bold':line.is_bold,
                                                 'is_number':line.is_number,
                                                 'type':type,
                                                 'line':line
                                                 }
            if not resu.get(line.id,False):
                    resu[line.id] = {'balance':0,
                                     'balance_start':0,
                                     'debit':0,
                                     'credit':0,
                                     'name':line.name,
                                     'name_en':line.name_en,
                                     'number':line.number,
                                     'seq':line.seq,
                                     'is_bold':line.is_bold,
                                     'is_number':line.is_number,
                                     'type':type,
                                     'line':line
                                     }                             
#         print ('resu ',resu    )                   
        return resu
    

    def create_report_detail_data(self, data):
        ''' Мөрийн удгуудыг тайлангийн өгөгдөлөөр буцаана. Данстайгаар
        '''
        initial_account_ids = []
        account_dict = {}
        account_ids = None
#         reports=self.env['report.mn.account.report_financial']
#         account_report = self.env['account.financial.report'].search([('id', '=', data['report_id'])])
        resu={}
        data=self._build_contexts(data)
#         print ('data ',data)
        for line in self.account_line_ids.sorted(key=lambda r: r.seq):
            if not line.is_line:
                balance=0
                balance_start=0
                debit=0
                credit=0
                accout_dict={}
                
                for account in line.account_ids:
                    account_br=account.with_context(data)
                    balance+=account_br.balance
                    balance_start+=account_br.balance_start
                    debit+=account_br.debit
                    credit+=account_br.credit
                    accout_dict[account.id]= {'balance':account_br.balance,
                                         'balance_start':account_br.balance_start,
                                         'debit':account_br.debit,
                                         'credit':account_br.credit,
                                         'name':account.name,
                                         'name_en':line.name_en,
                                         'number':account.code,
                                         'seq':'',
                                         'is_bold':False,
                                         'is_number':False
                                         }   
                resu[line.id] = {'balance':balance,
                                         'balance_start':balance_start,
                                         'debit':debit,
                                         'credit':credit,
                                         'name':line.name,
                                         'name_en':line.name_en,
                                         'number':line.number,
                                         'seq':line.seq,
                                         'is_bold':line.is_bold,
                                         'is_number':line.is_number,
                                         'account_ids':accout_dict
                                         }
                                       
#                     account_br=account.with_context(data)
#                     if resu.get(line.id,False):
#                         resu[line.id]['balance'] += account_br.balance
#                         resu[line.id]['balance_start'] += account_br.balance_start
#                         resu[line.id]['debit'] += account_br.debit
#                         resu[line.id]['credit'] += account_br.credit
#                     else:
#                         resu[line.id] = {'balance':account_br.balance,
#                                          'balance_start':account_br.balance_start,
#                                          'debit':account_br.debit,
#                                          'credit':account_br.credit,
#                                          'name':line.name,
#                                          'number':line.number,
#                                          'seq':line.seq,
#                                          'is_bold':line.is_bold,
#                                          'is_number':line.is_number
#                                          }
            else:
                for l in line.line_ids:
                    if l.is_line:
                        for ll in l.line_ids:
                            if ll.is_line:
                                for lll in ll.line_ids:
                                    for account in lll.account_ids:                    
                                        account_br=account.with_context(data)
                                        if resu.get(line.id,False):
                                            resu[line.id]['balance'] += account_br.balance
                                            resu[line.id]['balance_start'] += account_br.balance_start
                                            resu[line.id]['debit'] += account_br.debit
                                            resu[line.id]['credit'] += account_br.credit
                                        else:
                                            resu[line.id] = {'balance':account_br.balance,
                                                             'balance_start':account_br.balance_start,
                                                             'debit':account_br.debit,
                                                             'credit':account_br.credit,
                                                             'name':line.name,
                                                             'name_en':line.name_en,
                                                             'number':line.number,
                                                             'seq':line.seq,
                                                             'is_bold':line.is_bold,
                                                             'is_number':line.is_number
                                                             }
                            else:   
                                for account in ll.account_ids:   
                                    account_br=account.with_context(data)
                                    if resu.get(line.id,False):
                                        resu[line.id]['balance'] += account_br.balance
                                        resu[line.id]['balance_start'] += account_br.balance_start
                                        resu[line.id]['debit'] += account_br.debit
                                        resu[line.id]['credit'] += account_br.credit
                                    else:
                                        resu[line.id] = {'balance':account_br.balance,
                                                         'balance_start':account_br.balance_start,
                                                         'debit':account_br.debit,
                                                         'credit':account_br.credit,
                                                         'name':line.name,
                                                         'name_en':line.name_en,
                                                         'number':line.number,
                                                         'seq':line.seq,
                                                         'is_bold':line.is_bold,
                                                         'is_number':line.is_number
                                                         }
                    else:
                        for account in l.account_ids:
                            account_br=account.with_context(data)
                            if resu.get(line.id,False):
                                resu[line.id]['balance'] += account_br.balance
                                resu[line.id]['balance_start'] += account_br.balance_start
                                resu[line.id]['debit'] += account_br.debit
                                resu[line.id]['credit'] += account_br.credit
                            else:
                                resu[line.id] = {'balance':account_br.balance,
                                                 'balance_start':account_br.balance_start,
                                                 'debit':account_br.debit,
                                                 'credit':account_br.credit,
                                                 'name':line.name,
                                                 'name_en':line.name_en,
                                                 'number':line.number,
                                                 'seq':line.seq,
                                                 'is_bold':line.is_bold,
                                                 'is_number':line.is_number
                                                 }
            if not resu.get(line.id,False):
                    resu[line.id] = {'balance':0,
                                     'balance_start':0,
                                     'debit':0,
                                     'credit':0,
                                     'name':line.name,
                                     'name_en':line.name_en,
                                     'number':line.number,
                                     'seq':line.seq,
                                     'is_bold':line.is_bold,
                                     'is_number':line.is_number
                                     }                             
#         print ('resu ',resu    )                   
        return resu
        

    def create_report_detail_data_old(self, data):
        ''' Мөрийн удгуудыг тайлангийн өгөгдөлөөр буцаана. Данстайгаар
        '''
        initial_account_ids = []
        account_dict = {}
        account_ids = None
#         reports=self.env['report.mn.account.report_financial']
#         account_report = self.env['account.financial.report'].search([('id', '=', data['report_id'])])
        resu={}
        
        data=self._build_contexts(data)
        for line in self.account_line_ids.sorted(key=lambda r: r.seq):
            if not line.is_line:
                balance=0
                balance_start=0
                debit=0
                credit=0
                accout_dict={}
                for account in line.account_ids:
                    account_br=account.with_context(data)
                    balance+=account_br.balance
                    balance_start+=account_br.balance_start
                    debit+=account_br.debit
                    credit+=account_br.credit
                    accout_dict[account.id]= {'balance':account_br.balance,
                                         'balance_start':account_br.balance_start,
                                         'debit':account_br.debit,
                                         'credit':account_br.credit,
                                         'name':account.name,
                                         'number':account.code,
                                         'name_en':line.name_en,
                                         'seq':'',
                                         'is_bold':False,
                                         'is_number':False
                                         }  
#                     accout_dict.append(tmp)            
#                     if resu.has_key(line.id):
#                         resu[line.id]['balance'] += account_br.balance
#                         resu[line.id]['balance_start'] += account_br.balance_start
#                         resu[line.id]['debit'] += account_br.debit
#                         resu[line.id]['credit'] += account_br.credit
#                     else:
#                         resu[line.id] = {'balance':account_br.balance,
#                                          'balance_start':account_br.balance_start,
#                                          'debit':account_br.debit,
#                                          'credit':account_br.credit,
#                                          'name':line.name,
#                                          'number':line.number,
#                                          'seq':line.seq,
#                                          'is_bold':line.is_bold,
#                                          'is_number':line.is_number
#                                          }
                resu[line.id] = {'balance':balance,
                                         'balance_start':balance_start,
                                         'debit':debit,
                                         'credit':credit,
                                         'name':line.name,
                                         'name_en':line.name_en,
                                         'number':line.number,
                                         'seq':line.seq,
                                         'is_bold':line.is_bold,
                                         'is_number':line.is_number,
                                         'account_ids':accout_dict
                                         }
            else:
                for l in line.line_ids:
                    if l.is_line:
                        for ll in l.line_ids:
                            if ll.is_line:
                                for lll in ll.line_ids:
                                    for account in lll.account_ids:                    
                                        account_br=account.with_context(data)
                                        if resu.get(line.id,False):
                                            resu[line.id]['balance'] += account_br.balance
                                            resu[line.id]['balance_start'] += account_br.balance_start
                                            resu[line.id]['debit'] += account_br.debit
                                            resu[line.id]['credit'] += account_br.credit
                                        else:
                                            resu[line.id] = {'balance':account_br.balance,
                                                             'balance_start':account_br.balance_start,
                                                             'debit':account_br.debit,
                                                             'credit':account_br.credit,
                                                             'name':line.name,
                                                             'name_en':line.name_en,
                                                             'number':line.number,
                                                             'seq':line.seq,
                                                             'is_bold':line.is_bold,
                                                             'is_number':line.is_number
                                                             }
                            else:   
                                for account in ll.account_ids:   
                                    account_br=account.with_context(data)
                                    if resu.get(line.id,False):
                                        resu[line.id]['balance'] += account_br.balance
                                        resu[line.id]['balance_start'] += account_br.balance_start
                                        resu[line.id]['debit'] += account_br.debit
                                        resu[line.id]['credit'] += account_br.credit
                                    else:
                                        resu[line.id] = {'balance':account_br.balance,
                                                         'balance_start':account_br.balance_start,
                                                         'debit':account_br.debit,
                                                         'credit':account_br.credit,
                                                         'name':line.name,
                                                         'name_en':line.name_en,
                                                         'number':line.number,
                                                         'seq':line.seq,
                                                         'is_bold':line.is_bold,
                                                         'is_number':line.is_number
                                                         }
                    else:
                        for account in l.account_ids:
                            account_br=account.with_context(data)
                            if resu.get(line.id,False):
                                
                                resu[line.id]['balance'] += account_br.balance
                                resu[line.id]['balance_start'] += account_br.balance_start
                                resu[line.id]['debit'] += account_br.debit
                                resu[line.id]['credit'] += account_br.credit
                            else:
                                resu[line.id] = {'balance':account_br.balance,
                                                 'balance_start':account_br.balance_start,
                                                 'debit':account_br.debit,
                                                 'credit':account_br.credit,
                                                 'name':line.name,
                                                 'name_en':line.name_en,
                                                 'number':line.number,
                                                 'seq':line.seq,
                                                 'is_bold':line.is_bold,
                                                 'is_number':line.is_number
                                                 }
            if resu.get(line.id,False):
                
                    resu[line.id] = {'balance':0,
                                     'balance_start':0,
                                     'debit':0,
                                     'credit':0,
                                     'name':line.name,
                                     'name_en':line.name_en,
                                     'number':line.number,
                                     'seq':line.seq,
                                     'is_bold':line.is_bold,
                                     'is_number':line.is_number
                                     }                             
        # print ('resu ',resu  )                     
        return resu    
        
    def get_amount(self,line,data):
#         data['strict_range']
        balance=0
        balance_start=0
        debit=0
        credit=0
        if not line.is_line:
            for account in line.account_ids:
                account_br=account.with_context(data)
                balance += account_br.balance
                balance_start += account_br.balance_start
                debit += account_br.debit
                credit += account_br.credit
        else:
            for l in line.line_ids:
                if l.is_line:
                    for ll in l.line_ids:
                        if ll.is_line:
                            for lll in ll.line_ids:
                                for account in lll.account_ids:        
#                                     print ('account ',account)            
                                    account_br=account.with_context(data)
#                                     print ('account_br.credit ',account_br.credit)
                                    balance += account_br.balance
                                    balance_start += account_br.balance_start
                                    debit += account_br.debit
                                    credit += account_br.credit

                        else:   
                            for account in ll.account_ids:   
                                account_br=account.with_context(data)
                                balance += account_br.balance
                                balance_start += account_br.balance_start
                                debit += account_br.debit
                                credit += account_br.credit

                else:
                    for account in l.account_ids:
                        account_br=account.with_context(data)
                        balance += account_br.balance
                        balance_start += account_br.balance_start
                        debit += account_br.debit
                        credit += account_br.credit
#        print ('2====== ',balance,balance_start,debit,credit)
        return         balance,balance_start,debit,credit


    def create_report_equity_data(self, data):
        ''' Мөрийн удгуудыг тайлангийн өгөгдөлөөр буцаана.
        '''
        initial_account_ids = []
        account_dict = {}
        account_ids = None
#         reports=self.env['report.mn.account.report_financial']
#         account_report = self.env['account.financial.report'].search([('id', '=', data['report_id'])])
        resu={}
        data=self._build_contexts(data)

        eq_start=0
        eq_end=0
        hh_start=0
        hh_end=0
        nt_start=0
        nt_end=0
        du_start=0
        du_end=0
        gv_start=0
        gv_end=0
        other_start=0
        other_end=0
        ashig_start=0
        ashig_end=0    
        ashig_debit=0
        ashig_credit=0
        for account in self.equity_account_ids:
            account_br=account.with_context(data)
            eq_start+=account_br.balance_start
            eq_end+=account_br.balance
        for account in self.hh_account_ids:
            account_br=account.with_context(data)
            hh_start+=account_br.balance_start
            hh_end+=account_br.balance                    
        for account in self.nt_account_ids:
            account_br=account.with_context(data)
            nt_start+=account_br.balance_start
            nt_end+=account_br.balance
        for account in self.du_account_ids:
            account_br=account.with_context(data)
            du_start+=account_br.balance_start
            du_end+=account_br.balance
        for account in self.gv_account_ids:
            account_br=account.with_context(data)
            gv_start+=account_br.balance_start
            gv_end+=account_br.balance
        for account in self.other_account_ids:
            account_br=account.with_context(data)
            other_start+=account_br.balance_start
            other_end+=account_br.balance        
#         unaffected_earnings_type = self.env.ref("account.data_unaffected_earnings")
#         print ('data ',data)
#         earning_accounts=self.env['account.account'].search([('user_type_id','=',unaffected_earnings_type.id),('company_id','=',data['company_id'])])
#         print ('a',earning_accounts)
#         if len(earning_accounts)!=1:
#             raise UserError((u'Энэ компани дээр хуримтлагдсан ашиг төрөлтэй данс байхгүй эсвэл олон байна. Эсвэл компаний мэдээллээ буруу сонгосон байна'))
#         earning_account=earning_accounts[0]
#         print ('earning_account ',earning_account)
        for account in self.ha_account_ids:
            account_br=account.with_context(data)
            ashig_start+=account_br.balance_start
            ashig_end+=account_br.balance        
#        print ('data==== ',data)
#         for line in self.account_line_ids.sorted(key=lambda r: r.seq):#Зөвхөн ашигийг оруулах.
        for line in self.account_line_ids.sorted(key=lambda r: r.seq):#Зөвхөн ашигийг оруулах.

#             if line.number in ('2','8'):
            aaa,bbb,ashig_debit,ashig_credit = self.get_amount(line,data)
        
#         account_br=earning_account.with_context(data)
        resu = {
                            'eq_start':eq_start,
                            'eq_end':eq_end,
                            'hh_start':hh_start,
                            'hh_end':hh_end,
                            'nt_start':nt_start,
                            'nt_end':nt_end,
                            'du_start':du_start,
                            'du_end':du_end,
                            'gv_start':gv_start,
                            'gv_end':gv_end,
                            'other_start':other_start,
                            'other_end':other_end,
                            'ashig_start':ashig_start,
                            'ashig_end':ashig_end,
                            'ashig_debit':ashig_debit,
                            'ashig_credit':ashig_credit,
#                                  'name':line.name,
#                                  'number':line.number,
#                                  'seq':line.seq,
#                                  'is_bold':line.is_bold,
#                                  'is_number':line.is_number
                                 }
#        print ('resu ',resu)                       
        return resu
    
        
    @api.model
    def create(self, vals):
        parent_id = vals.pop('parent_id', False)
        res = super(ReportAccountFinancialReport, self).create(vals)
        # res._create_action_and_menu(parent_id)
        return res

    def write(self, vals):
        parent_id = vals.pop('parent_id', False)
        res = super(ReportAccountFinancialReport, self).write(vals)
        # if parent_id:
        #     # this keeps external ids "alive" when upgrading the module
        #     for report in self:
        #         report._create_action_and_menu(parent_id)
        return res

    def unlink(self):
        for report in self:
            menu = report.generated_menu_id
            if menu:
                if menu.action:
                    menu.action.unlink()
                menu.unlink()
        return super(ReportAccountFinancialReport, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        '''Copy the whole financial report hierarchy by duplicating each line recursively.

        :param default: Default values.
        :return: The copied account.financial.html.report record.
        '''
        self.ensure_one()
        if default is None:
            default = {}
        default.update({'name': self._get_copied_name()})
        copied_report_id = super(ReportAccountFinancialReport, self).copy(default=default)
        for line in self.line_ids:
            line._copy_hierarchy(report_id=self, copied_report_id=copied_report_id)
        return copied_report_id
    

class AccountAccount(models.Model):
    _inherit = "account.account"

    is_recpay = fields.Boolean('On partner report?')
    report_line_ids = fields.Many2many('account.financial.report.line', 'account_account_financial_line_report', 'account_id', 'report_id', 'Тайлангийн үзүүлэлт')
         



class AccountMove(models.Model):
    _inherit = "account.move"

    def get_order_line_xl(self, ids):
        context=self._context
        print_payment=False
        if context.get('print_payment',False):
            print_payment=True
        datas = []
        report_ids = self.search([('id','in',ids)], order='date')
#         print ('report_ids ',report_ids)
        i = 1
        for report_id in report_ids:
            lines = report_id.line_ids
            sum1 = 0
            sum2 = 0
            sum3 = 0
    #         print 'lines ',lines
            for line in lines:
                temp = [
                (str(i)),
                str(report_id.date),
                (report_id.name), 
                (line.name), 
                (line.account_id.code),
                (line.account_id.name), 
                (line.debit),
                (line.credit),
#                 (line.debit), 
#                 (line.credit), 
#                 (line.name[:50]+' ..'),
                ]
                datas.append(temp)
                i += 1
        
        # datas.append(temp)
        res = {'data':datas}
        return res    