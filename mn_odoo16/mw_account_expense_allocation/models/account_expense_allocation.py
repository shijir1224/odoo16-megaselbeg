# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from odoo.tools import float_is_zero, float_compare
import datetime


STATE_SELECTION = [
    ('draft', 'НООРОГ'),
    ('computed', 'ТООЦСОН'),
    ('confirmed', 'БАТАЛГААЖУУЛСАН'),
    ('done', 'ДУУССАН'),
]    

class AccountAllocationExpense(models.Model):
    _name = "account.allocation.expense"
    _description = "account.allocation.expense"

    name = fields.Char('Name')
    date = fields.Date('Date')
    amount = fields.Float('Amount')
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
    account_id      = fields.Many2one('account.account', 'Account', )   
    move_id      = fields.Many2one('account.move', 'Move', )   
    conf_id      = fields.Many2one('account.allocation.expense.conf', 'Config', )   
    line_ids = fields.One2many('account.allocation.expense.line','parent_id','Lines') 
    state = fields.Selection(STATE_SELECTION, 'ТӨЛӨВ', required=True, default='draft')
    
    is_move = fields.Boolean('Данс хуваарилах?')
    ref_move_id = fields.Many2one('account.move.line', 'Expense entry', )   

    is_change_move = fields.Boolean('Зардлын гүйлгээг засах?')
    change_move_id = fields.Many2one('account.move.line', 'Expense entry', )   
    journal_id = fields.Many2one('account.journal', 'Journal', domain="[('type', '=', 'general')]")
    
    @api.onchange('ref_move_id')
    def onchange_ref_move_id(self):
        if self.ref_move_id:
            self.amount = self.ref_move_id.debit
            self.account_id = self.ref_move_id.account_id.id
            self.journal_id=self.ref_move_id.journal_id.id
                

    @api.onchange('change_move_id')
    def onchange_change_move_id(self):
        if self.change_move_id:
            self.amount = self.change_move_id.debit
            self.account_id = self.change_move_id.account_id.id
            self.journal_id=self.change_move_id.journal_id.id
                
                                    
    def compute(self):
        for ale in self:
            
            if ale.conf_id:
                ale.line_ids.unlink()
                line_obj=self.env['account.allocation.expense.line']
                sum_line=0
                for line in ale.conf_id.line_ids:
                    sum_line+=line.amount
                for line in ale.conf_id.line_ids:
                    amount=line.amount*ale.amount/sum_line
                    account_id=line.account_id and line.account_id.id or False
                    if not account_id and ale.change_move_id:
                        account_id=ale.change_move_id.account_id.id
                    move=line_obj.create({'name':line.name,
                                     'branch_id':line.branch_id and line.branch_id.id or False,
                                     'amount':amount,
                                     'account_id':account_id,
#                                      'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
                                    'analytic_distribution':line.analytic_distribution,
                                     'parent_id':ale.id
                                     })
#                     print ('move::: ',move)
#                     move.action_asset_moves()
            else:
                raise UserError((u'Тохиргоо сонгогдоогүй байна !!!.'))
                
            ale.state='computed'
        return True    
    
                 
    def set_draft(self):
        for ale in self:
            ale.state='draft'
        return True    
    
    

    def create_move(self):
        sum_amount=0
        for ale in self:
            line_obj=self.env['account.allocation.expense.line']
            print ('ale.is_change_move ',ale.is_change_move)
            if ale.is_change_move and ale.change_move_id:
                if ale.move_id:
                    raise UserError(u'({0}) Гүйлгээ үүссэн байна.'.format( ale.move_id.name))
                sum_line=0
                lines=[]
                move_id=ale.change_move_id.move_id.id
                commands = [(2, ale.change_move_id.id, False)]
                for line in ale.line_ids:
                    print ('commands ',commands)
                    line_vals=self._prepare_line_write_values(ale,line)
                    commands.append((0, False, line_vals))
