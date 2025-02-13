from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time, datetime

class CashBoxOut(models.TransientModel):
    _inherit = 'cash.box.out'
    _description = 'Cash Box Out'


    @api.model
    def _get_default_date(self):
        context = dict(self.env.context)
        active_id = self.env['account.bank.statement'].browse(context.get('active_id'))
        return active_id.date

    
    partner_id = fields.Many2one('res.partner', u'Харилцагч')
    account_id = fields.Many2one('account.account', u'Данс')
    branch_id = fields.Many2one('res.branch', u'Салбар')
    move_id = fields.Many2one('account.move', u'Move')
    date = fields.Date(u'огноо',default=_get_default_date)
    
    def _calculate_values_for_statement_line(self, record):
        res=super(CashBoxOut , self )._calculate_values_for_statement_line(record)
        if self.partner_id:
            res.update({'partner_id':self.partner_id.id})
        if self.account_id:
            res.update({'account_id':self.account_id.id})
        if self.branch_id:
            res.update({'branch_res_id':self.branch_id.id})
        if self.date:
            res.update({'date':self.date})
            
        return res




class CashBoxTranfer(CashBoxOut):
    _name = 'cash.box.tranfer'
    
    name =fields.Char(string="Утга")
    branch_id = fields.Many2one('res.branch', string="Салбар")
    journal_id = fields.Many2one('account.journal', string='Statement',domain=[('type','in',('bank','cash')),])
    income_journal_id = fields.Many2one('account.journal', string='Statement',domain=[('type','in',('bank','cash')),])
    type = fields.Selection([('income',u'Орлого'),('expense',u'Зарлага')], string='Type',default='expense')
    date = fields.Date("Date",default=time.strftime('%Y-%m-%d'))
    amount_curr = fields.Float("Валютаарх дүн")
    foreign_currency_id = fields.Many2one('res.currency', string='Foreign Currency',
        help="The optional other currency if it is a multi-currency entry.")
    rate = fields.Float('Ханш')
    amount = fields.Float (string="Дүн")
    @api.onchange('foreign_currency_id','amount','amount_curr','rate')
    def onchange_foreign_currency_id(self):
        for line in self:
            if line.income_journal_id:
                company = line.income_journal_id.company_id
#                 print ('company ',company)
#                 print ('line.rate ',line.rate)
                if line.foreign_currency_id and line.foreign_currency_id.id!=company.currency_id.id and not line.rate:
                    currency_rates = line.foreign_currency_id._get_rates(company, line.date or fields.Date.context_today(line))
                    if currency_rates.get(line.foreign_currency_id.id,0)>1:
                         line.rate=currency_rates[line.foreign_currency_id.id]
                if line.rate and line.amount_curr!=0:
                    line.amount=line.rate*line.amount_curr
                
