
# -*- coding: utf-8 -*-
# Цагийн төлөвлөгөө рүү хүсэлтээс татах
import datetime
from datetime import datetime, timedelta
from odoo import models, _
from odoo.exceptions import UserError

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HrTimetable(models.Model):
	_inherit = "hr.timetable"
	
	def import_holiday_time(self):
		for obj in self:
			query = """SELECT 
				employee_id,
				id
				FROM hr_timetable_line
				WHERE parent_id=%s
				"""%(obj.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
			for record in records:
				self.import_holiday_time_many(record)
				self.import_holiday_time_one(record)
				# self.cancel_holiday_time(record) 

	#Тухайн огноонд үүссэн батлагдсан цагийн хүсэлтийг шүүж авах
	def import_holiday_time_many(self,record):
		query_many = """SELECT
			tc.id as id,
			tc.date_from as date_from,
			tc.time_from as time_from,
			tc.time_to as time_to,
			tc.employee_id as employee_id,
			hst.is_work as is_work,
			hst.id as hst_id,
			hr.id as hr_id,
			hl.id as hl_id
			FROM hr_time_compute tc
			LEFT JOIN hr_shift_time hst ON hst.id=tc.shift_plan_id
			LEFT JOIN hr_employee hr ON hr.id=tc.employee_id
			LEFT JOIN hr_leave_mw hl ON hl.id=tc.hr_parent_id
			WHERE tc.employee_id=%s and hl.state_type='done' and hl.is_many = True
		""" % (record[0])
		self.env.cr.execute(query_many)
		recs_many = self.env.cr.dictfetchall()
		for line in recs_many:
			time_compute_id = self.env['hr.time.compute'].search([('id','=',line['id'])],limit=1)
			line_obj = self.env['hr.timetable.line.line'].search([('date','=',line['date_from']),('parent_id','=',record[1])],limit=1)	 
			self.request_set_line(line,line_obj,record,time_compute_id)

	def import_holiday_time_one(self,record):
		query_one = """SELECT
			hl.id as hl_id,
			hl.create_date as create_date,
			hl.date_from as date_from,
			hl.date_to as date_to,
			hl.time_from as time_from,
			hl.time_to as time_to,
			hl.is_many as is_many,
			hst.is_work as is_work,
			hst.id as hst_id,
			hr.identification_id as identification_id,
			hr.name as hr_name,
			hr.id as hr_id
			FROM hr_leave_mw hl
			LEFT JOIN hr_shift_time hst ON hst.id=hl.shift_plan_id
			LEFT JOIN hr_employee hr ON hr.id=hl.employee_id
			WHERE hl.employee_id=%s and hl.state_type='done' and hl.is_many = False
		""" % (record[0])
		self.env.cr.execute(query_one)
		recs_one = self.env.cr.dictfetchall()
		for rec in recs_one:
			self.update_line_obj(rec,record)


	# Хүсэлтээ цагийн төлөвлөгөө рүү update хийх
	def update_line_obj(self,rec, record):
		from_dt = False
		to_dt = False
		if rec['is_work'] not in ('attendance','attendance_out') and rec['is_work'] != 'attendance_out':
			# Хүсэлтийн огноо
			if rec['date_from'] and rec['date_to']:
				from_dt = datetime.strptime(str(rec['date_from']+timedelta(hours=8)), DATETIME_FORMAT).date()
				to_dt = datetime.strptime(str(rec['date_to']+timedelta(hours=8)), DATETIME_FORMAT).date()
			else:
				raise UserError(_('%s өдөр үүсгэссэн %s дугаартай %s ажилтны хүсэлтийн огноо хоосон байна.')%(str(rec['create_date']),rec['identification_id']),str(rec['hr_name']))
			self.leave_request(rec,from_dt,to_dt,record)
		self.leave_request_attendance(rec,record)
	
	
	def leave_request(self,rec,from_dt,to_dt,record):
		step = timedelta(days=1)
		request_id = self.env['hr.leave.mw'].search([('id','=',rec['hl_id'])],limit=1)
		# Хүсэлтийн цаг авах
		while from_dt <= to_dt:
		# out_hour = datetime.strptime(str(rec['date_to']), DATETIME_FORMAT) + timedelta(hours=8)
		# date_from = datetime.strptime(str(rec['date_from']), DATETIME_FORMAT)+ timedelta(hours=8)
		# stept = timedelta(days=1)
		# while date_from <= out_hour:
			line_obj = self.env['hr.timetable.line.line'].search([('date','=',from_dt),('parent_id','=',record[1])],limit=1)	 
			self.request_set_line(rec,line_obj,record,request_id)
			# date_from +=stept
			from_dt += step

	def request_set_line(self,line,line_obj,record,request_id):
		line_line_pool=self.env['hr.timetable.line.line']
		dt_in = None
		dt_out = None
		if request_id.date_from:
			date_from = datetime.strptime(str(request_id.date_from), DATETIME_FORMAT) + timedelta(hours=8)
			dt_in, dt_out = self.leave_convert_datetime(line,date_from)
			line_id = self.env['hr.timetable.line.line'].search([('date','=',date_from),('parent_id','=',record[1])],limit=1)
		public_id = self.env['hr.shift.time'].search([('is_work', '=','public_holiday')],limit=1)
		none_id = self.env['hr.shift.time'].search([('is_work', '=','none')],limit=1)
		
		if line['is_work'] == 'pay_leave':
			# if line_obj.shift_plan_id.is_work =='none':
			# 	line_obj.update({
			# 		'shift_attribute_id':none_id.id,
			# 		'is_request': 'yes',
			# 		'free_wage_hour':0
			# 	})
			if line_obj.shift_plan_id.is_work =='public_holiday':
				line_obj.update({
					'shift_attribute_id':public_id.id,
					'is_request': 'yes',
					'free_wage_hour':0
				})
			else:
				hour = self.request_hour(line,line_obj,request_id,record)
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'free_wage_hour':hour,
					'leave_request_start': dt_in,
		 			'leave_request_end': dt_out,
					'is_request': 'yes'
				})

		elif line['is_work']=='training':
			hour = self.request_hour(line,line_obj,request_id,record)
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'training_hour':request_id.number_of_hour,
				'is_request': 'yes'
				})
		elif line['is_work']=='leave':
			if line_obj.shift_plan_id.is_work =='none':
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'free_hour':0,
					'is_request': 'yes'
				})
			elif line_obj.shift_plan_id.is_work =='public_holiday':
				line_obj.update({
					'shift_attribute_id':public_id.id,
					'is_request': 'yes',
					'free_hour':0
				})
			else:
				hour = self.request_hour(line,line_obj,request_id,record)
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'free_hour':hour,
					'is_request': 'yes',
					'leave_request_start': dt_in,
					'leave_request_end': dt_out,
				})
		elif line['is_work']=='sick':
			if line_obj.shift_plan_id.is_work =='none':
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'sick_hour':0,
					'is_request': 'yes'
				})
			elif line_obj.shift_plan_id.is_work =='public_holiday':
				line_obj.update({
					'shift_attribute_id':public_id.id,
					'is_request': 'yes',
					'sick_hour':0
				})
			else:
				hour = self.request_hour(line,line_obj,request_id,record)
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'sick_hour':hour,
					'is_request': 'yes'
				})
		elif line['is_work']=='overtime_hour':
			self.req_overtime(request_id,line_obj,line)
		elif line['is_work']=='vacation':
			if line_obj.shift_plan_id.is_work =='none':
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'is_request': 'yes',
					'vacation_day':0
				})
			elif line_obj.shift_plan_id.is_work =='public_holiday':
				line_obj.update({
					'shift_attribute_id':public_id.id,
					'shift_plan_id':public_id.id,
					'is_request': 'yes',
					'vacation_day':0
				})
			else:
				hour = self.request_hour(line,line_obj,request_id,record)
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					# 'shift_plan_id':line['hst_id'],
					'vacation_day':request_id.number_of_hour,
					'is_request': 'yes'
				})
		elif line['is_work']=='parental':
			if line_obj.shift_plan_id.is_work =='none':
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'shift_plan_id':none_id.id,
					'parental_hour':0,
					'is_request': 'yes'
				})
			elif line_obj.shift_plan_id.is_work =='public_holiday':
				line_obj.update({
					'shift_attribute_id':public_id.id,
					'shift_plan_id':public_id.id,
					'is_request': 'yes',
					'parental_hour':0
				})
			else:
				hour = self.request_hour(line,line_obj,request_id,record)
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					# 'shift_plan_id':line['hst_id'],
					'parental_hour':request_id.number_of_hour,
					'is_request': 'yes'
				})
		elif line['is_work']=='business_trip':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'busines_trip_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='out_work':
			if request_id.work_location_id.location_number == '1':				
				if line_obj.is_public_holiday == True:
					line_obj.update({
						'shift_attribute_id':public_id.id,
						'out_working_hour':0,
						'is_request': 'yes'
					})
				elif line_obj.shift_plan_id.is_work == 'none':
					line_obj.update({
						'shift_attribute_id':none_id.id,
						'out_working_hour':0,
						'is_request': 'yes'
					})
				else:
					line_obj.update({
						'shift_attribute_id':line['hst_id'],
						'out_working_hour':request_id.number_of_hour,
						'is_request': 'yes',
						'leave_request_start': dt_in,
		 				'leave_request_end': dt_out,
					})
			else:
				if line_obj.worked_hour ==line_obj.hour_to_work:
					line_obj.update({
						'shift_attribute_id':line['hst_id'],
						'out_working_hour':0,
						'is_request': 'yes'
					})
		elif line['is_work']=='day':
			hour = self.request_hour(line,line_obj,request_id,record)					  
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'worked_hour':hour,
				'shift_plan_id':line['hst_id'],
				'is_request': 'yes'
			})
		elif line['is_work']=='night':
			hour = self.request_hour(line,line_obj,request_id,record)					  
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'night_hour':hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='online_work':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'online_working_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='sickness':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'sickness_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='out':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'tourist_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='accumlated':
			if line_obj.shift_plan_id.is_work =='none':
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'is_request': 'yes',
					'accumlated_hour':0,
				})
			elif line_obj.shift_plan_id.is_work =='public_holiday':
				line_obj.update({
					'shift_attribute_id':public_id.id,
					'is_request': 'yes',
					'accumlated_hour':0
				})
			else:
				hour = self.request_hour(line,line_obj,request_id,record)					  
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'accumlated_hour':hour,
					'is_request': 'yes'
				})
		# elif line['is_work'] not in ('overtime_hour','attendance','attendance_out','working','work_night'):
			
		# 	line_obj.update({
		# 		'leave_request_start': dt_in,
		# 		'leave_request_end': dt_out,
		# 		'is_request': 'yes'
		# 	})
		elif line['is_work'] == 'work_day':
			hour = self.request_hour(line,line_obj,request_id,record)					  
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'worked_hour':0,			
				'night_hour':0,
				'over_work_day':request_id.number_of_hour,
				'is_request': 'yes',
			})
		elif line['is_work'] == 'over_day':
			hour = self.request_hour(line,line_obj,request_id,record)					  
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				# 'shift_plan_id':line['hst_id'],
				'over_work_day':request_id.number_of_hour,
				'is_request': 'yes',
			})
		elif line['is_work'] == 'worked':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				# 'shift_plan_id':line['hst_id'],
				'worked_salary_hour':request_id.number_of_hour,
				# 'worked_hour':request_id.number_of_hour,
				'is_request': 'yes',
			})
		elif line['is_work'] == 'night_over':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'over_work_night':request_id.number_of_hour,
				'is_request': 'yes',
			})
		elif line['is_work'] == 'over_night':
			hour = self.request_hour(line,line_obj,request_id,record)
			lunch_hour = 1
			if request_id.time_from <=22:
				if request_id.time_to >=6:
					req_ot = 22 - request_id.time_from +request_id.time_to-6
				else:
					req_ot = 22 - request_id.time_from
			else:
				if request_id.time_to <=6:
					over_night = request_id.number_of_hour
					req_ot = 0
				else:
					req_ot = request_id.time_to-6
			over_night = request_id.number_of_hour - req_ot
				
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				# 'shift_plan_id':line['hst_id'],
				'over_work_night':over_night,
				'over_work_day':req_ot,
				'is_request': 'yes',
				# 'worked_hour':0,
				'worked_salary_hour':over_night+req_ot+ line_obj.worked_hour
			})
		elif line['is_work'] == 'work_night':
			hour = self.request_hour(line,line_obj,request_id,record)
			lunch_hour = 1
			if request_id.time_from <=22:
				if request_id.time_to >=6:
					req_ot = 22 - request_id.time_from +request_id.time_to-6
				else:
					req_ot = 22 - request_id.time_from
			else:
				if request_id.time_to <=6:
					over_night = request_id.number_of_hour
					req_ot = 0
				else:
					req_ot = request_id.time_to-6
			over_night = request_id.number_of_hour - req_ot
				
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				# 'shift_plan_id':line['hst_id'],
				'over_work_night':over_night,
				'over_work_day':req_ot,
				'is_request': 'yes',
				'worked_hour':0,
				# 'worked_salary_hour':over_night+req_ot
			})
		elif line['is_work']=='attendance' and line['date_from']:
			att_dt = datetime.strptime(str(line['date_from']+timedelta(hours=8)), DATETIME_FORMAT).date()
			date_from = datetime.strptime(str(request_id.date_from), DATETIME_FORMAT) + timedelta(hours=8)
			line_obj = self.env['hr.timetable.line.line'].search([('date','=',att_dt),('parent_id','=',record[1])],limit=1)
			line_obj = line_line_pool.browse(line_obj.id)
			out=None
			if line_obj.end_time:
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'sign_in':att_dt,
					'sign_in_emp':date_from,
					'is_request': 'yes'
				})
		elif line['is_work']=='attendance_out' and line['date_from']:
			att_dt = datetime.strptime(str(line['date_from']), DATETIME_FORMAT).date()
			line_obj = self.env['hr.timetable.line.line'].search([('date','=',att_dt),('parent_id','=',record[1])],limit=1)
			line_obj = line_line_pool.browse(line_obj.id)
			out=None
			if line_obj.end_time:
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'sign_out':att_dt,
					'sign_out_emp':att_dt,
					'is_request': 'yes'
				})

	def req_overtime(self,shift_pool,line_obj,line):
		if line_obj.parent_id.parent_id.is_attendance==True and line_obj.parent_id.parent_id.is_mining!=True:
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'overtime_hour':shift_pool.number_of_hour,
				'req_overtime_hour':shift_pool.number_of_hour,
				'is_request': 'yes'
			})
		else:
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'req_overtime_hour':shift_pool.number_of_hour,
				'is_request': 'yes'
			})

	# Хүсэлтийн цаг фонд цагаас давсан эсэхийг шалгах функц
	def request_hour(self,rec,line_obj,request_id,record):
		req_out=None
		req_in = None
		e_work = None
		s_work = None
		dt_in = None
		dt_out = None
		hour=0
		if request_id.date_from:
			date_from = datetime.strptime(str(request_id.date_from), DATETIME_FORMAT)+ timedelta(hours=8)
			
			# Хүсэлийн цагийн Datetime руу хөрвүүлэн оноох
			dt_in, dt_out = self.leave_convert_datetime(rec,date_from)
			if dt_in:
				req_in = datetime.strptime(str(dt_in), DATETIME_FORMAT)
			if dt_out:
				req_out = datetime.strptime(str(dt_out), DATETIME_FORMAT)
		# АЗохих эхлэх дуусах цаг
			if line_obj.end_time:
				e_work = datetime.strptime(str(line_obj.end_time),DATETIME_FORMAT)
			if line_obj.start_time:
				s_work = datetime.strptime(str(line_obj.start_time),DATETIME_FORMAT)
			if req_out and e_work and req_in and s_work:
				if req_out > e_work:
					# Хүсэлтйин дуусах цаг АЗ дуусах цагаас их бол АЗ дуусах цагаар хязгаарлана
					zz=e_work - req_in
					zz_s = zz.total_seconds()
					minuts = divmod(zz_s, 60)[0] + divmod(zz_s, 60)[1]
					if line_obj.hour_to_work >= minuts/60:
						hour = minuts/60
					else:
						hour = line_obj.hour_to_work
				elif req_in < s_work:
				# Хүсэлтийн эхлэх цаг АЗохих эхоэх цагаас бага бол АЗ эхлэх цагаар хязгаарлана
					zz=s_work - req_out
					zz_s = zz.total_seconds()
					minuts = divmod(zz_s, 60)[0] + divmod(zz_s, 60)[1]
					if line_obj.hour_to_work >= minuts/60:
						hour = minuts/60
					else:
						hour = line_obj.hour_to_work
				else:
					if line_obj.hour_to_work >= request_id.number_of_hour:
						hour =request_id.number_of_hour
					else:
						hour = line_obj.hour_to_work
			else:
				if line_obj.parent_id.parent_id.is_attendance==True and line_obj.parent_id.parent_id.is_mining!=True:
					if line_obj.hour_to_work > request_id.number_of_hour:
						hour = request_id.number_of_hour
					else:
						hour = line_obj.hour_to_work
				else:
					hour = request_id.number_of_hour
			return hour
	

	def leave_request_attendance(self,rec,record):
		line_line_pool= self.env['hr.timetable.line.line']
		s_work = None
		if rec['is_work']=='attendance' and rec['date_from']:
			att_dt = datetime.strptime(str(rec['date_from']+timedelta(hours=8)), DATETIME_FORMAT).date()
			line_obj = self.env['hr.timetable.line.line'].search([('date','=',att_dt),('parent_id','=',record[1])],limit=1)
			line_obj = line_line_pool.browse(line_obj.id)
			if line_obj.start_time:
				s_work = datetime.strptime(str(line_obj.start_time), DATETIME_FORMAT)
			if rec['date_from']:
				date_from = datetime.strptime(str(rec['date_from']), DATETIME_FORMAT)
			if line_obj.sign_in:
				out = datetime.strptime(str(line_obj.sign_in), DATETIME_FORMAT)
				if out > rec['date_from']:
					line_obj.update({
						'shift_attribute_id':rec['hst_id'],
						'sign_out':out,
						'sign_in':rec['date_from'],
						'sign_out_emp':out,
						'sign_in_emp':rec['date_from'],
						'is_request': 'yes'
					})
				else:
					if s_work:
						if date_from > s_work:
							line_obj.update({
								'shift_attribute_id':rec['hst_id'],
								'sign_in':date_from,
								'sign_in_emp':date_from,
								'is_request': 'yes'
							})
						else:
							line_obj.update({
								'shift_attribute_id':rec['hst_id'],
								'sign_in':s_work,
								'sign_in_emp':s_work,
								'is_request': 'yes'
							})
					else:
						line_obj.update({
								'shift_attribute_id':rec['hst_id'],
								'sign_in':date_from,
								'sign_in_emp':date_from,
								'is_request': 'yes'
							})
			else:
				if s_work:
					if date_from > s_work:
						line_obj.update({
								'shift_attribute_id':rec['hst_id'],
								'sign_in':date_from,
								'sign_in_emp':date_from,
								'is_request': 'yes'
							})
					else:
						line_obj.update({
								'shift_attribute_id':rec['hst_id'],
								'sign_in':s_work,
								'sign_in_emp':s_work,
								'is_request': 'yes'
							})
				else:
					line_obj.update({
								'shift_attribute_id':rec['hst_id'],
								'sign_in':date_from,
								'sign_in_emp':date_from,
								'is_request': 'yes'
							})
		elif rec['is_work']=='attendance_out' and rec['date_to']:
			att_dt = datetime.strptime(str(rec['date_to']), DATETIME_FORMAT).date()
			line_obj = self.env['hr.timetable.line.line'].search([('date','=',att_dt),('parent_id','=',record[1])],limit=1)
			line_obj = line_line_pool.browse(line_obj.id)
			out=None
			if line_obj.end_time:
				line_obj.update({
					'shift_attribute_id':rec['hst_id'],
					'sign_out':line_obj.end_time,
					'sign_out_emp':rec['date_to'],
					'is_request': 'yes'
				})
	

	# Хүсэлтийн цагийг Datetime хуу хөрвүүлэх
	def leave_convert_datetime(self,rec,date_from):
		dt_in = None
		dt_out = None
		if rec['is_work'] not in ('overtime_hour','attendance','attendance_out','working'):
			req_time = 0
			req_time_out=0
			req_min=0
			req_min_out=0
			year_del=date_from.strftime("%Y")
			month_del=date_from.strftime("%m")
			day_del=date_from.strftime("%d")
			if rec['time_from']:
				req_time = int(rec['time_from'])
				if rec['time_from']-req_time>0:
					req_min = int((rec['time_from']-req_time)*60)
			datetime_in =year_del+'-'+month_del+'-'+day_del+' '+str(req_time)+':'+str(req_min)+':'+'00'
			if rec['time_to']:
				req_time_out = int(rec['time_to'])
				if rec['time_to']-req_time_out>0:
					req_min_out = int((rec['time_to']-req_time_out)*60)
		
			datetime_out =year_del+'-'+month_del+'-'+day_del+' '+str(req_time_out)+':'+str(req_min_out)+':'+'00'
			dt_in = datetime.strptime(str(datetime_in), DATETIME_FORMAT) - timedelta(hours=8)
			dt_out = datetime.strptime(str(datetime_out), DATETIME_FORMAT) - timedelta(hours=8)
		return dt_in,dt_out

	# Цагийн хүсэлт цуцлах
	def cancel_holiday_time(self):
		line_pool=self.env['hr.timetable.line'].search([('parent_id', '=', self.id)])
		for line in line_pool:
			line_line_pool=self.env['hr.timetable.line.line'].search([('is_request', '=', 'yes'),('parent_id', '=', line.id)])
			for obj in line_line_pool:
				obj.update({
					'shift_attribute_id':obj.shift_plan_id.id,
					'free_wage_hour':0,
					'training_hour':0,
					'free_hour':0,
					'sick_hour':0,
					'overtime_hour':0,
					'vacation_day':0,
					'parental_hour':0,
					'busines_trip_hour':0,
					'out_working_hour':0,
					'online_working_hour':0,
					'accumlated_hour':0,
					'is_request': 'no',
					'leave_request_start':None,
					'over_work_night':0,
					'over_work_day':0,
				})
