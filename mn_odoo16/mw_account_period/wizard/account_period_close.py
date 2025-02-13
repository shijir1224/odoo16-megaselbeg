# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _  # @UnresolvedImport
from odoo.exceptions import UserError, ValidationError  # @UnresolvedImport

class AccountPeriodClose(models.TransientModel):

    _name = "account.period.close"
    _description = "period close"

    def _get_company(self):
        if self.env.context.get('active_model', 'ir.ui.menu') == 'account.period':
            period = self.env['account.period'].browse(self.env.context.get('active_id'))
            return period.company_id.id

#     def _get_configuration(self):
# #         journal = self.env['account.config.settings'].search([], order="id desc", limit=1)
#         return 1

    def _get_period_display(self):
        res = {}
        closing_periods = u''
        if self.env.context.get('active_model', 'ir.ui.menu') == 'account.period':
            for p in self.env['account.period'].browse(self.env.context.get('active_ids')):
                closing_periods += u'%s\n' % p.name
        return res.setdefault(p, closing_periods)

    period_display = fields.Text(default=_get_period_display, method=True, string="To be closed periods", store=False)
    journal_id = fields.Many2one('account.journal', string='Reserve & Profit/Loss Journal')
    registered_date = fields.Date(string='Date', default=fields.Date.today)
    description = fields.Char(string='Name of New Entries', size=64)
    company_id = fields.Many2one('res.company', string='Company', default=_get_company)
    temporary = fields.Boolean(string='Temporary Closing',default=True, help='If check this box, closing of periods done without any closing entries.')

    @api.model
    def close_state(self, period_ids):
        """ Тайлант хугацааны төлөвийг хаагдсан төлөвт шилжүүлнэ.
        """
        mode = 'done'
        period_obj=self.env['account.period']
        for period_id in period_ids:
            period=period_obj.browse(period_id)
            period.write({'state':'done'})
