# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
import json

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, ustr
from odoo.exceptions import ValidationError
from odoo.osv import expression

class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "account financial report line"

    aged_number = fields.Integer(string='Насжилт бодох хоног',)
