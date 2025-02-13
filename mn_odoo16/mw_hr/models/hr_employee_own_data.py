
import datetime
from odoo import api, fields, models, _
class HrEmployeeFamilyMember(models.Model):
	_name = "hr.employee.family.member"
	_description = "Hr Employee Family Member"
	_inherit = ['mail.thread']
	_order = 'name'

	
	name = fields.Char(string='Name', size=128, required=True)
	is_children = fields.Boolean(string='Хүүхэд эсэх')
class HrEmployment(models.Model):
	_name = 'hr.employment'
	_description = 'Employee Employment'
	_rec_name="organization"
	
	organization = fields.Char(string='Байгууллага', size=124)
	is_minikin = fields.Boolean(string=u'Хэвийн бус нөхцөл бол чагтал')
	job_title = fields.Char(string='Албан тушаал', size=124)
	entered_date = fields.Date(string='Орсон огноо')
	resigned_date = fields.Date(string='Гарсан огноо')
	resigned_reason = fields.Text(string='Ажлаас гарсан шалтгаан')
	wage = fields.Char(string='Цалин')
	employee_id = fields.Many2one('hr.employee', string="Employee",index=True)
	is_ndsh = fields.Boolean(string='НДШ төлсөн эсэх')
	added_exp = fields.Boolean(string='Удаан жил тооцох эсэх')
class HrEmployeeFamilyLine(models.Model):
	_name = "hr.employee.family.line"
	_description = " Hr Employee Family Lines"
	 
	employee_id = fields.Many2one('hr.employee', string='Employee')
	family_member_id = fields.Many2one('hr.employee.family.member', string='Таны юу болох')
	name = fields.Char(string='Овог нэр', size=128)
	age = fields.Integer(string='Нас',compute='_compute_age',store=False)
	birth_year = fields.Integer(string='Төрсөн он')
	current_job = fields.Char(string='Эрхэлж буй ажил',size=64)
	contact = fields.Char(string='Холбоо барих утас', size=16)
	birth_date = fields.Date('Огноо',compute = '_compute_age',store=True)

	@api.depends('birth_year')
	def _compute_age(self):
		current_date = datetime.date.today().year
		for line in self:
			if line.birth_year:
				birth_date = line.birth_year
				current_age = current_date-birth_date
				line.age = current_age
				b_day = str(birth_date)+'-'+'02'+'-'+'02'
				line.birth_date = datetime.datetime.strptime(b_day, '%Y-%m-%d').date()
			else:
				line.age = 0
				line.birth_date = None
class HrEmployeeFamilyRelLine(models.Model):
	_name = "hr.employee.family.rel.line"
	_description = " Hr Employee Family Rel Lines"
	 
	employee_id = fields.Many2one('hr.employee', string='Employee')
	family_member_id = fields.Many2one('hr.employee.family.member', string='Таны юу болох')
	name = fields.Char(string='Овог нэр', size=128)
	age = fields.Integer(string='Нас',compute='_compute_age',store=True)
	birth_year = fields.Integer(string='Төрсөн он')
	current_job = fields.Char(string='Эрхэлж буй ажил',size=64)
	contact = fields.Char(string='Холбоо барих утас', size=16)

	@api.depends('birth_year')
	def _compute_age(self):
		current_date = datetime.date.today().year
		for line in self:
			if line.birth_year:
				birth_date = line.birth_year
				current_age = current_date-birth_date
				line.age = current_age
			else:
				line.age = 0
		return True

# class ResumeLineType(models.Model):
#     _inherit = 'hr.resume.line.type'

#     type = fields.Selection([('educatiion', 'Боловсрол'),('experience', 'Ажлын туршлага'),('experience_company', 'Компани дахь ажлын түүх'),('course', 'Сургалт дамжаа')],'Төрөл')

# class ResumeLine(models.Model):
#     _inherit = 'hr.resume.line'

#     where = fields.Char('Тайлбар')
#     profession = fields.Char('Эзэмшсэн мэргэжил')
#     certificate = fields.Selection([
#         ('graduate', 'Төгсөгч'),
#         ('bachelor', 'Бакалавр'),
#         ('master', 'Мастер'),
#         ('doctor', 'Доктор'),
#         ('other', 'Бусад')], 'Боловсролын зэрэг', default='other', groups="hr.group_hr_user", tracking=True)

#     type = fields.Selection([('educatiion', 'Боловсрол'),('experience', 'Ажлын туршлага'),('course', 'Сургалт дамжаа')],'Төрөл')

class HrEmployeeLocation(models.Model):
    _name = "hr.employee.location"
    _description = 'hr employee location'

    name = fields.Char(string=u'Аймаг/Хот')
class HrEmployeeLocationLine(models.Model):
	_name = "hr.employee.location.sub"
	_description = 'hr employee location line'

	name = fields.Char(u'Сум/Дүүрэг')
	employee_location_id = fields.Many2one('hr.employee.location', string='Аймаг хот', required=True)
	shifr = fields.Char(string='Шифр')