# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from venv import logger
from odoo import api, fields, models, _
import odoo.netsvc

class HrApplicant(models.Model):
	_inherit = "hr.applicant"
	
	image_1920 = fields.Binary(string="Image 1920",attachment=True)
	job_id_other = fields.Many2one('hr.job',string='Сонирхож буй бусад ажлын байр')
	date = fields.Date(string="Анкет бөглөсөн огноо")
	name = fields.Char(string="Name",required=False)
	family_name = fields.Char(string="Ургийн овог", required=False)
	last_name = fields.Char(string="Эцэг/эхийн/ нэр", required=False)
	birthday = fields.Date(string="Төрсөн он сар өдөр",compute='_compute_gender_birth',store=True,)
	age = fields.Integer('Нас',compute='_compute_age_your',store=True,)
	sex = fields.Selection(
		[('male', 'Эрэгтэй'), ('female', 'Эмэгтэй')], 'Хүйс',compute='_compute_gender_birth',store=True,)
	register = fields.Char(string='Регистрийн дугаар')
	address = fields.Char(string='Иргэний үнэмлэх дээрх хаяг')
	per_address = fields.Char(string='Түр оршин суугаа хаяг')
	driver_license = fields.Selection(
		[('yes', 'Тийм'), ('no', 'Үгүй')], string='Жолооны үнэмлэхтэй эсэх')
	license_type = fields.Char('Ангилал')
	bank_account = fields.Char('Дансны дугаар (ХХБ, Хаан банк)')
	driver_license = fields.Char('Жолооны ангилал')
	driver_year = fields.Integer('Жолоо барьсан жил')
	driver_number = fields.Char('Үнэмлэх дугаар')
	heigth = fields.Char('Биеийн өндөр')
	weigth = fields.Char('Жин')
	boot_size = fields.Char('Гутлын размер')
	shirt_size = fields.Char('Цамцны размер')
	pants_size = fields.Char('Өмдний размер')
	is_work_site = fields.Boolean('Хөдөө орон нутагт ээлжийн зохицуулалтаар ажиллах боломжтой эсэх')
	is_married = fields.Boolean('Гэрлэсэн эсэх')
	school_line_ids = fields.One2many('hr.school', 'school_app_id', string='Боловсрол')
	course_line_ids = fields.One2many('hr.course', 'course_app_id',string='Сургалт')
	language_line_ids = fields.One2many('hr.language', 'language_app_id',string='Гадаад хэлний мэдлэг')
	software_skill_line_ids = fields.One2many('hr.software.skill', 'skill_app_id',string='Програмын ур чадвар')
	employment_ids = fields.One2many('hr.employment', 'employment_app_id',string='Ажлын туршлага')
	family_line_ids = fields.One2many('hr.employee.family.line', 'family_app_id',string=' Гэр бүлийн байдал')
	family_rel_line_ids = fields.One2many('hr.employee.family.rel.line', 'family_rel_app_id',string=' Гэр бүлийн байдал')
	technic_ids = fields.One2many('hr.technic', 'parent_id',string='ур чадвар')
	degree_ids = fields.One2many('hr.degree', 'parent_id',string='зэрэг цол')
	prize_ids = fields.One2many('hr.prize', 'parent_id',string='Шагнал')
	family_employee_ids = fields.One2many('hr.family', 'hr_applicant_id',string='Хамаатан')
	advantage = fields.Text(string="Давуу тал")
	disadvantage = fields.Text(string="Сул тал")
	is_ita = fields.Boolean(string='Ита эсэх',default=False)
	work_desc = fields.Text(string="Хэрэв та 6 сараас дээш хугацаанд ажил эрхлээгүй бол шалтгаанаа бичнэ үү")
	introduce = fields.Text(string="Таны өөрийгөө илэрхийлэх хэсэг")
	is_medical_check = fields.Boolean(string='Эрүүл мэндийн үзлэгт хамрагдсан эсэх')
	medical_check_date = fields.Date(string='Эрүүл мэндийн үзлэгт хамрагдсан огноо')
	applicant_emp_id = fields.Many2one('hr.open.job',string='Нээлттэй ажлын байр')

	def get_birthday(self, register):
		if register:
			reg = register
			year = reg[2:4]
			month = reg[4:6]
			day = reg[6:8]
			if int(month[0]) >= 2:
				year = '20'+year
				month = str(int(month[0])-2)+month[1]
			else:
				year = '19'+year
			b_day = year+'-'+month+'-'+day
			datetime.strptime(b_day, '%Y-%m-%d')
			return b_day

	@api.depends('register')
	def _compute_gender_birth(self):
		for item in self:
			vat_gender = False
			vat_birthday = None
			if item.register:
				if len(item.register) >= 9:
					try:
						lan2 = item.register[len(item.register)-2]
						if (int(lan2) % 2) == 0:
							vat_gender = 'female'
						else:
							vat_gender = 'male'
					except Exception as e:
						logger.info('gender aldaa %s' % (e))
						pass
					try:
						vat_birthday = item.get_birthday(item.register)
					except Exception as e:
						logger.info('birthday aldaa %s' % (e))
						pass

				item.sex = vat_gender
				item.birthday = vat_birthday

	@api.depends('birthday')
	def _compute_age_your(self):
		current_date = datetime.now()
		current_year = current_date.year
		for item in self:
			if item.birthday:
				year = item.birthday.year
				item.age = current_year-int(year)
			else:
				item.age = 0
