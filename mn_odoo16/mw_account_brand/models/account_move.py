# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    brand_id = fields.Many2one('product.brand',)


class AccountAllocationExpenseConfLine(models.Model):
    _inherit = "account.allocation.expense.conf.line"
    
    brand_id = fields.Many2one('product.brand',)


class AccountAllocationExpenseLine(models.Model):
    _inherit = "account.allocation.expense.line"
    
    brand_id = fields.Many2one('product.brand',)




class AccountAllocationExpense(models.Model):
    _inherit = "account.allocation.expense"


#     @api.onchange('ref_move_id')
#     def onchange_ref_move_id(self):
#         print ('self.ref_move_id ',self.ref_move_id)
#         if self.ref_move_id:
#             self.amount = self.ref_move_id.credit
#             self.account_id = self.ref_move_id.account_id.id
#                 
# 
#     @api.onchange('change_move_id')
#     def onchange_ref_move_id(self):
#         print ('self.ref_move_id ',self.change_move_id)
#         if self.change_move_id:
#             self.amount = self.change_move_id.debi
#             self.account_id = self.change_move_id.account_id.id
                
    def compute(self):
        for ale in self:
            if ale.conf_id:
                ale.line_ids.unlink()
                line_obj=self.env['account.allocation.expense.line']
                sum_line=0
                for line in ale.conf_id.line_ids:
                    sum_line+=line.amount
                for line in ale.conf_id.line_ids:
                    amount=round(line.amount*ale.amount/sum_line,2)
                    move=line_obj.create({'name':line.name,
                                     'branch_id':line.branch_id and line.branch_id.id or False,
                                     'amount':amount,
                                     'account_id':line.account_id and line.account_id.id or False,
                                     # 'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
                                     'parent_id':ale.id,
                                     'brand_id':line.brand_id and line.brand_id.id or False,
                                     'analytic_distribution':line.analytic_distribution,
                                     })
            else:
                raise UserError((u'Тохиргоо сонгогдоогүй байна !!!.'))
                
#                     print ('move::: ',move)
#                     move.action_asset_moves()
            ale.state='computed'
        return True    
                
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
                'brand_id':line.brand_id and line.brand_id.id,
                # 'analytic_account_id': line.analytic_account_id.id,
                'branch_id':line.branch_id and line.branch_id.id,
                'analytic_distribution': line.analytic_distribution,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            }

        return line_vals             
            
    def create_move(self):
        sum_amount=0
        for ale in self:
            line_obj=self.env['account.allocation.expense.line']
            print ('ale.is_change_move ',ale.is_change_move)
            if ale.is_change_move and ale.change_move_id:
                sum_line=0
                lines=[]
                move_id=ale.change_move_id.move_id.id
                commands = [(2, ale.change_move_id.id, False)]
                for line in ale.line_ids:
                    print ('commands2 ',commands)
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
                        'brand_id':line.brand_id and line.brand_id.id,
                        # 'analytic_account_id': line.analytic_account_id.id,
                        'branch_id':line.branch_id and line.branch_id.id,
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
    
#     def create_move(self):
#         sum_amount=0
#         for ale in self:
#             line_obj=self.env['account.allocation.expense.line']
#             sum_line=0
#             lines=[]
#             for line in ale.line_ids:
#                 lines+=self._prepare_line_values(ale,line)
#                 sum_amount+=round(line.amount,2)
# #         print ('lines ',lines)
#         lines+=[(0, 0, {
#                 'name': self.name,
#                 'debit': 0,
#                 'credit': sum_amount,
#                 'account_id': self.account_id.id,
#                 'brand_id':line.brand_id and line.brand_id.id,
# #                 'analytic_account_id': line.analytic_account_id.id,
# #                 'branch_id':line.branch_id and line.branch_id.id,
# #                 'tax_ids': [(6, 0, line.tax_id.ids)],
# #                 'sale_line_ids': [(6, 0, [line.id])],
# #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
# #                 'analytic_account_id': order.analytic_account_id.id or False,
#         })]
#         vals={'ref':ale.name,
#               'line_ids':lines}
#         invoice = self.env['account.move'].sudo().create(vals)#.with_user(self.env.uid)
# #         invoice.message_post_with_view('mail.message_origin_link',
# #                     values={'self': invoice, 'origin': line.contract_id},
# #                     subtype_id=self.env.ref('mail.mt_note').id)
#         self.move_id=invoice.id
#         return True    
  
  
    def _prepare_line_values(self, order, line):
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
            
        line_vals =[(0, 0, {
                'debit': round(amount,2),
                'credit': 0,
                'account_id': line.account_id.id,
                # 'analytic_account_id': line.analytic_account_id.id,
                'branch_id':line.branch_id and line.branch_id.id,
                'brand_id':line.brand_id and line.brand_id.id,
                'analytic_distribution': line.analytic_distribution,
#                 'tax_ids': [(6, 0, line.tax_id.ids)],
#                 'sale_line_ids': [(6, 0, [line.id])],
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'analytic_account_id': order.analytic_account_id.id or False,
            })]

        return line_vals 
            