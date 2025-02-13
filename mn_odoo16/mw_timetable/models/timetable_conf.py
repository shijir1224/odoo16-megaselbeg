
# -*- coding: utf-8 -*-
# Цагийн төлөвлөгөөний тохиргоо хэсэг
import time
import datetime
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import calendar
from odoo.osv import osv

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class HrTimetable(models.Model):
	_inherit = "hr.timetable"

	#Тухайн сарын ростер дуусахад энэ товчийг заавал дарж ажилтны ростерийн эхлэх огноо, өдрийг шинэчилнэ
	def date_update(self):
		history_pool = self.env['date.history']
		for line in self.line_ids:
			emp_pool = self.env['hr.employee'].search(
				[('id', '=', line.employee_id.id)])
			history_id = history_pool.create({
				'employee_id': line.employee_id.id,
				'user_id': self.env.uid,
				'date': emp_pool.start_date,
				'update_date': date.today(),
				'day': emp_pool.start_day,
				'n_start_day': emp_pool.n_start_day,
				'w_start_day': emp_pool.w_start_day,
				'start_date': self.date_from,
				'end_date': self.date_to,
			})

			lll = self.env['hr.timetable.line.line'].search(
				[('date', '=', self.date_to), ('parent_id', '=', line.id)])
			to_dt = datetime.strptime(str(self.date_to), DATE_FORMAT).date()
			end_date = to_dt+timedelta(days=1)
			if lll.is_work_schedule=='day' or lll.is_work_schedule=='night':
				emp_pool.update({'start_date': end_date,
							 'w_start_day': lll.number,
							 'n_start_day': 0,
							 'start_day': lll.number+1})
			elif lll.is_work_schedule=='none':
				emp_pool.update({'start_date': end_date,
							 'n_start_day': lll.number,
							 'w_start_day': 0,
							 'start_day': lll.number+1})
			else:
				emp_pool.update({'start_date': end_date,
							 'start_day': lll.number+1})

	#5 Цагийн төлөвлөгөөг гараас зассан үед Create line дарвал бүгд цэвэрлэгдэнэ.Тиймээс ажилтан нэмэх товчоор ажилтан нэмж болно
	def create_add_data_pool(self):
		balance_data_pool = self.env['hr.timetable.line']
		line_line_pool = self.env['hr.timetable.line.line']
		for emp in self.employee_ids:
			line_emp = self.env['hr.timetable.line'].search([('parent_id', '=', self.id),('employee_id', '=', emp.id)],limit=1)
			if not line_emp:
				balance_data_pool = balance_data_pool.create({
					'employee_id': emp.id,
					'department_id': emp.department_id.id,
					'job_id': emp.job_id.id,
					'month': self.month,
					'year': self.year,
					'day_to_work_month':self.day_to_work_month,
					'hour_to_work_month':self.hour_to_work_month,
					'parent_id': self.id,
				})
				line_obj = balance_data_pool.browse(balance_data_pool)
				for line in line_obj:
					from_dt = datetime.strptime(
						str(self.date_from), DATE_FORMAT).date()
					to_dt = datetime.strptime(
						str(self.date_to), DATE_FORMAT).date()
					emp_obj = self.env['hr.employee'].search(
						[('id', '=', line.id.employee_id.id)], limit=1)
					if len(emp_obj) == 1:
						if emp_obj.start_date:
							start_date = datetime.strptime(
								str(emp_obj.start_date), DATE_FORMAT)
						else:
							raise osv.except_osv(u'%s кодтой %s ажилтны ростерийн тохиргоог оруулна уу' % (
								line.id.employee_id.identification_id, line.id.employee_id.name))
					else:
						raise osv.except_osv(u'%s кодтой %s ажилтны ростерийн бүртгэл алдаатай байна' % (
							line.id.employee_id.identification_id, line.id.employee_id.name))
					step = timedelta(days=1)
					while from_dt <= to_dt:
						public_hol_id=self.env['hr.public.holiday'].search([('days_date', '=', from_dt)])
						if public_hol_id:
							hol=True
						else:
							hol=False
						if to_dt >= from_dt:
							line_line_conf = line_line_pool.create({
								'date': from_dt,
								'parent_id': line.id.id,
								'employee_id': line.id.employee_id.id,
								'job_id': emp.job_id.id,
								'department_id': emp.department_id.id,
								'month': line.id.month,
								'year': line.id.year,
							})
							line_line_obj = line_line_pool.browse(line_line_conf)	
							self.create_employee(line_line_obj,emp_obj,from_dt,start_date,line,hol)
							from_dt += step
			else:
				raise UserError(_('%s дугаартай ажилтаны цаг орсон байна.')%(line_emp.employee_id.identification_id))
	def create_employee(self,line_line_obj,emp_obj,from_dt,start_date,line,hol):
		snum = 1
		sss_k = 0
		num = start_date.day
		sss_k = from_dt.day+emp_obj.start_day-num
		for ll in line_line_obj:
			step = timedelta(days=1)
			shift_line_ids = self.env['hr.shift.line'].search([('shift_id', '=', line.id.employee_id.roster_id.id), ('number', '=', sss_k)])
			if shift_line_ids:
				if emp_obj.roster_id:

					if from_dt.day >= start_date.day:
						if hol==True:
							holiday_id = self.env['hr.shift.time'].search([('is_work', '=','public_holiday')],limit=1)
							vals = ll.id.get_line_vals({'number': shift_line_ids.number,
										'date': from_dt,
										'is_work_schedule': holiday_id.is_work,
										'shift_plan_id': holiday_id.id,
										'shift_attribute_id': holiday_id.id,
										'hour_to_work': holiday_id.compute_sum_time,
										'is_public_holiday':hol,
										})
							ll.id.update(vals)
						else:
							vals = ll.id.get_line_vals({'number': shift_line_ids.number,
										'date': from_dt,
										'is_work_schedule': shift_line_ids.is_work,
										'shift_plan_id': shift_line_ids.name.id,
										'shift_attribute_id': shift_line_ids.name.id,
										'hour_to_work': shift_line_ids.compute_sum_time,
										'employee_id': emp_obj.id,
										})
							ll.id.update(vals)
					else:
						ll.id.update({
							'is_work_schedule': 'none',
						})
			else:
				shift_line_ids = self.env['hr.shift.line'].search(
					[('shift_id', '=', line.id.employee_id.roster_id.id), ('number', '=', snum)])
				if shift_line_ids.number == len(emp_obj.roster_id.line_ids):
					snum = 1
				else:
					snum += 1
				if sss_k > 0:
					if hol==True:
						holiday_id = self.env['hr.shift.time'].search([('is_work', '=','public_holiday')],limit=1)
						vals = ll.id.get_line_vals({'number': shift_line_ids.number,
									'date': from_dt,
									'is_work_schedule': holiday_id.is_work,
									'shift_plan_id': holiday_id.id,
									'shift_attribute_id': holiday_id.id,
									'hour_to_work': holiday_id.compute_sum_time,
									'is_public_holiday':hol,
									})
						ll.id.update(vals)
					else:
						vals = ll.id.get_line_vals({'number': shift_line_ids.number,
							'date': from_dt,
							'is_work_schedule': shift_line_ids.is_work,
							'shift_plan_id': shift_line_ids.name.id,
							'shift_attribute_id': shift_line_ids.name.id,
							'hour_to_work': shift_line_ids.compute_sum_time,
							'employee_id': emp_obj.id,
							})
						ll.id.update(vals)
				else:
					ll.id.update({
						'is_work_schedule': 'none',
					})

			from_dt += step
			sss_k += 1
		
	def import_holiday_time_emp(self):
		for emp in self.employee_ids:
			query = """SELECT 
				employee_id,
				id
				FROM hr_timetable_line
				WHERE parent_id=%s and employee_id= %s
				"""%(self.id,emp.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
			for record in records:
				query_all = """SELECT
					tc.id as id,
					tc.create_date as create_date,
					tc.date_from as date_from,
					tc.date_to as date_to,
					tc.time_from as time_from,
					tc.time_to as time_to,
					hst.is_work as is_work,
					tc.create_date as create_date,
					hr.identification_id as identification_id,
					hst.id as hst_id
					FROM hr_leave_mw tc
					LEFT JOIN hr_shift_time hst ON hst.id=tc.shift_plan_id
					LEFT JOIN hr_employee hr ON hr.id=tc.employee_id
					WHERE tc.employee_id=%s and tc.state_type='done'
				""" % (record[0])
				self.env.cr.execute(query_all)
				recs_all = self.env.cr.dictfetchall()
				for line in recs_all:
					self.update_line_obj(line,record)


	def action_update_shift_emp(self):
		if self.sh_date_from and self.sh_date_to and self.shift_id:
			for item in self.employee_ids:
				for l in self.line_ids:
					step = timedelta(days=1)
					if l.employee_id.id == item.id:
						for ll in l.line_ids:
							from_dt = datetime.strptime(
							str(self.sh_date_from), DATE_FORMAT).date()
							to_dt = datetime.strptime(
								str(self.sh_date_to), DATE_FORMAT).date()				
							while from_dt <= to_dt:
								if ll.date == from_dt:
									if self.shift_id.is_work != 'none':
										ll.update({
											'shift_plan_id':self.shift_id,
											'shift_attribute_id':self.shift_id,
											})
									else:
										ll.update({
											'shift_plan_id':self.shift_id,
											'shift_attribute_id':self.shift_id,
											})
								from_dt += step
    # Ажилтан сонгож ирц татах
	def import_attendance_emp(self):
		for obj in self.employee_ids:
			query = """SELECT
				employee_id
				FROM hr_timetable_line
				WHERE parent_id=%s and employee_id=%s
				""" % (self.id,obj.id)
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
				""" % (record[0], self.date_from, self.date_to)
				self.env.cr.execute(query)
				querys = self.env.cr.fetchall()
				for line in querys:
					self.set_attendance(line,record)


# Бүх ажилтны хуваарь солих
	def action_update_shift(self):
		for l in self.line_ids:
			step = timedelta(days=1)
			for ll in l.line_ids:
				if self.sh_date_from and self.sh_date_to and self.shift_id:
					from_dt = datetime.strptime(
					str(self.sh_date_from), DATE_FORMAT).date()
					to_dt = datetime.strptime(
						str(self.sh_date_to), DATE_FORMAT).date()				
					while from_dt <= to_dt:
						if ll.date == from_dt:
							if self.shift_id.is_work != 'none':
								ll.update({
									# 'shift_plan_id':self.shift_id,
									'shift_attribute_id':self.shift_id,
									})
							else:
								ll.update({
									# 'shift_plan_id':self.shift_id,
									'shift_attribute_id':self.shift_id,
									'sickness_hour':0,
									})
						from_dt += step

# Бүх ажилтны ирц оноох
	def action_update_attendance(self):
		for l in self.line_ids:
			reto_update = None
			refrom_update = None
			for ll in l.line_ids:
				if self.up_date_from and self.up_date_to:
					for emp in self.employee_ids:		
						step = timedelta(days=1)
						from_dt = datetime.strptime(str(self.date_from), DATE_FORMAT).date()
						to_dt = datetime.strptime(str(self.date_to), DATE_FORMAT).date()	
						if l.employee_id.id == emp.id:	
							while from_dt <= to_dt:
								if ll.date == from_dt:
									reto_update = self.up_date_to.replace(day=ll.date.day)
									refrom_update = self.up_date_from.replace(day=ll.date.day)
									if ll.is_work_schedule != 'none':
										ll.update({
												'sign_out':reto_update,
												'sign_out_emp':reto_update,
												'sign_in':refrom_update,
												'sign_in_emp':refrom_update,
											})
								from_dt += step
