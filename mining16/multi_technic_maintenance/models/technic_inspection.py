# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class TechnicInspectSetting(models.Model):
	_inherit = "technic.inspection.setting"

	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)

class TechnicInspect(models.Model):
	_inherit = 'technic.inspection'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True, default=lambda self: self.env.user.company_id,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})