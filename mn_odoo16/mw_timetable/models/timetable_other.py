# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import api, fields, models, _


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HrAttendance(models.Model):
	_inherit = "hr.attendance"

	worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)

	@api.depends('check_in', 'check_out')
	def _compute_worked_hours(self):
		for attendance in self:
			if attendance.check_out and attendance.check_in:
				delta = attendance.check_out - attendance.check_in
				if attendance.employee_id.roster_id.work_hour <= delta.total_seconds() / 3600.0:
					attendance.worked_hours = attendance.employee_id.roster_id.work_hour
				else:
					attendance.worked_hours = delta.total_seconds() / 3600.0
			else:
				attendance.worked_hours = False

	@api.depends('create_date')
	def _compute_date(self):
		for attendance in self:
			attendance.date = attendance.create_date

	date = fields.Date(string='Огноо', compute='_compute_date', store=True, readonly=True)


class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	roster_id = fields.Many2one('hr.shift','Ростер',tracking=True)
	start_day = fields.Integer('Эхлэх өдөр', default='1')
	w_start_day = fields.Integer('W', default='0')
	n_start_day = fields.Integer('RB', default='0')
	start_date = fields.Date('Эхлэх огноо')
	rest_day = fields.Float('Амрах хоног')
	date_history_ids = fields.One2many('date.history', 'employee_id', 'Өөрчлалтийн түүх')
	full_worked_hour = fields.Boolean(string='Ажилласан цаг бүтэн тооцох')
	is_not_tourist = fields.Boolean(string='Зам цаг тооцохгүй')
	
class DateHistory(models.Model):
	_name = 'date.history'
	_description = 'Date History'
	_order = 'create_date asc'

	employee_id = fields.Many2one('hr.employee', 'HR')
	update_date = fields.Date('Өөрчилсөн огноо')
	user_id = fields.Many2one('res.users', 'Өөрчилсөн ажилтан')
	day = fields.Integer('Эхлэх өдөр')
	date = fields.Date('Огноо')
	w_start_day = fields.Integer('W', default='0')
	n_start_day = fields.Integer('RB', default='0')
	start_date = fields.Date('Эхлэх огноо')
	end_date = fields.Date('Дуусах огноо')
	roster_id = fields.Many2one('hr.shift','Ростер')

