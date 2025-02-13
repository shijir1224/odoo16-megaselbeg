# -*- coding: utf-8 -*-
import time
from venv import logger
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class ResourceResource(models.Model):
	_inherit = "resource.resource"

	name = fields.Char(required=False)


class HrJob(models.Model):
	_inherit = "hr.job"

	job_code = fields.Char('АТ код', size=8)
	work_condition = fields.Selection([('in', 'Хэвийн'), ('not', 'Хэвийн бус хүнд'), (
		'not2', 'Хэвийн бус хортой')], 'Хөдөлмөрийн нөхцөл', tracking=True)
	job_degree = fields.Char(string='Зэрэглэл')
	import_plan = fields.Boolean(
		string='Төлөвлөгөө импортлох эсэх', default=False)


class HrDepartment(models.Model):
	_inherit = "hr.department"

	branch_id = fields.Many2one('res.branch',  string=u'Салбар', tracking=True)
	name = fields.Char('Department Name', required=False, tracking=True, translate=True)
	company_id = fields.Many2one('res.company', string='Company',
								 index=True, default=lambda self: self.env.company, tracking=True)
	
	manager_ids = fields.Many2many('res.users', 'res_user_hr_department_rel', 'department_id', 'res_user_id', string = 'Батлах удирдлагууд')

	@api.depends('name')
	def _compute_complete_name(self):
		for department in self:
			department.complete_name = department.name


