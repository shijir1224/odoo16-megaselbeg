#  -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class DisciplineDocument(models.Model):
	_name = "discipline.document"
	_inherit = ['mail.thread']
	_description = u'Discipline document'

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	
	
	employee_id= fields.Many2one('hr.employee',string= "Ажилтны нэр", required=True)
	department_id=fields.Many2one('hr.department', 'Хэлтэс',related='employee_id.department_id')
	job_id=fields.Many2one('hr.job', 'Албан тушаал',related='employee_id.job_id')
	engagement_in_company = fields.Date('Ажилд орсон огноо',related='employee_id.engagement_in_company')
	employee_type = fields.Selection([('employee', 'Үндсэн ажилтан'),('student', 'Цагийн ажилтан'),('trainee', 'Туршилтын ажилтан'),('contractor', 'Гэрээт'),('longleave', 'Урт хугацааны чөлөөтэй'),('maternity', 'Хүүхэд асрах чөлөөтэй'),('pregnant_leave', 'Жирэмсний амралт'),('resigned', 'Ажлаас гарсан'),('freelance', 'Бусад'),], string='Ажилтны төлөв', default='employee', required=True,tracking=True)

	number= fields.Char('Дугаар', readonly=True)
	registered_date= fields.Date('Огноо', required=True, readonly = True, default=fields.Date.context_today)
	type = fields.Many2one('warning.type','Зөрчлийн төрөл')
	caption= fields.Text('Зөрчлийн тэмдэглэл',size=196, required=True)
	date = fields.Date('Зөрчил гаргасан огноо', required=True)
	fond = fields.Text(string = 'Үндэслэл')
	discipline_employee_id= fields.Many2one('hr.employee', "Ажилтны нэр", default=_default_employee)
	discipline_department_id=fields.Many2one('hr.department', 'Хэлтэс')
	discipline_job_id=fields.Many2one('hr.job', 'Албан тушаал')
	active = fields.Boolean('Active', default=True, store=True, readonly=False)
	date_drom = fields.Date('Эхлэх огноо')
	date_to = fields.Date('Дуусах огноо')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	meet_summary = fields.Selection([('notice','Сануулах арга хэмжээ'),('salary','1 сарын хугацаанд цалингийн арга хэмжээ'),('salary2','2 сарын хугацаанд цалингийн арга хэмжээ'),('salary3','3 сарын хугацаанд цалингийн арга хэмжээ'),('end','Ажлаас халах арга хэмжээ '),('no_punish','Арга хэмжээ авахгүй байхаар шийдвэрлэсэн')],'Хурлын дүгнэлт')
	salary_procent = fields.Char('Цалингаас хасах хувь')
	salary_date_drom = fields.Date('Эхлэх огноо')
	salary_date_to = fields.Date('Дуусах огноо')
	employee_ids = fields.Many2many('hr.employee', 'discipline_document_doc', 'pun_id', 'empl_id', string='Мэдэгдэх ажилчид')
	memo = fields.Html('Хэлэлцүүлгийн тэмдэглэл')
	meet_start_date = fields.Date('Хурал огноо')
	meet_start_time = fields.Float('Хурал эхэлсэн цаг')
	num_employee_ids = fields.Many2many('hr.employee',string = 'Гишүүд')  
	before_discipline_ids = fields.Many2many('discipline.document', string="Өмнө гаргасан зөрчил", compute="_before_discipline", readonly = True)
	state = fields.Selection([('draft','Ноорог'),('sent','Шууд удирдлага'), ('approve','Албаны дарга, НУ'),('done','Захирал батласан')], default='draft', string='Төлөв')

	def action_done(self):
		self.write({'state':'done'})

	def action_draft(self):
		self.write({'state':'draft'})

	def action_sent(self):
		self.write({'state':'sent'})

	def action_approve(self):
		self.write({'state':'approve'})

