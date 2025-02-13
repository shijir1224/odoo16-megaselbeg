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

class AccountEmployeeRec(models.Model):
    _name = "account.employee.receivable"
    _description = "account.employee.receivable"

    name = fields.Char('Name')
    date = fields.Date('Date to')
    date_from = fields.Date('Date from')
    amount = fields.Float('Amount')
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
    account_id      = fields.Many2one('account.account', 'Account', )   
    move_id      = fields.Many2one('account.move', 'Move', )   
    conf_id      = fields.Many2one('account.employee.receivable.conf', 'Config', )   
    line_ids = fields.One2many('account.employee.receivable.line','parent_id','Lines') 
    move_line_ids = fields.Many2many('account.move','account_emprec_move_rel','emp_id','move_id','Lines') 
    state = fields.Selection(STATE_SELECTION, 'ТӨЛӨВ', required=True, default='draft')
    
    # is_move = fields.Boolean('Данс хуваарилах?')
    ref_move_id = fields.Many2one('account.move.line', 'Expense entry', )   
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id, )
   
    # is_change_move = fields.Boolean('Зардлын гүйлгээг засах?')
    journal_id = fields.Many2one('account.journal', 'Journal', domain="[('type', '=', 'general')]")
    company_ids = fields.Many2many('res.company', 'account_emprec_res_com_rel', 'conf_id', 'company_id', string="Company")
    
    @api.onchange('ref_move_id')
    def onchange_ref_move_id(self):
        if self.ref_move_id:
            self.amount = self.ref_move_id.debit
            self.account_id = self.ref_move_id.account_id.id
            self.journal_id=self.ref_move_id.journal_id.id
                
                                    
    def compute(self):
        for ale in self:
            partner_ids=[]
            # self.env['res.partner'].search([('','=',False)])
            for company in self.company_ids:
                partner_ids=self.env['hr.employee'].sudo().search_read([('partner_id','!=',False),
                                                                    ('company_id','=',company.id),
                                                                   # ('company_id','!=',self.company_id.id),
                                                                    # ('company_id','in',self.company_ids.ids),
                                                                   ], ['partner_id','company_id'])
                
                # .search_read([('company_id', '=', self.company_id.id)], ['code'])
                                                                   
                # print ('partner_ids ',partner_ids)
                account_ids=self.env['account.account'].sudo().search([
                                                                    # ('account_type','=','asset_receivable'),
                                                                    '|','|','|',
                                                                    ('is_coffee','=',True),
                                                                    ('is_drug','=',True),
                                                                    ('is_shop','=',True),
                                                                    ('is_food','=',True),
                                                                   # ('company_id','!=',company.id),
                                                                   ])

                print ('account_ids123 ',account_ids)
                for partner in partner_ids:
                    # ale.line_ids.unlink()
                    # print ('partner ',partner)
                    # emp_company=self.env['hr.employee'].sudo().search([('partner_id','=',partner.id),
                    #                                                    ('partner_id','=',partner.id),
                    #                                                    ('company_id','!=',company.id),
                    #                                                ],limit=1).company_id
                    # print ('emp_company ',emp_company)
                    line_obj=self.env['account.employee.receivable.line']
                    sum_line=0
                    move_ids=self.env['account.move.line'].sudo().search([('partner_id','=',partner.get('partner_id')[0]),
                                                                          ('account_id','in',account_ids.ids),
                                                                          ('date','>',ale.date_from),
                                                                          ('date','<=',ale.date),
                                                                           ('company_id','=',self.company_id.id),
                                                                           ('move_id.state','=','posted'),
                                                                           ('amount_residual','>',0),
                                                                           # ('company_id','in',self.company_ids.ids),
                                                                          ])
                    if move_ids:
                        # print ('move_ids ',move_ids.ids)
                        # balance = sum(move_ids.mapped('debit'))-sum(move_ids.mapped('credit'))
                        balance = sum(move_ids.mapped('amount_residual'))

                    # for line in ale.conf_id.line_ids:
                        # amount=line.amount*ale.amount/sum_line
                        # account_id=line.account_id and line.account_id.id or False
                        # if not account_id and ale.change_move_id:
                        #     account_id=ale.change_move_id.account_id.id
                        move=line_obj.create({'name':move_ids[0].name,
                                         'partner_id':partner.get('partner_id')[0],
                                         'amount':balance,
                                         'account_id':move_ids[0].account_id.id,
                                         'move_ids':[(6, 0, move_ids.ids)],
                                         # 'rec_com_id':company.id,
                                         # 'pay_com_id':partner.get('company_id')[0],
                                        'rec_com_id':move_ids[0].company_id.id,
                                        'pay_com_id':company.id,
    #                                      'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
                                        # 'analytic_distribution':line.analytic_distribution,
                                         'parent_id':ale.id
                                         })
    #                     print ('move::: ',move)
    #                     move.action_asset_moves()
            # else:
            #     raise UserError((u'Компани сонгогдоогүй байна !!!.'))
                
            ale.state='computed'
        return True    
    
                 
    def set_draft(self):
        for ale in self:
            ale.state='draft'
        return True    
    
    
    def create_move(self):
        for ale in self:
            line_obj=self.env['account.employee.receivable.line']
            data={}
            lines=[]
            pay_lines=[]
            sum_amount=0
            invoice_ids=[]
            rec_com=False
            pay_com_id=False
            for line_com in self.line_ids:
                rec_com = line_com.rec_com_id.id
                pay_com_id=line_com.pay_com_id.id
            vals={'ref':ale.name,
                    # 'partner_id':line.partner_id.id,
                    'company_id':pay_com_id,
                    # 'line_ids':lines
                    }

            invoice = self.env['account.move'].sudo().create(vals)
            invoice_ids.append(invoice.id)
            # self.write({'move_line_ids':[(6, 0, invoice_ids)]})
