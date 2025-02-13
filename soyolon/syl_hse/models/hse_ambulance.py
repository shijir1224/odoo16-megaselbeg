from odoo import  api, fields, models, _
from datetime import datetime, timedelta

from odoo.http import request
import json


class HseAmbulance(models.Model):
	_inherit ='hse.ambulance'

	employee_id = fields.Many2one('hr.employee', domain="[('is_doctor','=',True)]", string='Үзлэг хийсэн ажилтан', tracking=True, readonly=True, states={'draft':[('readonly',False)]})