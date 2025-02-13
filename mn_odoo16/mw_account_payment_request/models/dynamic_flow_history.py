from odoo import models, fields


class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    payment_request_id = fields.Many2one('payment.request', 'Payment request', ondelete='cascade', index=True)