#1 move
            vals2={'ref':ale.name,
                # 'partner_id':line.partner_id.id,
                'company_id':rec_com,
                # 'line_ids':pay_lines
                }
            invoice2 = self.env['account.move'].sudo().create(vals2)
            invoice_ids.append(invoice2.id)
            self.write({'move_line_ids':[(6, 0, invoice_ids)]})            
            for line in self.line_ids:
                # # pay_lines=[]
                # pay_lines+=[(0, 0, {
                #         'name': self.name + u' ажилтны авлага '+line.rec_com_id.name,
                #         'debit': 0,
                #         'credit': line.amount,
                #         'account_id': line.pay_com_id.emp_pay_account_id.id,
                #         'partner_id':line.rec_com_id.partner_id.id,
                #         'company_id':line.pay_com_id.id,
                #         'emp_partner_id':line.pay_com_id.partner_id.id,
                #         'move_id':invoice.id
                # })]
                # pay_lines+=[(0, 0, {
                #         'name': self.name + u' ажилтны авлага '+line.rec_com_id.name,
                #         'debit': line.amount,
                #         'credit': 0,
                #         'account_id': line.pay_com_id.emp_rec_account_id.id,
                #         'partner_id':line.partner_id.id,
                #         'company_id':line.pay_com_id.id,
                #         'emp_partner_id':line.pay_com_id.partner_id.id,
                #         'move_id':invoice.id
                # })]           

                pay_lines={
                        'name': self.name + u' ажилтны авлага '+line.rec_com_id.name,
                        'debit': 0,
                        'credit': line.amount,
                        'account_id': line.pay_com_id.emp_pay_account_id.id,
                        'partner_id':line.rec_com_id.partner_id.id,
                        'company_id':line.pay_com_id.id,
                        'emp_partner_id':line.pay_com_id.partner_id.id,
                        'move_id':invoice.id
                }
                line_id = self.env['account.move.line'].sudo().with_context(check_move_validity=False).create(pay_lines)
                line.pay_aml_id=line_id.id
                    
                pay_lines={
                        'name': self.name + u' ажилтны авлага '+line.rec_com_id.name,
                        'debit': line.amount,
                        'credit': 0,
                        'account_id': line.pay_com_id.emp_rec_account_id.id,
                        'partner_id':line.partner_id.id,
                        'company_id':line.pay_com_id.id,
                        'emp_partner_id':line.pay_com_id.partner_id.id,
                        'move_id':invoice.id
                }                        
                line_id2 = self.env['account.move.line'].sudo().with_context(check_move_validity=False).create(pay_lines)
                line.pay_aml_id2=line_id2.id
                pay_com_id=line.pay_com_id.id
                # vals2={'ref':ale.name,
                #     # 'partner_id':line.partner_id.id,
                #     'company_id':line.pay_com_id.id,
                #     'line_ids':pay_lines}
                # invoice2 = self.env['account.move'].sudo().create(vals2)
                # invoice_ids.append(invoice2.id)
                #
                lines={
                        'name': self.name + u' ажилтны авлага',
                        'debit': 0,
                        'credit': line.amount,
                        'account_id': line.account_id.id,
                        'partner_id':line.partner_id.id,
                        'emp_partner_id':line.pay_com_id.partner_id.id,
                        'move_id':invoice2.id
                }
                line_id3 = self.env['account.move.line'].sudo().with_context(check_move_validity=False).create(lines)
                line.rec_aml_id=line_id3.id
                lines={
                            'name': self.name + u' ажилтны авлага',
                            'debit': line.amount,
                            'credit': 0,
                            'account_id': line.rec_com_id.emp_rec_account_id.id,
                            'partner_id':line.pay_com_id.partner_id.id,
                            'emp_partner_id':line.pay_com_id.partner_id.id,
                            'move_id':invoice2.id
                    }
                line_id4 = self.env['account.move.line'].sudo().with_context(check_move_validity=False).create(lines)
                line.rec_aml_id2=line_id4.id
                
