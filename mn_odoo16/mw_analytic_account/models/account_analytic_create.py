# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from dateutil.relativedelta import relativedelta
from math import copysign

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round
from dateutil.relativedelta import relativedelta

TYPE_SELECTION = [
    ('check', 'Шалгах'),
    ('create', 'Үүсгэх'),
]



STATE_SELECTION = [
    ('draft', 'НООРОГ'),
    ('computed', 'ТООЦСОН'),
    ('confirmed', 'БАТАЛГААЖУУЛСАН'),
    ('done', 'ДУУССАН'),
]    
class AccountAnalytic(models.Model):
    
    _name = "account.analytic.create"
    _description = "account.analytic.create"

    name = fields.Char('Утга')
    start_date = fields.Date('Эхлэх огноо')
    end_date = fields.Date('Дуусах Огноо')
    amount = fields.Float('Amount')
    limit = fields.Integer('Limit',default=100)
    line_ids = fields.One2many('account.analytic.create.line','parent_id','Мөрүүд') 
    state = fields.Selection(STATE_SELECTION, 'ТӨЛӨВ', required=True, default='draft')
    empty_line_ids = fields.One2many('account.analytic.create.line','emp_parent_id','Мөрүүд') 
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.user.company_id)
                                
    def draft_set(self):
        for ale in self:
            ale.state='draft'
        return True    
    
    def compute(self):
        query="""select s.amount, 
                    round(l.debit,2) as debit,
                    round(l.credit,2) as credit,
                    s.id as sid,
                    l.id as lid,
                    l.date as date, 
                    l.account_id
                from account_analytic_line s left join 
                    account_move_line l on s.move_line_id=l.id 
                where ((s.amount>0 and round(s.amount,0)!=round(l.credit,0)) or (s.amount<0 and round(abs(s.amount),0)!=round(l.debit,0))) 
                    and l.date between '{0}' and '{1}' and l.company_id={3} order by l.id limit {2}
            """.format(self.start_date, self.end_date,self.limit,self.env.user.company_id.id)
        # print ('query ',query)
        self._cr.execute(
            query
        )
        row = self._cr.dictfetchall()
        # update account_analytic_line set general_account_id=foo.account_id from (
        #  select s.amount, 
        #             round(l.debit,2) as debit,
        #             round(l.credit,2) as credit,
        #             s.id as sid,
        #             l.id as lid,
        #             l.date as date, 
        #             l.account_id,s.general_account_id
        #         from account_analytic_line s left join 
        #             account_move_line l on s.move_line_id=l.id 
        #         where s.general_account_id!=l.account_id
        #         ) as foo where account_analytic_line.id=foo.sid
                
                
