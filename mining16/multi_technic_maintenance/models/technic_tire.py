# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

class TechnicTireSetting(models.Model):
	_inherit = 'technic.tire.setting'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)

class TechnicTire(models.Model):
	_inherit = 'technic.tire'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True, default=lambda self: self.env.user.company_id,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
		        'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	# Constraints
	_sql_constraints = [
		('tire_uniq', 'unique(company_id,serial_number)', "Serial number must be unique!"),
	]
