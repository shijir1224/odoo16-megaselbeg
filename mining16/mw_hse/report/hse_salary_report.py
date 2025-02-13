# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from datetime import datetime, timedelta

import pytz

class hse_my_safety(models.TransientModel):
    _name ='hse.salary.report'
    _description = 'Hse Salary Report'

    
    
