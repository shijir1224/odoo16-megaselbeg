#  -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import osv
import datetime
from datetime import  datetime, timedelta
from tempfile import NamedTemporaryFile
import base64
import xlrd
import  os

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class HrProjectEvaluation(models.Model):
	_name = "hr.project.evaluation"
	_descrition = 'Hr Project Evaluation'
	_inherit = ['mail.thread']

	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(HrProjectEvaluation, self).unlink()

	score = fields.Float('Тооцвол зохих гүй.урам-ын хувь',compute='_compute_score', store=True)
	huder = fields.Float(string='Хүдрийн бүтээл')
	name = fields.Char(string='Нэр')
	employee_id = fields.Many2one('hr.employee',string='Ажилтан')
	
	line_ids = fields.One2many('hr.project.evaluation.line','parent_id',string='Үнэлгээ')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True, required=True)
	date_from = fields.Date('Эхлэх огноо')
	date_to = fields.Date('Дуусах огноо')
	year = fields.Char('Жил')
	month = fields.Selection(
		[("1", "1 сар"),("2", "2 сар"),("3", "3 сар"),("4", "4 сар"),("5", "5 сар"),("6", "6 сар"),("7", "7 сар"),("8", "8 сар"),("9", "9 сар"),("90", "10 сар"),("91", "11 сар"),("92", "12 сар")],"Сар",required=True,)
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Хянасан'),('done_hr','Батласан'),('done','Нябо хүлээж авсан')],'Төлөв',default='draft',tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт файл')
	data = fields.Binary('Эксел файл')
	h_emp_id = fields.Many2one("hr.employee", "Хянасан")
	employee_id = fields.Many2one("hr.employee", "Нэгтгэсэн")
	confirm_emp_id = fields.Many2one("hr.employee", "Баталсан")

	@api.depends('huder')
	def _compute_score(self):
		for item in self:
			if item.huder >= 26000 and item.huder < 28000:
				item.score = 50
			elif item.huder >= 28000 and item.huder < 30000:
				item.score = 60
			elif item.huder >= 30000 and item.huder < 32000:
				item.score = 70
			elif item.huder >= 32000 and item.huder < 34000:
				item.score = 80
			elif item.huder >= 34000 and item.huder < 36000:
				item.score = 90
			elif item.huder >= 36000:
				item.score = 100
			else:
				item.score = 0

	def line_create(self):
		line_line_pool =  self.env['hr.project.evaluation.line']
		if self.line_ids:
			self.line_ids.unlink()
		employee =  self.env['hr.employee'].search([('employee_type','!=','resigned'),('work_location_id','=',2)])
		
		for rec in employee:
			obj = self.env['hour.balance.dynamic.line'].search([('month', '=', self.month ), ('year', '=', self.year ),('parent_id.type', '=', 'final'), ('employee_id','=', rec.id), ('state', '=', 'confirm_ahlah')])
			line_line_id = line_line_pool.create({
				'employee_id':rec.id,
				'parent_id':self.id,
				'employee_type':rec.employee_type,
				'job_id':rec.job_id.id,
				'attendance': obj.att_procent
			})
	
	
		
	def action_send(self):
		self.write({'state': 'sent'})
		
	def action_confirm(self):
		self.write({'state': 'confirm'})

	def action_done_hr(self):
		self.write({'state': 'done_hr'})


	def action_done(self):
		self.write({'state': 'done'})


	def action_draft(self):
		self.write({'state': 'draft'})

