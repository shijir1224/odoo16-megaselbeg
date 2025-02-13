from odoo import  api, fields, models, _


# accident_research_act
class AccidentResearchAct(models.Model):
	_name = "accident.research.act"
	_description = 'Accident Research Act'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('accident.research.act')
		return name
	
	name = fields.Char(string='Дугаар', readonly=True, default=_default_name)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, tracking=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True, default=lambda self: self.env.user.branch_id, domain="[('company_id','=',company_id)]", tracking=True)
	is_not_main = fields.Boolean(string='Гадны компани эсэх', default=False, tracking=True)
	partner_id=fields.Many2one('res.partner',string='Аж ахуйн нэгж байгууллагын нэр', tracking=True)
	employee_id = fields.Many2one('hr.employee', string='Ажилтан', tracking=True)
	location = fields.Char( related='partner_id.street', string='Байгууллагын хаяг')
	property_type = fields.Char(string='Өмчийн хэлбэр', tracking=True)
	lname = fields.Char( related='employee_id.last_name', string='Овог', store=True)
	fname = fields.Char( related='employee_id.name', string='Нэр', store=True)
	date_allocation = fields.Date(related='employee_id.birthday', string="Төрсөн огноо", store=True)
	age = fields.Integer(related='employee_id.age',string='Нас', store=True)
	gender = fields.Selection( related='employee_id.gender', string='Хүйс', store=True)
	register = fields.Char(string='Регистр', related='employee_id.passport_id')
	living_addsress = fields.Many2one(related='employee_id.country_id', string='Иргэний харъяалал', store=True)
	Social_Security_number = fields.Char(related='employee_id.ttd_number', string='Нийгмийн даатгалын дэвтрийн дугаар')
	pos_job = fields.Many2one(related='employee_id.job_id', string='Албан тушаал', store=True)
	levelicate = fields.Selection(related='employee_id.certificate', string='Боловсрол', store=True)
	certificate = fields.Many2one(related='employee_id.school_line_ids.job', string='Мэргэжил', store=True)
	start_date = fields.Date( related='employee_id.engagement_in_company', string='Компанид ажилд орсон огноо', store=True)
	command = fields.Char(string='Тушаал шийдвэрийн дугаар')
	pay_day = fields.Char(string='Шимтгэл төлж ажилласан хугацаа')
	work_safe = fields.Char(string='Аюулгүй ажиллагааны урьдчилсан болон анхан шатны зааварчилга авсан байдал ')
	work_safe_check = fields.Date(string='Хөдөлмөрийн аюулгүй байдал, эрүүл ахуйн сургалтад хамрагдсан ')
	health_examination = fields.Date(string='Эрүүл мэндийн үзлэгт хамгийн сүүлд орсон ')
	home_id = fields.Many2one(related='employee_id.address_home_id', string='Оршин суугаа хаяг real', store=True)
	live_address = fields.Text(related='employee_id.live_address', string='Оршин суугаа хаяг', store=True)
	injure_start = fields.Date(string='Үйлдвэрлэлийн осол, хурц хордлого гарсан ')
	work_loctation = fields.Char(string='Үйлдвэрлэлийн осол, хурц хордлого гарсан цех, тасаг, хэсэг, ажлын байрны нэр ')
	injure_limit = fields.Char(string='Үйлдвэрлэлийн осол, хурц хордлогын байдал /хөнгөн, хүнд, нас барсан/ ')
	injure_number = fields.Char(string='Үйлдвэрлэлийн осол, хурц хордлогод өртсөн хүний тоо /бүлэг осол эсэх/ ')
	injure_type = fields.Char(string='Үйлдвэрлэлийн осол, хурц хордлогын  гэмтлийн төрөл, ангилал ')
	injure_reason = fields.Char(string='Үйлдвэрлэлийн осол, хурц хордлого гаргахад хүргэсэн шалтгаан, хүчин зүйл ')
	commis_info = fields.Char(string='Комиссын дүгнэлт: Үйлдвэрлэлийн осол хурц хордлогыг гаргахад шууд нөлөөлсөн хүчин зүйл, шалтгаан, нөхцөл байдлын талаар тодорхой бичнэ. Дүрмийн 2.2.-т заасан тохиолдолд тусгайлан тэмдэглэнэ')
	commis_decision = fields.Char(string='Комиссын шийдвэр ')
	act_done = fields.Char(string='Акт тогтоосон комиссын дарга')

	lname_partner = fields.Char(string='Овог', tracking=True)
	fname_partner = fields.Char(string='Нэр', tracking=True)
	date_allocation_partner = fields.Date(string="Төрсөн огноо", tracking=True)
	age_partner = fields.Integer(string='Нас', tracking=True)
	gender_partner = fields.Selection([
		('Эрэгтэй','Эрэгтэй'),
		('Эмэгтэй','Эмэгтэй'),
		('Бусад','Бусад')
	], string='Хүйс', default=False, tracking=True)
	register_partner = fields.Char(string='Регистр', tracking=True)
	living_addsress_partner = fields.Text(string='Иргэний харъяалал', tracking=True)
	pos_job_partner = fields.Char(string='Албан тушаал', tracking=True)
	levelicate_partner = fields.Char(string='Боловсрол', tracking=True)
	certificate_partner = fields.Char(string='Мэргэжил', tracking=True)
	start_date_partner = fields.Date(string='Компанид ажилд орсон огноо', tracking=True)
	home_id_partner = fields.Char(string='Оршин суугаа хаяг', tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', tracking=True)