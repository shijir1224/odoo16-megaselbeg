from odoo import api, fields, models, _
from datetime import datetime, timedelta


class HseLocation(models.Model):
	_name ='hse.location'
	_description = 'Location'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'name asc'

	def name_get(self):
		res = []
		for item in self:
			name = item.name or ''
			if item.name:
				name = ('%s')%(item.name)
			res.append((item.id, name))
		return res
   
	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('branch_id', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()
	

	name = fields.Char('Нэр', required=True,)
	branch_id = fields.Many2one('res.branch', 'Салбар', required=True)
	responsible_id = fields.Many2one('hr.employee','Хариуцагч', domain=[('employee_type', 'in', ['employee','student'])])
	department_id = fields.Many2one('hr.department','Хэлтэс')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
class HsePartner(models.Model):
	_name ='hse.partner'
	_description = 'Partner'
	_order = 'name asc'

	name = fields.Char('Нэр', required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch','Салбар', required=True)
	email = fields.Char('Майл', required=True)

class HseHazardCategory(models.Model):
	_name ='hse.hazard.category'
	_description = 'Hazard category'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	name = fields.Char('Аюулын ангилал', required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

class HseSalaryConfig(models.Model):
	_name = 'hse.salary.config'
	_description = 'Hse Salary Config'

	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	conflict_type = fields.Many2one(
		'hse.discipline.type', string='Зөрчлийн төрөл')
	emp_type = fields.Selection([
		('emp', 'Ажилтан'),
		('repair', 'Засвар'),
		('Ope', 'Оператор'),
		('ITA', 'ИТА'),
	], string="Ажилтны ангилал",)
	point = fields.Char(string='Оноо')


class HseNoticeActionConfig(models.Model):
	_name = 'hse.notice.action.config'
	_description = 'Hse Notice Action Config'

	parent_act_id = fields.Many2one('preliminary.notice', string='Pre notice id', ondelete='cascade')
	name = fields.Char(string='Арга хэмжээ')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)

class HseInjuryEnvironment(models.Model):
	_name = 'hse.injury.environment'
	_description = 'Injury environment'

	parent_id = fields.Many2one('hse.injury.entry', string="Injury report", ondelete='cascade')
	name = fields.Char('Нэр', required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'


class HseInjuryEquipmentMaterials(models.Model):
	_name = 'hse.injury.equipment.materials'
	_description = 'Injury equipment materials'

	parent_id_1 = fields.Many2one('hse.injury.entry', string="Injury report", ondelete='cascade')
	name = fields.Char('Нэр', required=True, )
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'


class HseInjuryOperatingSystem(models.Model):
	_name = 'hse.injury.operating.system'
	_description = 'Injury operating system'

	parent_id_2 = fields.Many2one(
		'hse.injury.entry', string="Injury report", ondelete='cascade')
	name = fields.Char('Нэр', required=True, )
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'


class HseInjuryPerson(models.Model):
	_name = 'hse.injury.person'
	_description = 'Injury person'

	parent_id_3 = fields.Many2one(
		'hse.injury.entry', string="Injury report", ondelete='cascade')
	name = fields.Char('Нэр', required=True, )
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'


class HseInjuryNonStandardAction(models.Model):
	_name = 'hse.injury.non.standard'
	_description = 'Injury non standard action'

	parent_id_4 = fields.Many2one(
		'hse.injury.entry', string="Injury report", ondelete='cascade')
	name = fields.Char('Нэр', required=True, )
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'


class HseInjurynonStandardConditions(models.Model):
	_name = 'hse.injury.non.standard.conditions'
	_description = 'Injury non standard conditions'

	parent_id_5s = fields.Many2one(
		'hse.injury.entry', string="Injury report", ondelete='cascade')
	name = fields.Char('Нэр', required=True, )
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'


class HseEmployeeKpi(models.Model):
	_name = 'hse.employee.kpi'
	_description = 'Hse Employee Kpi'

	employee_hse_point = fields.Float(string='Ажилтны хувь')
	emp_type = fields.Selection([
		('emp', 'Ажилтан'),
		('repair', 'Засвар'),
		('Ope', 'Оператор'),
		('ITA', 'ИТА'),
	], string="Ажилтны ангилал",)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

class hse_discipline_history(models.Model):
	_name = 'hse.discipline.history'
	_description = u'Урсгалын түүх'
	_order = 'date desc'

	hse_id = fields.Many2one('hse.discipline.action', 'HSE', ondelete='cascade', index=True)
	user_id = fields.Many2one('res.users', 'Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now, index=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв', index=True)
	spend_time = fields.Float(string='Зарцуулсан цаг', compute='_compute_spend_time', store=True, readonly=True, digits=(16, 2))
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

	@api.depends('date', 'hse_id')
	def _compute_spend_time(self):
		for obj in self:
			domains = []
			if obj.hse_id:
				domains = [('hse_id', '=', obj.hse_id.id), ('id', '!=', obj.id)]
			if domains and isinstance(obj.id, int):
				ll = self.env['hse.discipline.history'].search(
					domains, order='date desc', limit=1)
				if ll:
					secs = (obj.date-ll.date).total_seconds()
					obj.spend_time = secs/3600
				else:
					obj.spend_time = 0
			else:
				obj.spend_time = 0

	def create_history(self, flow_line_id, hse_id):
		self.env['hse.discipline.history'].create({
            'hse_id': hse_id.id,
            'user_id': self.env.user.id,
            'date': datetime.now(),
			'flow_line_id': flow_line_id.id
        })


class DisciplineHistory(models.Model):
	_name = 'discipline.categ'
	_description = u'Зөрчлийн ангилал'

	hse_discipline_id = fields.Many2one('hse.discipline.action', 'HSE', ondelete='cascade', index=True)
	name = fields.Char(string='Зөрчлийн ангилалын нэр')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)


class hse_influencing_factor(models.Model):
	_name = 'hse.influencing.factor'
	_description = 'hse influencing factor'

	name = fields.Char(string='Нэр',)

class email_send_user(models.Model):
	_name = 'email.send.users'
	_description = 'Email Send Users'

	name = fields.Char(related='partner_id.email', string="Email", required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	partner_id = fields.Many2one('res.partner', string='Харилцагч', required=True)
	is_first = fields.Boolean('Анхныхаар харуулах', default=False)

class HseAccidentType(models.Model):
	_name ='hse.accident.type'
	_description = 'Types of accidents'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'name asc'
   
	name = fields.Char('Ослын төрөл', required=True, translate=True)
	value = fields.Char('Утга', required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
class HseDisciplineType(models.Model):
	_name ='hse.discipline.type'
	_description = 'Discipline Type'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'number' 
   
	name = fields.Text('Нэр', required=True)
	number = fields.Char('Дугаар')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	
	_sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')]

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
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

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

class HseRiskWorkplaceType(models.Model):
	_name ='hse.risk.workplace.type'
	_description = 'Risk workplace type'

	code = fields.Char(string="Код")
	name = fields.Char(string="Ажлын байрны нэр", required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

class HseRiskWorkplaceConfig(models.Model):
	_name = 'hse.risk.workplace.config'
	_description = 'Risk workplace config'

	code = fields.Char(string="Код")
	category_id = fields.Selection([
		('person','Хүмүүст'),
		('nature','Байгаль орчинд'),
		('owner','Өмчид')],
	string="Ангилал", required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)
	risk_consequences = fields.Selection([
		('1', 'Маш бага'),
		('2', 'Бага'),
		('3', 'Дунд'),
		('4', 'Их'),
		('5', 'Ноцтой')],
	string='Үр дагавар', required=True,)

	tailbar = fields.Char(string="Тайлбар",)
	level = fields.Selection([
		('low to','Маш бага'),
		('low','Бага'),
		('mid','Дунд'),
		('high','Их'),
		('danger','Ноцтой')
	], string="Түвшин", required=True)

	level_about = fields.Char(string="Түвшин тайлбар", required=True)
	zereglel = fields.Char(string="Зэрэглэл", required=True)

class HseWorkplaceInspectionConfig(models.Model):
	_name = 'hse.workplace.inspection.config'
	_description = 'Risk workplace.inspection.config'

	name = fields.Text('Үл тохирол')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=False, default=lambda self: self.env.user.company_id)

class TextTemplate(models.Model):
	_name = 'text.template'
	_description =  'Text template'

	name = fields.Char('Нэр')
	type = fields.Selection([
		('warning','Сэрэмжлүүлэх хуудас'),
		('notice','Урьдчилсан мэдэгдэл')
	], string='Төрөл', default='warning', required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	
class HseRulesDocumentType(models.Model):
	_name ='hse.rules.document.type'
	_description = 'Rules document Type'

	name = fields.Char('Төрөл')

	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
