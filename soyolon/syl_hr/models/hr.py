# -*- coding: utf-8 -*-
from logging import Logger
from venv import logger
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


DATETIME_FORMAT = "%Y-%m-%d"
DATE_FORMAT = "%Y-%m-%d"


class HrEmployee(models.Model):
	_inherit = "hr.employee"

	@api.depends('sum_company_year')
	def _health_percent(self):
		for item in self:
			if item.sum_company_year > 3:
				item.health_percent = 100
				item.insuranse = False
			elif item.sum_company_year > 2 and item.sum_company_year <= 3:
				item.health_percent = 80
				item.insuranse = False
			elif item.sum_company_year > 1 and item.sum_company_year <= 2:
				item.health_percent = 50
				item.insuranse = False
			else:
				item.health_percent = 0

			if item.health_percent >0:
				item.health_percent1 = 100 - item.health_percent
				item.insuranse = False
			else:
				item.health_percent1 =0
				item.insuranse = True

	@api.onchange('engagement_in_company')
	def _compute_long_date(self):
		for item in self:
			if item.engagement_in_company:
				item.long_year_date = item.engagement_in_company

	@api.depends('engagement_in_company', 'long_year_ids')
	def _compute_long_year(self):
		long_pool = self.env['long.year.line']
		plus_months = 0
		for item in self:
			today = date.today()
			long_year_ids = long_pool.search(
				[('parent_id', '=', item.id)])
			if item.engagement_in_company:
				start_company_date = datetime.strptime(
					str(self.engagement_in_company), "%Y-%m-%d")
				today = today
				delta = relativedelta(today, start_company_date)
				total_day = delta.years*365 + delta.months*30 + delta.days
				item.total_long_year = u'%d жил %d сар %d хоног' % (
					total_day/365, (total_day % 365)/30, (total_day % 365) % 30)
				item.long_year = delta.years
				item.long_year_month = delta.months
				item.long_year_day = delta.days
			else:
				item.total_long_year = 0
			for year in item.long_year_ids:
				if year.start_date and year.end_date:
					start_date = datetime.strptime(
						str(year.start_date), "%Y-%m-%d")
					end_date = datetime.strptime(
						str(year.end_date), "%Y-%m-%d")
					duration = relativedelta(end_date, start_date)
					# dur = duration.years * 12 + duration.months
					dur = duration.years * 365 + duration.months * 30 + duration.days
					if year.plus_year == True:
						# plus_months += months+dur
						plus_months += total_day+dur
						item.total_long_year = u'%d жил %d сар %d хоног' % (
							plus_months/365, (plus_months % 365) / 30, (plus_months % 365) % 30)

						item.long_year = plus_months/365
						item.long_year_month = (plus_months % 365) / 30
						item.long_year_day = (plus_months % 365) % 30
					elif year.deduct_year == True:
						deduct_months = total_day-dur
						item.total_long_year = u'%d жил %d сар %d хоног' % (
							deduct_months/365, (deduct_months % 365) / 30, (deduct_months % 365) % 30)

						item.long_year = deduct_months/365
						item.long_year_month = (deduct_months % 365) / 30
						item.long_year_day = (deduct_months % 365) % 30

	def _line_item(self):
		line = self.env['resigned.reason.line'].search([('type','=','type1')])
		w = []
		for cc in line:
			vals = {
				'item_id': cc.id,
				'type': cc.type
			}
			w.append(vals)
		return w

	trainee_line_ids = fields.One2many(
		'trainee.emp.line', 'employee_id', 'line')
	
	line_ids = fields.One2many(
		'resigned.reason', 'parent_id', 'line', default=_line_item)

	satisfaction = fields.Selection([('1', 'Сэтгэл ханамжтай'), ('2', 'Дунд зэрэг'), (
		'3', 'Огт ханамжгүй')], string='Та авч байсан цалиндаа хэр сэтгэл ханамжтай байсан бэ?')
	used_skill = fields.Selection([('1', 'Бүрэн дүүрэн '), ('2', 'Дунд зэрэг'), ('3', 'Огт ашиглаагүй')],
								  string='Таны хийж байсан ажил таны мэдлэг, ур чадварыг хэр ашиглаж чадаж байсан вэ?')
	emp_offer = fields.Selection([('1', 'Сайн'), ('2', 'Дунд'), ('3', 'Муу')],
								 string='Байгууллага ажилтнуудынхаа санал бодлыг хэр хүлээж авч хэрэгжүүлдэг гэж та бодож байна?')
	social_support = fields.Selection([('1', 'Сайн'), ('2', 'Дунд'), ('3', 'Муу')],
									  string='Байгууллагаас хэрэгжүүлж буй нийгмийн хангамж, дэмжлэгт ямар үнэлэлт өгөх вэ?')
	advantage = fields.Text(
		'Соёолон интернэшнл” ХХК-д ажиллахад давуу тал нь юу байсан бэ?')
	weakness = fields.Text(
		'Соёолон интернэшнл” ХХК-д ажиллахад дутагдалтай тал нь юу байсан бэ?')
	career_growth = fields.Text(
		'Байгууллага доторх карьер өсөлтийн талаар саналаа үлдээнэ үү?')
	comment = fields.Text(
		'Цаашид ажил сайжруулах тухай үнэтэй санал сэтгэгдэлээ үлдээнэ үү?')
	identification_id = fields.Char(
		string='Identification No', readonly=True, tracking=True)
	clothes_size = fields.Char(string='Ажлын хувцасны хэмжээ')
	boots_size = fields.Char(string='Ажлын гуталны хэмжээ')
	long_year_date = fields.Date(
		"Удаан жил тооцох огноо", compute=_compute_long_date)
	long_year_ids = fields.One2many(
		'long.year.line', 'parent_id', string='Удаан жил')
	total_long_year = fields.Char(
		compute=_compute_long_year, method=True, type='char', string=u'Нийт удаан жил')
	long_year = fields.Char(compute=_compute_long_year, string='Жил', size=2)
	long_year_month = fields.Char(
		compute=_compute_long_year, string='Сар', size=2)
	long_year_day = fields.Char(
		compute=_compute_long_year, string='Өдөр', size=2)
	shift = fields.Selection([('office', 'Оффис'), ('d', '1-р ээлж'), ('e', '2-р ээлж'), ('f', '3-р ээлж'), ('g', '4-р ээлж'), ('k', '5-р ээлж'),('l', '6-р ээлж'), ('m', '7-р ээлж'), ('n', '8-р ээлж'), ('o', '9-р ээлж'), ('r', '10-р ээлж'), ('w', '11-р ээлж')], default='office', string='Ээлж')
	group = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')],  string='Бүлэг')
	shift_g = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')],  string='Бүлэг')
	health_percent = fields.Float(
		string='ЭМД хувь/Компаниас/', compute='_health_percent', store=True)
	health_percent1 = fields.Float(string='ЭМД хувь/Хувиасаа/',compute='_health_percent')

	insuranse = fields.Boolean(string='ГОД',compute='_health_percent')
	is_health = fields.Boolean(string='ЭМҮ-т хамрагдсан эсэх', default=False)
	health_sdate = fields.Date(string='Эхлэх огноо')
	health_edate = fields.Date(string='Дуусах огноо')
	loan_count = fields.Integer(
		string='Цалингийн урьдчилгаа', compute='_compute_loan_count')
	work_year_bef = fields.Date(
		string='Ажлын жил', compute='_compute_engagement_in_company', store=True)
	is_ita = fields.Boolean(string='ИТА эсэх', default=False)
	job_id= fields.Many2one('hr.job','Албан тушаал',domain="[('department_id','=',department_id)]")
	hr_p_id= fields.Many2one('hr.project','Төсөл')
	jname_id= fields.Many2one('job.name','Мэргэжил')
	emp_melen = fields.Char('emp melen',store=True,compute='_compute_last_name')
	reason_id1 = fields.Many2one('resigned.reason.line', 'Соёолон интернэшнл” ХХК-д ажиллахад давуу тал нь юу байсан бэ?')
	reason_id2 = fields.Many2one('resigned.reason.line', '“Соёолон интернэшнл” ХХК-д ажиллахад дутагдалтай тал нь юу байсан бэ?')
	reason_id3 = fields.Many2one('resigned.reason.line', 'Байгууллага доторх карьер өсөлтийн талаар саналаа үлдээнэ үү?')
	reason_id4 = fields.Many2one('resigned.reason.line', 'Цаашид ажил сайжруулах тухай үнэтэй санал сэтгэгдэлээ үлдээнэ үү?')

	rate_score2 = fields.Float('Нийт авсан үнэлгээ нэгтгэл',compute='_compute_total_score',store=True)
	is_doctor = fields.Boolean('Эмч эсэх', default=False)

	emp_type = fields.Selection([('type1', 'ХБ'), ('type2', 'Тэтгэвэр')], string='Ажилтны төрөл')
	
	@api.depends('trainee_line_ids.get_score')
	def _compute_total_score(self):
		for item in self:
			rate_score2=0
			if item.trainee_line_ids:
				score = sum(item.trainee_line_ids.mapped('score'))
				if score>0:
					rate_score2 = (sum(item.trainee_line_ids.mapped('get_score')) * 100)/score
			item.rate_score2=rate_score2
		
	@api.depends('last_name')
	def _compute_last_name(self):
		for item in self:
			if item.last_name:
				item.emp_melen = item.last_name[:1]
			else:
				item.emp_melen =''

	
	sum_uls_work_year = fields.Char(compute='_compute_sum_year', type='char', string=u'Нийт улсад ажилласан')
	sum_uls_work_year_syl = fields.Char(
		compute='_compute_sum_year', type='char', string=u'Нийт улсад ажилласан')
	sum_uls_year_syl = fields.Float(
		compute='_compute_sum_year', string=u'Нийт улсад ажилласан жил', digits=(3, 2))
	natural_uls_work_year_syl = fields.Char(
		compute='_compute_sum_year', type='char', string=u'Улсад ажилласан')
	
	@api.depends('before_month','before_worked_month','engagement_in_company','is_minikin')
	def _compute_sum_year(self):
		for emp in self:
			monthss=0
			months_minikin=0
			if emp.before_month:
				monthss =  emp.before_month
			if emp.before_worked_month:
				months_minikin = emp.before_worked_month
			
			start_date = datetime.strptime(str(emp.engagement_in_company), "%Y-%m-%d").date()
			today = date.today()
			delta = relativedelta(today, start_date)
			if emp.is_minikin == True:
				months_minikin += delta.years * 12 + delta.months
				emp.minikin_uls_work_year = u'%d жил %d сар' % (
					months_minikin/12, months_minikin % 12)
				emp.minikin_uls_year = months_minikin
				emp.natural_uls_work_year_syl = u'%d жил %d сар' % (
					monthss/12, monthss % 12)
				emp.natural_uls_year = monthss
			else:
				monthss += delta.years * 12 + delta.months
				emp.natural_uls_work_year_syl = u'%d жил %d сар' % (
					monthss/12, monthss % 12)
				emp.natural_uls_year = monthss
				emp.minikin_uls_work_year = u'%d жил %d сар' % (
					months_minikin/12, months_minikin % 12)
				emp.minikin_uls_year = months_minikin
			sum_monthss = months_minikin + monthss
			emp.sum_uls_year_syl =sum_monthss/12
			emp.sum_uls_work_year_syl = u'%d жил %d сар' % (
				sum_monthss/12, sum_monthss % 12)
			

	def _days_of_annualleave(self):
		for item in self:
			minimum_number = 0
			if item.emp_type == 'type1':
				minimum_number = 20
			else:
				minimum_number = 15
			normal_extra = 0
			minikin_extra = 0
			if item.sum_uls_year_syl > 5 and item.sum_uls_year_syl < 10:
				normal_extra = 3
				if item.minikin_uls_year/12 > 5 and item.minikin_uls_year/12 < 10:
					minikin_extra = 2
			if item.sum_uls_year_syl >= 10 and item.sum_uls_year_syl < 15:
				normal_extra = 5
				if item.minikin_uls_year/12 >= 10 and item.minikin_uls_year/12 < 15:
					minikin_extra = 2
			if item.sum_uls_year_syl >= 15 and item.sum_uls_year_syl < 20:
				normal_extra = 7
				if item.minikin_uls_year/12 >= 15 and item.minikin_uls_year/12 < 20:
					minikin_extra = 2
			if item.sum_uls_year_syl >= 20 and item.sum_uls_year_syl < 25:
				normal_extra = 9
				if item.minikin_uls_year/12 >= 20 and item.minikin_uls_year/12 < 25:
					minikin_extra = 3
			if item.sum_uls_year_syl >= 25 and item.sum_uls_year_syl < 31:
				normal_extra = 11
				if item.minikin_uls_year/12 >= 25 and item.minikin_uls_year/12 < 31:
					minikin_extra = 4
			if item.sum_uls_year_syl >= 31:
				normal_extra = 14
				if item.minikin_uls_year/12 >= 31:
					minikin_extra = 4
			item.days_of_annualleave = minimum_number+normal_extra + minikin_extra

	days_of_annualleave = fields.Char(
		compute=_days_of_annualleave, type='char', string=u'ЭА амрах хоног')
	
	@api.depends('engagement_in_company')
	def _compute_engagement_in_company(self):
		today = date.today()
		for item in self:
			if item.engagement_in_company:
				if item.engagement_in_company.year == today.year:
					item.work_year_bef = item.engagement_in_company.replace(
						today.year + 1)
				else:
					item.work_year_bef = item.engagement_in_company.replace(
						today.year)

	def _compute_loan_count(self):
		loan = self.env['salary.loan'].search([('employee_id', '=', self.id)])
		for emp in self:
			emp.loan_count = len(loan)

	def action_deduction_plan(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id(
			'syl_hr.salary_loan_action')
		action['domain'] = [('employee_id', '=', self.id)]
		action['res_id'] = self.id
		return action

	@api.model
	def create(self, vals):
		res = super(HrEmployee, self).create(vals)
		if res.company_id:
			if not self.identification_id:
				res.identification_id = self.env['ir.sequence'].with_context(
					force_company=int(res.company_id)).next_by_code('hr.employee', res.company_id.id)
		return res


# Notification


	def cron_work_year_notification(self):
		today = datetime.now().date()
		emp_pool = self.env['hr.employee'].sudo().search([('employee_type','in',('employee','student','trainee'))])
		for item in emp_pool:
			if item.work_year_bef:
				not_date = item.work_year_bef - timedelta(days=60)
				today = datetime.now().date()
				if today == not_date:
					res_model = self.env['ir.model.data'].search([
						('module', '=', 'hr'),
						('name', '=', 'group_hr_manager')])
					groups = self.env['res.groups'].search(
						[('id', '=', res_model.mapped('res_id'))], limit=1)
					base_url = self.env['ir.config_parameter'].sudo(
					).get_param('web.base.url')
					action_id = self.env.ref('hr.view_employee_form').id
					html = u'<b>Ажилтан.</b><br/>'
					html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.employee&action=%s>%s</a></b> ажилтны ажлын жил %s-нд дуусна!""" % (
						base_url, self.id, action_id, item.name, item.work_year_bef)
					for receiver in groups.users:
						self.env['res.users'].send_chat(
							html, receiver.partner_id)


class LongYearLine(models.Model):
	_name = "long.year.line"
	_description = "Long Year line"

	start_date = fields.Date(string='Эхлэх огноо')
	end_date = fields.Date(string='Дуусах огноо')
	total = fields.Char(string='Нийт хугацаа', store=True)
	plus_year = fields.Boolean(string='Нэмэх')
	deduct_year = fields.Boolean(string='Хасах')
	parent_id = fields.Many2one('hr.employee', string='Ажилтан')
	engagement_in_company = fields.Date(
		string='Ажилд орсон огноо', related='parent_id.engagement_in_company')

	@api.onchange('start_date', 'end_date')
	def compute_total(self):
		for line in self:
			total_duration = timedelta(days=0)
			if line.start_date and line.end_date:
				start_date = datetime.strptime(
					str(line.start_date), "%Y-%m-%d")
				end_date = datetime.strptime(str(line.end_date), "%Y-%m-%d")
				duration = relativedelta(end_date, start_date)
				total_duration += duration
				months = duration.years * 12 + duration.months
				line.total = u'%d жил %d сар %d өдөр' % (
					months/12, months % 12, duration.days)
			else:
				line.total = 0


class ResignedReason(models.Model):
	_name = 'resigned.reason'
	_description = ' resigned reason'

	parent_id = fields.Many2one('hr.employee', 'Parent')
	check = fields.Boolean('Сонголт')
	item_id = fields.Many2one('resigned.reason.line', 'Шалтгаан')
	type = fields.Selection([('type1', 'Ажлаас гарсан шалтгаан'), ('type2', 'Ажиллахад давуу тал нь юу байсан бэ?'), ('type3', 'Ажиллахад дутагдалтай тал нь юу байсан бэ?'), ('type4', 'Байгууллага доторх карьер өсөлтийн талаар саналаа үлдээнэ үү?'), ('type5', 'Цаашид ажил сайжруулах тухай үнэтэй санал сэтгэгдэлээ үлдээнэ үү?')], string='Төрөл',related=False)


class ResignedReasonLine(models.Model):
	_name = 'resigned.reason.line'
	_description = ' resigned reason line'

	name = fields.Char('Нэр')
	type = fields.Selection([('type1', 'Ажлаас гарсан шалтгаан'), ('type2', 'Ажиллахад давуу тал нь юу байсан бэ?'), ('type3', 'Ажиллахад дутагдалтай тал нь юу байсан бэ?'), ('type4', 'Байгууллага доторх карьер өсөлтийн талаар саналаа үлдээнэ үү?'), ('type5', 'Цаашид ажил сайжруулах тухай үнэтэй санал сэтгэгдэлээ үлдээнэ үү?')], string='Төрөл')

	company_id = fields.Many2one(
		'res.company', 'Компани', default=lambda self: self.env.user.company_id)




class HrProject(models.Model):
	_name = 'hr.project'
	_description = 'Hr Project'

	name = fields.Char(string='Төслийн нэр')
	company_id = fields.Many2one(
		'res.partner', default=lambda self: self.env.user.company_id, string='Компани')
	account_expense_id = fields.Many2one('account.account', 'Цалингийн зардлын данс')
	account_shi_expense_id = fields.Many2one('account.account', 'НДШ зардлын данс')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Аналитик')
	analytic_shi_account_id = fields.Many2one('account.analytic.account', 'НДШ аналитик')



class ComplaintDocument(models.Model):
	_inherit = 'complaint.document'

	complain_att_ids = fields.Many2many('ir.attachment', 'hr_complain_attach_rel', 'item_id', 'complain_attach_id',
										string='Хавсралт')



class TraineeEmpLine(models.Model):
	_name = 'trainee.emp.line'
	_description = 'Trainee Emp Line'

	employee_id = fields.Many2one('hr.employee', 'Emp')
	name = fields.Char('Үнэлэх талууд')
	score = fields.Float('Авбал зохих оноо')
	get_score = fields.Float('Авсан оноо')
	