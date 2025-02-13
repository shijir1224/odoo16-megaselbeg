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
    ('contract_fee', 'Гэрээний шимтгэл'),
    ('claim_payment', 'Нөхөн төлбөр'),
    ('contract_change', 'Гэрээний нэмэлт өөрчлөлт'),
    ('dosh_fee', 'ДОШ Шимтгэл'),
    ('reinsurance', 'Давхар даатгал'),
    ('project', 'Төсөл'),
    ('partner_care', 'Харилцагчийн халамж'),
    ('cancel_return', 'Буцаалт цуцлалт'),
    ('other', 'Бусад'),
]



STATE_SELECTION = [
    ('draft', 'НООРОГ'),
    ('computed', 'ТООЦСОН'),
    ('confirmed', 'БАТАЛГААЖУУЛСАН'),
    ('done', 'ДУУССАН'),
]    
class AccountMove(models.Model):
    _inherit = 'account.move'

    is_move_asset = fields.Boolean('Хөрөнгийн гүйлгээ?',copy=False)
    asset_vat_id      = fields.Many2one('account.asset.vat.conf', 'НӨАТ тохиргоо', )   


#     def post(self):
#         # OVERRIDE
#         res = super(AccountMove, self).post()
# 
#         self._auto_create_asset_vat()
#         return res
    
    def _auto_create_asset(self):
        res = super(AccountMove, self)._auto_create_asset()
        self._auto_create_asset_vat(res)
        return res
    
    def _auto_create_asset_vat(self,assets):
        create_list = []
        invoice_list = []
        auto_validate = []
        # configured to automatically create assets
        for move in self:
            if not move.is_invoice():
                continue
            vat_obj=self.env['account.asset.vat']
            for move_line in move.line_ids:
                if move_line.account_id and (move_line.account_id.can_create_asset) and \
                                move_line.account_id.create_asset != 'no' and not move.reversed_entry_id\
                                    and move_line.tax_ids:
                    if not move.is_move_asset:
                        raise UserError((u'Хөрөнгийн худалдан авалт НӨАТ тай бол Хөрөнгийн гүйлгээг сонгоно уу {account}').format(account=move_line.account_id.display_name))
                    if not move.asset_vat_id:
                        raise UserError((u'Хөрөнгийн худалдан авалтын НӨАТ ийн тохиргоог сонгоно уу {account}').format(account=move_line.account_id.display_name))
                    print ('move_line ',move_line.original_many_asset_ids)
                    assts=move_line.original_many_asset_ids and move_line.original_many_asset_ids.ids or []
                    vals = { 
                        'name': move_line.name,
                        'date': move_line.date,
                        'amount': move_line.price_total-move_line.price_subtotal,
                        
                        'conf_id': move.asset_vat_id.id,
#                         'currency_id': move_line.company_currency_id.id,
                        'asset_ids': [(6, False, assts)],
                        'state': 'draft',
                        'month':move.asset_vat_id.month
                    }
#                     model_id = move_line.account_id.asset_model
#                     if model_id:
#                         vals.update({
#                             'model_id': model_id.id,
#                         })
#                     invoice_list.append(move)
                    create_list.append(vals)
            vats = vat_obj.create(create_list)
            vats.compute()
        return True    
  