class HrProjectEvaluationLine(models.Model):
	_name = "hr.project.evaluation.line"
	_descrition = 'Hr Project Evaluation Line'
	_inherit = ['mail.thread']
	_order = 'employee_id'

	employee_id = fields.Many2one('hr.employee','Ажилтан')
	parent_id = fields.Many2one('hr.project.evaluation','Parent')
	employee_type = fields.Selection([
		('employee', 'Үндсэн ажилтан'),
		('student', 'Цагийн ажилтан'),
		('trainee', 'Туршилтын ажилтан'),
		('contractor', 'Гэрээт'),
		('longleave', 'Урт хугацааны чөлөөтэй'),
		('maternity', 'Хүүхэд асрах чөлөөтэй'),
		('pregnant_leave', 'Жирэмсний амралт'),
		('resigned', 'Ажлаас гарсан'),
		('waiting', 'Хүлээгдэж буй'),
		('blacklist', 'Blacklist'),
		('freelance', 'Бусад'),
	], string='Ажилтны төлөв')
	attendance = fields.Float(string='Ирцийн хувь', compute = False)
	discipline = fields.Selection([('yes','Тийм'),('no','Үгүй')],string='Сахилгын шийтгэл', compute='_compute_discipline' )
	hab = fields.Selection([('yes','Тийм'),('no','Үгүй')],string='ХАБЭА,БО-ны зөрчил', compute = '_compute_hab')
	accident = fields.Selection([('yes','Тийм'),('no','Үгүй')],string='Үйлдвэрлэлийн осол, хурц хордлого бүртгэгдсэн эсэх', compute ='_compute_accident')
	description = fields.Char(string='Тайлбар')
	huder = fields.Float(string='Хүдрийн бүтээл',related='parent_id.huder',store=True)
	score = fields.Float('Тооцвол зохих гүй.урам-ын хувь',related='parent_id.score',store=True)
	not_score = fields.Float('Биелэгдээгүй хүдрийн бүтээлийн хувь')
	stop = fields.Float('Төл.бус зогсолтын цагт ногдох хувь')
	amount_score = fields.Float('Гүй.урамшуулал тооцох хувь', compute = '_compute_amount_score',store=True)
	is_ita = fields.Many2one('hr.employee', 'is_ita')
	disc_type = fields.Char('Шийтгэлийн шалтгаан')
	injury_reason = fields.Char('Үйлд.осол, хурц.хор шалтгаан')
	job_id = fields.Many2one('hr.job',string='Албан тушаал')
	date_from = fields.Date('Эхлэх огноо',related='parent_id.date_from',store=True)

	@api.depends('parent_id.date_from', 'discipline')
	def _compute_discipline(self):
		for item in self:
			obj = item.env['hr.order'].search([('start_date', '>=', item.parent_id.date_from),('state', '=', 'done')])
			line = obj.filtered(lambda r: r.order_employee_id == item.employee_id and r.order_type_id.type == 'type10')
			if line:
				item.discipline = 'yes'
				item.disc_type = line.discipline_name
			else:
				item.discipline = 'no'

	
			
	@api.depends('parent_id.date_from', 'parent_id.date_to')
	def _compute_hab(self):
		for item in self:
			obj =item.env['hse.discipline.action'].search([('employee_id', '=', item.employee_id.id), ('state', 'in', ('done','master'))])
			if obj:
				for line in obj:
					if line.now_discipline_date:
						now_discipline_date = (datetime.strptime(str(line.now_discipline_date), DATETIME_FORMAT)  + timedelta(hours=8)).date()
						if now_discipline_date >= item.parent_id.date_from and now_discipline_date <= item.parent_id.date_to:
							item.hab = 'yes'
			else:
				item.hab = 'no'


	@api.depends('parent_id.date_from', 'parent_id.date_to')
	def _compute_accident(self):
		for item in self:
			obj = item.env['accident.investigation'].search([('reporter_date', '>=', item.parent_id.date_from), ('reporter_date', '<=', item.parent_id.date_to), ('accident_employee_lines.employee_id', '=', item.employee_id.id),('state', '=', 'done')])
			if obj:
				for line in obj:
					item.accident = 'yes'
					item.injury_reason = line.injury_reason_ids.name
			else:
				item.accident = 'no'
				

	@api.depends('hab','discipline','stop','attendance', 'score','employee_id','parent_id.date_from','parent_id.date_to')
	def _compute_amount_score(self):
		for item in self:
			if item.parent_id.date_from and item.parent_id.date_to and item.employee_id:
				if item.employee_id.engagement_in_company >= item.parent_id.date_from and item.employee_id.engagement_in_company <=item.parent_id.date_to:
					item.amount_score = ((item.score - item.stop) * item.attendance) / 100
				else:
					if item.hab == 'yes' or item.discipline == 'yes' or item.accident == 'yes' or item.attendance < 100:
						item.amount_score = 0
					else:
						item.amount_score = ((item.score - item.stop) * item.attendance) / 100

			



	
	
