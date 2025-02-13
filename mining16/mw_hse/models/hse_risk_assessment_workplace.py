from odoo import  api, fields, models, _
from datetime import datetime, timedelta


class HseRiskAsseseementWorkplace(models.Model):
	_name ='hse.risk.assessment.workplace'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Risk assessment workplace'
	_order = 'name desc'

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.risk.assessment.workplace')

	name = fields.Char(string="Эрсдэлийн үнэлгээний дугаар", default=_default_name, copy=False, readonly=True)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Хийгдсэн')], string='Төлөв', readonly=True, tracking=True, default='draft')
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string="Компани", required=True)
	department_id = fields.Many2one('hr.department', string="Хэлтсийн нэр", required=True)
	branch_id = fields.Many2one('res.branch', string="Салбар", required=True, default=lambda self: self.env.user.branch_id, domain="[('company_id','=',company_id)]")
	workplace_type = fields.Many2one('hse.risk.workplace.type', string="Ажлын байрны нэр төрөл")
	risk_estimate_scope = fields.Selection([('workplace','Ажлын байр')], string="Эрсдэлийн үнэлгээний цар хүрээ", default="workplace")
	create_date = fields.Datetime(string="Зохион байгуулсан огноо", default=fields.Date.context_today)
	check_user_id = fields.Many2one("hr.employee", string="Хянасан ажилтны нэр", required=True)
	check_date = fields.Datetime(string="Хянасан огноо", default=fields.Date.context_today)
	result_1 = fields.Char(string="Хохирол үнэлгээ", readonly=True)
	result_2 = fields.Char(string="Түвшин", readonly=True)
	result_3 = fields.Char(string="Зэрэглэл", readonly=True)
	result_4 = fields.Char(string="Эрсдэлийн зэрэглэл", readonly=True)
	risk_probability = fields.Selection([
		('1', 'Бараг байнга/Өдөр тутам/'),
		('2', 'Элбэг(7 хоногт 1 удаа)'),
		('3', 'Боломжтой(Сард 1 удаа)'),
		('4', 'Хааяа нэг(Жилд 1 удаа)'),
		('5', 'Ховор(10 жилд 1 удаа)')],
	string='Магадлал давтамж', required=True)
	risk_consequences_1 = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар', required=True,)
	risk_consequences = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар 2', required=True,)
	category_id = fields.Selection([
		('person','Хүмүүст'),
		('nature','Байгаль орчинд'),
		('owner','Өмчид')],
	string="Ангилал", required=True)
	hse_risk_assessment_workplace_ids = fields.One2many('hse.risk.assessment.workplace.table', 'risk_assessment_workplace_id', string="Эрсдэлийн үнэлгээ", states={'done':[('readonly',True)]})
	hse_risk_estiamte_workplace_ids = fields.One2many('hse.risk.estimate.workplace.analysis', 'hse_risk_estimate_workplace_analysis_id', string="risk estimate workplace", states={'done':[('readonly',True)]})

	leader_employee_id = fields.Many2one('hr.employee', string="Эрсдэлийн үнэлгээ хийсэн багийн ахлагч")
	leader_employee_pos = fields.Many2one('hr.job', related='leader_employee_id.job_id', string='Албан тушаал', readonly=True)
	leader_employee_date = fields.Datetime(string='Огноо', copy=True)
	additional_explanation = fields.Text(string="Нэмэлт тайлбар", states={'done':[('readonly',True)]})
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт материал', states={'done':[('readonly',True)]})

	@api.onchange('category_id','risk_consequences')
	def onchange_category_id(self):
		if self.category_id or self.risk_consequences:
			categ_obj = self.env['hse.risk.workplace.config'].sudo().search([('category_id','=',self.category_id),('risk_consequences','=',self.risk_consequences)], limit=1)
			self.result_1 = categ_obj.tailbar

	@api.onchange('risk_consequences')
	def onchange_risk_consequences(self):
		if self.risk_consequences:
			risk_cons = self.env['hse.risk.workplace.config'].sudo().search([('risk_consequences','=',self.risk_consequences)], limit=1)
			self.result_2 = risk_cons.level_about	
			self.result_3 = risk_cons.zereglel

	@api.onchange('risk_consequences_1', 'risk_probability')
	def onchange_risk_matrix(self):
		if self.risk_consequences_1 or self.risk_probability:
			risk_pro = self.env['hse.risk.probability'].sudo().search([('risk_consequences','=',self.risk_consequences_1),('risk_probability','=',self.risk_probability)], limit=1)
			self.result_4 = risk_pro.name	


	def action_to_done(self):
		obj = self
		self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})


