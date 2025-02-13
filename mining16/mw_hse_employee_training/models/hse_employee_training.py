from odoo import  api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import xlsxwriter
import base64
from tempfile import NamedTemporaryFile
import os,xlrd


class HseEmployeeTraining(models.Model):
	_name ='hse.employee.training'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'ХАБ Ажилчдын сургалт'

	def unlink(self):
		for item in self:
			if item.state != 'draft':
				raise UserError('Батлагдсан байна. (Ноорог төлөв дээр устгана) !!!')
			else:
				False
		return super(HseEmployeeTraining, self).unlink()
	
	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.employee.training')

	@api.model
	def _default_email(self):
		if self.env.context.get('training',True):
			ii = self.env['email.send.users'].search([('is_first','=',True)])
			return ii.ids

	name = fields.Char(string='Дугаар', copy=False, default=_default_name, readonly=True)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	title_ids = fields.Many2many('hse.training.title', 'hse_training_title_attachments_rel', 'title_id', 'attachment_id', string='Сургалтын сэдэв', readonly=True, states={'draft':[('readonly',False)]})
	type = fields.Selection([
		('advance', 'Урьдчилсан зааварчилгаа'),
		('elementary', 'Анхан шатны зааварчилгаа'),
		('regularly', 'Ээлжит зааварчилгаа'),
		('not_regularly', 'Ээлжит бус зааварчилгаа'),
		('planned', 'Төлөвлөгөөт сургалт'),
		('contracted', 'Гэрээт ажилтны зааварчилгаа'),
		('guest', 'Зочидын зааварчилгаа'),
		('workplace', 'Өөр ажлын байранд шилжсэн сургалт'),
		('other', 'Бусад')], 'Төрөл', tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	date = fields.Date(string='Сургалт орсон огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	training_type = fields.Selection([
		('internal', 'Дотоод'),
		('foreign', 'Гадаад')], 'Сургалтын төрөл', tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	employee_ids = fields.Many2many('hr.employee', string='Сургалт орсон ажилтан', readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар/Байршил/', tracking=True, default=lambda self: self.env.user.branch_id, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', default=lambda self: self.env.user.company_id, readonly=True, states={'draft':[('readonly',False)]})
	partner_id = fields.Many2one('res.partner', string='Сургалт орсон', readonly=True, states={'draft':[('readonly',False)]})
	training_line = fields.One2many('hse.employee.training.line', 'training_id', 'HSE training line', readonly=True, states={'draft':[('readonly',False)]})
	training_partner_line = fields.One2many('hse.partner.training.line', 'training_id', 'HSE partner training line', readonly=True, states={'draft':[('readonly',False)]})
	mail_send_user_ids = fields.Many2many('email.send.users', string='Мэдэгдэл хүргэх имэйл', required=True, readonly=True, default=_default_email, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', 'hse_employee_training_ir_attachments_rel', 'employee_training_id', 'attachment_id', string='Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	is_sent = fields.Selection([
		('not_sent', 'Илгээгээгүй'),
		('sent', 'Илгээсэн'),
	], default='not_sent', string="Мэйл илгээсэн эсэх", readonly=True, tracking=True, copy=False)
	excel_data = fields.Binary(string='Импорт файл')

	search_company_id = fields.Many2one('res.company', string=u'Компани', default=lambda self: self.env.user.company_id)
	search_sector_ids = fields.Many2many('hr.department', 'sector_rel', 'sector_id', string=u'Нэгж', 
									  domain="[('company_id','=',search_company_id)]"
									#   ,('type','=','sector')
									  
									  )
	# search_department_ids = fields.Many2many('hr.department', 'deparment_rel', 'department_id', string=u'Алба хэсэг',
	# 									  domain="[('parent_id','=',search_sector_ids)]"
	# 									#   ,('type','=','department')
										  
	# 									  )

	review = fields.Char(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})

	def sent_to_mail(self):
		if self.is_sent == 'sent':
			raise UserError(_('Мэйл илгээгдсэн байна!!!'))
		self.is_sent = 'sent'

	def action_to_sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse_employee_training', 'action_hse_employee_training_core')[1]
		html = u'<b>ХАБ Шинэ ажилтны сургалтанд хамрагдсан ажилчдын мэдээлэл ирлээ Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.employee.training&action=%s>%s</a></b> дугаартай Сургалтын мэдээлэл ирлээ!"""% (base_url, self.id, action_id, self.name)
		for item in self.mail_send_user_ids:
			if item.partner_id:
				self.env.user.send_chat(html,[item.partner_id], with_mail=True)				
		self.sent_to_mail()


	def action_to_done(self):
		for item in self:
			if item.mail_send_user_ids and item.is_sent=='not_sent':
				item.action_to_sent_mail()
			self.write({'state': 'done'})

	def action_to_draft(self):
		self.write({'state': 'draft'})
  
	def delete_line(self):
		self.training_line.unlink()
	

	def employee_import(self):
		for item in self:
			domains = []
			# if item.training_line:
			# 	raise  UserError('Техникийн мэдээлэл оруулсан байна. (Мөрны мэдээллээ устгана уу).')
			self.training_line.unlink()
			
			domains += (
				)
			if item.search_company_id:
				domains.append(('company_id', '=', item.search_company_id.id))
			if item.search_sector_ids:
				domains.append(('department_id', 'in', item.search_sector_ids.ids))
			
			# if item.search_department_ids:
			# 	domains.append(('department_id', 'in', item.search_department_ids.ids))
			
			employee_line_ids = self.env['hr.employee'].sudo().search(domains)
			
			for line in employee_line_ids:
				self.env['hse.employee.training.line'].create({
					'training_id': self.id,
					'employee_id': line.id,
				})

	def delete_line(self):
		self.training_line.unlink()
  
	def date_value(self,dd):
		if dd:
			try:
				if type(dd)==float:
					serial = dd
					seconds = (serial - 25569) * 86400.0
					date=datetime.utcfromtimestamp(seconds)
				else:
					date = datetime.strptime(dd, '%Y-%m-%d')
			except ValueError:
				raise ValidationError(_('Date error %s row! \n \
				format must \'YYYY-mm-dd\'' % dd))
		else:
			date=''
		return date
  
	def import_from_excel(self):
		line_pool =  self.env['hse.employee.training.line']
		emp_obj = self.env['hr.employee']
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Aldaa')
		nrows = sheet.nrows
		rowi = 0
		data = []
		r = 0
		for item in range(2,nrows):
			row = sheet.row(item)
			emp_vat = row[0].value
			date = self.date_value(row[1].value)
			is_instruction = row[2].value or False
			score = row[3].value or False
			is_passed = row[4].value or False
			is_repeated = row[5].value or False
			is_archived = row[6].value or False	
			if emp_vat:
				emp_id = emp_obj.search([('passport_id','ilike',emp_vat)], limit=1)
			line_id = line_pool.create({
				'training_id': self.id,
				'employee_id': emp_id.id,
				'date': date,
				'is_instruction': is_instruction,
				'score': score,
				'is_passed': is_passed,
				'is_repeated': is_repeated,
				'is_archived': is_archived,
			})

  
	def export_template(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Сургалт темплати.xlsx'

		header = workbook.add_format({'bold': 1})
		header.set_font_size(12)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		worksheet = workbook.add_worksheet(u'Шинэ ажилтны сургалт темплати')
		worksheet.merge_range(0, 0, 0, 6, u"%s- өдрийн Шинэ ажилтны сургалт"%(self.date),header)
		# TABLE HEADER
		row = 1
		worksheet.set_column('A:G', 20)
		worksheet.write(row, 0, u"Ажилтны регистр", header_wrap)
		worksheet.write(row, 1, u"Огноо", header_wrap)
		worksheet.write(row, 2, u"Зааварчилга өгсөн", header_wrap)
		worksheet.write(row, 3, u"Дүн", header_wrap)
		worksheet.write(row, 4, u"Тэнцсэн эсэх", header_wrap)
		worksheet.write(row, 5, u"Давтан өгсөн эсэх", header_wrap)
		worksheet.write(row, 6, u"Архивласан", header_wrap)
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
				'type' : 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				'target': 'new',
		}


class HseEmployeeTrainingLine(models.Model):
	_name ='hse.employee.training.line'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'ХАБ Ажилчдын сургалтын мөр'

	training_id = fields.Many2one('hse.employee.training', string="Training ID", ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string="Ажилтан", tracking=True)
	employee_lastname = fields.Char(related='employee_id.last_name', string="Овог", readonly=True)
	employee_name = fields.Char(related='employee_id.name', string="Нэр", readonly=True)
	employee_vat = fields.Char(related='employee_id.passport_id', string="Регистр", readonly=True)
	department_id = fields.Many2one(related='employee_id.department_id', string='Хэсэг', readonly=True)
	branch_id = fields.Many2one(related='employee_id.department_id.branch_id', string='Салбар', readonly=True)
	company_id = fields.Many2one(related='employee_id.company_id', string='Компани', readonly=True)
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал', readonly=True)
	date = fields.Date('Өдөр', default=fields.Date.context_today, tracking=True)
	is_instruction = fields.Boolean('Зааварчилгаа өгсөн эсэх', default=False, tracking=True)
	score = fields.Float('Дүн', default=0, tracking=True)
	is_passed = fields.Boolean('Тэнцсэн эсэх', default=False, tracking=True)
	is_repeated = fields.Boolean('Давтан өгсөн эсэх', default=False, tracking=True)
	is_archived = fields.Boolean('Архивласан', default=False, tracking=True)

# class HseEmpTrainingWriteLine(models.Model):
# 	_name ='hse.emp.training.write.line'
# 	_inherit = ["mail.thread", "mail.activity.mixin"]
# 	_description = 'ХАБ Ажилчдын сургалтын бичих мөр'

# 	training_id = fields.Many2one('hse.employee.training', string="Training ID", ondelete='cascade')
# 	employee_id = fields.Char( string="Ажилтан", tracking=True)
# 	employee_lastname = fields.Char(string="Овог")
# 	employee_name = fields.Char(string="Нэр")
# 	employee_vat = fields.Char(string="Регистр")
# 	department_id = fields.Char(string='Хэсэг')
# 	company_id = fields.Char( string='Компани')
# 	job_id = fields.Char(string='Албан тушаал')
# 	date = fields.Date('Өдөр', default=fields.Date.context_today, tracking=True)
# 	is_instruction = fields.Boolean('Зааварчилгаа өгсөн эсэх', default=False, tracking=True)
# 	score = fields.Float('Дүн', default=0, tracking=True)
# 	is_passed = fields.Boolean('Тэнцсэн эсэх', default=False, tracking=True)
# 	is_repeated = fields.Boolean('Давтан өгсөн эсэх', default=False, tracking=True)
# 	is_archived = fields.Boolean('Архивласан', default=False, tracking=True)


class HsePartnerTrainingLine(models.Model):
	_name ='hse.partner.training.line'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Гадны болон Зочдын зааварчилгааны мөр'

	training_id = fields.Many2one('hse.employee.training', string="Training ID", ondelete='cascade')
	# partner_ = fields.Char( string="Сургалтанд суусан харилцагч", tracking=True)
	partner_name = fields.Char(string="Нэр")
	partner_vat = fields.Char(string="Регистр")
	partner_job = fields.Char(string='Албан тушаал')
	date = fields.Date('Өдөр', default=fields.Date.context_today, tracking=True)
	is_instruction = fields.Boolean('Зааварчилгаа өгсөн эсэх', default=False, tracking=True)
	score = fields.Float('Дүн', default=0, tracking=True)
	is_passed = fields.Boolean('Тэнцсэн эсэх', default=False, tracking=True)
	is_repeated = fields.Boolean('Давтан өгсөн эсэх', default=False, tracking=True)
	is_archived = fields.Boolean('Архивласан', default=False, tracking=True)


class HrEmployee(models.Model):
	_inherit ='hr.employee'

	training_employee_ids = fields.One2many('hse.employee.training.line', 'employee_id', 'HSE employee training line', readonly=True)

class HseTrainingTitle(models.Model):
	_name ='hse.training.title'
	_description = 'ХАБ сургалтын сэдэв'

	name = fields.Char(string="Нэр")
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)