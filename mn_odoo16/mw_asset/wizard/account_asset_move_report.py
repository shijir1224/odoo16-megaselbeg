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

class AccountAssetMoveLedgerReport(models.TransientModel):
    _name = 'account.asset.report.move.ledger.report'

    name = fields.Char()
    report_ids = fields.One2many('account.asset.report.move.ledger', 'report_id')
    report_name = fields.Char()
#     line_total_ids = fields.Many2many('account.report.move.ledger.line', relation='table_move_report_line_total')
#     line_super_total_id = fields.Many2one('account.report.move.ledger.line')
    print_time = fields.Char()
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
    report_object_ids = fields.One2many('account.asset.report.move.object', 'report_id')

class AccountAssetMoveObject(models.TransientModel):
    '''Тайлангийн ангилал буюу Ажилтнаар, ангилалаар, агуулахаар, байрлалаар гм бүлэглэх
    '''
    _name = 'account.asset.report.move.object'
    _order = 'name, id'

    name = fields.Char()
    object_id = fields.Integer()
    report_id = fields.Many2one('account.asset.report.move.ledger.report')
#     line_ids = fields.One2many('account.report.move.ledger.line', 'report_object_id')
    account_id = fields.Many2one('account.account', 'Account')
#     category_id = fields.Many2one('account.asset.category', 'Category')
#     partner_id = fields.Many2one('res.partner', 'Partner')
    branch_id = fields.Many2one('res.branch', 'Branch')
#     analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')


class AccountmoveLedger(models.TransientModel):
    _name = 'account.asset.report.move.ledger'
    _description = 'Account move Ledger'


    name = fields.Char(default=u'Үндсэн хөрөнгийн хөдөлгөөний тайлан /Ангиллаар/')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
#     journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id)]),
#                                    help='Select journal, for the Open Ledger you need to set all journals.')
    date_from = fields.Date(string='Эхлэх огноо', help='Use to compute initial balance.')
    date_to = fields.Date(string='Дуусах огноо', help='Use to compute the entrie matched with futur.')
    report_name = fields.Char('Report Name')
    report_id = fields.Many2one('account.asset.report.move.ledger.report')
    branch_ids = fields.Many2many('res.branch', relation='table_move_report_asset_branches', string="Салбарууд")
    
#     owner_emp_id = fields.Many2one('hr.employee', 'Owner')
    owner_emp_ids = fields.Many2many('hr.employee', relation='table_move_report_asset_emps',string="Эзэмшигчид")
    
    is_owner = fields.Boolean('Is owner report.', default=False)
    is_group = fields.Boolean('Is group.', default=False)

    account_ids = fields.Many2many('account.account', relation='table_move_report_asset_accounts',string="Дансууд")
    
    is_all_branch = fields.Boolean(u'Бүх салбар сонгох', default=False)
    is_all_account = fields.Boolean(u'Бүх данс сонгох', default=False)

    dep_ids = fields.Many2many('hr.department', relation='table_move_report_asset_deps')

    is_not_cost = fields.Boolean(u'Өртөггүй татах?', default=False)
    
    @api.onchange('is_all_branch')
    def onchange_is_all_branch(self):
        if self.is_all_branch:
            self.branch_ids = self.env['res.branch'].search([])
        else:
            self.branch_ids = False
            

    @api.onchange('is_all_account')
    def onchange_is_all_account(self):
        if self.is_all_account:
            self.account_ids = self.env['account.account'].search([('asset_model','!=',False)])
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
        graph_res = mod_obj.get_object_reference('account_asset_standard_report', 'account_asset_move_report_data_graph_date_cash_basis')
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
#        return self.env['report'].get_action(self, 'account_asset_move_report.report_account_asset_move_excel')
        return self.env.ref('account_asset_standard_report.action_asset_move_excel').report_action(self)

    def _get_name_report(self):
        report_name = 'asset detail report'
        return report_name

    def _owner_where(self):
        where=''
#         if self.owner_emp_id:
#             query = """select asset_id from asset_owner_emp_rel where emp_id = {0}""".format(self.owner_emp_id.id)
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
#         if self.owner_emp_id:
#             where = """ AND asset.owner_emp_id = {0} """.format(self.owner_emp_id.id)
        if self.owner_emp_ids:
