# -*- coding: utf-8 -*-

import time
import math
import calendar
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from odoo.tools import float_is_zero, float_compare
import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime


STATE_SELECTION = [
    ('draft', 'НООРОГ'),
    ('computed', 'ТООЦСОН'),
    ('confirmed', 'БАТАЛГААЖУУЛСАН'),
    ('done', 'ДУУССАН'),
]    

class AccountExpenseCalculation(models.Model):
    _name = "account.expense.calculation"
    _inherit = "analytic.mixin"    
    _description = "account.expense.calculation"

    name = fields.Char('Утга')
    date = fields.Date('Эхлэх огноо')
    amount = fields.Float('Дүн')
    account_id      = fields.Many2one('account.account', 'Данс', )  
    debit_acc_id = fields.Many2one('account.account', string='Дт данс', )
    partner_id = fields.Many2one('res.partner', string='Харилцагч', options="{'no_create': True}") 
    move_id      = fields.Many2one('account.move', 'Гүйлгээ', )   
    conf_id      = fields.Many2one('account.expense.calculation.conf', 'Config', )   
    line_ids = fields.One2many('account.expense.calculation.line','parent_id','Lines') 
    state = fields.Selection(STATE_SELECTION, 'ТӨЛӨВ', required=True, default='draft')
    value_residual = fields.Float(compute='_amount_residual', string='Residual Value')
    method_number = fields.Integer(string='Элэгдэх тоо',) #default=5, readonly=True,states={'draft': [('readonly', False)]}, 
    end_date    = fields.Date('Дуусах огноо')
    analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )
    branch_id      = fields.Many2one('res.branch', 'Branch', )
    brand_id      = fields.Many2one('product.brand', 'Brand', )
    journal_id      = fields.Many2one('account.journal', 'Journal', )
    expense_conf_id      = fields.Many2one('account.allocation.expense.conf', 'Config', )   
        
    number_day = fields.Integer(string='Элэгдэх хоног',) #default=5, readonly=True,states={'draft': [('readonly', False)]}, 
    is_month = fields.Boolean(string='Сараар тэнцүү элэгдүүлэх?',) #default=5, readonly=True,states={'draft': [('readonly', False)]}, 
        

    @api.onchange('is_month')
    def _is_month(self):
        for obj in self:
            if not obj.is_month:
                if obj.date and obj.end_date:
                    diff = obj.end_date - obj.date
                    obj.number_day=diff.days
                    

    @api.onchange('end_date')
    def _is_month(self):
        for obj in self:
            if not obj.is_month:
                if obj.date and obj.end_date:
                    diff = obj.end_date - obj.date
                    obj.number_day=diff.days                    
            
    @api.depends('amount', 'line_ids.move_id', 'line_ids.amount')
    def _amount_residual(self):
        for rec in self:
            total_amount = 0.0
            for line in rec.line_ids:
                if line.move_id:
                    total_amount += line.amount
            rec.value_residual = rec.amount - total_amount

    def compute(self):
        for ale in self:
            ale.compute_depreciation_board()
        return True    
    
    def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
#         undone_dotation_number = self.method_number
#         end_date = self.method_end
#         undone_dotation_number = 0
#         while depreciation_date <= end_date:
#             depreciation_date = date(depreciation_date.year, depreciation_date.month,
#                                      depreciation_date.day) + relativedelta(months=+self.method_period)
#             undone_dotation_number += 1
        return undone_dotation_number
    
    def compute_depreciation_board(self):
        self.ensure_one()

        posted_depreciation_line_ids = self.line_ids.filtered(lambda x: x.move_id).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.line_ids.filtered(lambda x: not x.move_id)

        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual

            # if we already have some previous validated entries, starting date is last entry + method period
            if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                last_depreciation_date = fields.Date.from_string(posted_depreciation_line_ids[-1].depreciation_date)
                depreciation_date = last_depreciation_date + relativedelta(months=+1)
                max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                depreciation_date = depreciation_date.replace(day=max_day_in_month)                
#                 print ('depreciation_date ',depreciation_date)
            else:
                # depreciation_date computed from the purchase date
                depreciation_date = self.date
            total_days = (depreciation_date.year % 4) and 365 or 366
            month_day = depreciation_date.day
            if self.is_month:
                undone_dotation_number = self.method_number #self._compute_board_undone_dotation_nb(depreciation_date, total_days)
            else:
                undone_dotation_number = self.number_day #self._compute_board_undone_dotation_nb(depreciation_date, total_days)
                
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number+2):
                sequence = x + 1
#                 amount = self.amount/undone_dotation_number
                #өдрөөр
                udruur=True
                if self.is_month:
                    amount = self.amount/undone_dotation_number
                else:
                    if sequence==1:
                        date = self.date
                        month_days = calendar.monthrange(date.year, date.month)[1]
                        days = month_days - date.day+1
                    else:
                        date=depreciation_date
                        month_days = calendar.monthrange(date.year, date.month)[1]
                        days = depreciation_date.day
                        