class HrEmployee(models.Model):
	_inherit = "hr.employee"
	_order = 'identification_id desc'

	def name_get(self):
		res = []
		for obj in self:
			if obj.sudo().identification_id and obj.name and obj.last_name:
				res.append((obj.id, obj.name+'.' + obj.last_name +
							' '+'/'+obj.sudo().identification_id+'/'))
			elif obj.name and obj.last_name:
				res.append((obj.id, obj.name+'.' + obj.last_name))
			else:
				res.append((obj.id, obj.name))

		return res
 
	user_id = fields.Many2one(
		'res.users', 'User', related=None, readonly=False)
	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	user_partner_id = fields.Many2one(
		related='user_id.partner_id', related_sudo=False, string="User's partner")

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('name', operator, name),
					  ('identification_id', operator, name)]
		pos = self.search(domain + args, limit=limit)
		return pos.name_get()

	@api.depends('engagement_in_company', 'is_minikin')
	def _compute_company_year(self):
		for item in self:
			today = date.today()
			if item.engagement_in_company:
				start_date = datetime.strptime(
					str(item.engagement_in_company), "%Y-%m-%d").date()
				if item.employee_type == 'resigned':
					if item.work_end_date:
						today = datetime.strptime(
							str(item.work_end_date), "%Y-%m-%d").date()
				else:
					today = today
				delta = relativedelta(today, start_date)
				months = delta.years * 12 + delta.months
				if item.is_minikin == True:
					item.minikin_compa_work_year = u'%d жил %d сар' % (
						months/12, months % 12)
					item.natural_compa_work_year = 0
				else:
					item.natural_compa_work_year = u'%d жил %d сар' % (
						months/12, months % 12)
					item.minikin_compa_work_year = 0
			else:
				item.minikin_compa_work_year = 0
				item.natural_compa_work_year = 0
			self.sum_company_year = months/12

	def _compute_sum_year(self):
		employment_pool = self.env['hr.employment']
		group_history_pool = self.env['hr.group.history']
		total_duration_minikin = timedelta(days=0)
		total_duration_natural = timedelta(days=0)
		total_year_natural = 0
		total_month_minikin = 0
		total_year_minikin = 0
		total_month_natural = 0
		for emp in self:
			employment_ids = employment_pool.search(
				[('employee_id', '=', emp.id)])
			for employment in employment_ids:
				resigned_date = None
				entered_date = None
				if employment.resigned_date and employment.entered_date:
					resigned_date = datetime.strptime(
						str(employment.resigned_date), "%Y-%m-%d")
					entered_date = datetime.strptime(
						str(employment.entered_date), "%Y-%m-%d")
					duration = resigned_date - entered_date
					if employment.is_ndsh == True:
						if employment.is_minikin == True:
							total_duration_minikin += duration
						else:
							total_duration_natural += duration
					total_year_minikin = (total_duration_minikin.days/365)
					total_month_minikin = (
						(total_duration_minikin.days-(total_duration_minikin.days/365*365))/30)
					total_year_natural = (total_duration_natural.days/365)
					total_month_natural = (
						(total_duration_natural.days-(total_duration_natural.days/365*365))/30)
			group_history_ids = group_history_pool.search(
				[('employee_id', '=', emp.id)])
			for group in group_history_ids:
				resigned_date = None
				entered_date = None
				if group.resigned_date and group.entered_date:
					resigned_date = datetime.strptime(
						str(group.resigned_date), "%Y-%m-%d")
					entered_date = datetime.strptime(
						str(group.entered_date), "%Y-%m-%d")
					duration = resigned_date - entered_date
					if group.is_minikin == True:
						total_duration_minikin += duration
					else:
						total_duration_natural += duration
					total_year_minikin = (total_duration_minikin.days/365)
					total_month_minikin = (
						(total_duration_minikin.days-(total_duration_minikin.days/365*365))/30)
					total_year_natural = (total_duration_natural.days/365)
					total_month_natural = (
						(total_duration_natural.days-(total_duration_natural.days/365*365))/30)
			months_minikin = total_year_minikin * 12 + total_month_minikin + \
				emp.before_worked_year * 12 + emp.before_worked_month
			months = total_year_natural * 12 + total_month_natural + \
				emp.before_year * 12 + emp.before_month
			start_date = datetime.strptime(
				str(emp.engagement_in_company), "%Y-%m-%d").date()
			today = date.today()
			delta = relativedelta(today, start_date)
			if emp.is_minikin == True:
				months_minikin += delta.years * 12 + delta.months
				emp.minikin_uls_work_year = u'%d жил %d сар' % (
					months_minikin/12, months_minikin % 12)
				emp.minikin_uls_year = months_minikin
				emp.natural_uls_work_year = u'%d жил %d сар' % (
					months/12, months % 12)
				emp.natural_uls_year = months
			else:
				months += delta.years * 12 + delta.months
				emp.natural_uls_work_year = u'%d жил %d сар' % (
					months/12, months % 12)
				emp.natural_uls_year = months
				emp.minikin_uls_work_year = u'%d жил %d сар' % (
					months_minikin/12, months_minikin % 12)
				emp.minikin_uls_year = months_minikin

			sum_months = months_minikin + months
			emp.sum_uls_year = (emp.minikin_uls_year + emp.natural_uls_year)/12
			emp.sum_uls_work_year = u'%d жил %d сар' % (
				sum_months/12, sum_months % 12)

	def _days_of_annualleave(self):
		for item in self:
			minimum_number = 0
			if item.is_to_thole == True:
				minimum_number = 20
			else:
				minimum_number = 15
			normal_extra = 0
			minikin_extra = 0
			if item.sum_uls_year > 5 and item.sum_uls_year < 10:
				normal_extra = 3
				if item.minikin_uls_year/12 > 5 and item.minikin_uls_year/12 < 10:
					minikin_extra = 2
			if item.sum_uls_year >= 10 and item.sum_uls_year < 15:
				normal_extra = 5
				if item.minikin_uls_year/12 >= 10 and item.minikin_uls_year/12 < 15:
					minikin_extra = 2
			if item.sum_uls_year >= 15 and item.sum_uls_year < 20:
				normal_extra = 7
				if item.minikin_uls_year/12 >= 15 and item.minikin_uls_year/12 < 20:
					minikin_extra = 2
			if item.sum_uls_year >= 20 and item.sum_uls_year < 25:
				normal_extra = 9
				if item.minikin_uls_year/12 >= 20 and item.minikin_uls_year/12 < 25:
					minikin_extra = 3
			if item.sum_uls_year >= 25 and item.sum_uls_year < 31:
				normal_extra = 11
				if item.minikin_uls_year/12 >= 25 and item.minikin_uls_year/12 < 31:
					minikin_extra = 4
			if item.sum_uls_year >= 31:
				normal_extra = 14
				if item.minikin_uls_year/12 >= 31:
					minikin_extra = 4
			item.days_of_annualleave = minimum_number+normal_extra + minikin_extra

	@api.depends('department_id')
	def _parent_department_id(self):
		for obj in self:
			if obj.department_id:
				if obj.department_id.parent_id:
					obj.parent_department_id = obj.department_id.parent_id.id
				else:
					obj.parent_department_id = obj.department_id.id
			else:
				obj.parent_department_id = None

	# Хувийн мэдээлэл
	name = fields.Char(string="Ажилтны нэр", related='resource_id.name',
					   required=False, store=True, readonly=False, tracking=True, translate=True)
	last_name = fields.Char(string='Овог', required=True)
	family_name = fields.Char(string='Ургийн овог')
	# is_married = fields.Boolean(string='Гэрлэсэн эсэх') ашиглахгүй core deer marital gej bga
	parent_department_id = fields.Many2one(
		'hr.department', string='Хэлтэс', store=True, readonly=True, compute=_parent_department_id)
	is_army = fields.Boolean(string='Цэргийн алба хаасан эсэх')
	driver_license_number = fields.Char(
		string='Жолооны үнэмлэхний дугаар', size=16, tracking=True)
	driver_license = fields.Char(string='Жолооны ангилал', tracking=True)
	driver_year = fields.Char(string='Жолоо барьсан жил', tracking=True)
	driver_license_b = fields.Boolean('B', tracking=True)
	driver_license_c = fields.Boolean('C', tracking=True)
	driver_license_d = fields.Boolean('D', tracking=True)
	driver_license_e = fields.Boolean('E', tracking=True)
	driver_license_m = fields.Boolean('M', tracking=True)
	work_phone = fields.Char('Work Phone', readonly=False)
	family_line_ids = fields.One2many(
		'hr.employee.family.line', 'employee_id', string='Гэр бүлийн мэдээлэл', tracking=True, copy=True)
	family_rel_line_ids = fields.One2many(
		'hr.employee.family.rel.line', 'employee_id', string='Ураг төрлийн байдал', tracking=True, copy=True)
	emp_loc_id = fields.Many2one(
		'hr.employee.location', string=u'Аймаг/Хот', tracking=True)
	emp_loc_sub_id = fields.Many2one('hr.employee.location.sub', string=u'Сум/Дүүрэг',
									 tracking=True, domain="[('employee_location_id','=',emp_loc_id)]")
	employment_ids = fields.One2many(
		'hr.employment', 'employee_id', string='Өмнөх ажлын туршлага', tracking=True, copy=True)
	gender = fields.Selection([('male', 'Эрэгтэй'), ('female', 'Эмэгтэй'), (
		'other', 'Бусад')], string='Хүйс', store=True, compute='_compute_gender_birth')
	birthday = fields.Date(string='Төрсөн өдөр', store=True,
						   compute='_compute_gender_birth')

	street = fields.Char(string='Тоот', size=64, tracking=True)
	apart = fields.Char(string='Байр', size=64, tracking=True)
	district = fields.Char(string='Баг')
	ward = fields.Many2one('ward.list', string='Хороо')
	road = fields.Char(string='Гудамж')
	apart_type = fields.Selection(
		[('house', 'Хашаа байшин'), ('apart', 'Орон сууц')], string='Төрөл')
	owner = fields.Selection(
		[('own', u'Өөрийн'), ('rent', u'Түрээс'), ('family', u'Эцэг эхийн')], string='Эзэмшил')
	children = fields.Integer(
		string='Хүүхдийн тоо', compute="_compute_children", tracking=True, store=True)
	family_count = fields.Integer(
		string='Ам бүлийн тоо', compute="_compute_family_count", tracking=True, store=True)
	phone = fields.Char(related=False, related_sudo=False,
						readonly=False, string="Хувийн утас")
	private_email = fields.Char(
		related=False, related_sudo=False, string="Хувийн имэйл",)
	ttd_number = fields.Char('Татвар төлөгчийн дугаар', required=True)
	hr_file = fields.Many2many('ir.attachment', 'hr_ir_attachment_rel',
							   'hr_file_template_id', 'attach_id', string='Файл')
	is_mission = fields.Selection([('1', u'Боломжтой'), ('2', u'3 хүртэлх насны хүүхэдтэй'), (
		'3', u'Жирэмсэн')], string='Томилолтоор явах боломжтой эсэх')
	certificate = fields.Selection([
		('not_graduate', 'Бүрэн бус дунд'),
		('graduate', 'Бүрэн дунд'),
		('technic', 'Техник,мэргэжлийн'),
		('diploma', 'Дипломын'),
		('bachelor', 'Бакалавр'),
		('master', 'Магистр'),
		('doctor', 'Доктор'),
		('other', 'Бусад')], 'Боловсролын зэрэг', default='other', groups="hr.group_hr_user")
	education_level = fields.Selection([('1', u'Сургуулийн өмнөх'), ('2', u'Бага'), ('3', u'Дунд'), ('4', u'Дээд'), (
		'5', u'МСҮТ'), ('college', u'Коллеж'), ('other', u'Бусад')], default='other', string='Боловсролын түвшин')
	age = fields.Integer(string='Нас', compute='_compute_age_your', store=True)
	file1 = fields.Many2many('ir.attachment', 'emp1_ir_attachment_rel',
							 'contract_id', 'attach_id', string='Файл')
	file2 = fields.Many2many('ir.attachment', 'emp2_ir_attachment_rel',
							 'contract_id', 'attach_id', string='Файл')
	file3 = fields.Many2many('ir.attachment', 'emp3_ir_attachment_rel',
							 'contract_id', 'attach_id', string='Файл')
	# mobile_phone = fields.Char('Work Mobile', compute=False, store=True, inverse='_inverse_work_contact_details')
	# work_email = fields.Char('Work Email', compute=False, store=True, inverse='_inverse_work_contact_details')

	def get_birthday(self, passport_id):
		if passport_id:
			reg = passport_id
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

	@api.depends('passport_id')
	def _compute_gender_birth(self):
		for item in self:
			vat_gender = False
			vat_birthday = None
			if item.passport_id:
				if len(item.passport_id) >= 9:
					try:
						lan2 = item.passport_id[len(item.passport_id)-2]
						if (int(lan2) % 2) == 0:
							vat_gender = 'female'
						else:
							vat_gender = 'male'
					except Exception as e:
						logger.info('gender aldaa %s' % (e))
						pass
					try:
						vat_birthday = item.get_birthday(item.passport_id)
					except Exception as e:
						logger.info('birthday aldaa %s' % (e))
						pass

				item.gender = vat_gender
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

