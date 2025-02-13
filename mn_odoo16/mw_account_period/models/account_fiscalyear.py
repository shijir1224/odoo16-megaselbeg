# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from dateutil.relativedelta import relativedelta

class AccountFiscalyear(models.Model):
    _name = "account.fiscalyear"
    _description = "Fiscal Year"

    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company')
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], 'Status', default="draft", copy=False)

    is_draft = fields.Boolean('Ноорог төлөв алгасах?',default=False)

    _order = "date_start"
    _sql_constraints = [
        ('company_name_uniq', 'unique(name, company_id)', 'The name of the fiscalyear must be unique per company!'),
    ]
    
    def _check_duration(self):
        for obj_fy in self:
            if obj_fy.date_stop < obj_fy.date_start:
                return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start', 'date_stop'])
    ]

    # Мөчлөгийг улирлаар үүсгэнэ.
    def create_period3(self):
        return self.create_period(3)

    # Мөчлөгийг сараар үүсгэнэ
    def create_period(self, interval=1):
        period_obj = self.env['account.period']
        month = interval
        if type(interval) == dict:
            month = interval['interval']
        for fy in self:
            ds = fy.date_start
            while ds < fy.date_stop:
                de = ds + relativedelta(months=month, days=-1)
                if de > fy.date_stop:
                    de = fy.date_stop

                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                    'company_id': fy.company_id.id,
                })
                ds = ds + relativedelta(months=month)
        return True,

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = args or []
        ids = self.browse()
        if name:
            ids = self.search([('name', operator, name)] + args, limit=limit)
        if not ids:
            ids = self.search([('code', operator, name)] + args, limit=limit)
        result = ids.name_get()
        return result


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Entry"

    def _check_fiscalyear_lock_date(self,check_date=None):
        # print ('check_date=== ',check_date)
        for move in self:
            date_ch=move.date
            if check_date:
                date_ch=check_date
            
            sql='SELECT state,is_draft FROM account_period WHERE date_start <= \'{0}\' and date_stop>=\'{0}\' and company_id={1} '.format(date_ch,move.company_id.id)
            self._cr.execute(sql)
            result = self._cr.fetchall()
            for (state,is_draft) in result:
#                 print ('state ',state)
                if state == 'done':
                    if (is_draft and move.state!='draft') or not is_draft:
                        raise UserError(u'Санхүүгийн мөчлөг хаагдсан байна. Бичилт нэмэх цуцлах боломжгүй.')


            #Данс хаах
            self._cr.execute('select account_id from account_account_close_rel r left join account_account_close c on r.close_id=c.id\
                                 WHERE date_start <= \'{0}\' and date_stop>=\'{0}\' and (account_and_partner=\'f\' or account_and_partner isnull) '.format(date_ch))
            acc_result = self._cr.fetchall()
            accounts=[]
            for acc in acc_result:   
                accounts.append(acc[0])                    
#             for line in move.line_ids:
# #                 if (line.account_id.internal_type in ('receivable','payable') \
# #                 and not line.partner_id :#line.account_id.id not in \
# #                     (42865,42869,15752,33011,33012,8387,32985,32986,15755,33015,33016,15753,8391,32983,32984,15754,33013,33014,8392,15761)) \
# #                     raise osv.except_osv(_('Warning !'), _(u'%s дугаартай. \n\n "%s" Авлага өглөгийн дансанд харилцагч заавал сонгоно уу!') % (line.move_id.name,line.account_id.name))
#                 if line.account_id.id in accounts:
#                     raise UserError(u'({0}) дансыг энэ хугацаан дахь гүйлгээ цоожилсон байна. Нягтланд хандана уу'.format( line.account_id.name))
                
            #Харилцагч хаах
            self._cr.execute('select partner_id from account_partner_close_rel r left join account_account_close c on r.close_id=c.id\
                                 WHERE date_start <= \'{0}\' and date_stop>=\'{0}\' and  (account_and_partner=\'f\' or account_and_partner isnull)'.format(date_ch))
            partner_result = self._cr.fetchall()
            partners=[]
            for partner in partner_result:   
                partners.append(partner[0])                    
