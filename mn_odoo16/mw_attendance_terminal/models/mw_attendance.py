
# -*- coding: utf-8 -*-
from datetime import  datetime,timedelta
from odoo import api, fields, models, _

class HrAttendance(models.Model):
	_inherit= "hr.attendance"

	day_shift = fields.Boolean('Day Shift', default=True)
	in_date = fields.Date('In date',index=True)
	work_location_id = fields.Many2one('hr.work.location', string='Ажлын байршил', required=True)
	road_hours = fields.Float(string='Зам цаг')
	
	@api.constrains('check_in', 'check_out', 'employee_id')
	def _check_validity(self):
		return True

class MwAttendance(models.Model):
	_name = 'mw.attendance'
	_description = "mw attendance"
	_inherit = ['mail.thread']
	_order = 'attendance_time, employee_id'

	name = fields.Char(string='Нэр')
	employee_id = fields.Many2one('hr.employee', string='Ажилтан', index=True,tracking=True)
	department_id = fields.Many2one('hr.department','Хэлтэс',tracking=True)
	job_id = fields.Many2one('hr.job','Албан тушаал',tracking=True)
	att_terminal_id = fields.Many2one('hr.attendance.terminal','Төхөөрөмж')
	attendance_time = fields.Datetime(string="Ирц", index=True,tracking=True)
	date = fields.Date(string='Огноо',tracking=True)
	# Ашиглахгүй
	device_id = fields.Char(string='Төхөөрөмжийн нэр',tracking=True)
	day_shift = fields.Boolean('Day Shift', default=True)

	attendance_type = fields.Selection([
			('in', 'Орох'),
			('out', 'Гарах'),],
			string=u'Ирцийн төрөл', )

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.name = self.employee_id.name

class ImportAtt(models.TransientModel):
	_name = 'import.att'
	_description = "import add"

	date=fields.Date('Огноо')
	conf_time_id = fields.Many2one('terminal.configuration', 'Ирцийн тохиргоо')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	department_id = fields.Many2one('hr.department','Хэлтэс')
	job_id = fields.Many2one('hr.job','Албан тушаал')

	def import_attendance_create(self):
		attendance_obj = self.env['hr.attendance']
		# print'==========',self.conf_time_id.morning_in[:10],datetime.strptime(self.conf_time_id.morning_in, "%Y-%m-%d %H:%M:%S")+timedelta(hours=8)
		# tt=datetime.strptime(self.conf_time_id.morning_in, "%Y-%m-%d %H:%M:%S")+timedelta(hours=8)
		# att_morning_in_ids = self.env['mw.attendance'].search([('date','=',self.date),('attendance_time','>=',self.conf_time_id.morning_in),('attendance_time','<=',self.conf_time_id.morning_out)])
		# query = """SELECT employee_id,
		# 			attendance_time + interval '8 hour'
		# 			FROM mw_attendance
		# 			WHERE (attendance_time + interval '8 hour')::date >= '%s' and (attendance_time + interval '8 hour')::date <= '%s' and date='%s'
		# 			"""%(self.conf_time_id.morning_in,self.conf_time_id.morning_out,self.date)
		# self.env.cr.execute(query)
		# records = self.env.cr.fetchall()
		# for rec in records:
		# query = """SELECT employee_id
		# 			FROM mw_attendance
		# 			WHERE date='%s'
		# 			GROUP BY employee_id
		# 			"""%(self.date)
		# self.env.cr.execute(query)
		# records = self.env.cr.fetchall()
		if not self.employee_id:
			query = """SELECT id
						FROM hr_employee
						WHERE employee_location='office' and status in ('working', 'experiment', 'contract')
						GROUP BY id
						"""
		else:
			query = """SELECT id
						FROM hr_employee
						WHERE id=%s
						"""%(self.employee_id.id)
		self.env.cr.execute(query)
		records = self.env.cr.fetchall()
		m_in=0
		l_in=0
		l_out=0
		n_out=0
		in_hour = datetime.strptime(self.date, "%Y-%m-%d")
		year=in_hour.date().strftime("%Y")
		month=in_hour.date().strftime("%m")
		day=in_hour.date().strftime("%d")

		s_morning_in=year+'-'+month+'-'+day+' '+'05'+':'+'00'+':'+'00'
		s_morning_out=year+'-'+month+'-'+day+' '+'11'+':'+'50'+':'+'00'
		s_lunch_in_from=year+'-'+month+'-'+day+' '+'11'+':'+'51'+':'+'00'
		s_lunch_in_to=year+'-'+month+'-'+day+' '+'12'+':'+'29'+':'+'00'
		s_lunch_out_from=year+'-'+month+'-'+day+' '+'12'+':'+'30'+':'+'00'
		s_lunch_out_to=year+'-'+month+'-'+day+' '+'13'+':'+'30'+':'+'00'
		s_evening_in=year+'-'+month+'-'+day+' '+'13'+':'+'30'+':'+'00'
		s_evening_out=year+'-'+month+'-'+day+' '+'23'+':'+'59'+':'+'00'

		morning_in = datetime.strptime(s_morning_in, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		morning_out = datetime.strptime(s_morning_out, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		lunch_in_from = datetime.strptime(s_lunch_in_from, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		lunch_in_to = datetime.strptime(s_lunch_in_to, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		lunch_out_from = datetime.strptime(s_lunch_out_from, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		lunch_out_to = datetime.strptime(s_lunch_out_to, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		evening_in = datetime.strptime(s_evening_in, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		evening_out = datetime.strptime(s_evening_out, "%Y-%m-%d %H:%M:%S")-timedelta(hours=8)
		for rec in records:
			att_morning_in = self.env['mw.attendance'].search([('employee_id','=',rec[0]),('attendance_time','>=',str(morning_in)),('attendance_time','<=',str(morning_out))], order='attendance_time desc', limit=1)
			if att_morning_in:
				m_in=att_morning_in.attendance_time
			else:
				m_in=False
			att_lunch_in = self.env['mw.attendance'].search([('employee_id','=',rec[0]),('attendance_time','>=',str(lunch_in_from)),('attendance_time','<=',str(lunch_in_to))], order='attendance_time desc', limit=1)
			if att_lunch_in:
				l_in=att_lunch_in.attendance_time
			else:
				l_in=False
			att_lunch_out = self.env['mw.attendance'].search([('employee_id','=',rec[0]),('attendance_time','>=',str(lunch_out_from)),('attendance_time','<=',str(lunch_out_to))], order='attendance_time desc', limit=1)
			if att_lunch_out:
				l_out=att_lunch_out.attendance_time
			else:
				l_out=False
			att_nigth_in = self.env['mw.attendance'].search([('employee_id','=',rec[0]),('attendance_time','>=',str(evening_in)),('attendance_time','<=',str(evening_out))], order='attendance_time desc', limit=1)
			if att_nigth_in:
				n_out=att_nigth_in.attendance_time
			else:
				n_out=False
			data = {
					'date': self.date,
					'check_in': '2019-04-01 00:00:00',
					'morning_in': m_in,
					'lunch_in': l_in,
					'lunch_out': l_out,
					'check_out': n_out,
					'employee_id': rec[0],

				}
			att_obj = attendance_obj.create(data)
			# att_morning_in_ids = self.env['mw.attendance'].search([('employee_id','=',rec[0]),('attendance_time','>=',self.conf_time_id.morning_in),('attendance_time','<=',self.conf_time_id.morning_out)])
			# self.regulation_employee_id.update({'status':'working'})
		return True
