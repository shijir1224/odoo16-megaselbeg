from odoo import api, fields, models, tools
from datetime import datetime
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_view_lines(self):
        action = self.env.ref('account.action_account_moves_all_tree')
        vals = action.read()[0]
        ids = self.line_ids.ids
        print ('<<<<<////////////////////////////////',ids)
        domain = [('id','in',ids)]
        vals['domain'] = domain
        vals['context'] = {}
        return vals
    def unlink(self):
        for move in self:
            if not self.env.user.has_group('mw_account.group_mn_account_move_stock_unlink') and not move.asset_id and move.stock_move_id:
                raise UserError(u'({0}) Агуулахтай холбоотой гүйлгээ устгах эрхгүй байна. Эрх бүхий нягтланд хандана уу'.format( move.name))
            elif not self.env.user.has_group('mw_account.group_mn_account_move_unlink') and not move.asset_id and not move.stock_move_id:
                raise UserError(u'({0}) Гүйлгээ устгах эрхгүй байна. Эрх бүхий нягтланд хандана уу'.format( move.name))
            elif not self.env.user.has_group('mw_asset.group_mn_asset_accountant') and move.asset_id and not move.stock_move_id:
                raise UserError(u'({0}) Хөрөнгөтэй холбоотой гүйлгээ устгах эрхгүй байна. Эрх бүхий нягтланд хандана уу'.format( move.name))
        return super().unlink()


    def action_view_lines_invoice(self):
        print ('------------------------')
        action = self.env.ref('mw_stock_account.action_account_invoice_move_line')
        print ('action',action)
        vals = action.read()[0]
        ids = self.invoice_line_ids.ids
        print ('<<<<<////////////////////////////////',ids)
        domain = [('id','in',ids)]
        vals['domain'] = domain
        vals['context'] = {'create':False,'edit':False}
        return vals