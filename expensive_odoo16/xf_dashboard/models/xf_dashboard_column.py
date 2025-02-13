# -*- coding: utf-8 -*-
from odoo import models, fields


class XFDashboardColumn(models.Model):
    _name = 'xf.dashboard.column'
    _description = 'Dashboard Column'
    _order = 'sequence asc'

    col_selection = [(str(n), str(n)) for n in range(1, 13)]

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True, translate=True)
    row_id = fields.Many2one('xf.dashboard.row', 'Row', required=True)
    col_sm = fields.Selection(string='Col SM', selection=col_selection, required=True, default='12')
    col_md = fields.Selection(string='Col MD', selection=col_selection, required=True, default='12')
    col_lg = fields.Selection(string='Col LG', selection=col_selection, required=True, default='12')
    col_xl = fields.Selection(string='Col XL', selection=col_selection, required=True, default='12')

    widgets = fields.One2many('xf.dashboard.widget', 'column_id', 'Widgets', readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Dashboard column name must be unique!'),
    ]
