# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenancePlanGenerator(models.Model):
	_inherit = 'maintenance.plan.generator'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True, 
		default=lambda self: self.env.user.company_id,)