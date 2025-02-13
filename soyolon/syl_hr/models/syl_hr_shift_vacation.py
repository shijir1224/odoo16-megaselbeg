# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


DATETIME_FORMAT = "%Y-%m-%d"
DATE_FORMAT = "%Y-%m-%d"


class ShiftVacationSchedule(models.Model):
	_inherit = "shift.vacation.schedule"

	type = fields.Selection([('plan', 'Төлөвлөгөөнөөс татах'), ('request', 'Хүсэлтээс татах'), (
		'other', 'Ажилтны мэдээллээс'), ('order', 'Тушаалаас татах')], 'Хаанаас татах сонгоно уу', required=True, default='draft', tracking=True)

	def create_schedule_line(self):
		line_pool = self.env['shift.vacation.schedule.line']
		if self.line_ids:
			self.line_ids.unlink()
		schedule_id = self.id
		if self.type == 'plan':
			query = """SELECT 
					department_id,
					job_id,
					employee_id,
					in_company_date,
					before_shift_vac_date,
					payslip_date,
					count_day,
					state
					FROM shift_vacation_plan_line
					WHERE payslip_date>='%s' and payslip_date<='%s' and state='done' 
					""" % (self.start_date, self.end_date)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
		elif self.type == 'request':
			query = """SELECT 
				department_id,
				job_id,
				employee_id,
				in_company_date,
				before_shift_vac_date,
				payslip_date,
				company_id,
				con_day
				FROM shift_vacation_request shr
				WHERE payslip_date>='%s' and payslip_date<='%s' and state_type='done'  and company_id=%s
				""" % (self.start_date, self.end_date, self.company_id.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
			minikin = {}
		elif self.type == 'order':
			query = """SELECT 
				order_department_id,
				order_job_id,
				order_employee_id,
				in_company_date,
				starttime,
				endtime,
				company_id,
				id
				FROM hr_order
				WHERE starttime>='%s' and starttime<='%s' and state='done' and company_id=%s
				""" % (self.start_date, self.end_date, self.company_id.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
			minikin = {}
			print('\n\n=================>\n\n', records)
		else:
			query = """SELECT 
				department_id,
				job_id,
				id,
				engagement_in_company,
				name,
				before_year_shipt_leave_date,
				company_id
				FROM hr_employee hr
				WHERE before_year_shipt_leave_date>='%s' and before_year_shipt_leave_date<='%s'  and company_id=%s
				""" % (self.start_date, self.end_date, self.company_id.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
		minikin = {}
		for record in records:
			employee_pool = self.env['hr.employee'].browse(record[2])
			count_day = 0
			if self.type == 'plan':
				count_day = record[6]
			elif self.type == 'request':
				count_day = str(record[7])[:4]

			else:
				count_day = employee_pool.days_of_annualleave

			if employee_pool.is_minikin == True:
				minikin = 'Хэвийн'
			else:
				minikin = 'Хэвийн бус'
			if self.type == 'order':
				order_pool = self.env['hr.order'].search(
					[('type', '=', 'type14'), ('id', '=', record[7])])
				for order in order_pool:
					line_data_id = line_pool.create({
						'department_id': order.order_department_id.id,
						'job_id': order.order_job_id.id,
						'employee_id': order.order_employee_id.id,
						'schedule_id': schedule_id,
						'in_company_date': order.in_company_date,
						'uls_year': order.order_employee_id.sum_uls_work_year_syl,
						'count_day': order.start_days,
						'before_shift_vac_date': order.order_employee_id.before_shift_vac_date,
						'is_minikin': order.order_employee_id.is_minikin,
						'payslip_date': order.starttime,
					})
			else:
				line_data_id = line_pool.create({
					'department_id': record[0],
					'job_id': record[1],
					'employee_id': record[2],
					'schedule_id': schedule_id,
					'in_company_date': record[3],
					'before_shift_vac_date': employee_pool.before_shift_vac_date,
					'payslip_date': record[5],
					'is_minikin': minikin,
					'uls_year': employee_pool.sum_uls_work_year_syl,
					'count_day': count_day,
				})
		return True


class ShiftVacationRequest(models.Model):
	_inherit = "shift.vacation.request"

	history_line_ids = fields.Many2many('shift.vacation.request', u'Өмнөх түүх', compute="before_contracts_view")
	vac_days = fields.Float('Амрах хоног')
	is_half = fields.Boolean('Үлдсэн амралтаа биеэр эдлэх эсэх')
	is_half_rest = fields.Boolean('Биеэр эдлэхдээ хувааж авах эсэх')
	is_rest = fields.Boolean('Үлдсэн амралтаа биеэр эдлэхгүй учир ээлжийн амралтын цалинг нэмэгдүүлэн тооцуулах')
	is_get_salary = fields.Boolean('Өөрийн хүсэлтээр цалин тооцуулах')
	l_startdate = fields.Date('Үлдсэн эхлэх огноо')
	l_enddate = fields.Date('Үлдсэн дуусах огноо')
	remain_days = fields.Float('Үлдсэн амрах хоног', compute='_compute_vac_days')
	work_year = fields.Date(string='Компанид ажилд орсон огноо', related='employee_id.engagement_in_company')
	work_year_bef = fields.Date(string='Ажлын жил')
	work_year_af = fields.Date(string='Аж')
	employee_id = fields.Many2one('hr.employee', string='Ажилтан')

	@api.depends('startdate', 'enddate')
	def _compute_day(self):
		st_d = 0
		en_d = 0
		day_hl=0
		for item in self:
			if item.startdate and item.enddate:
				holidays = self.env['hr.public.holiday'].search([('days_date','>=',item.startdate),('days_date','<=',item.enddate)])
				if holidays:
					for hh in holidays:
						day_hl += 1 if hh.days_date.weekday() < 5 else 0
				st_d = datetime.strptime(
					str(item.startdate), DATETIME_FORMAT).date()
				en_d = datetime.strptime(
					str(item.enddate), DATETIME_FORMAT).date()
				days_count = 0
				day_too = 0
				for single_date in item.daterange(st_d, en_d):
					days_count += 1 if single_date.weekday() < 5 else 0
					day_too = days_count
				item.days = day_too - day_hl

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.vac_days = self.employee_id.days_of_annualleave

	@api.onchange('work_year_bef')
	def onchange_work_year_bef(self):
		if self.work_year_bef:
			self.l_enddate = self.work_year_bef

	@api.depends('employee_id')
	def before_contracts_view(self):
		for item in self:
			before_contracts = item.env['shift.vacation.request'].search(
				[('employee_id', '=', item.employee_id.id)])
			item.history_line_ids = before_contracts.ids

	@api.depends('days', 'vac_days')
	def _compute_vac_days(self):
		for item in self:
			rr = item.vac_days - item.days
			if rr > 0:
				item.remain_days = rr
			else:
				item.remain_days = 0

	
class ShiftVacationPlan(models.Model):
	_inherit = "shift.vacation.plan"


	def execute_query(self):
		query = """SELECT 
			department_id,
			job_id,
			employee_id,
			in_company_date,
			before_shift_vac_date,
			payslip_date,
			days,
			startdate,
			enddate
			FROM shift_vacation_request
			WHERE year='%s' and state_type='done'
			""" % (self.year)
		self.env.cr.execute(query)
		return self.env.cr.fetchall()
	
	def create_plan_line(self):
		line_pool = self.env['shift.vacation.plan.line']
		if self.line_ids:
			self.line_ids.unlink()
		records = self.execute_query()
		for record in records:
			employee_pool = self.env['hr.employee'].browse(record[2])
			line_data_id = line_pool.create({
				'department_id': record[0],
				'job_id': record[1],
				'employee_id': record[2],
				'plan_id': self.id,
				'in_company_date': record[3],
				'before_shift_vac_date': record[4],
				'payslip_date': record[5],
				'uls_year': employee_pool.sum_uls_work_year_syl,
				'count_day': employee_pool.days_of_annualleave,
				'days': record[6],
				'startdate': record[7],
				'enddate': record[8],
			})
		return True
	
class ShiftVacationPlanLine(models.Model):
	_inherit = "shift.vacation.plan.line"

	days = fields.Float('Биеэр эдлэх хоног', digits=(2, 1))
	startdate = fields.Date(string='Эхлэх огноо')
	enddate = fields.Date(string='Дуусах огноо')
