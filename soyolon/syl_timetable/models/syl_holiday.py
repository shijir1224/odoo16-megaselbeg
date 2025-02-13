from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import time



DATETIME_FORMAT ="%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HrTimeCompute(models.Model):
	_inherit = "hr.time.compute"
	
	project_id = fields.Many2one('hr.project',string='Төсөл',related='hr_parent_id.project_id',store=True)
	overtime_type = fields.Selection(
		[("overtime", "Илүү цаг"), ("accumlated", "Нөхөн амрах")], "Цагийн төрөл",related='hr_parent_id.overtime_type',store=True)
	date_from = fields.Datetime('Огноо', copy=False, required=False, tracking=True, compute=False, default=time.strftime('%Y-%m-%d 00:00:00'))

# , default=time.strftime('%Y-%m-01')

class HrLeaveRequestMw(models.Model):
	_inherit = "hr.leave.mw"

	description = fields.Char(string='Шалтгаан')
	overtime_type = fields.Selection(
		[("overtime", "Илүү цаг"), ("accumlated", "Нөхөн амрах")], "Цагийн төрөл", tracking=True)
	paid_leave_type = fields.Selection(
		[("type1", "Эхнэр, нөхөр, төрсөн болон үрчилсэн эцэг эх, үр хүүхэд, нас барсан бол"),
   		("type2", "Ажилтан хуримын ёслолоо хийж байгаа бол"),
		("type3", "Ажилтны орон гэрт байгалийн болон нийтийг хамарсан гэнэтийн гамшиг тохиолдсон бол"),
		("type4", "Жирэмсний 3 болон 7 сартай байх хугацаандаа эмчийн хяналтад орж эрүүл мэндийн үзлэг шинжилгээ өгөх үед"),("type5", "Бусад"),],"Цалинтай чөлөөний төрөл", tracking=True)
	accumlated_hour = fields.Float('Нөхөн амрах цаг')
	history_line_ids = fields.Many2many(
		'hr.leave.mw', u'Өмнөх түүх', compute="before_contracts_view")
	vac_days = fields.Float(
		'Амрах хоног')
	is_half = fields.Boolean('Үлдсэн амралтаа биеэр эдлэх эсэх')
	is_half_rest = fields.Boolean('Биеэр эдлэхдээ хувааж авах эсэх')
	is_rest = fields.Boolean(
		'Үлдсэн амралтаа биеэр эдлэхгүй учир ээлжийн амралтын цалинг нэмэгдүүлэн тооцуулах')
	is_get_salary = fields.Boolean('Өөрийн хүсэлтээр цалин тооцуулах')
	startdate = fields.Date('Эхлэх огноо')
	enddate = fields.Date('Дуусах огноо')
	l_startdate = fields.Date('Үлдсэн эхлэх огноо')
	l_enddate = fields.Date('Үлдсэн дуусах огноо')
	remain_days = fields.Float(
		'Үлдсэн амрах хоног', compute='_compute_vac_days')
	work_year = fields.Date(
		string='Компанид ажилд орсон огноо', related='employee_id.engagement_in_company')
	work_year_bef = fields.Date(
		string='Ажлын жил')
	work_year_af = fields.Date(string='Аж')
	project_id = fields.Many2one('hr.project',string='Төсөл')

	@api.depends('time_from', 'time_to')
	def _compute_number_of_hour(self):
		for obj in self:
			if obj.time_to > obj.time_from:
				if obj.time_to >= 13 and obj.time_from < 13:
					obj.number_of_hour = obj.time_to-obj.time_from - obj.lunch_hour
				else:
					obj.number_of_hour = obj.time_to-obj.time_from
			else:
				obj.number_of_hour = 24-obj.time_from+obj.time_to

	@api.depends('date_from', 'date_to', 'number_of_hour')
	def _compute_day(self):
		for item in self:
			st_d = None
			en_d = None
			day_hl = 0
			day_too=0
			if item.date_from and item.date_to:
				holidays = self.env['hr.public.holiday'].search([('days_date','>=',item.date_from),('days_date','<=',item.date_to)])
				if holidays:
					for hh in holidays:
						day_hl += 1 if hh.days_date.weekday() < 5 else 0
				st_d = datetime.strptime(str(item.date_from + timedelta(hours=8)), DATETIME_FORMAT).date()
				en_d = datetime.strptime(str(item.date_to +timedelta(hours=8)), DATETIME_FORMAT).date()
				# Оффис Location number = 1 байх ёстой
				# Уурхай Location number = 2  уурхай амралтын өдөр хамааралгүй хүсэлт тооцох учир
				if item.work_location_id.location_number == '1':
					if item.is_work=='business_trip' or item.is_work=='training' or item.is_work=='overtime_hour':
						for single_date in item.daterange(st_d, en_d):
							day_too += 1
					else:
						for single_date in item.daterange(st_d, en_d):
							day_too += 1 if single_date.weekday() < 5 else 0
					item.days = day_too - day_hl
					item.total_hour = (item.days-day_hl) * item.number_of_hour if day_too>0 else 0
				else:
					for single_date in item.daterange(st_d, en_d):
						day_too += 1
					item.days = day_too
					item.total_hour = item.days * item.number_of_hour


	def accumlated_hour_check(self):
		if round(self.total_hour,0) > round(self.accumlated_hour,0):
			raise UserError(u'Таны нөхөж амрах цаг хүрэлцэхгүй байна!')
	
	def action_next_stage(self):
		# if self.is_work == 'vacation':
		# 	self.action_send()
		if self.is_work == 'accumlated':
			self.accumlated_hour_check()
			
		today = datetime.today()
		# if self.state_type=='draft':
		# 	if self.date_from+timedelta(hours=8) <= today-timedelta(hours=48):
		# 		raise UserError(u'Таны хүсэлт 48 цаг хэтэрсэн байна. Нөхөж илгээх боломжгүй.')
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id,'leave_id', self)	
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
				return True
			else:
				con_user = next_flow_line_id._get_flow_users_syl(self.branch_id,False,)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)

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
						
	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.vac_days = self.employee_id.days_of_annualleave
			self.accumlated_hour = self.employee_id.sum_accumlate_hour

	@api.onchange('work_year')
	def onchange_work_year(self):
		today = date.today()
		if self.work_year:
			if self.work_year.year == today.year:
				self.work_year_bef = self.work_year.replace(today.year + 1)
			else:
				self.work_year_bef = self.work_year.replace(today.year)

	@api.depends('employee_id')
	def before_contracts_view(self):
		for item in self:
			before_contracts = item.env['hr.leave.mw'].search(
				[('employee_id', '=', item.employee_id.id), ('is_work', '=', 'vacation')])
			item.history_line_ids = before_contracts.ids

	@api.depends('days', 'vac_days')
	def _compute_vac_days(self):
		for item in self:
			if item.days and item.vac_days:
				item.remain_days = item.vac_days - item.days
			else:
				item.remain_days = ''


class HrEmployee(models.Model):
	_inherit = "hr.employee"

	def action_shift_vacation(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id(
			'mw_hr.action_shift_vacation_request')
		action['domain'] = [('employee_id', '=', self.id), ('state_type', '=', 'done' )]
		action['res_id'] = self.id
		return action
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
	

	