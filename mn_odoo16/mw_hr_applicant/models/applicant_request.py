# -*- coding: utf-8 -*-
from logging import Logger
import time
from venv import logger

import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from tempfile import NamedTemporaryFile
from odoo.osv import osv
import os,xlrd
import xlsxwriter
from io import BytesIO
import base64

class EnrollmentPlan(models.Model):
	_name = 'enrollment.plan'
	_description = 'enrollment plan'
	_inherit = ['mail.thread']

	name = fields.Char(string='Нэр', tracking=True)
	year = fields.Char(string='Он', tracking=True)
	line_ids = fields.One2many('enrollment.plan.line','parent_id','Lines', tracking=True)
	data = fields.Binary(string='Эксел файл')
	file_fname = fields.Char(string='File name')
	company_id = fields.Many2one('res.company',string='Компани')

	@api.onchange('data')
	@api.depends('data','file_fname')
	def check_file_type(self):
		if self.data:
			filename,filetype = os.path.splitext(self.file_fname)

	def action_import_salary(self):
		balance_data_pool =  self.env['enrollment.plan.line']
		if self.line_ids:
			self.line_ids.unlink()
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Aldaa')
		nrows = sheet.nrows
		
		rowi = 0
		data = []
		r=0
		for item in range(4,nrows):

			row = sheet.row(item)
			default_job_code = row[0].value
			jan = row[3].value
			feb = row[4].value
			mar = row[5].value
			apr = row[6].value
			may = row[7].value
			jun = row[8].value
			jul = row[9].value
			aug = row[10].value
			sep = row[11].value
			oct = row[12].value
			nov = row[13].value
			dec = row[14].value
			job_ids = self.env['hr.job'].search([('job_code','=',default_job_code)],limit=1)
			if job_ids:
				balance_data_id = balance_data_pool.create({'job_id':job_ids.id,
							'year':self.year,
							'department_id':job_ids.department_id.id,
							'jan':jan,
							'feb':feb,
							'mar':mar,
							'apr':apr,
							'may':may,
							'jun':jun,
							'jul':jul,
							'aug':aug,
							'sep':sep,
							'oct':oct,
							'nov':nov,
							'dec':dec,
							'parent_id': self.id,
							})
			else:
				raise UserError(_('%s дугаартай албан тушаалын мэдээлэл байхгүй байна.')%(default_job_code))

	def enrollment_line_create(self):
		line_pool =  self.env['enrollment.plan.line']

		if self.line_ids:
			self.line_ids.unlink()
		for obj in self:
			query = '''SELECT
				hj.id as job_id, 
				hd.id as dep_id
				FROM hr_job hj
				LEFT JOIN hr_department hd On hd.id=hj.department_id'''
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			for record in records:
				line_id = line_pool.create({
					'job_id':record['job_id'],
					'year':obj.year,
					'department_id':record['dep_id'],
					'parent_id': obj.id,
				})
				
	def print_enrollment(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Enrollment report')

		file_name = 'Орон тоо төлөвлөлтийн тайлан'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#66b2ff')

		theadermon = workbook.add_format({'bold': 1})
		theadermon.set_font_size(9)
		theadermon.set_text_wrap()
		theadermon.set_font('Times new roman')
		theadermon.set_align('center')
		theadermon.set_align('vcenter')
		theadermon.set_border(style=1)
		theadermon.set_bg_color('#009900')

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		rowx=0
		save_row=5

		sheet.merge_range(rowx+1,0,rowx+1,16, 'ОРОН ТООНЫ ТӨЛӨВЛӨЛТ/'+self.year, theader1),

		rowx=3
		# sheet.write(rowx,0, u'АТ код', theader),
		sheet.write(rowx,1, u'Нэгж', theader),
		sheet.write(rowx,2, u'Ажлын байр', theader),
		sheet.write(rowx,3, u'1-р сар', theadermon),
		sheet.write(rowx,4, u'2-р сар', theadermon),
		sheet.write(rowx,5, u'3-р сар', theadermon),
		sheet.write(rowx,6, u'4-р сар', theadermon),
		sheet.write(rowx,7, u'5-р сар', theadermon),
		sheet.write(rowx,8, u'6-р сар', theadermon),
		sheet.write(rowx,9, u'7-р сар', theadermon),
		sheet.write(rowx,10, u'8-р сар', theadermon),
		sheet.write(rowx,11, u'9-р сар', theadermon),
		sheet.write(rowx,12, u'10-р сар', theadermon),
		sheet.write(rowx,13, u'11-р сар', theadermon),
		sheet.write(rowx,14, u'12-р сар', theadermon),
		sheet.write(rowx,15, u'Тайлбар', theader),
		rowx+=1
		
		sheet.set_column('A:A', 1)
		sheet.set_column('B:B', 25)
		sheet.set_column('C:C', 25)
		sheet.set_column('D:O', 5)
		sheet.set_column('P:P', 20)

		n=1
		des=''
		for data in self.line_ids:
			if data.comments:
				des=data.comments
			else:
				des=''

			# sheet.write(rowx, 0, data.job_id.code,contest_left)
			sheet.write(rowx, 1, data.department_id.name,contest_left)
			sheet.write(rowx, 2, data.job_id.name,contest_left)
			sheet.write(rowx, 3, data.jan,contest_left)
			sheet.write(rowx, 4, data.feb,contest_left)
			sheet.write(rowx, 5, data.mar,contest_left)
			sheet.write(rowx, 6, data.apr,contest_left)
			sheet.write(rowx, 7, data.may,contest_left)
			sheet.write(rowx, 8, data.jun,contest_left)
			sheet.write(rowx, 9, data.jul,contest_left)
			sheet.write(rowx, 10, data.aug,contest_left)
			sheet.write(rowx, 11, data.sep,contest_left)
			sheet.write(rowx, 12,data.oct,contest_left)
			sheet.write(rowx, 13,data.nov,contest_left)
			sheet.write(rowx, 14,data.dec,contest_left)
			sheet.write(rowx, 15,des,contest_left)

			rowx+=1
			n+=1
		sheet.merge_range(rowx,1,rowx,2, u'Нийлбэр', theader)
		sheet.write_formula(rowx, 3, '{=SUM('+self._symbol(save_row-1, 3) +':'+ self._symbol(rowx-1, 3)+')}', theadermon)
		sheet.write_formula(rowx, 4, '{=SUM('+self._symbol(save_row-1, 4) +':'+ self._symbol(rowx-1, 4)+')}', theadermon)
		sheet.write_formula(rowx, 5, '{=SUM('+self._symbol(save_row-1, 5) +':'+ self._symbol(rowx-1, 5)+')}', theadermon)
		sheet.write_formula(rowx, 6, '{=SUM('+self._symbol(save_row-1, 6) +':'+ self._symbol(rowx-1, 6)+')}', theadermon)
		sheet.write_formula(rowx, 7, '{=SUM('+self._symbol(save_row-1, 7) +':'+ self._symbol(rowx-1, 7)+')}', theadermon)
		sheet.write_formula(rowx, 8, '{=SUM('+self._symbol(save_row-1, 8) +':'+ self._symbol(rowx-1, 8)+')}', theadermon)
		sheet.write_formula(rowx, 9, '{=SUM('+self._symbol(save_row-1, 9) +':'+ self._symbol(rowx-1, 9)+')}', theadermon)
		sheet.write_formula(rowx, 10, '{=SUM('+self._symbol(save_row-1, 10) +':'+ self._symbol(rowx-1, 10)+')}', theadermon)
		sheet.write_formula(rowx, 11, '{=SUM('+self._symbol(save_row-1, 11) +':'+ self._symbol(rowx-1, 11)+')}', theadermon)
		sheet.write_formula(rowx, 12, '{=SUM('+self._symbol(save_row-1, 12) +':'+ self._symbol(rowx-1, 12)+')}', theadermon)
		sheet.write_formula(rowx, 13, '{=SUM('+self._symbol(save_row-1, 13) +':'+ self._symbol(rowx-1, 13)+')}', theadermon)
		sheet.write_formula(rowx, 14, '{=SUM('+self._symbol(save_row-1, 14) +':'+ self._symbol(rowx-1, 14)+')}', theadermon)
		sheet.write(rowx,15, u'', theader)


		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': 'web/content/?model=report.excel.output&id=' + str(excel_id.id) + '&filename_field=filename&download=true&field=data&filename=' + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

class EnrollmentPlanLine(models.Model):
	_name = 'enrollment.plan.line'
	_description = 'enrollment plan line'
	_inherit = ['mail.thread']

	parent_id =fields.Many2one('enrollment.plan','Parent')
	job_id = fields.Many2one('hr.job',string='Ажлын байр')
	department_id = fields.Many2one('hr.department',string='Нэгж/дэлгэрэнгүй/',related='job_id.department_id')
	department_name = fields.Char(string='Нэгж', related='department_id.name', store=True, readonly=False)
	comments = fields.Char('Тайлбар')
	year = fields.Char('Он')
	jan = fields.Integer('1 сар')
	feb = fields.Integer('2 сар')
	mar = fields.Integer('3 сар')
	apr = fields.Integer('4 сар')
	may = fields.Integer('5 сар')
	jun = fields.Integer('6 сар')
	jul = fields.Integer('7 сар')
	aug = fields.Integer('8 сар')
	sep = fields.Integer('9 сар')
	oct = fields.Integer('10 сар')
	nov = fields.Integer('11 сар')
	dec = fields.Integer('12 сар')

	jan_per = fields.Integer('Гүйцэтгэл')
	feb_per = fields.Integer('Гүйцэтгэл')
	mar_per = fields.Integer('Гүйцэтгэл')
	apr_per = fields.Integer('Гүйцэтгэл')
	may_per = fields.Integer('Гүйцэтгэл')
	jun_per = fields.Integer('Гүйцэтгэл')
	jul_per = fields.Integer('Гүйцэтгэл')
	aug_per = fields.Integer('Гүйцэтгэл')
	sep_per = fields.Integer('Гүйцэтгэл')
	oct_per = fields.Integer('Гүйцэтгэл')
	nov_per = fields.Integer('Гүйцэтгэл')
	dec_per = fields.Integer('Гүйцэтгэл')

class HrApplicantRequest(models.Model):
	_name = 'hr.applicant.request'
	_inherit = ['mail.thread']
	_description = 'hr applicant request'
	_order = 'request_date desc' 
	
	def name_get(self):
		res = []
		for item in self:
			if item.request_department_id and item.job_id:
				res_name = ' [' + item.request_department_id.name+']' + '' + item.job_id.name
				res.append((item.id, res_name))
		return res

	request_department_id = fields.Many2one('hr.department', string=u'Хэлтэс', required=False)
	request_date = fields.Date('Захиалгын огноо', required=True, tracking=True,default=lambda *a: time.strftime('%Y-%m-%d'))
	reason_of_job = fields.Selection([('none','сул орон тоо'),('new','шинэ орон тоо')],'Ажлын байр үүссэн шалтгаан', required=True)
	job_experience = fields.Char('Job experience', tracking=True,required=False)
	description_of_role = fields.Text(string='Хийж гүйцэтгэх үндсэн үүрэг', required=True)
	needs = fields.Text(string='Тавигдах шаардлага', required=True,)
	source_type = fields.Selection([('inside','Дотоодоос (группийн компаниудаас)'),('outside','Гаднаас'),('both','Дотоодоос болон гаднаас')],'Бүрдүүлэлтийн суваг', required=True, default='outside', tracking=True)
	file = fields.Many2many('ir.attachment', 'hr_regulation_ir_attachment_rel',
		'matrix_id', 'attach_id', string='Файл')
	job_id = fields.Many2one('hr.job', 'Ажлын байрны нэр', required=True, tracking=True)
	no_of_employee = fields.Integer(related='job_id.no_of_employee', string='Одоо байгаа ажилтны тоо',store=True)
	no_of_recruitment = fields.Integer(related='job_id.no_of_recruitment', string='Батлагдсан орон тоо',store=True)
	meeting_time = fields.Date('Ярилцлага хийх хугацаа', tracking=True)
	employee_count = fields.Integer('Ажлын байрны тоо', tracking=True , required=True)
	in_employee_date = fields.Date('Хэрэгцээт огноо', tracking=True)
	res_company_id = fields.Many2one(
		'res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	employee_id = fields.Many2one('hr.employee','Захиалга үүсгэсэн ажилтан', default=lambda self: self.env.user.employee_id.id, readonly=True)
	open_job_id = fields.Many2one('hr.open.job','Нээлттэй ажлын байр',readonly=True)
	education = fields.Selection([('medium','Бүрэн дунд'),('special','Тусгай мэргэжлийн'),('bachalor','Бакалавр'),('master','Магистр'),('not nec','Шаардлагагүй')],'Боловсролын түвшин')
	profession = fields.Char(string='Мэргэжил')
	worked_year = fields.Selection([('above5','5-с дээш жил'),('3-5','3-5 жил'),('1-2','1-2 жил'),('1-12','1-12 сар'),('not nec','Шаардлагагүй')],'Ажилласан жил')
	flow_desc = fields.Char('Урсгал таних',compute='_compute_flow_desc',store=True)
	description = fields.Text('Тайлбар')
	request_level = fields.Selection([('normal','Энгийн'),('urgent','Яаралтай'),('need','Нэн яаралтай')],string='Зэрэглэл')
	hr_employee_id = fields.Many2one('hr.employee',string='ХН мэргэжилтэн')
	avail_job_ids = fields.Many2many('hr.job','Албан тушаал', compute='_domain_job_id')
	is_filled = fields.Boolean(string='Бүрдүүлэлт хийгдсэн')
	work_type = fields.Selection([('1', 'Бүтэн цагийн'),('2', 'Цагийн ажил'),('7','Түр ажил'),('3','Ээлжийн'),('5','Улирлаар'),('6','Гэрээт/ Зөвлөх')],string='Төрөл')
	level = fields.Selection([('1','Дээд шатны удирдлага'),
    ('2' ,'Дунд шатны удирдлага'),
    ('3','Мэргэжилтэн'),
    ('4', 'Мэргэжил хамаарахгүй'),
    ('5', 'Оюутан /Дадлага/')],string='Түвшин')

	def archive_applicant(self):
		self.write({'active': False})

	def reset_applicant(self):
		self.write({'active': True})

	def action_open_job_create(self):
		open_job_pool=self.env['hr.open.job']
		if not self.open_job_id:
			line_data_id = open_job_pool.create({
					'department_id' : self.request_department_id.id,
					'no_of_recruitment' : self.employee_count,
					'date':self.request_date,
					'res_company_id':self.res_company_id.id,
					'job_id':self.job_id.id,
					'applicant_req_id':self.id,
					'work_type':self.work_type,
					'level':self.level
				})
			self.open_job_id = line_data_id.id
		else:
			raise UserError(u'Нээлттэй ажлын байр үүссэн байна.')

	def action_to_print(self):
		model_id = self.env['ir.model'].search([('model','=','hr.applicant.request')], limit=1)
		template = self.env['pdf.template.generator'].search([('model_id','=',model_id.id),('name','=','applicant')], limit=1)
		if template:
			res = template.print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
	
	@api.depends('request_department_id')
	def _domain_job_id(self):
		for item in self:
			if item.request_department_id:
				item.avail_job_ids = item.env['hr.job'].search([('department_id', '=', item.request_department_id.id)]).ids
			else:
				item.avail_job_ids = False
# Dynamic flow
	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','hr.applicant.request'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	@api.onchange('holiday_status_id')
	def _onchange_holiday_status_id(self):
		if self.holiday_status_id.type=='non_shift':
			self.is_non = True
		else:
			self.is_non = False

	@api.depends('reason_of_job')
	def _compute_flow_desc(self):
		for i in self:
			if i.reason_of_job == 'new':
				i.flow_desc = 'new'
			else:
				i.flow_desc = ''

	@api.depends('flow_desc')
	def compute_flow_id(self):
		for item in self:
			if item.flow_desc:
				item.flow_id = self.env['dynamic.flow'].search([('model_id.model','=','hr.applicant.request'),('description','=',item.flow_desc)], order='sequence', limit=1).id
			else:
				item.flow_id = self.env['dynamic.flow'].search([('model_id.model','=','hr.applicant.request')], order='sequence', limit=1).id

	is_non = fields.Boolean('Is non', default=False)
	history_ids = fields.One2many('dynamic.flow.history', 'applicant_id', 'Түүхүүд')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True,compute=False, copy=False,domain="[('model_id.model','=','hr.applicant.request')]", required=True)

	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=False,
		domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'hr.applicant.request')]")

	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	next_state_type = fields.Char(string='Next status', compute='_compute_next_state_type')
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	branch_id = fields.Many2one('res.branch','Branch', default=lambda self: self.env.user.branch_id)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
	
	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			users = item.flow_line_next_id._get_flow_users(item.branch_id,item.sudo().employee_id.department_id, item.sudo().employee_id.user_id)
			temp_users = users.ids if users else []
			item.confirm_user_ids = [(6,0,temp_users)]

	def action_next_stage(self):
		# if self.no_of_recruitment <= self.no_of_employee:
		# 	raise UserError(u'Захиалга үүсгэх боломжгүй. %s орон тоо дүүрсэн байна.'%self.job_id.name)
		# else :
			next_flow_line_id = self.flow_line_id._get_next_flow_line()
			if next_flow_line_id:
				if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
					self.flow_line_id = next_flow_line_id
					self.env['dynamic.flow.history'].create_history(next_flow_line_id,'applicant_id', self)	
					if self.flow_line_next_id:
						send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id)
						if send_users:
							self.send_chat_employee(send_users.mapped('partner_id'))
				else:
					con_user = next_flow_line_id._get_flow_users(self.branch_id,False)
					confirm_usernames = ''
					if con_user:
						confirm_usernames = ', '.join(con_user.mapped('display_name'))
					raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
	

	# def send_chat_next_users(self, partner_ids):
	# 	state = self.flow_line_id.name
	# 	base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
	# 	action_id = self.env.ref('mw_hr_applicant.action_hr_applicant_request').id
	# 	html = u'<b>Хүний нөөцийн захиалга</b><br/><i style='color: red'>%s</i> ажилтны үүсгэсэн </br>'%(self.sudo().employee_id.name)
	# 	html = u'''<span style='font-size:10pt; color:green;'><b><a target='_blank' href=%s/web#id=%s&view_type=form&model=hr.applicant.request&action=%s>%s</a></b> - request of description for employee <b>%s</b> into status'''% (base_url,self.id,action_id,self.employee_id.name,state)
	# 	self.flow_line_id.send_chat(html, partner_ids, with_mail=True)

	
	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_applicant.action_hr_applicant_request').id
		html = u'<b>Хүний нөөцийн захиалга</b><br/><i style="color: red">%s</i> ажилтны үүсгэсэн </br>'%(self.employee_id.name)
		html += u'''<b><a target='_blank' href=%s/web#id=%s&action=%s&model=hr.applicant.request&view_type=form>%s </a></b>ажлын байрны захиалга <b>%s</b> төлөвт орлоо. Батална уу'''% (base_url,self.id,action_id,self.job_id.name,state)
		self.flow_line_id.send_chat(html,partner_ids, with_mail=False)

	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if back_flow_line_id and next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(back_flow_line_id,'applicant_id', self)
				self.send_chat_employee(self.employee_id.user_id.partner_id)
			else:
				raise UserError(_('Буцаах хэрэглэгч биш байна!'))

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
		else:
			raise UserError(_('Цуцлах хэрэглэгч биш байна.'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

	@api.depends('flow_line_next_id.state_type')
	def _compute_next_state_type(self):
		for item in self:
			item.next_state_type = item.flow_line_next_id.state_type

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		else:
			search_domain.append(('flow_id.model_id.model','=','hr.applicant.request'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find().id
		else:
			self.flow_line_id = False

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	applicant_id = fields.Many2one('hr.applicant.request', string='Хүсэлт', ondelete='cascade', index=True)

class HrOpenJob(models.Model):
	_name = 'hr.open.job'
	_description = 'hr open job'

	@api.depends('department_id')
	def _parent_department_id(self):
		for obj in self:
			if obj.department_id:
				if obj.department_id.parent_id:
					obj.parent_department_id=obj.department_id.parent_id.id
				else:
					obj.parent_department_id=obj.department_id.id
			else:
				obj.parent_department_id=None

	state = fields.Selection([('draft','Нээлтэй'),('send','Дүүргэгдсэн')], 'Төлөв', default='draft', readonly=True, tracking=True)
	parent_department_id = fields.Many2one('hr.department',string='Хэлтэс',store=True, readonly=True, compute=_parent_department_id)
	department_id = fields.Many2one('hr.department', string=u'Хэлтэс', required=True)
	job_id = fields.Many2one('hr.job', 'Ажлын байр',required=True)
	job_name = fields.Char('Зангиа дахь зарын нэр')
	no_of_recruitment = fields.Integer(string='Зарлагдсан тоо', copy=False,
		help='Number of new employees you expect to recruit.', default=1)
	date = fields.Date('Огноо')
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env['res.company']._company_default_get('account.invoice'), readonly=True)
	# open_job_ids = fields.One2many('hr.applicant.request', 'open_job_id')
	applicant_req_id = fields.Many2one('hr.applicant.request', string='Applicant')
	no_of_employee = fields.Integer(string='Хангагдсан тоо',
		help='Number of employees currently occupying this job position.')
	expected_employees = fields.Integer(string='Нээлтэй',
		help='Expected number of employees for this job position after new recruitment.')
	anket_count = fields.Integer(string='Ирсэн анкет',compute='compute_applicant_count')
	interview_call = fields.Integer(string='Ярилцлагад дуудсан',compute='compute_interview_count')
	interview_count = fields.Integer(string='Ярилцлагад орсон',compute='compute_interview_come_count')
	work_type = fields.Selection([('1', 'Бүтэн цагийн'),('2', 'Цагийн ажил'),('7','Түр ажил'),('3','Ээлжийн'),('5','Улирлаар'),('6','Гэрээт/ Зөвлөх')],string='Төрөл')
	level = fields.Selection([('1','Дээд шатны удирдлага'),
    ('2' ,'Дунд шатны удирдлага'),
    ('3','Мэргэжилтэн'),
    ('4', 'Мэргэжил хамаарахгүй'),
    ('5', 'Оюутан /Дадлага/')],string='Түвшин')
	salary_type = fields.Selection([('4', '660,000 - 800,000'),
   ( '10','800,000 - 1,000,000'),
    ('5','1,000,000 - 1,200,000'),
    ('11', '1,200,000 - 1,500,000'),
    ('6','1,500,000 - 1,800,000'),
   ( '12', '1,800,000 - 2,100,000'),
   ( '7','2,100,000 - 2,500,000'),
    ('13', '2,500,000 - 3,000,000'),
    ('8','3,000,000 - 4,000,000'),
    ('9', '4,000,000 - 5,000,000'),
    ('14', '5,000,000 - 6,000,000'),
    ('15', '6,000,000 - 7,000,000'),
   ('16', '7,000,000 - 8,000,000'),
    ('17', '8,000,000-аас дээш')],string='Цалингийн төрөл')
	location = fields.Selection([('1', 'Улаанбаатар хот'),
    ('23','Багануур дүүрэг'),
    ('24','Багахангай дүүрэг'),
    ('25','Баянгол дүүрэг'),
    ('26','Баянзүрх дүүрэг'),
    ('27', 'Налайх дүүрэг'),
    ('28', 'Сонгинохайрхан дүүрэг'),
    ('29', 'Сүхбаатар дүүрэг'),
    ('30', 'Хан-Уул дүүрэг'),
    ('31', 'Чингэлтэй дүүрэг'),
	('15', 'Өмнөговь аймаг'),
    ('2','Дархан хот'),
    ('3', 'Эрдэнэт хот'),
    ('4', 'Архангай аймаг'),
    ('5','Баян-Өлгий аймаг'),
    ('6', 'Баянхонгор аймаг'),
    ('7', 'Булган аймаг'),
    ('8', 'Говь-Алтай аймаг'),
    ('9', 'Говьсүмбэр аймаг'),
    ('10', 'Дорноговь аймаг'),
    ('11', 'Дорнод аймаг'),
    ('12', 'Дундговь аймаг'),
   ('13', 'Завхан аймаг'),
    ('14', 'Өвөрхангай аймаг'),
    ('16', 'Сүхбаатар аймаг'),
    ('17', 'Сэлэнгэ аймаг'),
    ('18', 'Төв аймаг'),
    ('19', 'Увс аймаг'),
    ('20', 'Ховд аймаг'),
    ('21', 'Хөвсгөл аймаг'),
    ('22', 'Хэнтий аймаг')],string='Байршил')

	def name_get(self):
		res = []
		for item in self:
			if item.department_id or item.job_id:
				res_name = ' [' + \
					item.department_id.display_name+']' + '' + item.job_id.name
				res.append((item.id, res_name))
			else:
				res.append(res_name)
		return res
	
	@api.onchange('job_id')
	def onchnage_job_id(self):
		if self.job_id:
			self.job_name = self.job_id.name
		
	def action_send(self):
		self.write({'state': 'send'})
		self.applicant_req_id.is_filled = True
		
	def action_draft(self):
		self.write({'state': 'draft'})
			
	def action_hr_applicant_count(self):
		self.ensure_one()
		for app in self:
			applicant = self.env['hr.applicant'].search([('applicant_emp_id', '=', app.id)])
			if applicant:
				action = self.env['ir.actions.actions']._for_xml_id('hr_recruitment.crm_case_categ0_act_job')
				action['domain'] = [('applicant_emp_id', '=', app.id)]
				action['res_id'] = app.id
				return action

	def compute_applicant_count(self):
		for app in self:
			applicant = self.env['hr.applicant'].search([('applicant_emp_id', '=', app.id)])
			app.anket_count = len(applicant)
	
	def action_interview_count(self):
		self.ensure_one()
		for app in self:
			applicant = self.env['hr.applicant'].search([('applicant_emp_id', '=', app.id),('stage_id.sequence','=',6)])
			if applicant:
				action = self.env['ir.actions.actions']._for_xml_id('hr_recruitment.crm_case_categ0_act_job')
				action['res_id'] = app.id
				return action
			
	def compute_interview_count(self):
		for app in self:
			applicant = self.env['hr.applicant'].search([('applicant_emp_id', '=', app.id),('stage_id.sequence','=',6)])
			app.interview_call = len(applicant)
	
	def action_interview_come_count(self):
		self.ensure_one()
		for app in self:
			applicant = self.env['hr.applicant'].search([('applicant_emp_id', '=', app.id),('stage_id.sequence','=',7)])
			if applicant:
				action = self.env['ir.actions.actions']._for_xml_id('hr_recruitment.crm_case_categ0_act_job')
				action['res_id'] = app.id
				return action
	
	def compute_interview_come_count(self):
		for app in self:
			applicant = self.env['hr.applicant'].search([('applicant_emp_id', '=', app.id),('stage_id.sequence','=',7)])
			app.interview_count = len(applicant)