#                     sum_amount+=round(line.amount,2)
#                 lines+=[(0, 0, {
#                         'name': self.name,
#                         'debit': 0,
#                         'credit': sum_amount,
#                         'account_id': self.account_id.id,
        #                 'analytic_account_id': line.analytic_account_id.id,
        #                 'branch_id':line.branch_id and line.branch_id.id,
        #                 'tax_ids': [(6, 0, line.tax_id.ids)],
        #                 'sale_line_ids': [(6, 0, [line.id])],
        #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
        #                 'analytic_account_id': order.analytic_account_id.id or False,
#                 })]
                ale.change_move_id.move_id.write({'line_ids': commands})
                
#                 vals={'ref':ale.name,
#                       'line_ids':lines}
#                 invoice = self.env['account.move'].sudo().create(vals)#.with_user(self.env.uid)
        #         invoice.message_post_with_view('mail.message_origin_link',
        #                     values={'self': invoice, 'origin': line.contract_id},
        #                     subtype_id=self.env.ref('mail.mt_note').id)
                self.move_id=move_id                
            else:
                if ale.move_id:
                    raise UserError(u'({0}) Гүйлгээ үүссэн байна.'.format( ale.move_id.name))
                sum_line=0
                lines=[]
                for line in ale.line_ids:
                    lines+=self._prepare_line_values(ale,line)
                    sum_amount+=round(line.amount,2)
    #         print ('lines ',lines)
                lines+=[(0, 0, {
                        'name': self.name,
                        'debit': 0,
                        'credit': sum_amount,
                        'account_id': self.account_id.id,
        #                 'analytic_account_id': line.analytic_account_id.id,
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
                'debit': round(amount,2),
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
            
    def _prepare_line_write_values(self, order, line):
        name=order.name or ''
        amount=line.amount
#         if not order.partner_id:
#             raise UserError((u'{0} Гэрээнд харилцагч сонгогдоогүй байна !!!.'.format(order.name)))
#         if not order.insurance_product_id:
#             raise UserError((u'{0} Гэрээнд бүтээгдэхүүн сонгогдоогүй байна !!!.'.format(order.name)))
#         if not order.insurance_product_id.product_id:
#             raise UserError((u'{0} Бүтээгдэхүүн дээр бараа тохируулаагүй байна !!!.'.format(order.insurance_product_id.name)))
#         if not order.insurance_product_id.product_id.property_account_income_id:
#             raise UserError((u'{0} Бүтээгдэхүүн дээр данс тохируулаагүй байна !!!.'.format(order.insurance_product_id.product_id.name)))
        account_id=line.account_id and line.account_id.id or False
        if not account_id and order.change_move_id:
            account_id=order.change_move_id.account_id.id
        print ('account_id ',account_id)
        line_vals ={
                'debit': round(amount,2),
                'credit': 0,
                'account_id': account_id,
#                 'analytic_account_id': line.analytic_account_id.id,
                'analytic_distribution': line.analytic_distribution,
                'branch_id':line.branch_id and line.branch_id.id,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            }

        return line_vals             
            
class AccountAllocationExpenseLine(models.Model):
    _name = "account.allocation.expense.line"
    _description = "account.allocation.expense line"
    _inherit = 'analytic.mixin'    
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.allocation.expense', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )
#     analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )

    branch_id      = fields.Many2one('res.branch', 'New Branch', )
                            
                                   
class AccountAllocationExpenseConf(models.Model):
    _name = "account.allocation.expense.conf"
    _description = "account.allocation.expense.conf"
    
    name = fields.Char('Тайлбар')
    branch_id = fields.Many2one('res.branch', 'New Branch')
    expense_type = fields.Selection([('consume', 'АБХ'), ('asset', 'Үндсэн хөрөнгө'), ('product_expense', 'Шаардах'), ('other', 'Бусад')],
                                    default='other', required=True, string='Хуваарилах төрөл')
    line_ids = fields.One2many('account.allocation.expense.conf.line','parent_id','Lines',copy=True)
    journal_ids = fields.Many2many('account.journal', 'account_allocation_accunt_journal_rel', 'conf_id', 'journal_id', string="Journals")


class AccountAllocationExpenseConfLine(models.Model):
    _name = "account.allocation.expense.conf.line"
    _description = "account.allocation.expense conf"
    _inherit = 'analytic.mixin' 
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.allocation.expense.conf', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )
    analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
                            