from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

class HseHealthReference(models.TransientModel):
	_name = 'hse.health.reference'
	_description = 'Hse health reference'

	lastname = fields.Char('Овог')
	name = fields.Char('Нэр')
	vat = fields.Char('Регистрийн №')
	phone = fields.Char('Утас')
	employee_id = fields.Many2one('hr.employee', string='Харилцагч', readonly=True)
	hse_health_ids = fields.One2many('hse.health', related='employee_id.hse_health_ids', string=' Өвчний түүх', readonly=True, compute_sudo=True)
	history_ids = fields.Many2many('hse.health.history', readonly=True, compute_sudo=True, string="Үзлэгийн Түүх", compute='com_history')
	physical_ids = fields.Many2many('hse.physical.development', string='Бие бялдарын хөгжил', compute_sudo=True, compute='compute_physical',readonly=True)
	detection_ids = fields.Many2many('hse.early.detection', readonly=True, compute_sudo=True, string="Эрт Илрүүлэг", compute='com_detection')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	questionnaire_ids = fields.Many2many('health.questionnaire.line', readonly=True, compute_sudo=True, string="Эрүүл мэндийн асуумж", compute='com_questionnaire')
	specialist_ids = fields.Many2many('specialist.doctor.line', readonly=True, compute_sudo=True, string="Нарийн мэргэжлийн үзлэг", compute='com_specialist')

	@api.depends('history_ids','hse_health_ids')
	def com_history(self):
		for item in self:
			xxx = item.hse_health_ids.mapped('history_ids')
			item.sudo().history_ids = xxx
   
	@api.depends('physical_ids', 'hse_health_ids')
	def compute_physical(self):
		for item in self:
			xxx = item.hse_health_ids.mapped('physical_ids')
			item.sudo().physical_ids = xxx


	@api.depends('detection_ids','hse_health_ids')
	def com_detection(self):
		for item in self:
			xxx = item.hse_health_ids.mapped('detection_ids')
			item.sudo().detection_ids = xxx
	
	@api.depends('questionnaire_ids','hse_health_ids')
	def com_questionnaire(self):
		for item in self:
			xxx = item.hse_health_ids.mapped('health_questionnaire_line_ids')
			item.sudo().questionnaire_ids = xxx

	@api.depends('specialist_ids','hse_health_ids')
	def com_specialist(self):
		for item in self:
			xxx = item.hse_health_ids.mapped('specialist_doctor_line_ids')
			item.sudo().specialist_ids = xxx
		

	def find(self):
		domain = []
		oruud_cnt = 0
		if self.vat:
			oruud_cnt += 1
			domain.append(('employee_id.passport_id','ilike',self.vat))
		if self.phone:
			oruud_cnt += 1
			domain.append(('employee_id.work_phone','ilike',self.phone))
		if self.lastname:
			oruud_cnt += 1
			domain.append(('employee_id.last_name','ilike',self.lastname))
		if self.name:
			oruud_cnt += 1
			domain.append(('employee_id.name','like',self.name))
		oruud = []
		for x in range(1, oruud_cnt):
			oruud.append('|')
		oruud_cnt += 1
		domain = oruud + domain
		pols = self.env['hse.health'].sudo().search(domain, limit=1)
		if pols and pols.employee_id:
			self.employee_id = pols.employee_id.id
		else:
			self.employee_id = False


class HrEmployee(models.Model):
	_inherit = 'hr.employee'
	_description = 'Employee'

	hse_health_ids = fields.One2many('hse.health', 'employee_id', string='Эрүүл мэнд үзлэг')