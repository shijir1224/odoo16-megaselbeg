# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections
import calendar

import logging

_logger = logging.getLogger(__name__)


class SalesmanRoutePlanner(models.Model):
    _name = 'salesman.route.planner'
    _description = 'Salesman Route Planner'
    _inherit = 'mail.thread'
    _order = 'name'

    @api.depends('salesman_id')
    def set_name(self):
        for obj in self:
            if obj.salesman_id:
                obj.name = obj.salesman_id.name + ' маршрут'
            else:
                obj.name = 'Маршрут'

    # Columns
    name = fields.Char('Name', compute='set_name', store=True, readonly=True, copy=False)
    date = fields.Datetime('Created date', readonly=True, default=fields.Datetime.now(), copy=False)
    description = fields.Char(u'Description', copy=True, required=True, states={'confirmed': [('readonly', True)]})

    salesman_id = fields.Many2one('res.users', string='Salesman', required=True, copy=False,
                                  states={'confirmed': [('readonly', True)]})
    validator_id = fields.Many2one('res.users', string='Confirmed by', readonly=True)
    day_type = fields.Selection([
        ('weekly', 'By week'),
        ('monthly', 'By month'),
    ], string='Type', copy=True, default='weekly', required=True, )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], default='draft', required=True, string='State', tracking=True)

    _sql_constraints = [('salesman_id_uniq', 'unique (salesman_id)', 'Unique salesman!')]

    # ---------- CUSTOM ------------
    def action_to_draft(self):
        self.state = 'draft'

    def action_to_confirm(self):
        if not self.line_ids:
            raise UserError(_('Insert plan lines!'))
        self.state = 'confirmed'
        self.validator_id = self.env.user.id
        self.message_post(body="Confirmed by %s" % self.validator_id.name)

class SalesmanRoutePlannerLine(models.Model):
    _name = 'salesman.route.planner.line'
    _description = 'Salesman Route Planner Line'
    _order = 'week_day'

    # Columns
    parent_id = fields.Many2one('salesman.route.planner', 'Parent ID', ondelete='cascade')
    state = fields.Selection(related='parent_id.state', string="State", store=True)
    salesman_id = fields.Many2one(related='parent_id.salesman_id', string="Salesman", store=True)

    day_type = fields.Selection(related='parent_id.day_type', readonly=True)
    month_days = fields.Char(string="Month days", copy=True, help="Ex: 1,10,20")
    week_day = fields.Selection([
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ], string='Week day', copy=True, )

    route_ids = fields.Many2many('res.partner.route', string='Бүс', required=True,
                                 domain=[('route_type', '=', 'saler')])
    # added_partner_ids = fields.Many2many('res.partner', string='Added partners', compute='compute_added_partners')
    partner_ids = fields.Many2many('res.partner', string='Partners', copy=True, required=True, domain="[('route_id', 'in', route_ids)]")

    # @api.depends('parent_id.line_ids')
    # def compute_added_partners(self):
    #     for obj in self:
    #         obj.added_partner_ids = obj.mapped('parent_id.line_ids.partner_ids')

    # Partner дата бэлдэх
    @api.model
    def get_partner_datas(self, model, line_id, context=None):
        datas = {}
        temp = []
        obj = self.env['salesman.route.planner.line'].browse(line_id)
        for pa in obj.partner_ids:
            if pa.partner_latitude and pa.partner_longitude:
                p = {
                    'name': pa.name,
                    'lat': pa.partner_latitude,
                    'long': pa.partner_longitude
                }
                temp.append(p)
        datas['partners'] = temp
        _logger.info("----------------- Routes ===%s=== ", str(datas))
        return datas

    # Маршрутын дагуу байна уу эсэхийг шалгах
    def _check_partner_route(self, user_id, partner_id, date_order):
        routes = self.env['salesman.route.planner.line'].search([
            ('state', 'in', ['confirmed']),
            ('salesman_id', '=', user_id),
            ('partner_ids', 'in', partner_id),
        ])
        _logger.info("----------------- Routes %s", routes)
        if routes:
            my_date = datetime.strptime(date_order, "%Y-%m-%d")
            day = calendar.day_name[my_date.weekday()]
            _logger.info("----------------- Routes MONTH day, Week day %s %s", my_date.day, day)
            for route in routes:
                # Долоо хоногоор төлөвлөсөн эсэх шалгах
                if route.day_type == 'weekly':
                    if route.week_day == day:
                        return True
                # Сараар бол
                else:
                    days0 = route.month_days.split(',')
                    days = [int(x) for x in days0]
                    _logger.info("----------------- Routes MONTH days %s ", str(days))
                    if my_date.day in days:
                        return True
            return False
        else:
            return False


class SalesmanRoutePerformanceLine(models.Model):
    _name = 'salesman.route.performance.line'
    _description = 'Salesman Route Performance Line'
    _order = 'user_id, partner_id, date_order'

    # Columns
    user_id = fields.Many2one('res.users', string='User', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    date_order = fields.Date(string='Date', required=True)

    check_route = fields.Boolean(string='Маршрутын дагуу эсэх', default=False)
    state = fields.Selection([
        ('successful', 'Амжилттай'),
        ('lot_of_stock', 'Нөөц ихтэй'),
        ('closed', 'Хаалттай'),
        ('no_shop', 'Дэлгүүр татан буугдсан'),
        ('other', 'Бусад'),
    ], string='Type', )

class SalesmanRoutePlannerInherit(models.Model):
    _inherit = 'salesman.route.planner'

    line_ids = fields.One2many('salesman.route.planner.line', 'parent_id', 'Lines', copy=True,
                               states={'confirmed': [('readonly', True)]})

    # --------- OVERRIDED ----------
    def unlink(self):
        for s in self:
            if s.state != 'draft':
                raise UserError(_('In order to delete a record, it must be draft first!'))
        return super(SalesmanRoutePlannerInherit, self).unlink()