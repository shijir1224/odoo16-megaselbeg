# -*- coding: utf-8 -*-
from datetime import  datetime
from odoo.exceptions import UserError
from odoo import api, fields, models, _

DATE_FORMAT = "%Y-%m-%d"


class HrEvaluationConfiguration(models.Model):
	_name = "hr.performance"
	_descrition = 'Hr Evaluation Configuration'
	_inherit = ['mail.thread']

	def name_get(self):
		res = []
		for obj in self:
			if obj.name:
				res.append((obj.id,obj.name))
			else:
				res.append((obj.id, obj.name))
		return res

	name = fields.Char('Зорилт',tracking=True)
	score = fields.Float('Авах оноо',tracking=True)
	company_id = fields.Many2one('res.company', string='Компани')

class HrEvaluation(models.Model):
	_name = "hr.evaluation"
	_descrition = 'Hr Evaluation'
	_inherit = ['mail.thread']

	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(HrEvaluation, self).unlink()


	line_ids = fields.One2many('hr.evaluation.line','parent_id','Үнэлгээ')
	department_id = fields.Many2one('hr.department','Хэлтэс',tracking=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил',tracking=True)
	job_ids = fields.Many2many('hr.job', string='Үзүүлэлт өөрчилөх албан тушаалууд',tracking=True)
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True, required=True)
	date = fields.Date('Хугацаа', required=True,tracking=True)
	year = fields.Char('Жил', readonly=True)
	month = fields.Char('Сар', readonly=True)
	day = fields.Char('Өдөр', readonly=True)
	state = fields.Selection([('draft','Ноорог'),('sent','Цоожлогдсон'),('done','Үнэлсэн')],'Төлөв',default='draft',tracking=True)
	is_manager = fields. Boolean('Менежер үнэлэх эсэх', default=True)

	def action_send(self):
		self.write({'state': 'sent'})

	def action_done(self):
		self.write({'state': 'done'})

	def action_draft(self):
		self.write({'state': 'draft'})

	@api.onchange('date')
	def onchange_date(self):
		if self.date:
			start_date = datetime.strptime(str(self.date), DATE_FORMAT)
			self.year = str(self.date)[:4]
			self.month = start_date.month
			self.day = start_date.day


	# Албан тушаалаар үзүүлэлт өөрчлөх
	def update_job_lines(self):
		line_line_pool =  self.env['hr.evaluation.line.line']
		for item in self.line_ids:
			if item.job_id.id in (self.job_ids.ids):
				recs_job =  self.env['job.configuration'].search([('job_id','=',item.job_id.id)])
				if item.line_line_ids:
					item.line_line_ids.unlink()
				for rec in recs_job:
					e_ids = rec.give_employee_ids.mapped('id')
					j_ids = rec.give_job_ids.mapped('id')
					if rec.job_id.is_evaluation == True:
						line_line_id = line_line_pool.create({
							'line_parent_id':item.id,
							'conf_id':rec.conf_id.id,
							'score':rec.score,
							'get_score':0,
							'give_employee_ids':e_ids,
							'give_job_ids':j_ids,
						})


	def create_from_job(self,line_id):
		if self.is_manager==True:
			line_line_pool =  self.env['hr.evaluation.line.line']
			recs_job =  self.env['job.configuration'].search([('job_id','=',line_id.job_id.id)])
			driver_ids =[]
			for rec in recs_job:
				emp_ids = self.env['hr.employee'].search([('id','=',line_id.employee_id.parent_id.id)])
				driver_ids = emp_ids.mapped('id')
				line_line_id = line_line_pool.create({
					'line_parent_id':line_id.id,
					'conf_id':rec.conf_id.id,
					'score':rec.score,
					'get_score':0,
					'give_employee_ids':driver_ids,
					# 'give_job_ids':line_id.employee_id.parent_id.id,
				})
		else:
			line_line_pool =  self.env['hr.evaluation.line.line']
			recs_job =  self.env['job.configuration'].search([('job_id','=',line_id.job_id.id)])
			for rec in recs_job:
				e_ids = rec.give_employee_ids.mapped('id')
				j_ids = rec.give_job_ids.mapped('id')
				line_line_id = line_line_pool.create({
					'line_parent_id':line_id.id,
					'conf_id':rec.conf_id.id,
					'score':rec.score,
					'get_score':0,
					'give_employee_ids':e_ids,
					'give_job_ids':j_ids,
				})

	def create_from_employee(self,line_id):
		if self.is_manager==True:
			line_line_pool =  self.env['hr.evaluation.line.line']
			recs_emp=  self.env['employee.configuration'].search([('employee_id','=',line_id.employee_id.id)])
			for rec in recs_emp:
				emp_ids = self.env['hr.employee'].search([('id','=',line_id.employee_id.parent_id.id)])
				driver_ids = emp_ids.mapped('id')
				line_line_id = line_line_pool.create({
					'line_parent_id':line_id.id,
					'conf_id':rec.conf_id.id,
					'score':rec.score,
					'get_score':0,
					'give_employee_ids':driver_ids,
					# 'give_job_ids':line_id.employee_id.parent_id.id,
				})
		else:
			line_line_pool =  self.env['hr.evaluation.line.line']
			recs_emp=  self.env['employee.configuration'].search([('employee_id','=',line_id.employee_id.id)])
			for rec in recs_emp:
				e_ids = rec.give_employee_ids.mapped('id')
				j_ids = rec.give_job_ids.mapped('id')
				line_line_id = line_line_pool.create({
					'line_parent_id':line_id.id,
					'conf_id':rec.conf_id.id,
					'score':rec.score,
					'get_score':0,
					'give_employee_ids':e_ids,
					'give_job_ids':j_ids,
				})

	def set_conditions(self):
		conditions = ""
		if  self.department_id and self.work_location_id:
			conditions = "and hc.id=%s" % self.work_location_id.id
			conditions +=  " and hd.id = %s " % self.department_id.id
		elif self.department_id:
			conditions = " and hd.id = %s " % self.department_id.id
		elif self.work_location_id:
			conditions = " and hc.id = %s " % self.work_location_id.id
		return conditions

	def line_create(self):
		line_pool =  self.env['hr.evaluation.line']
		if self.line_ids:
			self.line_ids.unlink()
		if self.company_id:
			query = """ SELECT
				hr.id as id,
				hr.identification_id as ident_id,
				hr.is_evaluation as hr_evaluation,
				hr.employee_type as employee_type,
				hj.id as hj_id,
				hj.is_evaluation as hj_evaluation,
				rc.id as rc_id,
				hc.id as hc_id,
				hd.id as hd_id
				FROM hr_employee hr
				INNER JOIN hr_job hj ON hr.job_id=hj.id
				INNER JOIN res_company rc ON hr.company_id=rc.id
				INNER JOIN hr_department hd ON hr.department_id=hd.id
				INNER JOIN hr_work_location hc ON hr.work_location_id=hc.id
				WHERE hr.employee_type in ('employee','trainee','contractor') and rc.id=%s %s """%(self.company_id.id,self.set_conditions())
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			for record in records:
				line_id = line_pool.create({
					'parent_id':self.id,
					'ident_id':record['ident_id'],
					'employee_id':record['id'],
					'job_id':record['hj_id'],
					'department_id':record['hd_id'],
					'company_id':record['rc_id'],
					'work_location_id':record['hc_id'],
					# 'employee_type':record['employee_type'],
					'year':self.year,
					'month':self.month,
					'date':self.date,
				})
				if record['hr_evaluation'] == True:
					self.create_from_employee(line_id)
				elif record['hj_evaluation'] == True:
					self.create_from_job(line_id)


