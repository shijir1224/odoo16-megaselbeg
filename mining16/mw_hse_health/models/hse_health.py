from urllib.parse import uses_fragment
from odoo import  api, fields, models, _
from odoo.exceptions import UserError


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HseHealth(models.Model):
	_name ='hse.health'
	_description = 'Hse Health'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_rec_name = 'employee_id'
	_sql_constraints = [
		('employee_id_uniq', 'UNIQUE(employee_id)', 'Ажилтан давхардаж болохгүй!')
	]

	branch_id = fields.Many2one('res.branch', string='Салбар', default=lambda self: self.env.user.branch_id, tracking=True)
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, tracking=True)
	employee_id = fields.Many2one('hr.employee', string='Ажилтан', required=True, tracking=True)
	employee_vat = fields.Char(related='employee_id.passport_id', string='Регистр')
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал')
	company_id = fields.Many2one(related='employee_id.company_id', string='Компани')
	gender = fields.Selection(related='employee_id.gender', string='Хүйс')
	birth_year = fields.Date(related='employee_id.birthday', string='Төрсөн огноо')
	country_of_birth_id = fields.Many2one(related='employee_id.country_of_birth', string='Улс')
	phone = fields.Char(related='employee_id.work_phone', string='Утасны дугаар', )
	create_work_date = fields.Date(related='employee_id.engagement_in_company', string='Ажилд орсон огноо')
	department = fields.Many2one( related='employee_id.department_id', string='Хэсэг нэгж', store=True)
	emergency_phone = fields.Char( related='employee_id.emergency_phone', string='Яаралтай үед холбогдох дугаар')
	live_address = fields.Char(string='Гэрийн хаяг', compute='_compute_live_address', store=True)

	history_ids = fields.One2many('hse.health.history', 'parent_id', string='Өвчний түүх', tracking=True)
	physical_ids = fields.One2many('hse.physical.development', 'parent_id', string='Бие бялдарын хөгжил', tracking=True)
	detection_ids = fields.One2many('hse.early.detection', 'parent_id', string='Эрт илрүүлэг', tracking=True)
	health_questionnaire_line_ids = fields.One2many('health.questionnaire.line', 'health_id', string='Эрүүл мэндийн асуумжийн мөр', tracking=True)
	specialist_doctor_line_ids = fields.One2many('specialist.doctor.line', 'health_id', string='Нарий мэргэжлийн үзлэг', tracking=True)
	hse_ambulance_line_ids = fields.One2many('hse.ambulance.line', 'parent_id', string='Үзлэгийн түүх', tracking=True, readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт', tracking=True)

	@api.depends('employee_id','employee_id.live_address')
	def _compute_live_address(self):
		for item in self:
			if item.employee_id.live_address:
				item.live_address = str(item.employee_id.live_address)
			else:
				item.live_address = ''


class HseHealthHistory(models.Model):
	_name ='hse.health.history'
	_description = 'Hse Health History' 
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_rec_name = 'parent_id'

	date = fields.Date(string='Огноо',default=fields.Date.context_today)
	parent_id = fields.Many2one('hse.health', string='Health ID', ondelete='cascade')
	type = fields.Selection([
		('first', 'Анх ажилд орох үеийн үзлэг'),
		('that', 'Тухайн жилийн шинжилгээ'),
		('workplace_change', 'Ажлын байр өөрчлөх санал'),
	], 'Шинжилгээ үзлэг', tracking=True)

	doctor_type = fields.Selection([
		('qualified_doctor', 'Нарийн мэргэжлийн эмч'),
		('mine_doctor', 'Уурхайн эмч')
	], string='Эмч', tracking=True, default='mine_doctor', readonly=True)

	disp_type = fields.Selection([
		('hospital', 'Харьяаллын эмнэлэгт'),
		('mine_doctor', 'Уурхайн эмчийн хяналтанд')
	], string='Диспансерийн хяналт', tracking=True, default='mine_doctor')
	diagnosis_ids = fields.Many2many('patient.diagnosis', string='Үндсэн онош')
	additional_diagnosis = fields.Char(string='Туслах онош')
	
	workplace_change = fields.Selection([
		('approved', 'Зөвшөөрсөн'),
		('refused', 'Татгалзсан /шалтгаан тайлбар')
	], string='Нмэ үзлэг', tracking=True, default=False)
	employee_id = fields.Many2one('hr.employee', 'Ажилтан', related='parent_id.employee_id', store=True)
	additional_analysis_id = fields.Many2one('hse.health.analysis', string='Шинжилгээ', domain="[('employee_id', '=', employee_id)]")
	analysis_id_date = fields.Date('Шинжилгээ өгсөн хугцаа')
class HsePhysicalDevelopment(models.Model):
	_name ='hse.physical.development'
	_description = 'Hse Physical Development'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date desc'

	name = fields.Char(string='Нэр')
	parent_id = fields.Many2one('hse.health', string='Health ID', ondelete='cascade')
	date = fields.Date(string='Бүртгэсэн огноо',default=fields.Date.context_today, required=True)
	high = fields.Float(string='Өндөр/см/')
	weight = fields.Float(string='Жин/кг/')
	weight_index = fields.Float(string='Биеийн жингийн индекс', compute='_compute_weigth', store=True)
	review = fields.Text('Дүгнэлт/таргалалтын зэрэг/', readonly=True)
	waist_circumference = fields.Float('Бүсэлхүйн тойрог',)

	@api.depends('high','weight','weight_index','review')
	def _compute_weigth(self):
		for item in self:
			if item.high and item.weight:
				ss = (item.high/100)*(item.high/100)
				item.weight_index = item.weight/ss
				if item.weight_index:
					if item.weight_index < 18.5:
						item.review = 'Туранхай'
					if item.weight_index > 24.9 or item.weight_index > 18.5:
						item.review = 'Хэвийн жин'
					if item.weight_index > 29.9 or item.weight_index > 24.9:
						item.review = 'Илүүдэл жинтэй'
					if item.weight_index > 34.9 or item.weight_index > 29.9:
						item.review = 'Таргалалт 1 зэрэг'
					if item.weight_index > 39.9 or item.weight_index > 34.9:
						item.review = 'Таргалалт 2 зэрэг'
					if item.weight_index > 40.0 or item.weight_index > 39.9:
						item.review = 'Таргалалт 3 зэрэг'
				else:
					item.review = False

			else:
				item.weight_index = 0


class HseEarlyDetection(models.Model):
	_name ='hse.early.detection'
	_description = 'Hse Early Detection'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	parent_id = fields.Many2one('hse.health', string='Health ID', ondelete='cascade')
	date = fields.Date(string='Бүртгэсэн огноо',default=fields.Date.context_today, required=True)
	arterial_blood_pressure = fields.Char(string='Артерийн даралт')
	diabetes_risk_score = fields.Char(string='Чихрийн шижингийн эрсдэлийн оноо')
	blood_glucose_level = fields.Char('Цусны глюкозын хэмжээ/түргэвчлэсэн аргаар өлөн үед/>11')


class HealthQuestionaireLine(models.Model):
	_name ='health.questionnaire.line'
	_description = 'Health Questionnaire Line'
	_rec_name = 'date'

	date = fields.Date(string='Огноо')
	health_id = fields.Many2one('hse.health', string='Эрүүл мэндийн асуумж', ondelete='cascade', index=True)
	check_head = fields.Char(string='Тархи')
	check_heart = fields.Char(string='Зүрх судас')
	check_breath = fields.Char(string='Амьсгалын зам')
	check_injury = fields.Char(string='Гэмтэл бэртэл')
	check_endocrine = fields.Char(string='Дотоод шүүрл')
	check_internal_disease= fields.Char(string='Дотор')
	check_infectious_diseases= fields.Char(string='Халдварт өвчин')
	check_job_disease= fields.Char(string='Мэргэжлийн гаралтай өвчин')
	check_Hereditary_disease= fields.Char(string='Удамшлын өвчин')
	check_foot= fields.Char(string='Үе мөч')
	check_pharynx= fields.Char(string='Чих хамар хоолой')
	check_surgery= fields.Char(string='Мэс засал')
	check_nerve= fields.Char(string='Мэдрэл')
	check_eye= fields.Char(string='Нүд')
	diagnosis= fields.Char(string='Уурхайн эмчийн онош')
	additional_analysis= fields.Char(string='Нэмэлт шинжилгээ')
	note = fields.Text('Тэмдэглэл',)
	introduce= fields.Char(string='Онцгой тохиолдолд удридлагад танилцуулах')

class SpecialistDoctorLine(models.Model):
	_name ='specialist.doctor.line'
	_description = 'Specialist Doctor Line'
	_rec_name = 'date'

	health_id = fields.Many2one('hse.health', string='Нарийн мэргэжлийн үзлэг', ondelete='cascade', index=True)
	date = fields.Date(string='Огноо', default=fields.Date.context_today)
	type = fields.Selection([
		('first', 'Анх ажилд орох үеийн үзлэг'),
		('that', 'Тухайн жилийн шинжилгээ'),
		('workplace_change', 'Ажлын байр өөрчлөх санал'),
	], 'Шинжилгээ үзлэг', default='first', readonly=True)
	hospital_name = fields.Char(string='Эмнэлгийн нэр')
	doctor_type_ids = fields.Many2many('specialist.doctor.type.line', string='Эмч')
	disp_name = fields.Char(string='Диспансерийн хяналт', default='Харьяаллын эмнэлэгт', readonly=True)
	diagnosis_ids = fields.Many2many('patient.diagnosis', string='Үндсэн онош')
	additional_diagnosis = fields.Char(string='Туслах онош')
	employee_id = fields.Many2one('hr.employee', 'Ажилтан', related='health_id.employee_id', store=True)
	additional_analysis_id = fields.Many2one('hse.health.analysis', string='Шинжилгээ',domain="[('employee_id', '=', employee_id)]")
	analysis_id_date = fields.Date('Шинжилгээ өгсөн хугцаа')
	
	
class SpecialistDoctorTypeLine(models.Model):
	_name ='specialist.doctor.type.line'
	_description = 'Specialist Doctor Type Line'
	_rec_name = 'doctor_type'

	def name_get(self):
		res = []
		for item in self:
			name = ''
			doctor_type_string = dict(item._fields['doctor_type'].selection).get(item.doctor_type)
			if doctor_type_string:
				name = doctor_type_string
			res.append((item.id, name))
		return res

	doctor_type = fields.Selection([
		('heart','Зүрх судас'),
		('internal organ','Дотор'),
		('nerve','Мэдрэл'),
		('surgery','Мэс засал'),
		('mental','Сэтгэц'),
		('cancer','Хавдар'),
		('men','Эрэгтэйчүүд'),
		('women','Эмэгтэйчүүд'),
		('injure','Гэмтэл'),
		('tuberculosis','Сүрьеэ'),
		('bzho','БЗХӨ'),
		('ears_nose_throat','Чих, хамар, хоолой'),
		('eye','Нүд'),
		('skin_allergy','Арьс харшил'),
	], 'Эмч')
