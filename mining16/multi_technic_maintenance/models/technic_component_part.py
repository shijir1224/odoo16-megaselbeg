# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class TechnicComponentPart(models.Model):
	_inherit = 'technic.component.part'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True, default=lambda self: self.env.user.company_id,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	# Constraints
	_sql_constraints = [
		('component_uniq', 'unique(company_id,serial_number)', "Serial number must be unique!"),
	]

class TechnicComponentConfig(models.Model):
	_inherit = 'technic.component.config'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True, 
		default=lambda self: self.env.user.company_id,)