class HrEvaluationLine(models.Model):
	_name = "hr.evaluation.line"
	_descrition = 'Hr Evaluation Line'
	_inherit = ['mail.thread']


	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(HrEvaluationLine, self).unlink()


	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	@api.depends('department_id')
	def _parent_department_id(self):
		for obj in self:
			if obj.department_id:
				if obj.department_id.parent_id:
					obj.parent_department_id=obj.department_id.parent_id.id
				else:
					obj.parent_department_id=obj.department_id.id
			else:
				obj.parent_department_id=None

	parent_department_id = fields.Many2one('hr.department',string='Хэлтэс',store=True, readonly=True, compute=_parent_department_id)
	parent_id = fields.Many2one('hr.evaluation','Parent',ondelete='cascade')
	line_line_ids = fields.One2many('hr.evaluation.line.line','line_parent_id','Үзүүлэлт')
	employee_id = fields.Many2one('hr.employee','Ажилтан',default=_default_employee)
	ident_id = fields.Char('Ажилтны код')
	company_id = fields.Many2one('res.company', string='Компани')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	department_id = fields.Many2one('hr.department','Хэлтэс')
	score = fields.Float('Авах оноо',store=True,  readonly=True, compute='_compute_amount')
	own_score = fields.Float(string='Өөрийн оноо',readonly=True, compute='_compute_amount')
	sum_amount = fields.Float('Нийт авсан оноо',store=True,  readonly=True, compute='_compute_amount')
	date = fields.Date(related='parent_id.date', string='Хугацаа', required=True)
	year = fields.Char(related='parent_id.year', string='Жил',  store=True)
	month = fields.Char(related='parent_id.month', string='Сар',store=True)
	day = fields.Char(related='parent_id.day', string='Өдөр', readonly=True)
	state = fields.Selection([('draft','Ноорог'),('sent','Үнэлгээ хийсэн')],'Төлөв',default='draft',tracking=True)
	give_ids = fields.Many2many('hr.employee', string='Үнэлэх ажилчид')
	description_employee = fields.Text('Тайлбар')
	count = fields.Char('Үнэлсэн ажилтан')
	score_own = fields.Boolean('Өөрийгөө үнэлэх эсэх')
	create_date = fields.Date('Үүсгэсэн огноо', readonly = True, default=fields.Date.context_today)
	employee_type = fields.Selection([
		('employee', 'Үндсэн ажилтан'),
		('student', 'Цагийн ажилтан'),
		('trainee', 'Туршилтын ажилтан'),
		('contractor', 'Гэрээт ажилтан'),
		('longleave', 'Урт хугацааны чөлөөтэй'),
		('maternity', 'Хүүхэд асрах чөлөөтэй'),
		('pregnant_leave', 'Жирэмсний амралт'),
		('resigned', 'Ажлаас гарсан'),
		('blacklist', 'Blacklist'),
		('freelance', 'Бусад'),
		('waiting', 'Хүлээгдэж буй'),
		], string='Ажилтны төлөв', default='employee',tracking=True,readonly=True
	   )


	@api.onchange('create_date')
	def onchange_create_date(self):
		if self.create_date:
			self.year =self.create_date.year
			self.month =self.create_date.month

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.job_id =self.employee_id.job_id.id
			self.work_location_id =self.employee_id.work_location_id.id
			# self.employee_type =self.employee_id.employee_type
			self.company_id =self.employee_id.company_id.id
			self.ident_id =self.employee_id.identification_id
			self.department_id =self.employee_id.department_id.id

	def set_count(self):
		count = len(self.line_line_ids.mapped('give_employee_ids').ids)
		line_line=  len(self.env['hr.evaluation.line.line'].search([('state','=','done'),('line_parent_id','=',self.id)]))
		if line_line:
			self.count = str(count) + '/' + str(line_line)
		else:
			self.count = str(count) + '/' + '0'



	def line_create(self):
		line_line_pool =  self.env['hr.evaluation.line.line']
		if self.line_line_ids:
			self.line_line_ids.unlink()
		for obj in self:
			query1 = """ SELECT
				conf_id as conf_id ,
				score as score,
				id as id
				FROM employee_configuration
				WHERE employee_id=%s"""%(obj.employee_id.id)
			self.env.cr.execute(query1)
			recs = self.env.cr.dictfetchall()

			for rec in recs:
				conf_pool = self.env['employee.configuration'].search([('id','=',rec['id'])],limit=1)
				e_ids = conf_pool.give_employee_ids.mapped('id')
				j_ids = conf_pool.give_job_ids.mapped('id')
				line_line_id = line_line_pool.create({
					'line_parent_id':obj.id,
					'conf_id':rec['conf_id'],
					'score':rec['score'],
					'get_score':rec['score'],
					'give_employee_ids':e_ids,
					'give_job_ids':j_ids,
				})
		return True

	def action_send(self):
		for line in self.line_line_ids:
			line.write({'state':'sent'})
		self.write({'state': 'sent'})

	def action_send_hr(self):
		for line in self.line_line_ids:
			line.write({'state':'sent'})
		self.write({'state': 'sent'})

	def action_draft(self):
		for line in self.line_line_ids:
			line.write({'state':'draft'})
		self.write({'state': 'draft'})

	def compute_zero(self):
		for line in self.line_line_ids:
			line.write({'get_score':0})

	def action_draft_hr(self):
		for line in self.line_line_ids:
			line.write({'state': 'draft'})
		self.write({'state': 'draft'})

	@api.depends('line_line_ids','line_line_ids.get_score','line_line_ids.score')
	def _compute_amount(self):
		for obj in self:
			sum_amount=0
			sum_score=0
			sum_own_score =0
			for l in obj.line_line_ids:
				sum_amount+= l.get_score
				sum_score+=l.score
				sum_own_score+=l.own_score
			obj.sum_amount = sum_amount
			obj.score = sum_score
			obj.own_score = sum_own_score



