# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import time

class sale_order(models.Model):
    _inherit = 'sale.order'

    # pre_pay_date = fields.Date('Урьдчилгаа төлбөрийн огноо')
    pre_pay_amount = fields.Float('Урьдчилгаа төлбөрийн дүн')
    pre_pay_desc = fields.Char('Урьдчилгаа тайлбар')
    pre_pay_journal_id = fields.Many2one('account.journal','Урьдчилгаа төлбөр төлөх Журнал', domain=[('type', 'in', ['cash', 'bank'])])
    # pre_payment_count = fields.Integer(compute="_compute_pre_payment", string='Урьдчилгаа Төлбөрийн Тоо', copy=False, default=0)
    pre_payment_ids = fields.One2many('account.payment', 'sale_order_id', string='Урьдчилгаа Төлбөрүүд')
    # pre_payment_status = fields.Char( string='Урьдчилгаа төлбөр төлөв', compute='_get_pre_payment', readonly=True, copy=False, default='no')
    invoice_residual = fields.Float(string='Төлбөрийн үлдэгдэл', compute='_residual_amount', readonly=True,store=True)    

    @api.depends('order_line.invoice_lines','order_line.invoice_lines.move_id','order_line.invoice_lines.move_id.amount_residual')
    def _residual_amount(self):
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            residual=sum(invoices.mapped('amount_residual'))
            order.invoice_residual = residual

    def _get_pre_payment(self):
        for item in self:
            pre_payment_status = []
            for x in x.pre_payment_ids:
                pre_payment_status.append(dict(x._fields['state'].selection).get(x.state))
            item.pre_payment_status = pre_payment_status.join(',')

    def create_pre_payment(self):
        payment_obj = self.env['account.payment']
        if not self.pre_pay_amount or not self.pre_pay_journal_id:
            raise UserError(u'Төлбөрийн дүн, төлөх журнал заавал сонгоно.')
        
        desc = u'Урьдчилгаа төлбөр '+(self.pre_pay_desc or '')+' /'+self.display_name+'/'
        for order in self:
            wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=order.ids,
                                                                    open_invoices=True).create({
                'advance_payment_method': 'fixed',
                'fixed_amount': order.pre_pay_amount,
            })
            res = wiz.create_invoices()
            for invoice in order.invoice_ids:
                invoice.action_post()
                payment_wiz = self.env['account.payment.register'].with_context(active_model='account.move',
                                                                                active_ids=invoice.ids).create(
                    {
                        'journal_id': order.pre_pay_journal_id.id,
                        'amount': order.pre_pay_amount,
                        'currency_id': self.env.company.currency_id.id,
                        'payment_date': fields.Date.today(),
                        'communication': desc
                    })
                res = payment_wiz.action_create_payments()
                if res:
                    self.env['account.payment'].browse(res['res_id']).write({'sale_order_id': order.id,
                                                                             'branch_id': order.branch_id.id if order.branch_id else False})
            return True

    # @api.depends('pre_payment_ids')
    # def _compute_pre_payment(self):
    #     for item in self:
    #         item.pre_payment_count = len(item.sudo().pre_payment_ids)
    #         states = []
    #         for pay in item.sudo().pre_payment_ids:
    #             states.append(dict(self.env['account.payment']._fields['state'].selection).get(pay.state))
    #         item.pre_payment_status = ', '.join(states)

    @api.constrains('pre_payment_ids','amount_total')
    def _check_pre_payment_mw(self):
        for item in self:
            print (item.amount_total,'item.amount_total',sum(item.sudo().pre_payment_ids.mapped('amount')))
            if item.amount_total<sum(item.sudo().pre_payment_ids.mapped('amount')):
                raise ValidationError(u'%s Урьдчилгаа төлбөрийн дүн Үндсэн SO-өөс хэтрэхгүй'%(item.display_name))

class account_payment(models.Model):
    _inherit = 'account.payment'

    sale_order_id = fields.Many2one('sale.order','Хамаарах Урьдчилгаа PO', readonly=True, copy=False)
