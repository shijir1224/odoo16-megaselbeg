# -*- coding: utf-8 -*-
##############################################################################
#
#    ManageWall, Enterprise Management Solution    
#    Copyright (C) 2007-2014 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#
#    Email : daramaa26@gmail.com
#    Phone : 976 + 99081691
#
##############################################################################
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime, time, timedelta
from datetime import date, datetime
    
import logging
_logger = logging.getLogger(__name__)

class bank_payment_match_line(models.TransientModel):

    _name = "bank.payment.match.line"
    _description = "partial bank confirm line"
#     _rec_name = 'line_id'

    name=fields.Char("Name")
    account_id=fields.Many2one('account.account', string="Account", )
    amount=fields.Float("Amount", )
    line_id=fields.Many2one('account.bank.statement.line', "Move", )
    wizard_id=fields.Many2one('bank.payment.match', string="Wizard", ondelete='CASCADE',readonly=True)
    currency=fields.Many2one('res.currency', string="Currency", help="Currency in which Unit cost is expressed", ondelete='CASCADE',readonly=True)
    date=fields.Date('Date', )
    payment_id=fields.Many2one('account.move.line', 'Payment', )
    partner_id=fields.Many2one('res.partner', 'Partner', )

class bank_payment_match(models.TransientModel):
    
    _name = "bank.payment.match"
 # _rec_name = 'statement_id'
    _description = "Partial bank statement confirm Wizard"
    
    def search_partner(self,key,value):
        partner_id=False
        sql='''
            select id,regexp_matches('{0}',{1}) from res_partner
        '''.format(value,key)
        self._cr.execute(sql)
        partners = self._cr.fetchall()
        if partners:                        
#             print ('partners11 ' ,partners)
            for p in partners:
                if p[1][0]:
                    partner_id=p[0]    
        return partner_id
    

    def search_payment(self,partner_id,account_id,line):
        payment_ids=[]
#         if account_id.internal_type =='receivable' and line.amount>0:
        if line.amount>0:
            payment_ids=self.env['account.move.line'].search([('partner_id','=',partner_id),
#                                                             ('account_id','=',account_id.id),
                                                            ('debit','>',0),
                                                            ('amount_residual','>',0),
                                                            ('account_type','=','asset_receivable'),
                                                            ('move_id.state','=','posted'),
                                                            ],order='date, id ')
            
#         print ('payment_ids ',payment_ids)
        return payment_ids    
    

    def search_payment_payable(self,partner_id,account_id,line):
        payment_ids=[]
#         if account_id.internal_type =='receivable' and line.amount>0:
        if line.amount<0:
            print ('partner_id ',partner_id)
            payment_ids=self.env['account.move.line'].search([('partner_id','=',partner_id),
#                                                             ('account_id','=',account_id.id),
                                                            ('credit','>',0),
                                                            ('amount_residual','!=',0),
                                                            ('account_type','=','liability_payable'),
                                                            ('move_id.state','=','posted'),
                                                            ],order='date, id ')
            
#         print ('payment_ids ',payment_ids)
        return payment_ids        
    
    def search_contract(self,key,value,line):
        partner_id=False
#         sql='''
#             select id,regexp_matches('{0}',{1}) from account_move_line where id not in ({2})
#         '''.format(value,key,','.join(map(str, line.move_id.line_ids.ids)))
#         _logger.info('query %s'%(sql))
#         self._cr.execute(sql)
#         contracts = self._cr.fetchall()
#         contract_id=False
#         if contracts:                        
#             print ('contracts ' ,contracts)
#             for p in contracts:
#                 if p[1][0]:
#                     contract_id=p[0]
        for s in value.split(' '):
            sql='''
                select id from account_move_line where id not in ({2}) and name like '{0}%'
            '''.format(s,key,','.join(map(str, line.move_id.line_ids.ids)))
            _logger.info('query %s'%(sql))
            self._cr.execute(sql)
            contracts = self._cr.fetchall()
            contract_id=False
            if contracts:                        
                print ('contracts ' ,contracts)
                for p in contracts:
#                     if p[1][0]:
                    contract_id=p[0]
                break    
        return contract_id
    

    def search_partner_vat(self,key,value):
        partner_id=False
#         select id, vat from res_partner where (
#         'мөргөсөн' = ANY (string_to_array(REPLACE (vat, ' ', ','),','))
#         or 'ТХ-Араас' = ANY (string_to_array(REPLACE (vat, ' ', ','),','))
#               )
#         limit 1000
        
        sql='''
            select id,name from res_partner where vat = '{0}'
        '''.format(value,key)
        self._cr.execute(sql)
        partners = self._cr.fetchall()
        partner_id=False
        if partners:                        
            for p in partners:
                if p[1][0]:
                    partner_id=p[0]
#         else:
#             sql='''
#                 select id,name from insurance_contract where hp_id like '%{0}%'
#             '''.format(value,key)
#             print ('sql2 ',sql)
#             self._cr.execute(sql)
#             contracts = self._cr.fetchall()
#             partner_id=False
#             if contracts:                        
#                 print ('contracts ' ,contracts)
#                 for p in contracts:
#                     if p[1][0]:
#                         partner_id=p[0]                        
        return partner_id
        

    @api.model
    def _default_lines(self):
        context = self._context
        statement_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
  # statement_id = statement_ids[0]
        statement_lines=self.env['account.bank.statement.line'].browse(statement_ids)
        vals= []
        payment_id=False
        ins_payment_id=False
        _logger.info('statement_ids %s'%(statement_ids))
        
        for line in statement_lines:
#             if ((not line.journal_entry_ids) and (not line.account_id or not line.partner_id )):
            if (not line.account_id or not line.partner_id):# and line.amount>0:
                _logger.info('line %s'%(line))
                account_id=line.account_id and line.account_id
                partner_id=line.partner_id and line.partner_id.id 
                contract_id=False
                if not partner_id or not account_id:
#                     if line.bank_account_id:
#                         partner_id=line.bank_account_id.partner_id.id
# #                     elif line.partner_print:
# # #                         partners=self.env['res.partner'].search([('name','in',line.partner_print)])
# #                         partner_id=self.search_partner('vat',line.partner_print)
# #                         if not partner_id:
# #                             partner_id=self.search_partner('vat_company',line.partner_print)
# #                             if not partner_id:
# #                                 partner_id=self.search_partner('name',line.partner_print)
# #                         if not partner_id:
# #                             partner_id=self.search_partner('vat',line.name)
# #                             if not partner_id:
# #                                 partner_id=self.search_partner('name',line.name)
#                     else:
#                         partner_id=self.search_partner('vat',line.name)
#                         if not partner_id:
#                             partner_id=self.search_partner('name',line.name)
                    name=line.payment_ref #.replace('/','')
                    name=name.replace(',',' ')
                    for i in name.split(' '):
                        _logger.info('i %s'%(i))
                        i=i.replace(' ','')
                        if len(i)>2:
                            partner_id=self.search_partner_vat('name',i)
                            _logger.info('partner_id %s'%(partner_id))
                            if partner_id:
                                break
                if partner_id: # and account_id and not payment_id:
                    if line.amount>0:
                        payment_ids = self.search_payment(partner_id,account_id,line)
                    else:
                        payment_ids = self.search_payment_payable(partner_id,account_id,line)
                    check_res=abs(line.amount)
                    duussan=False
                    for pp in payment_ids:
                        if abs(pp.amount_residual)<=abs(check_res):
                            amount_residual=abs(pp.amount_residual)
                            check_res-=abs(pp.amount_residual)
                        else:
                            duussan=True
                            amount_residual=check_res
                        vals.append((0,0,{
                        'amount':amount_residual,
                        'account_id':pp.account_id and pp.account_id.id or False,
                        'date':line.date,
                        'name':line.name,
                        'partner_id':partner_id,
                        'line_id':line.id,
                        'payment_id':pp.id
                        }))
                        if duussan:
                            break
        return vals
    
    date=fields.Date('Date',)
    line_ids=fields.One2many('bank.payment.match.line', 'wizard_id', 'Lines',default=_default_lines)
 # statement_id=fields.Many2one('account.bank.statement', 'Statement', required=True, ondelete='CASCADE')
#     bank_lines=fields.Many2many('account.bank.statement.line', 'part_bank_rel','wizard_id', 'line_id','Product Moves')

    

    @api.model
    def default_get(self, fields):
        context = self._context
        res = super(bank_payment_match, self).default_get(fields)
        statement_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        if not statement_ids or len(statement_ids) != 1:
            return res
        assert active_model in ('account.bank.statement.line',), 'Bad context propagation'
        return res
    
    def confirm(self):
        account_statement = self.pool.get('account.bank.statement')
        account_statement_line = self.pool.get('account.bank.statement.line')
  # split_line=self.env['account.bank.statement.split.line']
        amsl_vals = []
        if self.line_ids.line_id.import_aml_ids:
            self.line_ids.line_id.import_aml_ids.unlink()
  # if self.line_ids.line_id.split_line_ids:
  #     self.line_ids.line_id.split_line_ids.unlink()

        for wizard_line in self.line_ids:
            if wizard_line.line_id:
                employee_id=False
                branch_id=False
                cash_type_id=False
                name=""
                account_id=wizard_line.account_id.id
                partner_id=wizard_line.partner_id.id
                if not wizard_line.line_id.account_id and wizard_line.account_id:
                    wizard_line.line_id.write({'account_id':wizard_line.account_id.id})
                if not wizard_line.line_id.partner_id and wizard_line.partner_id:
                    wizard_line.line_id.write({'partner_id':wizard_line.partner_id.id})
    # sp_vals=self._get_sp_vals(partner_id,account_id,wizard_line.line_id,wizard_line,employee_id,cash_type_id,branch_id)
    # split_id=split_line.create(sp_vals)
                if wizard_line.payment_id:
                    amsl_vals = [(0,0,{
                                        'import_aml_id':wizard_line.payment_id.id,
                                        'is_mnt':True,
                                        'aml_amount':wizard_line.amount
                                            })]
                    wizard_line.line_id.write({'import_aml_ids':amsl_vals,
                                                })
                    wizard_line.line_id.button_validate_line()
#             if wizard_line.ins_payment_id:
#                 wizard_line.ins_payment_id.paid_amount=wizard_line.amount
                
        return {'type': 'ir.actions.act_window_close'}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