class HrEvaluationLineLine(models.Model):
	_name = "hr.evaluation.line.line"
	_descrition = 'Hr Evaluation Line Line'
	_inherit = ['mail.thread']

	line_parent_id = fields.Many2one('hr.evaluation.line','Parent',ondelete='cascade')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	conf_id = fields.Many2one('hr.performance','Үзүүлэлт')
	score = fields.Float('Авах оноо')
	get_score = fields.Float('Өгсөн оноо')
	state = fields.Selection([('draft','Үнэлээгүй'),('sent','Үнэлсэн')],'Төлөв',default='draft')
	description = fields.Char('Тайлбар')
	give_employee_ids = fields.Many2many('hr.employee', string='Үнэлэх ажилтан')
	give_job_ids = fields.Many2many('hr.job', string='Үнэлэх албан тушаал')
	own_score = fields.Float(string='Өөрийн үнэлгээ')

	@api.onchange('get_score')
	def onchange_get_score(self):
		if self.get_score:
			if self.env.uid in self.give_employee_ids.user_id.ids:
				emp_id = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
				self.history += ' /' +str(emp_id.name) + '-' +str(self.get_score) + '-' + str(datetime.now())
			else:
				self.get_score = 0
				raise UserError((u'Уучлаарай! та энэ үзүүлэлтийг үнэлэх эрх алга. Үнэлэх ажилтны жагсаалтаас өөрийн нэртэй үзүүлэлтийг үнэлнэ үү!'))

	history = fields.Text('Түүх', readonly=True,default='.')

