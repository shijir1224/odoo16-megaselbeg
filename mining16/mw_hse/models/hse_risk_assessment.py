from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


	
class HseRiskAssessment(models.Model):
	_name ='hse.risk.assessment'
	_description = 'Risk assessment'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'datetime desc'
  
	# @api.depends('branch_id','datetime')
	# def _set_name(self):
	# 	for item in self:
	# 		if not item.name:
	# 			my_id = self.env['ir.model'].search([('model','=','hse.risk.assessment')] , limit=1)
	# 			conf_ids = self.env['hse.code.config'].search([('branch_id','=',item.branch_id.id),('model_id','=',my_id.id)], limit=1)
	# 			if conf_ids:
	# 				num_name = conf_ids.name
	# 				max_count = 0
	# 				self.env.cr.execute('SELECT id FROM hse_risk_assessment where branch_id = %s and EXTRACT(YEAR FROM date) = %s ',(item.branch_id.id, datetime.strptime(item.date, '%Y-%m-%d').year))
	# 				obj_ids = map(lambda x: x[0],self.env.cr.fetchall())
	# 				for item_sub in self.env['hse.risk.assessment'].browse(obj_ids):
	# 					s = item_sub.name
	# 					if s and int(s[len(num_name): len(s)]) > max_count:
	# 						max_count = int(s[len(num_name): len(s)])

	# 				item.name = num_name+str(max_count+1).zfill(4)

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.risk.assessment')
		return name

	name = fields.Char(string='Дугаар', readonly=True, default=_default_name)
	datetime = fields.Datetime(string='Огноо', required=True, states={'done':[('readonly',True)]}, default=fields.Date.context_today)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Хийгдсэн')], string='Төлөв', readonly=True, tracking=True, default='draft')
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', required=True, readonly=True, default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True, states={'done':[('readonly',True)]}, default=lambda self: self.env.user.branch_id
							 , domain="[('company_id','=',company_id)]"
							 )
	work_name = fields.Char(string='Гүйцэтгэх ажил', required=True)
	location_id = fields.Many2one('hse.location', string='Байршил', required=True, states={'done':[('readonly',True)]}, domain="[('branch_id','=',branch_id)]")
	location_do = fields.Char(string='Хаана хийх')
	work_approved_number = fields.Char(string='Ажлын зөвшөөрөл', required=True)
	work_approved_date = fields.Datetime(string='Зөвшөөрлийн хугацаа', required=True, states={'done':[('readonly',True)]}, default=fields.Date.context_today)
	tehnic_eseh = fields.Boolean('Техник, тоног төхөөрөмж хэрэгтэй эсэх', default=False)
	surgalt_eseh = fields.Selection([('1', 'Тийм'),('2', 'Үгүй')], default='1', string='Сургалт шаардлагатай эсэх')
	sertificat_eseh = fields.Selection([('1', 'Тийм'),('2', 'Үгүй')], default='1', string='Сертификат, үнэмлэх хэрэгтэй эсэх')
	danger_phone = fields.Char(string='Онцгой байдлын үед холбоо барих утас',)
	# occupational_safety_analysis_ids = fields.One2many('hse.occupational.safety.analysis', 'occupational_safety_analysis', string="workplace_inspection", states={'done':[('readonly',True)]})
	risk_assessment_table = fields.One2many('hse.risk.assessment.table', 'risk_assessment_id', 'Эрсдэлийн үнэлгээний хүснэгт')
	attachment_ids = fields.Many2many('ir.attachment', 'hse_risk_assessment_ir_attachments_rel','assessment_id', 'attachment_id', string='Эрсдэлийн үнэлгээний баталгаажуулсан хувилбар', readonly=True, states={'draft':[('readonly',False)]})
	hse_safety_analysis_ids = fields.One2many('hse.safety.analysis', 'hse_safety_analysis', string="hse_bolooch", states={'done':[('readonly',True)]})
	risk_probability = fields.Selection([
		('1', 'Бараг байнга'),
		('2', 'Элбэг'),
		('3', 'Боломжтой'),
		('4', 'Хааяа нэг'),
		('5', 'Ховор')],
	string='Магадлал', required=True, states={'done':[('readonly',True)]})
	risk_consequences = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар', required=True, states={'done':[('readonly',True)]})
	result_1 = fields.Char(string="Эрсдэлийн Зэрэглэл", readonly=True)
	result_2 = fields.Char(string="Эрсдэлийн Арга хэмжээ", readonly=True)
	risk_probability_result_3 = fields.Char(string="Магадлалын тайлбар", readonly=True)
	risk_probability_result_4 = fields.Char(string="Магадлалын боломж", readonly=True)
	risk_consequences_result_5 = fields.Char(string="Үр дагавар/Аюулгүй байдал, Эрүүл Ахуй/", readonly=True)
	risk_consequences_result_6 = fields.Char(string="Үр дагавар/Хохирол/", readonly=True)
	risk_consequences_result_7 = fields.Char(string="Үр дагавар/Байгаль орчин/", readonly=True)

	@api.onchange('risk_probability')
	def onchange_risk_probability(self):
		if self.risk_probability:
			risk_pro = self.env['hse.risk.probability'].sudo().search([('risk_probability','=',self.risk_probability)], limit=1)
			self.risk_probability_result_3 = risk_pro.risk_probability_about
			self.risk_probability_result_4 = risk_pro.risk_probability_opportunity

	@api.onchange('risk_consequences')
	def onchange_risk_consequences(self):
		if self.risk_consequences:
			risk_cons = self.env['hse.risk.probability'].sudo().search([('risk_consequences','=',self.risk_consequences)], limit=1)
			self.risk_consequences_result_5 = risk_cons.risk_consequences_hygiene
			self.risk_consequences_result_6 = risk_cons.risk_consequences_about		
			self.risk_consequences_result_7 = risk_cons.risk_consequences_nature		


	def action_risk_estimate(self):
		xox = self.env['hse.risk.probability'].sudo().search([('risk_probability','=',self.risk_probability),('risk_consequences','=',self.risk_consequences)], limit=1)
		self.result_1 = xox.prioraty
		self.result_2 = xox.risk_about


	def action_to_done(self):
		if not self.attachment_ids:
			raise UserError('Хавсралт файл заавал оруулж байж батлагдана!!!.')
		self.write({'state': 'done'})
	
	def action_to_draft(self):
		self.write({'state': 'draft'})

