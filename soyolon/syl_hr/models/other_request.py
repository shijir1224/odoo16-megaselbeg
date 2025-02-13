# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import xlsxwriter
from io import BytesIO
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring
class LongYear(models.Model):
	_name = 'long.year'
	_description = 'Long Year'
	_inherit = ['mail.thread']

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	name = fields.Char(string='Нэр')
	employee_id = fields.Many2one(
		'hr.employee', string='Бүртгэсэн ажилтан', default=_default_employee)
	company_id = fields.Many2one(
		'res.company', string='Компани', related='employee_id.company_id')
	job_id = fields.Many2one(
		'hr.job', string='Албан тушаал', related='employee_id.job_id')
	department_id = fields.Many2one(
		'hr.department', string='Алба нэгж', related='employee_id.department_id')
	date = fields.Date(string='Бүртгэсэн огноо',
					   default=fields.Date.context_today)
	state = fields.Selection([('draft', u'Ноорог'), ('sent', u'Илгээсэн'), ('confirm', u'Хянасан'), ('done_hr', u'Баталсан'),('done', u'Санхүү хүлээж авсан')], string='Төлөв', default='draft',tracking=True)
	line_ids = fields.One2many('long.year.approve', 'parent_id', string='Удаан жил')
	h_emp_id = fields.Many2one("hr.employee", "Хянасан")
	employee_id = fields.Many2one("hr.employee", "Нэгтгэсэн")
	confirm_emp_id = fields.Many2one("hr.employee", "Баталсан")

	def action_send(self):
		self.write({'state': 'sent'})

	def action_draft(self):
		self.write({'state': 'draft'})

	def action_confirm(self):
		self.write({'state': 'confirm'})
	def action_done(self):
		self.write({'state': 'done'})

	def action_done_hr(self):
		self.write({'state': 'done_hr'})

	def long_year(self):
		long_year_pool = self.env['long.year.approve']
		if self.line_ids:
			self.line_ids.unlink()
		query = """SELECT 
			hr.id as emp_id,
			hj.id as job_id,
			hr.identification_id as identification_id
			FROM hr_employee hr	
			LEFT JOIN hr_work_location wl On wl.id=hr.work_location_id		
			LEFT JOIN hr_job hj On hj.id=hr.job_id
			WHERE employee_type in ('employee','trainee','contractor') """
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		for obj in records:
			employee = self.env['hr.employee'].search([('id','=',obj['emp_id'])],limit=1)
			line_conf = long_year_pool.create({
				'identification_id': obj['identification_id'],
				'employee_id': obj['emp_id'],
				'job_id': obj['job_id'],
				'long_year': employee.total_long_year,
				'l_year':float(employee.long_year),
				'long_year_month':float(employee.long_year_month),
				'long_year_day':float(employee.long_year_day),
				'parent_id': self.id
			})   

	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Ажилтнуудын удаан жилийн мэдээлэл'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')
		
		content_left = workbook.add_format({'num_format': '#,##0'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('left')
		content_left.set_num_format('#,##0.00')

		content_left_h = workbook.add_format({})
		content_left_h.set_text_wrap()
		content_left_h.set_font('Times new roman')
		content_left_h.set_font_size(11)
		content_left_h.set_align('left')

		content_date_center = workbook.add_format({'num_format': 'YYYY-MM-DD'})
		content_date_center.set_text_wrap()
		content_date_center.set_font_size(9)
		content_date_center.set_border(style=1)
		content_date_center.set_align('vcenter')

		
		center = workbook.add_format({})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(11)	 
		center.set_align('right')
		center.set_border(style=1)
		center.set_align('vcenter')

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('center')
		center_att.set_align('vcenter')
		center_att.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Гүйцэтгэлийн нэгтгэл')

		sheet.merge_range(1, 0, 1, 8, u'БАТЛАВ. ЗАХИРГАА-ХҮНИЙ НӨӨЦИЙН ЗАХИРАЛ ...............................'' %s' '.' '%s' %(self.confirm_emp_id.last_name[:1],self.confirm_emp_id.name), h1)	
		sheet.merge_range(3, 0, 3, 8, u'Соёолон Интернэшнл ХХК-ийн ажилтнуудын ажилласан жилийн мэдээлэл', h1)

		rowx=6
		
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'Код', theader),
		sheet.write(rowx,2, u'Овог', theader),
		sheet.write(rowx,3, u'Нэр', theader),
		sheet.write(rowx,4, u'Регистрийн №', theader),
		sheet.write(rowx,5, u'Албан тушаал', theader),
		sheet.write(rowx,6, u'Компанид ажилд орсон огноо', theader),
		sheet.write(rowx,7, u'Компанид ажилласан хугацаа', theader),

		sheet.set_column('A:A', 4)
		sheet.set_column('B:H', 15)
		n=1
		rowx+=1
		for data in self.line_ids:
			sheet.write(rowx, 0, n,center)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.passport_id,content_left)
			sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 6,data.engagement_in_company,content_date_center)
			sheet.write(rowx, 7,data.long_year,center_att)
			
			rowx+=1
			n+=1
	
		sheet.merge_range(rowx+6,0,rowx+6,10,'Нэгтгэсэн:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.employee_id.job_id.name,self.employee_id.last_name[:1],self.employee_id.name), content_left_h),

		sheet.merge_range(rowx+8,0,rowx+8,10,'Хянасан:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.h_emp_id.job_id.name,self.h_emp_id.last_name[:1],self.h_emp_id.name), content_left_h),
	
		

		workbook.close()
		out = encodestring(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}
	
	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row + 1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col + 1
		while div:
			(div, mod) = divmod(div - 1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol
class LongYearApprove(models.Model):
	_name = 'long.year.approve'
	_description = 'Long Year Approve'
	
	employee_id = fields.Many2one('hr.employee',string='Ажилтан')
	job_id = fields.Many2one('hr.job',string='Албан тушаал')
	engagement_in_company = fields.Date(
		string='Ажилд орсон огноо', related='employee_id.engagement_in_company')
	long_year = fields.Char('Удаан жил')
	l_year = fields.Float(string='Жил')
	long_year_month = fields.Float(string='Сар')
	long_year_day = fields.Float(string='Өдөр')
	parent_id = fields.Many2one('long.year',string='parent')
	identification_id = fields.Char(string='Код')


class SalaryLevel(models.Model):
	_name = "salary.level"
	_description = "Salary level"

	name = fields.Char(string='Цалингийн код')
	position_level_sal = fields.Selection([('employee', 'Ажилтан'), ('specialist', 'Мэргэжилтэн'), ('supervisor', 'Ахлах'), (
		'manager', 'Менежер/инженер'), ('general', 'Ерөнхий'), ('director', 'Хэлтсийн захирал')], string='Албан тушаалын зэрэглэл')
	amount = fields.Float(string='Үндсэн цалин')
	skills_allounce = fields.Float('Ур чадварын нэмэгдэл')
	sum_wage = fields.Float('Нэг цагийн дундаж цалин', digits=(
		16, 2), readonly=True, compute='_compute_sum_wage')
	eval_salary = fields.Float('Гүйцэтгэлийн урамшуулал')
	kpi_salary = fields.Float('kpi урамшуулал')

	@api.depends('skills_allounce', 'amount')
	def _compute_sum_wage(self):
		for obj in self:
			obj.sum_wage = obj.skills_allounce+obj.amount

	@api.onchange('name')
	def give_position_level(self):
		if self.name:
			if 'O' in self.name:
				self.position_level_sal = 'employee'
			elif 'P' in self.name:
				self.position_level_sal = 'specialist'
			elif 'S' in self.name:
				self.position_level_sal = 'supervisor'
			elif 'M' in self.name:
				self.position_level_sal = 'manager'
			elif 'G' in self.name:
				self.position_level_sal = 'general'
			elif 'D' in self.name:
				self.position_level_sal = 'director'


class SalaryLoan(models.Model):
	_name = 'salary.loan'
	_description = 'Salary Loan'
	_inherit = ['mail.thread']

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	employee_id = fields.Many2one(
		'hr.employee', string='Ажилтан', default=_default_employee)
	company_id = fields.Many2one(
		'res.company', string='Компани', related='employee_id.company_id')
	job_id = fields.Many2one(
		'hr.job', string='Албан тушаал', related='employee_id.job_id')
	date = fields.Date(string='Огноо',
					   default=fields.Date.context_today)
	state = fields.Selection([('draft', u'Ноорог'), ('sent', u'Илгээсэн'),
							 ('done', u'Батлагдсан')], string='Төлөв', default='draft')
	amount = fields.Float(string='Мөнгөн дүн')
	description = fields.Char(string='Тайлбар')
	reason = fields.Text(string='Үндэслэл')
	def action_send(self):
		self.write({'state': 'sent'})

	def action_draft(self):
		self.write({'state': 'draft'})

	def action_done(self):
		self.write({'state': 'done'})

class HrEmployeeContract(models.Model):
	_inherit = "hr.employee.contract"
		
	plus_salary = fields.Many2one('salary.level',string='Ур чадварын нэмэгдэл',store=True)
	salary_code = fields.Many2one('salary.level', string='Цалингийн шатлал',store=True)

	
class DisciplineDocument(models.Model):
	_inherit = "discipline.document"
		
	document = fields.Boolean(string='Ажилтны бичгээр өгсөн тайлбар')
	director_desc = fields.Boolean(string='Шууд удирдлагын тодорхойлолт')
	other_doc = fields.Boolean(string='Бусад баримт, нотолгоо')
	document_de = fields.Char(string='Desc')
	director_desc_de = fields.Char(string='Desc')
	other_doc_de = fields.Char(string='Desc')


	@api.onchange('document')
	def _onchange_document(self):
		if self.document==True:
			self.document_de = 'Тийм'
		else:
			self.document_de = 'Үгүй'

	@api.onchange('director_desc')
	def _onchange_director_desc(self):
		if self.director_desc==True:
			self.director_desc_de = 'Тийм'
		else:
			self.director_desc_de = 'Үгүй'
	
	@api.onchange('other_doc')
	def _onchange_other_doc(self):
		if self.other_doc==True:
			self.other_doc_de = 'Тийм'
		else:
			self.other_doc_de = 'Үгүй'


class HealthInsuranceHr(models.Model):
	_name = 'health.insurance.hr'
	_description = "health insurance Hr"
	_inherit = ['mail.thread']


	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	
	name = fields.Char(string='Нэр')
	date = fields.Date('Огноо')
	line_ids = fields.One2many('health.insurance.line.hr','parent_id',string='Ажилчид')
	employee_id = fields.Many2one('hr.employee','Ажилтан', default = _default_employee)
	department_id = fields.Many2one('hr.department','Хэлтэс')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	state = fields.Selection([('draft', u'Ноорог'), ('sent', u'Илгээсэн'), ('confirm', u'Хянасан'),('done_hr', u'Батлагдсан'),('done', u'Санхүү хүлээж авсан')], string='Төлөв', default='draft')
	
	def action_draft(self):
		return self.write({'state': 'draft'})
	
	def action_send(self):
		return self.write({'state': 'sent'})
	
	def action_confirm(self):
		self.write({'state': 'confirm'})

	def action_done(self):
		self.write({'state': 'done'})

	def action_done_hr(self):
		self.write({'state': 'done_hr'})

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id

	def create_line(self):
		if self.line_ids:
			self.line_ids.unlink()
		emp = self.env['hr.employee'].search([('employee_type','=','employee')])
		line_pool = self.env['health.insurance.line.hr']
		for item in emp:
			if item.health_percent !=0:
				data = line_pool.create({
					'identification_id': item.identification_id,
					'employee_id': item.id,
					'job_id':item.job_id.id,
					'health_percent':item.health_percent,
					'health_percent1':item.health_percent1,
					'parent_id':self.id
				})
			

class HealthInsuranceLine(models.Model):
	_name = 'health.insurance.line.hr'
	_description = "health.insurance Line HR"

	parent_id = fields.Many2one('health.insurance.hr','Parent', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	job_id = fields.Many2one('hr.job',string='Албан тушаал')
	identification_id = fields.Char(string='Код')
	health_percent = fields.Float(string='ЭМД хувь')
	health_percent1 = fields.Float(string='ЭМД хувь/гараас/')


class WellBeingHr(models.Model):
	_name = 'well.being.hr'
	_description = "Well Being Hr"
	_inherit = ['mail.thread']

	year = fields.Char('Жил')
	quart = fields.Selection([('1', u'1-р улирал'), ('2', u'2-р улирал'),('3', u'3-р улирал'),('4', u'4-р улирал')], string='Улирал')
	line_ids = fields.One2many('well.being.hr.line','parent_id',string='мөр')
   
   
class WellBeingHrLine(models.Model):
	_name = 'well.being.hr.line'
	_description = "Well Being Hr Line"

	parent_id = fields.Many2one('well.being.hr','Parent', ondelete='cascade')
	name = fields.Char('Үйл ажиллагаа')
	s_date = fields.Date('Огноо')
	emp_count = fields.Float('Нийт ажилтны тоо')
	count = fields.Float('Хамрагдсан ажилтны тоо')
	procent = fields.Float('Ирцийн хувь',compute='compute_procent',store=True)
	budget = fields.Float('Батлагдсан төсөв')
	performance =  fields.Float('Зарцуулсан төсөв')
	budget_procent = fields.Float('Төсөвийн гүйцэтгэлийн хувь',compute='compute_procent',store=True)
	description =  fields.Char('Тайлбар')
	ev = fields.Float('Сэтгэл ханамжийн үнэлгээ')

	@api.depends('emp_count','count','performance','budget')
	def compute_procent(self):
		for item in self:
			if item.emp_count and item.count:
				item.procent = item.count *100/item.emp_count
			else:
				item.procent = 0
			if item.budget and item.performance:
				item.budget_procent = item.performance *100/item.budget
			else:
				item.budget_procent = 0
			





class RoutingSlipHr(models.Model):
	_inherit = "routing.slip.hr"


	def action_next_stage(self):
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if self.num_employee_id and self.state_type == 'draft':
			self.send_chat_num_employee()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(
					next_flow_line_id,'routing_slip_id', self)
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
					if send_users:
						self.send_chat_next_users(
							send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(
						con_user.mapped('display_name'))
				raise UserError(
					u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)
			
	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_all_user_ids(self):
		for item in self:
			temp_users = []
			for w in item.flow_id.line_ids:
				temp = []
				try:
					temp = w._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id).ids
				except:
					pass
				temp_users+=temp
			item.confirm_all_user_ids = temp_users

	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			users = item.flow_line_next_id._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
			temp_users = users.ids if users else []
			item.confirm_user_ids = [(6,0,temp_users)]
			

			

class DynamicFlowLine(models.Model):
	_inherit = 'dynamic.flow.line'
	
	check_type = fields.Selection([('department', 'Хэлтэсийн менежер'), ('branch', 'Салбар менежер'), ('manager', 'Тухайн хүний менежер'),('job_manager', 'АБ шууд удирдлага')],string='Шалгах төрөл')
	# job дээр батлах удирдлага тохируулах шаардлага гарсан
	def _get_flow_users_syl(self, branch_id=False, department_id=False, user_id=False, job_id=False):
		ret_users = False
		if self.type in ['fixed', 'user']:
			ret_users = self.user_ids
		elif self.type == 'group':
			ret_users = self.group_id.users
		elif self.type == 'all':
			ret_users = self.user_ids + self.group_id.users
		if ret_users and self.check_type:
			if self.check_type == 'manager':
				if user_id:
					ret_users = ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
					if self.env.user.id in ret_users.ids:
						return self.env.user
				if not user_id:
					raise ValidationError(u'Та %s урсгалд батлах эрхгүй байна !' % self.name)
				if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
					raise ValidationError(
						u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна !' % (self.name, user_id.name))
				return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
			elif self.check_type == 'department':
				if not department_id:
					raise ValidationError(
						u'%s Урсгалд хэлтэс явуулаагүй байна %s %s %s' % (self.name, branch_id, department_id, user_id))
				if not ret_users.filtered(lambda r: r.id in department_id.manager_ids.ids):
					raise ValidationError(u'"%s" төлөвийн Хэлтэсийн менежер сонгогдоогүй байна' % self.name)
				return ret_users.filtered(lambda r: r.id in department_id.manager_ids.ids)
			elif self.check_type == 'job_manager':
				
				if not job_id:
					raise ValidationError(
						u'%s Урсгалд албан тушаал явуулаагүй байна %s %s %s' % (self.name, branch_id, job_id, user_id))
				if not ret_users.filtered(lambda r: r.id in job_id.interviewer_ids.ids):
					raise ValidationError(u'"%s" төлөвийн албан тушаал дээр удирдлага сонгогдоогүй байна' % self.name)
				return ret_users.filtered(lambda r: r.id in job_id.interviewer_ids.ids)
			print('\n\n======',self.check_type,ret_users,job_id.interviewer_ids.ids)
		return ret_users
	


class HrAllowance(models.Model):
	_inherit = 'hr.allowance'

	state = fields.Selection([('draft','Ноорог'), ('sent','Илгээсэн'),('confirm','хянасан'),('to_pay','Төлбөрийн хүсэлт үүссэн'),('done','Олгосон')], default='draft', string='Төлөв')


	def action_done(self):
		self.write({'state':'done'})
		

	def action_confirm(self):
		for obj in self:
			payment_pool=self.env['payment.request']
			payment_narration=self.env['payment.request.narration'].search([('name','=','Тэтгэмж')])
			payment_flow = self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request')], order='sequence',limit=1)
			data_id = payment_pool.create({
				'narration_id': payment_narration.id,
				'description' : obj.type,
				'department_id' : obj.employee_id.department_id.id,
				'amount' : obj.amount,
				'flow_id': payment_flow.id,
				'allowance_id': obj.id
			})
			self.request_id = data_id.id
		self.write({'state':'confirm'})
		
	def action_to_pay(self):
		self.write({'state':'to_pay'})
	