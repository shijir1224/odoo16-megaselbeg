from odoo import  api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class HseWorkHazardAnalysis(models.Model):
	_name = 'hse.work.hazard.analysis'
	_description = 'Hse Work Hazard Analysis'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	def _get_name(self):
		return self.env['ir.sequence'].next_by_code('hse.work.hazard.analysis')

	name = fields.Char(string='Дугаар' , default=_get_name, readonly=True)
	state = fields.Selection([
		('draft','Ноорог'),
		('sent','Илгээсэн'),
		('done', 'Дууссан')], 'Төлөв', readonly=True, default='draft', tracking=True)
	branch_id = fields.Many2one('res.branch', string='Төсөл', required=True, states={'done':[('readonly',True)]})
	date = fields.Date(string='Үүсгэсэн огноо', required=True, readonly=True, states={'draft':[('readonly',False)]}, default=fields.Date.context_today)
	location_id = fields.Many2one('hse.location', string='Байршил', required=True, states={'done':[('readonly',True)]})
	equipment_ids = fields.Many2many('work.equipment', 'equipment_id', 'analysis_id', string='Ажлын тусгай хувцас, нэг бүрийн хамгаалах хэрэгсэл', domain="[('type','=','equipment')]")
	people_ids = fields.Many2many('work.equipment', 'people_id', 'analysis_id', string='Ажиллах хүчний бүрэлдэхүүн', domain="[('type','=','people')]")
	danger_ids = fields.Many2many('work.equipment', 'danger_id', 'analysis_id', string='Ажил гүйцэтгэхэд учирч болох аюул, эрсдэл', domain="[('type','=','danger')]")
	consent_ids = fields.Many2many('work.equipment', 'consent_id', 'analysis_id', string='Өндөр эрсдэлтэй ажлын зөвшөөрөл', domain="[('type','=','consent')]")
	safe_ids = fields.Many2many('work.equipment', 'safe_id', 'analysis_id', string='Аюулгүй байдлын арга хэмжээ', domain="[('type','=','safe')]")
	danger_work_ids = fields.One2many('danger.analysis', 'danger_work_id', string='Ажлын алхам')
	team_status_ids = fields.One2many('hse.work.hazard.analysis.line','parent_id', string='Багын мэдээлэл')
	hse_employee_id = fields.Many2one('hr.employee', string='ХАБ ажилтан', required=True, states={'done':[('readonly',True)]})


	def action_to_done(self):
		self.write({'state': 'done'})
	
	def action_to_sent(self):
		self.write({'state': 'sent'})

	def action_to_draft(self):
		self.write({'state': 'draft'})
	
class HseWrokHazardAnalysisLine(models.Model):
	_name = 'hse.work.hazard.analysis.line'
	_description = 'Hse Work Hazard Analysis Line'
	_sql_constraints = [('employee_id_uniq', 'unique(parent_id,employee_id)', u'Ажилтан даврардахгүй!')]
	
	parent_id = fields.Many2one('hse.work.hazard.analysis', string='Багын мэдээлэл', required=True)
	team_user_type = fields.Selection([
		('a', ' Ахлагч'),
		('b', 'Гишүүн')
	], 'Багийн статус',  readonly=True)
	employee_id = fields.Many2one('hr.employee', string='Ажилтан')
	lname = fields.Char( related='employee_id.last_name', string='Овог', store=True)
	fname = fields.Char( related='employee_id.name', string='Нэр', store=True)
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал', store=True)


class WorkEquipment(models.Model):
	_name = 'work.equipment'
	_description = 'Work Equipment'

	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
		('equipment','Ажлын тусгай хувцас, нэг бүрийн хамгаалах хэрэгсэл'),
		('people','Ажлах хүчний бүрэлдхүүн'), 
		('danger','Ажлах гүйцэтгэхэд учирч болох аюул, эрсдэл'), 
		('consent','Өндөр эрсдэлтэй ажлын зөвшөөрөл'), 
		('safe','Аюулгүй байдлын арга хэмжээ')
	], string='Төрөл', required=True)


class DangerAnalysis(models.Model):
	_name = 'danger.analysis'
	_description = 'Danger Analysis'
	
	danger_work_id = fields.Many2one('hse.work.hazard.analysis',string= 'Дүн шинжилгээ')
	work_step = fields.Char( string='Ажлын алхам')
	work_danger = fields.Char( string='Аюул')
	work_result = fields.Char( string='Үр дагавар')
	work_control = fields.Char( string='Хяналт')
	work_tips = fields.Char( string='Нэмэлт зөвлөмж')