# TODO pdf-r hevleh tohioldold ashiglana.
	def action_print(self):
		model_id = self.env['ir.model'].search(
			[('model', '=', 'hr.employee')], limit=1)
		template = self.env['pdf.template.generator'].search(
			[('model_id', '=', model_id.id), ('name', '=', 'hr')], limit=1)
		if template:
			res = template.print_template(self.id)
			return res
		else:
			raise UserError(
				_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

	def year(self, ids):
		line = self.browse(ids)
		sheet_year = str(line.engagement_in_company).split('-')[0]
		return sheet_year

	def month(self, ids):
		line = self.browse(ids)
		sheet_month = str(line.engagement_in_company).split('-')[1]
		return sheet_month

	def day(self, ids):
		line = self.browse(ids)
		sheet_day = str(line.engagement_in_company).split('-')[2]
		return sheet_day

	@api.depends('family_line_ids')
	def _compute_children(self):
		chh = 0
		for item in self:
			for ii in item.family_line_ids:
				if ii.family_member_id.is_children == True:
					chh += 1
					# else:
					# 	chh = item.children
			item.children = chh

	@api.depends('family_line_ids')
	def _compute_family_count(self):
		count = 1
		for item in self:
			for ii in item.family_line_ids:
				count += 1

			item.family_count = count

	# ажлын мэдээлэл
	employee_type = fields.Selection([
		('employee', 'Үндсэн ажилтан'),
		('student', 'Цагийн ажилтан'),
		('trainee', 'Туршилтын ажилтан'),
		('contractor', 'Гэрээт'),
		('longleave', 'Урт хугацааны чөлөөтэй'),
		('maternity', 'Хүүхэд асрах чөлөөтэй'),
		('pregnant_leave', 'Жирэмсний амралт'),
		('resigned', 'Ажлаас гарсан'),
		('waiting', 'Хүлээгдэж буй'),
		('blacklist', 'Blacklist'),
		('freelance', 'Бусад'),
	], string='Ажилтны төлөв', default='waiting', required=True, tracking=True)
	work_location_id = fields.Many2one(
		'hr.work.location', string='Ажлын байршил', required=True)
	work_end_date = fields.Date(string='Ажлаас гарсан огноо', tracking=True)
	is_this_month_wage = fields.Boolean(
		string='Энэ сард цалин бодох бол чеклэнэ үү', default=False, tracking=True)
	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	resigned_type = fields.Selection(
		[('type1', 'Ажилтны санаачлага'), ('type2', 'АО санаачлага')], 'Ажлаас гарах шалтгаан')

	# Ажилласан жил
	engagement_in_company = fields.Date(string='Компанид ажилд орсон огноо',
										required=True, default=lambda *a: time.strftime('%Y-%m-%d'), tracking=True)
	minikin_compa_work_year = fields.Char(
		compute=_compute_company_year, type='char', string=u'Компанид ажилласан')
	natural_compa_work_year = fields.Char(
		compute=_compute_company_year, type='char', string=u'Компанид ажилласан ')
	sum_company_year = fields.Float(
		compute=_compute_company_year, string=u'Нийт Компанид ажилласан жил', digits=(3, 2), store=True)
	minikin_uls_work_year = fields.Char(
		compute=_compute_sum_year, type='char', string=u'Улсад ажилласан')
	natural_uls_work_year = fields.Char(
		compute=_compute_sum_year, type='char', string=u'Улсад ажилласан')
	sum_uls_work_year = fields.Char(
		compute=_compute_sum_year, type='char', string=u'Нийт улсад ажилласан')
	minikin_uls_year = fields.Float(
		compute=_compute_sum_year, string=u'Uls minikin')
	natural_uls_year = fields.Float(
		compute=_compute_sum_year, string=u'Uls natural ')
	sum_uls_year = fields.Float(
		compute=_compute_sum_year, string=u'Нийт улсад ажилласан жил', digits=(3, 2))
	# long_year = fields.Float(
	# 	compute=_compute_sum_year, string=u'Нийт удаан жил', digits=(3, 2))
	before_year = fields.Integer(string='Өмнө ажилласан жил', tracking=True)
	before_month = fields.Integer(string='Өмнө ажилласан сар', tracking=True)
	before_worked_year = fields.Integer(
		string=u'Өмнө ажилласан жил', tracking=True)
	before_worked_month = fields.Integer(
		string='Өмнө ажилласан сар', tracking=True)
	is_minikin = fields.Boolean(string='Хэвийн бус нөхцөл бол чагтал')
	is_director = fields.Boolean(string='Гүйцэтгэх захирал эсэх')
	is_to_thole = fields.Boolean(string='Тусгай хэрэгцээт ажилтан эсэх')
	is_ita = fields.Boolean(string='ИТА эсэх', default=False)
	days_of_annualleave = fields.Char(
		compute=_days_of_annualleave, type='char', string=u'ЭА амрах хоног')
	annualleave = fields.Char(string='Амарсан хоног')
	before_shift_vac_date = fields.Date(
		string='Өмнөх ЭА цалин авсан огноо', tracking=True)
	before_year_shipt_leave_date = fields.Date(
		string='Дараагийн ЭА цалин авах огноо', tracking=True, compute='_compute_after_year_shipt_leave_date', store=True)
	live_address = fields.Text(string='Бүртгэлтэй хаяг')
	identification_id = fields.Char(string='Ажилтны код', tracking=True)
	passport_id = fields.Char('Регистр', tracking=True, required=True)
	is_foreign_employee = fields.Boolean(
		'Гадаад иргэн', default=False, tracking=True)

	group_history_ids = fields.One2many(
		'hr.group.history', 'employee_id', string='Группд ажилласан туршлага', tracking=True, copy=True)
	company_history_ids = fields.One2many(
		'hr.company.history', 'employee_id', string='Компанид ажилласан туршлага', tracking=True, copy=True)
	# education_line_ids = fields.One2many('hr.education.line', 'employee_id', string="Resumé lines")
	prize_line_ids = fields.One2many(
		'hr.prize', 'employee_id', string='Гавьяа шагнал', copy=True)
	talent_line_ids = fields.One2many(
		'hr.talent', 'employee_id', string='Авьяас чадвар, сонирхол', copy=True)

	bank_id = fields.Many2one('res.bank', string='Банк')
	account_number = fields.Char(string='Дансны дугаар',tracking=True)
	# department_id = fields.Many2one('hr.department', string='Алба нэгж', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True)


	@api.depends('before_shift_vac_date')
	def _compute_after_year_shipt_leave_date(self):
		for item in self:
			if item.before_shift_vac_date:
				item.before_year_shipt_leave_date = item.before_shift_vac_date + \
					relativedelta(months=12)
			else:
				item.before_year_shipt_leave_date = None
# TODO ajiltan burtgehed auto hariltsagch uusdeg boljee.

	def create_partner(self):
		# if self.user_partner_id or self.partner_id:
		# 	raise UserError(_("Харилцагч үүссэн байна"))
		# else:
		partner_obj = self.sudo().env['res.partner']
		if self.identification_id:
			user_name_last = self.name + " " + \
				self.last_name[:1] + " "+self.identification_id
		else:
			user_name_last = self.name + " " + self.last_name[:1]
		obj_res_partner = partner_obj.search([('vat', '=', self.passport_id)],limit=1)
		if not obj_res_partner:
			obj_partner_id = partner_obj.create({
				'name': user_name_last,
				'email': self.work_email,
				'company_id': self.company_id.id,
				'vat': self.passport_id,
				'ref': self.identification_id,
				'phone': self.work_phone,
				'employee': True
			})
			self.write({'user_partner_id': obj_partner_id.id})
			self.write({'partner_id': obj_partner_id.id})
		else:
			obj_res_partner.update({
				'name': user_name_last,
				'email': self.work_email,
				'company_id': self.company_id.id,
				'vat': self.passport_id,
				'ref': self.identification_id,
				'phone': self.work_phone,
				'employee': True
			})
			self.write({'user_partner_id': obj_res_partner.id})
			self.write({'partner_id': obj_res_partner.id})
		return True

	def _inverse_work_contact_details(self):
		for employee in self:
			name = employee.name + "." + employee.last_name[:1]
			obj_res_partner = self.sudo().env['res.partner'].search(
				[('vat', 'like', employee.passport_id)], limit=1)
			if not obj_res_partner:
				if not employee.is_foreign_employee:
					employee.work_contact_id = self.env['res.partner'].sudo().create({
						'email': employee.work_email,
						'mobile': employee.mobile_phone,
						'phone': self.work_phone,
						'vat': self.passport_id,
						'name': name,
						# 'ref': employee.identification_id,
						'image_1920': employee.image_1920,
						'function': employee.job_id.name,
						'employee': True
					})
				else:
					employee.work_contact_id = self.env['res.partner'].sudo().create({
						'email': employee.work_email,
						'mobile': employee.mobile_phone,
						'phone': self.work_phone,
						'name': name,
						'image_1920': employee.image_1920,
						'function': employee.job_id.name,
						'employee': True
					})
			else:
				if not employee.is_foreign_employee:
					employee.work_contact_id = obj_res_partner.id
					obj_res_partner.sudo().write({
						'email': employee.work_email,
						'mobile': employee.mobile_phone,
						'phone': self.work_phone,
						'vat': self.passport_id,
						'name': name,
						# 'ref': employee.identification_id,
						'image_1920': employee.image_1920,
						'function': employee.job_id.name,
						'employee': True
					})
				else:
					employee.work_contact_id = obj_res_partner.id
					obj_res_partner.sudo().write({
						'email': employee.work_email,
						'mobile': employee.mobile_phone,
						'phone': self.work_phone,
						# 'vat': self.passport_id,
						'name': name,
						# 'ref': employee.identification_id,
						'image_1920': employee.image_1920,
						'function': employee.job_id.name,
						'employee': True
					})
				# if not obj_res_partner.ref:
				# 	obj_res_partner.ref = employee.id
			self.write({'user_partner_id': employee.work_contact_id.id})
			self.write({'partner_id': employee.work_contact_id.id})

	@api.onchange('passport_id')
	def compute_place_of_birth(self):
		for employee in self:
			if employee.passport_id:
				id_letter = employee.passport_id
				first_letter = id_letter[0]
				second_letter = id_letter[1]
				all_letter = first_letter + second_letter
				place_id = self.env['hr.employee.location.sub'].search(
					[('shifr', '=', all_letter)])
				if place_id:
					if place_id.employee_location_id:
						employee.place_of_birth = place_id.employee_location_id.name
					if place_id.name:
						employee.place_of_birth = place_id.employee_location_id.name + ", " + place_id.name

	def create_user(self):
		login_name = ''
		if self.user_id:
			raise UserError(_("Хэрэглэгч үүссэн байна"))
		else:
			if self.work_email:
				login_name = self.work_email
			else:
				raise UserError(
					_("Ажилтны мэйл хоосон байна. Ажлын мэйл форматаар оруулна уу"))
			if login_name != '':
				user_obj = self.sudo().env['res.users']
				partner_obj = self.sudo().env['res.partner']
				obj_res_user_ids = user_obj.search(
					[('login', '=', login_name)])
				if obj_res_user_ids:
					for users in obj_res_user_ids:
						self.write({'user_id': users.id})
				else:
					if self.identification_id:
						user_name_last = self.name + " " + \
							self.last_name[:1] + " "+self.identification_id
					else:
						user_name_last = self.name + " " + self.last_name[:1]
					obj_res_partner_ids = partner_obj.search(
						[('vat', 'ilike', self.passport_id)])
					if not obj_res_partner_ids:
						if not self.is_foreign_employee:
							obj_user_id = user_obj.create({
								'name': user_name_last,
								'login': login_name,
								'password': 'Erp123456@',
								'email': self.work_email,
								# 'company_id': self.company_id.id,
								'department_id': self.department_id.id,
								'branch_id': 1,
								'lang': self.env.user.lang,
								'vat': self.passport_id,
								'manager_user_ids': self.parent_id.user_id,
							})
						else:
							obj_user_id = user_obj.create({
								'name': user_name_last,
								'login': login_name,
								'password': 'Erp123456@',
								'email': self.work_email,
								# 'company_id': self.company_id.id,
								'department_id': self.department_id.id,
								'branch_id': 1,
								'lang': self.env.user.lang,
								# 'vat': self.passport_id,
								'manager_user_ids': self.parent_id.user_id,
							})
					else:
						obj_user_id = user_obj.create({
							'name': user_name_last,
							'login': login_name,
							'password': 'Erp123456@',
							'branch_id': 1,
							'email': self.work_email,
							# 'company_id': self.company_id.id,
							'department_id': self.department_id.id,
							'lang': self.env.user.lang,
							'partner_id': obj_res_partner_ids.id,
							'vat': self.passport_id,
							'manager_user_ids': self.parent_id.user_id,
						})
						# obj_user_id.partner_id.ref = self.identification_id
						obj_user_id.partner_id.phone = self.work_phone
						obj_user_id.partner_id.employee = True
						# obj_user_id.partner_id.vat = self.passport_id
					self.write({'user_id': obj_user_id.id})
					self.write({'user_partner_id': obj_user_id.partner_id.id})
			else:
				raise UserError(_("Fill out employee's work email"))
		return True

	_sql_constraints = [
		('passport_id_uniqe', 'unique(passport_id,company_id,identification_id)',
		 'Ижил регистртэй ажилтан байж болохгүй!')
	]

	def cron_birth_notification(self):
		today = date.today() + timedelta(days=1)
		emp_pool = self.env['hr.employee'].sudo().search(
			[('employee_type', 'in', ('employee', 'trainee', 'contractor'))])
		for item in emp_pool:
			if item.birthday:
				birthday = date(today.year, item.birthday.month,
								item.birthday.day)
				days_until_birthday = (birthday-today).days
				if days_until_birthday == 0:
					item.send_birth_notif_hr()

	def birthday_notification(self):
		today = date.today()
		emp_pool = self.env['hr.employee'].sudo().search(
			[('employee_type', 'in', ('employee', 'trainee', 'contractor'))])
		for item in emp_pool:
			if item.birthday:
				birthday = date(today.year, item.birthday.month,
								item.birthday.day)
				days_until_birthday = (birthday-today).days
				if days_until_birthday == 0:
					item.send_birthday_notif_hr()

	def cron_shipt_leave_dur(self):
		today = datetime.now().date()
		employees = self.env['hr.employee'].sudo().search([])
		for item in employees:
			if item.before_shift_vac_date:
				not_date = item.before_shift_vac_date - timedelta(days=35)
				if today == not_date:
					base_url = self.env['ir.config_parameter'].sudo(
					).get_param('web.base.url')
					action_id = self.env.ref('hr.view_employee_form').id
					html = u'<b>Ажилтан.</b><br/>'
					html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.employee&action=%s>%s</a></b> таны ЭА авах огноо %s-нд үүснэ!""" % (
						base_url, self.id, action_id, item.name, item.before_shift_vac_date)
					self.env['res.users'].send_chat(html, item.partner_id)

	def send_birth_notif_hr(self):
		res_model = self.env['ir.model.data'].search([
			('module', '=', 'hr'),
			('name', 'in', ['group_hr_manager'])])
		groups = self.env['res.groups'].search(
			[('id', 'in', res_model.mapped('res_id'))], limit=1)

		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env.ref('hr.open_view_employee_list_my').id
		html = u'<b>Төрсөн өдрийн мэдэгдэл.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.employee&action=%s>%s</a></b>Ажилтны төрсөн өдөр болоход 1 хоног үлдсэн байна!""" % (
			base_url, self.id, action_id, self.name)
		for receiver in groups.users:
			self.env['res.users'].send_chat(html, receiver.partner_id)

	def send_birthday_notif_hr(self):
		res_model = self.env['ir.model.data'].search([
			('module', '=', 'hr'),
			('name', 'in', ['group_hr_manager'])])
		groups = self.env['res.groups'].search(
			[('id', 'in', res_model.mapped('res_id'))], limit=1)

		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env.ref('hr.open_view_employee_list_my').id
		html = u'<b>Төрсөн өдрийн мэдэгдэл.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.employee&action=%s> Өнөөдөр %s</a></b> ажилтны төрсөн өдөр!""" % (
			base_url, self.id, action_id, self.name)
		for receiver in groups.users:
			self.env['res.users'].send_chat(html, receiver.partner_id)


