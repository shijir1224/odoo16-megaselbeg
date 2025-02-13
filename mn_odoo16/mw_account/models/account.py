# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.osv import expression

class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account"

    def _compute_data(self):
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) " \
                       "- COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit"
        }
        cr = self.env.cr
#         children_and_consolidated = self._get_children_and_consol()
        accounts = {}
        accounts2 = {}
        sums = {}
        sums2 = {}
        check_initial = True
        field_names=['debit', 'credit', 'balance']
#         if children_and_consolidated:
        context = dict(self._context or {})
#         print ('context+++++++++:  ',context)
        MoveLine = self.env['account.move.line']
        tables, where_clause, where_params = MoveLine._query_get()
        # print 'where_params ',where_params
#             params = (tuple(children_and_consolidated),) + tuple(where_params)
        # print 'self',self.ids
        params =  (tuple(self.ids),) + tuple(where_params)
#            Тайлант хугацаа
        
#             aml_query = self.env['account.move.line')._query_get(cr, uid, context=context)
        partner_where=""
        partner_id=context.get('partner_id',False) 
        if partner_id:
            partner_where=" AND l.partner_id={0} ".format(partner_id)
        wheres = [""]
#         print ('partner_where ',partner_where)
        if where_clause.strip():
            wheres.append(where_clause.strip())

#            Эцсийн үлдэгдэл
        filters = " AND ".join(wheres)
        # print ('wheres------------- ',wheres)
        # print ('params ',params)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        filters = filters.replace('l__account_id', 'a')
#             logger.debug('addons.'+account_obj._name, netsvc.LOG_DEBUG,
#                                       'Filters: %s'%filters)
#         _logger.info('addons.'+str(self.ids)+'Filters: %s'%filters)
        # print ('filters ',filters)
        request = ("SELECT a.id as id, " +\
                   ', '.join(map(mapping.__getitem__, field_names)) +
                   " FROM account_move_line l left join " \
                   "       account_move m on l.move_id=m.id left join " \
                   "       account_account a on l.account_id=a.id " \
                   " WHERE a.id IN %s " \
                        + filters +" "+ partner_where+
                   " GROUP BY a.id")
        self.env.cr.execute(request, params)

        for res in self.env.cr.dictfetchall():
            accounts[res['id']] = res
#            Эхний үлдэгдэл. Өмнөх жилийн Хаалт хийсэн бөгөөд тайлангийн эхний огноо
#             жилийн эхний огноотой давхцаж байвал.
#                 
# #            Зөвхөн эхний үлдэгдлийн бичилтийг шүүх
#         1031
#         if self.user_type_id.
        state=context.get('target_move',False) and context['target_move'] or context.get('state',False) and context['state'] or 'posted'
        date_from=context.get('date_from',False) and context['date_from'] or time.strftime('%Y-%m-%d')
        company_id=context.get('company_id',False) and context['company_id'] or self.env.user.company_id and self.env.user.company_id.id or 1
        if not isinstance(date_from, datetime.datetime):
            if isinstance(date_from,str):
                date_from=datetime.date(int(date_from.split('-')[0]),int(date_from.split('-')[1]),int(date_from.split('-')[2]))
        tables_start, where_clause_start, where_params_start = MoveLine.with_context(date_from=date_from, 
                                                                      state=state,
                                                                      date_to=False, strict_range=True, initial_bal=True)._query_get()
        params_start = (tuple(self.ids),) + tuple(where_params_start)
#            Тайлант хугацаа
#             print "self.env.context+++++++++++++++++ ",self.env.context
        
#             aml_query = self.env['account.move.line')._query_get(cr, uid, context=context)
        wheres_start = [""]
        if where_clause_start.strip():
            wheres_start.append(where_clause_start.strip())

        filters_start = " AND ".join(wheres_start)
        filters_start = filters_start.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        filters_start = filters_start.replace('l__account_id', 'a')
