# -*- coding: utf-8 -*-

from odoo import models, fields


class XFDashboardIcon(models.Model):
    _name = 'xf.dashboard.icon'
    _description = 'Dashboard Icon'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    icon = fields.Image(string='Icon', attachment=True, required=True, copy=False)