class HseRiskProbability(models.Model):
	_name ='hse.risk.probability'
	_description = 'Hse risk probability'

	name = fields.Char(string="Дугаар", required=True)
	prioraty = fields.Char(string="Зэрэглэл", required=True)
	risk_about = fields.Char(string="Арга хэмжээ", required=True)
	risk_probability_about = fields.Char(string="Магадлалын тайлбар", required=True)
	risk_probability_opportunity = fields.Char(string="Магадлалын боломж", required=True)
	risk_consequences_hygiene = fields.Char(string="Үр дагавар/Аюулгүй байдал, Эрүүл Ахуй/", required=True)
	risk_consequences_about = fields.Char(string="Үр дагавар/Хохирол/", required=True)
	risk_consequences_nature = fields.Char(string="Үр дагавар/Байгаль орчин/", required=True)
	risk_level = fields.Char(string="Түвшин", required=True)
	damaged_estimate = fields.Char(string="Хохирол үнэлгээ")

	risk_probability = fields.Selection([
		('1', 'Бараг байнга'),
		('2', 'Элбэг'),
		('3', 'Боломжтой'),
		('4', 'Хааяа нэг'),
		('5', 'Ховор')],
	string='Магадлал', required=True)
	risk_consequences = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар', required=True,)

class HseRiskAssessmentTable(models.Model):
	_name ='hse.risk.assessment.table'
	_description = 'Risk assessment table'

	risk_assessment_id = fields.Many2one('hse.risk.assessment','Assessment ID', required=True)
	step = fields.Char('Ажлын Алхам', required=True)
	danger = fields.Text('Аюул', required=True)
	initial_risk_level_ids = fields.Many2many('hse.risk.probability', 'hse_risk_probability_table_rel', 'risk_probability_id', 'risk_level_id', string="Анхны Эрсдэлийн Түвшин", required=True)
	control_measures = fields.Text('Хяналтын арга хэмжээ', required=True)
	method_used = fields.Selection([
		('delete','Устгах/Арилгах'),
		('substitution','Орлуулах'),
		('isolation','Тусгаарлах'),
		('engineering','Инженерчлэл'),
		('administration','Захиргаа'),
		('nbhh','НБХХ')], 
	string='Хэрэглэсэн арга', required=True)
	balance_risk_assessment_ids = fields.Many2many('hse.risk.probability', 'hse_risk_probability_rel', 'risk_probability_id', 'balance_risk_assessment_id', string="Үлдэгдэл Эрсдэл", required=True)
	employee_ids = fields.Many2many('hr.employee', 'hse_risk_assessment_table_employee_rel', 'employee_id', 'risk_assessment_id', string='Хариуцагч ажилтан')
	# risk_rating_id = fields.Many2one('hse.risk.rating','Буурсан зэрэг', required=True)
	# controls_to_reduce_risk = fields.Text('Эрсдэлийг бууруулах хяналтын хэмжээ', required=True)
	# reduced_risk_rating_id = fields.Many2one('hse.risk.rating','Буурсан зэрэг', required=True)
	# partner_ids = fields.Many2many('hse.partner', 'hse_risk_assessment_table_partner_rel', 'wo_is_id','partner_id', 'Хариуцагч харилцагч')



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

   
	hse_safety_analysis = fields.Many2one('hse.risk.assessment', string="hse Safety analysis", required=True)
	employee_id = fields.Many2one('hr.employee', string='Нэр')
	company = fields.Many2one('res.company', related='employee_id.company_id', string="Компани", readonly=True, )
	employee_position = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал', readonly=True)
	datetime = fields.Datetime('Огноо', default=fields.Date.context_today)