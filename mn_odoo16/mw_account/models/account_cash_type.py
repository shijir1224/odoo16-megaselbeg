from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression



class AccountCashMoveType(models.Model):
    _name = 'account.cash.move.type'
    _description = 'Cash Move Type'
    _rec_name = 'display_name'

    TYPE_SELECTION = [
        ('activities_income', 'Үндсэн үйл ажиллагааны мөнгөн орлого'),
        ('activities_expense', 'Үндсэн үйл ажиллагааны мөнгөн зарлага'),
        ('investing_income', 'Хөрөнгө оруулалтын үйл ажиллагааны мөнгөн орлого'),
        ('investing_expense', 'Хөрөнгө оруулалтын үйл ажиллагааны мөнгөн зарлага'),
        ('financing_income', 'Санхүүгийн үйл ажиллагааны мөнгөн орлого'),
        ('financing_expense', 'Санхүүгийн үйл ажиллагааны мөнгөн зарлага'),
        ('dummy', 'Бүх цэвэр мөнгөн гүйлгээ')
    ]


    display_name = fields.Char(string='Display Name', compute='_compute_display_name')



    INCOME_SELECTION = [
        ('income','Орлого'),
        ('expense','Зарлага'),
        (' ',' '),
    ]

    name = fields.Char('Name', size=100, required=True)
    group_name = fields.Selection(TYPE_SELECTION, 'Group', required=True)
    sequence = fields.Integer('Sequence', help="This sequence is used when generate statement of cash flows report. Sequence is ordered into the groups.")
    name_en = fields.Char('Name mn', size=100, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    is_income = fields.Selection(INCOME_SELECTION, 'TYPE', required=True)
    number = fields.Char('Number', size=10, required=True)
    bank_line_ids = fields.One2many('account.bank.statement.line', 'cash_type_id', string='Lines',)

    view_name = fields.Char('Code', size=100)


    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|','|', ('number', '=ilike', '%' + name + '%'),  ('view_name', '=ilike', '%' + name + '%'), ('name', operator, name)]
    #         if operator in expression.NEGATIVE_TERM_OPERATORS:
    #             domain = ['&', '!'] + domain[1:]
    #     accounts = self.search(domain + args, limit=limit)
    #     return accounts.name_get()
    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            display_name = ''
            if record.name:
                display_name = record.name
                record.display_name = display_name
                if record.view_name:
                    display_name = record.name + ' ' + record.view_name
                    record.display_name = display_name
            else:
                record.display_name = ' '





    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not name and self._context.get('partner_id') and self._context.get('move_type'):
            return self._order_accounts_by_frequency_for_partner(
                            self.env.company.id, self._context.get('partner_id'), self._context.get('move_type'))
        args = args or []
        domain = []
        if name:
            if operator in ('=', '!='):
                domain = ['|','|', ('number', '=ilike', '%' + name + '%'),  ('view_name', '=ilike', '%' + name + '%'), ('name', operator, name)]
            else:
                domain = ['|','|', ('number', '=ilike', '%' + name + '%'),  ('view_name', '=ilike', '%' + name + '%'), ('name', operator, name)]
                # if operator in expression.NEGATIVE_TERM_OPERATORS:
            #     domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.depends('name', 'number')
    def name_get(self):
        result = []
        for account in self:
            name = ''
            if account.view_name:
                name+= account.view_name + ' ' + account.name
            else:
                name+= account.name
            result.append((account.id, name))
        return result
class AccountCashSkipConf(models.Model):
    _name = 'account.cash.skip.conf'
    _description = 'Cash Move skip config'

    name = fields.Char('Name', size=100, required=True)
    skip_journal_ids = fields.Many2many('account.journal', relation='account_cash_flow_skip_journals')
    skip_cash_move_types = fields.Many2many('account.cash.move.type', string="Cash type")
    add_accounts = fields.Many2many('account.account', string="Accounts")
class AccountCashCheck(models.Model):
    _name = 'account.cash.move.check'
    _description = 'Cash Move Type Check'

    name = fields.Char('Name', size=100, required=True)
    bank_line_ids = fields.One2many('account.bank.statement.line', 'cash_type_id', string='Lines',)
    line_ids = fields.One2many('account.cash.move.check.line', 'parent_id', 'Мөр')
    null_line_ids = fields.One2many('account.cash.move.check.null.line', 'parent_id', 'Мөр хоосон')
    state = fields.Selection([('draft','Ноорог'),('done','Confirm')], 'state', default='draft')
    company_id = fields.Many2one('res.company', 'Company',required=True)


    def update(self):
        count=0
        for e in self:#.browse(ids):
            for l in e.account_line_ids:
                count+=1
#                print '-----------',count,'==',l.aml_credit_id.id
                if l.aml_credit_id.id:
#                     l.aml_credit_id.write({'credit':l.amount})
                    query = """
                            update account_move_line set credit={0} where id={1}""" .format(l.amount,l.aml_credit_id.id)
                    self.env.cr.execute(query)
                    self.env.cr.commit()
#                     query_result = cr.dictfetchall()
                if l.aml_debit_id.id:
#                     l.aml_debit_id.write({'debit':l.amount})
                    query = """
                            update account_move_line set debit={0} where id={1}""" .format(l.amount,l.aml_debit_id.id)
                    self.env.cr.execute(query)
                    self.env.cr.commit()
#                     query_result = cr.dictfetchall()
#         cr.commit()
        return True
    
    
    def compute(self):
        incomes = ('activities_income','investing_income', 'financing_income')
        expenses= ('activities_expense', 'investing_expense', 'financing_expense')

        for e in self:#.browse(cr,uid,ids):
            if not self.company_id.transfer_account_id:
                raise ValidationError((u'{0} Компани дээр касс харилцахын клиринг данс тохируулаагүй байна '.format(self.company_id.name)))
            categ_where=""
            warehouse_where=""
            query = """
                    select bl.id as bsl_id,cash_type_id,amount,is_income,group_name 
                    from account_bank_statement_line bl left join 
                        account_cash_move_type t on bl.cash_type_id=t.id  left join 
                        account_move am on bl.move_id = am.id
                    where is_income='expense' and amount>0 and bl.account_id<>{0} and am.company_id={1}
                    union 
                    select bl.id as bsl_id,cash_type_id,amount,is_income,group_name 
                    from account_bank_statement_line bl left join 
                        account_cash_move_type t on bl.cash_type_id=t.id  left join 
                        account_move am on bl.move_id = am.id
                    where is_income<>'expense' and amount<0 and bl.account_id<>{0} and am.company_id={1} """.format(self.company_id.transfer_account_id.id,self.company_id.id)

            # print ('query ',query)
            self._cr.execute(query)
            query_result = self._cr.dictfetchall()
#             print 'query_result ',query_result
            if  e.line_ids:
                raise ValidationError((u'Мөрүүд үүссэн байна'))
            
            for r in query_result:
                print ('rrr ',r)
                    
                line_pool=self.env['account.cash.move.check.line']
                line_pool.create({
                                                'name':r['bsl_id'],
#                                                'debit':r['debit'],
#                                                'credit':r['credit'],
                                                'amount': r['amount'],
#                                                 'unit_price': r['price_unit'],
                                                'parent_id':e.id,
#                                                 'account_id':debit_id,
                                                'cash_type_id':r['cash_type_id'],
                                                'bank_line_id':r['bsl_id'],
                                                'is_income':r['is_income'],
                                                       })
   
   
        return True
    
    def compute_null(self):
        incomes = ('activities_income','investing_income', 'financing_income')
        expenses= ('activities_expense', 'investing_expense', 'financing_expense')

        for e in self:#.browse(cr,uid,ids):
            categ_where=""
            warehouse_where=""
#             query = """
#                         select (debit-credit) as amount,debit,credit, date,id from account_move_line 
#                         where account_id in 
#                                 (select id from account_account where internal_type ='liquidity' and 
#                                 (is_temporary isnull or is_temporary='f'))
#                                 and cash_type_id isnull and account_id<>{0}""".format(self.company_id.transfer_account_id.id)

            query = """
                        select amount as amount, date,id from account_bank_statement_line 
                        where cash_type_id isnull and account_id<>{0} and company_id={1}""".format(self.company_id.transfer_account_id.id,self.company_id.id)


            print ('query ',query)
            self._cr.execute(query)
            query_result = self._cr.dictfetchall()
#             print 'query_result ',query_result
            if  e.null_line_ids:
                raise ValidationError((u'Мөрүүд үүссэн байна'))
            
            for r in query_result:
                print ('rrr2 ',r)
                    
                line_pool=self.env['account.cash.move.check.null.line']
                line_pool.create({
                                                'name':r['id'],
#                                                 'debit':r['debit'],
#                                                 'credit':r['credit'],
                                                'amount': r['amount'],
#                                                 'unit_price': r['price_unit'],
                                                'parent_id':e.id,
#                                                 'account_id':debit_id,
#                                                 'cash_type_id':r['cash_type_id'],
                                                'bsl_id':r['id'],
#                                                 'is_income':r['is_income'],
                                                       })
   
   
        return True    
class AccountCashCheckLine(models.Model):
    _name = 'account.cash.move.check.line'
    _description = u'Line'



    INCOME_SELECTION = [
        ('income','Income'),
        ('expense','Expense'),
        (' ',' '),
    ]

    name = fields.Char('Name')
    parent_id = fields.Many2one('account.cash.move.check', 'Толгой', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')

    amount = fields.Float('Amount')
    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")
    bank_line_id = fields.Many2one('account.bank.statement.line', string='Bank line',)
    is_income = fields.Selection(INCOME_SELECTION, 'TYPE')
    date = fields.Date("Start Date",related='bank_line_id.date', store=True)
    
    

class AccountCashCheckNullLine(models.Model):
    _name = 'account.cash.move.check.null.line'
    _description = u'Line'

    INCOME_SELECTION = [
        ('income','Income'),
        ('expense','Expense'),
        (' ',' '),
    ]

    name = fields.Char('Name')
    parent_id = fields.Many2one('account.cash.move.check', 'Толгой', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')

    amount = fields.Float('Amount')
    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")
    aml_id = fields.Many2one('account.move.line', string='Move line',)
    bsl_id = fields.Many2one('account.bank.statement.line', string='Statement line',)
#     is_income = fields.Selection(INCOME_SELECTION, 'TYPE')
    date = fields.Date("Start Date",related='aml_id.date', store=True)    
        
class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    _description = "Bank Statement line"

    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")


class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account Account"

    is_temporary = fields.Boolean(string="Is temporary")
