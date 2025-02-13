# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

JOB_TYPE = [
	('operator','Оператор'),
	('repairman','Засварчин'),
	('clerk','Клерк'),
	('dispatcher','Диспетчер'),
	('check_mechanic','Шалгах механик'),
	('planner','Төлөвлөгч'),
	('master','Ээлжийн ахлах'),
	('maintenance_supervisor','Засварын ахлах'),
	('maintenance_superintendent','Засварын дарга'),
]

class hrDepartment(models.Model):
	_inherit = 'hr.department'

	is_maintenance = fields.Boolean(string='Засварын хэлтэс эсэх', default=True)

class hrJob(models.Model):
	_inherit = 'hr.job'

	maintenance_job_types = fields.Selection(JOB_TYPE, string=u'Засвар & Техникийн албал тушаал')