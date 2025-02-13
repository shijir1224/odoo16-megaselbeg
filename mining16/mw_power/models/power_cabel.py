# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import UserError

class power_cabel(models.Model):
    _name = 'power.cabel'
    _description = 'power cabel'
    _order = 'date desc'

    date = fields.Date('Огноо', default=fields.Date.context_today, required=True)
    object_id = fields.Many2one('power.category', string='ОДОО БАЙГАА БАЙРШИЛ', required=True)
    state = fields.Selection([('state1','АШИГЛАЖ БАЙГАА'),('state2','БЭЛЭН БАЙДАЛ')], string='Төлөв', required=True)
    product_id = fields.Many2one('product.product', string='КАБЕЛЬ МАРК', required=True)
    metr = fields.Float(string='МЕТР', required=True)
    desc = fields.Text(string='АШИГЛАГДАЖ БАЙГАА БАЙДАЛ', required=True)
    