class HrAwardType(models.Model):
	_name = 'hr.award.type'
	_description = 'hr.award.type'

	name = fields.Char(string='Төрлийн нэр')


class HrPrizeName(models.Model):
	_name = 'hr.prize.name'
	_description = 'Prize name'

	name = fields.Char(string='Шагналын нэр')
	type = fields.Char(string='Шагналын төрөл')


class HrPrize(models.Model):
	_name = 'hr.prize'
	_description = 'Employee prize'
	_inherit = ['mail.thread']

	prize_type = fields.Selection([('1', 'Төрийн шагнал'),
								   ('2', 'Засгийн газрын шагнал'),
								   ('3', 'Төрийн бус байгууллагын шагнал'),
								   ('4', 'Группын шагнал'),
								   ('5', 'Байгууллагын шагнал')], string='Шагналын төрөл')
	prize_name_id = fields.Many2one('hr.prize.name', string='Шагналын нэр')
	prize_comity = fields.Char(string='Шагнагдсан байгууллага', size=64)
	prize_date = fields.Date(string='Шагнагдсан огноо')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	award_type_id = fields.Many2one('hr.award.type', string='Шагналын төрөл')
	award_amount = fields.Float('Шагналын дүн')


class HrTalent(models.Model):
	_name = 'hr.talent'
	_description = 'Employee talent'
	_inherit = ['mail.thread']

	name = fields.Char(string='Төрөл', size=64)
	success = fields.Char(string='Гаргасан амжилтууд', size=64)
	employee_id = fields.Many2one('hr.employee', string='Employee')