#             dep_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
            
            if len(self.owner_emp_ids)==1:
                where += " and asset.owner_emp_id  = %s " %self.owner_emp_ids[0].id
            if len(self.owner_emp_ids)>1:
                where = " and asset.owner_emp_id in ("+','.join(map(str,self.owner_emp_ids.ids))+") "
                                        
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
        query = """,(select name from hr_department where id =aca.owner_dep_id
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
        if branch:
            branch_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
        if self.dep_ids:
#             dep_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
            
            if len(self.dep_ids)==1:
                dep_where += " and asset.owner_dep_id  = %s " %self.dep_ids[0].id
            if len(self.dep_ids)>1:
                dep_where = " and asset.owner_dep_id in ("+','.join(map(str,self.dep_ids.ids))+") "
                                        
#                     2020 оны 12 сард аваад элэгдэл нь 2021 1 сараас эхэлж байвал эхний үлдэргдэл биш орлого дээр тусаж байгааг засах.
#                        CASE WHEN asset.acquisition_date notnull and asset.acquisition_date <= %(date_from)s
#                        then asset.acquisition_date else max_date_before.date end  as max_date_before, 
#                        --max_date_before.date as max_date_before,

        sql = """
                SELECT asset.id as asset_id,
                       asset.parent_id as parent_id,
                       asset.name as asset_name,
                       asset.book_value as asset_value,
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
                       account.code as account_code,
                       account.name as account_name,
                       account.id as account_id,
                       COALESCE(first_move.asset_depreciated_value, move_before.asset_depreciated_value, 0.0) as depreciated_start,
                       COALESCE(first_move.asset_remaining_value, move_before.asset_remaining_value, 0.0) as remaining_start,
                       COALESCE(last_move.asset_depreciated_value, move_before.asset_depreciated_value, 0.0) as depreciated_end,
                       COALESCE(last_move.asset_remaining_value, move_before.asset_remaining_value, 0.0) as remaining_end,
                       COALESCE(first_move.amount_total, 0.0) as depreciation
                FROM account_asset as asset
                LEFT JOIN account_account as account ON asset.account_asset_id = account.id
                LEFT OUTER JOIN (SELECT MIN(date) as date, asset_id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s {where_account_move} GROUP BY asset_id) min_date_in ON min_date_in.asset_id = asset.id
                LEFT OUTER JOIN (SELECT MAX(date) as date, asset_id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s {where_account_move} GROUP BY asset_id) max_date_in ON max_date_in.asset_id = asset.id
                LEFT OUTER JOIN (SELECT MAX(date) as date, asset_id FROM account_move WHERE date <= %(date_from)s {where_account_move} GROUP BY asset_id) max_date_before ON max_date_before.asset_id = asset.id
                LEFT OUTER JOIN account_move as first_move ON first_move.id = (SELECT m.id FROM account_move m WHERE m.asset_id = asset.id AND m.date = min_date_in.date  {where_account_move} ORDER BY m.id ASC LIMIT 1)
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
                ORDER BY account.code;
            """.format(where_account_move=where_account_move,owner_where=owner_where,branch_where=branch_where,dep_where=dep_where)
# asset.company_id in %(company_ids)s
        date_to = self.date_to
        date_from = self.date_from
#         company_ids = tuple(t['id'] for t in self._get_options_companies(options))
#         print ('sql===123: ',sql)
        self.flush()
        self.env.cr.execute(sql, {'date_to': date_to, 'date_from': date_from, 'account_id': account.id})
        results = self.env.cr.dictfetchall()
#         print ('results ',results)
        return results        
    
    

    def _get_assets_move_lines(self, account,branch):
        where_account_move = ""
#         if options.get('all_entries') is False:
        where_account_move += " AND state = 'posted'"
#         owner_where=self._owner_where()
        owner_where=''
        if len(self.owner_emp_ids)==1:
            owner_where += " and to_emp_id  = %s " %self.owner_emp_ids[0].id
        if len(self.owner_emp_ids)>1:
            owner_where = " and to_emp_id in ("+','.join(map(str,self.owner_emp_ids.ids))+") "

        branch_where=''
        dep_where=''
        if branch:
            branch_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
        if self.dep_ids:
            if len(self.dep_ids)==1:
                dep_where += " and asset.owner_dep_id  = %s " %self.dep_ids[0].id
            if len(self.dep_ids)>1:
                dep_where = " and asset.owner_dep_id in ("+','.join(map(str,self.dep_ids.ids))+") "
        sql = """select h.name as asset_id,h.date,asset.original_value as asset_original_value
                from account_asset_move_history h left join account_asset asset on asset.id=h.name
                WHERE h.date BETWEEN %(date_from)s AND %(date_to)s
                AND asset.state not in ('model', 'draft')
                AND asset.asset_type = 'purchase'
                AND account_asset_id=%(account_id)s
                {owner_where}
                {branch_where}
                {dep_where}
                ORDER BY account_asset_id;
            """.format(owner_where=owner_where,branch_where=branch_where,dep_where=dep_where)
# asset.company_id in %(company_ids)s
        date_to = self.date_to
        date_from = self.date_from
#         company_ids = tuple(t['id'] for t in self._get_options_companies(options))
        print ('sql===1234: ',sql)
        self.flush()
        self.env.cr.execute(sql, {'date_to': date_to, 'date_from': date_from, 'account_id': account.id})
        results = self.env.cr.dictfetchall()
        print ('results ',results)
        return results            
    
    
    def _get_assets_move_ex_lines(self, account,branch):
        where_account_move = ""
#         if options.get('all_entries') is False:
        where_account_move += " AND state = 'posted'"
#         owner_where=self._owner_where()
        owner_where=''
        if len(self.owner_emp_ids)==1:
            owner_where += " and from_emp_id  = %s " %self.owner_emp_ids[0].id
        if len(self.owner_emp_ids)>1:
            owner_where = " and from_emp_id in ("+','.join(map(str,self.owner_emp_ids.ids))+") "

        branch_where=''
        dep_where=''
        if branch:
            branch_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
        if self.dep_ids:
#             dep_where =' AND (asset.branch_id={0} or asset.branch_id isnull)'.format(branch.id) 
            
            if len(self.dep_ids)==1:
                dep_where += " and asset.owner_dep_id  = %s " %self.dep_ids[0].id
            if len(self.dep_ids)>1:
                dep_where = " and asset.owner_dep_id in ("+','.join(map(str,self.dep_ids.ids))+") "
                                        
#                     2020 оны 12 сард аваад элэгдэл нь 2021 1 сараас эхэлж байвал эхний үлдэргдэл биш орлого дээр тусаж байгааг засах.
#                        CASE WHEN asset.acquisition_date notnull and asset.acquisition_date <= %(date_from)s
#                        then asset.acquisition_date else max_date_before.date end  as max_date_before, 
#                        --max_date_before.date as max_date_before,

        sql = """select h.name as asset_id,h.date ,asset.original_value as  asset_original_value,h.id as h_id 
                from account_asset_move_history h left join account_asset asset on asset.id=h.name
                WHERE h.date BETWEEN %(date_from)s AND %(date_to)s
                AND asset.state not in ('model', 'draft')
                AND asset.asset_type = 'purchase'
                AND account_asset_id=%(account_id)s
                {owner_where}
                {branch_where}
                {dep_where}
                ORDER BY account_asset_id;
            """.format(owner_where=owner_where,branch_where=branch_where,dep_where=dep_where)
# asset.company_id in %(company_ids)s
        date_to = self.date_to
        date_from = self.date_from
#         company_ids = tuple(t['id'] for t in self._get_options_companies(options))
        print ('sql===1235: ',sql)
        self.flush()
        self.env.cr.execute(sql, {'date_to': date_to, 'date_from': date_from, 'account_id': account.id})
        results = self.env.cr.dictfetchall()
        print ('results222 ',results)
        return results                
    
    def _pre_compute(self):
        print ('444444')
        vals = {'report_name': self._get_name_report(),
                'name': self._get_name_report(),
                'date_to': self.date_to if self.date_to else "2099-01-01",
                'date_from': self.date_from if self.date_from else "1970-01-01",
                }
        self.report_id = self.env['account.asset.report.move.ledger.report'].create(vals)
        
#        print 'self.category_ids.ids ',self.category_ids.ids
        first_capital_dict={}
        
        branch_loop=[]
        if self.branch_ids:
            branch_loop=self.branch_ids
        else:
            branch_loop=[False]
#         for branch in self.branch_ids:
        for branch in branch_loop:
#          print ('branch ',branch.name)
#          for category in self.category_ids:
           for account in self.account_ids:
            obj_vals = {
                'name':'categ',
                'object_id':account.id,
                'branch_id':branch and branch.id or False,
#                 'category_id':category.id,
                'account_id':account.id,
                'report_id':self.report_id.id
                }
            obj_id=self.env['account.asset.report.move.object'].create(obj_vals)
                         
            datas = self._get_assets_lines(account,branch)
            move_in_datas = self._get_assets_move_lines(account,branch)
            move_ex_datas = self._get_assets_move_ex_lines(account,branch)
            if not self.is_group:
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
                    depreciation=0
#                     print ('aaas',al['asset_disposal_date'])
                    if not al['asset_disposal_date']:#al['depreciated_start']> al['depreciation'] and not Акталсан бол хасахгүй LV-2-8 ын хувьд дүнтэй, харин MV-TR-1-64 ны хувь C1 0 байх ёстой
#                         print ('al',al)
                        depreciation= al['depreciation'] 
                    depreciation_opening = al['depreciated_start'] - depreciation#-al['depreciation'] Акталсан бол хасахгүй LV-2-8 ын хувьд дүнтэй, харин MV-TR-1-64 ны хувь C1 0 байх ёстой  
                    depreciation_closing = al['depreciated_end']
                    depreciation_minus = 0.0
                    if al['asset_id'] in (631,661,1136,377):
                        print ('depreciation_opening 1111 ',depreciation_opening)
                    asset_opening = al['asset_original_value'] if al['max_date_before'] else 0.0
                    asset_add = 0.0 if al['max_date_before'] else al['asset_original_value']
                    asset_minus = 0.0
#                     print ('asset_opening:::== ',asset_opening)
#                     print ('children_lines ',children_lines)
                    for child in children_lines[al['asset_id']]:
#                         print ('child' ,child)
                        depreciation_c=0
                        if al['depreciated_start']> child['depreciation'] and child['asset_disposal_date']:
                            depreciation_c= child['depreciation'] 
                        
                        depreciation_opening += child['depreciated_start'] - depreciation_c#- child['depreciation'] Акталсан бол хасахгүй LV-2-8
                        depreciation_closing += child['depreciated_end']
        
                        asset_opening += child['asset_original_value'] if child['max_date_before'] else 0.0
                        chasset=self.env['account.asset'].browse(child['asset_id'])
                        if chasset.modify_history_id and chasset.modify_history_id.type=='capitalization':
                            capital+= 0.0 if child['max_date_before'] else child['asset_original_value']
                        else:
                            asset_add += 0.0 if child['max_date_before'] else child['asset_original_value']
#                     print ('asset_add ',asset_add)
#                     print ('asset_opening222== ',asset_opening)
                    depreciation_add = depreciation_closing - depreciation_opening
                    asset_closing = asset_opening + asset_add
        
                    if al['asset_state'] == 'close' and al['asset_disposal_date'] and al['asset_disposal_date'] <= fields.Date.to_date(self.date_to):
                        depreciation_minus = depreciation_closing
                        depreciation_closing = 0.0
                        asset_minus = asset_closing
                        asset_closing = 0.0
        
                    asset_gross = asset_closing - depreciation_closing
                    name = str(al['asset_name'])
                    asset = self.env['account.asset'].browse(al['asset_id'])
                    owners='none'
                    branch_name='none'
                    serial='none'
                    number='none'
                    job='none'
                    department='none'
                    internal_code='none'
                    if asset.owner_emp_id:
                        owners=asset.owner_emp_id.name
                    if asset.original_move_line_ids:
                        job =asset.original_move_line_ids.filtered(lambda r: r.partner_id!=False) and \
                                    asset.original_move_line_ids.filtered(lambda r: r.partner_id!=False)[0].partner_id.name\
                                    or ''

                    if asset.owner_dep_id:
                        department=asset.owner_dep_id.name
                    if asset.branch_id:
                        branch_name= asset.branch_id.name
    #             print 'category------ ',category.name
                    type='Орлого'
                    if asset_add>0 or asset_minus:
                        too=1
                        if asset_minus!=0:
                            too=-1
                            type='Зарлага'
                        move_inc=0
                        move_ex=0
    
                        query = u"""INSERT INTO  account_asset_move_report_data
                        (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
                        income_value,move_inc_value,expense_value,move_exp_value,initial_depr,income_depr,
                        expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,
                        serial,number,job,department,internal_code,salvage_value,type)
                        VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
                        ,'{21}','{22}','{23}','{24}','{25}',{26},'{27}')
                        """.format(self.id,1,time.strftime('%Y-%m-%d'),al['asset_id'],al['asset_date'],too,al['asset_acquisition_date'],asset_opening,
                                   asset_add,move_inc,asset_minus+move_ex_val,move_ex,
                                   depreciation_opening,depreciation_add,depreciation_minus,depreciation_opening+depreciation_add-depreciation_minus,self.report_id.id,account.id,obj_id.id
                                   ,owners,branch_name,serial,number,job,department,internal_code,salvage_value,type
                                   )
                        
                        self.env.cr.execute(query)
            #Шилжлит орлого
                for l in move_in_datas:
                    print ('llllllll222 ',l)
                    capital=0
                    move_ex_val=0
                    asset_add=0
                    name = str(al['asset_name'])
                    asset = self.env['account.asset'].browse(l['asset_id'])
                    owners='none'
                    branch_name='none'
                    serial='none'
                    number='none'
                    job='none'
                    department='none'
                    internal_code='none'
                    if asset.owner_emp_id:
                        owners=asset.owner_emp_id.name
                    if asset.owner_dep_id:
                        department=asset.owner_dep_id.name
                    if asset.branch_id:
                        branch_name= asset.branch_id.name
    #             print 'category------ ',category.name
                    asset_add=l['asset_original_value']
                    print ('asset_add123: ',asset_add)
                    if asset.original_move_line_ids:
                        job =asset.original_move_line_ids.filtered(lambda r: r.partner_id!=False) and \
                                    asset.original_move_line_ids.filtered(lambda r: r.partner_id!=False)[0].partner_id.name\
                                    or ''
                    
                    if asset_add:
                        too=-1
                        move_inc=0
                        move_ex=asset_minus
                        type='Хөдөлгөөн орлого'
                        query = u"""INSERT INTO  account_asset_move_report_data
                        (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
                        income_value,move_inc_value,expense_value,move_exp_value,initial_depr,income_depr,
                        expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,type)
                        VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
                        ,'{21}')
                        """.format(self.id,1,time.strftime('%Y-%m-%d'),l['asset_id'],l['date'].strftime('%Y-%m-%d'),too,l['date'].strftime('%Y-%m-%d'),0,
                                   asset_add,move_inc,asset_minus,move_ex,
                                   depreciation_opening,depreciation_add,depreciation_minus,depreciation_opening+depreciation_add-depreciation_minus,self.report_id.id,account.id,obj_id.id
                                   ,owners,branch_name,type
                                   )
                        print ('query ',query)
                        self.env.cr.execute(query)  
            #Шилжлит зарлага
                for l in move_ex_datas:
                    print ('llllllllex ',l)
                    capital=0
                    move_ex_val=0
                    asset_add=0
                    name = str(al['asset_name'])
                    asset = self.env['account.asset'].browse(l['asset_id'])
                    history = self.env['account.asset.move.history'].browse(l['h_id'])
                    owners='none'#харилцагч
                    branch_name='none'
                    serial='none'
                    number='none'
                    job='none'
                    department='none'
                    internal_code='none'
#                     if asset.owner_emp_id:
#                         owners=asset.owner_emp_id.name
                    if history and history.from_emp_rp_id:
                        owners=history.from_emp_rp_id.name      
                                          
                    if asset.original_move_line_ids:
                        job =asset.original_move_line_ids.filtered(lambda r: r.partner_id!=False) and \
                                    asset.original_move_line_ids.filtered(lambda r: r.partner_id!=False)[0].partner_id.name\
                                    or ''
                        
                    if asset.owner_dep_id:
                        department=asset.owner_dep_id.name
                    if asset.branch_id:
                        branch_name= asset.branch_id.name
    #             print 'category------ ',category.name
                    asset_minus=l['asset_original_value']
                    if asset_minus:
                        too=-1
                        move_inc=0
                        move_ex=asset_minus
                        type='Хөдөлгөөн зарлага'
                        query = u"""INSERT INTO  account_asset_move_report_data
                        (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
                        income_value,move_inc_value,expense_value,move_exp_value,initial_depr,income_depr,
                        expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,type)
                        VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
                        ,'{21}')
                        """.format(self.id,1,time.strftime('%Y-%m-%d'),l['asset_id'],l['date'].strftime('%Y-%m-%d'),too,l['date'].strftime('%Y-%m-%d'),0,
                                   asset_add,move_inc,asset_minus,move_ex,
                                   depreciation_opening,depreciation_add,depreciation_minus,depreciation_opening+depreciation_add-depreciation_minus,self.report_id.id,account.id,obj_id.id
                                   ,owners,branch_name,type
                                   )
                        print ('query ',query)
                        self.env.cr.execute(query)                                    
            else:
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
                    depreciation_minus = 0.0
        
                    asset_opening = al['asset_original_value'] if al['max_date_before'] else 0.0
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
                    if asset.owner_emp_id:
                        owners=asset.owner_emp_id.name
                    if asset.owner_dep_id:
                        department=asset.owner_dep_id.name
                    if asset.branch_id:
                        branch_name= asset.branch_id.name
                    tmp = {'asset_id':al['asset_id'],
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
#                             'owner':owners,
                            'branch':branch_name,
                            'serial':serial,
                            'number':number,
                            'job':job,
                            'department':department,
                            'internal_code':internal_code,
                            'salvage_value':salvage_value
                           }
#                     if list(filter(lambda o : o['group_id']==al['group_id'], all_datas)):
#                         list(filter(lambda o : o['group_id']==al['group_id'], all_datas))[0]['owner']+=', '+owners
#                     else:
#                          tmp.update({'owner':owners})
                    # if tmp_dict.get(al['group_id'],False):
                    #     if tmp_dict[al['group_id']].get('owner',False):
                    #         tmp_dict[al['group_id']]['owner'] +=', '+owners
                    #     else:
                    #         tmp_dict[al['group_id']]={'owner':owners}
                    # else:
                    #         tmp_dict[al['group_id']]={'owner':owners}
                            
                    all_datas.append(tmp)
#                 print ('all_datas11111 ',all_datas)
#                 print ('tmp_dict ',tmp_dict)
                df = pandas.DataFrame(all_datas)
                result = df.groupby(['date'])['asset_opening', 'asset_add','capital','expense_value','final_value','initial_depr','income_depr','expense_depr','final_depr'].sum()
#                 print ('ttt ',result)
                for i,al in result.iterrows():
                    print ('iii ',i)
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
                    move_inc=0
                    move_ex=0
                    query = u"""INSERT INTO  account_asset_move_report_data
                    (wizard_id, create_uid, create_date, asset_id, first_depr_date, qty, date, initial_value,
                    income_value,move_inc_value,expense_value,move_exp_value,initial_depr,income_depr,
                    expense_depr,final_depr,report_id,account_id,report_obj_id,owner,branch,
                    serial,number,job,department,internal_code,salvage_value,group_id)
                    VALUES({0},{1},'{2}',{3},'{4}',{5},'{6}',{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},'{19}','{20}'
                    ,'{21}','{22}','{23}','{24}','{25}',{26},{27})
                    """.format(self.id,1,time.strftime('%Y-%m-%d'),'null',date,11,date,al['asset_opening'],
                               al['asset_add'],move_inc,al['expense_value'],move_ex,al['initial_depr'],
                               al['income_depr'],al['expense_depr'],al['final_depr'],
                               self.report_id.id,account.id,obj_id.id
                               ,owners,branch_name,serial,number,job,department,internal_code,salvage_value,group_id
                               )
#                     print ('query ',query)
                    self.env.cr.execute(query)

            

    def _sql_get_line_for_report(self, type_l, report_object=None):
#        print 'a111'
        if self.is_group:
            query = """SELECT
                        d.*,'null' as code,g.name,0 as method_number      
                    FROM
                        account_asset_move_report_data d 
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
                        account_asset_move_report_data d 
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
#         move_inc_value,expense_value,move_exp_value,
        query = """SELECT
                    sum(income_value) as income_value,
                    sum(move_inc_value) as move_inc_value,
                    sum(move_exp_value) as move_exp_value,
                    sum(initial_value) as initial_value,
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
                    account_asset_move_report_data 
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
