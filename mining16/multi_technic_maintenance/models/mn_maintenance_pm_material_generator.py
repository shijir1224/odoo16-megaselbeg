# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenancePmMaterialGenerator(models.Model):
	_inherit = 'maintenance.pm.material.generator'
	# Columns
	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)