#     @api.onchange('amount_curr')
#     def _onchange_amount_curr(self):
#         if self.amount_curr:
#             context = dict(self._context or {})
#             active_model = context.get('active_model', False)
#             active_ids = context.get('active_ids', [])
#             statement = self.env[active_model].browse(active_ids)
#             print ('statement ',statement)
#             
#             if self.income_statement_id and self.income_statement_id.journal_id.currency_id:
#                 if self.income_statement_id.journal_id.currency_id!=statement.company_id.currency_id:
#                     company_currency = statement.company_id.currency_id
#                     currency = self.income_statement_id.journal_id.currency_id
#                     print ('currency ',currency)
#                     print ('company_currency ',company_currency)
#                     amount_mnt = currency._convert(self.amount_curr, company_currency, statement.company_id, self.date)
#                     print ('amount_mnt ',amount_mnt)
#                     self.amount=amount_mnt
                    
    def _calculate_values_for_statement_line(self, record,account_id):
        amount = self.amount
        print ('record.journal_id.currency_id ',record.journal_id.currency_id)
        if record.journal_id.currency_id and record.journal_id.company_id.currency_id!=record.journal_id.currency_id:
            amount=self.amount_curr
        
        if self.type=='income':
            amount = amount
        elif self.type=='expense':
            amount = -amount
        return {
            'move_id':self.move_id.id,
            'date': self.date,
            'journal_id': self.income_journal_id.id,
            'amount':amount,
            'partner_id': self.partner_id.id or False,
            'account_id': account_id,#record.journal_id.company_id.transfer_account_id.id,
            'name': self.name,
            'payment_ref':self.name,
            'branch_res_id':self.branch_id and self.branch_id.id or record.branch_id and record.branch_id.id or False,
        }
    print('=========', _calculate_values_for_statement_line)

    def _calculate_values_for_statement_income_line(self, record,account_id,id):
        print ('record.journal_id.currency_id2++ ',record.journal_id.currency_id)
        amount = self.amount
        if record.journal_id.currency_id and record.journal_id.company_id.currency_id!=record.journal_id.currency_id:
            amount=self.amount_curr
        if self.type=='income':
            amount = -amount
        elif self.type=='expense':
            amount = amount
        print ('self.move_id.id' ,self.move_id.id)
        return {
            'move_id':self.move_id.id,
            'date': self.date,
            'journal_id': self.income_journal_id.id,
#             'journal_id': record.journal_id.id,
            'amount': amount,
            'partner_id': self.partner_id.id or False,
            'account_id':account_id,#record.journal_id.company_id.transfer_account_id.id,
            'name': self.name,
            'branch_res_id':self.branch_id and self.branch_id.id or record.branch_id and record.branch_id.id or False,
            'transfer_line_id':id[0].id,
            'payment_ref':self.name,
        }
        
        
    def run(self):
        if self.date:
            context = self.env.context
            active_model = context.get('active_model', False)
            active_ids = context.get('active_ids', [])
            records = self.env['account.bank.statement.line'].browse(active_ids)
            return self._run(records)
        else:
            raise UserError(_(u'Огноо оруулна уу.!'))

    def _run(self, records):
#         print ('records ',records)
        context = dict(self._context or {})
        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', [])
        records = self.env['account.bank.statement.line'].browse(active_ids)
        move_obj=self.env['account.move']
#         records = self.env['account.bank.statement'].browse(records.income_statement_id)
 
        for box in self:
            for record in records:
                if not record.journal_id:
                    raise UserError(_("Please check that the field 'Journal' is set on the Bank Statement"))
                if record.journal_id.company_id.is_cash_transaction_account:
                    transfer_account_id = record.journal_id.default_account_id.id  
                    self_account_id = box.income_journal_id.default_account_id.id  
                    move_vals = {
                            'name': '/', #+'/'+str(datetime.strptime(self.date, '%Y-%m-%d').year),
                            'date': record.date,
                            'journal_id': record.journal_id.id,
                        }
                    new_move_id = move_obj.create(move_vals)
                    print ('new_move_id ',new_move_id)
                    self.write({'move_id':new_move_id})  
                elif not record.journal_id.company_id.transfer_account_id:
                    raise UserError(_("Please check that the field 'Transfer Account' is set on the company."))
                else:
                    self_account_id = record.journal_id.company_id.transfer_account_id.id #box.income_statement_id.journal_id.default_account_id.id
                    transfer_account_id=record.journal_id.company_id.transfer_account_id.id
                id=box._create_bank_statement_self_line(record,self_account_id)
#                 transfer_account_id=record.journal_id.default_account_id.id
#                 transfer_account_id = record.journal_id.company_id.is_cash_transaction_account and \
#                             box.income_statement_id.journal_id.default_account_id.id or record.journal_id.company_id.transfer_account_id.id
                box._create_bank_statement_income_line(box.income_journal_id,transfer_account_id,id)
        return {}

    def _create_bank_statement_income_line(self, record,account_id,id):
        line_obj = self.env['account.bank.statement.line']
        if record.state == 'confirm':
            raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
        values = self._calculate_values_for_statement_income_line(record,account_id,id)
        id=line_obj.with_context(internal=True).create(values)
        return id
#         return record.write({'line_ids': [(0, False, values[0])]})

    def _create_bank_statement_self_line(self, record,account_id):
        line_obj = self.env['account.bank.statement.line']
        if record.state == 'confirm':
            raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
        values = self._calculate_values_for_statement_line(record,account_id)
        id=line_obj.with_context(internal=True).create(values)
        return id