#             for line in move.line_ids:
# #                 if (line.account_id.internal_type in ('receivable','payable') \
# #                 and not line.partner_id :#line.account_id.id not in \
# #                     (42865,42869,15752,33011,33012,8387,32985,32986,15755,33015,33016,15753,8391,32983,32984,15754,33013,33014,8392,15761)) \
# #                     raise osv.except_osv(_('Warning !'), _(u'%s дугаартай. \n\n "%s" Авлага өглөгийн дансанд харилцагч заавал сонгоно уу!') % (line.move_id.name,line.account_id.name))
#                 if line.partner_id and line.partner_id.id in partners:
#                     raise UserError(u'({0}) харилцагчийг энэ хугацаан дахь гүйлгээ цоожилсон байна. Нягтланд хандана уу'.format( line.partner_id.name))
                                
            #Зэрэг
            self._cr.execute('select id from account_account_close\
                                 WHERE date_start <= \'{0}\' and date_stop>=\'{0}\' and account_and_partner=\'t\' '.format(date_ch))
            all_result = self._cr.fetchall()
            all_res=[]
            for res in all_result:   
                all_res.append(res[0])                    
            all_accounts=[]
            all_partners=[]
            if len(all_res):
                res_where=""
                if len(all_res)==1:
                    res_where = " and c.id = "+str(all_res[0])+" "
                elif len(all_res)>1:
                    res_where = " and c.id in ("+','.join(map(str,all_res))+") "
                self._cr.execute('select account_id from account_account_close_rel r left join account_account_close c on r.close_id=c.id\
                                     WHERE date_start <= \'{0}\' and date_stop>=\'{0}\'  {1} '.format(date_ch,res_where))
                acc_result = self._cr.fetchall()
                for acc in acc_result:   
                    all_accounts.append(acc[0])                    
                self._cr.execute('select partner_id from account_partner_close_rel r left join account_account_close c on r.close_id=c.id\
                                     WHERE date_start <= \'{0}\' and date_stop>=\'{0}\'  {1} '.format(date_ch,res_where))
                partner_result = self._cr.fetchall()
                for partner in partner_result:   
                    all_partners.append(partner[0])                    
                                
            for line in move.line_ids:
#                 if (line.account_id.internal_type in ('receivable','payable') \
#                 and not line.partner_id :#line.account_id.id not in \
#                     (42865,42869,15752,33011,33012,8387,32985,32986,15755,33015,33016,15753,8391,32983,32984,15754,33013,33014,8392,15761)) \
#                     raise osv.except_osv(_('Warning !'), _(u'%s дугаартай. \n\n "%s" Авлага өглөгийн дансанд харилцагч заавал сонгоно уу!') % (line.move_id.name,line.account_id.name))
                if line.partner_id and line.partner_id.id in partners:
                    raise UserError(u'({0}) харилцагчийг энэ хугацаан дахь гүйлгээ цоожилсон байна. Нягтланд хандана уу'.format( line.partner_id.name))
                if line.account_id.id in accounts:
                    raise UserError(u'({0}) дансыг энэ хугацаан дахь гүйлгээ цоожилсон байна. Нягтланд хандана уу'.format( line.account_id.name))
                if (line.account_id.id in all_accounts) and (line.partner_id and line.partner_id.id in all_partners):
                    raise UserError(u'({0}) данс, ({1}) харилцагч энэ хугацаан дахь гүйлгээ цоожилсон байна. Нягтланд хандана уу'.format( line.account_id.name,line.partner_id.name))

        res = super(AccountMove, self)._check_fiscalyear_lock_date()
        return res
    

class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def unlink(self):
        # мөчлөг хаасан бол салгахгүй
        context = dict(self._context or {})
        if not self:
            return True

        for part in self:
            if not self.env.user.has_group('mw_account_period.group_remove_period_reconcile'):
                # print(s )
                if not self.env.user.has_group('mw_account.group_remove_reconcile'):
                    raise UserError(('Тулгалт салгах эрхгүй байна!!! .'))
                elif self.env.user.has_group('mw_account.group_remove_reconcile'):
                    sql='SELECT state,is_draft FROM account_period WHERE date_start <= \'{0}\' and date_stop>=\'{0}\' and company_id={1} '.format(part.debit_move_id.date,part.debit_move_id.company_id.id)
                    self._cr.execute(sql)
                    result = self._cr.fetchall()
                    for (state,is_draft) in result:
                        if state == 'done':
                            if (is_draft and state!='draft') or not is_draft:
                                raise UserError(u'Санхүүгийн мөчлөг хаагдсан байна. Тулгалт салгах боломжгүй.{} '.format(part.debit_move_id.date))
                    sql='SELECT state,is_draft FROM account_period WHERE date_start <= \'{0}\' and date_stop>=\'{0}\' and company_id={1} '.format(part.credit_move_id.date,part.debit_move_id.company_id.id)
                    self._cr.execute(sql)
                    result = self._cr.fetchall()
                    for (state,is_draft) in result:
        #                 print ('state ',state)
                        if state == 'done':
                            if (is_draft and state!='draft') or not is_draft:
                                raise UserError(u'Санхүүгийн мөчлөг хаагдсан байна. Тулгалт салгах боломжгүй.{} '.format(part.credit_move_id.date))

        res = super().unlink()

        return res