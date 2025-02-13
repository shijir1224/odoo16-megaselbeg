# -*- coding: utf-8 -*-


# Санамж:
# Тодотгосон хуваарь руу хүсэлтийн төрөл орж байгаа
# Ажилласан цагийг тодотгосон хуваариас тооцож байгаа
# Хүсэлт орсон бол ажилласан цагийг Үндсэн хуваариас тооцно
# Үндсэн хуваариа өөрчилөх шаардлага гарч давхар хүсэлт орсон бол үндсэн хуваариа uptade хийнэ
# Хоцролт тооцох эсэх чеклэвэл ээлж дээр хоцролтын цагаас хоцролтоо тооцно үгүй бол ээлж дээрх эхлэх цагаас тооцно

import time
import datetime
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import calendar
from odoo.osv import osv

import logging
_logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
month=[('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
		('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
		('90','10 сар'), ('91','11 сар'), ('92','12 сар')]

class HrTimetable(models.Model):
	_name = "hr.timetable"
	_inherit = ['mail.thread']
	_description = "Timetable"

	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(HrTimetable, self).unlink()

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	employee_id = fields.Many2one('hr.employee','Үүсгэсэн ажилтан', default=_default_employee, required=True)
	name= fields.Char('Төлөвлөгөөний нэр', size=150)
	year= fields.Char(string='Жил', size=8, required=True,default=date.today().year)
	month=fields.Selection(month, 'Сар', required=True)
	department_id= fields.Many2one('hr.department', "Хэлтэс")
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	line_ids= fields.One2many('hr.timetable.line', 'parent_id', 'Employee hour balance')
	date_from = fields.Date('Эхлэх огноо', default=time.strftime('%Y-%m-01'),required=True)
	date_to = fields.Date('Дуусах огноо',required=True, tracking=True)
	shift_id = fields.Many2one('hr.shift','Ростер' , tracking=True)
	is_attendance = fields.Boolean('Ирц татах эсэх', tracking=True)
	is_plan = fields.Boolean('Ажилтны төлөвлөгөөнөөс татах эсэх?', tracking=True)
	is_mining = fields.Boolean('Уурхайн цаг татах')
	data = fields.Binary('Эксел файл', tracking=True)
	file_fname = fields.Char(string='File name', tracking=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил', required=True, tracking=True)
	day_to_work_month=fields.Float('Ажиллавал зохих өдөр', default='21', tracking=True)
	hour_to_work_month=fields.Float('Ажиллавал зохих цаг', default='168', tracking=True)
	# Тохиргоо хэсэг
	employee_ids = fields.Many2many('hr.employee',string = 'Ажилчид', tracking=True)
	up_date_from = fields.Datetime('Орсон ирц', tracking=True)
	up_date_to = fields.Datetime('Гарсан ирц', tracking=True)
	month_da = fields.Boolean('Сар дамнасан ')
	# Тухайн огнооны хоорондхыг сонгосон хувиараар цэнэглэх
	shift_id = fields.Many2one('hr.shift.time','Хуваарь', tracking=True)
	sh_date_from = fields.Date('Эхлэх огноо', tracking=True)
	sh_date_to = fields.Date('Дуусах огноо', tracking=True)
	is_limit = fields.Boolean('Лимит тооцох эсэх')
	is_late = fields.Boolean('Хоцролт тооцох эсэх')
	state= fields.Selection([('draft','Ноорог'),
				('lock',u'Цоожлох'),
				('send',u'Илгээсэн'),
				('confirm',u'ХН хянасан'),
				('done',u'Дууссан')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)


	timetable_line_line_rltd = fields.One2many('hr.timetable.line.line', compute="_compute_timetbale_lines")
	only_attendance = fields.Boolean('Ирцээс тооцох', tracking=True)

	def _compute_timetbale_lines(self):
		for item in self:
			ids=self.env['hr.timetable.line.line']
			for l in item.line_ids:
				for ll in l.line_ids:
					ids+=ll
			item.timetable_line_line_rltd = ids


	def action_lock(self):
		self.write({'state': 'lock'})

	def action_send(self):
		self.write({'state': 'send'})

	def action_confirm(self):
		self.write({'state': 'confirm'})

	def action_done(self):
		self.date_update()
		self.write({'state': 'done'})

	def action_draft(self):
		self.write({'state': 'draft'})

	def all_cancel(self):
		for l in self.line_ids:
			l.update({'is_update':False})

	def all_yes(self):
		for l in self.line_ids:
			l.update({'is_update':True})

	#  Create line Ажилчдын төлөвлөгөө татах
	def create_line(self):
		if self.line_ids:
			self.line_ids.unlink()
			if self.line_ids.line_ids:
				self.line_ids.line_ids.unlink()
		self.create_this_month()

	# query дээрх нөхцөл шалгах
	def set_conditions(self):
		conditions = ""
		if  self.department_id and self.work_location_id:
			conditions = " and wl.id= %s" % self.work_location_id.id
			conditions +=  " and hd.id = %s " % self.department_id.id
		elif self.department_id:
			conditions = " and hd.id = %s " % self.department_id.id
		elif self.work_location_id:
			conditions = " and wl.id = %s " % self.work_location_id.id
		return conditions

	# HR Timetable Line create хийх
	def create_this_month(self):
		balance_data_pool = self.env['hr.timetable.line']
		line_line_pool = self.env['hr.timetable.line.line']
		query = """SELECT
			he.id as emp_id,
			hd.id as dep_id,
			hj.id as hj_id,
			wl.id as wl_id
			FROM hr_employee he
			LEFT JOIN hr_department hd On hd.id=he.department_id
			LEFT JOIN hr_job hj On hj.id=he.job_id
			LEFT JOIN hr_work_location wl On wl.id=he.work_location_id
			WHERE hj.import_plan = False and employee_type in ('employee','trainee','contractor') and he.start_date<='%s' %s
			ORDER BY he.name """ % (self.date_to,self.set_conditions())
		self.env.cr.execute(query)
		records_loc = self.env.cr.dictfetchall()
		if self.is_plan == True:
			self.employee_line_create()
		else:
			if  self.work_location_id:
				resigned_emps = self.env['hr.employee'].search([('is_this_month_wage', '=', True),('work_end_date', '>=', self.date_from),('work_end_date', '<=', self.date_to),('employee_type', '=', 'resigned'),('work_location_id', '=', self.work_location_id.id)])
				if self.department_id:
					resigned_emps = self.env['hr.employee'].search([('is_this_month_wage', '=', True),('work_end_date', '>=', self.date_from),('work_end_date', '<=', self.date_to),('employee_type', '=', 'resigned'),('work_location_id', '=', self.work_location_id.id),('department_id', '=', self.department_id.id)])
			sequence=1
			for r_emp in resigned_emps:
				balance_data_pool = balance_data_pool.create({
					'employee_id':r_emp.id,
					'department_id': r_emp.department_id.id,
					'job_id': r_emp.job_id.id,
					'month': self.month,
					'year': self.year,
					'day_to_work_month':self.day_to_work_month,
					'hour_to_work_month':self.hour_to_work_month,
					'parent_id': self.id,
					'sequence': sequence,
				})
				self.create_data_pool(balance_data_pool,line_line_pool)
				sequence+=1
			for loc in records_loc:
				balance_data_pool = balance_data_pool.create({
					'employee_id':loc['emp_id'],
					'department_id': loc['dep_id'],
					'job_id': loc['hj_id'],
					'month': self.month,
					'year': self.year,
					'day_to_work_month':self.day_to_work_month,
					'hour_to_work_month':self.hour_to_work_month,
					'parent_id': self.id,
					'sequence': sequence,
				})
				sequence+=1
				self.create_data_pool(balance_data_pool,line_line_pool)

	# Ажилтан дээр тохируулсан ростероос татна
	def create_data_pool(self,balance_data_pool,line_line_pool):
		if balance_data_pool:
			line_obj = balance_data_pool.browse(balance_data_pool)
			none_id = self.env['hr.shift.time'].search([('is_work', '=','none')],limit=1)
			for line in line_obj:
				from_dt = datetime.strptime(
					str(self.date_from), DATE_FORMAT).date()
				to_dt = datetime.strptime(
					str(self.date_to), DATE_FORMAT).date()
				emp_obj = self.env['hr.employee'].search(
					[('id', '=', line.id.employee_id.id)], limit=1)
				if len(emp_obj) == 1:
					if emp_obj.start_date:
						start_date = datetime.strptime(str(emp_obj.start_date), DATE_FORMAT)
					else:
						raise osv.except_osv(u'%s кодтой %s ажилтны ростерийн тохиргоог оруулна уу' % (
							line.id.employee_id.identification_id, line.id.employee_id.name))
				else:
					raise osv.except_osv(u'%s кодтой %s ажилтны ростерийн бүртгэл алдаатай байна' % (
						line.id.employee_id.identification_id, line.id.employee_id.name))

				sss_k = 0
				snum = 1
				step = timedelta(days=1)
				while from_dt <= to_dt:
					public_hol_id=self.env['hr.public.holiday'].search([('days_date', '=', from_dt)],limit=1)
					hol=True if public_hol_id else False
					if to_dt >= from_dt:
						# hr.timetable.line.line - Ажилтан create хийх
						line_line_conf = line_line_pool.create({
							'date': from_dt,
							'name': 'nameffff',
							'parent_id': line.id.id,
							'employee_id': line.id.employee_id.id,
							'job_id': line.id.job_id.id,
							'department_id':line.id.department_id.id,
							'month': line.id.month,
							'year': line.id.year,
							'work_location_id': self.work_location_id.id,
							'is_not_tourist': emp_obj.is_not_tourist,
							
						})
						line_line_obj = line_line_pool.browse(
							line_line_conf)
					num = 0
					# Хуваарь тохируулах дээр сонгосон эхлэх өдрөөр эхлэнэ
					f_day=0
					if from_dt.day < start_date.day and self.month_da==True:
						day = calendar.monthrange(self.date_from.year, self.date_from.month)[1]
						# Сар дамнаж төлөвлөгөө татаж байгаа газар сарын сүүлийн хоног
						f_day = from_dt.day + day
						# 26+5=31
					else:
						f_day = from_dt.day
					num = start_date.day
					# num = 30
					sss_k =f_day + emp_obj.start_day-num
					shift_line = self.env['hr.shift.line'].search([('shift_id', '=', line.id.employee_id.roster_id.id), ('number', '=', sss_k)])
					for ll in line_line_obj:
						if shift_line:
							if from_dt.day >= start_date.day:
								self.up_get_line_vals(sss_k,hol,ll,from_dt,none_id,shift_line)
								# print('\n\n----emem111',from_dt,sss_k,ll.id.employee_id.name)
							# Сар дамнах
							elif from_dt.day <= start_date.day and self.month_da==True:
								self.up_get_line_vals(sss_k,hol,ll,from_dt,none_id,shift_line)

							elif from_dt < start_date.date():
								ll.id.update({
									'is_work_schedule': 'none',
									'shift_plan_id': none_id.id,
									'shift_attribute_id': none_id.id,
								})
							else:
								ll.id.update({
									'is_work_schedule': 'none',
									'shift_plan_id': none_id.id,
									'shift_attribute_id': none_id.id,
								})
						else:
							# Ростерийн эхнээс эхлүүлэх
							shift_line = self.env['hr.shift.line'].search([('shift_id', '=', line.id.employee_id.roster_id.id), ('number', '=', snum)])
							if from_dt < emp_obj.start_date:
								ll.id.update({
									'is_work_schedule': 'none',
									'shift_plan_id': none_id.id,
									'shift_attribute_id': none_id.id,
								})
							else:
								if shift_line.number == len(emp_obj.roster_id.line_ids):
									snum = 1
								else:
									snum += 1
								self.up_get_line_vals(sss_k,hol,ll,from_dt,none_id,shift_line)
						from_dt += step
						sss_k += 1

	# Бүх нийтийн амралтын өдөр таних
	def up_get_line_vals(self,sss_k,hol,ll,from_dt,none_id,shift_line):
		if sss_k > 0:
			if hol==True:
				holiday_id = self.env['hr.shift.time'].search([('is_work', '=','public_holiday')],limit=1)
				vals = ll.id.get_line_vals({
					'number': shift_line.number,
					'date': from_dt,
					'is_work_schedule': holiday_id.is_work,
					'shift_plan_id': shift_line.name.id,
					'shift_attribute_id': holiday_id.id,
					'is_public_holiday':hol,

					})
				ll.id.update(vals)
			else:
				vals = ll.id.get_line_vals({
					'number': shift_line.number,
					'date': from_dt,
					'is_work_schedule': shift_line.name.is_work,
					'shift_plan_id': shift_line.name.id,
					'shift_attribute_id': shift_line.name.id,
					'is_public_holiday':hol,
					})
				ll.id.update(vals)
		else:
			ll.id.update({
				'is_work_schedule': 'none',
				'shift_plan_id': none_id.id,
				'shift_attribute_id': none_id.id,
			})

	# Ирцийн төхөөрөмжийн ирц татах
	def import_attendance(self):
		for obj in self:
			query = """SELECT
				employee_id
				FROM hr_timetable_line
				WHERE parent_id=%s
				""" % (obj.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
			for record in records:
				query = """SELECT
					ll.id,
					ll.date,
					sht.end_time,
					sht.start_time,
					hr.name,
					line.employee_id,
					hj.id,
					ll.is_work_schedule
					FROM hr_timetable_line_line ll
					LEFT JOIN hr_timetable_line line ON ll.parent_id=line.id
					LEFT JOIN hr_employee hr ON line.employee_id=hr.id
					LEFT JOIN hr_job hj ON hr.job_id=hj.id
					LEFT JOIN hr_shift_time sht ON ll.shift_plan_id=sht.id
					WHERE line.employee_id=%s and ll.date>='%s' and ll.date<='%s'
					ORDER BY ll.date
				""" % (record[0], obj.date_from, obj.date_to)
				self.env.cr.execute(query)
				querys = self.env.cr.fetchall()
				for line in querys:
					self.set_attendance(line,record)

# Ирц оноох hr attendance aas
	def set_hr_attendance(self):
		for l in self.line_ids:
			for ll in l.line_ids:
				id = 0
				hr_att_count = self.env['hr.attendance'].search([('employee_id','=',l.employee_id.id),('in_date','=',ll.date)],order='check_in desc',)
				hr_att = self.env['hr.attendance'].search([('employee_id','=',l.employee_id.id),('in_date','=',ll.date)],order='check_in desc', limit=1)
				id = hr_att.id
				if hr_att:
					tt_ll = self.env['hr.timetable.line.line'].search([('id', '=', ll.id),('date', '=', hr_att.in_date)])
					if tt_ll.is_work_schedule in ('day','night','in','out'):
						if tt_ll.start_time and tt_ll.end_time:
							tt_ll.update({
									'sign_in_emp': hr_att.check_in,
									'sign_out_emp': hr_att.check_out,
									'sign_in': tt_ll.start_time,
									'sign_out': tt_ll.end_time,
								})
						else:
							raise UserError(_('%s ээлжний цаг байхгүй байна.Ээлж цэснээс шалгана уу')%(tt_ll.shift_plan_id.name))
					else:
					# Амралтын өдөр ирц татах
						if tt_ll.is_work_schedule in ('none','public_holiday'):
							tt_ll.update({
									'sign_in_emp': hr_att.check_in,
									'sign_out_emp': hr_att.check_out,
									'sign_in': hr_att.check_in,
									'sign_out':  hr_att.check_out,
								})
					hr_att_hour = self.env['hr.attendance'].search([('employee_id','=',l.employee_id.id),('in_date','=',ll.date),('id','!=',id)], limit=1)
					if hr_att_hour:
						tt_ll = self.env['hr.timetable.line.line'].search([('id', '=', ll.id),('date', '=', hr_att.in_date)])
						tt_ll.update({
								'worked_hour': tt_ll.worked_hour+hr_att_hour.worked_hours,
								'worked_salary_hour': tt_ll.worked_salary_hour+hr_att_hour.worked_hours,
							})

	# Ирц оноох
	def set_attendance(self,line,record):
		line_line_pool = self.env['hr.timetable.line.line']
		line_id = line[0]
		line_obj = line_line_pool.search([('id', '=', line_id)])
		datetime_in = self.hour_minute_replace(line_obj.date)
		att_len = self.env['mw.attendance'].sudo().search([('employee_id','=',record[0]),('date','=',line[1])])
		att_in=None
		add_in_hour=None
		mi_in_hour=None
		add_out_hour=None
		# Ирц ганцхан байх үед
		if len(att_len)==1:
			if self.is_limit==True:
				in_time = 0
				out_time = 0
				# Лимитээр хязгаарлах
				att_limit_in = self.env['mw.attendance'].sudo().search([('employee_id','=',record[0]),('attendance_time','>=',line_obj.in_limit_start),('attendance_time','<=',line_obj.in_limit_end)], order='attendance_time asc', limit=1)
				att_limit_out = self.env['mw.attendance'].sudo().search([('employee_id','=',record[0]),('attendance_time','>=',line_obj.out_limit_start),('attendance_time','<=',line_obj.out_limit_end)], order='attendance_time desc', limit=1)
				# start_time = self.late_hour(line_obj.late_s,line_obj.start_time)
				if att_limit_in.attendance_time and line_obj.start_time:
					# Орсон цаг ажил эхлэх цагаас хамааруулах эхлэх цагаас бага бол АЗ цагийг онооно эсрэг тохиолдолд шууд онооно
					if line_obj.start_time >= att_limit_in.attendance_time:
						in_time = line_obj.start_time
					else:
						in_time = att_limit_in.attendance_time
					line_obj.update({
						'sign_in': in_time,
						'sign_in_emp': att_limit_in[0].attendance_time,
					})
				if att_limit_out.attendance_time and line_obj.end_time:
					# Гарсан цаг ажил дуусах цагаас хамааруулах дуусах цагаас их бол АЗ цагийг онооно эсрэг тохиолдолд шууд онооно
					if line_obj.end_time<=att_limit_out.attendance_time:
						out_time = line_obj.end_time
					else:
						out_time = att_limit_out.attendance_time
					line_obj.update({
						'sign_out': out_time,
						'sign_out_emp': att_limit_out[0].attendance_time,
					})
			else:
				# Лимит тооцохгүй бол
				att_in_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]), ('attendance_time', '>=', datetime_in)], order='attendance_time asc', limit=1)
				if att_in_id:
					# Орсон цаг
					att_in = datetime.strptime(str(att_in_id.attendance_time), DATETIME_FORMAT) + timedelta(hours=8)
					# Орсон гарсан ирц рүү онооход интервал тооцох
					if line_obj.start_time:
						# Орох цагаас 2 цагийн интервал
						add_in_hour = line_obj.start_time + timedelta(hours=10)
						mi_in_hour = line_obj.start_time - timedelta(hours=6)
					if line_obj.end_time:
						# Гарах цагаас 2 цагийн интервал
						add_out_hour = line_obj.end_time + timedelta(hours=10)
					if add_in_hour  and mi_in_hour:
						if att_in <= add_in_hour and att_in >= mi_in_hour:
							# гарсан ирц байхгүй бол хонож ажилласан хүний шөнийн ирцийг гарсан ирцэд татах
							att_tomm_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]+ timedelta(days=1))], order='attendance_time asc', limit=1)
							if att_tomm_id:
								# Тухайн өдрийн 04 цаг == datetime_out
								if line_obj.shift_plan_id.is_work=='night':
									line_obj.update({
										'sign_in': line_obj.start_time,
										'sign_in_emp': att_in,
										'sign_out': line_obj.end_time,
										'sign_out_emp': att_tomm_id.attendance_time,
									})
								else:
									line_obj.update({
										'sign_in': line_obj.start_time,
										'sign_in_emp': att_in,
										'sign_out': None,
										'sign_out_emp': None,
									})
							else:
								self.set_sign_in(line_obj,att_in_id.attendance_time,line_obj.start_time)

					elif add_out_hour and add_out_hour:
						if att_in <= add_out_hour and att_in >= add_out_hour:
							self.set_sign_out(line_obj,att_in,line_obj.end_time)
					else:
						if att_in.hour > 4:
							line_obj.update({
									'sign_in':att_in_id.attendance_time,
									'sign_in_emp':att_in_id.attendance_time,
								})
		else:
			# Ирц 2оос дээш үед
			self.set_att_in_out(line,record,line_obj)


	# орсон гарсан ирц
	def set_att_in_out(self,line,record,line_obj):
		datetime_in = self.hour_minute_replace(line_obj.date)- timedelta(hours=8)
		datetime_out = self.hour_minute_replace(line_obj.date).replace(hour=23,minute=59) - timedelta(hours=8)
		# Лимитээр хязгаарлах
		if self.is_limit==True:
			in_time = 0
			out_time = 0
			att_limit_in = self.env['mw.attendance'].sudo().search([('employee_id','=',record[0]),('attendance_time','>=',line_obj.in_limit_start),('attendance_time','<=',line_obj.in_limit_end)], order='attendance_time asc', limit=1)
			att_limit_out = self.env['mw.attendance'].sudo().search([('employee_id','=',record[0]),('attendance_time','>=',line_obj.out_limit_start),('attendance_time','<=',line_obj.out_limit_end)], order='attendance_time desc', limit=1)
			if att_limit_in.attendance_time and line_obj.start_time:
				if line_obj.start_time>=att_limit_in.attendance_time:
					in_time = line_obj.start_time
				else:
					in_time = att_limit_in.attendance_time
				line_obj.update({
					'sign_in': in_time,
					'sign_in_emp': att_limit_in[0].attendance_time
				})
			if att_limit_out.attendance_time and line_obj.end_time:
				if line_obj.end_time<=att_limit_out.attendance_time:
					out_time = line_obj.end_time
				else:
					out_time = att_limit_out.attendance_time

				line_obj.update({
					'sign_out': out_time,
					'sign_out_emp': att_limit_out[0].attendance_time,
				})
			else:
				# Амралтын өдөр ирц татах
				if line_obj.is_work_schedule == 'none':
					line_obj.update({
							'sign_in': att_limit_in.attendance_time,
							'sign_in_emp': att_limit_in.attendance_time,
							'sign_out': att_limit_out.attendance_time,
							'sign_out_emp': att_limit_out.attendance_time,
						})
		else:
			att_out_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]),('attendance_time', '<=', datetime_out)], order='attendance_time desc',limit=1)
			att_in_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]), ('attendance_time', '>=', datetime_in)], order='attendance_time asc',limit=1)
			s_in=None
			s_out=None
			if att_in_id and att_out_id:
				s_in = datetime.strptime(str(att_in_id.attendance_time), DATETIME_FORMAT) + timedelta(hours=8)
				s_out = datetime.strptime(str(att_out_id.attendance_time), DATETIME_FORMAT)	+ timedelta(hours=8)
				in_seconds = s_in.minute * 60 + s_in.second
				out_seconds = s_out.minute * 60 + s_out.second
				if line_obj.is_work_schedule in ('day','night'):
					if line_obj.start_time and line_obj.end_time:
						if s_in.hour == s_out.hour and in_seconds + 600 >= out_seconds:
							# гарсан ирц байхгүй бол хонож ажилласан хүний шөнийн ирцийг гарсан ирцэд татах
							att_tomm_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]+ timedelta(days=1))], order='attendance_time asc', limit=1)
							if att_tomm_id:
								tom_in = datetime.strptime(str(att_tomm_id.attendance_time), DATETIME_FORMAT)
								if line_obj.shift_plan_id.is_work=='night':
									line_obj.update({
										'sign_in_emp':att_in_id.attendance_time,
										'sign_out_emp':tom_in,
									})
								else:
									line_obj.update({
										'sign_in_emp': att_in_id.attendance_time,
										'sign_out_emp': None,
									})
							else:
								line_obj.update({
									'sign_in': line_obj.start_time,
									'sign_in_emp': att_in_id.attendance_time,
									'sign_out': None,
									'sign_out_emp': None,
								})
						else:
							if s_out <= line_obj.end_time+ timedelta(hours=8):
								if s_in <= line_obj.start_time+ timedelta(hours=8):
									line_obj.update({
										'sign_in': line_obj.start_time,
										'sign_in_emp': att_in_id.attendance_time,
										'sign_out': att_out_id.attendance_time,
										'sign_out_emp': att_out_id.attendance_time,
									})
								else:
									line_obj.update({
										'sign_in': att_in_id.attendance_time,
										'sign_in_emp': att_in_id.attendance_time,
										'sign_out': att_out_id.attendance_time,
										'sign_out_emp': att_out_id.attendance_time,
									})

							if s_out >= line_obj.end_time + timedelta(hours=8):
								if s_in <= line_obj.start_time + timedelta(hours=8):
									line_obj.update({
										'sign_in': line_obj.start_time,
										'sign_in_emp': att_in_id.attendance_time,
										'sign_out': line_obj.end_time,
										'sign_out_emp': att_out_id.attendance_time,
									})
								else:
									line_obj.update({
										'sign_in': att_in_id.attendance_time,
										'sign_in_emp': att_in_id.attendance_time,
										'sign_out': line_obj.end_time,
										'sign_out_emp': att_out_id.attendance_time,
									})
					else:
						raise UserError(_('%s ээлжний цаг байхгүй байна.Ээлж цэснээс шалгана уу')%(line_obj.shift_plan_id.name))
				else:
					# Амралтын өдөр ирц татах
					if line_obj.is_work_schedule == 'none':
						line_obj.update({
								'sign_in': att_in_id.attendance_time,
								'sign_in_emp': att_in_id.attendance_time,
								'sign_out': att_out_id.attendance_time,
								'sign_out_emp': att_out_id.attendance_time,
							})
			else:
				line_obj.update({
					'sign_in': None,
					'sign_in_emp': None,
					'sign_out': None,
					'sign_out_emp': None,
				})


	# Хоцролт тооцох цаг
	def late_hour(self,late_s,s_time):
		start_time=None
		if self.is_late == True:
			start_time = late_s
		else:
			start_time = s_time
		return start_time


	def hour_minute_replace(self,date):
		if date:
			datee = str(date) + ' ' + '04' +':'+'00'+':'+'00'
			date_s = datetime.strptime(str(datee), DATETIME_FORMAT)
			return date_s

	# att_datetime - Ирцээр орж ирсэн цаг , datetime - орж ирэх ёстой цаг
	def set_sign_in(self,line_obj,att_datetime,datetime):
		if att_datetime and datetime:
			if att_datetime <= datetime:
				line_obj.update({
					'sign_in': datetime,
					'sign_in_emp': att_datetime,
				})
			else:
				line_obj.update({
					'sign_in':att_datetime,
					'sign_in_emp':att_datetime,
				})

	def set_sign_out(self,line_obj,att_datetime,datetime):
		if att_datetime and datetime:
			if att_datetime <= datetime:
				line_obj.update({
					'sign_out': att_datetime,
					'sign_out_emp': att_datetime,
				})
			else:
				line_obj.update({
					'sign_out':datetime,
					'sign_out_emp':att_datetime,
				})