#             logger.debug('addons.'+account_obj._name, netsvc.LOG_DEBUG,
#                                       'Filters: %s'%filters)
#         _logger.info('addons.'+str(self.ids)+'filters_start: %s'%filters_start)
        request_start = ("SELECT a.id as id, " +\
                   ', '.join(map(mapping.__getitem__, field_names)) +
                   " FROM account_move_line l left join " \
                   "       account_move m on l.move_id=m.id  left join " \
                   "       account_account a on l.account_id=a.id " \
                   " WHERE l.account_id IN %s " \
                        + filters_start + " "+partner_where+
                   " GROUP BY a.id")
        field_names.append('starting_balance')
        self.env.cr.execute(request_start, params_start)
#             self.logger.notifyChannel('addons.'+account_obj._name, netsvc.LOG_DEBUG,
#                                       'Status: %s'%self.env.cr.statusmessage)
#             _logger.info('addons.'+self.name+'Status: %s'%self.env.cr.statusmessage)

        for res in self.env.cr.dictfetchall():
            accounts2[res['id']] = res

#             self.env.cr.execute(request_start, params)
# #            Шүүгдсэн дансны эхний үлдэгдлийн журналд бичигдсэн бичилтийг шүүх 
#         children_and_consolidated.reverse()
#         brs = list(self.browse(children_and_consolidated))
#             print "children_and_consolidated ",children_and_consolidated
        currency_obj = self.env['res.currency']
#         while brs:
#             current = brs.pop(0)
        for current in self:
            # print 'account---- ',current
            for fn in field_names:
#                    'starting_balance'-д balance ийн дүнг өгнө
                if fn=='starting_balance':
                    sums.setdefault(current.id, {})[fn] = accounts2.get(current.id, {}).get('balance', 0.0)
                else:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
#                 for child in current.child_id:
#                     if child.company_id.currency_id.id == current.company_id.currency_id.id:
#                         sums[current.id][fn] += sums[child.id][fn]
#                     else:
#                         sums[current.id][fn] += currency_obj.compute(cr, self._uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)
        res = {}
        #0.0 оор цэнэглэж {'credit': 0.0, 'balance': 0.0, 'debit': 0.0} хэлбэрийн dic үүсгэх
#        field_names.extend(report_fields)
        null_result = dict((fn, 0.0) for fn in field_names)
#         unaffected_earnings_type = self.env.ref("account.data_unaffected_earnings")
        earning_accounts=self.search([('account_type','=','equity_unaffected'),('company_id','=',company_id)])
#         print ('a',earning_accounts)
        if len(earning_accounts)!=1:
            raise UserError((u'Энэ компани дээр хуримтлагдсан ашиг төрөлтэй данс байхгүй эсвэл олон байна. Эсвэл компаний мэдээллээ буруу сонгосон байна'))
        earning_account=earning_accounts[0]
        for id in self.ids: 
            #earnings түр дансдын зөрүүгээр харуулдаг данс, хаах илүү үйлдэл хийхгүй.
            #Хэрэв 410100 данс дээр тайлант үед гүйлгээ гарсан бол дараагийн тайлант хугацаанд хэрхэн харуулахыг засах шаардлагатайм байна.
            #Ер нь бол өмнөх үеийнхруу бичүүлэх нь зөв байх.
            if id==earning_account.id:
                
#                            "    AND l.date < %s  AND  l.date >= %s " \
# date_from.split('-')[0]+'-01-01',
                #түр дансдын нийлбэр дүн гарна. Тиймээс өмнөх үеийн гүйлгээг энд бичхгүй байх.
                if state =='all':
                    state_where=' AND m.state in (\'draft\',\'posted\')'
                else:
                    state_where=' AND m.state=\'posted\''