#                     if date.day != month_days:
#                             amount = amount / month_days * days
#                     amount = (self.amount / total_days/(undone_dotation_number/12))*days
                    amount = (self.amount / undone_dotation_number)*days
#                 amount = round(amount,2)
#                 if float_is_zero(amount, precision_rounding=2):
                amount=min(amount,residual_amount)
                if amount<=0:
                    continue
#                 amount=min(amount,residual_amount)                
                residual_amount -= amount
                if residual_amount>=0 or amount>0:
                    vals = {
                        'amount': amount,
                        'parent_id': self.id,
    #                     'sequence': sequence,
                        'name': (self.name or '') + '/' + str(sequence),
                        'remaining_value': residual_amount,
                        'depreciated_value': self.amount - ( residual_amount),
                        'depreciation_date': depreciation_date,
                    }
                    commands.append((0, False, vals))

                    depreciation_date = depreciation_date + relativedelta(months=+1)
    
    #                 if month_day > 28 and self.date_first_depreciation == 'manual':
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
#                     depreciation_date = depreciation_date.replace(day=min(max_day_in_month, month_day))
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)
                else:
                    break
                # datetime doesn't take into account that the number of days is not the same for each month
#                 if not self.prorata and self.method_period % 12 != 0 and self.date_first_depreciation == 'last_day_period':
#                     max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
#                     depreciation_date = depreciation_date.replace(day=max_day_in_month)

        self.write({'line_ids': commands})

        return True
    

    def create_move(self):
        sum_amount=0
        for ale in self:
            line_obj=self.env['account.expense.calculation.line']
            sum_line=0
            lines=[]
            for line in ale.line_ids:
                lines+=self._prepare_line_values(ale,line)
                sum_amount+=line.amount
#         print ('lines ',lines)
        lines+=[(0, 0, {
                'name': self.name,
                'debit': 0,
                'credit': sum_amount,
                'account_id': self.account_id.id,
                'analytic_distribution': line.analytic_distribution,
#                 'branch_id':line.branch_id and line.branch_id.id,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
        })]
        vals={'ref':ale.name,
              'line_ids':lines}
        invoice = self.env['account.move'].sudo().create(vals)#.with_user(self.env.uid)
#         invoice.message_post_with_view('mail.message_origin_link',
#                     values={'self': invoice, 'origin': line.contract_id},
#                     subtype_id=self.env.ref('mail.mt_note').id)
        self.move_id=invoice.id
        return True    
  
  
    def _prepare_line_values(self, order, line):
        name=order.name or ''
        amount=line.amount
            
        line_vals =[(0, 0, {
                'debit': amount,
                'credit': 0,
                'account_id': line.account_id.id,
                'analytic_distribution': line.analytic_distribution,
                'branch_id':line.branch_id and line.branch_id.id,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            })]

        return line_vals 
            
            
class AccountAllocationExpenseLine(models.Model):
    _name = "account.expense.calculation.line"
    _description = "account.expense.calculation line"
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    remaining_value = fields.Float('Үлдэгдэл дүн')
    depreciated_value = fields.Float('Элэгдсэн дүн')
    depreciation_date = fields.Date('Огноо')
    
    parent_id      = fields.Many2one('account.expense.calculation', 'Parent', )
    move_id      = fields.Many2one('account.move', 'Move', )
                            
                   
    def compute_data(self,conf_id,sum_line):
        res=[]
        if conf_id:
            line_obj=self.env['account.allocation.expense.line']
#             sum_line=0
#             for line in conf_id.line_ids:
#                 sum_line+=line.amount
            for line in conf_id.line_ids:
                amount=line.amount*ale.amount/sum_line
#                 account_id=line.account_id and line.account_id.id or False
#                 if not account_id and ale.change_move_id:
#                     account_id=ale.change_move_id.account_id.id
                res.append({'name':line.name,
                                 'branch_id':line.branch_id and line.branch_id.id or False,
                                 'amount':round(amount,2),
                                 'account_id':account_id,
                                 'analytic_distribution':line.analytic_distribution or False,
#                                  'parent_id':ale.id
                                 })
        return res    
    
    def button_validate_line(self):
        sum_amount=0
        sum_line=0
        lines=[]
#         for line in self:
#             lines+=self._prepare_line_values(ale,line)
#             sum_amount+=line.amount
#         print ('lines ',lines)
        if not self.parent_id.debit_acc_id and not self.parent_id.expense_conf_id:
            raise UserError((u'{0} Дебит данс сонгоогүй байна !!!.'.format(self.parent_id.name)))
        if not self.parent_id.account_id:
            raise UserError((u'{0} Кредит данс сонгоогүй байна !!!.'.format(self.parent_id.name)))
        if not self.parent_id.journal_id:
            raise UserError((u'{0} журнал данс сонгоогүй байна !!!.'.format(self.parent_id.name)))
        if not self.parent_id.expense_conf_id:
            if not self.parent_id.analytic_distribution:
                raise UserError((u'{0} шинжилгээний данс данс сонгоогүй байна !!!.'.format(self.parent_id.name)))
        if not self.parent_id.branch_id:
            raise UserError((u'{0} салбар данс сонгоогүй байна !!!.'.format(self.parent_id.name)))
        # if not self.parent_id.brand_id:
        #     raise UserError((u'{0} брэнд данс сонгоогүй байна !!!.'.format(self.parent_id.name)))
        if self.parent_id.expense_conf_id:
#             for self.parent_id.expense_conf_id
            conf_id=self.parent_id.expense_conf_id
            sum_line=0
            sum_amount=0
            for line in conf_id.line_ids:
                sum_line+=line.amount
            for line in conf_id.line_ids:
                account_id=line.account_id and line.account_id.id or False
                if not account_id and self.parent_id.debit_acc_id:
                    account_id=self.parent_id.debit_acc_id.id
                amount=self.amount*line.amount/sum_line
                sum_amount+=round(amount,2)
#                 res.append({'name':line.name,
#                                  'amount':amount,
#                                  'account_id':account_id,
# #                                  'parent_id':ale.id
#                                  })            
                lines+=[(0, 0, {
                    'name': line.name,
                    'debit': round(amount,2),
                    'credit': 0,
                    'account_id': account_id,
                    'analytic_distribution':line.analytic_distribution or False,
                    'branch_id':line.branch_id and line.branch_id.id or False,
#                     'brand_id': self.parent_id.brand_id.id,
                    'partner_id': self.parent_id.partner_id and self.parent_id.partner_id.id or False,
    #                 'tax_ids': [(6, 0, line.tax_id.ids)],
    #                 'sale_line_ids': [(6, 0, [line.id])],
    #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
    #                 'analytic_account_id': order.analytic_account_id.id or False,
                })]
            lines+=[(0, 0, {
                    'name': self.name,
                    'debit': 0,
                    'credit': sum_amount,
                    'account_id': self.parent_id.account_id.id,
                    'analytic_distribution': self.parent_id.analytic_distribution,
                    'branch_id':self.parent_id.branch_id.id,
                    'partner_id': self.parent_id.partner_id and self.parent_id.partner_id.id or False,
    #                 'tax_ids': [(6, 0, line.tax_id.ids)],
    #                 'sale_line_ids': [(6, 0, [line.id])],
    #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'brand_id': self.parent_id.brand_id.id,
            })]
        else:
            lines+=[(0, 0, {
                    'name': self.name,
                    'debit': round(self.amount,2),
                    'credit': 0,
                    'account_id': self.parent_id.debit_acc_id.id,
                    'analytic_distribution': self.parent_id.analytic_distribution,
                    'branch_id':self.parent_id.branch_id.id,
                    'brand_id': self.parent_id.brand_id.id,
                    'partner_id': self.parent_id.partner_id and self.parent_id.partner_id.id or False,
    #                 'tax_ids': [(6, 0, line.tax_id.ids)],
    #                 'sale_line_ids': [(6, 0, [line.id])],
    #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
    #                 'analytic_account_id': order.analytic_account_id.id or False,
            })]
            lines+=[(0, 0, {
                    'name': self.name,
                    'debit': 0,
                    'credit': round(self.amount,2),
                    'account_id': self.parent_id.account_id.id,
                    'analytic_distribution': self.parent_id.analytic_distribution,
                    'branch_id':self.parent_id.branch_id.id,
                    'partner_id': self.parent_id.partner_id and self.parent_id.partner_id.id or False,
    #                 'tax_ids': [(6, 0, line.tax_id.ids)],
    #                 'sale_line_ids': [(6, 0, [line.id])],
    #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'brand_id': self.parent_id.brand_id.id,
            })] 
#         print ('lines ',lines)       
        vals={'ref':self.name,
              'date':self.depreciation_date,
              'partner_id': self.parent_id.partner_id and self.parent_id.partner_id.id or False,
              'journal_id':self.parent_id.journal_id.id,
              'line_ids':lines}
        invoice = self.env['account.move'].sudo().create(vals)#.with_user(self.env.uid)
#         invoice.message_post_with_view('mail.message_origin_link',
#                     values={'self': invoice, 'origin': line.contract_id},
#                     subtype_id=self.env.ref('mail.mt_note').id)
        self.move_id=invoice.id
        return True    
                                   
class AccountAllocationExpenseConf(models.Model):
    _name = "account.expense.calculation.conf"
    _description = "account.expense.calculation.conf"
    
    name = fields.Char('Тайлбар')
#     parent_id      = fields.Many2one('asset.move.request', 'Parent', )
#     owner_emp_id      = fields.Many2one('hr.employee', 'New Employee', )
#     owner_dep_id      = fields.Many2one('hr.department', 'New department', )
#     date               =  fields.Datetime('Date', required=True)
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
    line_ids = fields.One2many('account.expense.calculation.conf.line','parent_id','Lines')
              

class AccountAllocationExpenseConfLine(models.Model):
    _name = "account.expense.calculation.conf.line"
    _inherit = "analytic.mixin"
    _description = "account.expense.calculation conf"
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.expense.calculation.conf', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )
    analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
                            