# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from odoo.addons.mw_base.verbose_format import verbose_format
# from dateutil.relativedelta import relativedelta


DATETIME_FORMAT = "%Y-%m-%d"
DATE_FORMAT = "%Y-%m-%d"


class HrOrder(models.Model):
	_inherit = 'hr.order'

	salary_code = fields.Many2one('salary.level', string='Цалингийн шатлал')
	salary_tootsoh_day = fields.Float('Цалин олгох өдөр')
	is_salary_day = fields.Boolean('Үлдсэн амралтын хоногт цалин олгогдох эсэх?')
	is_rest = fields.Boolean('Үлдсэн амралтаа биеэр эдлэхгүй учир ээлжийн амралтын цалинг нэмэгдүүлэн тооцуулах')
	remain_date = fields.Date(string='Үлдсэн огноо')
	remain_end_date = fields.Date(string='Үлдсэн дуусах огноо')
	employee_id = fields.Many2one('hr.employee', 'Parent')
	insured_type_id = fields.Many2one('insured.type', string='Даатгуулагчийн төрөл')
	position_level = fields.Char(string='Албан тушаалын шатлал', related='order_job_id.job_degree')
	order_att_ids_done = fields.Many2many('ir.attachment', 'order_line_attach_rel', 'item_id', 'order_attach_id',
										  string='Батлагдсан тушаалын хавсралт')
	state = fields.Selection([('draft', u'Ноорог'), ('send', u'Илгээсэн'), ('approve', u'Хянасан'), ('done', u'Баталсан'), ('sent', u'Ажилтанд илгээх'), ('canceled', u'Цуцалсан')], 'Төлөв', default='draft', tracking=True)
	reward = fields.Char('Шагналын дүн')
	trial = fields.Char('Туршилтын сар')
	train_name = fields.Char('Сургалтын нэр')
	train_cost = fields.Float('Сургалтын дүн')
	train_cost_ch = fields.Char('Сургалтын дүн /хэвлэх/')
	train_cost_str = fields.Char('Сургалтын дүн /үсгээр/', compute='_amount_train_str')
	article = fields.Char('ХДЖ-ын заалт', tracking=True)
	applied_date = fields.Date('Өргөдөл өгсөн огноо')
	hr_emp_id = fields.Many2one('hr.employee', string='Хүний нөөцийн ахлах мэргэжилтэн')
	doc_employee_id = fields.Many2one('hr.employee', string='Хүний нөөцийн ахлах мэргэжилтэн', tracking=True)
	manager_emp_id = fields.Many2one('hr.employee', string='Удирдлага')
	con_day = fields.Float(string='Ногдох хоног', readonly=False,store=True, digits=(3, 2),compute=False)
	vac_days = fields.Char('Нийт амрах хоног', related='order_employee_id.days_of_annualleave')
	work_location_id = fields.Many2one('hr.work.location', string='Ажлын байршил')

	@api.onchange('order_employee_id')
	def _onchange_order_employee_id(self):
		if self.order_employee_id:
			contract_pool = self.env['hr.employee.contract'].search(
				[('employee_id', '=', self.order_employee_id.id)], limit=1)
			self.contract_number = contract_pool.number
			self.in_company_date = self.order_employee_id.engagement_in_company
			self.work_location_id = self.order_employee_id.work_location_id.id
			self.before_shift_vac_date = self.order_employee_id.before_shift_vac_date
			self.count_day = self.order_employee_id.days_of_annualleave
			self.this_vac_date = self.order_employee_id.before_year_shipt_leave_date
			self.order_department_id = self.order_employee_id.department_id.id
			self.order_job_id = self.order_employee_id.job_id.id
			self.order_name_melen = self.order_employee_id.last_name[:1]
			self.salary_tootsoh_day = self.order_employee_id.days_of_annualleave

	@api.onchange('salary_tootsoh_day')
	def onchange_salary_tootsoh_day(self):
		if self.salary_tootsoh_day and self.starttime:
			day = datetime.strptime(str(self.starttime), "%Y-%m-%d")
			days_to_add = self.salary_tootsoh_day
			while days_to_add > 0:
				day += timedelta(days=1)
				if day.weekday() < 5:
					days_to_add -= 1

			self.endtime = day.strftime("%Y-%m-%d")

	@api.depends('remain_date', 'remain_end_date')
	def _compute_vac_days(self):
		for item in self:
			if item.remain_date and item.remain_end_date:
				remain_date = datetime.strptime(str(item.remain_date), DATE_FORMAT)
				remain_end_date = datetime.strptime(str(item.remain_end_date), DATE_FORMAT)
				days_count=0
				for single_date in item.daterange(remain_date, remain_end_date):
					days_count += 1 if single_date.weekday() < 5 else 0
					item.end_days = days_count
			else:
				item.end_days = ''


	@api.onchange('applied_date')
	def onchange_applied_date(self):
		if self.applied_date:
			start_date = datetime.strptime(str(self.applied_date), DATE_FORMAT)
			self.year = str(self.applied_date)[:4]
			self.month = start_date.month
			self.day = start_date.day

	@api.depends('train_cost')
	def _amount_train_str(self):
		for line in self:
			if line.train_cost:
				line.train_cost_str = verbose_format(abs(line.train_cost))
			else:
				line.train_cost_str = ''

	@api.onchange('train_cost')
	def onchange_train_cost(self):
		if self.train_cost:
			self.train_cost_ch = '{0:,.2f}'.format(
				self.train_cost).split('.')[0]

	@api.depends('starttime', 'endtime')
	def _compute_day(self):
		for item in self:
			st_d = None
			en_d = None
			day_hl=0
			if item.starttime and item.endtime:
				holidays = self.env['hr.public.holiday'].search([('days_date','>=',item.starttime),('days_date','<=',item.endtime)])
				if holidays:
					for hh in holidays:
						day_hl += 1 if hh.days_date.weekday() < 5 else 0
				st_d = datetime.strptime(
					str(item.starttime), DATETIME_FORMAT).date()
				en_d = datetime.strptime(
					str(item.endtime), DATETIME_FORMAT).date()
				days_count = 0
				day_too = 0
				for single_date in item.daterange(st_d, en_d):
					days_count += 1 if single_date.weekday() < 5 else 0
					day_too = days_count
				item.start_days = day_too - day_hl
			else:
				item.start_days = 0
	# Үндсэн цалин шинэчлэх

	def create_hr_contract(self):
		contract_id = False
		if self.is_many_emp == True:
			for item in self.order_lines:
				if item.employee_id:
					employee = self.env['hr.contract'].search(
						[('employee_id', '=', item.employee_id.id)], limit=1)
					if employee:
						# employee.update({'wage': item.wage_change})
						item.contract_id = employee.id
					else:
						vals = {
							'employee_id': item.employee_id.id,
							'name': item.employee_id.identification_id,
							 'wage': self.salary_code.amount,
						}
						contract_id = self.env['hr.contract'].create(vals)
						item.contract_id = contract_id.id
		else:
			if self.order_employee_id:
				employee = self.env['hr.contract'].search(
					[('employee_id', '=', self.order_employee_id.id)], limit=1)
				if employee:
					employee.update({'level_id': self.salary_code.id})
					employee.update({'wage': self.salary_code.amount})
					self.contract_id = employee.id
				else:
					vals = {
						'employee_id': self.order_employee_id.id,
						'name': self.order_employee_id.identification_id,
						'wage': self.wage,
						'level_id': self.salary_code.id,
						'wage': self.salary_code.amount,
					}
					contract_id = self.env['hr.contract'].create(vals)
					self.contract_id = contract_id.id

	def action_draft(self):
		return self.write({'state': 'draft'})

	def action_send_email(self):
		for ii in self.order_att_ids_done:
			if self.order_employee_id:
				html = u'<b> "%s" Танд өдрийн батлагдсан тушаал ирсэн байна</b><br/>' % (date.today()-timedelta(days=1))
				subject_mail = u'Батлагдсан тушаал'
				mail_obj = self.env['mail.mail'].sudo().create({
				'email_from': self.company_id.email,
				'email_to': self.order_employee_id.private_email,
				'subject': subject_mail,
				'body_html': '%s' % html,
				'attachment_ids':[ii.id]
				})
		return self.write({'state': 'sent'})

