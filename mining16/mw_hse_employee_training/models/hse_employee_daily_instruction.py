from odoo import  api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import xlsxwriter
import base64
from tempfile import NamedTemporaryFile
import os,xlrd


class HseEmployeeDailyInstructiong(models.Model):
	_name ='hse.employee.daily.instruction'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'ХАБ-Өдөр тутмын зааварчилгаа'

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.employee.daily.instruction')


	name = fields.Char(string='Дугаар', copy=False, default=_default_name, readonly=True)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	date = fields.Date('Зааварчилгаа өгсөн огноо', default=fields.Date.context_today, tracking=True, readonly=True, required=True, states={'draft':[('readonly',False)]})
	employee_id = fields.Many2one('hr.employee', string='Зааварчилгаа өгсөн ажилтан', required=True, readonly=True, states={'draft':[('readonly',False)]})
	daily_instruction_line = fields.One2many('hse.employee.daily.instruction.line', 'daily_instruction_id', 'HSE daily instruction line', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', 'hse_employee_daily_instruction_ir_attachments_rel', 'employee_daily_instruction_id', 'attachment_id', string='Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: self.env.user.branch_id)
	excel_data = fields.Binary(string='Импорт файл')
	part = fields.Selection([
		('a', 'Өдөр'),
		('b', 'Шөнө')
	], 'Ээлж', required=True, readonly=True, states={'draft':[('readonly',False)]})
	search_company_id = fields.Many2one('res.company', string=u'Компани', default=lambda self: self.env.user.company_id)
	search_sector_ids = fields.Many2many('hr.department', 'sector_id', 'sector_rel', string=u'Нэгж', 
		# 'sector_rel', 'sector_id',
		domain="[('company_id','=',search_company_id)]"
		)
		#   ,('type','=','sector')

	def action_to_download(self):
		daily_instruction_line =  self.env['hse.employee.daily.instruction.line']
		if self.daily_instruction_line:
			self.daily_instruction_line.unlink()
		if self.part=='a':
			time_obj = self.env['hr.timetable.line.line'].search([
				('date','=',self.date),
				('is_work_schedule','in',['day','night']),
				('parent_id.department_id.branch_id','=',self.branch_id.id),
				('hour_to_work','>=',0),
				('shift_plan_id.is_work','=','day'),
				('parent_id.department_id','in',self.search_sector_ids.ids),
				])
			for time in time_obj:
				line_conf = daily_instruction_line.create({
					'daily_instruction_id': self.id,
					'employee_id': time.employee_id.id,
					'job_id': time.job_id.id,
					'date': self.date,
					'is_instruction': False,
				})
		else:
			time_obj = self.env['hr.timetable.line.line'].search([
				('date','=',self.date),
				('is_work_schedule','in',['day','night']),
				('parent_id.department_id.branch_id','=',self.branch_id.id),
				('hour_to_work','>=',0),
				('shift_plan_id.is_work','>=',self.part),
				('shift_plan_id.is_work','=','night'),
				('parent_id.department_id','in',self.search_sector_ids.ids),
				])
			for time in time_obj:
				line_conf = daily_instruction_line.create({
					'daily_instruction_id': self.id,
					'employee_id': time.employee_id.id,
					'job_id': time.job_id.id,
					'date': self.date,
					'is_instruction': False,
				})


	def action_to_done(self):
		for item in self:
			item.write({'state': 'done'})

	def action_to_draft(self):
		for item in self:
			item.write({'state': 'draft'})
  
	def delete_line(self):
		self.daily_instruction_line.unlink()
  
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
		line_pool =  self.env['hse.employee.daily.instruction.line']
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
			if emp_vat:
				emp_id = emp_obj.search([('passport_id','ilike',emp_vat)], limit=1)
			line_id = line_pool.create({
				'daily_instruction_id': self.id,
				'employee_id': emp_id.id,
				'date': date,
				'is_instruction': is_instruction,
			})

  
	def export_template(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Зааварчилгаа темплати.xlsx'

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

class HseEmployeeDailyInstructiongLine(models.Model):
	_name ='hse.employee.daily.instruction.line'
	_description = 'ХАБ Ажилчдын сургалтын мөр'
	_inherit = ["mail.thread", "mail.activity.mixin"]


	daily_instruction_id = fields.Many2one('hse.employee.daily.instruction', string="DailyInstructiong ID", ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string="Ажилтан", tracking=True)
	employee_lastname = fields.Char(related='employee_id.last_name', string="Овог", readonly=True)
	employee_name = fields.Char(related='employee_id.name', string="Нэр", readonly=True)
	company_id = fields.Many2one(related='employee_id.company_id', string='Компани', readonly=True)
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал', readonly=True)
	date = fields.Date('Өдөр', default=fields.Date.context_today, tracking=True)
	is_instruction = fields.Boolean('Зааварчилгаа өгсөн эсэх', default=False, tracking=True)


class HrEmployee(models.Model):
	_inherit ='hr.employee'

	daily_instruction_employee_ids = fields.One2many('hse.employee.daily.instruction.line', 'employee_id', 'HSE employee daily instruction line', readonly=True)
