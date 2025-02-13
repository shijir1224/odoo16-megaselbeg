# -*- coding: utf-8 -*-
import calendar
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import fields, models, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    is_expense_split      = fields.Boolean('Зардал хуваах?', )   
    allocation_id      = fields.Many2one('account.allocation.expense.conf', 'Зардал хаваах тохиргоо', )   
    journal_id = fields.Many2one('account.journal', string='journal', store=True)


        
class AccountAssetMoveLine(models.Model):
    _inherit = 'account.asset.move.line'
    
    old_allocation_id      = fields.Many2one('account.allocation.expense.conf', 'Зардал тохиргоо', )   
    new_allocation_id      = fields.Many2one('account.allocation.expense.conf', 'Шинэ зардал тохиргоо', )   


    @api.model
    def create(self, values):
        # Хөрөнгийг сонгосон тохиолдолд тухайн хөрөнгийн мэдээллээр мөрийг шинэчилж үүсгэх
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'old_allocation_id': asset.allocation_id.id,
            })
        return super(AccountAssetMoveLine, self).create(values)

    def write(self, values):
        # Хөрөнгийг өөрчилсөн, шинээр бичсэн тохиолдолд тухайн хөрөнгийн мэдээллээр мөрийг шинэчилж үүсгэх
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'old_allocation_id': asset.allocation_id.id,
            })
        return super(AccountAssetMoveLine, self).write(values)

    def get_recieve_values(self):
        res = super(AccountAssetMoveLine, self).get_recieve_values()
        if self.new_allocation_id:
            res.update({'allocation_id':self.new_allocation_id.id})
        return res

#     @api.onchange('asset_id')
#     def onchange_asset(self):
#         if not self.asset_id:
#             return
#         self.old_allocation_id = self.asset_id.allocation_id.id
        
# class AccountAssetDepreciationLine(models.Model):
#     _inherit = 'account.asset.depreciation.line'
#     _order = 'sequence'

#     def _prepare_expense_move(self, line):
#         allocation_id=line.asset_id.allocation_id
#         category_id = line.asset_id.category_id
#         asset_exp_id = line.asset_id
#         account_analytic_id = line.asset_id.account_analytic_id
#         analytic_tag_ids = line.asset_id.analytic_tag_ids
#         depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
#         company_currency = line.asset_id.company_id.currency_id
#         current_currency = line.asset_id.currency_id
#         prec = company_currency.decimal_places
#         amount = current_currency._convert(
#             line.amount, company_currency, line.asset_id.company_id, depreciation_date)
#         asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
#         move_line_1 = {
#             'name': asset_name,
#             'account_id': asset_exp_id.account_depreciation_id.id,
#             'debit': 0.0 if float_compare(round(amount,2), 0.0, precision_digits=prec) > 0 else round(-amount,2),
#             'credit': round(amount,2) if float_compare(round(amount,2), 0.0, precision_digits=prec) > 0 else 0.0,
#             'partner_id': line.asset_id.partner_id.id,
#             'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
#             'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
#             'currency_id': company_currency != current_currency and current_currency.id or False,
#             'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
#             'asset_id':line.asset_id.id
#         }
#         lines=[(0, 0, move_line_1)]
#         if allocation_id:
#             sum_line=0
#             check_sum=0
#             for l in allocation_id.line_ids:
#                 sum_line+=l.amount
            
#             for l in allocation_id.line_ids:
#                 amount_sub=round(amount*l.amount/sum_line,2)
#                 check_sum+=amount_sub
#                 lines+= [(0,0,{
#                     'name': asset_name,
# #                     'account_id': category_id.account_depreciation_expense_id.id,
#                      'account_id':(l.account_id and l.account_id.id) or (asset_exp_id.account_depreciation_expense_id and asset_exp_id.account_depreciation_expense_id.id) or category_id.account_depreciation_expense_id.id,
#                     'credit': 0.0 if float_compare(round(amount,2), 0.0, precision_digits=prec) > 0 else round(-amount,2),
#                     'debit': round(amount_sub,2),
#                     'partner_id': line.asset_id.partner_id.id,
# #                     'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
#                      'analytic_account_id':l.analytic_account_id and l.analytic_account_id.id or False,
#                     'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
#                     'currency_id': company_currency != current_currency and current_currency.id or False,
#                     'amount_currency': company_currency != current_currency and line.amount or 0.0,
#                     'branch_id':l.branch_id and l.branch_id.id or False,
#                     'brand_id':l.brand_id and l.brand_id.id or False,
#                     'asset_id':line.asset_id.id
#                 })]

#             if check_sum!=round(amount,2):
#                 zuruu=round(amount,2)-check_sum
#                 for i in lines:
#                     if i[2]['debit']>0:
#                         i[2]['debit']+=zuruu
#                         break
                