# Батлах товчоор ажилтны мэдээлэл рүү шинэчлэлт хийгдэнэ
	
	def action_done(self):
		# Үндсэн ажилтан
		if self.type == 'type1':
			self.update_type1()

		# Туршилтын ажилтан
		if self.type == 'type2':
			if self.is_many_emp == True:
				for item in self.order_lines:
					item.employee_id.update({'employee_type': 'trainee'})
					item.employee_id.update({'job_id': item.job_id.id})
					item.employee_id.update(
						{'department_id': item.department_id.id})
					item.employee_id.update(
						{'engagement_in_company': self.starttime})
			else:
				self.order_employee_id.update({'employee_type': 'trainee'})
				self.order_employee_id.update({'job_id': self.order_job_id.id})
				self.order_employee_id.update(
					{'department_id': self.order_department_id.id})
				self.order_employee_id.update(
					{'engagement_in_company': self.starttime})

		# Ажлын байр өөрчлөх тухай
		if self.type == 'type4':
			self.action_send_email_all()
			if self.is_many_emp == True:
				for item in self.order_lines:
					item.employee_id.update({'job_id': item.new_job_id.id})
					item.employee_id.update(
						{'department_id': item.new_department_id.id})
			else:
				self.order_employee_id.update({'job_id': self.job_id_after.id})
				self.order_employee_id.update(
					{'department_id': self.department_id_after.id})

		# Ажлаас гарсан төлөвт орох
		if self.type == 'type6':
			self.update_type6()

		# Жирэмсний чөлөө авах тохиолдол
		if self.type == 'type7':
			if self.is_many_emp == True:
				for item in self.order_lines:
					item.employee_id.update(
						{'employee_type': 'pregnant_leave'})
			else:
				self.order_employee_id.update(
					{'employee_type': 'pregnant_leave'})

		# Хүүхэд асрах чөлөө авах тухай
		if self.type == 'type8':
			if self.is_many_emp == True:
				for item in self.order_lines:
					item.employee_id.update({'employee_type': 'maternity'})
			else:
				self.order_employee_id.update({'employee_type': 'maternity'})

		# Урт хугацааны чөлөө
		if self.type == 'type9':
			if self.is_many_emp == True:
				for item in self.order_lines:
					item.employee_id.update({'employee_type': 'longleave'})
			else:
				self.order_employee_id.update({'employee_type': 'longleave'})
		# Ээлжийн амралтын тушаалаас цагийн хүсэлт үүсгэх
		if self.type == 'type13':
			leave_pool = self.env['hr.leave.mw']
			type = self.env['hr.shift.time'].search(
				[('is_work', '=', 'vacation')], limit=1)
			leave_data_id = leave_pool.create({
				'department_id': self.order_department_id.id,
				'employee_id': self.order_employee_id.id,
				'work_location_id': self.order_employee_id.work_location_id.id,
				'shift_plan_id': type.id,
				'flow_id': 4,
				'date_from': self.starttime,
				'date_to': self.endtime,
				'vac_days': self.start_days,
				'time_from': 8,
				'time_to': 17,
			})
			if self.remain_date:
				leave_pool = self.env['hr.leave.mw']
				type = self.env['hr.shift.time'].search(
					[('is_work', '=', 'vacation')], limit=1)
				leave_data_id = leave_pool.create({
					'department_id': self.order_department_id.id,
					'employee_id': self.order_employee_id.id,
					'work_location_id': self.order_employee_id.work_location_id.id,
					'shift_plan_id': type.id,
					'flow_id': 4,
					'date_from': self.remain_date,
					'date_to': self.remain_end_date,
					'vac_days': self.start_days,
					'time_from': 8,
					'time_to': 17,
				})
		return self.write({'state': 'done'})
	def update_type1(self):
		history_line_id = self.env['hr.company.history']
		if self.is_many_emp == True:
				for item in self.order_lines:
					item.employee_id.update({'employee_type': 'employee'})
					item.employee_id.update({'job_id': item.job_id.id})
					item.employee_id.update({'department_id': item.department_id.id})
		else:
			history_line_id = history_line_id.create({
				'employee_id': self.order_employee_id.id,
				'pre_value': dict(self.order_employee_id._fields['employee_type'].selection).get(self.order_employee_id.employee_type),
				'type': 'type',
				'order': self.id,
				'date': self.starttime,
			})
			self.order_employee_id.update({'employee_type': 'employee'})
			if self.job_id_after:
				self.order_employee_id.update({'job_id': self.job_id_after.id})
			if self.department_id_after:
				self.order_employee_id.update({'department_id': self.department_id_after.id})
			history_line_id = history_line_id.update({
				'employee_id': self.order_employee_id.id,
				'new_value': dict(self.order_employee_id._fields['employee_type'].selection).get(self.order_employee_id.employee_type),
			})

	def vacation_date_notification(self):
		today = datetime.now().date()
		emp_pool = self.env['hr.order'].sudo().search([])
		for item in emp_pool:
			if item.remain_date:
				not_date = item.remain_date - timedelta(days=20)
				today = datetime.now().date()
				if today == not_date:
					res_model = self.env['ir.model.data'].search([
						('module', '=', 'hr'),
						('name', '=', 'group_hr_manager')])
					groups = self.env['res.groups'].search(
						[('id', '=', res_model.mapped('res_id'))], limit=1)
					base_url = self.env['ir.config_parameter'].sudo(
					).get_param('web.base.url')
					action_id = self.env.ref(
						'mw_hr_order.view_hr_order_form').id
					html = u'<b>Ажилтан.</b><br/>'
					html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.order&action=%s>%s</a></b> ажилтны ээлжийн амралтаа авахад 20 хоног үлдлээ!""" % (
						base_url, self.id, action_id, item.employee_id.name)
					for receiver in groups.users:
						self.env['res.users'].send_chat(
							html, receiver.partner_id)

	def action_send_email_all(self):
		partner_obj = self.env['hr.employee'].search([('employee_type','=','employee')]).mapped('partner_id')
		html = u'<b>Сайн байцгаана уу?</b><br/>'
		html += u"""<b><a target="_blank"></a></b>%s.%s нь %s-д  %s өдрөөс эхлэн албан тушаал
			дэвшин ажиллах болсныг дуулгахад таатай байна.
			<br/>%s.%s шинэ албан тушаалд дэвшин ажиллаж байгаад нь баяр хүргэж, цаашдын
			ажилд нь улам их амжилт хүсье.
			<br/>Хүндэтгэсэн,
			<br/>%s.%s """% (self.order_name_melen, self.order_employee_id.name, self.job_id_after.name, self.starttime,self.order_name_melen, self.order_employee_id.name,self.emp_name_melen,self.employee_id.name)
		for item in partner_obj:
			if item.email and item.id != self.order_employee_id.partner_id.id:
				self.send_emails('Баяр хүргэе.', html,item.email)
				
	def send_emails(self, subject, body, partner_mail):
		mail_obj = self.env['mail.mail'].sudo().create({
			'email_from': self.env.user.email_formatted,
			'email_to': partner_mail,
			'subject': subject,
			'body_html': '%s' % body
		})
		mail_obj.send()

class HrOrderType(models.Model):
	_inherit = 'hr.order.type'

	type = fields.Selection([('type1', u'Ажилд авах - Үндсэн ажилтан төлөв'),
							 ('type2', u'Ажилд авах - Туршилтын ажилтан төлөв'),
							 ('type3', u'Үндсэн цалин өөрчлөгдөх'),
							 ('type4', u'Албан тушаал өөрчлөх'),
							 ('type5', u'Шагнал'),
							 ('type6', u'Ажлаас чөлөөлөх - Ажлаас гарсан төлөв'),
							 ('type7', u'Жирэмсний амралт - Жирэмсний чөлөө'),
							 ('type8', u'Хүүхэд асрах чөлөө - Хүүхэд асрах чөлөө чөлөө'),
							 ('type9', u'Чөлөө олгох - Урт хугацааны чөлөө'),
							 ('type10', u'Сахилга'),
							 ('type11', u'Тэтгэмж'),
							 ('type12', u'Бусад'),
							 ('type13', u'Ээлжийн амралт'),
							 ('type14', u'Ээлжийн амралт олговор олгох'),
							 ('type15', u'Сургалтанд хамруулах тухай'),
							 ], u'Type', tracking=True, required=True)
