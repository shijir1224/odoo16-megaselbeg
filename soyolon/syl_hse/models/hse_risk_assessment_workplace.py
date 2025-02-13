
from odoo import api, fields, models, _


class hseWorkplaceInspection(models.Model):
	_inherit = 'hse.risk.assessment.workplace'

	person_ids = fields.Many2many('danger.damage', 'danger_person_rel', 'person_id', string='ХҮНД', readonly=True, states={'draft': [('readonly', False)]})
	equipment_ids = fields.Many2many('danger.damage', 'danger_equipment_rel', 'equipment_id', string='ТОНОГ ТӨХӨӨРӨМЖИНД', readonly=True, states={'draft': [('readonly', False)]})
	production_ids = fields.Many2many('danger.damage', 'danger_production_rel', 'production_id', string='ҮЙЛДВЭРЛЭЛД', readonly=True, states={'draft': [('readonly', False)]})
	env_ids = fields.Many2many('danger.damage', 'danger_env_rel', 'env_id', string='БАЙГАЛЬ ОРЧИНД', readonly=True, states={'draft': [('readonly', False)]})

	danger_recognize_ids = fields.One2many('danger.recognize', 'ass_workplace_id', string='=Аюулыг таних')
	danger_control_ids = fields.One2many('danger.control', 'ass_workplace_id', string='Аюулыг ханилт')
	risk_assessment_ids = fields.One2many('risk.assessment', 'ass_workplace_id', string='Эрсдэлийн үнэлгээ')
	risk_plan_ids = fields.One2many('risk.plan', 'ass_workplace_id', string='Эрсдэл бууруулах төлөвлөгөө')

	risk_probability = fields.Selection([
		('1', 'Бараг байнга/Өдөр тутам/'),
		('2', 'Элбэг(7 хоногт 1 удаа)'),
		('3', 'Боломжтой(Сард 1 удаа)'),
		('4', 'Хааяа нэг(Жилд 1 удаа)'),
		('5', 'Ховор(10 жилд 1 удаа)')],
	string='Магадлал давтамж', required=False)

	risk_consequences_1 = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар', required=False,)

	risk_consequences = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар 2', required=False,)

	category_id = fields.Selection([
		('person','Хүмүүст'),
		('nature','Байгаль орчинд'),
		('owner','Өмчид')],
	string="Ангилал", required=False)

	def onchange_category_id(self):
		pass

	def onchange_risk_consequences(self):
		pass

	def onchange_risk_matrix(self):
		pass


class DangerDamage(models.Model):
	_name = 'danger.damage'
	_description = 'Danger Damage'

	name = fields.Char(string='Нэр', required=True)


class DangerRecognize(models.Model):
	_name = 'danger.recognize'
	_description = 'Danger Recognize'

	ass_workplace_id = fields.Many2one('hse.risk.assessment.workplace', string='Parent ID')
	activity = fields.Char(string='Үйл ажиллагаа')
	pot_danger = fields.Char(string='Болзошгүй аюул')
	danger_location = fields.Char(string='Аюулын байршил')
	reason = fields.Char(string='Шалтгаан')
	acc_result = fields.Char(string='Ослын үр дүн')
	

class DangerControl(models.Model):
	_name = 'danger.control'
	_description = 'Danger Control'

	ass_workplace_id = fields.Many2one('hse.risk.assessment.workplace', string='Parent ID')
	exist_control = fields.Char(string='Одоо байгаа хяналт')
	control_branch = fields.Char(string='Хяналтыг тогтоож буй нэгж, салбар')


class RiskAssessment(models.Model):
	_name = 'risk.assessment'
	_description = 'Risk Assessment'

	ass_workplace_id = fields.Many2one('hse.risk.assessment.workplace', string='Parent ID')
	damage = fields.Selection([
		('heavy','Хүнд'),
		('med','Дунд'),
		('light','Хөнгөн')
	], string='Хохирол', default=False)
	probability = fields.Selection([
		('high','Өндөр'),
		('med','Дунд'),
		('low','Бага')
	], string='Магадлал')
	risk_degree = fields.Char(string='Эрсдэлийн зэрэг', readonly=True)
	cost = fields.Char(string='Болзошгүй зардал')


	@api.onchange('damage','probability')
	def onchange_risk_degree(self):
		if self.damage or self.probability:
			obj = self.env['risk.assessment.config'].sudo().search([('damage','=',self.damage),('probability','=',self.probability)], limit=1)
			self.risk_degree = obj.risk_degree


class RiskPlan(models.Model):
	_name = 'risk.plan'
	_description = 'Risk Plan'

	ass_workplace_id = fields.Many2one('hse.risk.assessment.workplace', string='Parent ID')
	action_taken = fields.Char(string='Авах арга хэмжээ')
	who = fields.Char(string='Хэн?')
	when = fields.Char(string='Хэзээ?')
	damage = fields.Selection([
		('heavy','Хүнд'),
		('med','Дунд'),
		('light','Хөнгөн')
	], string='Хохирол /Арга хэмжээ авсны дараа/', default=False)
	probability = fields.Selection([
		('high','Өндөр'),
		('med','Дунд'),
		('low','Бага'),
	], string='Магадлал /Арга хэмжээ авсны дараа/', default=False)
	risk_degree = fields.Char(string='Эрсдэлийн зэрэг /Арга хэмжээ авсны дараа/', readonly=True)

	@api.onchange('damage','probability')
	def onchange_risk_degree(self):
		if self.damage or self.probability:
			obj = self.env['risk.assessment.config'].sudo().search([('damage','=',self.damage),('probability','=',self.probability)], limit=1)
			self.risk_degree = obj.risk_degree
	

class RiskAssessmentConfig(models.Model):
	_name = 'risk.assessment.config'
	_description = 'Risk assessment config'
	_rec_name = 'risk_degree'

	damage = fields.Selection([
		('heavy','Хүнд'),
		('med','Дунд'),
		('light','Хөнгөн')
	], string="Хохирол", required=True)

	probability = fields.Selection([
		('high','Өндөр'),
		('med','Дунд'),
		('low','Бага'),
	], string='Магадлал', required=True,)

	risk_degree = fields.Char(string="Эрсдэлийн зэрэг", required=True)
