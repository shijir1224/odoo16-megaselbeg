from odoo import fields, models


class PaymentRequestButsaaltTailbar(models.TransientModel):
    _name = 'payment.request.butsaalt.tailbar'
    _description = 'Payment Request butsaalt tailbar'

    butsaalt_tailbar = fields.Text(string='Буцаалтын тайлбар')
    request_id = fields.Many2one('payment.request', string='Баримт')

    def action_done(self):
        self.request_id.butsaalt_tailbar = (self.request_id.butsaalt_tailbar or '') + '' + self.butsaalt_tailbar + ' ' + self.env.user.display_name + '\n'
        self.request_id.with_context(force_back=True).action_back_stage()