# #         print ('lines123 ',lines)
#         move_vals = {
#             'ref': line.asset_id.code,
#             'date': depreciation_date or False,
#             'journal_id': category_id.journal_id.id,
#             'line_ids': lines,
#         }
#         return move_vals
# # 

#     def create_move(self, post_move=True):
#         created_moves = self.env['account.move']
#         for line in self:
#             if line.move_id:
#                 line.cancel_move()
#             else:
#                 # Тухайн элэгдлээс өмнөх элэгдлүүдийг батлаагүй бол алдааны мэдээлэл өгнө. Энэ нь элэгдлийн самбар зөв ажиллахад зориулсан болно
#                 unposted_lines = self.search([('asset_id', '=', line.asset_id.id), ('depreciation_date', '<', line.depreciation_date), ('move_check', '=', False), ('id', '!=', line.id)])
#                 if unposted_lines:
#                     raise UserError("Before depreciation line cannot approve! {}".format(line.asset_id.code))
#                 if line.asset_id.is_expense_split and line.asset_id.allocation_id:
#                     move_vals = self._prepare_expense_move(line)
#                 else:
#                     move_vals = self._prepare_move(line)
#                 print ('move_vals ',move_vals)
#                 move = self.env['account.move'].create(move_vals)
#                 line.write({'move_id': move.id, 'move_check': True, 'move_posted_check': True})
#                 created_moves |= move
#         created_moves.action_post()
# #         if post_move and created_moves:
# #         created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).action_post()
#         return [x.id for x in created_moves]
#     def _prepare_move(self, line):
#         category_id = line.asset_id.category_id
#         asset_exp_id = line.asset_id
#         account_analytic_id = line.asset_id.account_analytic_id
#         analytic_tag_ids = line.asset_id.analytic_tag_ids
#         depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
#         company_currency = line.asset_id.company_id.currency_id
#         current_currency = line.asset_id.currency_id
#         prec = company_currency.decimal_places
#         amount = current_currency._convert(
#             line.amount, company_currency, line.asset_id.company_id, depreciation_date)
#         asset_name = line.asset_id.journal_name or ' '+ ' ' + line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
#         move_line_1 = {
#             'name': asset_name,
#             'account_id': category_id.account_depreciation_id.id,
#             'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
#             'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
#             'partner_id': line.asset_id.partner_id.id,
#             'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
#             'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
#             'currency_id': company_currency != current_currency and current_currency.id or False,
#             'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
#             'asset_id': line.asset_id.id
#         }
#         move_line_2 = {
#             'name': asset_name,
#    		 	'account_id':asset_exp_id.account_depreciation_expense_id and asset_exp_id.account_depreciation_expense_id.id or category_id.account_depreciation_expense_id.id,
#             'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
#             'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
#             'partner_id': line.asset_id.partner_id.id,
#             'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
#             'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
#             'currency_id': company_currency != current_currency and current_currency.id or False,
#             'amount_currency': company_currency != current_currency and line.amount or 0.0,
#             'asset_id': line.asset_id.id
#         }
#         move_vals = {
#             'ref': line.asset_id.code,
#             'date': depreciation_date or False,
#             'journal_id': category_id.journal_id.id,
#             'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
#         }
#         return move_vals

#     def _prepare_move_grouped(self):
#         asset_id = self[0].asset_id
#         category_id = asset_id.category_id  # we can suppose that all lines have the same category
#         account_analytic_id = asset_id.account_analytic_id
#         analytic_tag_ids = asset_id.analytic_tag_ids
#         depreciation_date = self.env.context.get('depreciation_date') or fields.Date.context_today(self)
#         amount = 0.0
#         for line in self:
#             # Sum amount of all depreciation lines
#             company_currency = line.asset_id.company_id.currency_id
#             current_currency = line.asset_id.currency_id
#             company = line.asset_id.company_id
#             amount += current_currency._convert(line.amount, company_currency, company, fields.Date.today())

#         name = category_id.name + _(' (grouped)')
#         move_line_1 = {
#             'name': name,
#             'account_id': category_id.account_depreciation_id.id,
#             'debit': 0.0,
#             'credit': amount,
#             'journal_id': category_id.journal_id.id,
#             'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
#             'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
#         }
#         move_line_2 = {
#             'name': name,
#             'account_id': asset_exp_id.account_depreciation_expense_id.id,
#             'credit': 0.0,
#             'debit': amount,
#             'journal_id': category_id.journal_id.id,
#             'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
#             'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
#         }
#         move_vals = {
#             'ref': category_id.name,
#             'date': depreciation_date or False,
#             'journal_id': category_id.journal_id.id,
#             'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
#         }

#         return move_vals
