# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json, requests


import logging

class res_partner(models.Model):
    _inherit = 'res.partner'

    def _partner_receivable_payable_get(self):
        for partner in self:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
#             where_params = [tuple(self.ids)] + where_params
            where_params = [partner.id] + where_params
            self._cr.execute("""SELECT l.partner_id, a.id, SUM(l.debit)-SUM(l.credit) as amount 
                          FROM account_move_line l  
                          left join account_move m on l.move_id=m.id 
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          WHERE 
                          a.is_employee_recpay ='t' 
                          AND m.state='posted' 
                          AND l.partner_id = %s 
                          """ + where_clause + """ and l.company_id={0} 
                          GROUP BY l.partner_id, a.id
                          """.format(self.env.user.company_id.id), where_params)
            res=self._cr.fetchall()
#             print ('res ',res)
            if res:
                partner.receivable_payable =res[0][2]
            else:
                partner.receivable_payable =0
    def _partner_mobile_receivable_get(self):
        for partner in self:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
#             where_params = [tuple(self.ids)] + where_params
            where_params = [partner.id] + where_params
            self._cr.execute("""SELECT l.partner_id, a.id, SUM(l.debit)-SUM(l.credit) as amount 
                          FROM account_move_line l  
                          left join account_move m on l.move_id=m.id 
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          WHERE 
                          a.mobile_receivable ='t' 
                          AND m.state='posted' 
                          AND l.partner_id = %s 
                          """ + where_clause + """ and l.company_id={0} 
                          GROUP BY l.partner_id, a.id
                          """.format(self.env.user.company_id.id), where_params)
            res=self._cr.fetchall()
#             print ('res ',res)
            if res:
                partner.mobile_receivable =res[0][2]
            else:
                partner.mobile_receivable =0
    def _partner_clotes_receivable_get(self):
        for partner in self:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
#             where_params = [tuple(self.ids)] + where_params
            where_params = [partner.id] + where_params
            self._cr.execute("""SELECT l.partner_id, a.id, SUM(l.debit)-SUM(l.credit) as amount 
                          FROM account_move_line l  
                          left join account_move m on l.move_id=m.id 
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          WHERE 
                          a.clotes_receivable ='t' 
                          AND m.state='posted' 
                          AND l.partner_id = %s 
                          """ + where_clause + """ and l.company_id={0} 
                          GROUP BY l.partner_id, a.id
                          """.format(self.env.user.company_id.id), where_params)
            res=self._cr.fetchall()
#             print ('res ',res)
            if res:
                partner.clotes_receivable =res[0][2]
            else:
                partner.clotes_receivable =0
    def _partner_payment_receivable_get(self):
        for partner in self:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
#             where_params = [tuple(self.ids)] + where_params
            where_params = [partner.id] + where_params
            self._cr.execute("""SELECT l.partner_id, a.id, SUM(l.debit)-SUM(l.credit) as amount 
                          FROM account_move_line l  
                          left join account_move m on l.move_id=m.id 
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          WHERE 
                          a.payment_receivable ='t' 
                          AND m.state='posted' 
                          AND l.partner_id = %s 
                          """ + where_clause + """ and l.company_id={0} 
                          GROUP BY l.partner_id, a.id
                          """.format(self.env.user.company_id.id), where_params)
            res=self._cr.fetchall()
#             print ('res ',res)
            if res:
                partner.payment_receivable =res[0][2]
            else:
                partner.payment_receivable =0

    receivable_payable = fields.Monetary(compute='_partner_receivable_payable_get', 
        string='Ажилтны авлага', help="Total amount this customer owes you.")
    mobile_receivable = fields.Monetary(compute='_partner_mobile_receivable_get', string='Утасны төлбөр')
    clotes_receivable = fields.Monetary(compute='_partner_clotes_receivable_get', string='Хувцасны төлбөр')
    payment_receivable = fields.Monetary(compute='_partner_payment_receivable_get', string='Торгууль')

    receivable_payable_hand = fields.Float(string='Ажилтны авлага')
    mobile_receivable_hand = fields.Float(string='Утасны төлбөр')
    clotes_receivable_hand = fields.Float(string='Хувцасны төлбөр')
    payment_receivable_hand = fields.Float(string='Торгууль')

