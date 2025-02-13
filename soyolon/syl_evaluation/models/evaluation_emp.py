from odoo import fields, models,api, _
from odoo.exceptions import UserError


class HrEvaluationEmp(models.Model):
	_name = "hr.evaluation.emp"
	_descrition = 'Hr Evaluation Emp'
	_inherit = ['mail.thread']


	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(HrEvaluationEmp, self).unlink()


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

	line_line_ids = fields.One2many('hr.evaluation.emp.line','line_parent_id','Үзүүлэлт')
	employee_id = fields.Many2one('hr.employee','Ажилтан',default=_default_employee)
	ident_id = fields.Char('Ажилтны код',related='employee_id.identification_id')
	
	company_id = fields.Many2one('res.company', string='Компани')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	department_id = fields.Many2one('hr.department','Хэлтэс')
	own_score = fields.Float(string='Өөрийн оноо',readonly=True, compute='_compute_amount', digits=(2, 0))
	sum_amount = fields.Float('Удирдлагын оноо',store=True,  readonly=True, compute='_compute_amount', digits=(2, 0))
	year = fields.Char(string='Жил',  store=True)
	month = fields.Integer(string='Сар',store=True)
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Үнэлсэн'),('done','Зөвшөөрсөн')],'Төлөв',default='draft',tracking=True)
	description_employee = fields.Text('Тайлбар')
	create_date = fields.Date('Үүсгэсэн огноо', readonly = True, default=fields.Date.context_today)
	data = fields.Binary('Эксел файл')
	num_employee_id =  fields.Many2one('hr.employee', 'Удирлага')

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.job_id =self.employee_id.job_id.id
			self.work_location_id =self.employee_id.work_location_id.id
			self.company_id =self.employee_id.company_id.id
			self.ident_id =self.employee_id.identification_id
			self.department_id =self.employee_id.department_id.id

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
		self.write({'state': 'sent'})

	def action_confirm(self):
		self.write({'state': 'confirm'})

	def action_done(self):
		self.write({'state':'done'})

	def action_draft(self):
		self.write({'state': 'draft'})

	def compute_zero(self):
		for line in self.line_line_ids:
			line.write({'get_score':0})

	def action_draft_hr(self):
		self.write({'state': 'draft'})

	@api.depends('line_line_ids','line_line_ids.get_score','line_line_ids.own_score')
	def _compute_amount(self):
		for obj in self:
			len_line = len(obj.line_line_ids)
			get_score = sum(obj.line_line_ids.mapped('get_score'))
			own_score= sum(obj.line_line_ids.mapped('own_score'))
			avj_get=0
			avj_own=0
			if len_line>0 and get_score>0:
				avj_get = get_score/len_line
			if len_line>0 and own_score>0:
				avj_own= own_score/len_line
			obj.sum_amount = avj_get
			obj.own_score = avj_own



class HrEvaluationEmpLine(models.Model):
	_name = "hr.evaluation.emp.line"
	_descrition = 'Hr Evaluation Emp Line'
	_inherit = ['mail.thread']

	line_parent_id = fields.Many2one('hr.evaluation.emp','Parent',ondelete='cascade')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	conf_kpi_id = fields.Many2one('ev.kpi.conf','KPI')
	task = fields.Char('Хийгдэх ажлууд')
	get_score = fields.Float('Удирдлагын үнэлгээ')
	get_description = fields.Char('Удирдлагын тайлбар')
	description = fields.Char('Өөрийн тайлбар')
	own_score = fields.Float(string='Өөрийн үнэлгээ')
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Үнэлсэн'),('done','Зөвшөөрсөн')],'Төлөв',default='draft',tracking=True,related='line_parent_id.state',store=True)
	file = fields.Many2many('ir.attachment', 'hr_emp_ev_ir_attachment_rel','hr_emp_ev_file_template_id', 'attach_id', string='Файл')


	