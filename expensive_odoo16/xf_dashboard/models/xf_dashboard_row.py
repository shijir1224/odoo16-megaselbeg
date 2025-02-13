# -*- coding: utf-8 -*-
from odoo import models, fields


class XFDashboardRow(models.Model):
    _name = 'xf.dashboard.row'
    _description = 'Dashboard Row'
    _order = 'sequence asc'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True, translate=True)
    groups = fields.Many2many('res.groups', 'xf_dashboard_row_groups', 'row_id', 'group_id',
                              string='Groups',
                              help="If this field is empty, the row applies to all users. "
                                   "Otherwise, the row applies to the users of those groups only.")
    columns = fields.One2many('xf.dashboard.column', 'row_id', 'Columns')
    widgets = fields.One2many('xf.dashboard.widget', 'row_id', 'Widgets', readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Dashboard Row Name must be unique!'),
    ]