#             vals={'ref':ale.name,
#                     # 'partner_id':line.partner_id.id,
#                     'company_id':line.rec_com_id.id,
#                     'line_ids':lines}
#
#             invoice = self.env['account.move'].sudo().create(vals)
#             invoice_ids.append(invoice.id)
#             # self.write({'move_line_ids':[(6, 0, invoice_ids)]})
# #1 move
#             vals2={'ref':ale.name,
#                 # 'partner_id':line.partner_id.id,
#                 'company_id':pay_com_id,
#                 'line_ids':pay_lines}
#             invoice2 = self.env['account.move'].sudo().create(vals2)
#             invoice_ids.append(invoice2.id)
#             self.write({'move_line_ids':[(6, 0, invoice_ids)]})
            
            
        #         invoice.message_post_with_view('mail.message_origin_link',
        #                     values={'self': invoice, 'origin': line.contract_id},
        #                     subtype_id=self.env.ref('mail.mt_note').id)
        return True    
  
    def post_reconcile(self):
        for line in self.line_ids:
            if line.rec_aml_id and line.rec_aml_id2 and line.pay_aml_id and line.pay_aml_id2:
                if line.rec_aml_id.move_id.state=='draft':
                    line.rec_aml_id.move_id.action_post()
                for move in line.move_ids:
                    # line_r=move.line_ids.filtered(lambda l: l.account_id.id==rec_aml_id.account_id.id)
                    if not line.rec_aml_id.reconciled and not move.reconciled:
                        # print ('line.reconcile ',line.rec_aml_id.reconcile)
                        # print ('line.account_id ',line.rec_aml_id.account_id)
                        #
                        # print ('move.move ',move.reconcile)
                        # print ('move.account_id ',move.account_id)
    
                        (line.rec_aml_id | move).reconcile()
            else:
                raise UserError((u'{0} мөрөнд гүйлгээ хоосон байна байна !!!.'.format(line.name)))                
            
    # rec_aml_id      = fields.Many2one('account.move.line', 'Авлага1', )
    # rec_aml_id2      = fields.Many2one('account.move.line', 'Авлага2', )
    #
    # pay_aml_id      = fields.Many2one('account.move.line', 'Өглөг1', )
    # pay_aml_id2      = fields.Many2one('account.move.line', 'Өглөг2', )
                

    def create_move_old(self):
        for ale in self:
            line_obj=self.env['account.employee.receivable.line']
            data={}
            lines=[]
            pay_lines=[]
            sum_amount=0
            invoice_ids=[]
            for line in self.line_ids:
                # pay_lines=[]
                pay_lines+=[(0, 0, {
                        'name': self.name + u' ажилтны авлага '+line.rec_com_id.name,
                        'debit': 0,
                        'credit': line.amount,
                        'account_id': line.pay_com_id.emp_pay_account_id.id,
                        'partner_id':line.rec_com_id.partner_id.id,
                        'company_id':line.pay_com_id.id,
                        'emp_partner_id':line.pay_com_id.partner_id.id,
                })]
                pay_lines+=[(0, 0, {
                        'name': self.name + u' ажилтны авлага '+line.rec_com_id.name,
                        'debit': line.amount,
                        'credit': 0,
                        'account_id': line.pay_com_id.emp_rec_account_id.id,
                        'partner_id':line.partner_id.id,
                        'company_id':line.pay_com_id.id,
                        'emp_partner_id':line.pay_com_id.partner_id.id,
                })]              
                pay_com_id=line.pay_com_id.id
                # vals2={'ref':ale.name,
                #     # 'partner_id':line.partner_id.id,
                #     'company_id':line.pay_com_id.id,
                #     'line_ids':pay_lines}
                # invoice2 = self.env['account.move'].sudo().create(vals2)
                # invoice_ids.append(invoice2.id)
                #
                lines+=[(0, 0, {
                        'name': self.name + u' ажилтны авлага',
                        'debit': 0,
                        'credit': line.amount,
                        'account_id': line.account_id.id,
                        'partner_id':line.partner_id.id,
                        'emp_partner_id':line.pay_com_id.partner_id.id,
                })]
                lines+=[(0, 0, {
                            'name': self.name + u' ажилтны авлага',
                            'debit': line.amount,
                            'credit': 0,
                            'account_id': line.rec_com_id.emp_rec_account_id.id,
                            'partner_id':line.pay_com_id.partner_id.id,
                            'emp_partner_id':line.pay_com_id.partner_id.id,
                    })]
            vals={'ref':ale.name,
                    # 'partner_id':line.partner_id.id,
                    'company_id':line.rec_com_id.id,
                    'line_ids':lines}

            invoice = self.env['account.move'].sudo().create(vals)
            invoice_ids.append(invoice.id)
            # self.write({'move_line_ids':[(6, 0, invoice_ids)]})
