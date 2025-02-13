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

from datetime import timedelta
from lxml import etree

import base64

# from odoo.addons.test_website.tests.test_reset_views import break_view

try:
    # Python 2 support
    from base64 import encodebytes
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodebytes

import time
import datetime
from datetime import datetime

import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

import time
import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools.translate import _

import xlwt
from xlwt import *
# from odoo.addons.c2c_reporting_tools.c2c_helper import *
from operator import itemgetter

# from odoo.addons.mn_base import report_helper
# logger = netsvc.Logger()
logger = logging.getLogger('odoo')


class account_partner_ledger(models.TransientModel):
    """
        Өглөгийн дансны товчоо
    """

    _name = "account.partner.ledger2"
    _description = "Payable Account Ledger"

    CONDITION_SELECTION = [('all', 'All Partner'), ('non-balance', 'Non balanced'), ('balance', 'Balanced')]
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    #     account_id = fields.Many2one('account.account', 'Account', domain=[('type','in',['payable','receivable'])])
    #     account_id = fields.Many2one('account.account', 'Account', domain=['|',('user_type_id.type','in',['payable','receivable']),('is_recpay','=',True)])
    account_id = fields.Many2one('account.account', 'Account',
                                 domain=['|', ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                                         ('is_recpay', '=', True)])
    account_ids = fields.Many2many('account.account', 'account_partner_ledger_account_rel', 'report_id', 'account_id',
                                   'Accounts', domain=['|', ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                                                       ('is_recpay', '=', True)])

    #     fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal year', required=True),
    #     filter = fields.Selection([('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True),
    #     period_from = fields.Many2one('account.period', 'Start period'),
    #     period_to = fields.Many2one('account.period', 'End period'),
    date_from = fields.Date("Start Date", default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date", default=time.strftime('%Y-%m-%d'))
    target_move = fields.Selection([('all', 'All Entries'),
                                    ('posted', 'All Posted Entries')], 'Target Moves', required=True, default='posted')
    partner_id = fields.Many2one('res.partner', 'Partner', help="If empty, display all partners")
    condition = fields.Selection(CONDITION_SELECTION, 'Condition', required=True, default='all')
    type = fields.Selection([('all', 'All'), ('payable', 'Payable'),
                             ('receivable', 'Receivable')], 'Type', default='all')
    is_currency = fields.Boolean(u'Валюттай татах?')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    branch_id = fields.Many2one('res.branch', 'Branch')

    tag_id = fields.Many2one('res.partner.category', 'Category')
    brand_id = fields.Many2one('product.brand', 'Brand')

    is_vat_num = fields.Boolean(u'Регистр татах?', default=False)

    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()

    is_not_group = fields.Boolean(u'Харилцагчаар груплэхгүй?', default=False)
    is_with_balance = fields.Boolean(string='Үлдэгдэлтэй эсэх?', default=False)

    @api.onchange("receivable_accounts_only", "payable_accounts_only")
    def onchange_type_accounts_only(self):
        """Handle receivable/payable accounts only change."""
        if self.receivable_accounts_only or self.payable_accounts_only:
            domain = [("company_id", "=", self.company_id.id)]
            if self.receivable_accounts_only and self.payable_accounts_only:
                domain += [("internal_type", "in", ("receivable", "payable"))]
            elif self.receivable_accounts_only:
                domain += [("internal_type", "=", "receivable")]
            elif self.payable_accounts_only:
                domain += [("internal_type", "=", "payable")]
            self.account_ids = self.env["account.account"].search(domain)
        else:
            self.account_ids = None

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
        #         data['form'].update(self.read(['chart_account_ids'])[0])
        #         result.update(self.read(['check_balance_method'])[0])
        #         result.update(self.read(['chart_account_ids'])[0])

        return result

    def prepare_data(self, context=None):

        data = {}
        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
        #         data = self.pre_print_report(data)
        data['form']['company_id'] = form['company_id'][0]
        #         data['form']['account_ids'] = data['form']['chart_account_ids']
        #         data['form']['company_type'] = data['form']['company_type']
        #         data['form']['check_balance_method'] = form['check_balance_method']
        return data

    def print_report(self, context=None):
        if context is None:
            context = {}

        data = self.prepare_data()

        if context['report_type'] == 'payable':
            report_name = u'Өглөгийн дансны товчоо'
        elif context['report_type'] == 'receivable':
            report_name = u'Авлагын дансны товчоо'
        else:  # both
            report_name = u'Авлага, өглөгийн дансны товчоо '

        context.update({'report_type': 'payable'})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.partner.ledger2',
            'datas': data,
            'context': context,
            'nodestroy': True,
        }

    def _get_partner_where(self):
        partner_where = ""
        if self.partner_id:
            partner_ids = [self.partner_id.id]
            #             child_ids = self.env['res.partner'].search([('parent_id','=',self.partner_id.id)])
            #             if child_ids :
            #                 partner_ids = child_ids
            #             if self.partner_id.id not in partner_ids:
            #                 partner_ids += [self.partner_id.id]
            #             partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
            partner_where = " AND l.partner_id = {} ".format(self.partner_id.id)
        elif self.tag_id:
            partner_ids = self.env['res.partner'].search([('category_id', 'in', [self.tag_id.id])])
            #             print ('partner_ids ',partner_ids.ids)
            partner_where = " AND l.partner_id in (" + ','.join(map(str, partner_ids.ids)) + ") "
        elif self.warehouse_id:
            warehouse_id = [self.warehouse_id.id]
            partner_ids = self.env['res.partner'].search([('depend_warehouse_id', '=', warehouse_id)]).ids
            partner_where = " AND l.partner_id in (" + ','.join(map(str, partner_ids)) + ") "

        return partner_where

    def create_report_data(self, data):
        ''' Гүйлгээ баланс тайлангийн мэдээллийг боловсруулж
            тайлангийн форматад тохируулан python [{},{},{}...]
            загвараар хүснэгтийн мөр багануудын өгөгдлийг боловсруулна.

        '''
        cr = self._cr

        def characteristic_key(r):
            p = 'none'
            if r['partner_id']:
                p = str(r['partner_id'])
            a = 'none'
            if r['account_id']:
                a = str(r['account_id'])
            f = 'none'
            if r['ref']:
                f = r['ref']
            return (p + ':' + a + ':' + f)

        account_obj = self.env['account.account']
        partner_obj = self.pool.get('res.partner')
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        move_line_obj = self.pool.get('account.move.line')
        #         print ('data ',data)
        account_where = ""
        if data.get('account_id', False):
            account_where = " AND l.account_id = %s " % data['account_id'][0]

        if self.account_ids:
            if len(self.account_ids) == 1:
                account_where += " AND l.account_id = %s " % self.account_ids[0].id
            if len(self.account_ids) > 1:
                account_where = " AND l.account_id in (" + ','.join(map(str, self.account_ids.ids)) + ") "
        if self.branch_id:
            account_where += " AND l.branch_id = %s " % self.branch_id.id
        if self.brand_id:
            account_where += " AND l.brand_id = %s " % self.brand_id.id
        #                 account_where += " AND l.account_id in (%s) " % self.account_ids.ids

        #         if data['type'] in ['receivable','payable']:
        #             account_where += " AND ac.type = '%s' " % data['type']
        #         else:
        #             account_where += " AND ac.type in ('receivable','payable') "
        partner_where = self._get_partner_where()
        #
        #         if data.get('partner_id', False):
        #             partner_ids = [data['partner_id'][0]]
        #             child_ids = self.env['res.partner'].search([('parent_id','=',data['partner_id'][0])])
        #             if child_ids :
        #                 partner_ids = child_ids
        #             if data['partner_id'][0] not in partner_ids:
        #                 partner_ids += [data['partner_id'][0]]
        #             partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        #         elif self.tag_id:
        #             partner_ids = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])
        # #             print ('partner_ids ',partner_ids.ids)
        #             partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids.ids))+") "
        #
        #         elif data.get('warehouse_id', False):
        #             warehouse_id = [data['warehouse_id'][0]]
        #             partner_ids = self.env['res.partner'].search([('depend_warehouse_id','=',warehouse_id)]).ids
        #             partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        #

        company_where = ""
        #         if data.get('company_id', False):
        #             company_where = " AND l.company_id = %s " % data['company_id'][0]
        if self.company_id:
            company_where = " AND l.company_id = %s " % self.company_id.id

        #         print ('company_where ',company_where)
        #         initial_context, initial_bal_journal = self.get_initial_balance_context(cr, uid, data, context=context)
        #
        #         initial_query = move_line_obj._query_get(cr, uid, obj='l', context=initial_context)
        #         fiscalyear = fiscalyear_obj.browse(cr, uid, data['fiscalyear_id'][0])
        #         if initial_bal_journal :
        #             initial_query += " AND l.journal_id = %s " % initial_bal_journal
        #         elif data['date_from'] == fiscalyear.date_start:
        #             initial_query += " AND l.journal_id = -1 "

        # Эхний

        #         where=account_obj.get_initial_balance_partner([],data)
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        #         move_lines = dict(map(lambda x: (x, []), accounts.ids))
        #         print "data context ",data
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                                                  state=data['target_move'],
                                                                                  date_to=False, strict_range=True,
                                                                                  initial_bal=True)._query_get()
        init_wheres = [""]

        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
        filters = filters.replace('l__account_id', 'ac')
        print ('filters=======: ',filters)
        #         print 'where ',where
        initw = filters
        move_state = ['draft', 'posted']
        if data['target_move'] != 'all':
            move_state = ['posted']
        initial_query = ''
        #         fil=filters,tuple(init_where_params)
        #         print 'initial_query ',str(fil)
        report_types = '\'' + data['type'] + '\''
        if data['type'] == 'all':
            report_types = "'asset_receivable','liability_payable'"
            # ('account_type', 'in', ['asset_receivable', 'liability_payable']),
        # Тайлант хугацааны эхний үлдэгдлийг тооцоолно
        cr.execute(
            "SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,ac.account_type AS account_type, "
            "p.name as partner_name, l.brand_id as brand_id, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
            "CASE WHEN l.amount_currency > 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS debit_cur,"
            "CASE WHEN l.amount_currency < 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS credit_cur,"
            "CASE WHEN ac.account_type in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other') "
            "THEN sum(debit) - sum(credit) "
            "ELSE SUM(credit) - sum(debit) "
            "END AS ibalance, "
            "ac.account_type "
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
            "JOIN account_account ac ON (l.account_id = ac.id) "
            "JOIN account_move am ON (am.id = l.move_id) "
            "WHERE (ac.account_type IN (" + report_types + ") or ac.is_recpay='t') "
            " " + initial_query + " " + account_where + " " + partner_where + " " + company_where + " " + filters + " "
            "GROUP BY p.id, p.ref, p.name, l.brand_id, l.account_id,ac.name,ac.code,ac.account_type, l.currency_id,l.amount_currency "
            "ORDER BY ac.name ",
            tuple(init_where_params))
        #         cr.execute(sql, params)
        res = cr.dictfetchall()
        partner_data = {}
        #         print ('res1 ',res)

        for r in res:
            if r['ibalance'] != 0:
                key = characteristic_key(r)
                if key not in partner_data:
                    partner_data[key] = {
                        'partner_id': r['partner_id'],
                        'brand_id': r['brand_id'],
                        'currency_id': r['currency_id'],
                        'date': '',
                        'partner_ref': r['ref'] or '',
                        'name': r['partner_name'] or u'Харилцагчгүй',
                        'account_code': r['code'],
                        'account': '%s %s' % (r['code'], r['account_name']),
                        'account_name': r['account_name'],
                        'account_type': r['account_type'],
                        'initial_cur': 0,
                        'initial': 0,
                        'debit_cur': 0,
                        'debit': 0,
                        'credit_cur': 0,
                        'credit': 0,
                        'balance_cur': 0,
                        'balance': 0,
                        'created': '',
                    }

                # if r['account_type'] in 'passive':
                if    r['account_type'] in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):
                    partner_data[key]['initial'] += (r['credit'] or 0) - (r['debit'] or 0)
                    partner_data[key]['initial_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
                else:
                    partner_data[key]['initial'] += (r['debit'] or 0) - (r['credit'] or 0)
                    partner_data[key]['initial_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)

        for key, value in partner_data.items():
            partner_data[key]['balance_cur'] = partner_data[key]['initial_cur']
            partner_data[key]['balance'] = partner_data[key]['initial']

        # -------------------------------------------------------------------------------
        #         Тайлант хугацааны гүйлгээг тооцоолж эцсийн үлдэгдлийг тодорхойлно
        #         current_context = context.copy()
        #         current_context.update({
        #             'fiscalyear': data['fiscalyear_id'][0],
        #             'date_from': data['date_from'],
        #             'date_to': data['date_to']
        #         })
        #         query = move_line_obj._query_get(cr, uid, obj='l', context=current_context)
        #         if initial_bal_journal:
        #             query += " AND l.journal_id <> %s " % initial_bal_journal

        #         cr = self.env.cr
        MoveLine = self.env['account.move.line']
        #         print 'data.get(,{}) ',data.get('used_context',{})
        #         init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
        #                                                         state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        tables, where_clause, where_params = MoveLine.with_context(date_from=data['date_from'],
                                                                   state=data['target_move'], date_to=data['date_to'],
                                                                   strict_range=True, )._query_get()
        query = ''
        wheres = [""]
        #         print 'where_params============================ ',where_params
        #         print 'where_clause---------------------------- ',where_clause
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')

        #         fil=filters,tuple(init_where_params)
        #         print 'initial_query ',str(fil)
        report_types = '\'' + data['type'] + '\''
        if data['type'] == 'all':
            report_types = "'asset_receivable','liability_payable'"
        cr.execute(
            "SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,ac.account_type AS account_type, "
            "p.name as partner_name, l.brand_id as brand_id, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
            "CASE WHEN l.amount_currency > 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS debit_cur,"
            "CASE WHEN l.amount_currency < 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS credit_cur,"
            "ac.account_type, "
            "array_agg((select login from res_users where id=am.create_uid)) as users "
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
            "JOIN account_account ac ON (l.account_id = ac.id) "
            "JOIN account_move am ON (am.id = l.move_id) "
            "WHERE (ac.account_type IN (" + report_types + ") or ac.is_recpay='t') "
            " " + query + " " + account_where + " " + partner_where + " " + company_where + " " + filters + " "
            "GROUP BY p.id, p.ref, p.name, l.brand_id, l.account_id,ac.name,ac.code,ac.account_type, l.currency_id, l.amount_currency "
            "ORDER BY ac.name ",
            tuple(where_params))
        # "ORDER BY p.name,l.account_id ")

        res = cr.dictfetchall()
        # print ('res ',res)
        for r in res:
            if r['debit'] > 0 or r['credit'] > 0:
                key = characteristic_key(r)
                if key not in partner_data:
                    partner_data[key] = {
                        'partner_id': r['partner_id'],
                        'brand_id': r['brand_id'],
                        'currency_id': r['currency_id'],
                        'date': '',
                        'partner_ref': r['ref'] or '',
                        'name': r['partner_name'] or u'Харилцагчгүй',
                        'account': '%s %s' % (r['code'], r['account_name']),
                        'account_code': r['code'],
                        'account_name': r['account_name'],
                        'account_type': r['account_type'],
                        'initial_cur': 0,
                        'initial': 0,
                        'debit_cur': 0,
                        'debit': 0,
                        'credit_cur': 0,
                        'credit': 0,
                        'balance': 0,
                        'balance_cur': 0,
                        'created': r['users'],
                    }
                partner_data[key]['debit_cur'] += (r['debit_cur'] or 0)
                partner_data[key]['debit'] += (r['debit'] or 0)
                partner_data[key]['credit_cur'] += (abs(r['credit_cur']) or 0)
                partner_data[key]['credit'] += (abs(r['credit']) or 0)
                # if r['balance_type'] == 'passive':
                if  r['account_type'] in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):
                
                    partner_data[key]['balance'] += (r['credit'] or 0) - (r['debit'] or 0)
                    partner_data[key]['balance_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
                else:
                    partner_data[key]['balance'] += (r['debit'] or 0) - (r['credit'] or 0)
                    partner_data[key]['balance_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
        #         print 'partner_data: ', partner_data
        if not data.get('partner_id', False) and data['condition'] != 'all':
            if data['condition'] == 'non-balance':
                for key in partner_data.keys():
                    if abs(partner_data[key]['balance']) >= 1:
                        del partner_data[key]
            else:
                for key in partner_data.keys():
                    if abs(partner_data[key]['balance']) < 1:
                        del partner_data[key]
        #
        # return sorted(partner_data.values(), key=itemgetter('name'))
        return sorted(partner_data.values(), key=itemgetter('account_type'))

    def create_report_data_account(self, data):
        ''' Гүйлгээ баланс тайлангийн мэдээллийг боловсруулж
            тайлангийн форматад тохируулан python [{},{},{}...]
            загвараар хүснэгтийн мөр багануудын өгөгдлийг боловсруулна.

        '''
        cr = self._cr

        def characteristic_key(r):
            #             print 'rrrrr ',r
            p = 'none'
            if r['partner_id']:
                p = str(r['partner_id'])
            a = 'none'
            if r['account_id']:
                a = str(r['account_id'])
            f = 'none'
            if r['ref']:
                f = r['ref']
            return (p + ':' + a + ':' + f)

        account_obj = self.env['account.account']
        partner_obj = self.pool.get('res.partner')
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        move_line_obj = self.pool.get('account.move.line')

        account_where = ""
        if data.get('account_id', False):
            account_where = " AND l.account_id = %s " % data['account_id'][0]

        if self.branch_id:
            account_where += " AND l.branch_id = %s " % self.branch_id.id

        if self.brand_id:
            account_where += " AND l.brand_id = %s " % self.brand_id.id

        partner_where = self._get_partner_where()
        #         if data.get('partner_id', False):
        #             partner_ids = [data['partner_id'][0]]
        # #             child_ids = self.env['res.partner'].search([('parent_id','=',data['partner_id'][0])])
        # #             if child_ids :
        # #                 partner_ids = child_ids
        #             if data['partner_id'][0] not in partner_ids:
        #                 partner_ids += [data['partner_id'][0]]
        #             partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        #         elif data.get('warehouse_id', False):
        #             warehouse_id = [data['warehouse_id'][0]]
        #             partner_ids = self.env['res.partner'].search([('depend_warehouse_id','=',warehouse_id)]).ids
        #             partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "

        company_where = ""
        #         if data.get('company_id', False):
        #             company_where = " AND l.company_id = %s " % data['company_id'][0]
        if self.company_id:
            company_where = " AND l.company_id = %s " % self.company_id.id

        # Эхний

        #         where=account_obj.get_initial_balance_partner([],data)
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        #         move_lines = dict(map(lambda x: (x, []), accounts.ids))
        #         print "data context ",data
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                                                  state=data['target_move'],
                                                                                  date_to=False, strict_range=True,
                                                                                  initial_bal=True)._query_get()
        init_wheres = [""]

        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
        filters = filters.replace('l__account_id', 'ac')
        #         print 'where ',where
        initw = filters
        move_state = ['draft', 'posted']
        if data['target_move'] != 'all':
            move_state = ['posted']
        initial_query = ''
        #         fil=filters,tuple(init_where_params)
        #         print 'initial_query ',str(fil)
        report_types = '\'' + data['type'] + '\''
        if data['type'] == 'all':
            report_types = "'asset_receivable','liability_payable'"
        # Тайлант хугацааны эхний үлдэгдлийг тооцоолно
        cr.execute(
            "SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,ac.account_type AS account_type, "
            "p.name as partner_name, l.brand_id as brand_id, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
            "CASE WHEN l.amount_currency > 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS debit_cur,"
            "CASE WHEN l.amount_currency < 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS credit_cur,"
            "CASE WHEN ac.account_type in ('liability_payable',\
                                'liability_credit_card',\
                                'liability_current','liability_non_current',\
                                'equity','equity_unaffected','income','income_other') "
            "THEN sum(debit) - sum(credit) "
            "ELSE SUM(credit) - sum(debit) "
            "END AS ibalance, "
            "ac.account_type, "
            "(select category_id from res_partner_res_partner_category_rel where partner_id=p.id limit 1) as category_id "
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
            "JOIN account_account ac ON (l.account_id = ac.id) "
            "JOIN account_move am ON (am.id = l.move_id) "
            "WHERE (ac.account_type IN (" + report_types + ") or ac.is_recpay='t') "
            " " + initial_query + " " + account_where + " " + partner_where + " " + company_where + " " + filters + " "
            "GROUP BY p.id, p.ref, p.name, l.brand_id, l.account_id,ac.name,ac.code,ac.account_type, l.currency_id,l.amount_currency "
            "ORDER BY ac.name ",
            tuple(init_where_params))
        #         cr.execute(sql, params)
        res = cr.dictfetchall()
        #         print 'res ',res
        partner_data = {}
        for r in res:
            if r['ibalance'] != 0:
                key = characteristic_key(r)
                if key not in partner_data:
                    partner_data[key] = {
                        'partner_id': r['partner_id'],
                        'brand_id': r['brand_id'],
                        'currency_id': r['currency_id'],
                        'date': '',
                        'partner_ref': r['ref'] or '',
                        'name': r['partner_name'] or u'Харилцагчгүй',
                        'account_code': r['code'],
                        'account': '%s %s' % (r['code'], r['account_name']),
                        'account_name': r['account_name'],
                        'account_type': r['account_type'],
                        'initial_cur': 0,
                        'initial': 0,
                        'debit_cur': 0,
                        'debit': 0,
                        'credit_cur': 0,
                        'credit': 0,
                        'balance_cur': 0,
                        'balance': 0,
                        'category_id': r['category_id'],
                        'created': '',
                    }
                # if r['balance_type'] == 'passive':
                if    r['account_type'] in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):
                
                    partner_data[key]['initial'] += (r['credit'] or 0) - (r['debit'] or 0)
                    partner_data[key]['initial_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
                else:
                    partner_data[key]['initial'] += (r['debit'] or 0) - (r['credit'] or 0)
                    partner_data[key]['initial_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)

        for key, value in partner_data.items():
            partner_data[key]['balance_cur'] = partner_data[key]['initial_cur']
            partner_data[key]['balance'] = partner_data[key]['initial']

        # -------------------------------------------------------------------------------
        MoveLine = self.env['account.move.line']
        #         init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
        #                                                         state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        tables, where_clause, where_params = MoveLine.with_context(date_from=data['date_from'],
                                                                   state=data['target_move'], date_to=data['date_to'],
                                                                   strict_range=True, )._query_get()
        query = ''
        wheres = [""]
        #         print 'where_params============================ ',where_params
        #         print 'where_clause---------------------------- ',where_clause
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')

        #         fil=filters,tuple(init_where_params)
        #         print 'initial_query ',str(fil)
        report_types = '\'' + data['type'] + '\''
        if data['type'] == 'all':
            report_types = "'asset_receivable','liability_payable'"
        cr.execute(
            "SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,ac.account_type AS account_type, "
            "p.name as partner_name, l.brand_id as brand_id, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
            "CASE WHEN l.amount_currency > 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS debit_cur,"
            "CASE WHEN l.amount_currency < 0 "
            "THEN sum(l.amount_currency) "
            "ELSE 0 "
            "END AS credit_cur,"
            "ac.account_type, "
            "(select category_id from res_partner_res_partner_category_rel where partner_id=p.id limit 1) as category_id, "
            "array_agg((select login from res_users where id=am.create_uid)) as users "
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
            "JOIN account_account ac ON (l.account_id = ac.id) "
            "JOIN account_move am ON (am.id = l.move_id) "
            "WHERE (ac.account_type IN (" + report_types + ") or ac.is_recpay='t') "
            " " + query + " " + account_where + " " + partner_where + " " + company_where + " " + filters + " "
            "GROUP BY p.id, p.ref, p.name, l.brand_id, l.account_id,ac.name,ac.code,ac.account_type, l.currency_id, l.amount_currency "
            "ORDER BY ac.name ",
            tuple(where_params))
        # "ORDER BY p.name,l.account_id ")

        res = cr.dictfetchall()
        #         print 'res ',res
        for r in res:
            if r['debit'] > 0 or r['credit'] > 0:
                key = characteristic_key(r)
                if key not in partner_data:
                    partner_data[key] = {
                        'partner_id': r['partner_id'],
                        'brand_id': r['brand_id'],
                        'currency_id': r['currency_id'],
                        'date': '',
                        'partner_ref': r['ref'] or '',
                        'name': r['partner_name'] or u'Харилцагчгүй',
                        'account': '%s %s' % (r['code'], r['account_name']),
                        'account_code': r['code'],
                        'account_name': r['account_name'],
                        'account_type': r['account_type'],
                        'initial_cur': 0,
                        'initial': 0,
                        'debit_cur': 0,
                        'debit': 0,
                        'credit_cur': 0,
                        'credit': 0,
                        'balance': 0,
                        'balance_cur': 0,
                        'category_id': r['category_id'],
                        'created': r['users']
                    }
                partner_data[key]['debit_cur'] += (r['debit_cur'] or 0)
                partner_data[key]['debit'] += (r['debit'] or 0)
                partner_data[key]['credit_cur'] += (abs(r['credit_cur']) or 0)
                partner_data[key]['credit'] += (abs(r['credit']) or 0)
                # if r['balance_type'] == 'passive':
                if    r['account_type'] in ('liability_payable',\
                                            'liability_credit_card',\
                                            'liability_current','liability_non_current',\
                                            'equity','equity_unaffected','income','income_other'):
                    partner_data[key]['balance'] += (r['credit'] or 0) - (r['debit'] or 0)
                    partner_data[key]['balance_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
                else:
                    partner_data[key]['balance'] += (r['debit'] or 0) - (r['credit'] or 0)
                    partner_data[key]['balance_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
        #         print 'partner_data: ', partner_data
        if not data.get('partner_id', False) and data['condition'] != 'all':
            if data['condition'] == 'non-balance':
                for key in partner_data.keys():
                    if abs(partner_data[key]['balance']) >= 1:
                        del partner_data[key]
            else:
                for key in partner_data.keys():
                    if abs(partner_data[key]['balance']) < 1:
                        del partner_data[key]
        #
        # return sorted(partner_data.values(), key=itemgetter('name'))
        return sorted(partner_data.values(), key=itemgetter('account_type'))


    def _build_contexts(self, data):
        result = {}
        # result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] or False
        return result

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
        #        print "guilgee balancee   23165465464654654654",data
        form = self.read()[0]
        data['form'] = form
        data['form'].update(self._build_contexts(data))
        #         data = self.pre_print_report(data)
        #         if  form['is_excel']:
        return self._make_excel(data)

    def data_calc(self, data, data_wz, lines, sums):
        if data_wz.get('account_id', False):
            for line in lines:
                if line['account_type'] == 'payable':
                    balance = -line['balance']
                else:
                    balance = line['balance']

                if line['category_id'] not in data.keys():
                    data[line['category_id']] = [{'partner_ref': line['partner_ref'],
                                                  'brand_id': line['brand_id'],
                                                  'name': line['name'],
                                                  'account_type': line['account_type'],
                                                  #                                                                     'currency_id' : currency,
                                                  'initial_cur': line['initial_cur'],
                                                  'initial': line['initial'],
                                                  'debit_cur': line['debit_cur'],
                                                  'debit': line['debit'],
                                                  'credit_cur': line['credit_cur'],
                                                  'credit': line['credit'],
                                                  'balance_cur': line['balance_cur'],
                                                  'balance': balance,
                                                  #                                                            'account' : line['account'],
                                                  'account_code': line['account_code'],
                                                  'account_name': line['account_name'],
                                                  'partner_id': line['partner_id'],
                                                  'created': line['created'],
                                                  }]
                    sums[line['category_id']] = {'sum_initial_cur': line['initial_cur'],
                                                 'sum_initial': line['initial'],
                                                 'sum_debit_cur': line['debit_cur'],
                                                 'sum_debit': line['debit'],
                                                 'sum_credit_cur': line['credit_cur'],
                                                 'sum_credit': line['credit'],
                                                 'sum_balance_cur': line['balance_cur'],
                                                 'sum_balance': balance
                                                 }
                else:
                    data[line['category_id']].append({'partner_ref': line['partner_ref'],
                                                      'brand_id': line['brand_id'],
                                                      'name': line['name'],
                                                      'account_type': line['account_type'],
                                                      #                                                                     'currency_id' : currency,
                                                      'initial_cur': line['initial_cur'],
                                                      'initial': line['initial'],
                                                      'debit_cur': line['debit_cur'],
                                                      'debit': line['debit'],
                                                      'credit_cur': line['credit_cur'],
                                                      'credit': line['credit'],
                                                      'balance_cur': line['balance_cur'],
                                                      'balance': balance,
                                                      #                                                            'account' : line['account'],
                                                      'account_code': line['account_code'],
                                                      'account_name': line['account_name'],
                                                      'partner_id': line['partner_id'],
                                                      'created': line['created'],
                                                      })

        else:
            for line in lines:
                if line['account_type'] == 'payable':
                    balance = -line['balance']
                else:
                    balance = line['balance']
                #                     print ('line ',line)
                if line['partner_id'] not in data.keys():
                    data[line['partner_id']] = [{'partner_ref': line['partner_ref'],
                                                 'brand_id': line['brand_id'],
                                                 'name': line['name'],
                                                 'account_type': line['account_type'],
                                                 'currency_id': line['currency_id'],
                                                 'initial_cur': line['initial_cur'],
                                                 'initial': line['initial'],
                                                 'debit_cur': line['debit_cur'],
                                                 'debit': line['debit'],
                                                 'credit_cur': line['credit_cur'],
                                                 'credit': line['credit'],
                                                 'balance_cur': line['balance_cur'],
                                                 'balance': balance,
                                                 #                                                            'account' : line['account'],
                                                 'account_code': line['account_code'],
                                                 'account_name': line['account_name'],
                                                 'created': line['created'],
                                                 }]
                    sums[line['partner_id']] = {'sum_initial_cur': line['initial_cur'],
                                                'sum_initial': line['initial'],
                                                'sum_debit_cur': line['debit_cur'],
                                                'sum_debit': line['debit'],
                                                'sum_credit_cur': line['credit_cur'],
                                                'sum_credit': line['credit'],
                                                'sum_balance_cur': line['balance_cur'],
                                                'sum_balance': balance
                                                }
                else:
                    data[line['partner_id']].append({'partner_ref': line['partner_ref'],
                                                     'brand_id': line['brand_id'],
                                                     'name': line['name'],
                                                     'account_type': line['account_type'],
                                                     'currency_id': line['currency_id'],
                                                     'initial_cur': line['initial_cur'],
                                                     'initial': line['initial'],
                                                     'debit_cur': line['debit_cur'],
                                                     'debit': line['debit'],
                                                     'credit_cur': line['credit_cur'],
                                                     'credit': line['credit'],
                                                     'balance_cur': line['balance_cur'],
                                                     'balance': balance,
                                                     #                                                            'account' : line['account'],
                                                     'account_code': line['account_code'],
                                                     'account_name': line['account_name'],
                                                     'created': line['created'],
                                                     })

        return data, sums

    def _get_vat(self, partner):
        return self.is_vat_num and partner.vat or partner.ref

    def _make_excel(self, data):
        #         data = self.prepare_data(cr, uid, ids, context=context)
        #         user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.company_id

        #         pretty = c2c_helper.comma_me # Тоог мянгатын нарийвчлалтай болгодог method
        styledict = self.env['abstract.report.excel'].get_easyxf_styles()

        ezxf = xlwt.easyxf
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet(u'Payable Receivable Ledger', cell_overwrite_ok=True)
        sheet_act = book.add_sheet(u'Төлбөр тогтоосон акт')
        sheet.portrait = False
        data_wz = data['form']
        date_str = '%s-%s' % (
            #             datetime.datetime.strptime(data_wz['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
            #             datetime.datetime.strptime(data_wz['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
            data['form']['date_from'],
            data['form']['date_to']
        )
        title = u'Маягт АӨ-1'
        report_name = u'Харилцагчийн товчоо '

        sheet.write(0, 6, title, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
        sheet.write(0, 0, u'Байгууллагын нэр: %s' % company.name,
                    xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet.write(2, 2, report_name, xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))

        sheet_act.write_merge(2, 2, 2, 5, u'ЭД ХАРИУЦАГЧИЙН ТӨЛБӨР ТОГТООСОН АКТ',
                              xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))
        #         sheet_act.write(5, 0, u'"Жүр үр" ХХК-ийн '+unicode(self.warehouse_id.code)+u' агуулахын эд хариуцагчид өдрөөс өдрийг хүртэлх хугацаанд хариуцаж байсан бараа материалын', xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet_act.write(6, 0,
                        u"      тооцоог нягтлан бодох бүртгэлийн анхан шатны баримтуудаар нэг бүрчлэн шалгаж үзэхэд %s" % u'(' + '            ' + u') төгрөгний',
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet_act.write(7, 3, u"%s" % u'зөрүүтэй гарсан болно.',
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        # sheet_act.write(9, 2, u'Тооцооны дэлгэрэнгүй хүснэгт', xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))
        sheet_act.write(3, 7, u'%s' % (time.strftime('%Y-%m-%d'),),
                        ezxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 160'))
        sheet_act.write(10, 1, u'Код', styledict['heading_xf'])
        sheet_act.write(10, 2, u'Нэрс', styledict['heading_xf'])
        sheet_act.write_merge(10, 10, 3, 4, u'Тооцоо хийсэн өдрүүд', styledict['heading_xf'])
        sheet_act.write_merge(11, 17, 3, 4, u'', styledict['text_xf'])
        sheet_act.write(10, 5, u'Дүн', styledict['heading_xf'])
        sheet_act.write(10, 6, u'Гарын үсэг', styledict['heading_xf'])
        sheet_act.write(17, 1, u'Дүн', styledict['text_xf'])
        sheet_act.write(11, 1, u'', styledict['text_xf'])
        sheet_act.write(11, 2, u'', styledict['text_xf'])
        sheet_act.write(11, 5, u'', styledict['text_xf'])
        sheet_act.write(11, 6, u'', styledict['text_xf'])
        sheet_act.write(12, 1, u'', styledict['text_xf'])
        sheet_act.write(12, 2, u'', styledict['text_xf'])
        sheet_act.write(12, 5, u'', styledict['text_xf'])
        sheet_act.write(12, 6, u'', styledict['text_xf'])
        sheet_act.write(13, 1, u'', styledict['text_xf'])
        sheet_act.write(13, 2, u'', styledict['text_xf'])
        sheet_act.write(13, 5, u'', styledict['text_xf'])
        sheet_act.write(13, 6, u'', styledict['text_xf'])
        sheet_act.write(14, 1, u'', styledict['text_xf'])
        sheet_act.write(14, 2, u'', styledict['text_xf'])
        sheet_act.write(14, 5, u'', styledict['text_xf'])
        sheet_act.write(14, 6, u'', styledict['text_xf'])
        sheet_act.write(15, 1, u'', styledict['text_xf'])
        sheet_act.write(15, 2, u'', styledict['text_xf'])
        sheet_act.write(15, 5, u'', styledict['text_xf'])
        sheet_act.write(15, 6, u'', styledict['text_xf'])
        sheet_act.write(16, 1, u'', styledict['text_xf'])
        sheet_act.write(16, 2, u'', styledict['text_xf'])
        sheet_act.write(16, 5, u'', styledict['text_xf'])
        sheet_act.write(16, 6, u'', styledict['text_xf'])
        sheet_act.write(17, 2, u'', styledict['text_xf'])
        sheet_act.write(17, 5, u'', styledict['text_xf'])
        sheet_act.write(17, 6, u'', styledict['text_xf'])
        sheet_act.write(20, 2,
                        u'Тайлан гаргасан: Нягтлан бодогч ............................... /                          /',
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet_act.write(22, 2,
                        u'Танилцсан: Салбарын менежер ............................... /                          /',
                        xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))

        if data_wz.get('account_id', False):
            a = self.env['account.account'].browse(data_wz['account_id'][0])
            sheet.write(3, 0, u'Дансны дугаар: %s' % a.code,
                        xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
            sheet.write(3, 6, u'Дансны нэр: %s' % a.name,
                        xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))

        sheet.write(5, 7, u'Тайлант хугацаа: %s' % date_str,
                    xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
        if data_wz.get('partner_id', False):
            partner = self.env['res.partner'].browse(data_wz['partner_id'][0])
            sheet.write(4, 0, u"Харилцагчийн код: %s" % (partner.ref or ''),
                        xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
            sheet.write(4, 6, u"Харилцагчийн нэр: %s" % partner.name,
                        xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))

        rowx = 7
        if data_wz.get('account_id', False):
            lines = self.create_report_data_account(data['form'])
        else:
            lines = self.create_report_data(data['form'])
        if not data_wz['is_currency']:
            if not self.is_not_group:
                sheet.write_merge(rowx, rowx + 2, 0, 0, u'', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 1, 1, u'Код', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 2, 2, u'Нэр', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 3, 3, u'Эхний үлдэгдэл', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 4, 4, u'Дебет', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 5, 5, u'Кредит', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 6, 6, u'Эцсийн үлдэгдэл', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 7, 7, u'Үүсгэсэн', styledict['heading_xf'])
                sheet.panes_frozen = True
                sheet.horz_split_pos = 10  # freeze the first row
                rowx += 3
            else:
                sheet.write_merge(rowx, rowx + 2, 0, 0, u'', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 1, 1, u'Харилцагч Код', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 2, 2, u'Харилцагч Нэр', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 3, 3, u'Данс Код', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 4, 4, u'Данс Нэр', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 5, 5, u'Эхний үлдэгдэл', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 6, 6, u'Дебет', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 7, 7, u'Кредит', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 8, 8, u'Эцсийн үлдэгдэл', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx + 2, 9, 9, u'Үүсгэсэн', styledict['heading_xf'])
                sheet.panes_frozen = True
                sheet.horz_split_pos = 10  # freeze the first row
                rowx += 3

            #             lines = report_service.get_report_data(cr, uid, data, context=context)
            data = {}
            sums = {}
            cur_data = {}
            data, sums = self.data_calc(data, data_wz, lines, sums)

            number = 1

            totals = [0, 0, 0, 0, 0, 0, 0, 0]

            a = {}
            #             print ('data1111 ',data)
            #             for key in sorted(data.keys()):
            #                  a[key] = data[key]
            #             print ('data1:::: ',data)
            if data_wz.get('account_id', False):
                for k in data.keys():
                    if data_wz.get('account_id', False):
                        partner_cat = self.env['res.partner.category'].browse(k)
                        if partner_cat:
                            sheet.write(rowx, 0, u'Ангилал:', styledict['text_bold_xf_no_wrap'])
                            sheet.write(rowx, 1, partner_cat.name, styledict['text_bold_xf_no_wrap'])
                        else:
                            sheet.write(rowx, 0, u'Ангилал:', styledict['text_bold_xf_no_wrap'])
                            sheet.write(rowx, 1, u'Ангилалгүй', styledict['text_bold_xf_no_wrap'])
                        #                     sheet.write(rowx, 2, partner.name, styledict['text_bold_xf_no_wrap'])
                        rowx += 1
                        #                     print "k",k
                        #                     print "data[k] ",data[k]
                        totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                        sort_data = []
                        for l in data[k]:
                            partner = self.env['res.partner'].browse(l['partner_id'])
                            if partner.name:
                                l['partner_name'] = partner.name
                            else:
                                l['partner_name'] = 'null'
                            sort_data.append(l)
                        #                     for line in data[k]:
                        result = sorted(sort_data, key=itemgetter('partner_name'))
                        for line in result:
                            if self.is_with_balance and line['balance'] == 0:
                                continue
                            partner = self.env['res.partner'].browse(line['partner_id'])
                            #                         print 'partner ',partner
                            # for key, lines in a:
                            #                         print "lines ",line
                            #                 if key == u'Ангилалгүй':
                            #                     sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
                            #                 else:
                            #                 sheet.write(rowx, 0, '', styledict['text_center_xf'])
                            vat = self._get_vat(partner)
                            sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                            sheet.write(rowx, 1, vat, styledict['text_xf'])
                            sheet.write(rowx, 2, partner.name, styledict['text_xf'])
                            #                 sheet.write(rowx, 5, line['initial_cur'], styledict['number_xf'])
                            sheet.write(rowx, 3, line['initial'], styledict['number_xf'])
                            #                 sheet.write(rowx, 7, line['debit_cur'], styledict['number_xf'])
                            sheet.write(rowx, 4, line['debit'], styledict['number_xf'])
                            #                 sheet.write(rowx, 9, line['credit_cur'], styledict['number_xf'])
                            sheet.write(rowx, 5, line['credit'], styledict['number_xf'])
                            #                 sheet.write(rowx, 11, line['balance_cur'], styledict['number_xf'])
                            sheet.write(rowx, 6, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['created'], styledict['number_xf'])

                            totals[0] += line['initial_cur']
                            totals[1] += line['initial']
                            totals[2] += line['debit_cur']
                            totals[3] += line['debit']
                            totals[4] += line['credit_cur']
                            totals[5] += line['credit']
                            #                 totals[6] += line['balance_cur']
                            totals[7] += line['balance']

                            totals2[0] += line['initial_cur']
                            totals2[1] += line['initial']
                            totals2[2] += line['debit_cur']
                            totals2[3] += line['debit']
                            totals2[4] += line['credit_cur']
                            totals2[5] += line['credit']
                            #                 totals[6] += line['balance_cur']
                            totals2[7] += line['balance']

                            number += 1
                            rowx += 1

                        sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
                        sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
                        sheet.write(rowx, 4, totals2[3], styledict['number_bold_xf'])
                        sheet.write(rowx, 5, totals2[5], styledict['number_bold_xf'])
                        sheet.write(rowx, 6, totals2[7], styledict['number_bold_xf'])
                        rowx += 1
            else:
                if not self.is_not_group:
                    sorted_data = {}
                    # print('data ', data)
                    for i in data.keys():
                        #                         sorted_data[data[i][0]['name']+':'+str(i)]=data[i]
                        sorted_data[str(i)] = data[i]  # зөвхөн id г авах data[i][0]['name']+':'+
                    # print ('sorted_data ',sorted_data)
                    for k in sorted(sorted_data.keys()):
                        #                         print ('sorted_data[k] ',sorted_data[k])
                        #                 for k in data.keys():
                        #                 else:
                        #                     partner = self.env['res.partner'].browse(k)
                        #                     ref=partner.ref
                        #                     name=partner.name
                        ref = sorted_data[k][0]['partner_ref']
                        if k != 'None':
                            partner = self.env['res.partner'].browse(int(k))
                            ref = self._get_vat(partner)
                        name = sorted_data[k][0]['name']
                        row_end = rowx
                        #                         sheet.write(rowx, 0, u'харилцагч:', styledict['text_bold_xf_no_wrap'])
                        #                         sheet.write(rowx, 1, ref, styledict['text_bold_xf_no_wrap'])
                        #                         sheet.write(rowx, 2, name, styledict['text_bold_xf_no_wrap'])
                        rowx += 1
                        #                     print "k-------------",k
                        #                     print "data[k] ",data[k]

                        totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                        for line in sorted_data[k]:
                            # for key, lines in a:
                            #                 if key == u'Ангилалгүй':
                            #                     sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
                            #                 else:
                            #                 sheet.write(rowx, 0, '', styledict['text_center_xf'])
                            if self.is_with_balance and line['balance'] == 0:
                                continue
                            sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                            sheet.write(rowx, 1, line['account_code'], styledict['text_xf'])
                            sheet.write(rowx, 2, line['account_name'], styledict['text_xf'])
                            #                 sheet.write(rowx, 5, line['initial_cur'], styledict['number_xf'])
                            sheet.write(rowx, 3, line['initial'], styledict['number_xf'])
                            #                 sheet.write(rowx, 7, line['debit_cur'], styledict['number_xf'])
                            sheet.write(rowx, 4, line['debit'], styledict['number_xf'])
                            #                 sheet.write(rowx, 9, line['credit_cur'], styledict['number_xf'])
                            sheet.write(rowx, 5, line['credit'], styledict['number_xf'])
                            #                 sheet.write(rowx, 11, line['balance_cur'], styledict['number_xf'])
                            sheet.write(rowx, 6, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['created'], styledict['number_xf'])

                            totals[0] += line['initial_cur']
                            totals[1] += line['initial']
                            totals[2] += line['debit_cur']
                            totals[3] += line['debit']
                            totals[4] += line['credit_cur']
                            totals[5] += line['credit']
                            #                 totals[6] += line['balance_cur']
                            totals[7] += line['balance']

                            totals2[0] += line['initial_cur']
                            totals2[1] += line['initial']
                            totals2[2] += line['debit_cur']
                            totals2[3] += line['debit']
                            totals2[4] += line['credit_cur']
                            totals2[5] += line['credit']
                            #                 totals[6] += line['balance_cur']
                            totals2[7] += line['balance']

                            number += 1
                            rowx += 1
                        if (self.is_with_balance and totals2[7] != 0) or not self.is_with_balance:
                            sheet.write(row_end, 0, u'харилцагч:', styledict['text_bold_xf_no_wrap'])
                            sheet.write(row_end, 1, ref, styledict['text_bold_xf_no_wrap'])
                            sheet.write(row_end, 2, name, styledict['text_bold_xf_no_wrap'])

                            sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
                            sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
                            sheet.write(rowx, 4, totals2[3], styledict['number_bold_xf'])
                            sheet.write(rowx, 5, totals2[5], styledict['number_bold_xf'])
                            sheet.write(rowx, 6, totals2[7], styledict['number_bold_xf'])
                            sheet.write(rowx, 7, '', styledict['number_xf'])
                            rowx += 1
                        else:
                            rowx = row_end
                else:
                    sorted_data = {}
                    for i in data.keys():
                        #                         sorted_data[data[i][0]['name']+':'+str(i)]=data[i]
                        sorted_data[str(i)] = data[i]  # зөвхөн id г авах data[i][0]['name']+':'+

                    for k in sorted(sorted_data.keys()):
                        ref = sorted_data[k][0]['partner_ref']
                        name = sorted_data[k][0]['name']
                        if k != 'None':
                            partner = self.env['res.partner'].browse(int(k))
                            ref = self._get_vat(partner)

                        #                         sheet.write(rowx, 0, u'харилцагч:', styledict['text_bold_xf_no_wrap'])
                        #                         sheet.write(rowx, 1, ref, styledict['text_bold_xf_no_wrap'])
                        #                         sheet.write(rowx, 2, name, styledict['text_bold_xf_no_wrap'])
                        #                         rowx += 1
                        #                     print "k-------------",k
                        #                     print "data[k] ",data[k]

                        totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                        for line in sorted_data[k]:
                            # for key, lines in a:
                            #                 if key == u'Ангилалгүй':
                            #                     sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
                            #                 else:
                            #                 sheet.write(rowx, 0, '', styledict['text_center_xf'])
                            if self.is_with_balance and line['balance'] == 0:
                                continue
                            sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                            sheet.write(rowx, 1, ref, styledict['text_xf'])
                            sheet.write(rowx, 2, name, styledict['text_xf'])
                            sheet.write(rowx, 3, line['account_code'], styledict['text_xf'])
                            sheet.write(rowx, 4, line['account_name'], styledict['text_xf'])
                            sheet.write(rowx, 5, line['initial'], styledict['number_xf'])
                            sheet.write(rowx, 6, line['debit'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['credit'], styledict['number_xf'])
                            sheet.write(rowx, 8, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 9, line['created'], styledict['number_xf'])

                            totals[0] += line['initial_cur']
                            totals[1] += line['initial']
                            totals[2] += line['debit_cur']
                            totals[3] += line['debit']
                            totals[4] += line['credit_cur']
                            totals[5] += line['credit']
                            #                 totals[6] += line['balance_cur']
                            totals[7] += line['balance']

                            totals2[0] += line['initial_cur']
                            totals2[1] += line['initial']
                            totals2[2] += line['debit_cur']
                            totals2[3] += line['debit']
                            totals2[4] += line['credit_cur']
                            totals2[5] += line['credit']
                            #                 totals[6] += line['balance_cur']
                            totals2[7] += line['balance']

                            number += 1
                            rowx += 1

            #                         sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
            #                         sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
            #                         sheet.write(rowx, 4, totals2[3], styledict['number_bold_xf'])
            #                         sheet.write(rowx, 5, totals2[5], styledict['number_bold_xf'])
            #                         sheet.write(rowx, 6, totals2[7], styledict['number_bold_xf'])
            #                         rowx+=1
            if number < 10:
                while number <= 10:
                    sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                    sheet.write(rowx, 1, '', styledict['text_xf'])
                    sheet.write(rowx, 2, '', styledict['text_xf'])
                    sheet.write(rowx, 3, '', styledict['text_xf'])
                    sheet.write(rowx, 4, '', styledict['number_xf'])
                    sheet.write(rowx, 5, '', styledict['number_xf'])
                    sheet.write(rowx, 6, '', styledict['number_xf'])
                    sheet.write(rowx, 7, '', styledict['number_xf'])
                    # sheet.write(rowx, 8, '', styledict['text_xf'])
                    number += 1
                    rowx += 1
            if not self.is_not_group:
                sheet.write_merge(rowx, rowx, 0, 2, u'Нийт дүн', styledict['heading_xf'])
                sheet.write(rowx, 3, totals[1], styledict['gold_number_bold_xf'])
                sheet.write(rowx, 4, totals[3], styledict['gold_number_bold_xf'])
                sheet.write(rowx, 5, totals[5], styledict['gold_number_bold_xf'])
                sheet.write(rowx, 6, totals[7], styledict['gold_number_bold_xf'])
            else:
                sheet.write_merge(rowx, rowx, 0, 4, u'Нийт дүн', styledict['heading_xf'])
                sheet.write(rowx, 5, totals[1], styledict['gold_number_bold_xf'])
                sheet.write(rowx, 6, totals[3], styledict['gold_number_bold_xf'])
                sheet.write(rowx, 7, totals[5], styledict['gold_number_bold_xf'])
                sheet.write(rowx, 8, totals[7], styledict['gold_number_bold_xf'])

            rowx += 1
            for key, value in cur_data.items():
                sheet.write(rowx, 0, '', styledict['text_xf'])
                sheet.write(rowx, 1, '', styledict['text_xf'])
                sheet.write(rowx, 2, '', styledict['text_xf_grey'])
                sheet.write(rowx, 3, key, styledict['text_xf_grey'])
                sheet.write(rowx, 4, '', styledict['text_xf_grey'])
                sheet.write(rowx, 5, value['initial_cur'], styledict['number_xf_grey'])
                sheet.write(rowx, 6, value['initial'], styledict['number_xf_grey'])
                sheet.write(rowx, 7, value['debit_cur'], styledict['number_xf_grey'])
                sheet.write(rowx, 8, value['debit'], styledict['number_xf_grey'])
                sheet.write(rowx, 9, value['credit_cur'], styledict['number_xf_grey'])
                sheet.write(rowx, 10, value['credit'], styledict['number_xf_grey'])
                sheet.write(rowx, 11, value['balance_cur'], styledict['number_xf_grey'])
                sheet.write(rowx, 12, value['balance'], styledict['number_xf_grey'])
                rowx += 1
            inch = 1200
            if not self.is_not_group:
                sheet.col(0).width = int(2 * inch)
                sheet.col(1).width = int(3 * inch)
                sheet.col(2).width = int(5 * inch)
                sheet.col(3).width = int(3 * inch)
                sheet.col(4).width = int(3 * inch)
                sheet.col(5).width = int(3 * inch)
                sheet.col(6).width = int(3 * inch)
            else:
                sheet.col(0).width = int(2 * inch)
                sheet.col(1).width = int(3 * inch)
                sheet.col(2).width = int(5 * inch)
                sheet.col(3).width = int(3 * inch)
                sheet.col(4).width = int(5 * inch)
                sheet.col(5).width = int(3 * inch)
                sheet.col(6).width = int(3 * inch)
                sheet.col(7).width = int(3 * inch)
                sheet.col(8).width = int(3 * inch)
        else:
            sheet.write_merge(rowx, rowx + 2, 0, 0, u'', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx + 2, 1, 1, u'', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx + 2, 2, 2, u'Код', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx + 2, 3, 3, u'Нэр', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx + 2, 4, 4, u'Валютын төрөл', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx + 1, 5, 6, u'Эхний үлдэгдэл', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 5, 5, u'Валют', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 6, 6, u'Төгрөг', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx, 7, 10, u'Гүйлгээний дүн', styledict['heading_xf'])
            sheet.write_merge(rowx + 1, rowx + 1, 7, 8, u'Дебит', styledict['heading_xf'])
            sheet.write_merge(rowx + 1, rowx + 1, 9, 10, u'Кредит', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 7, 7, u'Валют', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 8, 8, u'Төгрөг', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 9, 9, u'Валют', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 10, 10, u'Төгрөг', styledict['heading_xf'])
            sheet.write_merge(rowx, rowx + 1, 11, 12, u'Эцсийн үлдэгдэл', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 11, 11, u'Валют', styledict['heading_xf'])
            sheet.write_merge(rowx + 2, rowx + 2, 12, 12, u'Төгрөг', styledict['heading_xf'])
            rowx += 3
            #
            data = {}
            sums = {}
            cur_data = {}
            data, sums = self.data_calc(data, data_wz, lines, sums)

            number = 1

            totals = [0, 0, 0, 0, 0, 0, 0, 0]

            a = {}
            number = 1
            for k in data.keys():
                if data_wz.get('account_id', False):
                    partner_cat = self.env['res.partner.category'].browse(k)
                    if partner_cat:
                        sheet.write(rowx, 0, u'Ангилал:', styledict['text_bold_xf_no_wrap'])
                        sheet.write(rowx, 1, partner_cat.name, styledict['text_bold_xf_no_wrap'])
                    else:
                        sheet.write(rowx, 0, u'Ангилал:', styledict['text_bold_xf_no_wrap'])
                        sheet.write(rowx, 1, u'Ангилалгүй', styledict['text_bold_xf_no_wrap'])
                    #                     sheet.write(rowx, 2, partner.name, styledict['text_bold_xf_no_wrap'])
                    rowx += 1
                    #                     print "k",k
                    #                     print "data[k] ",data[k]
                    totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                    sort_data = []
                    for l in data[k]:
                        partner = self.env['res.partner'].browse(l['partner_id'])
                        if partner.name:
                            l['partner_name'] = partner.name
                        else:
                            l['partner_name'] = 'null'
                        sort_data.append(l)
                    #                     for line in data[k]:
                    result = sorted(sort_data, key=itemgetter('partner_name'))
                    for line in result:
                        if self.is_with_balance and line['balance_cur'] == 0 and line['balance'] == 0:
                            continue
                        partner = self.env['res.partner'].browse(line['partner_id'])
                        #                         print 'partner ',partner
                        # for key, lines in a:
                        #                         print "lines ",line
                        #                 if key == u'Ангилалгүй':
                        #                     sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
                        #                 else:
                        #                 sheet.write(rowx, 0, '', styledict['text_center_xf'])
                        currency = ''
                        if line.get('currency_id', False):
                            currency = self.env['res.currency'].browse(line['currency_id']).name
                        vat = self._get_vat(partner)
                        sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                        sheet.write(rowx, 1, '', styledict['text_xf'])
                        sheet.write(rowx, 2, vat, styledict['text_xf'])
                        sheet.write(rowx, 3, partner.name, styledict['text_xf'])
                        sheet.write(rowx, 4, currency, styledict['text_center_xf'])
                        sheet.write(rowx, 5, line['initial_cur'], styledict['number_xf'])
                        sheet.write(rowx, 6, line['initial'], styledict['number_xf'])
                        sheet.write(rowx, 7, line['debit_cur'], styledict['number_xf'])
                        sheet.write(rowx, 8, line['debit'], styledict['number_xf'])
                        sheet.write(rowx, 9, line['credit_cur'], styledict['number_xf'])
                        sheet.write(rowx, 10, line['credit'], styledict['number_xf'])
                        sheet.write(rowx, 11, line['balance_cur'], styledict['number_xf'])
                        sheet.write(rowx, 12, line['balance'], styledict['number_xf'])

                        totals[0] += line['initial_cur']
                        totals[1] += line['initial']
                        totals[2] += line['debit_cur']
                        totals[3] += line['debit']
                        totals[4] += line['credit_cur']
                        totals[5] += line['credit']
                        totals[6] += line['balance_cur']
                        totals[7] += line['balance']

                        totals2[0] += line['initial_cur']
                        totals2[1] += line['initial']
                        totals2[2] += line['debit_cur']
                        totals2[3] += line['debit']
                        totals2[4] += line['credit_cur']
                        totals2[5] += line['credit']
                        totals2[6] += line['balance_cur']
                        totals2[7] += line['balance']

                        number += 1
                        rowx += 1

                    #                     sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
                    #                     sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
                    #                     sheet.write(rowx, 4, totals2[2], styledict['number_bold_xf'])
                    #                     sheet.write(rowx, 5, totals2[3], styledict['number_bold_xf'])
                    #                     sheet.write(rowx, 6, totals2[4], styledict['number_bold_xf'])
                    #                     sheet.write(rowx, 7, totals2[5], styledict['number_bold_xf'])
                    #                     sheet.write(rowx, 8, totals2[6], styledict['number_bold_xf'])
                    #                     sheet.write(rowx, 9, totals2[7], styledict['number_bold_xf'])
                    # #                     sheet.write(rowx, 10, totals2[8], styledict['number_bold_xf'])
                    # #                     sheet.write(rowx, 11, totals2[9], styledict['number_bold_xf'])
                    sheet.write(rowx, 0, u'', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 1, u'', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 3, u'', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 4, u'', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 5, totals2[0], styledict['number_bold_xf'])
                    sheet.write(rowx, 6, totals2[1], styledict['number_bold_xf'])
                    sheet.write(rowx, 7, totals2[2], styledict['number_bold_xf'])
                    sheet.write(rowx, 8, totals2[3], styledict['number_bold_xf'])
                    sheet.write(rowx, 9, totals2[4], styledict['number_bold_xf'])
                    sheet.write(rowx, 10, totals2[5], styledict['number_bold_xf'])
                    sheet.write(rowx, 11, totals2[6], styledict['number_bold_xf'])
                    sheet.write(rowx, 12, totals2[7], styledict['number_bold_xf'])
                    rowx += 1
                else:
                    partner = self.env['res.partner'].browse(k)
                    vat = self._get_vat(partner)
                    sheet.write(rowx, 0, u'харилцагч:', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 1, vat, styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 2, partner.name, styledict['text_bold_xf_no_wrap'])
                    rowx += 1
                    #                     print "k-------------",k
                    #                     print "data[k] ",data[k]
                    totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                    for line in data[k]:
                        if self.is_with_balance and line['balance_cur'] == 0 and line['balance'] == 0:
                            continue
                        # for key, lines in a:
                        #                 if key == u'Ангилалгүй':
                        #                     sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
                        #                 else:
                        #                 sheet.write(rowx, 0, '', styledict['text_center_xf'])
                        currency = ''
                        if line.get('currency_id', False):
                            currency = self.env['res.currency'].browse(line['currency_id']).name
                        sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                        sheet.write(rowx, 1, '', styledict['text_center_xf'])
                        sheet.write(rowx, 2, line['account_code'], styledict['text_xf'])
                        sheet.write(rowx, 3, line['account_name'], styledict['text_xf'])
                        sheet.write(rowx, 4, currency, styledict['text_center_xf'])
                        sheet.write(rowx, 5, line['initial_cur'], styledict['number_xf'])
                        sheet.write(rowx, 6, line['initial'], styledict['number_xf'])
                        sheet.write(rowx, 7, line['debit_cur'], styledict['number_xf'])
                        sheet.write(rowx, 8, line['debit'], styledict['number_xf'])
                        sheet.write(rowx, 9, line['credit_cur'], styledict['number_xf'])
                        sheet.write(rowx, 10, line['credit'], styledict['number_xf'])
                        sheet.write(rowx, 11, line['balance_cur'], styledict['number_xf'])
                        sheet.write(rowx, 12, line['balance'], styledict['number_xf'])

                        totals[0] += line['initial_cur']
                        totals[1] += line['initial']
                        totals[2] += line['debit_cur']
                        totals[3] += line['debit']
                        totals[4] += line['credit_cur']
                        totals[5] += line['credit']
                        totals[6] += line['balance_cur']
                        totals[7] += line['balance']

                        totals2[0] += line['initial_cur']
                        totals2[1] += line['initial']
                        totals2[2] += line['debit_cur']
                        totals2[3] += line['debit']
                        totals2[4] += line['credit_cur']
                        totals2[5] += line['credit']
                        totals2[6] += line['balance_cur']
                        totals2[7] += line['balance']

                        number += 1
                        rowx += 1

                    sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
                    sheet.write(rowx, 5, totals2[0], styledict['number_bold_xf'])
                    sheet.write(rowx, 6, totals2[1], styledict['number_bold_xf'])
                    sheet.write(rowx, 7, totals2[2], styledict['number_bold_xf'])
                    sheet.write(rowx, 8, totals2[3], styledict['number_bold_xf'])
                    sheet.write(rowx, 9, totals2[4], styledict['number_bold_xf'])
                    sheet.write(rowx, 10, totals2[5], styledict['number_bold_xf'])
                    sheet.write(rowx, 11, totals2[6], styledict['number_bold_xf'])
                    sheet.write(rowx, 12, totals2[7], styledict['number_bold_xf'])
                    rowx += 1

            if number < 10:
                while number <= 10:
                    sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                    sheet.write(rowx, 1, '', styledict['text_xf'])
                    sheet.write(rowx, 2, '', styledict['text_xf'])
                    sheet.write(rowx, 3, '', styledict['text_xf'])
                    sheet.write(rowx, 4, '', styledict['number_xf'])
                    sheet.write(rowx, 5, '', styledict['number_xf'])
                    sheet.write(rowx, 6, '', styledict['number_xf'])
                    sheet.write(rowx, 7, '', styledict['number_xf'])
                    sheet.write(rowx, 8, '', styledict['number_xf'])
                    sheet.write(rowx, 9, '', styledict['number_xf'])
                    sheet.write(rowx, 10, '', styledict['number_xf'])
                    sheet.write(rowx, 11, '', styledict['number_xf'])
                    sheet.write(rowx, 12, '', styledict['number_xf'])
                    number += 1
                    rowx += 1

            sheet.write_merge(rowx, rowx, 0, 2, u'Нийт дүн', styledict['heading_xf'])
            sheet.write(rowx, 5, totals[0], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 6, totals[1], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 7, totals[2], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 8, totals[3], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 9, totals[4], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 10, totals[5], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 11, totals[6], styledict['gold_number_bold_xf'])
            sheet.write(rowx, 12, totals[7], styledict['gold_number_bold_xf'])
            #             sheet.write(rowx, 12, totals[8], styledict['gold_number_bold_xf'])

            rowx += 1

            inch = 1200
            sheet.col(0).width = int(1.6 * inch)
            sheet.col(1).width = int(0.6 * inch)
            sheet.col(2).width = int(3 * inch)
            sheet.col(3).width = int(5 * inch)
            sheet.col(4).width = int(1 * inch)
            sheet.col(5).width = int(2 * inch)
            sheet.col(6).width = int(3 * inch)
            sheet.col(7).width = int(2 * inch)
            sheet.col(8).width = int(3 * inch)
            sheet.col(9).width = int(2 * inch)
            sheet.col(10).width = int(3 * inch)
            sheet.col(11).width = int(2 * inch)
            sheet.col(12).width = int(3 * inch)

        sheet.write(rowx, 0, u'Хэвлэсэн огноо: %s' % (time.strftime('%Y-%m-%d'),),
                    ezxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 160'))

        sheet.write(rowx + 4, 2,
                    u"Боловсруулсан: Нягтлан бодогч ......................................... /                                         /",
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet.write(rowx + 6, 2,
                    u"Хянасан: Ерөнхий нягтлан бодогч .............................................../                                         /",
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))

        #         return {'data':book, 'attache_name':report_service.attache_name}

        #         from io import StringIO
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)

        filename = "partner_balance_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
        #         out = base64.encodebytes(buffer.getvalue())
        out = encodebytes(buffer.getvalue())
        buffer.close()

        excel_id = self.env['report.excel.output'].create({
            'data': out,
            'name': filename
        })
        # cdccdcd
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(
                excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
        }

    def _get_partner_domain(self):
        partner_ids = []
        if self.partner_id:
            partner_ids = self.partner_id
        elif self.tag_id:
            partner_ids = self.env['res.partner'].search([('category_id', 'in', [self.tag_id.id])])

        return partner_ids

    def get_domain(self, domain, donwload=False):
        domain_val = ''
        account_ids = []
        acc_domain = [("company_id", "=", self.company_id.id)]
        acc_domain += [("internal_type", "in", ("receivable", "payable"))]
        account_ids = self.env["account.account"].search(acc_domain)
        if self.account_ids:
            #             account_ids=self.account_ids.ids
            domain.append(('account_id', 'in', account_ids.ids))
        elif self.account_id:
            domain.append(('account_id', '=', self.account_id.id))
        domain.append('|')
        domain.append(('date_init', '<', self.date_from))
        domain.append('&')
        domain.append(('date', '<=', self.date_to))
        domain.append(('date', '>=', self.date_from))
        domain.append(('move_id.state', '=', 'posted'))
        if self.is_with_balance:
            # domain.append(('|',('final_debit','!=',0),('final_credit','!=',0)))
            domain.append('|')
            domain.append(('final_debit', '!=', 0))
            domain.append(('final_credit', '!=', 0))
        #         if account_ids:
        #         if self.partner_id:
        #             domain.append(('partner_id','=',self.partner_id.id))
        #         elif self.tag_id:
        #             partner_ids = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])
        #             domain.append(('partner_id','in',partner_ids.ids))
        partner_ids = self._get_partner_domain()
        # print('partner_ids+++++ ', partner_ids)
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids.ids))
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        if self.brand_id:
            domain.append(('brand_id', '=', self.brand_id.id))
        #         print ('domain ,',domain)
        return domain

    def get_domain_balance_where(self, domain, donwload=False):
        # select sum(final_debit-final_credit),partner_id from (select * from account_transaction_balance_pivot where account_id=4754 and partner_id in (22789, 17653, 22449, 17712, 17713, 17711, 17720, 17721, 17790, 19199, 20911, 19200, 20745, 17788, 20746, 17792, 17787, 17786, 17785, 17784, 17791, 19201, 22588, 22589, 17745, 20858, 19218, 17766, 22952, 23060, 17774, 17773, 18600, 17812, 17813, 17811, 17684, 17686, 17687, 17697, 17696, 17698, 17702, 17703, 17691, 17704, 17701, 17700, 17694, 17695, 17693, 17690, 17685, 22863, 17680, 17692, 17682, 17683, 19582, 17681, 22392, 17746, 17730, 17724, 17725, 17729, 17732, 17728, 19203, 17765) and (date_init<'2023-05-01' or date between '2023-05-01' and '2023-05-16')) as foo group by partner_id;
        domain_val = ''
        account_ids = []
        acc_domain = [("company_id", "=", self.company_id.id)]
        acc_domain += [("internal_type", "in", ("receivable", "payable"))]
        account_ids = self.env["account.account"].search(acc_domain)
        acc_where = ""
        if self.account_ids:
            #             domain.append(('account_id','in',account_ids.ids))
            acc_where = " account_id in (" + ','.join(map(str, account_ids.ids)) + ") "

        elif self.account_id:
            #             domain.append(('account_id','=',self.account_id.id))
            acc_where = " account_id = {} ".format(self.account_id.id)
        date_where = ' and (date_init<\'{0}\' or date between \'{0}\' and \'{1}\') '.format(
            self.date_from.strftime("%Y-%m-%d"), self.date_to.strftime("%Y-%m-%d"))
        partner_ids = self._get_partner_domain()

        if partner_ids:
            partner_where = " AND partner_id in (" + ','.join(map(str, partner_ids.ids)) + ") "
        #         if self.branch_id:
        #             domain.append(('branch_id','=',self.branch_id.id))
        #         print ('domain ,',domain)
        self._cr.execute(
            "select * from ( "
            "select sum(final_debit-final_credit) as bal,partner_id from "
            "(select * from account_transaction_balance_pivot "
            "WHERE "
            " " + acc_where + " " + partner_where + " " + date_where + " "
                                                                       ") as foo group by partner_id "
                                                                       ") as ff where bal=0 ")
        # "ORDER BY p.name,l.account_id ")

        res = self._cr.dictfetchall()
        #         print ('res ',res)
        partners = []
        for r in res:
            if r.get('partner_id', False):
                partners.append(r['partner_id'])
        return partners

    #         return domain

    def print_report_html(self):
        ''' Pivot
        '''
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to',  'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')

        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
        data['form']['company_id'] = form['company_id'][0]
        acc_domain = [("company_id", "=", self.company_id.id)]
        acc_domain += [("internal_type", "in", ("receivable", "payable"))]
        account_ids = self.env["account.account"].search(acc_domain)
        if self.account_ids:
            account_ids = self.account_ids.ids
        data['form']['account_ids'] = account_ids
        data['form']['check_balance_method'] = True

        datas = data
        domain = []
        action = self.env.ref('mw_account.action_account_partner_ledget_pivot_pivot')
        vals = action.read()[0]
        dom = self.get_domain(domain)
        if self.is_with_balance:
            partners_zero = self.get_domain_balance_where(domain)
            #             print ('dom+++++++++ ',partners_zero)
            dom.append(('partner_id', 'not in', partners_zero))
        #         if self.teg_uld_harahgui and qty_char:
        #             model_obj = action.res_model
        #             obj_model = self.env[model_obj]
        #             result_ids = []
        #             gl_initial_acc_bs = self.env[model_obj].read_group(
        #             domain=dom,
        #             fields=["product_id", qty_char],
        #             groupby=["product_id"],
        #             )
        #             for gl in gl_initial_acc_bs:
        #                 if gl[qty_char]!=0:
        #                     result_ids.append(gl['product_id'][0])
        #
        #             if result_ids:
        #                 dom = [('product_id','in',result_ids)]+dom
        vals['domain'] = dom
        return vals

    def print_report_html_backup(self):
        self.ensure_one()
        result_context = dict(self._context or {})
        self.ensure_one()
        result_context = dict(self._context or {})

        #         data['form'].update(self._build_contexts(data))
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to',  'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')

        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
        #         data = self.pre_print_report(data)
        data['form']['type'] = self.type
        data['form']['company_id'] = self.company_id.id
        data['form']['condition'] = self.condition
        data['form']['partner_id'] = self.partner_id and [self.partner_id.id] or False

        data['form']['account_id'] = self.account_id and [self.account_id.id] or False

        #         data['form']['account_ids'] = data['form']['chart_account_ids']
        #         data['form']['company_type'] = data['form']['company_type']
        #         data['form']['check_balance_method'] = form['check_balance_method']
        #         data['form']['is_categ'] = form['is_categ']
        #         data['form']['is_parent'] = form['is_parent']
        if self.account_id:
            lines = self.create_report_data_account(data['form'])
        else:
            lines = self.create_report_data(data['form'])
        data_wz = data['form']
        sums = {}
        data_c = {}
        #         print ('lines ',lines)
        data, susm = self.data_calc(data_c, data_wz, lines, sums)
        number = 1
        all_datas = []
        totals = [0, 0, 0, 0, 0, 0, 0, 0]
        #         print ('data:::: ',data)
        for k in data.keys():
            if data_wz.get('account_id', False):

                partner_cat = self.env['res.partner.category'].browse(k)
                if partner_cat:
                    row_data = {'Dd': u'Ангилал',
                                'Code': '',
                                'Name': partner_cat.name,
                                'C1': '',
                                'Debit': '',
                                'Credit': '',
                                'C2': ''}
                else:
                    row_data = {'Dd': u'Ангилал',
                                'Code': '',
                                'Name': u'Ангилалгүй',
                                'C1': '',
                                'Debit': '',
                                'Credit': '',
                                'C2': ''}
                all_datas.append(row_data)
                totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                sort_data = []
                for l in data[k]:
                    partner = self.env['res.partner'].browse(l['partner_id'])
                    if partner.name:
                        l['partner_name'] = partner.name
                    else:
                        l['partner_name'] = 'null'
                    sort_data.append(l)
                #                     for line in data[k]:
                result = sorted(sort_data, key=itemgetter('partner_name'))
                for line in result:
                    partner = self.env['res.partner'].browse(line['partner_id'])
                    #                     sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                    #                     sheet.write(rowx, 1, partner.ref, styledict['text_xf'])
                    #                     sheet.write(rowx, 2, partner.name, styledict['text_xf'])
                    #
                    row_data = {
                        'Dd': number,
                        'Code': partner.ref,
                        'Name': partner.name,
                        'C1': line['initial'],
                        'Debit': line['debit'],
                        'Credit': line['credit'],
                        'C2': line['balance']
                    }
                    all_datas.append(row_data)

                    totals[0] += line['initial_cur']
                    totals[1] += line['initial']
                    totals[2] += line['debit_cur']
                    totals[3] += line['debit']
                    totals[4] += line['credit_cur']
                    totals[5] += line['credit']
                    #                 totals[6] += line['balance_cur']
                    totals[7] += line['balance']

                    totals2[0] += line['initial_cur']
                    totals2[1] += line['initial']
                    totals2[2] += line['debit_cur']
                    totals2[3] += line['debit']
                    totals2[4] += line['credit_cur']
                    totals2[5] += line['credit']
                    #                 totals[6] += line['balance_cur']
                    totals2[7] += line['balance']

                    number += 1
                row_data = {'Dd': u'',
                            'Code': '',
                            'Name': u'Дүн',
                            'C1': totals2[1],
                            'Debit': totals2[3],
                            'Credit': totals2[5],
                            'C2': totals2[7]}
                all_datas.append(row_data)

            else:
                partner = self.env['res.partner'].browse(k)
                row_data = {'Dd': u'харилцагч',
                            'Code': partner.ref,
                            'Name': partner.name,
                            'C1': '',
                            'Debit': '',
                            'Credit': '',
                            'C2': ''}
                all_datas.append(row_data)
                totals2 = [0, 0, 0, 0, 0, 0, 0, 0]
                for line in data[k]:
                    row_data = {
                        'Dd': number,
                        'Code': line['account_code'],
                        'Name': line['account_name'],
                        'C1': line['initial'],
                        'Debit': line['debit'],
                        'Credit': line['credit'],
                        'C2': line['balance']
                    }
                    all_datas.append(row_data)

                    totals[0] += line['initial_cur']
                    totals[1] += line['initial']
                    totals[2] += line['debit_cur']
                    totals[3] += line['debit']
                    totals[4] += line['credit_cur']
                    totals[5] += line['credit']
                    #                 totals[6] += line['balance_cur']
                    totals[7] += line['balance']

                    totals2[0] += line['initial_cur']
                    totals2[1] += line['initial']
                    totals2[2] += line['debit_cur']
                    totals2[3] += line['debit']
                    totals2[4] += line['credit_cur']
                    totals2[5] += line['credit']
                    #                 totals[6] += line['balance_cur']
                    totals2[7] += line['balance']

                    number += 1

                #                 sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
                #                 sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
                #                 sheet.write(rowx, 4, totals2[3], styledict['number_bold_xf'])
                #                 sheet.write(rowx, 5, totals2[5], styledict['number_bold_xf'])
                #                 sheet.write(rowx, 6, totals2[7], styledict['number_bold_xf'])
                row_data = {'Dd': u'',
                            'Code': '',
                            'Name': u'Дүн',
                            'C1': totals2[1],
                            'Debit': totals2[3],
                            'Credit': totals2[5],
                            'C2': totals2[7]}
                all_datas.append(row_data)
        #         data['form'].update(self._build_contexts(data))

        #         print ('lines ',lines)
        ir_model_obj = self.env['ir.model.data']
        report_id = self.env['mw.account.report'].with_context(data=all_datas).create({'name': 'report2',
                                                                                       #                                                                     'account_id':self.account_id.id,
                                                                                       'date_from': self.date_from,
                                                                                       'date_to': self.date_to
                                                                                       })
        result_context.update({'data': all_datas})
        model, action_id = ir_model_obj.get_object_reference('mw_account', 'action_mw_account_partner_ledger_report')
        [action] = self.env[model].browse(action_id).read()
        #         print ('result_context ',result_context)
        action['context'] = result_context
        action['res_id'] = report_id.id
        #         print ('action ',action)
        return action
