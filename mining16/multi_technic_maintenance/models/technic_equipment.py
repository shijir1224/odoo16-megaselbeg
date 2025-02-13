# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import collections
from odoo.osv import expression

class TechnicEquipmentSetting(models.Model):
	_inherit = 'technic.equipment.setting'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)

class TechnicEquipment(models.Model):
	_inherit = 'technic.equipment'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True, default=lambda self: self.env.user.company_id,
		states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
				'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

	_sql_constraints = [
		('technic_uniq', 'unique(company_id,vin_number,name)', "Technic's name and VIN must be unique!")
	]