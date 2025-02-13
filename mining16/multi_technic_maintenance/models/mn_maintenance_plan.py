# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenancePlan(models.Model):
	_inherit = 'maintenance.plan'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)

class MaintenancePlanLine(models.Model):
	_inherit = 'maintenance.plan.line'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)
