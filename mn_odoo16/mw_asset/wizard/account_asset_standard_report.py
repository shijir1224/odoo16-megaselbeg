# -*- coding: utf-8 -*-

import calendar

from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, UserError
import time
from collections import defaultdict
import pandas
from sre_constants import BRANCH

D_LEDGER = {'general': {'name': _('General Ledger'),
                        'group_by': 'account_id',
                        'model': 'account.account',
                        'short': 'code',
                        },
            'partner': {'name': _('Partner Ledger'),
                        'group_by': 'partner_id',
                        'model': 'res.partner',
                        'short': 'name',
                        },
            'journal': {'name': _('Journal Ledger'),
                        'group_by': 'journal_id',
                        'model': 'account.journal',
                        'short': 'code',
                        },
            'open': {'name': _('Open Ledger'),
                     'group_by': 'account_id',
                     'model': 'account.account',
                     'short': 'code',
                     },
            'aged': {'name': _('Aged Balance'),
                     'group_by': 'partner_id',
                     'model': 'res.partner',
                     'short': 'name',
                     },
            'analytic': {'name': _('Analytic Ledger'),
                         'group_by': 'analytic_account_id',
                         'model': 'account.analytic.account',
                         'short': 'name',
                         },

            }
    
class AccountStandardLedgerPeriode(models.TransientModel):
    _name = 'account.asset.report.standard.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')

class AccountAssetStandardLedgerReport(models.TransientModel):
    _name = 'account.asset.report.standard.ledger.report'

    name = fields.Char()
    report_ids = fields.One2many('account.asset.report.standard.ledger', 'report_id')
    report_name = fields.Char()
#     line_total_ids = fields.Many2many('account.report.standard.ledger.line', relation='table_standard_report_line_total')
#     line_super_total_id = fields.Many2one('account.report.standard.ledger.line')
    print_time = fields.Char()
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
    report_object_ids = fields.One2many('account.asset.report.standard.object', 'report_id')

class AccountAssetStandardObject(models.TransientModel):
    '''Тайлангийн ангилал буюу Ажилтнаар, ангилалаар, агуулахаар, байрлалаар гм бүлэглэх
    '''
    _name = 'account.asset.report.standard.object'
    _order = 'name, id'

    name = fields.Char()
    object_id = fields.Integer()
    report_id = fields.Many2one('account.asset.report.standard.ledger.report')
#     line_ids = fields.One2many('account.report.standard.ledger.line', 'report_object_id')
    account_id = fields.Many2one('account.account', 'Account')
#     category_id = fields.Many2one('account.asset.category', 'Category')
#     partner_id = fields.Many2one('res.partner', 'Partner')
    branch_id = fields.Many2one('res.branch', 'Branch')
#     analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')


