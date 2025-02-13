# -*- coding: utf-8 -*-

import calendar
from datetime import datetime

import datetime
from datetime import  datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval as eval
import numpy as np
from odoo import api, fields, models, _
import xlrd
from tempfile import NamedTemporaryFile
import os
import base64
from odoo import  models, _
from odoo.osv import osv
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class HourBalanceDynamicConfiguration(models.Model):
	_inherit = "hour.balance.dynamic.configuration"
	
	hour_type = fields.Selection(
		[
			("working", "Ажилласан цаг"),
			("working_ub", "УБ Ажилласан цаг"),
			("working_day", "Ажилласан өдөр"),
			("overtime", "Илүү цаг"),
			("accumlated", "Нөхөн амрах"),
		],
		"Цагийн төрөл",
		tracking=True,
	)

class HourBalanceDynamic(models.Model):
	_inherit = "hour.balance.dynamic"


	hour_to_work = fields.Float('АЗ цаг бүтэн')
	day_to_work_month = fields.Float("Ажиллавал зохих өдөр", compute='_compute_hour_to_work',digits=(2, 0))
	hour_to_work_month = fields.Float("Ажиллавал зохих цаг", compute='_compute_hour_to_work', digits=(2, 0))
	group = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')], string='Бүлэг')
	shift_g = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')], string='Бүлэг')
	h_emp_id = fields.Many2one("hr.employee", "Хянасан")
	state = fields.Selection(
		[
			("draft", "Ноорог"),
			("send", "Илгээсэн"),
			("confirm", "Хянасан"),
			("confirm_ahlah", "Баталсан"),
			("done", "НЯБО хүлээж авсан"),
			("refuse", "Цуцлагдсан"),
		],"Төлөв",
		readonly=True,
		default="draft",
		tracking=True,
		copy=False,
	)

	def action_confirm(self):
		self.write({"state": "confirm"})
	

	def balance_line_create(self):
		timetable_data_pool = self.env["hr.timetable.line"].search(
			[("year", "=", self.year), ("month", "=", self.month)]
		)
		htw = 0
		htd = 0
		if self.balance_line_ids:
			self.balance_line_ids.unlink()
		sequence=1
		for bll in timetable_data_pool:
			if self.is_htw_plan == True:
				query = """SELECT sum(tl.hour_to_work) as hour
						FROM hr_timetable_line_line tl
						LEFT JOIN hr_timetable_line al ON al.id=tl.parent_id 
						LEFT JOIN hr_shift_time hs ON hs.id=tl.shift_plan_id
						WHERE al.id=%s and date>='%s' and date<='%s' and hs.is_work not in ('out')
						""" % (bll.id,self.date_from,self.date_to)
				self.env.cr.execute(query)
				records = self.env.cr.dictfetchall()			
				if records[0]:
					htw = records[0]["hour"]
				else:
					htw = 0
				query_day = """SELECT count(tl.id) as count
						FROM hr_timetable_line_line tl
						LEFT JOIN hr_timetable_line al ON al.id=tl.parent_id 
						LEFT JOIN hr_shift_time sht ON sht.id=tl.shift_plan_id 
						WHERE al.id=%s and sht.is_work not in ('none','public_holiday','out') and date>='%s' and date<='%s'
						""" %(
					bll.id,
					self.date_from,
					self.date_to,
				)
				self.env.cr.execute(query_day)
				recs = self.env.cr.dictfetchall()
				if recs[0]:
					htd = recs[0]["count"]
				else:
					htd = 0
			else:
				htw = self.hour_to_work_month
				htd = self.day_to_work_month
			emp = self.env["hr.employee"].search([("id", "=", bll.employee_id.id),("company_id", "=", self.company_id.id),("work_location_id", "=", self.work_location_id.id)],limit=1)
			if self.department_id and not self.shift_g:
				if emp.department_id == self.department_id:
					self.create_pool(bll, emp, htw, htd,sequence)
					sequence+=1
			elif self.shift_g and self.department_id:
				if emp.shift_g == self.shift_g and emp.department_id == self.department_id:
					self.create_pool(bll, emp, htw, htd,sequence)
					sequence+=1
			else:
				emp_all = self.env["hr.employee"].search(
				[("id", "=", bll.employee_id.id),("company_id", "=", self.company_id.id)],
				limit=1,)
				self.create_pool(bll, emp_all, htw, htd,sequence)
				sequence+=1

	def create_conf_both(self, cl, bp, balance_line_data_pool):
		balance_line_hour_data_pool = self.env["hour.balance.dynamic.line.line.hour"]
		hour=0
		hour2=0
		hour1=0
		hour3=0
		hour4=0
		if self.date_from and self.date_to:
			if cl.query:
				query_ex = cl.query % (
					bp.timetable_line_id.id,
					self.date_from,
					self.date_to,
				)
				self.env.cr.execute(query_ex)
				records = self.env.cr.dictfetchall()
			for rec in records:
				if rec["hour"]:
					hour = round(rec["hour"],2)
			
				if 'hour2' in cl.query:
					if rec["hour2"]:
						hour2 = round(rec["hour2"],2)
				
				if 'hour1' in cl.query:
					if rec["hour1"]:
						hour1 = round(rec["hour1"],2)
				
				if 'hour3' in cl.query:
					if rec["hour3"]:
						hour3 = round(rec["hour3"],2)
					
				if 'hour4' in cl.query:
					if rec["hour4"]:
						hour4 = round(rec["hour4"],2)
				
				balance_line_pool = balance_line_data_pool.create({"parent_id": bp.id, "hour": hour, "conf_id": cl.id,"hour_type": cl.hour_type})

				balance_line_hour_pool = balance_line_hour_data_pool.create({"parent_id": bp.id, "name": hour,"conf_id": cl.id})
				if balance_line_pool:
					localdict={'line':balance_line_pool,'result':None,'htw':bp.hour_to_work_month,'hour':hour,'hour2':hour2,'hour1':hour1,'hour3':hour3,'hour4':hour4}
					tomyo=balance_line_pool.conf_id.tomyo
					if '/' in tomyo:
						try:
							eval('%s'%(tomyo), localdict, mode='exec', nocopy=True) 
						except ValueError:
							raise Warning((u'%s цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.name)))
					else:
						eval('%s' %(tomyo), localdict, mode='exec', nocopy=True)#  
						balance_line_pool.write({"hour":localdict['result']})
				if balance_line_hour_pool:
					localdict={'result':None,'htw':bp.hour_to_work_month,'hour':hour,'hour2':hour2,'hour1':hour1,'hour3':hour3,'hour4':hour4}
					tomyo=balance_line_hour_pool.conf_id.tomyo
					eval('%s' %(tomyo), localdict, mode='exec', nocopy=True)#  
					balance_line_hour_pool.write({"name":localdict['result']})
	
	@api.depends('date_from','date_to')
	def _compute_hour_to_work(self):
		for item in self:
			day_too=0		
			if item.date_from and item.date_to:
				holiday = self.env['hr.public.holiday'].search([('days_date','>=',item.date_from),('days_date','<=',item.date_to)])
				date_to = item.date_to + relativedelta(days=1)
				if item.type =='final':
					if holiday:
						for hh in holiday:
							day_too += 1 if hh.days_date.weekday() < 5 else 0
							days = np.busday_count(item.date_from, date_to)
							item.day_to_work_month = (days - day_too)
							item.hour_to_work_month = (days - day_too) * 8
					else:
						days = np.busday_count(item.date_from, date_to)
						item.day_to_work_month = days 
						item.hour_to_work_month =days * 8
				else:
					date_to = item.date_from + relativedelta(months=1)
					holiday = self.env['hr.public.holiday'].search([('days_date','>=',self.date_from),('days_date','<',date_to)])
					if holiday:
						for hh in holiday:
							day_too += 1 if hh.days_date.weekday() < 5 else 0
							days = np.busday_count(item.date_from, date_to)
							item.day_to_work_month = (days - day_too)
							item.hour_to_work_month = (days - day_too) * 8
					else:
						days = np.busday_count(item.date_from, date_to)
						item.day_to_work_month = days
						item.hour_to_work_month = days * 8
			else:
				item.hour_to_work_month = 0
				item.day_to_work_month = 0
				


	def create_pool(self, bll, emp, htw, htd,sequence):
		balance_data_pool = self.env["hour.balance.dynamic.line"]
		bp = balance_data_pool.create(
			{
				"timetable_line_id": bll.id,
				"employee_id": emp.id,
				"year": self.year,
				"month": self.month,
				"day_to_work_month": htd,
				"hour_to_work_month": htw,
				"hour_to_work":self.hour_to_work,
				"parent_id": self.id,
				"identification_id": emp.identification_id,
				"department_id": emp.department_id.id,
				"job_id": emp.job_id.id,
				"sequence":sequence
			}
		)
		self.create_conf(bp)


	def action_done(self):
		for line in self.balance_line_ids:
			line.write({"state": "done"})	
		self.write({"state": "done"})

	def action_import_hour_balance(self):
		balance_pool =  self.env['hour.balance.dynamic.line']
		balance_line_pool =  self.env['hour.balance.dynamic.line.line']
		balance_line_hour_pool = self.env['hour.balance.dynamic.line.line.hour']
		if self.balance_line_ids:
			self.balance_line_ids.unlink()
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Aldaa')
		nrows = sheet.nrows
		ncols = sheet.ncols
		for item in range(6,nrows):
			row = sheet.row(item)
			default_code = row[2].value
			day_to_work_month = row[5].value
			hour_to_work_month = row[6].value
			hour_to_work = row[7].value
			employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
			if employee_ids:
				balance_data_ids = balance_pool.create({'employee_id':employee_ids.id,
							'year':self.year,
							'month':self.month,
							'parent_id': self.id,
							'department_id':employee_ids.department_id.id,
							'job_id':employee_ids.job_id.id,
							'employee_type':employee_ids.employee_type,
							'day_to_work_month':day_to_work_month,
							'hour_to_work_month':hour_to_work_month,
							'hour_to_work':hour_to_work,
							})
				for dd in balance_data_ids:
					# дугаарлалт авах 8 буюу H багана
					col = 8
					#  дугаарлалт авах 5 мөр
					rowh = sheet.row(5)
					for ncol in range(8,ncols):
						number = rowh[col].value
						conf_pool =  self.env['hour.balance.dynamic.configuration'].search([('number','=',number)],limit=1)
						if conf_pool:
							balance_line_pool = balance_line_pool.create({
									'parent_id':dd.id,
									'conf_id':conf_pool.id,
									'hour':row[col].value,
									})
							balance_line_hour_pool = balance_line_hour_pool.create({
									'parent_id':dd.id,
									'conf_id':conf_pool.id,
									'name':row[col].value,
									})
							number = []
							col +=1
							item +=1
						else:
							raise UserError(_('%s дугаартай цагийн тохиргоо хийгдээгүй байна.')%(number))
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

class HourBalanceLineDynamic(models.Model):
	_inherit = "hour.balance.dynamic.line"
	_order = "name"

	name= fields.Char('Ажилтны код', readonly='1',related='employee_id.name',store=True)
	hour_to_work = fields.Float('АЗ цаг бүтэн')
	total_worked_hour = fields.Float("Нийт ажилласан цаг", digits=(3, 2), default=0,compute='_compute_worked_hour',store=True)

	@api.depends('balance_line_line_ids')
	def _compute_worked_hour(self):
		for item in self:
			total_worked_hour=0
			for bl in item.balance_line_line_ids:
				if bl.conf_id.hour_type=='working':
					total_worked_hour = bl.hour
			item.total_worked_hour = total_worked_hour
class HourBalanceDynamicLineLine(models.Model):
	_inherit = "hour.balance.dynamic.line.line"


	hour_type = fields.Selection(
		[
			("working", "Уурхай Ажилласан цаг"),
			("working_ub", "УБ Ажилласан цаг"),
			("working_day", "Ажилласан өдөр"),
			("overtime", "Илүү цаг"),
			("accumlated", "Нөхөн амрах"),
		],
		"Цагийн төрөл",
		tracking=True,
	)

class HrTimetable(models.Model):
	_inherit = "hr.timetable"

	shift = fields.Selection([('office', 'Оффис'), ('d', '1-р ээлж'), ('e', '2-р ээлж'), ('f', '3-р ээлж'), ('g', '4-р ээлж'), ('k', '5-р ээлж'),('l', '6-р ээлж'), ('m', '7-р ээлж'), ('n', '8-р ээлж'), ('o', '9-р ээлж'), ('r', '10-р ээлж'), ('w', '11-р ээлж')], default='office', string='Ээлж')


	def set_conditions(self):
		conditions = ""
		if  self.department_id and self.work_location_id:
			conditions = "and wl.id= %s" % self.work_location_id.id
			conditions +=  " and hd.id = %s " % self.department_id.id
			if self.shift:
				conditions += " and he.shift ='%s' " % self.shift
		return conditions
	
	def daterange(self, start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)

	def create_data_pool(self,balance_data_pool,line_line_pool):
		super(HrTimetable,self).create_data_pool(balance_data_pool,line_line_pool)	
		lines = self.env['hr.timetable.line'].search([('parent_id','=',self.id)])
		for line in lines:
			line_lines = self.env['hr.timetable.line.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('parent_id','=',line.id)])
			for item in line_lines:
				for single_date in self.daterange(self.date_from, self.date_to):
					public_hol_id=self.env['hr.public.holiday'].search([('days_date', '=', single_date)],limit=1)
					hol=True if public_hol_id else False
					if single_date == item.date:
						if single_date.weekday() < 5:
							item.update({
								'is_weekend':False,
								'project_id': line.employee_id.hr_p_id.id,
								'is_public_holiday':hol,
							})
						else:
							item.update({
								'is_weekend':True,
								'project_id': line.employee_id.hr_p_id.id,
								'is_public_holiday':hol,
							})

	def create_this_month(self):
		balance_data_pool = self.env['hr.timetable.line']
		line_line_pool = self.env['hr.timetable.line.line']
		query = """SELECT
			he.id as emp_id,
			hd.id as dep_id,
			hj.id as hj_id,
			wl.id as wl_id,
			hp.id as hp_id
			FROM hr_employee he
			LEFT JOIN hr_department hd On hd.id=he.department_id
			LEFT JOIN hr_job hj On hj.id=he.job_id
			LEFT JOIN hr_project hp On hp.id=he.hr_p_id
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
					if self.shift:
						resigned_emps = self.env['hr.employee'].search([('is_this_month_wage', '=', True),('work_end_date', '>=', self.date_from),('work_end_date', '<=', self.date_to),('employee_type', '=', 'resigned'),('work_location_id', '=', self.work_location_id.id),('shift', '=', self.shift),('department_id', '=', self.department_id.id)])
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

	def up_get_line_vals(self,sss_k,hol,ll,from_dt,none_id,shift_line):
		if sss_k > 0:
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

	# Ирц оноох
	def set_attendance(self,line,record):
		line_line_pool = self.env['hr.timetable.line.line']
		line_id = line[0]
		line_obj = line_line_pool.search([('id', '=', line_id)])
		datetime_in = self.hour_minute_replace(line_obj.date) - timedelta(hours=8)
		att_len = self.env['mw.attendance'].sudo().search([('employee_id','=',record[0]),('date','=',line[1])])
		att_in=None
		add_in_hour=None
		mi_in_hour=None
		add_out_hour=None
		# Ирц ганцхан байх үед
		if len(att_len)==1:
			# Лимит тооцохгүй бол
			att_in_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]), ('attendance_time', '>=', datetime_in)], order='attendance_time asc', limit=1)
			
			if att_in_id:
				# Орсон цаг
				att_in = datetime.strptime(str(att_in_id.attendance_time), DATETIME_FORMAT)
				# Орсон гарсан ирц рүү онооход интервал тооцох
				if line_obj.start_time:
					# Орох цагаас интервал
					add_in_hour = line_obj.start_time + timedelta(hours=7)
					mi_in_hour = line_obj.start_time - timedelta(hours=2)
				if line_obj.end_time:
					# Гарах цагаас интервал
					add_out_hour = line_obj.end_time + timedelta(hours=14)
				if add_in_hour  and mi_in_hour:
					if att_in <= add_in_hour and att_in >= mi_in_hour:
						
						# гарсан ирц байхгүй бол хонож ажилласан хүний шөнийн ирцийг гарсан ирцэд татах
						att_tomm_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]+ timedelta(days=1))], order='attendance_time asc', limit=1)
						if att_tomm_id:
							att_tom_in = datetime.strptime(str(att_tomm_id.attendance_time), DATETIME_FORMAT)  + timedelta(hours=8)
							
							if att_tom_in.hour <=5:
								# Тухайн өдрийн 04 цаг == datetime_out
								if line_obj.shift_plan_id.is_work=='night':
									line_obj.update({
										'sign_in': line_obj.start_time,
										'sign_in_emp': att_in,
										'sign_out': line_obj.end_time,
										'sign_out_emp': att_tomm_id.attendance_time,
									})
								else:
									# Хонож ажилласан ажилтан орсон цагаас гарсан цагийг автоматаар тооцох
									line_obj.update({
										'sign_in': line_obj.start_time,
										'sign_in_emp': att_in,
										'sign_out': line_obj.end_time,
										'sign_out_emp': att_in + timedelta(hours=9),
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
					else:
						line_obj.update({
							'sign_out': line_obj.end_time,
							'sign_out_emp': att_in,
						})
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

	def set_att_in_out(self,line,record,line_obj):
		datetime_in = self.hour_minute_replace(line_obj.date)- timedelta(hours=8)
		datetime_out = self.hour_minute_replace(line_obj.date).replace(hour=23,minute=59)- timedelta(hours=8)
		# Лимитгүй татах Лимитээр татхаар орсон гарсан цаг хязгаарлагдаад ирц орж ирэхгүй байв
		att_out_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]),('attendance_time', '<=', datetime_out)], order='attendance_time desc',limit=1)
		att_in_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]), ('attendance_time', '>=', datetime_in)], order='attendance_time asc',limit=1)
		s_in=None
		s_out=None
		if att_in_id and att_out_id:
			s_in = datetime.strptime(str(att_in_id.attendance_time), DATETIME_FORMAT) + timedelta(hours=8)
			s_out = datetime.strptime(str(att_out_id.attendance_time), DATETIME_FORMAT)+ timedelta(hours=8)
			in_seconds = s_in.minute * 60 + s_in.second
			out_seconds = s_out.minute * 60 + s_out.second
			if line_obj.shift_plan_id.is_work in ('day','night','in_night','in','out'):
				if s_in.hour == s_out.hour and in_seconds + 600 >= out_seconds:
					# гарсан ирц байхгүй бол хонож ажилласан хүний шөнийн ирцийг гарсан ирцэд татах
					att_tomm_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', record[0]), ('date', '=', line[1]+ timedelta(days=1))], order='attendance_time asc', limit=1)
					if att_tomm_id:
						tom_in = datetime.strptime(str(att_tomm_id.attendance_time), DATETIME_FORMAT) + timedelta(hours=8)
						# Өдөр дамнасан цаг нь Орох лимитээс 2 цагиййн өмнө байх ажилласан 
						if tom_in.hour <= 6:
							line_obj.update({
								'sign_in_emp': att_in_id.attendance_time,
								'sign_in':att_in_id.attendance_time,
								'sign_out_emp': s_in + timedelta(hours=1),
								'sign_out':s_in + timedelta(hours=1),
							})
						else:
							line_obj.update({
								'sign_in_emp':  att_in_id.attendance_time,
								'sign_in': att_in_id.attendance_time,
								'sign_out_emp': None,
								'sign_out':None
							})
					else:
						line_obj.update({
							'sign_in': line_obj.start_time,
							'sign_in_emp': att_in_id.attendance_time,
							'sign_out': None,
							'sign_out_emp': None,
						})
				else:
					line_obj.update({
						'sign_in': att_in_id.attendance_time,
						'sign_in_emp': att_in_id.attendance_time,
						'sign_out': att_out_id.attendance_time,
						'sign_out_emp': att_out_id.attendance_time,
					})	
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

	def request_hour(self,rec,line_obj,request_id,record):
		hour=0
		# TODO Хүсэлтийн цагийн орсон гарсан цаг лимиттэй харицуулахгүй түр хаав
		if line_obj.hour_to_work >= request_id.number_of_hour:
			hour = round(request_id.number_of_hour,2)
		else:
			hour = line_obj.hour_to_work
		return hour
	
	def req_overtime(self,shift_pool,line_obj,line):
		if line_obj.parent_id.parent_id.is_attendance==True and line_obj.parent_id.parent_id.is_mining!=True:
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'req_overtime_hour':shift_pool.number_of_hour,
				'is_request': 'yes'
			})

	def request_set_line(self,line,line_obj,record,request_id):
		super(HrTimetable,self).request_set_line(line,line_obj,record,request_id)
		date_from = datetime.strptime(str(request_id.date_from), DATETIME_FORMAT) + timedelta(hours=8)
		dt_in, dt_out = self.leave_convert_datetime(line,date_from)
		line_obj.update({
			'leave_request_start': dt_in,
			'leave_request_end': dt_out,
		})
		if line['is_work']=='accumlated':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'accumlated_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='business_trip':
			# if request_id.project_id:
			if line_obj.is_public_holiday ==True:
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'holiday_worked_hour':request_id.number_of_hour,
					'busines_trip_hour':0,
					'is_request': 'yes',
					'project_id': request_id.project_id.id
				})
			else:
				if request_id.employee_id.work_location_id.location_number=='1':
					line_obj.update({
						'shift_attribute_id':line['hst_id'],
						'busines_trip_hour':request_id.number_of_hour,
						'is_request': 'yes',
						'project_id': request_id.project_id.id
					})
				else:
					# Амралтын өдөр бол томилолтын цаг илүү цаг руу орно 
					if line_obj.is_weekend==True:
						line_obj.update({
							'shift_attribute_id':line['hst_id'],
							'bt_hour':request_id.number_of_hour,
							'busines_trip_hour':0,
							'is_request': 'yes',
							'project_id': request_id.project_id.id
						})
					else:
						# if request_id.number_of_hour>=8:
						line_obj.update({
							'shift_attribute_id':line['hst_id'],
							'bt_hour':request_id.number_of_hour,
							'busines_trip_hour':0,
							'is_request': 'yes',
							'project_id': request_id.project_id.id
						})
						# else:
							# line_obj.update({
							# 	'shift_attribute_id':line['hst_id'],
							# 	'busines_trip_hour':request_id.number_of_hour,
							# 	'is_request': 'yes',
							# 	'project_id': request_id.project_id.id
							# })
			# else:
			# 	raise UserError(_('%s ажилтны томилолтын хүсэлт дээр төсөл сонгогдоогүй байна')%(request_id.employee_id.name))
		elif line['is_work']=='day':

			hour = self.request_hour(line,line_obj,request_id,record)					  
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'over_work_day':request_id.number_of_hour,
				'is_request': 'yes',
			})
		elif line['is_work']=='online_work':
			line_obj.update({
				'shift_plan_id':line['hst_id'],
				'shift_attribute_id':line['hst_id'],
				'online_working_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='night':
			hour = self.request_hour(line,line_obj,request_id,record)					  
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'over_work_night':request_id.number_of_hour,
				'is_request': 'yes',
			})
		elif line['is_work']=='out':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'tourist_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='in':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'tourist_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='none':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'tourist_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		elif line['is_work']=='out_work':
			hour = self.request_hour(line,line_obj,request_id,record)
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'out_working_hour':request_id.number_of_hour,
				'is_request': 'yes'
			})
		
		elif line['is_work']=='vacation':
			none_id = self.env['hr.shift.time'].search([('is_work', '=','none')],limit=1)
			if line_obj.shift_plan_id.is_work =='none':
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'is_request': 'yes',
					'vacation_day':0
				})
			elif line_obj.is_public_holiday == True:
				line_obj.update({
					'shift_attribute_id':none_id.id,
					'shift_plan_id':none_id.id,
					'is_request': 'yes',
					'vacation_day':request_id.number_of_hour,
				})
			else:
				line_obj.update({
					'shift_attribute_id':line['hst_id'],
					'shift_plan_id':line['hst_id'],
					'vacation_day':request_id.number_of_hour,
					'is_request': 'yes'
				})
		elif line['is_work'] =='public_holiday':
			line_obj.update({
				'shift_attribute_id':line['hst_id'],
				'shift_plan_id':line['hst_id'],
				'is_request': 'yes',
				'holiday_worked_hour':request_id.number_of_hour,
			})

	def leave_request_attendance(self,rec,record):
		line_line_pool= self.env['hr.timetable.line.line']
		s_work = None
		if rec['is_work']=='attendance' and rec['date_from']:
			att_dt = datetime.strptime(str(rec['date_from']), DATETIME_FORMAT).date()
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

class HrTimetableLine(models.Model):
	_inherit = "hr.timetable.line"

	overtime = fields.Float(string =u'Илүү цаг', digits=(3, 2),compute='_compute_overtime',store=True)
	z_hour = fields.Float(string =u'Зөрүү цаг', digits=(3, 2),compute='_compute_overtime',store=True)
	busines_trip_hour = fields.Float('Томилолтой цаг', digits=(3, 2),compute='_compute_bt_hour',store=True)
	busines_trip_hour2 = fields.Float('Томилолтой цаг 2', digits=(3, 2),compute='_compute_bt_hour',store=True)


	
	@api.depends('line_ids','line_ids.busines_trip_hour')
	def _compute_bt_hour(self):
		for item in self:
			if item.line_ids:
				item.busines_trip_hour = sum([line.busines_trip_hour for line in item.line_ids.filtered(lambda r: r.shift_plan_id.is_work != 'none')])
				item.busines_trip_hour2 = sum([line.busines_trip_hour for line in item.line_ids])
			else:
				item.busines_trip_hour=0
				item.busines_trip_hour2=0

	@api.depends('line_ids','line_ids.req_overtime_hour','line_ids.overtime_hour','line_ids.worked_salary_hour','line_ids.hour_to_work')
	def _compute_overtime(self):
		for item in self:
			ot_hour=0
			worked_hour_all=0
			overtime_hour=0
			hour_to_work=0
			save_hour=0
			hour_to_work=0
			all_hour=0
			worked_hour_all=0
			busines_trip_hour=0
			zuruu_tsag = 0
			busines_tt=0
			over_hour=0
			zz=0
			limit_day=6
			for line in item.line_ids:
				all_hour=0
				hasah=0
				print('\n=====line.date.weekday()',line.date.weekday())
				if line.date == item.parent_id.date_to:
					limit_day = line.date.weekday()
			
				if line.date.weekday() <=limit_day:
					if line.is_public_holiday!=True:
						hour_to_work +=line.hour_to_work
					worked_hour_all +=line.worked_salary_hour
					overtime_hour +=line.req_overtime_hour
					over_hour +=line.overtime_hour
					busines_trip_hour +=line.busines_trip_hour
					if line.busines_trip_hour:
						hasah +=1
					if line.shift_plan_id.is_work != 'none':
						busines_tt += (hasah*8)
					all_hour = overtime_hour + worked_hour_all + busines_trip_hour + over_hour
				if line.date.weekday()==limit_day:
					if all_hour>hour_to_work:
						ot_hour = all_hour - hour_to_work
						if hour_to_work>=(worked_hour_all + busines_tt) and ot_hour>0:
							zz = hour_to_work - (worked_hour_all + busines_tt)
						save_hour+=ot_hour
						zuruu_tsag+= zz
						print('\n=====all_hour',all_hour,hour_to_work,save_hour,zuruu_tsag)
					else:
						if line.shift_plan_id.is_work == 'none':
							zuruu_tsag+= busines_trip_hour
						if overtime_hour>0:
							zuruu_tsag+=overtime_hour
					ot_hour=0
					hour_to_work=0
					worked_hour_all=0
					overtime_hour=0
					busines_trip_hour=0
					busines_tt=0
					all_hour=0
					over_hour=0
					zz=0
			item.z_hour = zuruu_tsag	
			item.overtime=save_hour
			
class HrTimetableLineLine(models.Model):
	_inherit = "hr.timetable.line.line"

	overtime_all = fields.Float('Нийт илүү цаг',compute='_compute_overtime_all')
	accumlated_ot = fields.Float('Нэмэх БӨ цаг')
	is_weekend = fields.Boolean('Амралтын өдөр эсэх?')
	sickness_hour = fields.Float(string =u'Тасалсан цаг', digits=(3, 2))
	late_limit_date = fields.Datetime("Хоцролт лимит огноо",compute='_compute_late_limit_date',store=True)
	hour_to_work_n= fields.Float('АЗЦ шөнө',related='shift_plan_id.compute_sum_time',store=True)
	weekend_night= fields.Float(string='АБ шөнө')
	bt_hour= fields.Float(string='Том амралтын өдөр тооцохгүй томилолт')
	project_id= fields.Many2one('hr.project',string='Төсөл')
	worked_hour = fields.Float(compute='_compute_worked_hour',store=True, string = u'Ажилласан цаг', digits=(2, 2))
	worked_day_hour = fields.Float(compute='_compute_worked_day_hour',store=True, string = u'Хоног тооцох цаг', digits=(2, 2))
	is_work_schedule = fields.Selection(selection_add=[('in_night', 'In (Шөнө)'),])
	# Хоцролт тооцох цаг дээр 1 цаг нэмсэн 1 цагаас хэтэрвэл таслалт руу орно
	@api.depends('late_s')
	def _compute_late_limit_date(self):
		for item in self:
			if item.late_s:
				item.late_limit_date = datetime.strptime(str(item.late_s), DATETIME_FORMAT) + timedelta(hours=1)
			else:
				item.late_limit_date = False

	@api.depends('is_work_schedule','worked_hour', 'out_working_hour', 'online_working_hour', 'free_wage_hour','accumlated_hour','night_hour','parental_hour','training_hour','bt_hour')
	def _compute_worked_salary_hour(self):
		for obj in self:
			worked_hour=0
			if obj.is_work_schedule == 'night':
				worked_hour = 0
			else:
				worked_hour = obj.worked_hour 
			sum_hour  = worked_hour+obj.out_working_hour+obj.online_working_hour + obj.training_hour + obj.free_wage_hour
			
			if obj.hour_to_work <= sum_hour:
				obj.worked_salary_hour = obj.hour_to_work - obj.night_hour 
				if obj.bt_hour:
					obj.worked_salary_hour = obj.bt_hour
			else:
				obj.worked_salary_hour = sum_hour

	@api.depends('worked_hour', 'out_working_hour', 'online_working_hour', 'free_wage_hour','busines_trip_hour','night_hour','req_overtime_hour','training_hour','accumlated_hour')
	def _compute_worked_day_hour(self):
		for obj in self:
			sum_hour=0
			sum_hour  = obj.worked_hour +obj.out_working_hour+obj.online_working_hour + obj.training_hour + obj.free_wage_hour + obj.busines_trip_hour + obj.req_overtime_hour + obj.accumlated_hour
			obj.worked_day_hour = sum_hour


	@api.depends('overtime_hour','accumlated_hour')
	def _compute_overtime_all(self):
		for item in self:
			overtime_all=0
			if item.overtime_hour:
				overtime_all +=item.overtime_hour
			item.overtime_all=overtime_all

	def set_sign_in(self,sign_in):
		in_datetime=None
		if sign_in:
			in_datetime = datetime.strptime(str(sign_in), DATETIME_FORMAT) + timedelta(hours=8)
		return in_datetime
	
	def set_sickness_hour(self,obj,sickn_hour):
		sickness_hour=0
		is_not_att=False
		if obj.work_location_id.location_number=='1':
			if obj.sign_in_emp and obj.sign_out_emp:
				sign_in = datetime.strptime(str(obj.sign_in_emp), DATETIME_FORMAT) + timedelta(hours=8)
				sign_out = datetime.strptime(str(obj.sign_out_emp), DATETIME_FORMAT) + timedelta(hours=8)
				# Эхний 60 минутыг хоцролтоор үлдсэн цагийг таслалтаар тооцно
				if obj.late_limit_date and obj.is_request == 'no':
					late_limit_date = datetime.strptime(str(obj.late_limit_date), DATETIME_FORMAT) + timedelta(hours=8)
					in_limit_end = datetime.strptime(str(obj.in_limit_end), DATETIME_FORMAT) + timedelta(hours=8)
					if sign_in > late_limit_date:
						sickness_delta= sign_in - (late_limit_date - timedelta(hours=1))
						result = self._delayed_min(sickness_delta)
						if result>0:
							sickness_hour= result/60

			elif obj.sign_out_emp:
				sickness_hour = 4
				is_not_att = True
			elif obj.sign_in_emp:
				sickness_hour = 4
				is_not_att = True
			
			sickness_hour+=sickn_hour
			# Тасалсан цаг АЗ цаг онооно Бүх нийтийн амралтын өдөр бол таслалт тооцохгүй
			if obj.is_public_holiday == True or obj.shift_attribute_id.is_work=='business_trip':
				obj.sickness_hour=0
			else:
				hasah=0
				hasah_busad = (obj.free_hour+obj.sick_hour+obj.accumlated_hour +obj.busines_trip_hour+ obj.out_working_hour+ obj.online_working_hour)
				if obj.shift_plan_id.compute_sum_time>=hasah_busad:
					hasah = obj.shift_plan_id.compute_sum_time-hasah_busad
				if hasah_busad>0:
					if sickness_hour >= hasah:
						sickness_hour -= hasah
					else:
						sickness_hour = 0
				
				if is_not_att==True and hasah_busad<=0:
					sickness_hour=4
				if is_not_att==True and hasah==0:
					sickness_hour=0
				if hasah_busad>0:
					if is_not_att==False and sickness_hour<=hasah_busad:
						sickness_hour=0
				print('\n\n==kjsdkahsdkasjh=',obj.date,obj.employee_id.name,is_not_att,hasah_busad,hasah,sickness_hour)
				# _logger.info('\n\n =======is_not_att %s'%(is_not_att))
				# _logger.info('\n\n =======employee_id %s'%(obj.employee_id.name))
			# 	# _logger.info('\n\n ======= obj.date %s'%(obj.date))
				obj.sickness_hour = sickness_hour
			
			if obj.worked_salary_hour>=8:
				obj.sickness_hour=0

				

				
		
	def worked_hour_attendance(self,obj):
		delayed_min = 0
		worked_hour = 0
		hour = 0
		type_vac = ''
		sign_in=None
		sign_out=None
		req_out=None
		req_in=None
		if obj.leave_request_end and obj.leave_request_start:
			req_out = datetime.strptime(str(obj.leave_request_end), DATETIME_FORMAT)
			req_in = datetime.strptime(str(obj.leave_request_start), DATETIME_FORMAT)
		if obj.shift_plan_id.is_work != 'none' and obj.shift_plan_id.is_work != 'public_holiday':
			if obj.sign_in_emp:
				sign_in = obj.sign_in_emp
			if obj.sign_out_emp:
				sign_out = obj.sign_out_emp
			# Орох гарах лимитийн цагаар орсон гарсан цагийг хязгаарлаж ажилласан цаг тооцох
			if sign_in:
				if obj.in_limit_start and obj.in_limit_end:
					if obj.in_limit_start >= sign_in:
						sign_in = obj.in_limit_start
			if obj.out_limit_end and sign_out:
				if obj.out_limit_end <= sign_out:
					sign_out = obj.out_limit_end
		
			hour,delayed_min,lunch_hour,early_min = self.set_delayed_hour(obj,sign_in,sign_out)
			# Ээлжийн амралттай болон бүх нийтийн амралтын өдөр ажилласан бол хоцролт тооцохгүй
			if type_vac == 'vacation' or obj.is_public_holiday==True or obj.work_location_id.location_number == '2':
				obj.delayed_min = 0
				obj.early_min = 0
			else:
				hasah=0
				hasah_busad = (obj.free_hour+obj.sick_hour+obj.out_working_hour+obj.accumlated_hour +obj.busines_trip_hour+obj.training_hour)
				if hasah_busad>0:
					hasah = hasah_busad *60
				if delayed_min > hasah:
					obj.delayed_min = delayed_min-hasah
				else:
					# Ugluu hotsorson oroi huselttei uyd hotsrolt tootsoh
					obj.delayed_min = 0
					if req_in and sign_out:
						if req_out >= sign_out:
							obj.delayed_min = delayed_min
					if sign_out and sign_in and req_out:
						if req_out <= sign_out and req_out>=sign_in:
							obj.delayed_min = delayed_min
						
				if early_min > hasah:
					obj.early_min = early_min-hasah
				else:
					obj.early_min =0
			
			worked_hour = round(hour/60, 2) 
			if worked_hour > 0 and obj.is_work_schedule !='night':
				if obj.hour_to_work < worked_hour:
					obj.worked_hour = obj.hour_to_work
					if req_in and req_out and obj.is_work_schedule=='leave':
						if req_in>=sign_in and req_out<=sign_out:
							obj.worked_hour -= obj.free_hour
				else:
					obj.worked_hour = worked_hour
					if req_in and req_out and sign_out and sign_in and obj.is_work_schedule=='leave':
						if req_in>=sign_in and req_out<=sign_out:
							obj.worked_hour -= (obj.free_hour)		
			else:
				obj.worked_hour = 0
			if obj.is_work_schedule =='night' and worked_hour>=0:
				obj.night_hour = worked_hour
			elif obj.shift_plan_id.is_work =='none' or obj.shift_attribute_id.is_work=='business_trip':
				obj.worked_hour = 0
				obj.night_hour = 0
			else:
				obj.night_hour =0
		if obj.parent_id.employee_id.full_worked_hour==True:
			obj.holiday_worked_hour = 0

		if obj.is_public_holiday==True and worked_hour>0:
			obj.worked_hour = 0
	

	


	def seconds_replace(self,date):
		if date:
			date = date.replace(second=0, microsecond=0)
		return date 
# Ажилласан цаг болон хоцролт,таслалт тооцох функц
	def set_delayed_hour(self,obj,sign_in, sign_out):
		time_delta=None
		lunch_in = None
		lunch_out = None
		req_out=None
		req_in = None
		delayed_min = 0
		lunch_hour=0
		sickn_hour=0
		hour = 0
		s_work = None
		e_work = None
		s_in = None
		delayed_delta=0
		early_min=0
		late_limit_date = None
		if obj.lunch_start_time:
			lunch_in = datetime.strptime(str(obj.lunch_start_time), DATETIME_FORMAT) + timedelta(hours=8)
		if obj.lunch_end_time:
			lunch_out = datetime.strptime(str(obj.lunch_end_time), DATETIME_FORMAT) + timedelta(hours=8)
		# Хоцролт тохиргоон дээр сонгосон цагаас тооцох
		start_time = self.late_hour(obj,obj.late_s,obj.start_time)
		if start_time:
			s_work = datetime.strptime(str(start_time), DATETIME_FORMAT)+timedelta(hours=8)
		
		if obj.leave_request_end and obj.leave_request_start:
			req_out = datetime.strptime(str(obj.leave_request_end), DATETIME_FORMAT)+timedelta(hours=8)
			req_in = datetime.strptime(str(obj.leave_request_start), DATETIME_FORMAT)+timedelta(hours=8)
		if obj.shift_plan_id:
			lunch_hour = obj.shift_plan_id.compute_sum_lunch
		# Орсон гарсан ирц 2 уулаа байх үед
		if sign_in and sign_out:
			s_in = self.seconds_replace(datetime.strptime(str(sign_in), DATETIME_FORMAT) + timedelta(hours=8))
			s_out = self.seconds_replace(datetime.strptime(str(sign_out), DATETIME_FORMAT) + timedelta(hours=8))
			# s_in - Орсон цаг 8:33
			# s_work - Орох ёстой цаг 8:00
			# s_out - garsan цаг 8:33
			# e_work - garah ёстой цаг 8:00
			if s_in and s_work:
				if obj.late_limit_date :
					late_limit_date = datetime.strptime(str(obj.late_limit_date), DATETIME_FORMAT) + timedelta(hours=8)
				if s_in > s_work:
					delayed_delta = obj.delayed_delta_compute(s_in,s_out)
					delayed_min = self._delayed_min(delayed_delta)
					if late_limit_date:
						if s_in > late_limit_date:
							delayed_delta = obj.delayed_delta_compute(s_in,s_out)
							delayed_min = 0
			if s_out and s_in:
				e_work = s_in+timedelta(hours=9)
				if e_work.hour>=19 and e_work.minute>=1:
					e_work = e_work.replace(hour=int(19), minute=int(0), second=0,microsecond=0)
				if s_out and e_work:
					if s_out <= e_work:
						early_min_delta =obj.early_delta_compute(req_out,s_out,e_work)
						early_min = self._delayed_min(early_min_delta)
						if early_min > 60:
							sickn_hour =(early_min)/60
							early_min = 0
						if req_in:
							if req_in >= s_out:
								early_min = 0
				if s_out>s_in:				
					if lunch_out and lunch_in:
						if lunch_in<=s_out and lunch_out>=s_out: #12 <= y and 13 >=y
							time_delta = lunch_in-s_in 
						elif s_in<=lunch_out and s_in>=lunch_in: #12<= x >=13
							time_delta = s_out-lunch_out
						elif s_in<=lunch_in and s_out >= lunch_out: # 12 >= x and 13 <=y
							time_delta = lunch_in-s_in
							time_delta += (s_out-lunch_out)
						else:
							time_delta = s_out-s_in
					else:
						time_delta = s_out-s_in
					
					if time_delta:
						hour = time_delta.total_seconds()/60
								
		# Орсан гарсан аль нэг нь байвал цайны цагаас тооцно. нэмэлт хүсэлт орж ирвэл хүсэлтээс тооцно
		elif sign_in and obj.lunch_start_time and not sign_out:
			s_in = datetime.strptime(str(sign_in), DATETIME_FORMAT) + timedelta(hours=8)
			lunch_in = datetime.strptime(str(obj.lunch_start_time), DATETIME_FORMAT) + timedelta(hours=8)
			if s_in and lunch_in:
				delayed_delta = obj.delayed_delta_compute(s_in,lunch_in)
				delayed_min = self._delayed_min(delayed_delta)
			if req_in and req_out:
				if req_in<s_in:
					if e_work:
						time_delta =e_work - req_out
				elif req_in>=s_in:					
					time_delta = req_in-s_in
			if time_delta:
				hour = time_delta.total_seconds()/60
			else:
				if obj.work_location_id.location_number == '1':
					hour = 240 - delayed_min
				else:
					hour = obj.hour_to_work*60
		elif sign_out and lunch_out and not sign_in:
			s_out = datetime.strptime(str(sign_out), DATETIME_FORMAT) + timedelta(hours=8)
			if req_in and req_out:
				if req_in<=s_out and s_out>=req_out:
					if req_out >= lunch_in and req_out<=lunch_out:
						if e_work and lunch_out:
							time_delta = e_work - lunch_out
					else:
						time_delta = s_out-req_out
				else:
					if e_work and lunch_out:
						time_delta = e_work - lunch_out
				if time_delta:
					hour = time_delta.total_seconds()/60
			else:
				if obj.work_location_id.id==1:
					hour = 240
				else:
					hour = obj.hour_to_work*60
		else:
			hour = 0
			# Тасалсан цаг АЗ цаг онооно Бүх нийтийн амралтын өдөр бол таслалт тооцохгүй
			sickn_hour =obj.hour_to_work
		self.set_sickness_hour(obj,sickn_hour)
		return hour,delayed_min,lunch_hour,early_min

	def delayed_delta_compute(self,s_in,sign_out):
		# self.late_s хоцролт тооцох цаг
		# s_in орсон цаг
		# s_work # ажил эхлэх ёстой цаг
		
		s_start_time=self.start_time
		s_late_time=self.late_s
		delayed_delta=0
		if  self.shift_plan_id and self.shift_plan_id.is_limit: #уян хатан бол
			uyan_oroh_duusah=self.shift_plan_id.in_e_time
			uyan_oroh_ehleh=self.shift_plan_id.in_s_time
	
			uyan_garah_duusah=self.shift_plan_id.out_e_time
			uyan_garah_ehleh=self.shift_plan_id.out_s_time
			if uyan_oroh_duusah and uyan_oroh_ehleh and \
				uyan_garah_duusah and uyan_garah_ehleh:
				s_start_time = self.hour_minute_replace(uyan_oroh_duusah,self.date) #10 цаг
				s_work = datetime.strptime(str(s_start_time), DATETIME_FORMAT)+timedelta(hours=8) 
				if s_work<s_in:
					delayed_delta = s_in-s_work
			else:
				raise UserError(('Ээлж дээр Лимит тохируулах эсэх? идэвхитэй байгаа боловч цагуудаа бүрэн бөглөөгүй байна {}'.format(self.shift_plan_id.name)))
				
		else:
			# s_start_time = obj.hour_minute_replace(self.shift_plan_id.start_time,self.date)
			# s_start_time = self.hour_minute_replace(self.shift_plan_id.in_e_time,self.date)

			start_time = self.late_hour(self,s_late_time,s_start_time)
			if start_time:
				datetime.strptime(str(start_time), DATETIME_FORMAT)+timedelta(hours=8) 
				delayed_delta = s_in-s_work
		return delayed_delta
	
	def early_delta_compute(self,req_out,s_out,s_in):
		# self.late_s хоцролт тооцох цаг
		# s_in орсон цаг
		# s_work # ажил эхлэх ёстой цаг
		early_min_delta=0
		if  self.shift_plan_id and self.shift_plan_id.is_limit: #уян хатан бол
			uyan_oroh_duusah=self.shift_plan_id.in_e_time
			uyan_oroh_ehleh=self.shift_plan_id.in_s_time
	
			uyan_garah_duusah=self.shift_plan_id.out_e_time
			uyan_garah_ehleh=self.shift_plan_id.out_s_time
			if uyan_oroh_duusah and uyan_oroh_ehleh and \
				uyan_garah_duusah and uyan_garah_ehleh:
				garah_yostoi=s_in
				if garah_yostoi>s_out:
					early_min_delta=garah_yostoi-s_out
			else:
				raise UserError(('Ээлж дээр Лимит тохируулах эсэх? идэвхитэй байгаа боловч цагуудаа бүрэн бөглөөгүй байна {}'.format(self.shift_plan_id.name)))
				
		else:
			e_work=None
			if self.end_time:
				e_work = datetime.strptime(str(self.end_time),DATETIME_FORMAT)+timedelta(hours=8)
				early_min_delta=0
				if req_out:
					if req_out >= e_work:
						early_min_delta = e_work - req_out
					else:
						early_min_delta = e_work - s_out
				else:
					early_min_delta = e_work - s_out
	
		return early_min_delta	
	
	@api.depends('sign_in', 'sign_out','is_work_schedule','shift_attribute_id', 'free_hour','hour_to_work','free_wage_hour', 'busines_trip_hour', 'sick_hour',)
	def _compute_worked_hour(self):
		for obj in self:
			full_hour_emp = self.env['hr.employee'].search([('full_worked_hour', '=', True),('employee_type', '!=', 'resigned'),('id','=',obj.employee_id.id)])
			# Төхөөрөмжийн ирцээс татах
			if obj.parent_id.parent_id.is_mining!=True:
				if full_hour_emp:
					for full_emp in full_hour_emp:
						self.worked_hour_schedule(obj)
				else:
					self.worked_hour_attendance(obj)
			# Ээлжээс ажилласан цаг тооцох
			else:
				self.worked_hour_schedule(obj)

	
	def worked_hour_schedule(self,obj):
		attendance = False
		if obj.sign_in:
			attendance = True
		if obj.sign_out:
			attendance = True
		if obj.sign_out and obj.sign_in:
			attendance = True
		if not obj.sign_out and not obj.sign_in:
			attendance = False
		worked_hour = 0
		night_hour = 0 
		tourist_hour = 0 
		overtime_hour = 0 
		weekend_night = 0 
		holiday_worked_hour = 0 
		sickness_hour		 = 0 
		accumlated_ot=0
		if obj.shift_plan_id:
			hasah = obj.shift_plan_id.compute_sum_all_time -obj.sick_hour - obj.sickness_hour-obj.free_hour-obj.vacation_day - obj.busines_trip_hour - obj.free_wage_hour - obj.out_working_hour
			hasah_tsag= hasah if hasah>=0 else 0
			if attendance==True or obj.employee_id.full_worked_hour==True:
				if obj.shift_plan_id.is_work == 'night':
					hasah = obj.hour_to_work_n -obj.sick_hour - obj.sickness_hour-obj.free_hour-obj.vacation_day - obj.busines_trip_hour - obj.free_wage_hour - obj.out_working_hour
					hasah_tsag= hasah if hasah>=0 else 0
					if obj.is_weekend == True and obj.is_public_holiday==False:
						night_hour = obj.hour_to_work_n
						overtime_hour = obj.shift_plan_id.compute_sum_all_time 
						weekend_night = obj.hour_to_work_n
					elif obj.is_weekend == True and obj.is_public_holiday==True: 
						night_hour = obj.hour_to_work_n
						holiday_worked_hour = obj.shift_plan_id.compute_sum_all_time
						weekend_night = obj.hour_to_work_n
						# accumlated_ot = obj.hour_to_work_n
					elif obj.is_public_holiday==True and obj.is_weekend == False: 
						night_hour = obj.hour_to_work_n
						holiday_worked_hour = obj.shift_plan_id.compute_sum_all_time
						weekend_night = obj.hour_to_work_n
					else:
						night_hour = hasah_tsag
						overtime_hour = obj.shift_plan_id.compute_sum_ov_time 
				elif obj.shift_plan_id.is_work == 'in':
					if obj.is_public_holiday==True:
						holiday_worked_hour = obj.shift_plan_id.compute_sum_all_time
					elif obj.is_weekend == True and obj.is_public_holiday==False: 
						overtime_hour = obj.shift_plan_id.compute_sum_all_time
					else:
						overtime_hour = obj.shift_plan_id.compute_sum_ov_time
						worked_hour = obj.shift_plan_id.compute_sum_time
				elif obj.shift_plan_id.is_work == 'in_night':
					if obj.is_public_holiday==True:
						holiday_worked_hour = obj.shift_plan_id.compute_sum_all_time
					elif obj.is_weekend == True and obj.is_public_holiday==False: 
						overtime_hour = obj.shift_plan_id.compute_sum_all_time
						night_hour=8
						weekend_night = 8
					else:
						overtime_hour = obj.shift_plan_id.compute_sum_ov_time
						tourist_hour = obj.shift_plan_id.compute_sum_time
						night_hour=8
				elif obj.shift_plan_id.is_work == 'day':
					if obj.work_location_id.location_number=='2':
						if obj.is_weekend == True and obj.is_public_holiday==False:
							overtime_hour = hasah_tsag
						elif obj.is_public_holiday == True and  obj.is_weekend == True:
							holiday_worked_hour = hasah_tsag
						elif obj.is_public_holiday==True and obj.is_weekend == False: 
							holiday_worked_hour = hasah_tsag
						else:
							worked_hour = obj.shift_plan_id.compute_sum_time
							overtime_hour = obj.shift_plan_id.compute_sum_ov_time
					else:
						if obj.is_public_holiday == True:
							worked_hour=0
						else:
							worked_hour = obj.shift_plan_id.compute_sum_time	

				elif obj.shift_plan_id.is_work == 'out':
					tourist_hour = obj.shift_plan_id.compute_sum_all_time
				elif obj.shift_attribute_id.is_work == 'business_trip' and obj.is_public_holiday==True:
					holiday_worked_hour = 11
				elif obj.shift_attribute_id.is_work == 'business_trip' and obj.is_weekend==True:
					overtime_hour = 11
				# elif obj.shift_attribute_id.is_work == 'business_trip':
				#  Доорхагууд 0 байх тохиолдол
				if obj.shift_attribute_id.is_work in ('bereavement','vacation','sickness','leave','sick','pay_leave','outage','none','parental'):
					worked_hour = 0
					night_hour = 0 
					tourist_hour = 0 
					overtime_hour = 0 
					weekend_night = 0 
					holiday_worked_hour = 0 
					sickness_hour= 0
			elif attendance==False:
				if obj.shift_attribute_id.is_work not in ('bereavement','vacation','sickness','leave','sick','pay_leave','outage','none','parental','online_work','out_work','business_trip'):
					worked_hour = 0
					night_hour = 0 
					tourist_hour = 0 
					overtime_hour = 0 
					weekend_night = 0 
					holiday_worked_hour = 0 
					sickness_hour= 11	
					accumlated_ot=0			
				elif obj.shift_attribute_id.is_work == 'business_trip' and obj.is_public_holiday==True:
					holiday_worked_hour = obj.bt_hour
				elif obj.shift_attribute_id.is_work == 'business_trip' and obj.is_public_holiday==False and obj.is_weekend==False:
					if obj.bt_hour>8:
						overtime_hour= (obj.bt_hour-8)
						worked_hour=8
					else:
						worked_hour=obj.bt_hour
				elif obj.shift_attribute_id.is_work == 'business_trip' and obj.is_weekend==True and obj.work_location_id.id!=1:
					overtime_hour = obj.bt_hour

		obj.worked_hour = worked_hour
		obj.night_hour = night_hour
		obj.tourist_hour = tourist_hour
		obj.overtime_hour=overtime_hour
		obj.weekend_night=weekend_night
		obj.holiday_worked_hour = holiday_worked_hour
		obj.sickness_hour = sickness_hour		

class HrEmployee(models.Model):
	_inherit = "hr.employee"


	accumlated_hour_ids = fields.One2many('accumlated.hour','employee_id',string='Нөхөж амрах хуримтлагдсан цаг')
	overtime_hour_ids = fields.One2many('overtime.hour','employee_id',string='Илүү хуримтлагдсан цаг')

	sum_accumlate_hour = fields.Float('Нийт нөхөн амрах цаг',compute='_compute_sum_hour',store=True)
	sum_overtime_hour = fields.Float('Нийт илүү цаг',compute='_compute_sum_hour',store=True)


	@api.depends('accumlated_hour_ids','overtime_hour_ids')
	def _compute_sum_hour(self):
		for item in self:
			sum_accumlate_hour=0
			sum_overtime_hour=0
			if item.accumlated_hour_ids:
				accumlated_ids = item.accumlated_hour_ids.filtered(lambda line: line.is_active==True)
				sum_accumlate_hour = sum(accumlated_ids.mapped('hour'))
			if item.overtime_hour_ids:
				overtime_ids = item.overtime_hour_ids.filtered(lambda line: line.is_active==True)
				sum_overtime_hour = sum(overtime_ids.mapped('hour'))
			item.sum_accumlate_hour = sum_accumlate_hour
			item.sum_overtime_hour = sum_overtime_hour
	

class AccumlatedHour(models.Model):
	_name = "accumlated.hour"
	_description = "Accumlated Hour"
	
	hour = fields.Float('Нөхөн амрах цаг')
	date = fields.Date('Огноо')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	balance_id = fields.Many2one('hour.balance.dynamic','Цагийн баланс')
	is_active = fields.Boolean('Идэвхтэй эсэх')
	
class OvertimeHour(models.Model):
	_name = "overtime.hour"
	_description = "Overtime Hour"
	
	hour = fields.Float('Илүү цаг')
	date = fields.Date('Огноо')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	balance_id = fields.Many2one('hour.balance.dynamic','Цагийн баланс')
	is_active = fields.Boolean('Идэвхтэй эсэх')
	
class HrShiftTime(models.Model):
	_inherit = 'hr.shift.time'
	
	is_work = fields.Selection(selection_add=[('in_night', 'In (Шөнө)'),])

class HrShiftTime(models.Model):
	_inherit = 'hr.shift.line'
	
	is_work = fields.Selection(selection_add=[('in_night', 'In (Шөнө)'),])