# Onchange
	@api.onchange('num_employee_id')
	def onchange_num_employee_id(self):
		if self.num_employee_id:
			self.num_job_id = self.num_employee_id.job_id.id

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id
			self.job_id = self.employee_id.job_id
			self.employee_type = self.employee_id.employee_type
			self.engagement_in_company = self.employee_id.engagement_in_company

	@api.onchange('discipline_employee_id')
	def _onchange_discipline_employee_id(self):
		if self.discipline_employee_id:
			self.discipline_department_id = self.discipline_employee_id.department_id
			self.discipline_job_id = self.discipline_employee_id.job_id

# Functions
	def meet_start_time_change(self,ids):
		time = self.browse(ids)
		str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(time.meet_start_time, {}) or '')
		return str_val

	def procent_convert(self):
		self.salary_procent_convert = "{:.0%}".format(self.salary_procent)
						
	
	@api.depends('employee_id')
	def _before_discipline(self):
		for item in self:
			disciplines = item.env['discipline.document'].search([('employee_id','=',item.employee_id.id),('date','<',item.date)])
			item.before_discipline_ids = disciplines.ids

# Print functions
	def get_employee_lines(self, ids):
		print ('\n\n========get_employee_lines=====\n\n',self.num_print_name)
		self.num_printed_name()
		headers = [
			u'№',
			u'Нэр',
			u'Овог',
			u'Албан тушаал',
		]
		datas = []
		report_id = self.browse(ids)
		i = 1
		sum1 = 0
		sum2 = 0
		sum3 = 0
		
		for line in report_id.num_employee_ids:
			temp = [
				str(i),
				line.name,
				line.last_name,
				line.job_id.name,
			]
			datas.append(temp)
			i += 1
		res = {'header': headers, 'data':datas}
		return res
		
	def get_employee_lines_2(self, ids):
		headers = [
			u'№',
			u'ЗШТК-ын гишүүн',
			u'Гарын үсэг',
		]
		datas = []
		report_id = self.browse(ids)
		i = 1
		sum1 = 0
		sum2 = 0
		sum3 = 0
		
		for line in report_id.num_employee_ids:
			temp = [
				str(i),
				line.name, 
				'',
			]
			datas.append(temp)
			i += 1
		res = {'header': headers, 'data':datas}
		return res
	
    

	def get_discipline_lines(self,ids):
		report_id = self.browse(ids)
		print('\n\n========2=====\n\n',report_id.before_discipline_ids.ids)
		if  report_id.before_discipline_ids.ids != []:
			headers = [
				u'№',
				u'Зөрчил гаргасан огноо',
				u'Дугаар',
			]
			datas = []
			report_id = self.browse(ids)
			i = 1
			sum1 = 0
			sum2 = 0
			sum3 = 0
				
			for line in report_id.before_discipline_ids:
				temp = [
					str(i),
					line.date.strftime("%m/%d/%Y"), 
					line.number,
				]
				datas.append(temp)
				i += 1
			res = {'header': headers, 'data':datas}
			return res

	def action_discipline_print(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','discipline.document')], limit=1)
			
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','discipline_template_id')], limit=1)
		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
	
	def action_meet_print(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','discipline.document')], limit=1)
			
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','meeting_template')], limit=1)
		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))



class PunishmentMeetingConclusion(models.Model):
	_name = "discipline.meeting.conclusion"
	_description = "Punishment Meeting Conclution"

	name = fields.Char('Нэр')


