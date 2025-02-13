# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _   
from odoo.exceptions import UserError     

class AccountPeriod(models.Model):
    _name = "account.period"
    _description = "Account period"
    _inherit = ['mail.thread']

    name = fields.Char('Period Name', required=True, tracking=True)
    code = fields.Char('Code', required=True, tracking=True)
    date_start = fields.Date('Start of Period', required=True, states={'done': [('readonly', True)]}, tracking=True)
    date_stop = fields.Date('End of Period', required=True, states={'done': [('readonly', True)]}, tracking=True)
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True, states={'done': [('readonly', True)]})
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], 'Status', readonly=True, copy=False, tracking=True, default="draft", help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')
    company_id = fields.Many2one('res.company', string='Company', store=True)

    is_draft = fields.Boolean(related='fiscalyear_id.is_draft', string='Ноорог төлөв алгасах?',store=True)

    _order = "date_start"
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
    ]

    def _check_duration(self):
        obj_period = self.env['account.period']
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    def _check_year_limit(self):
        for obj_period in self:
            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                return False
            pids = self.search([('date_stop', '>=', obj_period.date_start), ('date_start', '<=', obj_period.date_stop), ('id', '<>', obj_period.id)])
            for period in self and pids:
                if period.fiscalyear_id.company_id.id == obj_period.fiscalyear_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
        (_check_year_limit, 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.', ['date_stop'])
    ]

    
    def action_draft(self):
        # Мөчлөгийг дахин нээхэд өмнөх хаагдсан мөчлөгийн огноогоор түгжигдэнэ.
        state_id = 'done'
        closed_periods = self.env['account.period'].search([('state', '=', state_id)], order="id desc", limit=2)

        if closed_periods:
            count = 1
#             for closed_period in closed_periods:
#                 self.env['account.config.settings'].search([], order="id desc", limit=1).write({
#                         'period_lock_date': closed_period.date_stop if 2 == count else False,
#                         'fiscalyear_lock_date': closed_period.date_stop if 2 == count else False
#                 })
#                 count += 1
        mode = 'draft'
        
#         self.env.cr.execute('update account_period set state=%s where id in %s', (mode, tuple(self.ids),))
        self.write({'state':mode})

        # Мөчлөгийг нээсэн тохиолдолд тухайн журналын бичилтийг цуцалж, устгана.
        account_move = self.env['account.move']
        find_id = self.env['account.period.close'].search([('period_display', '=', self.name)], limit=1)
        if find_id:
            move_id = account_move.search([('journal_id', '=', find_id.journal_id.id), ('date', '=', str(self.date_stop))], limit=1)
            if move_id:
                move_id.write({'state': "draft"})
                move_id.unlink()
        return True

    # Батлагдсан төлөвтэй мөчлөг устахгүй.
    def unlink(self):
        for period in self:
            if period.state not in ('draft'):
                raise UserError(_('You cannot delete an period which is done. You should reopen it instead.'))
        return super(AccountPeriod, self).unlink()

