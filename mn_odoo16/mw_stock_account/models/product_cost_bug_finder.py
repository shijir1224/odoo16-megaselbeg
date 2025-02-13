# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_is_zero

import logging

_logger = logging.getLogger(__name__)

class product_cost_bug_finder(models.Model):
    _name = 'product.cost.bug.finder'
    _description = 'Product cost bug finder'