#                 params3=(earning_account.id,earning_account.id,date_from.split('-')[0]+'-01-01',company_id)
                params3=(earning_account.id,earning_account.id,str(date_from.year)+'-01-01',company_id)
                request3 = ("SELECT %s as id, " +\
                           "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                           " FROM account_move_line l " \
                           "       left join account_move m "
                           "           on l.move_id=m.id " \
                           "       left join account_account a " \
                           "            on l.account_id = a.id " \
                           " WHERE l.account_id <> %s " \
                           "    AND a.include_initial_balance = FALSE " \
                           "    AND l.date < %s " \
                           "    AND l.company_id=%s " \
                           " "+state_where)
                self.env.cr.execute(request3, params3)
                for r in self.env.cr.dictfetchall():
                    sums[r['id']]['starting_balance'] = r['balance']
            #earnings
            res[id] = sums.get(id, null_result)
        for s in self:
            s.balance=res[s.id]['balance']+res[s.id]['starting_balance']
            s.balance_start=res[s.id]['starting_balance']
            s.debit=res[s.id]['debit']
            s.credit=res[s.id]['credit']
#             print ('s.code ',s.code)
#             print ('s.balance ',s.balance)
                        
    balance = fields.Float(compute='_compute_data', string='Balance')
    balance_start = fields.Float(compute='_compute_data', string='Balance start')
    debit = fields.Float(compute='_compute_data', string='Debit')
    credit = fields.Float(compute='_compute_data', string='Credit')
    code_group_id = fields.Many2one('account.code.type', string="Account group", copy=False)


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not name and self._context.get('partner_id') and self._context.get('move_type'):
            return self._order_accounts_by_frequency_for_partner(
                            self.env.company.id, self._context.get('partner_id'), self._context.get('move_type'))
        args = args or []
        domain = []
        if name:
            if operator in ('=', '!='):
                domain = ['|', ('code', '=', name), ('name', operator, name)]
            else:
                domain = ['|', ('code', '=ilike', name+ '%'), ('name', operator, name)]
            # if operator in expression.NEGATIVE_TERM_OPERATORS:
            #     domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
              
    @api.constrains('code')
    def _check_account_code(self):
        return()
        # for account in self:
        #     if not re.match(ACCOUNT_CODE_REGEX, account.code):
        #         raise ValidationError(_(
        #             "The account code can only contain alphanumeric characters and dots."
        #         ))
class AccountCodeType(models.Model):
    _name = 'account.code.type'
    _description = 'Account Type'
    _order = 'sequence,code'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    parent_id = fields.Many2one('account.code.type', string="Parent group", copy=False)
    root_id = fields.Many2one('account.code.root', compute='_compute_account_root', store=True)
    account_ids = fields.One2many('account.account', 'code_group_id', string='Accounts',)
    sequence = fields.Integer('Sequence')
    
    @api.depends('code')
    def _compute_account_root(self):
        for record in self:
            record.root_id = (ord(record.code[0]) * 1000 + ord(record.code[1:2] or '\x00')) if record.code else False


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|','|', ('name', '=ilike', '%' + name + '%'),  ('code', '=ilike', '%' + name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for account in self:
            if account.code:
                name = account.code + ' ' + account.name
            else:
                name = account.name
                
            result.append((account.id, name))
        return result
        
class AccountCodeRoot(models.Model):
    _name = 'account.code.root'
    _description = 'Account codes first 2 digits'
    _auto = False

    name = fields.Char()
    parent_id = fields.Many2one('account.code.root')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT DISTINCT ASCII(code) * 1000 + ASCII(SUBSTRING(code,2,1)) AS id,
                   LEFT(code,2) AS name,
                   ASCII(code) AS parent_id
            FROM account_code_type WHERE code IS NOT NULL
            UNION ALL
            SELECT DISTINCT ASCII(code) AS id,
                   LEFT(code,1) AS name,
                   NULL::int AS parent_id
            FROM account_code_type WHERE code IS NOT NULL
            )''' % (self._table,)
        )

            