#             self.env.cr.execute("""UPDATE account_journal_period set state=%s WHERE period_id=%s""", (mode, period_id))
#             self.env.cr.execute("""UPDATE account_period set state='done' WHERE id=""" + str(period_id))
            
        return True

    @api.model
    def action_close(self, period_ids):
        ''' Тайлант хугацааг хааж орлого зарлагын түр дансуудын
            үлдэгдлийг орлого зарлагын нэгдсэн дансанд хаана.
        '''
        obj_acc_move = self.env['account.move']

        if not self.journal_id.default_debit_account_id or not self.journal_id.default_credit_account_id:
            raise ValidationError(_('There is no Default Debit/Credit Account defined on your selected journal!'))
        if not self.journal_id.profit_account_id or not self.journal_id.loss_account_id:
            raise ValidationError(_('There is no Reserve & Profit/Loss Account defined on your selected journal!'))
        res = []
        search_account = []

        # Орлого, зарлагын түр дансуудыг тодорхойлох : income, expense гэсэн төрөлтэй дансны төрлүүдийг шүүнэ.
        for type in self.env['account.account.type'].search([('type', 'in', ['income', 'expense'])]):
            for account in self.env['account.account'].search([('id', '<>', self.journal_id.default_debit_account_id.id), ('user_type_id', '=', type.id)]):
                search_account.append(account.id)
        if not search_account:
            return res

        # Тухайн дансны тайлант хугацааны хоорондох дүнг олно
        for period in self.env['account.period'].browse(period_ids):
            account_sum_dict = self.env['account.move.line'].get_balance(period.company_id.id, search_account, period.date_start, period.date_stop, None)
            reverse_debit = reverse_credit = 0.0
            move_lines = []
            for line in account_sum_dict:
                # account_move руу бичих өгөгдөл
                debit, credit = line['debit'], line['credit']
                balance = credit - debit
                # Орлого зарлагын түр дансуудыг хаана.
                move_lines.append((0, 0, {
                            'debit': (credit > debit and abs(balance)) or 0.0,
                            'credit': (debit > credit and abs(balance)) or 0.0,
                            'name': self.description,
                            'date': period.date_stop,
                            'journal_id': self.journal_id.id,
                            'currency_id': False,
                            'account_id': line['account_id'],
                            'company_id': self.company_id.id,
                }))
                reverse_debit += (credit > debit and abs(balance)) or 0.0
                reverse_credit += (debit > credit and abs(balance)) or 0.0
            if reverse_credit > reverse_debit:
                # create move lines
                move_lines.append((0, 0, {
                        'debit': abs(reverse_credit - reverse_debit),
                        'credit': 0,
                        'name': self.description,
                        'date': period.date_stop,
                        'create_date': period.date_stop,
                        'journal_id': self.journal_id.id,
                        'period_id': period.id,
                        'account_id': self.journal_id.default_debit_account_id.id,
                        'company_id': self.company_id.id,
                }))
                move_lines.append((0, 0, {
                        'debit': 0,
                        'credit': abs(reverse_credit - reverse_debit),
                        'name': self.description,
                        'date': period.date_stop,
                        'create_date': period.date_stop,
                        'journal_id': self.journal_id.id,
                        'period_id': period.id,
                        'account_id': self.journal_id.default_debit_account_id.id,
                        'company_id': self.company_id.id,
                }))
                move_lines.append((0, 0, {
                        'debit': abs(reverse_credit - reverse_debit),
                        'credit': 0,
                        'name': self.description,
                        'date': period.date_stop,
                        'create_date': period.date_stop,
                        'journal_id': self.journal_id.id,
                        'period_id': period.id,
                        'account_id': self.journal_id.loss_account_id.id,
                        'company_id': self.company_id.id,
                }))
            elif reverse_debit > reverse_credit:
                move_lines.append((0, 0, {
                        'debit': 0,
                        'credit': abs(reverse_debit - reverse_credit),
                        'name': self.description,
                        'date': period.date_stop,
                        'date_created': period.date_stop,
                        'journal_id': self.journal_id.id,
                        'period_id': period.id,
                        'account_id': self.journal_id.default_credit_account_id.id,
                        'company_id': self.company_id.id,
                }))
                move_lines.append((0, 0, {
                        'debit': abs(reverse_debit - reverse_credit),
                        'credit': 0,
                        'name': self.description,
                        'date': period.date_stop,
                        'date_created': period.date_stop,
                        'journal_id': self.journal_id.id,
                        'period_id': period.id,
                        'account_id': self.journal_id.default_credit_account_id.id,
                        'company_id': self.company_id.id,
                }))
                move_lines.append((0, 0, {
                        'debit': 0,
                        'credit': abs(reverse_debit - reverse_credit),
                        'name': self.description,
                        'date': period.date_stop,
                        'date_created': period.date_stop,
                        'journal_id': self.journal_id.id,
                        'period_id': period.id,
                        'account_id': self.journal_id.profit_account_id.id,
                        'company_id': self.company_id.id,
                }))
            if move_lines:
                move_id = obj_acc_move.create({
                        'journal_id': self.journal_id.id,
                        'date': period.date_stop,
                        'state': 'posted',
                        'narration': u'%s мөчлөгийн хаалтын гүйлгээ.' % (period.name,),
                        'line_ids': move_lines
                })
                res.append(move_id)
        return res

    
    def data_save(self):
        for period_close_id in self:
            if 'active_ids' in self.env.context and self.env.context.get('active_ids'):
                period_ids = self.env.context.get('active_ids')
            else:
                period_ids = period_close_id.id

        # Өмнөх сарын мөчлөг хаагдаагүй болон мөчлөгүүд нэг санхүүгийн жилд харьяалагдаагүй бол анхааруулна.
        active_ids = self.env['account.period'].search([('id', 'in', period_ids)], order="id desc")
        minimum_value = 0
        fis_id = False
        for active_id in active_ids:
            if not fis_id:
                fis_id = active_id.fiscalyear_id.id
            else:
                if fis_id != active_id.fiscalyear_id.id:
                    raise ValidationError(_('Which period you have selected are must be same fiscalyear.'))
                else:
                    fis_id = active_id.fiscalyear_id.id

            if active_id.id < minimum_value or minimum_value == 0:
                minimum_value = active_id.id

        minimum_record = self.env['account.period'].search([('state', "=", 'draft'), ('fiscalyear_id', '=', fis_id)], order="id asc", limit=1)
        if minimum_value > minimum_record.id:
            raise UserError(_("Please, close previous month's period!"))

        """ Хаах гэж буй тайлант хугацааны гүйлгээнүүдийг хааж
                орлого зарлагын нэгдсэн дансанд бичнэ.
        """
        obj_acc_move = self.env['account.move']
        if not self.temporary:
            if not self.journal_id:
                raise UserError(_('There is no Journal defined on this company !'))

            res = self.action_close(period_ids)
            if res:
                for res_id in res:
                    obj_acc_move.browse(res_id.id)._post()

            # Хаагдсан мөчлөгийн дуусах огноогоор бичилтийг түгжинэ.
            self.close_state(period_ids)
            for line in self.env['account.period'].browse(self.env.context.get('active_ids')):
                self.env['account.config.settings'].search([], order="id desc", limit=1).create({
                    'period_lock_date': line.date_stop,
                    'fiscalyear_lock_date': line.date_stop,
                    })

            # Бичигдсэн журналын бичилтүүдийг дэлгэцэнд харуулах
            return {
                'name': _('Closing Entries'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'context': "{'visible_id':%(j)s, 'journal_id': %(j)d, 'search_default_journal_id':%(j)d}" % ({'j': self.journal_id.id}),
                'domain': (len(res) > 0 and "[('id', 'in', " + str([str(i.id) for i in res]) + ")]") or "[('id','=',False)]"

            }
        else:
            # closing All selected Periods without closing entries
            self.close_state(period_ids)
            return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
