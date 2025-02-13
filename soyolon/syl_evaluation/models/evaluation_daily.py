

from odoo import api, fields, models, _


class HrEvaluationConfiguration(models.Model):
	_inherit = "hr.performance"
					
					

	name = fields.Char('Зорилго-Objectives',tracking=True)
	goal = fields.Char(string='Хүрэх үр дүн')
	desc = fields.Char('Ажлын гүйцэтгэлийн хэмжүүр KPI')
	score = fields.Float('Жигнэгдсэн хувь',tracking=True)
	department_id = fields.Many2one('hr.department','Хэлтэс')


class HrEvaluation(models.Model):
	_inherit = "hr.evaluation"


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
				WHERE hr.employee_type in ('employee','trainee','contractor')  and rc.id=%s %s """%(self.company_id.id,self.set_conditions())
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			for record in records:
				print('\n--recordhj_evaluatio--',record['hj_evaluation'])
				if record['hj_evaluation'] == True:
					line_id = line_pool.create({
						'parent_id':self.id,
						'ident_id':record['ident_id'],
						'employee_id':record['id'],
						'job_id':record['hj_id'],
						'department_id':record['hd_id'],
						'company_id':record['rc_id'],
						'work_location_id':record['hc_id'],
						'year':self.year,
						'month':self.month,
						'date':self.date,
					})
					if record['hr_evaluation'] == True:
						self.create_from_employee(line_id)
				


	def create_from_employee(self,line_id):
		line_line_pool =  self.env['hr.evaluation.line.line']
		recs_emp=  self.env['employee.configuration'].search([('employee_id','=',line_id.employee_id.id)])
		for rec in recs_emp:
			
			
			line_line_id = line_line_pool.create({
				'line_parent_id':line_id.id,
				'conf_id':rec.conf_id.id,
				'score':rec.score,
				'goal':rec.conf_id.goal,
				'desc':rec.conf_id.desc,
			})

class EmployeeConfiguration(models.Model):
	_inherit = "employee.configuration"

	department_id = fields.Many2one('hr.department','Хэлтэс',related='employee_id.department_id')
	
class HrEvaluationLine(models.Model):
	_inherit = "hr.evaluation.line"

	year = fields.Char(related=False, string='Жил',  store=True)
	month = fields.Char(related=False, string='Сар',store=True)
	month_s = fields.Integer(string='Сар')
	ident_id = fields.Char('Ажилтны код',related='employee_id.identification_id')
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Үнэлсэн'),('done','Зөвшөөрсөн')],'Төлөв',default='draft',tracking=True)

	@api.depends('line_line_ids','line_line_ids.get_score','line_line_ids.score')
	def _compute_amount(self):
		for obj in self:
			sum_amount=0
			sum_score=0
			sum_own_score =0
			len_line = len(obj.line_line_ids)
			get_score = sum(obj.line_line_ids.mapped('get_score'))
			own_score= sum(obj.line_line_ids.mapped('own_score'))
			score= sum(obj.line_line_ids.mapped('score'))
			if len_line>0 and get_score>0:
				sum_amount = get_score/len_line
			if len_line>0 and own_score>0:
				sum_own_score = own_score/len_line
			if len_line>0 and score>0:
				sum_score = score/len_line
		
			obj.sum_amount = sum_amount
			obj.score = sum_score
			obj.own_score = sum_own_score

	def action_confirm(self):
		self.write({'state': 'confirm'})

	def action_done(self):
		self.write({'state':'done'})
	


class HrEvaluationLineLine(models.Model):
	_inherit = "hr.evaluation.line.line"

	task = fields.Char('Хийгдэх ажлууд')
	conf_kpi_id = fields.Many2one('ev.kpi.conf','KPI')
	name = fields.Char('Зорилго')
	goal = fields.Char('Хүрэх үр дүн')
	desc = fields.Char('Ажлын гүйцэтгэлийн хэмжүүр KPI')
	get_desc = fields.Char('Удирдлагын тайлбар')
	score = fields.Float('Жигнэгдсэн хувь',tracking=True)
	file = fields.Many2many('ir.attachment', 'hr_ev_ir_attachment_rel','hr_ev_file_template_id', 'attach_id', string='Файл')
	state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Үнэлсэн'),('done','Зөвшөөрсөн')],'Төлөв',default='draft',tracking=True,related='line_parent_id.state',store=True)

	@api.onchange('get_score')
	def onchange_get_score(self):
		if self.get_score:
			if self.env.uid in self.give_employee_ids.user_id.ids:
				emp_id = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
	



	@api.onchange('conf_id')
	def onchange_conf_id(self):
		if self.conf_id:
			self.name =self.conf_id.name
			self.goal =self.conf_id.goal
			self.desc =self.conf_id.desc
			self.score =self.conf_id.score