#1 move
            vals2={'ref':ale.name,
                # 'partner_id':line.partner_id.id,
                'company_id':pay_com_id,
                'line_ids':pay_lines}
            invoice2 = self.env['account.move'].sudo().create(vals2)
            invoice_ids.append(invoice2.id)
            self.write({'move_line_ids':[(6, 0, invoice_ids)]})
            
            
        #         invoice.message_post_with_view('mail.message_origin_link',
        #                     values={'self': invoice, 'origin': line.contract_id},
        #                     subtype_id=self.env.ref('mail.mt_note').id)
        return True    
  
  
    def _prepare_line_values(self, order, line):
        name=order.name or ''
        amount=line.amount
            
        line_vals =[(0, 0, {
                'debit': round(amount,2),
                'credit': 0,
                'account_id': line.account_id.id,
                # 'analytic_distribution': line.analytic_distribution,
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
                # 'analytic_distribution': line.analytic_distribution,
                'branch_id':line.branch_id and line.branch_id.id,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            }

        return line_vals             
            
class AccountEmployeeRecLine(models.Model):
    _name = "account.employee.receivable.line"
    _description = "account.employee.receivable line"
    _inherit = 'analytic.mixin'    
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.employee.receivable', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )

    partner_id      = fields.Many2one('res.partner', 'Partner', )
    rec_com_id      = fields.Many2one('res.company', 'Авлагын компани', )
    pay_com_id      = fields.Many2one('res.company', 'Өглөнийн компани', )
    move_ids = fields.Many2many('account.move.line', 'account_emprec_aml_rel', 'conf_id', 'account_id', string="Moves")

    rec_aml_id      = fields.Many2one('account.move.line', 'Авлага1', )
    rec_aml_id2      = fields.Many2one('account.move.line', 'Авлага2', )
    
    pay_aml_id      = fields.Many2one('account.move.line', 'Өглөг1', )
    pay_aml_id2      = fields.Many2one('account.move.line', 'Өглөг2', )
    
class AccountEmployeeRecMoveLine(models.Model):
    _name = "account.employee.receivable.move.line"
    _description = "account.employee.receivable move line"
    _inherit = 'analytic.mixin'    
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.employee.receivable', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )

    partner_id      = fields.Many2one('res.partner', 'Partner', )
    rec_com_id      = fields.Many2one('res.company', 'Авлагын компани', )
    pay_com_id      = fields.Many2one('res.company', 'Өглөнийн компани', )
    move_id = fields.Many2many('account.move', 'account_emprec_am_rel', 'conf_id', 'account_id', string="Moves")
                                   
                                   
                                                                      
class AccountEmployeeRecConf(models.Model):
    _name = "account.employee.receivable.conf"
    _description = "account.employee.receivable.conf"
    
    name = fields.Char('Тайлбар')
    branch_id = fields.Many2one('res.branch', 'New Branch')
    expense_type = fields.Selection([('consume', 'АБХ'), ('asset', 'Үндсэн хөрөнгө'), ('product_expense', 'Шаардах'), ('other', 'Бусад')],
                                    default='other', required=True, string='Хуваарилах төрөл')
    line_ids = fields.One2many('account.employee.receivable.conf.line','parent_id','Lines',copy=True)
    account_ids = fields.Many2many('account.account', 'account_emprec_accunt_account_rel', 'conf_id', 'account_id', string="Account")


class AccountEmployeeRecConfLine(models.Model):
    _name = "account.employee.receivable.conf.line"
    _description = "account.employee.receivable conf"
    _inherit = 'analytic.mixin' 
    
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    parent_id      = fields.Many2one('account.employee.receivable.conf', 'Parent', )
    account_id      = fields.Many2one('account.account', 'Account', )
    analytic_account_id      = fields.Many2one('account.analytic.account', ' Analytic account', )
    branch_id      = fields.Many2one('res.branch', 'New Branch', )   
                      

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'
                            
    emp_partner_id      = fields.Many2one('res.partner', 'Ажилтны авлагын компани', )                            