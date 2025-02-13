from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError


class PaymentRequestUpdate(models.Model):
    _name = 'payment.request.update'
    _desc = 'payment.request.update'
    _inherit = ['analytic.mixin']



    journal_id =  fields.Many2one('account.journal', string='Журнал', domain=([('type', 'in', ['bank', 'cash'])]))
    ex_account_id =  fields.Many2one('account.account', string='Данс')
    cash_type_id =  fields.Many2one('account.cash.move.type', string='Мөнгөн гүйлгээний төрөл')
    payment_ids = fields.Many2many('payment.request', string='Төлбөрийн хүсэлтүүд', default=lambda self: self.env.context.get('active_ids', []))



    def done_button(self):
        for item in self.payment_ids:
            if self.ex_account_id:
                item.ex_account_id  = self.ex_account_id.id
            if self.journal_id:
                item.journal_id  = self.journal_id.id
            if self.cash_type_id:
                item.cash_type_id  = self.cash_type_id.id