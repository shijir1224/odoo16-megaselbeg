from email.policy import default
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning
import time


class HealthTreatment(models.Model):
	_name ='health.treatment'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'health treatment'
   
	name = fields.Char(string='Гарчиг', tracking=True, required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	treatment_line_ids = fields.One2many('health.treatment.line', 'treatment_id', string='Эмчилгээний мөр')
	ambulance_line_id = fields.Many2one('hse.ambulance', string='Холбоотой үзлэг')
 
	def unlink(self):
		for line in self:
			if line.treatment_line_ids:
				raise UserError('Эмчилгээний мөр байна.!!!')
		return super(HealthTreatment, self).unlink()

class HealthTreatmentLine(models.Model):
	_name ='health.treatment.line'
	_description = 'health treatment line'


	treatment_id = fields.Many2one('health.treatment', string='Treatment ID', )
	treatment_type = fields.Selection([
		('drug', 'Эм тарианы эмчилгээ'),
		('phys', 'Физик эмчилгээ'),
		('other', 'Бусад')
	], string='Эмчилгээний төрөл')
	health_precise_id = fields.Many2one('health.precise.treatment', string='Эмчилгээ')
	treatment_fre = fields.Integer(string='Эмчилгээний давтамж')


class HealthPreciseTreatment(models.Model):
	_name ='health.precise.treatment'
	_description = 'health precise treatment'

	name = fields.Char(string='Эмчилгээний нэр')