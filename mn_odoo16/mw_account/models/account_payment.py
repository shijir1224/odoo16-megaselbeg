from odoo import models, fields, api, _, Command

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cash_type_id = fields.Many2one('account.cash.move.type', string="Мөнгөн гүйлгээний төрөл", readonly="1")
    statement_line_id = fields.Many2one('account.bank.statement.line', string="Харилцахын Хуулга", invisible="1")


    def action_post(self):
        ''' draft -> posted '''
        self.move_id._post(soft=False)
        self.create_bank_statement()
        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()
    def button_open_statement_line(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Хуулга"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement.line',
            'context': {'create': False},
            'view_mode': 'tree',
            'domain': [('id','=',self.statement_line_id.id)]
        }
    def create_bank_statement(self):
        for payment in self:
            if payment.payment_type =='outbound':
                amount = payment.amount*-1
            else:
                amount = payment.amount
            ss = payment.env['account.bank.statement.line'].create({
                    'payment_ref': payment.ref or '/',
                    'ref': payment.ref or '/',
                    'amount': amount,
                    'partner_id': payment.partner_id.id,
                    'date': payment.date,
                    'cash_type_id': payment.cash_type_id.id,
                    # 'move_id':payment.move_id.id,
                    'journal_id':payment.journal_id.id,
                })
            self.statement_line_id = ss.id
            pp = ss.move_id
            ss.update({'move_id':payment.move_id.id})
            pp.button_draft()
            pp.unlink()


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    
    cash_type_id = fields.Many2one('account.cash.move.type', string="Мөнгөн гүйлгээний төрөл")
   
    def _create_payment_vals_from_wizard(self, batch_result):
        action = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        batch_result.update({
            'cash_type_id':self.cash_type_id.id
        })
        return action