class HrGroupHistory(models.Model):
	_name = 'hr.group.history'
	_description = 'Group History'
	_rec_name = "organization"

	organization = fields.Char(string='Компани', size=124)
	is_minikin = fields.Boolean(u'Хэвийн бус нөхцөл бол чагтал')
	job_title = fields.Char(string='Албан тушаал', size=124)
	entered_date = fields.Date(string='Орсон огноо')
	resigned_date = fields.Date(string='Гарсан огноо')
	wage = fields.Char(string='Цалин')
	employee_id = fields.Many2one('hr.employee', string="Employee")


class HrCompanyHistory(models.Model):
	_name = 'hr.company.history'
	_description = 'Company History'

	organization = fields.Char(string='Байгууллага', size=124)
	department_id = fields.Many2one('hr.department', 'Хэлтэс')
	job_id = fields.Many2one('hr.job', 'Албан тушаал')
	company_id = fields.Many2one('res.company', 'Компани')
	is_minikin = fields.Boolean(u'Хэвийн бус нөхцөл бол чагтал')
	job_title = fields.Char(string='Албан тушаал', size=124)
	entered_date = fields.Date(string='Орсон огноо')
	resigned_date = fields.Date(string='Гарсан огноо')
	wage = fields.Char(string='Цалин')
	employee_id = fields.Many2one('hr.employee', string="Employee")
	new_value = fields.Char(string='Шинэ утга')
	pre_value = fields.Char(string='Өмнөх утга')
	type = fields.Selection([('job', 'Ажил'), ('depart', 'Хэлтэс'), (
		'level', 'Зэрэглэл'), ('type', 'Төлөв'), ('company', 'Компани')], string='Төрөл')
	date = fields.Date(string='Огноо')
	# order = fields.Many2one('hr.order', string='Тушаал')


class WardList(models.Model):
	_name = 'ward.list'
	_description = 'Ward List'

	name = fields.Char(string='Нэр', size=124)


class Partner(models.Model):
	_inherit = "res.partner"

	type = fields.Selection(selection_add=[
		('contact', 'Contact'),
		('invoice', 'Invoice Address'),
		('delivery', 'Delivery Address'),
		('private', 'Private Address'),
		('other', 'Other Address'),
	], string='Address Type',
		default=False)
