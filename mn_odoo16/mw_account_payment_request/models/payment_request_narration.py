from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class PaymentRequestNarration(models.Model):
    """ Мөнгө хүсэх зориулалт"""
    _name = 'payment.request.narration'
    _description = 'Payment Request Narration'

    name = fields.Char('Гүйлгээний утга', size=128, required=True)
    description = fields.Text('Дэлгэрэнгүй тайлбар')
    default_check_items = fields.One2many('payment.request.narration.item', 'narration_id', 'Default Accompaniments')
    flow_hamaarah_id = fields.Many2one('dynamic.flow', string='Хамаарах урсгал',
                                       domain="[('model_id.model', '=', 'payment.request')]", company_dependent=True)
    is_mission  = fields.Boolean(string='Томилолт эсэх', default=False,  help='Used when creating a payment request from hr_mission')

class PaymentRequestNarrationItem(models.Model):
    """ Default Narration Items"""

    _name = 'payment.request.narration.item'
    _description = 'Payment Request Narration Default Accompaniments'

    name = fields.Char('Name', size=128, required=True)
    type = fields.Many2one('payment.request.item.type', 'Accompaniments Type', required=True)
    description = fields.Text('Description')
    narration_id = fields.Many2one('payment.request.narration', 'Narration', required=True)