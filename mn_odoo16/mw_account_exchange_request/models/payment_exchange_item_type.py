from odoo import fields, models


class PaymentRequestItemType(models.Model):
    """ Дагалдах баримтын төрөл"""

    _name = 'payment.request.item.type'
    _description = 'Payment Request Accompaniments Type'

    name = fields.Char('Name', size=64, required=True)
    description = fields.Text('Description')
