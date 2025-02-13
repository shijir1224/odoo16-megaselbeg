# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class MaintenanceInspectionConfig(models.Model):
	_inherit = 'maintenance.inspection.config'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True, 
		default=lambda self: self.env.user.company_id,)

	_sql_constraints = [('config_name_uniq', 'unique(company_id,name)', 'Name must be unique!')]

class MaintenanceExperienceLibrary(models.Model):
	_inherit = 'maintenance.experience.library'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True, 
		default=lambda self: self.env.user.company_id,)
