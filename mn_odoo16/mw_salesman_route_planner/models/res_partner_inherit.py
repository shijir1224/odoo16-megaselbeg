# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class res_partner_route(models.Model):
    _name = 'res.partner.route'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "res partner route"

    name = fields.Char('Route', required=True, tracking=True)
    description = fields.Char('Description', tracking=True)
    user_ids = fields.Many2many('res.users', 'user_route_rel', 'route_id', 'user_id',
                                string=u'Холбоотой хэрэглэгч', tracking=True)
    driver_id = fields.Many2one('res.users', string=u'Жолооч', tracking=True)
    parent_id = fields.Many2one('res.partner.route', string=u'Parent', tracking=True)
    route_type = fields.Selection([
        ('saler', u'ХТ'),
        ('deliverer', u'Түгээлт'),
    ], string=u'Төрөл', default='saler', tracking=True)

class ResUsers(models.Model):
    _inherit = 'res.users'

    route_ids = fields.Many2many('res.partner.route', 'user_route_rel', 'user_id', 'route_id', string=u'Чиглэлүүд', )


class res_partner(models.Model):
    _inherit = 'res.partner'

    route_id = fields.Many2one('res.partner.route', string='Route')

    @api.model
    def create(self, vals):
        if vals.get('route'):
            route_id = self.env['res.partner.route'].search([('name', '=', vals['route'])])
            if route_id:
                vals['route_id'] = route_id.id
            else:
                self.env['res.partner.route'].create({'name': vals['route']})
        partner = super(res_partner, self).create(vals)
        return partner
