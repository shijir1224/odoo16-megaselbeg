from odoo import api, fields, models, _


class AccidentInvestigation(models.Model):
	_name = 'accident.investigation'
	_description = 'Ослын судалгааны тайлан'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('accident.investigation')
		return name

	name = fields.Char(string='Бүртгэлийн дугаар', copy=False, readonly=True, default=_default_name)
	state = fields.Selection([
		('draft', 'Ноорог'),
		('sent', 'Илгээсэн'),
		('repaired', 'Зассан'),
		('done', 'Дууссан')
	], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Datetime(string='Огноо', required=True, tracking=True, default=fields.Datetime.now,)
	branch_id = fields.Many2one('res.branch', string='Төсөл', tracking=True)
	location_id = fields.Many2one('hse.location', string='Байршил', tracking=True)
	user_id = fields.Many2one('res.users', string='Үүсгэсэн ажилтан', tracking=True, default=lambda self: self.env.user)
	reporter_type = fields.Selection([
		('partner', 'Гадны ажилтан'),
		('employee', 'Дотоод ажилтан')
	], string='Мэдээлсэн хүний төрөл', default='employee', required=True, tracking=True)
	employee_id = fields.Many2one('hr.employee', string='Ажилтан')
	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	reporter_date = fields.Datetime('Мэдээлсэн огноо', tracking=True, default=fields.Datetime.now,)
	is_injured_witness = fields.Boolean('Гэрчтэй эсэх', default=False)
	injured_witness_lines = fields.One2many('injured.witness.line', 'parent_id', string='Гэрчийн мэдээлэл')
	happened = fields.Many2many('injury.registration', 'injury_registration_happened_rel', 'injury_happened_id', string='Болсон явдлын тодорхойлолт', domain="[('type','=','happened')]", required=True)
	received_employee_id = fields.Many2one('hr.employee', string='Мэдээлэл хүлээн авсан ажилтан', required=True, tracking=True)
	received_job_id = fields.Many2one(related='received_employee_id.job_id', string='Албан тушаал')
	research_create_date = fields.Date(string='Судалгааны баг байгуулагдсан огноо', required=True)
	research_team_lines = fields.One2many('injured.research.team.line', 'parent_id', string='Судалгааны баг мэдээлэл')
	accident_employee_lines = fields.One2many('accident.employee.line', 'parent_id', string='Осолд өртсөн ажилтны мэдээлэл')
	accident_partner_lines = fields.One2many('accident.partner.line', 'parent_id', string='Осолд өртсөн харилцагч мэдээлэл')
	injury_consequences = fields.Selection([
		('died', 'Нас барсан'),
		('lost_time', 'Хугацаа алдсан'),
		('hcha', 'ХЧА'),
		('medical_help', 'Эмнэлэгийн тусламж авсан'),
	], string='Гэмтлийн үр дагавар', default=False)
	work_assigned = fields.Char(string='Тухайн үед оноосон ажил')
	injury_ids = fields.Many2many('injury.registration', string='Гэмтэл', domain="[('type','=','injury')]")
	injury_action_ids= fields.Many2many('injury.registration', 'injury_registration_action_rel', 'injury_action_id', string='Гэмтэл/үйлээр/', domain="[('type','=','action')]")
	injury_reason_ids = fields.Many2many('injury.registration', 'injury_registration_reason_rel', 'injury_reason_id', string='Гэмтэл шалтгаан', domain="[('type','=','reason')]")
	
	injury_object = fields.Char(string='Гэмтэл учруулсан биет')
	on_site_method = fields.Char(string='Газар дээр нь авсан арга хэмжээ')
	first_responder = fields.Char(string='Анхны тусламж үзүүлэгч')
	first_respond_date = fields.Datetime(string='Анхны тусламж үзүүлсэн огноо')
	first_respond_type = fields.Char(string='Үзүүлсэн тусламжийн төрөл')
	first_respond_after = fields.Selection([
		('working', 'Ажлаа үргэлжүүлсэн'),
		('doctor', 'Эмчийн тусламж авсан'),
		('go_hospital', 'Дараагийн шатны эмнэлэгт шилжсэн'),
		('go_home', 'Гэртээ харьсан'),
	], string='Анхны тусламж авсаны дараа', default=False)

	corrective_action_lines = fields.One2many('corrective.action', 'parent_id', string='Залруулах арга хэмжээ')
	person_attachment_ids = fields.Many2many('ir.attachment', 'accident_investigation_person_attachment_rel', 'person_report_id', string='Хавсралт')
	environment_attachment_ids = fields.Many2many('ir.attachment', 'accident_investigation_env_attachment_rel', 'env_report_id', string='Хавсралт')
	equipment_attachment_ids = fields.Many2many('ir.attachment', 'accident_investigation_equip_attachment_rel', 'equip_report_id', string='Хавсралт')
	methodology_attachment_ids = fields.Many2many('ir.attachment', 'accident_investigation_method_attachment_rel', 'method_report_id', string='Хавсралт')
	organization_attachment_ids = fields.Many2many('ir.attachment', 'accident_investigation_organiz_attachment_rel', 'organiz_report_id', string='Хавсралт')
	influeced_attachment_ids = fields.Many2many('ir.attachment', 'influenced_factor_analyse_attachment_rel', 'influeced_report_id', string='Хавсралт')

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_sent(self):
		self.write({'state': 'sent'})
	
	def action_to_repaired(self):
		self.write({'state': 'repaired'})
	
	def action_to_done(self):
		self.write({'state': 'done'})
	

class InjuredWitnessLine(models.Model):
	_name = 'injured.witness.line'
	_description = 'Гэрчийн мэдээлэл'

	parent_id = fields.Many2one('accident.investigation', string='Accident ID')
	name = fields.Char(string='Гэрч/байгаа бол/', required=True)
	job_name = fields.Char(string='Албан тушаал')
	employee_status = fields.Selection([
		('gereet', 'Гэрээт компани'),
		('undsen', 'Үндсэн ажилтан'),
		('guest', 'Зочин'),
	], 'Ажилтны статус', default=False)

class InjuredWitnessLine(models.Model):
	_name = 'injured.research.team.line'
	_description = 'Судалгааны багийн гишүүд'

	parent_id = fields.Many2one('accident.investigation', string='Accident ID')
	employee_id = fields.Many2one('hr.employee', string='Овог нэр', required=True)
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал', readonly=True)
	department_id = fields.Many2one(related='employee_id.department_id', string='Хэлтэс', readonly=True)
	research_team_status = fields.Selection([
		('captian', 'Багийн ахлагч'),
		('member', 'Багийн гишүүн'),
		('assistant', 'Нарийн бичиг'),
	], 'Судалгааны багийн статус', default=False)


class InjuredWitnessLine(models.Model):
	_name = 'accident.employee.line'
	_description = 'Осолд өртсөн ажилчид мэдээлэл'



	parent_id = fields.Many2one('accident.investigation', string='Accident ID')
	employee_id = fields.Many2one('hr.employee', string='Өртсөн хүн', required=True)
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал', readonly=True)
	work_year = fields.Char(related='employee_id.natural_compa_work_year', string='Ажилсан жил', readonly=True)
	that_time = fields.Selection([
		('working', 'Ажлын байранд ажлаа хийж байсан'),
		('working_travel', 'Ажлын шугамаар аялж явсан'),
		('to_work', 'Ажилдаа ирж, ажлаасаа тарж явсан'),
	], 'Ажилтны статус', default=False)
	stop_work = fields.Selection([
		('yes', 'Тийм'),
		('no', 'Үгүй'),
	], 'Ажлаа завсарласан уу ', default=False)
	off_work = fields.Char(string='Ажил завсарласан хугацаа', )
	is_day_instruction= fields.Selection([
		('yes', 'Тийм'),
		('no', 'Үгүй'),
	], 'Ажил эхлэхийн өмнө аюулгүй ажиллагааны зааварчилгаа авсан эсэх', default=False, readonly=True, compute='_compute_training')
	hr_training = fields.Char(string='Ажилтай холбоотой сургалтанд/Хүний нөөц/')
	hse_training = fields.Char(string='Ажилтай холбоотой сургалтанд/ХАБ/')


	@api.depends('is_day_instruction')
	def _compute_training(self):
		training = self.env['hse.employee.daily.instruction.line'].search([('parent_id.date','=',self.parent_id.date),('employee_id','=',self.employee_id.id)], limit=1)
		for item in self:
			if training:
				item.is_day_instruction = 'Тийм'
			else:
				item.is_day_instruction = 'Үгүй'
	

class InjuredPersonLine(models.Model):
	_name = 'accident.partner.line'
	_description = 'Осолд өртсөн харилцагч мэдээлэл'

	parent_id = fields.Many2one('accident.investigation', string='Accident ID')
	partner_id = fields.Many2one('res.partner', string='Өртсөн хүн', required=True)
	employee_status = fields.Selection([
		('gereet', 'Гэрээт компани'),
		('guest', 'Зочин'),
	], 'Ажилтны статус', default=False)

class InjuryRegistration(models.Model):
	_name = 'injury.registration'
	_description = 'Гэмтлийн бүртгэл'

	name = fields.Char(string='Нэр')
	type = fields.Selection([
		('injury', 'гэмтэл'),
		('action', 'үйлээр нь'),
		('reason', 'шалтгаан'),
		('happened','Болсон явдлын тодорхойлт')
	], 'Төрөл', default='injury')


class CorrectiveAction(models.Model):
	_name = 'corrective.action'
	_description = 'Залруулах арга хэмжээ'

	parent_id = fields.Many2one('accident.investigation', string='Accident ID')
	measures = fields.Char(string='Арга хэмжээ')
	employee_id = fields.Many2one('hr.employee', string='Хариуцах ажилтан')
	corrected_date = fields.Date(string='Залруулсан байвал зохих хугацаа')
	corrective_action = fields.Char(string='Залруулсан арга хэмжээ')
	completed_date = fields.Date(string='Гүйцэтгэж дууссан хугацаа')
