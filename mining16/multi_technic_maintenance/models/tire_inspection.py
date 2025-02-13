# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class TireInspect(models.Model):
	_inherit = 'tire.inspection'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})

	_sql_constraints = [
		('name_uniq', 'unique(company_id,name)', 'Name must be unique!'),
	]