class WarningDocument(models.Model):
	_name = "warning.document"
	_inherit = ['mail.thread']
	_description = u'Warning Document'

	def warning_default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	number= fields.Char('Дугаар', readonly=True)
	registered_date= fields.Date('Огноо', required=True, default=fields.Date.context_today)

	employee_id= fields.Many2one('hr.employee', "Ажилтны нэр", required=True)
	department_id=fields.Many2one('hr.department', 'Хэлтэс')
	type = fields.Many2one('warning.type','Сануулгын төрөл')
	engagement_in_company = fields.Date('Ажилд орсон огноо')
	employee_type = fields.Selection([('employee', 'Үндсэн ажилтан'),('student', 'Цагийн ажилтан'),('trainee', 'Туршилтын ажилтан'),('contractor', 'Гэрээт'),('longleave', 'Урт хугацааны чөлөөтэй'),('maternity', 'Хүүхэд асрах чөлөөтэй'),('pregnant_leave', 'Жирэмсний амралт'),('resigned', 'Ажлаас гарсан'),('freelance', 'Бусад'),], string='Ажилтны төлөв', default='employee', required=True,tracking=True)
	job_id=fields.Many2one('hr.job', 'Албан тушаал')
	caption= fields.Text('Сануулга тэмдэглэл',size=196, required=True)
	date = fields.Date('Сануулга гаргасан огноо', required=True)
	fond = fields.Text('Үндэслэл', required=True)
	answer = fields.Text('Цаашид анхааран зүйлс', required=True)
	is_warning = fields.Boolean('Өмнө гаргасан анхааруулгатай эсэх', default=False)
	warning_employee_id= fields.Many2one('hr.employee', "Ажилтны нэр", default=warning_default_employee)
	warning_department_id=fields.Many2one('hr.department', 'Хэлтэс')
	warning_job_id=fields.Many2one('hr.job', 'Албан тушаал')
	
	active = fields.Boolean('Active', default=True, store=True, readonly=False)
	before_warning_ids = fields.Many2many('warning.document', string='Өмнө гаргасан анхааруулга', compute="_before_warning")
	employee_ids = fields.Many2many('hr.employee', 'warning_document_doc', 'war_id', 'empl_id', string='Мэдэгдэх ажилчид')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	state = fields.Selection([('draft','Ноорог'),('sent','Шууд удирдлага'),('done','Ажилтан')], default='draft', string='Төлөв')

	def action_done(self):
		self.write({'state':'done'})

	def action_draft(self):
		self.write({'state':'draft'})

	def action_sent(self):
		self.write({'state':'sent'})

# Onchange
	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id
			self.job_id = self.employee_id.job_id
			self.employee_type = self.employee_id.employee_type
			self.engagement_in_company = self.employee_id.engagement_in_company

	@api.onchange('warning_employee_id')
	def _onchange_warning_employee_id(self):
		if self.warning_employee_id:
			self.warning_department_id = self.warning_employee_id.department_id.id
			self.warning_job_id = self.warning_employee_id.job_id.id


# Function
	@api.depends('employee_id')
	def _before_warning(self):
		for item in self:
			warning = item.env['warning.document'].search([('employee_id','=',item.employee_id.id),('date','<',item.date)])
			item.before_warning_ids = warning.ids

	def get_before_warning_lines(self, ids):
		headers = [
			u'№',
			u'Зөрчил гаргасан огноо',
			u'Үндэслэл',
			u'Дугаар',
		]
		datas = []
		report_id = self.browse(ids)
		i = 1
		sum1 = 0
		sum2 = 0
		sum3 = 0
			
		for line in report_id.before_warning_ids:
			temp = [
				str(i),
				line.date.strftime("%m/%d/%Y"), 
				line.fond,
				line.number,
			]
			datas.append(temp)
			i += 1
		res = {'header': headers, 'data':datas}
		return res
		
	
class WarningTYpe(models.Model):
	_name = "warning.type"
	_inherit = ['mail.thread']
	_description = u'Warning type'

	name = fields.Char('Нэр')

class HrEmployee(models.Model):
	_inherit = "hr.employee"

	discipline_count = fields.Integer(string='Холбоотой зөрчлийн тоо',compute='_compute_disc_count' )

	def _compute_disc_count(self):
		discipline = self.env['discipline.document'].search([('employee_id','=',self.id)])
		for emp in self:
			emp.discipline_count = len(discipline)

	def action_hr_discipline(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_discipline.action_discipline_document_tree_view')
		action['domain'] = [('employee_id','=',self.id)]
		action['res_id'] = self.id
		return action