class AccountAassetVAT(models.Model):
    _name = "account.asset.vat"
    _description = "account.asset.vat"

    name = fields.Char('Утга    ')
    date = fields.Date('Огноо')
    last_short_date = fields.Date('Богино огноо')
    last_long_date = fields.Date('Урт Огноо')
    amount = fields.Float('Amount')
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
    account_id      = fields.Many2one('account.account', 'Данс', )   
    move_id      = fields.Many2one('account.move', 'Move', )   
    conf_id      = fields.Many2one('account.asset.vat.conf', 'Тохиргоо', )   
    line_ids = fields.One2many('account.asset.vat.line','parent_id','Мөрүүд') 
    state = fields.Selection(STATE_SELECTION, 'ТӨЛӨВ', required=True, default='draft')
    month = fields.Integer('Элэгдүүлэх сар')    
    asset_ids = fields.Many2many('account.asset', 'account_asset_vat_rel','aml_id', 'asset_id', string='Assets', copy=False)

    long_account_id      = fields.Many2one('account.account', 'Account long', related='conf_id.long_account_id')
    short_account_id      = fields.Many2one('account.account', 'Account short', related='conf_id.short_account_id')

    short_move_ids = fields.Many2many('account.move', 'account_asset_vat_short_move_rel','vat_id', 'move_id', string='Short moves', copy=False)
    long_move_ids = fields.Many2many('account.move', 'account_asset_vat_long_move_rel','vat_id', 'move_id', string='Long moves', copy=False)

    def draft_set(self):
        for ale in self:
            ale.state='draft'
        return True    
    
    
    def compute(self):
        for ale in self:
            
            if ale.conf_id:
                ale.line_ids.unlink()
                number=ale.month
                amount=ale.amount/ale.month
                date=ale.date
                while number>0:
                    line_obj=self.env['account.asset.vat.line']
                    move=line_obj.create({
                                     'name':str(number)+' - ' +ale.name,
                                     'amount':amount,
                                     'date':date,
#                                      'account_id':line.account_id and line.account_id.id or False,
#                                      'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
                                     'parent_id':ale.id
                                     })
                    date = date+relativedelta(months=1)
                    number-=1
            ale.state='computed'
        return True    
    

    def create_move(self):
        sum_amount=0
        for ale in self:
            amount=0
            if not ale.last_long_date:
                raise UserError((u'Урт огноогоо оруулана уу.'))
            
            for line in ale.line_ids:
                if line.date<=ale.last_long_date and not line.long_move_id:
                    amount+=line.amount
                    line.state='short'
            
            line_obj=self.env['account.asset.vat.line']
            lines =[(0, 0, {
                'debit': amount,
                'credit': 0,
                'account_id': ale.short_account_id.id,
#                 'analytic_account_id': line.analytic_account_id.id,
#                 'branch_id':line.branch_id and line.branch_id.id,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            })]
            lines+=[(0, 0, {
                    'name': self.name,
                    'debit': 0,
                    'credit': amount,
                    'account_id': self.long_account_id.id,
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
            ale.move_id=invoice.id
            ale.write({'long_move_ids':ale.long_move_ids.ids+[invoice.id]})
            
            for line in ale.line_ids:
                if line.date<=ale.last_long_date and not line.long_move_id:
                    line.long_move_id=invoice.id            
        return True    
    

    def create_short_move(self):
        sum_amount=0
        for ale in self:
            amount=0
            if not ale.last_short_date:
                raise UserError((u'Урт огноогоо оруулана уу.'))
            for line in ale.line_ids:
                if line.date<=ale.last_short_date and not line.short_move_id:
                    amount+=line.amount
                    line.state='done'
            
            line_obj=self.env['account.asset.vat.line']
            lines =[(0, 0, {
                'debit': amount,
                'credit': 0,
                'account_id': ale.account_id.id,
#                 'analytic_account_id': line.analytic_account_id.id,
#                 'branch_id':line.branch_id and line.branch_id.id,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            })]
            lines+=[(0, 0, {
                    'name': self.name,
                    'debit': 0,
                    'credit': amount,
                    'account_id': self.short_account_id.id,
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
            ale.move_id=invoice.id
            ale.write({'short_move_ids':ale.long_move_ids.ids+[invoice.id]})
            
            for line in ale.line_ids:
                if line.date<=ale.last_short_date and not line.short_move_id:
                    line.short_move_id=invoice.id            
        return True        
  
  
STATE_LINE = [
    ('draft', 'НООРОГ'),
    ('short', 'Богино'),
    ('long', 'Урт'),
    ('done', 'хэрэгжсэн'),
]                
class AccountAllocationExpenseLine(models.Model):
    _name = "account.asset.vat.line"
    _description = "account.asset.vat line"
    
    name = fields.Char('Утга')
    amount = fields.Float('Дүн')
    date = fields.Date('Огноо')
    parent_id      = fields.Many2one('account.asset.vat', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Данс', )
    analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )
    short_move_id      = fields.Many2one('account.move', 'Move', )
    long_move_id      = fields.Many2one('account.move', 'Move', )
                            
    state = fields.Selection(STATE_LINE, 'ТӨЛӨВ', required=True, default='draft')
                                   
class AccountAllocationExpenseConf(models.Model):
    _name = "account.asset.vat.conf"
    _description = "account.asset.vat.conf"
    
    name = fields.Char('Тайлбар')
    month = fields.Integer('Элэгдүүлэх сар')
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
    long_account_id      = fields.Many2one('account.account', 'Account long', )
    short_account_id      = fields.Many2one('account.account', 'Account short', )

    line_ids = fields.One2many('account.asset.vat.conf.line','parent_id','Lines')
              

class AccountAllocationExpenseConfLine(models.Model):
    _name = "account.asset.vat.conf.line"
    _description = "account.asset.vat conf"
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.asset.vat.conf', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )
    analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
                            

