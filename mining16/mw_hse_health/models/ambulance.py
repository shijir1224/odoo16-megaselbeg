from email.policy import default
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning
import time


class HseAmbulance(models.Model):
	_name ='hse.ambulance'
	_description = 'hse ambulance'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def create(self, vals):
		value = self.search([
			('branch_id', '=', vals['branch_id']), 
			('date', '=', vals['date'])
		])
		if value:
			raise UserError(u'Анхааруулга!!! Сонгосон өдөр, сонгосон салбар дээр бүртгэл байгаа тул дахин үүсгэх боломжгүй.')
		res = super(HseAmbulance, self).create(vals)
		return res

	@api.model
	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.branch_id.name + ' ' + obj.date.strftime('%Y-%m-%d') + ' Үзлэгийн мэдээ'))
		return result

	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	number = fields.Char(string='Сар',  tracking=True,  default=time.strftime('%Y-%m'), readonly=True)
	state = fields.Selection([
		('draft', 'Ноорог'),
		('done', 'Баталсан')
		], 'Төлөв', copy=False, default='draft', required=True)
	date = fields.Date(string='Үзлэгийн Өдөр', required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	uid_id = fields.Many2one('res.users', string='Хариуцсан эмч', store=True, default=lambda self: self.env.user, required=True, readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True, readonly=True, states={'draft':[('readonly',False)]})
	line_ids = fields.One2many('hse.ambulance.line', 'parent_id', string='Үзлэгт орсон хүмүүсийн түүх/Ажилчид/', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	external_line_ids = fields.One2many('hse.ambulance.external', 'parent_id', string='Үзлэгт орсон хүмүүсийн түүх(Гадны)', tracking=True, readonly=True, states={'draft':[('readonly',False)]})

	def action_to_draft(self):
		self.write({'state': 'draft'})	
	
	def action_to_done(self):
		self.write({'state': 'done'})	


	def unlink(self):
		for line in self:
			if line.line_ids or line.external_line_ids:
				raise UserError(_('Үзлэгт орсон ажилтан байна. Устгаж болохгүй(Үзлэгийн мэдээллийг цэвэрлэнэ үү)!!!'))
		return super(HseAmbulance, self).unlink()
	

class HseAmbulanceLine(models.Model):
	_name ='hse.ambulance.line'
	_description = 'hse ambulance line'
	
	name = fields.Char(string='Нэр')
	date = fields.Datetime(string='Үзлэгт орсон өдөр/цаг минут/', default=fields.Datetime.now )
	parent_id = fields.Many2one('hse.ambulance', string='Ambulance_id', )
	employee_id = fields.Many2one('hr.employee', string='Үзлэгт орсон ажилтан')
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал')
	department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Харьяалагдах нэгж', readonly=True, store=True)
	employee_vat = fields.Char(related='employee_id.passport_id', string='Регистер')
	age_id = fields.Integer(related='employee_id.age', string='Нас', readonly=True, store=True)
	employee_gender = fields.Selection(related='employee_id.gender', string='Хүйс')
	diagnosis_ids = fields.Many2many('patient.diagnosis', string='Үндсэн онош')
	additional_diagnosis = fields.Char(string='Туслах онош')

	decision_type = fields.Selection([
		('observation', 'Ажиглалт'),
		('Released_work', 'Ажлаа чөлөөлсөн'),
		('Returned_to_work', 'Ажилд нь буцааж гаргасан'),
		('Sent_to_hospital', 'Дээд шатлалын эмнэлэгт илгээсэн')
	], string='Шийдвэрлэсэн байдал')
	help_type = fields.Selection([
		('urgent', 'Яаралтай'),
		('sick', 'Өвчний улмаас'),
		('early', 'Урьдчилан сэрээлэх'),
		('control', 'Идэвхтэй  хяналт '),
	], string='Тусламжийн төрөл')

	note = fields.Text('Эмчийн тэмдэглэл')
	treatment_fre = fields.Char(string='Эмчилгээний давтамж')
	date_day = fields.Date(string='Өдөр', compute='_compute_date', store=True)
	type_treatment_ids = fields.Many2many('type.treatment', 'treatment_type_rel_2', 'typetreatment_id', 'ambulance_id',string='Эмчилгээний төрөл')
	# агуулхаас авна дараа
	medicine_name =fields.Char(string='Эмийн нэр')
	medicine_number =fields.Integer(string='Тоо ширхэг')
	hse_employee = fields.Many2many('res.users', string='Мэйл хүлээн авагчид')
	prescription =fields.Char(string='Заавар')
	attachment_ids = fields.Many2many('ir.attachment', 'ambulance_line_attachment_rel_2', 'ambulance_id', 'attachment_id', string='Хавсралт')
	additional_analysis_id = fields.Many2one('hse.health.analysis', string='Шинжилгээ', domain="[('employee_id', '=', employee_id)]")
	
	mail_type = fields.Selection([
		('infectious_disease','Халдварт өвчин '),
		('take_time_off','Өвчний улмаас '),
		], string ='Мэйл илгээх төрөл')
	
	def send_emails(self, subject, body, attachment_ids):
		mail_obj = self.env['mail.mail'].sudo().create({
			'email_from': self.env.user.company_id.email,
			'email_to': self.employee_id.parent_id.work_email,
			'subject': subject,
			'body_html': '%s' % body,
			'attachment_ids': attachment_ids
		})
		mail_obj.send()

	def sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse_health', 'action_hse_ambulance')[1]
		if self.mail_type == 'infectious_disease':
			html = u'<b>Халдварт өвчин бүртгэсэн мэдэгдэл ирлээ!!! Доорх линкээр орно уу.</b><br/>'
			html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.ambulance.line&action=%s>%s</a></b>,Халдварт өвчин бүртгэсэн мэдэгдэл ирлээ!!!"""% (base_url, self.id, action_id, self.date)
		else:
			html = u'<b>Чөлөө өвчлөлтэй холбоотой. Доорх линкээр орно уу.</b><br/>'
			html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.ambulance.line&action=%s>%s</a></b>,Чөлөөний мэдэгдэл ирлээ!!!"""% (base_url,self.id,action_id,self.date)
		self.send_emails(
			subject='Эмчийн үзлэг', 
			body=html, 
			attachment_ids=self.attachment_ids.ids
		)
		# for item in self.employee_id:
		# 	if item.partner_id:
		# 		self.env.user.send_chat(html,[item.partner_id], with_mail=True, attachment_ids=self.attachment_ids.ids)

	def action_drug_registration(self):
		context = dict(self._context)
		view_id = self.env['ir.ui.view'].search([('model','=','drug.expenditure.detail'),('name','=','drug.expenditure.detail.wizard.form')])	
# 'res_id': self.id,
		return {
			'name':_("Эмийн зарлага"),
			'type': 'ir.actions.act_window',
			'res_model': 'drug.expenditure.detail',
			'view_mode': 'form',
			'view_type': 'form',
			'context': context,
			'target': 'new',
			'view_id': view_id.id,
		}

	@api.depends('date')
	def _compute_date(self):
		for item in self:
			if item.date:
				item.date_day = item.date.strftime('%Y-%m-%d')
			else: ''

class HseAmbulanceExternal(models.Model):
	_name ='hse.ambulance.external'
	_description = 'hse ambulance external'

	name = fields.Char(string='Нэр')
	date = fields.Date(string='Үзлэгт орсон өдөр',default=fields.Datetime.now )
	parent_id = fields.Many2one('hse.ambulance', string='Ambulance_id', )
	employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	partner_id = fields.Many2one('res.partner', string='Үзлэгт орсон ажилтан', index=True)
	partner_vat = fields.Char(related='partner_id.vat', string='Регистр', store=True)
	age = fields.Integer(string='Нас', store=True)
	job = fields.Char(string='Албан тушаал')
	gender = fields.Selection([
        ('male', 'Эр'),
        ('female', 'Эм')
	], string='Хүйс')
	diagnosis_ids = fields.Many2many('patient.diagnosis', string='Үндсэн онош')
	additional_diagnosis = fields.Char(string='Туслах онош')
	disease_ids = fields.Many2many('disease.category', string='Өвчлөл')
	treatment_type_ids = fields.Many2many('type.treatment', 'treatment_type_rel_1','type_treatment_id', 'ambulance_id',string='Эмчилгээний төрөл')
	attachment_ids = fields.Many2many('ir.attachment', 'ambulance_external_attachment_rel_2', 'ambulance_id', 'attachment_id', string='Хавсралт')
	decision_type = fields.Selection([
		('observation', 'Ажиглалт'),
		('Released_work', 'Ажлаа чөлөөлсөн'),
		('Returned_to_work', 'Ажилд нь буцааж гаргасан'),
		('Sent_to_hospital', 'Дээд шатлалын эмнэлэгт илгээсэн')
	], string='Шийдвэрлэсэн байдал')
	note_book = fields.Text('Тэмдэглэл')
	treatment_fre = fields.Char(string='Эмчилгээний давтамж')
	# агуулхаас авна дараа
	medicine_number =fields.Integer(string='Тоо ширхэг')
	prescription =fields.Char(string='Заавар')
	medicine_name =fields.Char(string='Эмийн нэр')
	additional_analysis_id = fields.Many2one('hse.health.analysis', string='Шинжилгээ', domain="[('employee_id', '=', employee_id)]")
	hse_employee_ids = fields.Many2many('res.users', string='Мэйл хүлээн авагчид')
	
	mail_type = fields.Selection([
		('infectious_disease','Халдварт өвчин '),
		('take_time_off','Чөлөө '),
		], string ='Мэйл илгээх төрөл')

	def sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse_health', 'action_hse_ambulance')[1]
		if self.mail_type == 'infectious_disease':
			html = u'<b>Халдварт өвчин бүртгэсэн мэдэгдэл ирлээ!!! Доорх линкээр орно уу.</b><br/>'
			html += u"""<b>%s</b>,Халдварт өвчин бүртгэсэн мэдэгдэл ирлээ!!!"""% (self.date)
		else:
			html = u'<b>Чөлөө өвчлөлтэй холбоотой. Доорх линкээр орно уу.</b><br/>'
			html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=preliminary.notice&action=%s>%s</a></b>,Чөлөөний мэдэгдэл ирлээ!!!"""% (base_url,self.id,action_id,self.date)
		for item in self.hse_employee_ids:
			if item.partner_id:
				self.env.user.send_chat(html,[item.partner_id], with_mail=True, attachment_ids=self.attachment_ids.ids)
					
	def action_drug_registration(self):
		context = dict(self._context)
		view_id = self.env['ir.ui.view'].search([('model','=','drug.expenditure.detail'),('name','=','drug.expenditure.detail.wizard.form')])	
		# 'res_id': self.id,
		return {
			'name':_("Эмийн зарлага"),
			'type': 'ir.actions.act_window',
			'res_model': 'drug.expenditure.detail',
			'view_mode': 'form',
			'view_type': 'form',
			'context': context,
			'target': 'new',
			'view_id': view_id.id,
		}

class PatientDiagnosis(models.Model):
	_name ='patient.diagnosis'
	_description = 'patient diagnosis'


	name = fields.Char(string='Нэр', required=True)
	code = fields.Char(string='Код')
	english_name = fields.Char(string='Англи нэр')
 
	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if args is None:
			args = []
		recs = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
		return recs.name_get()
 
class DiseaseCategor(models.Model):
	_name ='disease.category'
	_description = 'patient diagnosis'
   
	name = fields.Char(string='Нэр')
	code = fields.Char(string='Код')
	english_name = fields.Char(string='Англи нэр')
 

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		if args is None:
			args = []
		recs = self.search(['|','|', ('name', operator, name), ('code', operator, name),('english_name', operator, name)] + args, limit=limit)
		return recs.name_get()


class HrEmployee(models.Model):
	_inherit ='hr.employee'

	ambulance_employee_ids = fields.One2many('hse.ambulance.line', 'employee_id', 'ХАБ Эмчийн үзлэгийн түүх', readonly=True)

class TypeTreatment(models.Model):
	_name ='type.treatment'
	_description = 'type treatment'


	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
		('suggestion','Зөвлөгөө '),
		('medicinal_cereal','Эм тарианы эмчилгээ'), 
		('Physiotherapy','Физик эмчилгээ'), 
		('part_treatment','Хэсгийн эмчилгээ'),
		('bandage','Боолт'), 
		('surgery','Мэс ажилбар'),
		('wounds_cleansing','Шарх, Цэвэрлэгээ'),
		('removing_foreign_body','Нүднээс гадны биет авах '),
		('other_medical','Бусад '),
	], string='Төрөл', required=True)

class MedicalExaminationBeforeWorks(models.Model):
	_name ='medical.examination.before.work'
	_description = 'Medical examination before work'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	rec_name = 'employee_id'


	# Ажлын өмнөх эмчийн үзлэг
	employee_id = fields.Many2one('hr.employee', string='Ажилтан')
	last_name = fields.Char(related='employee_id.last_name', string='Овог')
	first_name = fields.Char(related='employee_id.name',string=' нэр')
	job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал')
	department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Хэсэг нэгж')
	Iinspection = fields.Boolean(string="Үзлэгт орсон эсэх")
	measures_taken = fields.Char(string='Авсан арга хэмжээ')
	result = fields.Char(string=' Үр дүн')
	Reason = fields.Char(string=' Шалтгаан')


class DrugExpenditureDetail(models.Model):
	_name ='drug.expenditure.detail'
	_description = 'drug expenditure detail'

	# @api.model
	# def name_get(self):
	# 	result = []
	# 	for obj in self:
	# 		result.append(
	# 			(obj.id, obj.ambulance_line_id.date.stfrtime('%Y-%m-%d') + ' ' +'Зарлагын мэдээ'))
	# 	return result
   
	ambulance_line_id = fields.Many2one('hse.ambulance.line', string='Үзлэгийн мэдээлэл', ondelete='cascade', index=True)
	drug_expenditure_line_ids = fields.One2many('hse.drug.expenditure.line', 'expenditure_detail_id', string='Эмийн зарлагууд', readonly=False)
	drug_expenditure_id = fields.Many2one('hse.drug.expenditure.line', string='Эмийн зарлагын мэдээ', ondelete='cascade', index=True)

	def action_confirm(self):
		for item in self.drug_expenditure_line_ids:
			if not item.name:
				raise UserError('Зарлагын жагсаалт хоосон байна.')
			else:
				line_ids = []
				for ll in item:
					line_vals = {
						'name': ll.name.id,
						'balance': ll.balance,
						'expenditure_count': ll.expenditure_count,
						'uom_id': ll.uom_id.id,
						'drug_id': ll.id,
						'expenditure_detail_id': ll.expenditure_detail_id.id
					}
					line_ids.append((0, 0, line_vals))
				vals = {
					'number': 'Эмийн зарлага'+ ' ' ,
					# +self.ambulance_line_id.date,
					'company_id': self.env.user.company_id.id,
					'employee_id': self.env.user.employee_id.id,
					'date': datetime.now(),
					'line_ids': line_ids,
				}

				drug_expenditure = self.env['hse.drug.expenditure'].create(vals)
				# self.write({'expenditure_detail_id': drug_expenditure.id})