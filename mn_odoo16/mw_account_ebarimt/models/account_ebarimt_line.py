# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _   # @UnresolvedImport
from odoo.exceptions import UserError     # @UnresolvedImport

class AccountEbarimtCalcLine(models.Model):
    _name = "account.ebarimt.calculation.line"
    _description = "Account period"

    name = fields.Char('Name', required=True)
    date = fields.Date('Date', required=True)
    parent_id = fields.Many2one('account.ebarimt.calculation', 'Ebarimt')
    partner_id = fields.Many2one('res.partner', 'Partner')
    regno = fields.Char('Register', required=True)
    partner_name = fields.Char('Partner Name')
    padaan = fields.Char('Padaan')
    amount = fields.Float(u'НӨАТ гүй')
    nuat = fields.Float(u'НӨАТ')
    noattai = fields.Float(u'НӨАТ тай')
    
    _order = "date"

    
    def action_draft(self):
        # Мөчлөгийг дахин нээхэд өмнөх хаагдсан мөчлөгийн огноогоор түгжигдэнэ.
        state_id = 'done'
        closed_periods = self.env['account.ebarimt.calculation.line'].search([('state', '=', state_id)], order="id desc", limit=2)

        if closed_periods:
            count = 1
#             for closed_period in closed_periods:
#                 self.env['account.config.settings'].search([], order="id desc", limit=1).write({
#                         'period_lock_date': closed_period.date_stop if 2 == count else False,
#                         'fiscalyear_lock_date': closed_period.date_stop if 2 == count else False
#                 })
#                 count += 1
        mode = 'draft'
        self.env.cr.execute('update account_period set state=%s where id in %s', (mode, tuple(self.ids),))

        # Мөчлөгийг нээсэн тохиолдолд тухайн журналын бичилтийг цуцалж, устгана.
        account_move = self.env['account.move']
        find_id = self.env['account.ebarimt.calculation.line.close'].search([('period_display', '=', self.name)], limit=1)
        if find_id:
            move_id = account_move.search([('journal_id', '=', find_id.journal_id.id), ('date', '=', str(self.date_stop))], limit=1)
            if move_id:
                move_id.write({'state': "draft"})
                move_id.unlink()
        return True

    # Батлагдсан төлөвтэй мөчлөг устахгүй.
    
#     def unlink(self):
#         for period in self:
#             if period.state not in ('draft'):
#                 raise UserError(_('You cannot delete an period which is done. You should reopen it instead.'))
#         return super(AccountEbarimtCalcLine, self).unlink()



class AccountEbarimtCalcGroupLine(models.Model):
    _name = "account.ebarimt.calculation.group.line"
    _description = "Account period"

    name = fields.Char('Name', required=True)
    date = fields.Date('Date', required=True)
    parent_id = fields.Many2one('account.ebarimt.calculation', 'Ebarimt')
    partner_id = fields.Many2one('res.partner', 'Partner')
    regno = fields.Char('Register', required=True)
    partner_name = fields.Char('Partner Name')
    amount = fields.Float(u'НӨАТ гүй')
    nuat = fields.Float(u'НӨАТ')
    noattai = fields.Float(u'НӨАТ тай')
    
    _order = "date"




class AccountEbarimtCalcAccountLine(models.Model):
    _name = "account.ebarimt.calculation.account.line"
    _description = "Account period"

    name = fields.Char('Name', required=True)
    date = fields.Date('Date', required=True)
    parent_id = fields.Many2one('account.ebarimt.calculation', 'Ebarimt')
    partner_id = fields.Many2one('res.partner', 'Partner')
    regno = fields.Char('Register', required=True)
    partner_name = fields.Char('Partner Name')
    amount = fields.Float(u'НӨАТ')
    residual = fields.Float(u'Санхүү үлдэгдэл')
    zuruu = fields.Float(u'Зөрүү')
    
    _order = "date"