# Ээлж тохируулах
class HrShiftTime(models.Model):
	_name = 'hr.shift.time'
	_description = 'Hr Shift Time'
	_inherit = ['mail.thread']

	
	active = fields.Boolean('Active',default=True, store=True, readonly=False)
	name = fields.Char('Нэр',tracking=True)
	flag = fields.Char('Тэмдэглэгээ',tracking=True)
	desc = fields.Char('Тайлбар',tracking=True)
	color = fields.Integer('Color',tracking=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил',tracking=True)
	start_time = fields.Float(u'Энгийн эхлэх цаг',required=True,tracking=True)
	end_time = fields.Float(u'Энгийн дуусах цаг',required=True,tracking=True)
	night_start_time = fields.Float(u'Шөнө цаг/эхлэх/',tracking=True)
	night_end_time = fields.Float(u'Шөнө цаг/дуусах/',tracking=True)
	lunch_start_time = fields.Float(u'Цайны цаг/эхлэх/',tracking=True)
	lunch_end_time = fields.Float(u'Цайны цаг/дуусах/',tracking=True)
	in_s_time = fields.Float(u'Орох лимит/эхлэх/')
	in_e_time = fields.Float(u'Орох лимит/дуусах/')
	out_s_time = fields.Float(u'Гарах лимит/эхлэх/')
	out_e_time = fields.Float(u'Гарах лимит/дуусах/')
	late_s_time = fields.Float(u'Хоцролт тооцох цаг')
	is_request= fields.Boolean('Хүсэлтийн төрөл эсэх',tracking=True)
	is_limit= fields.Boolean('Лимит тохируулах эсэх')
	company_id = fields.Many2one('res.company','Компани', default=lambda self: self.env.user.company_id, readonly=True,tracking=True)
	compute_sum_time = fields.Float('Энгийн цаг', readonly=True, compute='_compute_amount',tracking=True)
	compute_sum_lunch = fields.Float('Цайны цаг', readonly=True, compute='_compute_amount',tracking=True)
	compute_sum_ov_time = fields.Float('Нийт шөнө цаг', readonly=True, compute='_compute_amount',tracking=True)
	compute_sum_all_time = fields.Float('Нийт цаг', readonly=True, compute='_compute_all_hour',tracking=True, store=True)
	is_work = fields.Selection([('day',u'Өдөр'),('night',u'Шөнө'),('vacation',u'Ээлжийн амралт'),('sick',u'Өвчтэй'),('leave',u'Чөлөөтэй'),('pay_leave',u'Цалинтай чөлөө'),('overtime_hour',u'Илүү цаг'),('outage',u'Сул зогсолт'),('sickness',u'Тасалсан'),('none',u'Амралт'),('in','In'),('out','Out'),('parental',u'Аавын 10 хоног'),('bereavement',u'Ажил явдал'),('business_trip',u'Томилолт'),('training',u'Сургалт'),('out_work',u'Гадуур ажилласан'),('online_work',u'Зайнаас ажилласан'),('accumlated',u'Нөхөж амрах'),('attendance',u'Орсон ирц нөхөн бүртгүүлэх'),('attendance_out',u'Гарсан ирц нөхөн бүртгүүлэх'),('resigned',u'Ажлаас гарсан'),('public_holiday',u'Нийтээр амрах өдөр'),('over_day',u'Сунаж ажилласан өдөр'),('over_night',u'Сунаж ажилласан шөнө'),('work_night',u'Хуваарийн бус /шөнө/'),('work_day',u'Хуваарийн бус /өдөр/'),('worked','Ажилласан'),('out_attend','Буух (ирцгүй)'),('night_over','Илүү цаг /шөнө/ ')], u'Хуваарь', default='none',tracking=True)
	roster_change = fields.Float(string='Ээлж солих цаг')

	@api.depends('end_time','start_time','lunch_end_time','lunch_start_time','night_start_time','night_end_time')
	def _compute_amount(self):
		for obj in self:
			if obj.end_time<obj.start_time:
				obj.compute_sum_time = 24-obj.start_time+obj.end_time-(obj.lunch_end_time-obj.lunch_start_time)
			else:
				obj.compute_sum_time = obj.end_time-obj.start_time-(obj.lunch_end_time-obj.lunch_start_time)
				
			if obj.lunch_end_time<obj.lunch_start_time:
				obj.compute_sum_lunch = 24-obj.lunch_start_time+obj.lunch_end_time
			else:
				obj.compute_sum_lunch = obj.lunch_end_time-obj.lunch_start_time
			if obj.night_end_time<obj.night_start_time:
				obj.compute_sum_ov_time = 24-obj.night_start_time+obj.night_end_time
			else:
				obj.compute_sum_ov_time = obj.night_end_time-obj.night_start_time
			if obj.is_work=='night':
				obj.compute_sum_time = obj.compute_sum_time -obj.compute_sum_ov_time
			else :
				obj.compute_sum_time = obj.compute_sum_time

	@api.depends('compute_sum_time','compute_sum_ov_time')
	def _compute_all_hour(self):
		compute_sum_all_time =0
		for obj in self:
			if obj.compute_sum_time:
				compute_sum_all_time += obj.compute_sum_time
			if obj.compute_sum_ov_time:
				compute_sum_all_time += obj.compute_sum_ov_time
			obj.compute_sum_all_time = compute_sum_all_time

class HrShift (models.Model):
	_name = 'hr.shift'
	_description = 'Hr Shift'

	name = fields.Char(string = u'Нэр', required=True)
	start_date = fields.Date(string = 'Эхлэх огноо', required=True)   
	line_ids=fields.One2many('hr.shift.line', 'shift_id', u'Мөрүүд')  
	end_date = fields.Date(string =u'Дуусах огноо')	
	shift_time_id = fields.Many2one('hr.shift.time',string = u'Ээлж', required=True)
	employee_many_ids = fields.Many2many('hr.employee', string='Хамрагдах ажилчид')
	is_7_2 =fields.Boolean('Амралтын өдрийг таних')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	work_hour = fields.Float('Ажлын цаг')
	work_location_id = fields.Many2one('hr.work.location',string='Ажлын байршил')
	
	def daterange(self, start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)

	def date_update(self):
		from_dt = datetime.strptime(str(self.start_date), DATE_FORMAT).date()
		step = timedelta(days=1)
		for l in self.line_ids:
			l.update({'date':from_dt})
			from_dt += step

	def line_update(self):
		for l in self.line_ids:
			if l.is_update == True:
				l.update({'name':self.shift_time_id.id,
					'end_time':self.shift_time_id.end_time,
					'start_time':self.shift_time_id.start_time,
					'lunch_start_time':self.shift_time_id.lunch_start_time,
					'lunch_end_time':self.shift_time_id.lunch_end_time,
					'compute_sum_time':self.shift_time_id.compute_sum_time,
					'compute_sum_lunch':self.shift_time_id.compute_sum_lunch,
					'night_start_time': self.shift_time_id.night_start_time,
					'night_end_time': self.shift_time_id.night_end_time,
					'compute_sum_all_time':self.shift_time_id.compute_sum_time+self.shift_time_id.compute_sum_ov_time,
					'compute_sum_ov_time':self.shift_time_id.compute_sum_ov_time,
					'is_work':self.shift_time_id.is_work})

	def all_cancel(self):
		for l in self.line_ids:
			l.update({'is_update':False})

	def all_yes(self):
		for l in self.line_ids:
			l.update({'is_update':True})

	def create_line(self):
		line_data_pool = self.env['hr.shift.line']
		if self.line_ids:
			self.line_ids.unlink()
		for obj in self:
			if obj.is_7_2 == True:
				start_date = datetime.strptime(
					str(obj.start_date), DATE_FORMAT)
				end_date = datetime.strptime(str(obj.end_date), DATE_FORMAT)
				n = 1
				for single_date in self.daterange(start_date, end_date):
					if single_date.weekday() < 5:
						line_line_conf = line_data_pool.create({
							'number': n,
							'date': single_date,
							'shift_id': obj.id,
							'name': obj.shift_time_id.id,
							'end_time': obj.shift_time_id.end_time,
							'start_time': obj.shift_time_id.start_time,
							'lunch_start_time': obj.shift_time_id.lunch_start_time,
							'lunch_end_time': obj.shift_time_id.lunch_end_time,
							'is_work': obj.shift_time_id.is_work,
							'compute_sum_time': obj.shift_time_id.compute_sum_time,
							'compute_sum_all_time':obj.shift_time_id.compute_sum_time+obj.shift_time_id.compute_sum_ov_time,
							'compute_sum_ov_time':obj.shift_time_id.compute_sum_ov_time,
							'compute_sum_lunch': obj.shift_time_id.compute_sum_lunch,
							'start_time': obj.shift_time_id.start_time,

						})
						n += 1
					else:
						shift_pool = self.env['hr.shift.time'].search(
							[('is_work', '=', 'none')], limit=1)
						line_line_conf = line_data_pool.create({
							'number': n,
							'date': single_date,
							'shift_id': obj.id,
							'name': shift_pool.id,
							'end_time': shift_pool.end_time,
							'start_time': shift_pool.start_time,
							'lunch_start_time': shift_pool.lunch_start_time,
							'lunch_end_time': shift_pool.lunch_end_time,
							'is_work': shift_pool.is_work,
							'compute_sum_time': obj.shift_time_id.compute_sum_time,
							'compute_sum_all_time':obj.shift_time_id.compute_sum_time+obj.shift_time_id.compute_sum_ov_time,
							'compute_sum_ov_time':obj.shift_time_id.compute_sum_ov_time,
							'compute_sum_lunch': shift_pool.compute_sum_lunch,
						})
						n += 1
			else:
				from_dt = datetime.strptime(
					str(self.start_date), DATE_FORMAT).date()
				to_dt = datetime.strptime(
					str(self.end_date), DATE_FORMAT).date()
				step = timedelta(days=1)
				for obj in self:
					n = 1
					while from_dt <= to_dt:
						line_line_conf = line_data_pool.create({
							'number': n,
							'date': from_dt,
							'shift_id': obj.id,
							'name': obj.shift_time_id.id,
							'end_time': obj.shift_time_id.end_time,
							'start_time': obj.shift_time_id.start_time,
							'lunch_start_time': obj.shift_time_id.lunch_start_time,
							'lunch_end_time': obj.shift_time_id.lunch_end_time,
							'is_work': obj.shift_time_id.is_work,
							'compute_sum_time': obj.shift_time_id.compute_sum_time,
							'compute_sum_all_time':obj.shift_time_id.compute_sum_time+obj.shift_time_id.compute_sum_ov_time,
							'compute_sum_ov_time':obj.shift_time_id.compute_sum_ov_time,
							'compute_sum_lunch': obj.shift_time_id.compute_sum_lunch,
							'night_start_time': obj.shift_time_id.night_start_time,
							'night_end_time': obj.shift_time_id.night_end_time,
							
						})
						from_dt += step
						n += 1

	
class HrShiftLine(models.Model):
	_name = 'hr.shift.line'
	_description = 'Hr Shift Line'

	is_update = fields.Boolean('Update')

	date = fields.Date('Огноо')
	name = fields.Many2one('hr.shift.time',string = u'Нэр', required=True)
	number = fields.Integer(u'Дугаар')
	start_time = fields.Float(u'Эхлэх цаг')
	end_time = fields.Float(u'Дуусах цаг')
	night_start_time = fields.Float(u'Илүү цаг/эхлэх/')
	night_end_time = fields.Float(u'Илүү цаг/дуусах/')
	lunch_start_time = fields.Float(u'Цайны цаг/эхлэх/')
	lunch_end_time = fields.Float(u'Цайны цаг/дуусах/')
	shift_id=fields.Many2one('hr.shift', 'Shift', ondelete='cascade')   
	compute_sum_time = fields.Float(string=u'Энгийн цаг',store=True, readonly=True)
	compute_sum_ov_time = fields.Float(string=u'Шөнийн цаг',store=True, readonly=True)
	compute_sum_all_time = fields.Float('Нийт цаг', readonly=True, store=True)
	compute_sum_lunch = fields.Float(string=u'Цайны цаг', store=True, readonly=True)
	
	is_work = fields.Selection([('day',u'Өдөр'),('night',u'Шөнө'),('vacation',u'Ээлжийн амралт'),('sick',u'Өвчтэй'),('leave',u'Чөлөөтэй'),('pay_leave',u'Цалинтай чөлөө'),('overtime_hour',u'Илүү цаг'),('outage',u'Сул зогсолт'),('sickness',u'Тасалсан'),('none',u'Амралт'),('in','In'),('out','Out'),('parental',u'Аавын 10 хоног'),('bereavement',u'Ажил явдал'),('business_trip',u'Томилолт'),('training',u'Сургалт'),('out_work',u'Гадуур ажилласан'),('online_work',u'Зайнаас ажилласан'),('accumlated',u'Нөхөж амрах'),('attendance',u'Орсон ирц нөхөн бүртгүүлэх'),('attendance_out',u'Гарсан ирц нөхөн бүртгүүлэх'),('resigned',u'Ажлаас гарсан'),('public_holiday',u'Нийтээр амрах өдөр'),('out_attend',u'Буух /ирцгүй/')], u'Хуваарь', default='none') 

	@api.onchange('name')
	def onchange_name(self):
		self.start_time = self.name.start_time
		self.end_time = self.name.end_time
		self.lunch_start_time = self.name.lunch_start_time
		self.lunch_end_time = self.name.lunch_end_time
		self.is_work = self.name.is_work
		self.compute_sum_time = self.name.compute_sum_time
		self.compute_sum_lunch = self.name.compute_sum_lunch




class HrPublicHoliday (models.Model):
	_name = 'hr.public.holiday'
	_description = 'Hr Public Holiday'
	_order = "days_date desc"

	name = fields.Char(string = 'Нэр', required=True)
	days_date = fields.Date(string = 'Огноо', required=True)
	

	# @api.model
	# def create(self, vals):
	# 	self.write({'state': 'draft'})
	# 	return super(HrPublicHoliday, self).create(vals)
	

# Тохиргоо Ростер тохируулах 
class HrEmployeeDateSet(models.TransientModel):
	_name = 'hr.employee.date.set'
	_description = 'Hr Timetable Line Set'

	s_date = fields.Date('Эхлэх огноо')
	s_day = fields.Float('Эхлэх өдөр',  digits=(2,0))
	roster_id = fields.Many2one('hr.shift','Ростер')



	def action_update(self):
		obj = self.env['hr.employee'].browse(self._context['active_ids'])
		for item in obj:
			if self.s_date:
				item.update({
					'start_date': self.s_date
					})
			if self.s_day:
				item.update({
					'start_day': self.s_day,
					})
				
			if self.roster_id:
				item.update({
					'roster_id': self.roster_id.id,
					})
		return True
