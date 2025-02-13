from odoo import  api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

DATE_FORMAT = "%Y-%m-%d"


class DailyReport(models.Model):
	_name ='hse.daily.report'
	_description = 'Hse Daily Report'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.model
	def create(self, vals):
		# value = self.search([
        #     ('branch_id', '=', vals['branch_id']), 
        #     ('year_month','=', vals['year_month'])])
		# if value:
		# 	raise UserError(u'Анхааруулга!!! Сонгосон Төсөл, сонгосон он/сард бүртгэл байгаа тул дахин үүсгэх боломжгүй.')
		res = super(DailyReport, self).create(vals)
		return res


	@api.model
	def name_get(self):
		result = []
		for obj in self:
			if obj.branch_id and obj.year_month:
				result.append((obj.id, obj.branch_id.name + ' (' + obj.year_month + ')'))
			else:
				raise UserError(_('Төсөл болон Он сар сонгоно уу!!!')) 
		return result

	def _get_year_month(self):
		year_list = []
		current_year = datetime.now().year
		current_month = datetime.now().month
		for j in range(current_month, 0, -1):
			year_month = str(current_year) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(12, 0, -1):
			year_month = str(current_year - 1) + ("/" if j > 9 else "/0") + str(j)
			year_list.append((year_month, year_month))
		for j in range(2, 7, 1):
			year_month = str(current_year - j) + "/12"
			year_list.append((year_month, year_month))
		return year_list


	def _compute_name(self):
		for obj in self:
			if obj.branch_id and obj.year_month:
				obj.name = obj.branch_id.name + ' '+ obj.year_month + ' сарын мэдээ'
			else:
				obj.name='Сарын мэдээ'

	name = fields.Char(string='Нэр', readonly=True, tracking=True, compute=_compute_name)
	state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
	wdwltinjury = fields.Char(string='Хөдөлмөрийн чадвар түр алдалтгүй ажилласан хоног', readonly=True, states={'draft':[('readonly',False)]})
	daily_report_line = fields.One2many('hse.daily.report.line', 'daily_id', 'Daily report line', readonly=True, states={'draft':[('readonly',False)]})
	start_date = fields.Date('Эхлэх огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	end_date = fields.Date('Дуусах огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Төсөл', tracking=True, required=False, readonly=True, domain="[('company_id','=',company_id)]", states={'draft':[('readonly',False)]})
	year_month = fields.Selection(string='Он/Сар', selection=_get_year_month, required=True, tracking=True, readonly=True, states={'draft':[('readonly',False)]})

	def action_to_draft(self):
		self.write({'state': 'draft'})
	
	def action_to_done(self):
		self.write({'state': 'done'})

	def unlink(self):
		for item in self:
			if item.state !='draft':
				raise UserError(_('Ноорог төлөв биш байна.!!!'))
		return super(DailyReport, self).unlink()
	
	def action_to_date(self):
		if self.daily_report_line:
			raise UserError(u'Анхааруулга!!! Мөрөн дээр бүртгэл байгаа тул өөрчлөх боломжгүй.')
		else:
			line_data_pool =  self.env['hse.daily.report.line']
			if self.daily_report_line:
				self.daily_report_line.unlink()
			from_dt = datetime.strptime(str(self.start_date), DATE_FORMAT).date()
			to_dt = datetime.strptime(str(self.end_date), DATE_FORMAT).date()
			step = relativedelta(days=1)
			for obj in self:
				while from_dt <= to_dt:
					line_line_conf = line_data_pool.create({
						'daily_id':obj.id,
						'date':from_dt,
					})
					from_dt += step
	
	def update_all(self):
		for line in self.daily_report_line:
			line.update_daily_report()

class HseDailyReportLine(models.Model):
	_name = 'hse.daily.report.line'
	_description = 'Daily report line'


	daily_id = fields.Many2one('hse.daily.report', 'Daily_id', ondelete='cascade', readonly=True)
	branch_id = fields.Many2one(related='daily_id.branch_id', string='Төсөл', readonly=True, store=True)
	date = fields.Date('Хугацаа', required=True, default=fields.Date.context_today)
	ita_count = fields.Integer(string='ИТА' , readonly=True)
	employee_count = fields.Integer(string='Ажилтан', readonly=True)
	gereet_employee_count = fields.Integer(string='Гэрээт')
	guest_count = fields.Integer(string='Зочин/Төв оффис/', readonly=True)
	total_employee = fields.Integer(string='Нийт', readonly=True)
	uildver_osol = fields.Integer(string='Үйлдвэрлэлийн осол' , readonly=True)
	osol_duhsun = fields.Integer(string='Осол дөхсөн тохиолдол', readonly=True)
	first_help = fields.Integer(string='Анхны тусламж авсан', readonly=True, default=0)
	hosp_help = fields.Integer(string='Эмнэлэгийн тусламж авсан', readonly=True)
	timed_damage = fields.Integer(string='Хугацаа алдсан гэмтэл', readonly=True, default=0)
	property_damage = fields.Integer(string='Өмчийн эвдрэл гэмтэл', default=0, readonly=True)
	leakage = fields.Integer(string='Асгаралт', default=0, readonly=True)
	fire_incident = fields.Integer(string='Гал түймрийн тохиолдол', readonly=True)
	urid_zaavar = fields.Integer(string='Урьдчилсан зааварчилгаа', readonly=True)
	first_zaavar = fields.Integer(string='Анхан шатны зааварчилгаа', readonly=True)
	guest_zaavar = fields.Integer(string='Зочны зааварчилгаа', readonly=True)
	regularly_zaavar = fields.Integer(string='Ээлжит зааварчилгаа', readonly=True)
	not_regularly_zaavar = fields.Integer(string='Ээлжит бус зааварчилгаа', readonly=True)
	high_risk = fields.Integer(string='Өндөр эрсдэлтэй ажлын зөвшөөрөл', readonly=True)
	risk_assessment = fields.Integer(string='Болзошгүй эрсдлийн үнэлгээ', readonly=True)
	workplace_inspection = fields.Integer(string='Ажлын байрны үзлэг', readonly=True)
	vehicle_check = fields.Integer(string='Тээврийн хэрэгслийн хяналт')
	field_instruction = fields.Integer(string='Талбайн зааварчилгаа')
	hse_conf = fields.Integer(string='ХАБЭА-н уулзалт')
	noticed = fields.Integer(string='Мэдэгдэл өгсөн')
	work_stopped = fields.Integer(string='Ажил зогсоосон')
	other = fields.Char(string='Бусад')

	urid_zaavar_sum = fields.Integer(string='Урьдчилсан зааварчилгаа', readonly=True)
	first_zaavar_sum = fields.Integer(string='Анхан шатны зааварчилгаа', readonly=True)
	guest_zaavar_sum = fields.Integer(string='Зочны зааварчилгаа', readonly=True)
	regularly_zaavar_sum = fields.Integer(string='Ээлжит зааварчилгаа', readonly=True)
	not_regularly_zaavar_sum = fields.Integer(string='Ээлжит бус зааварчилгаа', readonly=True)

	attachment_ids = fields.Many2many('ir.attachment', 'daily_report_line_rel', 'daily_line_id', 'attachment_id', string=u'Хавсралт', tracking=True)

	def update_daily_report(self):
		time_obj = self.env['hr.timetable.line.line']
		emp_obj = self.env['hr.employee']
		injury_obj = self.env['hse.injury.entry']
		ambulance_line_obj = self.env['hse.ambulance.line']
		fire_obj = self.env['hse.fire']
		training_obj = self.env['hse.employee.training']
		training_line_obj = self.env['hse.employee.training.line']
		guest_line_obj = self.env['hse.partner.training.line']
		risk_asseesstment_obj = self.env['hse.risk.assessment.workplace']
		workplace_obj = self.env['hse.workplace.inspection']
		preliminary_obj = sum(self.env['preliminary.notice'].sudo().search([('date','=',self.date)]))
		warning_obj = sum(self.env['hse.warning.page'].sudo().search([('date','=',self.date)]))
		for item in self:
			if item.date:
				item.ita_count = len(time_obj.sudo().search([
					('date','=',item.date),
					('employee_id.is_ita','=',True),
					('is_work_schedule','in',['day','night']),
					('hour_to_work','!=',0),
					('worked_hour','!=',0),
					# ('compute_sum_all_time','!=',0),
					# ('shift_plan_id.is_work','not in',['day','night','pay_leave','in','out','out_work','over_day','over_night','holiday_work','online_work']),
					('shift_plan_id.is_work','not in',['sick','leave','sickness','none','resigned']),
					('parent_id.department_id.branch_id','=',self.branch_id.id),
				]).ids)
				item.employee_count = len(time_obj.sudo().search([
					('date','=',item.date),
					('employee_id.is_ita','=',False),
					('is_work_schedule','in',['day','night']),
					('hour_to_work','!=',0),
					('worked_hour','!=',0),
					# ('compute_sum_all_time','!=',0),
					# ('shift_plan_id.is_work','not in',['day','night','pay_leave','in','out','out_work','over_day','over_night','holiday_work','online_work']),
					('shift_plan_id.is_work','not in',['sick','leave','sickness','none','resigned']),
					('parent_id.department_id.branch_id','=',self.branch_id.id),
					]).ids)
				item.guest_count = len(training_obj.sudo().search([('date','=',item.date),('type','=','guest')]).ids)
				item.total_employee = item.ita_count + item.employee_count +item.guest_count + item.gereet_employee_count
				item.uildver_osol = len(injury_obj.search([('date','like',item.date),('branch_id','=',self.branch_id.id)]).ids)
				# item.first_help = len(ambulance_line_obj.sudo().search([('date_day','=',item.date),('employee_id.department_id.branch_id','=',self.branch_id.id)]).ids)
				item.hosp_help = len(ambulance_line_obj.sudo().search([('date_day','=',item.date),('employee_id.department_id.branch_id','=',self.branch_id.id)]).ids)
				# item.timed_damage = len(ambulance_line_obj.sudo().search([('date_day','=',item.date),('employee_id.department_id.branch_id','=',self.branch_id.id)]).ids)
				item.fire_incident = len(fire_obj.sudo().search([('date','=',item.date),('employee_id.department_id.branch_id','=',self.branch_id.id)]).ids)
				item.urid_zaavar = len(training_obj.sudo().search([('date','=',item.date),('type','=','advance'),('branch_id','=',self.branch_id.id)]).ids)
				item.first_zaavar = len(training_obj.sudo().search([('date','=',item.date),('type','=','elementary'),('branch_id','=',self.branch_id.id)]).ids)
				item.guest_zaavar = len(training_obj.sudo().search([('date','=',item.date),('type','=','guest'),('branch_id','=',self.branch_id.id)]).ids)
				item.regularly_zaavar = len(training_obj.sudo().search([('date','=',item.date),('type','=','regularly'),('branch_id','=',self.branch_id.id)]).ids)
				item.not_regularly_zaavar = len(training_obj.sudo().search([('date','=',item.date),('type','=','not_regularly'),('branch_id','=',self.branch_id.id)]).ids)

				item.urid_zaavar_sum = len(training_line_obj.sudo().search([('training_id.date','=',item.date),('training_id.type','=','advance'),('training_id.branch_id','=',self.branch_id.id)]).ids)
				item.first_zaavar_sum = len(training_line_obj.sudo().search([('training_id.date','=',item.date),('training_id.type','=','elementary'),('training_id.branch_id','=',self.branch_id.id)]).ids)
				item.guest_zaavar_sum = len(guest_line_obj.sudo().search([('training_id.date','=',item.date),('training_id.type','=','guest'),('training_id.branch_id','=',self.branch_id.id)]).ids)
				item.regularly_zaavar_sum = len(training_line_obj.sudo().search([('training_id.date','=',item.date),('training_id.type','=','regularly'),('training_id.branch_id','=',self.branch_id.id)]).ids)
				item.not_regularly_zaavar_sum = len(training_line_obj.sudo().search([('training_id.date','=',item.date),('training_id.type','=','not_regularly'),('training_id.branch_id','=',self.branch_id.id)]).ids)


				item.risk_assessment = len(risk_asseesstment_obj.sudo().search([('create_date','=',item.date),('check_user_id.user_id.branch_id','=',self.branch_id.id)]).ids)
				item.workplace_inspection  = len(workplace_obj.search([('date','=',item.date),('branch_id','=',self.branch_id.id)]).ids)
				item.noticed = preliminary_obj + warning_obj