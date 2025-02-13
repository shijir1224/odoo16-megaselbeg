
from odoo import fields, models, _

month=[('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
		('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
		('90','10 сар'), ('91','11 сар'), ('92','12 сар')]

class EvKPIConf(models.Model):
	_name = "ev.kpi.conf"
	_descrition = 'Ev Kpi Conf'
	_inherit = ['mail.thread']


	name = fields.Char(string='KPI')
	department_id = fields.Many2one('hr.department',string='Хэлтэс')
  

class EvObjectiveConf(models.Model):
	_name = "ev.objective.conf"
	_descrition = 'Ev Objective Conf'
	_inherit = ['mail.thread']


	name = fields.Char(string='Зорилго')
	goal = fields.Char(string='Хүрэх үр дүн')
	descrition = fields.Char(string='Тайлбар')
	department_id = fields.Many2one('hr.department',string='Хэлтэс')
	pillar_goal = fields.Selection([('goal1','Хүртэх өгөөж'),('goal2','Хамт(даа)лаг'),('goal3','Хүнлэг зарчим ESG')],string='ЗХ тулгуур зорилго')


class HrEvaluationYearPlan(models.Model):
	_name = "hr.evaluation.year.plan"
	_descrition = 'Hr Evaluation Plan'
	_inherit = ['mail.thread']


	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	
	employee_id = fields.Many2one('hr.employee','Боловсруулсан',default=_default_employee)
	n_employee_id = fields.Many2one('hr.employee','Хянасан')
	name = fields.Char(string='Нэр')
	year = fields.Char(string='Жил')
	department_id = fields.Many2one('hr.department',string='Хэлтэс')
	company_id = fields.Many2one('res.company',default=lambda self: self.env.user.company_id,string='Компани')
	state = fields.Selection([('draft','Ноорог'),('sent','Боловсруулсан'),('done','Хянасан')],default='draft',string='Төлөв')
	sprint = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4')],string='Улирал')
	line_ids = fields.One2many('hr.evaluation.year.plan.line','parent_id',string='')
	e = fields.Many2one('hr.department',string='Хэлтэс')

	def action_send(self):
		self.write({'state':'sent'})

	def action_done(self):
		self.write({'state':'done'})

	def action_draft(self):
		self.write({'state':'draft'})


class HrEvaluationYearPlanLine(models.Model):
	_name = "hr.evaluation.year.plan.line"
	_descrition = 'Hr Evaluation Year Plan Line'

	pillar_goal = fields.Selection([('goal1','Хүртэх өгөөж'),('goal2','Хамт(даа)лаг'),('goal3','Хүнлэг зарчим ESG')],string='ЗХ тулгуур зорилго')
	ev_objective_id = fields.Many2one('ev.objective.conf',string='Стратеги зорилго', domain="[('department_id','=', department_id)]")
	goal = fields.Char(string='Хүрэх үр дүн',related='ev_objective_id.goal',store=True)
	descrition = fields.Char(string='Тайлбар',related='ev_objective_id.descrition',store=True)
	parent_id = fields.Many2one('hr.evaluation.year.plan',string='Parent')
	line_line_ids = fields.One2many('hr.evaluation.year.plan.line.line','parent_id',string='')
	department_id = fields.Many2one('hr.department',string='Хэлтэс',related='parent_id.department_id',store=True)
	year = fields.Char(string='Жил',related='parent_id.year')
	data = fields.Binary('Эксел файл')


class HrEvaluationYearPlanLineLineLine(models.Model):
	_name = "hr.evaluation.year.plan.line.line"
	_descrition = 'Hr Evaluation Year Plan Line Line'


	conf_id = fields.Many2one('hr.performance',string='KPI')
	conf_kpi_id = fields.Many2one('ev.kpi.conf',string='KPI')
	task = fields.Char('Хийгдэх ажлууд')
	month=fields.Integer('Сар')
	department_id = fields.Many2one('hr.department',string='Хэлтэс',related='parent_id.department_id',store=True)

	r_employee_ids = fields.Many2many('hr.employee','hr_temp_year_rel','hr_temp_year_id', 'employee_id',string= 'R: хянах')
	a_employee_ids = fields.Many2many('hr.employee','hr_aemp_year_rel','hr_aemp_year_id', 'employee_id',string= 'A: батлах, шийдвэрлэх')
	t_employee_ids = fields.Many2many('hr.employee','hr_temp_year_rel','hr_temp_year_id', 'employee_id',string= 'T: гүйцэтгэх, боловсруулах')
	ts_employee_ids = fields.Many2many('hr.employee','hr_ts_year_rel','hr_ts_year_id', 'employee_id',string= 'T: гүйцэтгэх, боловсруулах')
	s_employee_ids = fields.Many2many('hr.employee','hr_semp_year_rel','hr_semp_year_id', 'employee_id',string= 'S: дэмжих, зөвлөлдөх')
	i_employee_ids = fields.Many2many('hr.employee','hr_iemp_year_rel','hr_iemp_year_id', 'employee_id',string= 'I: мэдээлэлтэй байх')


	r_employee_id = fields.Many2one('hr.employee','R: хянах')
	a_employee_id = fields.Many2one('hr.employee','A: батлах, шийдвэрлэх')
	t_employee_id = fields.Many2one('hr.employee','T: гүйцэтгэх, боловсруулах')
	s_employee_id = fields.Many2one('hr.employee','S: дэмжих, зөвлөлдөх')
	i_employee_id = fields.Many2one('hr.employee','I: мэдээлэлтэй байх')


	parent_id = fields.Many2one('hr.evaluation.year.plan.line',string='Parent')
