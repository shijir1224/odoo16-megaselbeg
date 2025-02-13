# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import logging

class MaintenanceWorkOrder(models.Model):
	_inherit = 'maintenance.workorder'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)
	# Constraint
	_sql_constraints = [('wo_name_uniq', 'unique(company_id,name)','Name must be unique!')]
