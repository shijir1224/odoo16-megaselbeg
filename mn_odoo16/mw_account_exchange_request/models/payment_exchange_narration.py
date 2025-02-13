from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class exchangeRequestNarration(models.Model):
    """ Мөнгө хүсэх зориулалт"""
    _name = 'exchange.request.narration'
    _description = 'exchange Request Narration'

    name = fields.Char('Гүйлгээний утга', size=128, required=True)
    description = fields.Text('Дэлгэрэнгүй тайлбар')
    default_check_items = fields.One2many('exchange.request.narration.item', 'narration_id', 'Default Accompaniments')
    flow_hamaarah_id = fields.Many2one('dynamic.flow', string='Хамаарах урсгал',
                                       domain="[('model_id.model', '=', 'exchange.request')]", company_dependent=True)
    is_mission  = fields.Boolean(string='Томилолт эсэх', default=False,  help='Used when creating a exchange request from hr_mission')

class exchangeRequestNarrationItem(models.Model):
    """ Default Narration Items"""

    _name = 'exchange.request.narration.item'
    _description = 'exchange Request Narration Default Accompaniments'

    name = fields.Char('Name', size=128, required=True)
    type = fields.Many2one('exchange.request.item.type', 'Accompaniments Type', required=True)
    description = fields.Text('Description')
    narration_id = fields.Many2one('exchange.request.narration', 'Narration', required=True)