class HseRiskAssessmentTable(models.Model):
	_name ='hse.risk.assessment.workplace.table'
	_description = 'Risk assessment workplace table'
	# _order = 'step asc'

	risk_assessment_workplace_id = fields.Many2one('hse.risk.assessment.workplace','Workplace ID', required=True)
	danger_type = fields.Char(string="Аюулын ангилал")
	danger = fields.Text('Аюул', required=True)
	risk = fields.Text('Эрсдэл', required=True)
	rnow_control = fields.Char('Одоогийн хяналт', required=True)
	risk_probability = fields.Selection([
		('1', 'Бараг байнга/Өдөр тутам/'),
		('2', 'Элбэг(7 хоногт 1 удаа)'),
		('3', 'Боломжтой(Сард 1 удаа)'),
		('4', 'Хааяа нэг(Жилд 1 удаа)'),
		('5', 'Ховор(10 жилд 1 удаа)')],
	string="Одоогийн магадлал", required=True)
	risk_consequences = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Одоогийн Үр дагавар', required=True,)
	rnow_risk_level = fields.Char(string="Одоогийн эрсдлийн түвшин", readonly=True)
	corr_action = fields.Text(string="Хариу арга хэмжээ", required=True)
	risk_probability_decrease = fields.Selection([
		('1', 'Бараг байнга/Өдөр тутам/'),
		('2', 'Элбэг(7 хоногт 1 удаа)'),
		('3', 'Боломжтой(Сард 1 удаа)'),
		('4', 'Хааяа нэг(Жилд 1 удаа)'),
		('5', 'Ховор(10 жилд 1 удаа)')],
	string="Буурах магадлал", required=True)
	risk_consequences_decrease = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Буурах үр дагавар', required=True,)
	rnow_risk_level_decrease = fields.Char(string="Буурах эрсдлийн түвшин", readonly=True)
	employee_ids = fields.Many2many('hr.employee', 'hse_risk_assessment_workplace_table_employee_rel', 'wo_is_id','employee_id', 'Хариуцагч ажилтан')

	@api.onchange('risk_consequences', 'risk_probability')
	def onchange_risk_matrix(self):
		if self.risk_consequences or self.risk_probability:
			risk_1 = self.env['hse.risk.probability'].sudo().search([('risk_consequences','=',self.risk_consequences),('risk_probability','=',self.risk_probability)], limit=1)
			self.rnow_risk_level = risk_1.name

	@api.onchange('risk_consequences_decrease', 'risk_probability_decrease')
	def onchange_risk_matrix_2(self):
		if self.risk_consequences_decrease or self.risk_probability_decrease:
			risk_2 = self.env['hse.risk.probability'].sudo().search([('risk_consequences','=',self.risk_consequences_decrease),('risk_probability','=',self.risk_probability_decrease)], limit=1)
			self.rnow_risk_level_decrease = risk_2.name	

class hseriskestimateworkplaceanalysis(models.Model):
	_name ='hse.risk.estimate.workplace.analysis'
	_description = 'hse risk estimate workplace analysis'
   
	hse_risk_estimate_workplace_analysis_id = fields.Many2one('hse.risk.assessment.workplace', string="hse risk estimate", required=True)
	employee_id = fields.Many2one('hr.employee', string='Багийн гишүүд')
	employee_position = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал', readonly=True)
	datetime = fields.Datetime(string='Огноо', copy=True)
		

class hsesafetyanalysis(models.Model):
	_name ='hse.safety.analysis'
	_description = 'hse safety analysis'
	# _order = 'step asc'

   
	hse_safety_analysis = fields.Many2one('hse.risk.assessment', string="hse Safety analysis", required=True)
	employee_id = fields.Many2one('hr.employee', string='Нэр')
	company = fields.Many2one('res.company', related='employee_id.company_id', string="Компани", readonly=True, )
	employee_position = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал', readonly=True)
	datetime = fields.Datetime('Огноо', default=fields.Date.context_today)

class HseRiskWorkplaceType(models.Model):
	_name ='hse.risk.workplace.type'
	_description = 'Risk workplace type'

	code = fields.Char(string="Код")
	name = fields.Char(string="Ажлын байрны нэр", required=True)