from odoo import fields, models,api,_
from odoo.osv import osv
from tempfile import NamedTemporaryFile
import base64
import xlrd
import  os
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"


class HrEvaluationCons(models.Model):
	_name = "hr.evaluation.cons"
	_descrition = 'Hr Evaluation Cons'
	_inherit = ['mail.thread']

	year = fields.Char(string='Жил')
	month = fields.Integer(string='Сар')
	date_from = fields.Date('Эхлэх огноо')
	date_to = fields.Date('Дуусах огноо')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True, required=True)
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Хянасан'),('confirm_hr','Баталсан'),('done','Нябо хүлээж авсан')],default='draft',string='Төлөв',tracking=True)
	line_ids = fields.One2many('hr.evaluation.cons.line','parent_id',string='Үнэлгээ мөр')
	data = fields.Binary('Эксел файл')
	h_emp_id = fields.Many2one("hr.employee", "Хянасан")
	employee_id = fields.Many2one("hr.employee", "Нэгтгэсэн")
	confirm_emp_id = fields.Many2one("hr.employee", "Баталсан")

	def line_create(self):
		if self.line_ids:
			self.line_ids.unlink()
		if self.work_location_id:
			line_obj = self.env['hr.evaluation.cons.line']
			employees = self.env['hr.employee'].search([('work_location_id','=',self.work_location_id.id),('employee_type','=',('employee','trainee','contractor'))])
			for emp in employees:
				line_id = line_obj.create({
					'parent_id':self.id,
					'department_id':emp.department_id.id,
					'employee_id':emp.id,
					'job_id':emp.job_id.id,
				})

	def compute_line(self):
		for line in self.line_ids:
			plan =0
			daily=0
			team=0
			lines_daily = self.env['hr.evaluation.line'].search([('employee_id','=',line.employee_id.id),('state','=','done'),('year','=',self.year)])
			lines_plan = self.env['hr.evaluation.emp'].search([('employee_id','=',line.employee_id.id),('state','=','done'),('year','=',self.year),('month','=',self.month)])
			lines_team = self.env['hr.evaluation.plan'].search([('state','=','done'),('year','=',self.year),('month','=',self.month)])
			l_hb = self.env['hour.balance.dynamic.line'].search([('state','=','done'),('date_from','=',self.date_from),('date_to','=',self.date_to),('employee_id','=',line.employee_id.id)],limit=1)
			ll_hb_day = self.env['hour.balance.dynamic.line.line'].search([('hour_type','=','working_day'),('parent_id','=',l_hb.id)])
			ll_hb_hour = self.env['hour.balance.dynamic.line.line'].search([('hour_type','=','working_ub'),('parent_id','=',l_hb.id)])
			if l_hb.employee_id.id == line.employee_id.id:
				att_procent=0
				if ll_hb_hour.hour * 100>0:
					att_procent = ll_hb_hour.hour * 100/l_hb.hour_to_work_month
				line.update({
					'leave_day':ll_hb_day.hour,
					'hour_to_work':l_hb.hour_to_work_month,
					'worked_hour':ll_hb_hour.hour,
					'att_procent':att_procent
				})
				
			for ld in lines_daily:
				if line.employee_id.is_shu != True:
					if int(ld.month) == self.month:
						if ld.sum_amount>0:
							daily = ld.sum_amount * 0.6
						line.update({
							'daily_score':daily
						})
			for lp in lines_plan:
				if line.employee_id.is_shu != True:
					if lp.sum_amount>0:
						plan = lp.sum_amount * 0.3
					line.update({
						'plan_score':plan
					})
			for lt in lines_team:
				if lt.department_id.id == line.department_id.id:
					if line.employee_id.is_shu == True:
						team_score=0
						bag = lt.kpi_daily_head + lt.kpi_head
						if bag>0:
							team_score = bag/2
						line.update({
							'daily_score':lt.kpi_daily_head,
							'team_score':team_score,
							'plan_score':lt.kpi_head
						})
					elif line.job_id.job_code == 'захирал':
						line.update({
							'plan_score':lt.kpi_head
						})
					else:
						if lt.kpi_team>0:
							team = lt.kpi_team * 0.10
						line.update({
							'team_score':team
						})


	
	
	def action_send(self):
		self.write({'state': 'sent'})
		for line in self.line_ids:
			line.write({'state':'sent'})

	def action_return(self):
		self.write({'state': 'sent'})
		for line in self.line_ids:
			line.write({'state':'sent'})
	
	def action_confirm(self):
		self.write({'state':'confirm'})
		for line in self.line_ids:
			line.write({'state':'confirm'})
	
	def action_confirm_hr(self):
		self.write({'state':'confirm_hr'})
		for line in self.line_ids:
			line.write({'state':'confirm_hr'})

	def action_done(self):
		self.write({'state':'done'})
		for line in self.line_ids:
			line.write({'state':'done'})
		

	def action_draft(self):
		self.write({'state': 'draft'})
		for line in self.line_ids:
			line.write({'state':'draft'})
	