class HrSchool(models.Model):
	_inherit = 'hr.school'
	
	school_app_id = fields.Many2one('hr.applicant',string='Applicant')
class HrLanguage(models.Model):
	_inherit = 'hr.language'
	
	language_app_id = fields.Many2one('hr.applicant',string='Applicant')
class HrSoftwareSkill(models.Model):
	_inherit = 'hr.software.skill'

	skill_app_id = fields.Many2one('hr.applicant',string='Applicant')
class HrCourse(models.Model):
	_inherit = 'hr.course'

	course_app_id = fields.Many2one('hr.applicant',string='Applicant')
	start_date = fields.Date('Элссэн огноо')
	end_date = fields.Date('Төгссөн огноо')
	
class HrEmployment(models.Model):
	_inherit = 'hr.employment'
	
	employment_app_id = fields.Many2one('hr.applicant',string='Applicant')
	role = fields.Text(string='Таны хийж гүйцэтгэж байсан ажлын үндсэн чиг үүрэг')
	number = fields.Char(string='Удирдах ажилтны мэдээлэл, утас')
class HrEmployeeFamilyLine(models.Model):
	_inherit = "hr.employee.family.line"

	family_app_id = fields.Many2one('hr.applicant',string='Applicant')
class HrEmployeeFamilyRelLine(models.Model):
	_inherit = "hr.employee.family.rel.line"

	family_rel_app_id = fields.Many2one('hr.applicant',string='Applicant')
class HrTechnic(models.Model):
	_name = "hr.technic"

	parent_id = fields.Many2one('hr.applicant',string='Applicant')
	name = fields.Char(string='Барьж байсан техник')
	years = fields.Char(string='Тухайн техник дээр ажилласан туршлага /Жил сар/')
	level = fields.Selection([('0',u'0'),('1',u'1'),('2',u'2'),('3',u'3')],string='Түвшин')
class HrDegree(models.Model):
	_inherit ='hr.degree'
	
	spent_time = fields.Char(string='Хичээллэсэн хугацаа')
	parent_id = fields.Many2one('hr.applicant',string='Applicant')
class HrPrize(models.Model):
	_inherit = 'hr.prize'
	
	parent_id = fields.Many2one('hr.applicant',string='Applicant')
	desc = fields.Text(string='Шагнагдсан үндэслэл')

class HrFamily(models.Model):
	_name = 'hr.family'
	
	member_id= fields.Many2one('hr.employee.family.member',string='Таны хэн болох')
	employee_id= fields.Many2one('hr.employee',string='Ажилтан')
	job_id= fields.Many2one('hr.job',string='Албан тушаал')
	department_id= fields.Many2one('hr.department',string='Газар, хэсэг')
	hr_applicant_id = fields.Many2one('hr.applicant',string='Applicant')
	
	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id