class HrEvaluationLineStateUpdate(models.TransientModel):
	_name = 'hr.evaluation.line.state.update'
	_description = 'Hr Evaluation Line State Update'

	def action_to_sent(self):
		context=self._context
		if context['active_model'] == 'hr.evaluation.line':
			for cd_id in (context['active_ids']):
				leave = self.env['hr.evaluation.line'].search([('id', '=', cd_id)], limit=1)
				if leave.state in ('draft','done'):
					leave.action_send_hr()
				else:
					raise UserError('Сонгосон үнэлгээ Ноорог төлөвтэй биш байна.')


	def action_to_sent_hr(self):
		context=self._context
		if context['active_model'] == 'hr.evaluation.line':
			for cd_id in (context['active_ids']):
				leave = self.env['hr.evaluation.line'].search([('id', '=', cd_id)], limit=1)
				leave.write({'state': 'sent'})

	def action_done_hr(self):
		context=self._context
		if context['active_model'] == 'hr.evaluation.line':
			for cd_id in (context['active_ids']):
				leave = self.env['hr.evaluation.line'].search([('id', '=', cd_id)], limit=1)
				leave.write({'state': 'done'})


	def action_to_draft(self):
		context=self._context
		if context['active_model'] == 'hr.evaluation.line':
			for cd_id in (context['active_ids']):
				leave = self.env['hr.evaluation.line'].search([('id', '=', cd_id)], limit=1)
				leave.action_draft_hr()


# Үнэлгээ тохируулах
class HrEmployee(models.Model):
	_inherit = "hr.employee"

	conf_emp_ids = fields.One2many('employee.configuration','employee_id','Тохиргоо')
	is_evaluation=fields.Boolean('Үнэлгээ тохируулах эсэх')

class EmployeeConfiguration(models.Model):
	_name = "employee.configuration"
	_descrition = 'Employee Line'

	employee_id = fields.Many2one('hr.employee','Ажилтан')
	conf_id = fields.Many2one('hr.performance','Үзүүлэлт')
	score = fields.Float(related='conf_id.score',store=True, string='Авах оноо')
	give_employee_ids = fields.Many2many('hr.employee', string='Үнэлэх ажилтан')
	give_job_ids = fields.Many2many('hr.job',string='Үнэлэх албан тушаал')


class HrJob(models.Model):
	_inherit = "hr.job"

	is_evaluation=fields.Boolean('Үнэлгээ тохируулах эсэх')
	conf_job_ids = fields.One2many('job.configuration','job_id','Тохиргоо')


class JobConfiguration(models.Model):
	_name = "job.configuration"
	_descrition = 'Job Line'

	job_id = fields.Many2one('hr.job','Албан тушаал')
	conf_id = fields.Many2one('hr.performance','Үзүүлэлт')
	score = fields.Float(string='Авах оноо',related='conf_id.score',store=True)
	give_employee_ids = fields.Many2many('hr.employee', string='Үнэлэх ажилтан')
	give_job_ids = fields.Many2many('hr.job',string='Үнэлэх албан тушаал')