class HrEvaluationConsLine(models.Model):
	_name = "hr.evaluation.cons.line"
	_descrition = 'Hr Evaluation Cons Line'
	_inherit = ['mail.thread']
	_order = 'department_id,employee_id'

	parent_id = fields.Many2one('hr.evaluation.cons','Parent',ondelete='cascade')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	department_id = fields.Many2one('hr.department','Хэлтэс')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	year = fields.Char(string='Жил',related='parent_id.year',store=True)
	month = fields.Integer(string='Сар',related='parent_id.month',store=True)
	daily_score = fields.Float('Өдөр тутмын үйл ажиллагааны гүйцэтгэл-60%', digits=(2, 0))
	plan_score = fields.Float('Төлөвлөгөөт ажлын гүйцэтгэл-30%', digits=(2, 0))
	team_score = fields.Float('Багийн гүйцэтгэл-10%', digits=(2, 0))
	total_score = fields.Float('Нийт гүйцэтгэлийн үнэлгээ',store=True, digits=(2, 0),compute='_compute_total_score')
	leave_day = fields.Float('ЭА болон чөлөөний хоног', digits=(2, 0))
	worked_hour = fields.Float('Ажилласан цаг', digits=(2, 0))
	hour_to_work = fields.Float('AЗ цаг', digits=(2, 0))
	att_procent = fields.Float('Ирцийн хувь', digits=(2, 0),compute='_compute_total_score',store=True)
	descrition = fields.Char('Тайлбар')
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Хянасан'),('confirm_hr','Баталсан'),('done','Нябо хүлээж авсан')],default='draft',string='Төлөв')
	date_from = fields.Date('Эхлэх огноо',related='parent_id.date_from',store=True)

	def action_emp_done(self):
		self.write({'state':'emp_done'})

	@api.depends('daily_score','plan_score','team_score','employee_id.is_shu','worked_hour','hour_to_work','att_procent','job_id.job_code','leave_day')
	def _compute_total_score(self):
		for obj in self:
			if obj.employee_id.is_shu==True:
				if obj.leave_day >=4:
					obj.total_score = (obj.team_score * obj.att_procent)/100
				else:
					obj.total_score = obj.team_score
			elif obj.job_id.job_code == 'захирал':
				obj.total_score = obj.plan_score
			else:
				if obj.leave_day >=4:
					obj.total_score = (obj.daily_score * obj.att_procent)/100  + obj.plan_score + obj.team_score
				else:
					obj.total_score = obj.daily_score + obj.plan_score + obj.team_score
				

	
class HrEmployee(models.Model):
	_inherit = 'hr.employee'
	
	is_shu = fields.Boolean(string='Хэлтсийн удирдлага эсэх', default=False)
	ev_cons_ids = fields.One2many('hr.evaluation.cons.line','employee_id',string='Үнэлгээ')
