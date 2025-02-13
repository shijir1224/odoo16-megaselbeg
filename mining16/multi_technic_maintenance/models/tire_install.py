# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class TechnicTireInstall(models.Model):
	_inherit = 'technic.tire.install'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,
		states={'open': [('readonly', True)],'remove': [('readonly', True)],'done': [('readonly', True)]})
