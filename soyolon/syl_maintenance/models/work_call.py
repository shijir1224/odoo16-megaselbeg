# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time


class WorkCall(models.Model):
    _name = 'work.call'

    name = fields.Char(string='Нэр', required=True)
    code = fields.Float(string='Код')
    company = fields.Many2one('res.company', string='Компани')