# select s.amount, 
#                     round(l.debit,2) as debit,
#                     round(l.credit,2) as credit,
#                     s.id as sid,
#                     l.id as lid,
#                     l.date as date, 
#                     l.account_id,s.date as sdate
#                 from account_analytic_line s left join 
#                     account_move_line l on s.move_line_id=l.id 
#                 where  
#                    l.date!=s.date and l.company_id=6;
# update account_analytic_line set date=foo.date from (               
# select s.amount, 
#                     round(l.debit,2) as debit,
#                     round(l.credit,2) as credit,
#                     s.id as sid,
#                     l.id as lid,
#                     l.date as date, 
#                     l.account_id,s.date as sdate
#                 from account_analytic_line s left join 
#                     account_move_line l on s.move_line_id=l.id 
#                 where  
#                    l.date!=s.date and l.company_id=6
#                    ) as foo where    account_analytic_line.id=foo.sid                   
        if row:
            number=1
            for r in row:
                line_obj=self.env['account.analytic.create.line']
                move=line_obj.create({
                                 'name':str(number)+' - ' +self.name,
                                 'amount':r['amount'],
                                 'date':r['date'],
                                 'account_id':r['account_id'],
                                 'analytic_line_id':r['sid'],
                                 'move_line_id':r['lid'],
                                 'debit':r['debit'],
                                 'credit':r['credit'],
                                 'parent_id':self.id
                                 })
                number+=1
        self.state='computed'
        return True    
    

    def compute_create(self):
        query="""select l.id as lid, 
                        a.id as account_id,
                        round(l.debit,2) as debit, 
                        round(l.credit,2) as credit,
                        l.date 
                    from account_move_line l left join
                        account_move m  on m.id=l.move_id left join 
                        account_account a on a.id=l.account_id  
                    where l.date between '{0}' and '{1}' and l.company_id={3} 
                            and a.create_analytic='t'
                            and m.state='posted'  
                            and l.id not in (select move_line_id from account_analytic_line where move_line_id notnull and company_id={3}) 
                        order by l.id limit {2}
            """.format(self.start_date, self.end_date,self.limit,self.env.user.company_id.id)
        self._cr.execute(
            query
        )
        row = self._cr.dictfetchall()
        
        if row:
            number=1
            for r in row:
                line_obj=self.env['account.analytic.create.line']
                move=line_obj.create({
                                 'name':str(number)+' - ' +self.name,
                                 'amount':0,
                                 'date':r['date'],
                                 'account_id':r['account_id'],
                                 'move_line_id':r['lid'],
                                 'debit':r['debit'],
                                 'credit':r['credit'],
                                 'emp_parent_id':self.id
                                 })
                number+=1
        self.state='computed'
        return True    
    
    def create_move(self):
        sum_amount=0
        for ale in self.line_ids:
            if ale.analytic_line_id:
                amount=0
                if ale.debit>0:
                    amount=-ale.debit
                elif ale.credit>0:
                    amount=ale.credit
                elif ale.credit==0 and ale.debit==0 :
                    amount=0
                ale.analytic_line_id.write({'amount':amount})
        return True    
    
    def calc_analytics(self):
        sum_amount=0
        for ale in self.empty_line_ids:
            if ale.move_line_id:
                analytic_distribution= self._find_analytic_distribution(ale.move_line_id)
                print ('analytic_distribution11111 ',analytic_distribution)
                if analytic_distribution:
                    ale.move_line_id.write({'analytic_distribution':analytic_distribution})
                    ale.write({'analytic_distribution':analytic_distribution})
        return True    
    
    def _find_analytic_distribution(self,line):
        print ('123=====112')
        if line.display_type == 'product' and line.move_id.is_invoice(include_receipts=True) and line.move_id.stock_warehouse_id.analytic_distribution:
            return line.move_id.stock_warehouse_id.analytic_distribution
        return False
        
    def create_short_move(self):
        for ale in self:
            amount=0
            for line in ale.empty_line_ids:
                if line.move_line_id:
                    if not line.move_line_id.analytic_line_ids:
                        # if not line.move_line_id.analytic_distribution:
                        #     raise UserError(('Данс дээр шинжилгээний бичилт үүсгэнэ гэж тохируулсан боловч санхүү гүйлгээнд шинжилгээний данс сонгоогүй байна!\
                        #                          Шинжилгээний данс тооцох товч дарж тооцож нэг үзээрэй ! \
                        #                           {}'.format(line.move_line_id.name)))
                        if line.move_line_id.analytic_distribution:
                            a_id=line.move_line_id._create_analytic_lines()
                            print ('a_ida_id ',a_id, line.move_line_id.name)
                            # line.write({'analytic_line_id':a_id})
                            if len(a_id) == 1:
                                line.write({'analytic_line_id':a_id})
                            elif len(a_id) > 1:
                                for i in range(0, len(a_id)):
                                    copy_line = line.copy()
                                    copy_line.write({'analytic_line_id': a_id[i]})
                                    i += 1
            
        return True        
  
  
class AccountAllocationExpenseLine(models.Model):
    _inherit = "analytic.mixin"
    _name = "account.analytic.create.line"
    _description = "account.analytic.create line"
    
    name = fields.Char('Утга')
    amount = fields.Float('Дүн')
    date = fields.Date('Огноо')
    parent_id      = fields.Many2one('account.analytic.create', 'Parent', )
    emp_parent_id      = fields.Many2one('account.analytic.create', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Данс', )
    analytic_line_id      = fields.Many2one('account.analytic.line', ' Analytic line', )
    move_line_id      = fields.Many2one('account.move.line', 'Move', )
                            
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')