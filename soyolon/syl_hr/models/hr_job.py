# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class HrJob(models.Model):
	_inherit = 'hr.job'


	def write(self, values):
		res = super(HrJob,self).write(values)
		no1 = 0
		for line in self.line_ids:
			no1 +=1
			line.sequence = no1
		return res

	needs = fields.Text(string='Үндсэн ба тусгай шаардлага')
	role = fields.Text(string='Үндсэн чиг үүрэг')
	direct_dep = fields.Many2one('hr.job',string='Шууд харьяалагдах')
	direct_job = fields.Many2one('hr.job',string='Шууд харьяалах')
	direct_emp = fields.Many2one('hr.job',string='Орлон гүйцэтгэх')
	ability = fields.Text(string='Мэргэжлийн ур чадвар')
	base_skills = fields.Text(string='Суурь ур чадварууд')
	# equipment = fields.Text(string='Ажлын байранд ашиглах тоног төхөөрөмж, багаж, хэрэгсэл')
	goal = fields.Text(string='Зорилго')
	date = fields.Date(string='Огноо')
	education_new = fields.Char( string= 'Боловсрол')
	exprience_new = fields.Char(string="Туршлага")
	certificate = fields.Char(string="Мэргэжлийн сертификат ")
	knowledge = fields.Char(string="Мэдлэг")
	behaviour = fields.Char(string="Зан төлөв")
	# emp_number = fields.Float(string="Хариуцах ажилтны тоо")
	finance = fields.Char(string="Санхүү")
	budget = fields.Float(string="Төсөв")
	line_ids = fields.One2many('hr.job.line', 'job_id', 'АБ чиг үүрэг')
	work_condition = fields.Selection([('in', 'Хэвийн'), ('not', 'Хэвийн бус хүнд'), (
		'not2', 'Хэвийн бус хортой')], 'Хөдөлмөрийн нөхцөл', tracking=True)
	location = fields.Selection([('Оффис', 'Оффис'), ('Уурхай', 'Уурхай')], 'Байршил', tracking=True)
	work_condition_ch = fields.Char('Хөдөлмөрийн нөхцөл',compute='_compute_work_condition',store=True)

	@api.depends('work_condition')
	def _compute_work_condition(self):
		for item in self:
			work_condition_ch=''
			if item.work_condition=='in':
				work_condition_ch = 'Хэвийн'
			elif item.work_condition=='not':
				work_condition_ch = 'Хэвийн бус хүнд'
			elif item.work_condition=='not2':
				work_condition_ch = 'Хэвийн бус хортой'
			item.work_condition_ch = work_condition_ch

	@api.depends('no_of_recruitment', 'employee_ids.job_id', 'employee_ids.active')
	def _compute_employees(self):
		employee_data = self.env['hr.employee']._read_group([('job_id', 'in', self.ids),('employee_type', 'in', ('employee','trainee','contractor'))], ['job_id'], ['job_id'])
		result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
		for job in self:
			job.no_of_employee = result.get(job.id, 0)
			job.expected_employees = result.get(job.id, 0) + job.no_of_recruitment


class HrJobLine(models.Model):
	_name = 'hr.job.line'

	abt_id = fields.Many2one('hr.job.abt','АБ чиг үүрэг')
	job_id = fields.Many2one('hr.job','АБ чиг үүрэг')
	sequence = fields.Integer('Дугаарлалт')



class HrJobAbt(models.Model):
	_name = 'hr.job.abt'

	name = fields.Char('Нэр')
	