class AccountStandardLedger(models.TransientModel):
    _name = 'account.asset.report.standard.ledger'
    _description = 'Account Standard Ledger'

    def _get_periode_date(self):
        lang_code = self.env.user.lang or 'en_US'
        lang_id = self.env['res.lang']._lang_get(lang_code)
        date_format = self.env['res.lang'].browse(lang_id).date_format

        today_year = fields.datetime.now().year
        company = self.env.user.company_id
        last_day = company.fiscalyear_last_day or 31
        last_month = company.fiscalyear_last_month or 12

        periode_obj = self.env['account.asset.report.standard.ledger.periode']
        periode_obj.search([]).unlink()
        periode_ids = periode_obj
        for year in range(today_year, today_year - 4, -1):
            date_from = datetime(year - 1, last_month, last_day) + timedelta(days=1)
            date_to = datetime(year, last_month, last_day)
            user_periode = "%s - %s" % (date_from.strftime(date_format),
                                        date_to.strftime(date_format),
                                        )
            vals = {
                'name': user_periode,
                'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT), }
            periode_ids += periode_obj.create(vals)
        return False

    name = fields.Char(default=u'Үндсэн хөрөнгийн дэлгэрэнгүй тайлан')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
#     journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id)]),
#                                    help='Select journal, for the Open Ledger you need to set all journals.')
    date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.',default=fields.Date.context_today)
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.',default=fields.Date.context_today)
    result_selection = fields.Selection([('customer', 'Customers'),
                                         ('supplier', 'Suppliers'),
                                         ('customer_supplier', 'Customers and Suppliers')
                                         ], string="Partner's", required=True, default='supplier')
    report_name = fields.Char('Report Name')
    old_temp = fields.Boolean('Old template.', default=True)
    report_id = fields.Many2one('account.asset.report.standard.ledger.report')
    branch_ids = fields.Many2many('res.branch', relation='table_standard_report_asset_branches')
    asset_types = fields.Many2many('account.asset.type', string="Хөрөнгийн төрөл")
    
#     owner_id = fields.Many2one('hr.employee', 'Owner')
    owner_id = fields.Many2many('res.partner', domain=[("employee", "=", True)], relation='table_standard_report_asset_partner_new')
    
    is_owner = fields.Boolean('Is owner report.', default=False)
    is_group = fields.Boolean('Is group.', default=False)

    account_ids = fields.Many2many('account.account', domain=lambda self: [('account_type','=','asset_fixed')], relation='table_standard_report_asset_accounts')
    
    is_all_branch = fields.Boolean(u'Бүх салбар сонгох', default=False) 
    is_all_account = fields.Boolean(u'Бүх данс сонгох', default=False)

    dep_ids = fields.Many2many('hr.department', relation='table_standard_report_asset_deps')

    is_not_cost = fields.Boolean(u'Өртөггүй татах?', default=False)
    is_depreciated = fields.Boolean(u'Элэгдлийн тайлан', default=False)
    is_total = fields.Boolean(u'Товчоо тайлан', default=False)
    is_capital = fields.Boolean(u'Капиталжуулалтын тайлан', default=False)
    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end
    @api.onchange('is_group')
    def _onchange_is_group(self):
        if self.is_group == True:
            self.is_not_cost = False
            self.is_depreciated = False
            self.is_total = False
            self.is_capital = False
            self.is_owner = False
    @api.onchange('is_not_cost')
    def _onchange_is_not_cost(self):
        if self.is_not_cost == True:
            self.is_group = False
            self.is_depreciated = False
            self.is_total = False
            self.is_capital = False
            self.is_owner = False
    @api.onchange('is_depreciated')
    def _onchange_is_depreciated(self):
        if self.is_depreciated == True:
            self.is_group = False
            self.is_not_cost = False
            self.is_total = False
            self.is_capital = False
            self.is_owner = False
    @api.onchange('is_total')
    def _onchange_is_total(self):
        if self.is_total == True:
            self.is_group = False
            self.is_not_cost = False
            self.is_depreciated = False
            self.is_capital = False
            self.is_owner = False
    @api.onchange('is_capital')
    def _onchange_is_capital(self):
        if self.is_capital == True:
            self.is_group = False
            self.is_not_cost = False
            self.is_depreciated = False
            self.is_total = False
            self.is_owner = False
    @api.onchange('is_owner')
    def _onchange_is_owner(self):
        if self.is_owner == True:
            self.is_group = False
            self.is_not_cost = False
            self.is_depreciated = False
            self.is_total = False
            self.is_capital = False
    @api.onchange('is_all_branch')
    def onchange_is_all_branch(self):
        if self.is_all_branch:
            self.branch_ids = self.env['res.branch'].search([])
        else:
            self.branch_ids = False
            

    @api.onchange('is_all_account')
    def onchange_is_all_account(self):
        if self.is_all_account:
            self.account_ids = self.env['account.account'].search([('account_type','=','asset_fixed'),('create_asset','!=','no')])
        else:
            self.account_ids = False
                        
                
    def action_view_lines(self):
        self.ensure_one()
#         self._compute_data()
        self._pre_compute()
        context = dict(self._context)
        print ('self.report_id123 ',self.report_id)

        mod_obj = self.env['ir.model.data']        

        # INIT query
        # Орлого зарлага хамтдаа
        search_res = mod_obj.get_object_reference('account_asset_standard_report', 'view_account_asset_report_filter')
        search_id = search_res and search_res[1] or False
        pivot_res = mod_obj.get_object_reference('account_asset_standard_report', 'view_account_asset_report_pivot')
        pivot_id = pivot_res and pivot_res[1] or False
        tree_res = mod_obj.get_object_reference('account_asset_standard_report', 'view_account_asset_report_tree')
        tree_id = tree_res and tree_res[1] or False
        graph_res = mod_obj.get_object_reference('account_asset_standard_report', 'account_asset_report_data_graph_date_cash_basis')
        graph_id = tree_res and graph_res[1] or False

        return {
                'name': _('Report'),
                'view_type': 'form',
                'view_mode': 'pivot,tree,graph',
                'res_model': 'account.asset.report.data',
                'view_id': False,
                'views': [(pivot_id, 'pivot'),(tree_id, 'tree'),(graph_id, 'graph')],
                'search_view_id': search_id,
                'domain': [('report_id','=',self.report_id.id),
#                            ('date','<=',self.date_end),
#                            ('account_id.company_id','=',self.company_id.id),
#                            ('state','=',self.state),
                           ],
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': context,
            }                         

    
    def print_excel_report(self):
        self.ensure_one()
#         self._compute_data()
        self._pre_compute()
        print ('12312312')
#        return self.env['report'].get_action(self, 'account_asset_standard_report.report_account_asset_standard_excel')
        return self.env.ref('mw_asset.action_asset_standard_excel').report_action(self)

    def _get_name_report(self):
        report_name = 'asset detail report'
        return report_name

    def _owner_where(self):
        where=''
#         if self.owner_id:
#             query = """select asset_id from asset_owner_emp_rel where emp_id = {0}""".format(self.owner_id.id)
#             print ('query2 ',query)
#             self.env.cr.execute(query)
#             ids=[]
#             for line in self.env.cr.dictfetchall():
#                 print ('wiz line  ',line )
#                 ids.append(line['asset_id'])
#             if len(ids)>1:
#                 where += ' WHERE asset_id in ('+','.join(map(str, ids))+') '
#             elif len(ids)==1:
#                 where += ' WHERE asset_id = '+str(ids[0])+' '
        where=''
#         if self.owner_id:
#             where = """ AND asset.owner_id = {0} """.format(self.owner_id.id)
        if self.owner_id:
#             dep_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
            
            if len(self.owner_id)==1:
                where += " and asset.owner_id  = %s " %self.owner_id[0].id
            if len(self.owner_id)>1:
                where = " and asset.owner_id in ("+','.join(map(str,self.owner_id.ids))+") "
                                        
#         print ('where ',where)
        return where


    def _owner_select(self):
        query = """,(SELECT 
                                array_agg(name) 
                             FROM res_partner where id in (select owner_id from account_asset where id=report_data.asset_id )
                            ) as owners """
        return query
    

    def _job_select(self):
        query = """,'' as job """
        return query
    

    def _dep_select(self):
        query = """,(select name from hr_department where id =aca.owner_department_id
                            ) as department """
        return query
        
    def _serial_select(self):
        query = """,'serial' as serial,'number' as number,'' as internal_code """
        return query    
    

    def _date_select(self):
        query = """,CASE WHEN aca.purchase_date notnull then aca.purchase_date else aca.date end as idate """
        return query    
        

    def _get_assets_lines(self, account,branch):
        "Get the data from the database"
        where_account_move = ""
#         if options.get('all_entries') is False:
        where_account_move += " AND state = 'posted'"
        owner_where=self._owner_where()
        branch_where=''
        dep_where=''
        type_where=''
#         if branch:
#             branch_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
#             branch_where =' AND asset.branch_id={0}'.format(branch.id) 
        if self.branch_ids:
            if len(self.branch_ids)==1:
                branch_where += " and asset.branch_id  = %s " %self.branch_ids[0].id
            if len(self.branch_ids)>1:
                branch_where = " and asset.branch_id in ("+','.join(map(str,self.branch_ids.ids))+") "

        if self.asset_types:
            if len(self.asset_types)==1:
                type_where += " and asset.asset_type_id  = %s " %self.asset_types[0].id
            if len(self.asset_types)>1:
                type_where = " and asset.asset_type_id in ("+','.join(map(str,self.asset_types.ids))+") "


        if self.dep_ids:
#             dep_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
            
            if len(self.dep_ids)==1:
                dep_where += " and asset.owner_department_id  = %s " %self.dep_ids[0].id
            if len(self.dep_ids)>1:
                dep_where = " and asset.owner_department_id in ("+','.join(map(str,self.dep_ids.ids))+") "
                                        
#                     2020 оны 12 сард аваад элэгдэл нь 2021 1 сараас эхэлж байвал эхний үлдэргдэл биш орлого дээр тусаж байгааг засах.
#                        CASE WHEN asset.acquisition_date notnull and asset.acquisition_date <= %(date_from)s
#                        then asset.acquisition_date else max_date_before.date end  as max_date_before, 
#                        --max_date_before.date as max_date_before,
        print ('branch_where ',branch_where)
#
# select sum(l1.debit) as debit_all,sum(l1.credit) as credit_all,
#         case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
#         then sum(l1.debit)  else 0 end as close_debit
#         from account_account a left join account_move_line l1 on l1.account_id=a.id  
#         where a.id in (select credit_account_id from mrp_product_standart_cost_line where credit_account_id notnull) 
#         and a.company_id=1 and l1.date between '2024-03-01' and '2024-03-31' and l1.company_id=1 and a.id=30122 
#         and l1.branch_id=36         group by l1.move_id
#
# select sum(debit_all) as debit_all,   
# sum(credit_all) as credit_all, 
# sum(close_debit) as close_debit,
# sum(close_credit) as close_credit,
# sum(mrp_debit) as mrp_debit,
# sum(mrp_credit) as mrp_credit,
# sum(other_debit) as other_debit,
# sum(other_credit) as other_credit,
# code
#  from (     
# select a.code,sum(l1.debit) as debit_all,sum(l1.credit) as credit_all,
#         case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
#         then sum(l1.debit)  else 0 end as mrp_debit,
#         case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
#         then sum(l1.credit)  else 0 end as mrp_credit,
#         case when l1.move_id in (select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
#         then sum(l1.debit)  else 0 end as close_debit,
#         case when l1.move_id in (select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
#         then sum(l1.credit)  else 0 end as close_credit,
#         case when l1.move_id not in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull union all select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
#         then sum(l1.debit)  else 0 end as other_debit,
#         case when l1.move_id not in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull union all select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
#         then sum(l1.credit)  else 0 end as other_credit
#         from account_account a left join account_move_line l1 on l1.account_id=a.id  
#         where a.id in (select credit_account_id from mrp_product_standart_cost_line where credit_account_id notnull) 
#         and a.company_id=1 and l1.date between '2024-03-01' and '2024-03-31' and l1.company_id=1 and a.id in (30122, 30118)
#         and l1.branch_id=36         group by l1.move_id ,a.code 
#         ) as foo group by code
#
# select sum(l1.debit) as debit_all,sum(l1.credit) as credit_all from account_account a left join account_move_line l1 on l1.account_id=a.id  where a.id in (select credit_account_id from mrp_product_standart_cost_line where credit_account_id notnull) and a.company_id=1 and l1.date between '2024-03-01' and '2024-03-31' and l1.company_id=1 and a.id=30122 and l1.branch_id=36 ;        
#

        sql = """
                SELECT asset.id as asset_id,
                       asset.parent_id as parent_id,
                       asset.name as asset_name,
                       asset.original_value as asset_original_value,
                       asset.prorata_date as asset_date,
                       CASE WHEN asset.acquisition_date notnull and asset.acquisition_date <= %(date_from)s
                       then asset.acquisition_date else max_date_before.date end  as max_date_before, 
                       --max_date_before.date as max_date_before,
                       asset.disposal_date as asset_disposal_date,
                       asset.acquisition_date as asset_acquisition_date,
                       asset.method as asset_method,
                       (SELECT COUNT(*) FROM account_move WHERE asset_id = asset.id AND asset_value_change != 't') as asset_method_number,
                       asset.method_period as asset_method_period,
                       asset.method_progress_factor as asset_method_progress_factor,
                       asset.state as asset_state,
                       asset.close_status as close_status,
                       asset.car_number as car_number,
                       asset.car_vat as car_vat,
                       asset.car_color as car_color,
                       account.code as account_code,
                       account.name as account_name,
                       account.id as account_id,
                       COALESCE(first_move.asset_depreciated_value, move_before.asset_depreciated_value, 0.0) as depreciated_start,
                       COALESCE(first_move.asset_remaining_value, move_before.asset_remaining_value, 0.0) as remaining_start,
                       COALESCE(last_move.asset_depreciated_value, move_before.asset_depreciated_value, 0.0) as depreciated_end,
                       COALESCE(last_move.depreciation_value, move_before.depreciation_value, 0.0) as depreciation_value_end,
                       COALESCE(last_move.asset_remaining_value, move_before.asset_remaining_value, 0.0) as remaining_end,
                       COALESCE(first_move.amount_total, 0.0) as depreciation
                FROM account_asset as asset
                LEFT JOIN account_account as account ON asset.account_asset_id = account.id
                LEFT OUTER JOIN (SELECT MIN(date) as date, asset_id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s {where_account_move} GROUP BY asset_id) min_date_in ON min_date_in.asset_id = asset.id
                LEFT OUTER JOIN (SELECT MAX(date) as date, asset_id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s {where_account_move} GROUP BY asset_id) max_date_in ON max_date_in.asset_id = asset.id
                LEFT OUTER JOIN (SELECT MAX(date) as date, asset_id FROM account_move WHERE date <= %(date_from)s {where_account_move} GROUP BY asset_id) max_date_before ON max_date_before.asset_id = asset.id
                LEFT OUTER JOIN account_move as first_move ON first_move.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = min_date_in.date {where_account_move} ORDER BY m.id ASC LIMIT 1)
                LEFT OUTER JOIN account_move as last_move ON last_move.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = max_date_in.date {where_account_move} ORDER BY m.id DESC LIMIT 1)
                LEFT OUTER JOIN account_move as move_before ON move_before.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = max_date_before.date {where_account_move} ORDER BY m.id DESC LIMIT 1)
                WHERE asset.acquisition_date <= %(date_to)s
                AND (asset.disposal_date >= %(date_from)s OR asset.disposal_date IS NULL)
                AND asset.state not in ('model', 'draft')
                AND asset.asset_type = 'purchase'
                AND account.id=%(account_id)s
                {owner_where}
                {branch_where}
                {dep_where}
                {type_where}
                ORDER BY account.code;
            """.format(where_account_move=where_account_move,owner_where=owner_where,branch_where=branch_where,dep_where=dep_where,type_where=type_where)
# asset.company_id in %(company_ids)s
        date_to = self.date_to
        date_from = self.date_from
#         company_ids = tuple(t['id'] for t in self._get_options_companies(options))
        print ('sql===1234: ',sql)
        self.flush()
        self.env.cr.execute(sql, {'date_to': date_to, 'date_from': date_from, 'account_id': account.id})
        results = self.env.cr.dictfetchall()
#         print ('results ',results)
        return results        
    
    def _pre_compute(self):
        print ('444444')
        vals = {'report_name': self._get_name_report(),
                'name': self._get_name_report(),
                'date_to': self.date_to if self.date_to else "2099-01-01",
                'date_from': self.date_from if self.date_from else "1970-01-01",
                }
        self.report_id = self.env['account.asset.report.standard.ledger.report'].create(vals)
        
#        print 'self.category_ids.ids ',self.category_ids.ids
        first_capital_dict={}
        
        branch_loop=[]
        if self.branch_ids:
            branch_loop=self.branch_ids
        else:
            branch_loop=[False]
#         for branch in self.branch_ids:
#         for branch in branch_loop:
#            print ('branch.name ',branch.name)
#          for category in self.category_ids:
        branch=False
        for account in self.account_ids:
            obj_vals = {
                'name':'categ',
                'object_id':account.id,
#                 'branch_id':branch and branch.id or False,
#                 'category_id':category.id,
                'account_id':account.id,
                'report_id':self.report_id.id
                }
            obj_id=self.env['account.asset.report.standard.object'].create(obj_vals)
                         
            if self.is_group:
                datas = self._get_assets_lines(account,branch)
#                 print ('datas ',datas)
#                 parent_lines = []
#                 children_lines = defaultdict(list)
                groupped_datas = defaultdict(list)
                all_datas = []
                tmp_dict={}
#                 print ('datas ',datas)
                parent_lines = []
                children_lines = defaultdict(list)
                for al in datas:
                    if al['parent_id']:
                        children_lines[al['parent_id']] += [al]
                    else:
                        parent_lines += [al]
                for al in parent_lines:
                    capital=0
                    move_ex_val=0
                    salvage_value=0
                    if al['asset_method'] == 'linear' and al['asset_method_number']:  # some assets might have 0 depreciations because they dont lose value
                        asset_depreciation_rate = ('{:.2f} %').format((100.0 / al['asset_method_number']) * (12 / int(al['asset_method_period'])))
                    elif al['asset_method'] == 'linear':
                        asset_depreciation_rate = ('{:.2f} %').format(0.0)
                    else:
                        asset_depreciation_rate = ('{:.2f} %').format(float(al['asset_method_progress_factor']) * 100)
        
                    depreciation_opening = al['depreciated_start'] - al['depreciation']
                    depreciation_closing = al['depreciated_end'] 
                    # if dep_close> 0:
                    #     depreciation_closing = al['depreciated_end'] - al['depreciation_value_end']
                    depreciation_minus = 0.0
                    asset_opening = al['asset_original_value'] if al['max_date_before'] else 0.0
                    # print('sadffafas',al['max_date_before'])
                    asset_add = 0.0 if al['max_date_before'] else al['asset_original_value']
                    asset_minus = 0.0
#                     print ('asset_opening:::== ',asset_opening)
                    for child in children_lines[al['asset_id']]:
                        depreciation_opening += child['depreciated_start'] - child['depreciation']
                        depreciation_closing += child['depreciated_end']
        
                        asset_opening += child['asset_original_value'] if child['max_date_before'] else 0.0
                        asset_add += 0.0 if child['max_date_before'] else child['asset_original_value']
        
#                     print ('asset_opening222== ',asset_opening)
                    depreciation_add = depreciation_closing - depreciation_opening
                    asset_closing = asset_opening + asset_add
        
                    if al['asset_state'] == 'close' and al['asset_disposal_date'] and al['asset_disposal_date'] <= fields.Date.to_date(self.date_to):
                        depreciation_minus = depreciation_closing
                        depreciation_closing = 0.0
                        asset_minus = asset_closing
                        asset_closing = 0.0
        
                    asset_gross = asset_closing - depreciation_closing
    #                 total = [x + y for x, y in zip(total, [asset_opening, asset_add, asset_minus, asset_closing, depreciation_opening, depreciation_add, depreciation_minus, depreciation_closing, asset_gross])]
        
    #                 id = "_".join([self._get_account_group(al['account_code'])[0], str(al['asset_id'])])
                    name = str(al['asset_name'])
                    asset = self.env['account.asset'].browse(al['asset_id'])
                    owners='none'
                    branch_name='none'
                    serial='none'
                    number='none'
                    job='none'
                    department='none'
                    internal_code='none'
                    asset_type_name = 'none'
                    if asset.owner_id:
                        owners=asset.owner_id.name
                    if asset.owner_department_id:
                        department=asset.owner_department_id.name
                    if asset.branch_id:
                        branch_name= asset.branch_id.name
                    if asset.asset_type_id:
                        asset_type_name = asset.asset_type_id.name
                    
    #             print 'category------ ',category.name
#                     query = u"""INSERT INTO  account_asset_report_data
#                     (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
#                     income_value,capital_value,expense_value,final_value,initial_depr,income_depr,
#                     expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,
#                     serial,number,job,department,internal_code,salvage_value)
#                     VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
#                     ,'{21}','{22}','{23}','{24}','{25}',{26})
#                     """.format(self.id,1,time.strftime('%Y-%m-%d'),al['asset_id'],al['asset_date'],1,al['asset_acquisition_date'],asset_opening,
#                                asset_add,capital,asset_minus+move_ex_val,asset_opening+asset_add+capital-(asset_minus+move_ex_val)-salvage_value,
#                                depreciation_opening,depreciation_add,depreciation_minus,depreciation_opening+depreciation_add-depreciation_minus,self.report_id.id,account.id,obj_id.id
#                                ,owners,branch_name,serial,number,job,department,internal_code,salvage_value
#                                )
#                     self.env.cr.execute(query)
                    tmp = {'asset_id':al['asset_id'],
                           'group_id':al['group_id'],
                           'date':al['asset_date'],
                           'date2':al['asset_acquisition_date'],
                            'asset_opening':asset_opening,
                            'asset_add':   asset_add,
                            'capital':capital,
                            'expense_value':asset_minus+move_ex_val,
                            'final_value':asset_opening+asset_add+capital-(asset_minus+move_ex_val)-salvage_value,
                            'initial_depr':depreciation_opening,
                            'income_depr':depreciation_add,
                            'expense_depr':depreciation_minus,
                            'final_depr':depreciation_opening+depreciation_add-depreciation_minus,
                            'report_id':self.report_id.id,
                            'account_id':account.id,
                            'report_obj_id':obj_id.id,
                            'branch':branch_name,
                            'serial':serial,
                            'number':number,
                            'job':job,
                            'department':department,
                            'internal_code':internal_code,
                            'salvage_value':salvage_value,
                            'close_status':close_status,
                            'car_color':car_color,
                            'car_number':car_number,
                            'car_vat':car_vat,
                            'asset_type_name':asset_type_name
                           }
#                     if list(filter(lambda o : o['group_id']==al['group_id'], all_datas)):
#                         list(filter(lambda o : o['group_id']==al['group_id'], all_datas))[0]['owner']+=', '+owners
#                     else:
#                          tmp.update({'owner':owners})
                    if tmp_dict.get(al['group_id'],False):
                        if tmp_dict[al['group_id']].get('owner',False):
                            tmp_dict[al['group_id']]['owner'] +=', '+owners
                        else:
                            tmp_dict[al['group_id']]={'owner':owners}
                    else:
                            tmp_dict[al['group_id']]={'owner':owners}
                            
                    all_datas.append(tmp)
#                 print ('all_datas11111 ',all_datas)
#                 print ('tmp_dict ',tmp_dict)
                df = pandas.DataFrame(all_datas)
                result = df.groupby(['group_id','date'])['asset_opening', 'asset_add','capital','expense_value','final_value','initial_depr','income_depr','expense_depr','final_depr'].sum()
#                 print ('ttt ',result)
                for i,al in result.iterrows():
                    # print ('iii ',i)
#                     print ('alal ',al)
                    group_br = self.env['account.asset.group'].browse(i[0])
                    date=i[1]
                    group_id = i[0]
#                     print ('group_br ',group_br)
#                     print ('group_br ',group_br.name)
                    owners='none'
                    branch_name='none'
                    serial='none'
                    number='none'
                    job='none'
                    department='none'
                    internal_code='none'
                    salvage_value=0
                    owners = tmp_dict[group_id]['owner']
                    query = u"""INSERT INTO  account_asset_report_data
                    (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
                    income_value,capital_value,expense_value,final_value,initial_depr,income_depr,
                    expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,
                    serial,number,job,department,internal_code,salvage_value,group_id,car_number,car_vat,car_color,asset_type_name)
                    VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
                    ,'{21}','{22}','{23}','{24}','{25}',{26},{27},{28},{29},{30},{31},{32})
                    """.format(self.id,1,time.strftime('%Y-%m-%d'),'null',date,11,date,al['asset_opening'],
                               al['asset_add'],al['capital'],al['expense_value'],al['final_value'],al['initial_depr'],
                               al['income_depr'],al['expense_depr'],al['final_depr'],al['car_number'],al['car_vat'],al['car_color'],al['asset_type_name'],
                               self.report_id.id,account.id,obj_id.id
                               ,owners,branch_name,serial,number,job,department,internal_code,salvage_value,group_id,close_status,asset_type_name
                               )
#                     print ('query ',query)
                    self.env.cr.execute(query)
            else:
                datas = self._get_assets_lines(account,branch)
                print ('datas ',datas)
                parent_lines = []
                children_lines = defaultdict(list)
                for al in datas:
                    if al['parent_id']:
                        # print ('1231312131213===== ',al)
                        children_lines[al['parent_id']] += [al]
                    else:
                        parent_lines += [al]
                for al in parent_lines:
                    capital=0
                    cap_come_amount=0
                    chasset=self.env['account.asset'].browse(al['asset_id'])
                    if chasset.capital_value:
                        capital_line=self.env['account.asset.capital.line'].search([("asset_id", '=', chasset.id),("state", '=', "capital")])
                        for cap_lines in capital_line:
                            if cap_lines.date >= self.date_from and cap_lines.date <=self.date_to:
                                capital += cap_lines.capital_amount
                            elif cap_lines.date>self.date_to:
                                capital =0
                                cap_come_amount = 0
                            else:
                                cap_come_amount+=cap_lines.capital_amount
                    move_ex_val=0
                    salvage_value=0
                    if al['asset_method'] == 'linear' and al['asset_method_number']:  # some assets might have 0 depreciations because they dont lose value
                        asset_depreciation_rate = ('{:.2f} %').format((100.0 / al['asset_method_number']) * (12 / int(al['asset_method_period'])))
                    elif al['asset_method'] == 'linear':
                        asset_depreciation_rate = ('{:.2f} %').format(0.0)
                    else:
                        asset_depreciation_rate = ('{:.2f} %').format(float(al['asset_method_progress_factor']) * 100)
                    # if al['asset_id'] in (611,43788):
                        # print ('alalala++++++++++ ',al)
                    depreciation=0
#                     print ('aaas',al['asset_disposal_date'])
                    if not al['asset_disposal_date'] or \
                        (al['asset_disposal_date'] and al['asset_disposal_date']>self.date_from and al['depreciated_start']!=al['depreciation']):#al['depreciated_start']> al['depreciation'] and not Акталсан бол хасахгүй LV-2-8 ын хувьд дүнтэй, харин MV-TR-1-64 ны хувь C1 0 байх ёстой
#                         print ('al',al) al['depreciated_start']!=al['depreciation']) Бульдозер (PR734) 8188LV-2-7

                        depreciation= al['depreciation'] 
                    depreciation_opening = al['depreciated_start'] - depreciation#-al['depreciation'] Акталсан бол хасахгүй LV-2-8 ын хувьд дүнтэй, харин MV-TR-1-64 ны хувь C1 0 байх ёстой  
                    depreciation_closing = al['depreciated_end'] 
                    # if dep_close> 0:
                    #     depreciation_closing = al['depreciated_end'] - al['depreciation_value_end']
                    depreciation_minus = 0.0
                    # if al['asset_id'] in (611,661,43788):#,587,660):
                        # print ('depreciation_opening 1111 ',depreciation_opening)
                        # print ('al',al)
                        # print ('depreciation111 ',depreciation)
                    asset_opening = al['asset_original_value'] if al['max_date_before'] and al['max_date_before']<self.date_from else 0.0
                    asset_opening +=cap_come_amount
                    # print('asset_add',al['max_date_before'])
                    # print(s)
                    asset_add = 0.0 if al['max_date_before'] and al['max_date_before']<self.date_from else al['asset_original_value']
                        
                    asset_minus = 0.0
                    if al['asset_id'] in (611,587,1136,43788):
                        print ('asset_opening:::== ',asset_opening)
#                     print ('children_lines ',children_lines)
                    for child in children_lines[al['asset_id']]:
#                         if al['asset_id'] in (611,587,1136,43788):
                        print ('child' ,child)
                        depreciation_c=0
                        chasset=self.env['account.asset'].browse(child['asset_id'])
#                         if chasset.active:
    
                        if al['depreciated_start']> child['depreciation']: # and child['asset_disposal_date']:
                            depreciation_c= child['depreciation'] 
                        if al['asset_id'] in (611,43788):
                            print ('111587 ',child['depreciated_start'])
                            print ('depreciation_c ',depreciation_c)
                        depreciation_opening += child['depreciated_start'] - depreciation_c#- child['depreciation'] Акталсан бол хасахгүй LV-2-8
                        depreciation_closing += child['depreciated_end']
                        
                        asset_opening += child['asset_original_value'] if child['max_date_before'] else 0.0
                        # if chasset.modify_history_id and chasset.modify_history_id.type=='capitalization':
                        #     capital+= 0.0 if child['max_date_before'] else child['asset_original_value']
                        # else:
                        #     asset_add += 0.0 if child['max_date_before'] else child['asset_original_value']
#                     print ('asset_add ',asset_add)
#                     print ('asset_opening222== ',asset_opening)
                    if al['asset_id'] in (611,587,1136,660):
                        print ('depreciation_opening 2222 ',depreciation_opening)

                    depreciation_add = depreciation_closing - depreciation_opening
                    asset_closing = asset_opening + asset_add
        
                    if al['asset_state'] == 'close' and al['asset_disposal_date'] and al['asset_disposal_date'] <= fields.Date.to_date(self.date_to):
                        depreciation_minus = depreciation_closing
                        depreciation_closing = 0.0
                        asset_minus = asset_closing
                        asset_closing = 0.0
        
                    asset_gross = asset_closing - depreciation_closing
    #                 total = [x + y for x, y in zip(total, [asset_opening, asset_add, asset_minus, asset_closing, depreciation_opening, depreciation_add, depreciation_minus, depreciation_closing, asset_gross])]
        
                    if al['asset_id'] in (631,661,1136,377):
                        print ('depreciation_opening=== ',depreciation_opening)
    #                 id = "_".join([self._get_account_group(al['account_code'])[0], str(al['asset_id'])])
                    name = str(al['asset_name'])
                    asset = self.env['account.asset'].browse(al['asset_id'])
                    owners='none'
                    branch_name='none'
                    serial='none'
                    number='none'
                    job='none'
                    department='none'
                    close_status ='none'
                    car_number = 'none'
                    car_vat = 'none'
                    car_color = 'none'
                    date_mw=al['asset_acquisition_date']
                    asset_type_name='none'
                    if asset.acquisition_date:
                        date_mw=asset.acquisition_date
                    internal_code='none'
                    if hasattr(asset, 'owner_id') and asset.owner_id:  
                        owners=''
                        for o in asset.owner_id:
                            owners+=o.name+', '
                    if asset.owner_id:
                        owners=asset.owner_id.name
                        if asset.owner_id.employee_ids and asset.owner_id.employee_ids[0].job_id:
                            job=asset.owner_id.employee_ids[0].job_id.name
                    if asset.owner_department_id:
                        department=asset.owner_department_id.name
                    if asset.location_id:
                        branch_name= asset.location_id.name
                    if asset.car_number:
                        car_number= asset.car_number
                    if asset.car_vat:
                        car_vat= asset.car_vat
                    if asset.car_color:
                        car_color= asset.car_color
                    if asset.serial:
                        serial=asset.serial
                    if asset.close_status == 'sell':
                        close_status = 'Борлуулсан'
                    elif asset.close_status == 'dispose':
                        close_status = 'Актласан'
                    elif asset.close_status == 'not_state':
                        close_status = ' '
                    if asset.asset_type_id:
                        asset_type_name = asset.asset_type_id.name
                    if hasattr(asset, 'old_code') and asset.old_code:  
                        internal_code=asset.old_code
#                         88102061
    #             print 'category------ ',category.name
                    query = u"""INSERT INTO  account_asset_report_data
                    (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
                    income_value,capital_value,expense_value,final_value,initial_depr,income_depr,
                    expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,
                    serial,number,job,department,internal_code,salvage_value,close_status,car_number,car_vat,car_color,asset_type_name)
                    VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
                    ,'{21}','{22}','{23}','{24}','{25}',{26},'{27}','{28}','{29}','{30}','{31}')
                    """.format(self.id,1,time.strftime('%Y-%m-%d'),al['asset_id'],al['asset_date'],1,date_mw,asset_opening,
                               asset_add,capital,asset_minus+move_ex_val,asset_opening+asset_add+capital-(asset_minus+move_ex_val)-salvage_value,
                               depreciation_opening,depreciation_add,depreciation_minus,depreciation_opening+depreciation_add-depreciation_minus,self.report_id.id,account.id,obj_id.id
                               ,owners,branch_name,serial,number,job,department,internal_code,salvage_value,close_status,car_number,car_vat,car_color,asset_type_name
                               )
                    
    #                     {'name': self.format_value(asset_opening), 'no_format_name': asset_opening},  # Assets
    #                     {'name': self.format_value(asset_add), 'no_format_name': asset_add},
    #                     {'name': self.format_value(asset_minus), 'no_format_name': asset_minus},
    #                     {'name': self.format_value(asset_closing), 'no_format_name': asset_closing},
    #                     {'name': self.format_value(depreciation_opening), 'no_format_name': depreciation_opening},  # Depreciation
    #                     {'name': self.format_value(depreciation_add), 'no_format_name': depreciation_add},
    #                     {'name': self.format_value(depreciation_minus), 'no_format_name': depreciation_minus},
    #                     {'name': self.format_value(depreciation_closing), 'no_format_name': depreciation_closing},
    #                     {'name': self.format_value(asset_gross), 'no_format_name': asset_gross},  # Gross
                    
                    self.env.cr.execute(query)
            

    def _sql_get_line_for_report(self, type_l, report_object=None):
#        print 'a111'
        if self.is_group:
            query = """SELECT
                        d.*,'null' as code,g.name,0 as method_number      
                    FROM
                        account_asset_report_data d 
                        left join 
                        account_asset_group g on d.group_id=g.id
                    WHERE
                        report_id = %s
                    ORDER BY
                        asset_id
                    """            
        else:
            query = """SELECT
                        d.*,a.code,a.name,a.method_number      
                    FROM
                        account_asset_report_data d 
                        left join 
                        account_asset a on d.asset_id=a.id
                    WHERE
                        report_id = %s
                    ORDER BY
                        asset_id
                    """
        params = [
#             self.type, self.type, self.type, self.type, self.type, self.type,
            self.report_id.id,
#             True if report_object is None else False,
#             report_object,
#             type_l
        ]

        self.env.cr.execute(query, tuple(params))
        result  = self.env.cr.dictfetchall()   
#         print 'result ',result
        return result   
    
    def _sql_get_total_for_report(self, type_l, report_object=None):
        
        query = """SELECT
                    sum(income_value) as income_value,
                    sum(income_depr) as income_depr,
                    sum(final_value) as final_value,
                    sum(initial_value) as initial_value,
                    sum(capital_value) as capital_value,
                    sum(initial_depr) as initial_depr,
                    sum(expense_depr) as expense_depr,
                    sum(expense_value) as expense_value,
                    sum(final_depr) as final_depr,
                    sum(income_value) as income_value,
                    sum(income_value) as income_value,
                    sum(salvage_value) as salvage_value,
                    '' as date,
                    '' as code,'Total' as name     
                FROM
                    account_asset_report_data 
                WHERE
                    report_id = %s
                """
        params = [
#             self.type, self.type, self.type, self.type, self.type, self.type,
            self.report_id.id,
#             True if report_object is None else False,
#             report_object,
#             type_l
        ]

        self.env.cr.execute(query, tuple(params))
        result  = self.env.cr.dictfetchall()   
#         print 'result ',result
        return result   

    def _format_total(self):
        if not self.company_currency_id:
            return
        lines = self.report_id.line_total_ids + self.report_id.line_super_total_id
        for line in lines:
            line.write({
                'debit': self.company_currency_id.round(line.debit) + 0.0,
                'credit': self.company_currency_id.round(line.credit) + 0.0,
                'balance': self.company_currency_id.round(line.balance) + 0.0,
                'current': self.company_currency_id.round(line.current) + 0.0,
                'age_30_days': self.company_currency_id.round(line.age_30_days) + 0.0,
                'age_60_days': self.company_currency_id.round(line.age_60_days) + 0.0,
                'age_90_days': self.company_currency_id.round(line.age_90_days) + 0.0,
                'age_120_days': self.company_currency_id.round(line.age_120_days) + 0.0,
                'older': self.company_currency_id.round(line.older) + 0.0,
            })
