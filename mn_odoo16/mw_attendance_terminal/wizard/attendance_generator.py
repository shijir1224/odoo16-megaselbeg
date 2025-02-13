# -*- coding: utf-8 -*-

from odoo.osv import osv
from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class AttendanceGenerator(models.TransientModel):
	_name = 'attendance.generator'
	_description = 'Attendance Generator'

	start_date = fields.Date('Эхлэх огноо', required=True)
	end_date = fields.Date('Дуусах огноо', required=True)
	company_id = fields.Many2one('res.company',string='Компани', default= lambda self: self.env['hr.employee'].sudo().search([("user_id", "=", self.env.user.id)], limit=1).company_id.id)
	sector_id = fields.Many2one('hr.department', string='Сектор', domain=[('type', '=', 'sector')], default= lambda self: self.env['hr.employee'].sudo().search([("user_id", "=", self.env.user.id), ("active", "=", True)], limit=1).sector.id)
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	department_id = fields.Many2one('hr.department','Алба нэгж')
	work_location_id = fields.Many2one('hr.work.location', string='Ажлын байршил', required=True)
	# sector_id = fields.Many2one('hr.department','Сектор', domain="[('type', '=', 'sector')]")

	def create_attendance(self):
		attendance_pool = self.env['hr.attendance']
		if self.department_id:
			if self.employee_id:
				set_employee_query = """
					SELECT 
							ma.employee_id as emp_id,
							ma.date as date,
							ma.day_shift as day_shift
					FROM 
							mw_attendance ma
							LEFT JOIN hr_employee emp ON ma.employee_id = emp.id
					WHERE 
							ma.date >= '%s' 
						AND ma.date <= '%s' 
						AND emp.work_location_id = '%s'
						AND ma.employee_id = '%s'
						AND emp.department_id = '%s'
					GROUP BY 
							ma.employee_id, ma.date, ma.day_shift
				"""%(self.start_date, self.end_date, self.work_location_id.id, self.employee_id.id, self.department_id.id)
				self.env.cr.execute(set_employee_query)
				employee_set = self.env.cr.dictfetchall()
			else:
				set_employee_query = """
					SELECT 
							ma.employee_id as emp_id,
							ma.date as date,
							ma.day_shift as day_shift
					FROM 
							mw_attendance ma
							LEFT JOIN hr_employee emp ON ma.employee_id = emp.id
					WHERE 
							ma.date >= '%s' 
						AND ma.date <= '%s' 
						AND emp.work_location_id = '%s'
						AND emp.company_id = '%s'
						AND emp.department_id = '%s'
					GROUP BY 
							ma.employee_id, ma.date, ma.day_shift
				"""%(self.start_date, self.end_date, self.work_location_id.id, self.company_id.id,self.department_id.id)
				self.env.cr.execute(set_employee_query)
				employee_set = self.env.cr.dictfetchall()
		else:
			if self.employee_id:
				set_employee_query = """
					SELECT 
							ma.employee_id as emp_id,
							ma.date as date,
							ma.day_shift as day_shift
					FROM 
							mw_attendance ma
							LEFT JOIN hr_employee emp ON ma.employee_id = emp.id
					WHERE 
							ma.date >= '%s' 
						AND ma.date <= '%s' 
						AND emp.work_location_id = '%s'
						AND ma.employee_id = '%s'
					GROUP BY 
							ma.employee_id, ma.date, ma.day_shift
				"""%(self.start_date, self.end_date, self.work_location_id.id, self.employee_id.id)
				self.env.cr.execute(set_employee_query)
				employee_set = self.env.cr.dictfetchall()
			else:
				set_employee_query = """
					SELECT 
							ma.employee_id as emp_id,
							ma.date as date,
							ma.day_shift as day_shift
					FROM 
							mw_attendance ma
							LEFT JOIN hr_employee emp ON ma.employee_id = emp.id
					WHERE 
							ma.date >= '%s' 
						AND ma.date <= '%s' 
						AND emp.work_location_id = '%s'
						AND emp.company_id = '%s'
					GROUP BY 
							ma.employee_id, ma.date, ma.day_shift
				"""%(self.start_date, self.end_date, self.work_location_id.id, self.company_id.id)
				self.env.cr.execute(set_employee_query)
				employee_set = self.env.cr.dictfetchall()
		for emp in employee_set:
			if emp['day_shift']==True:

				att_in_id = self.env['mw.attendance'].sudo().search([('employee_id', '=',emp['emp_id']),
															('date', '=',emp['date']),('day_shift', '=',True)], order='attendance_time asc',limit=1)
				att_out_id = self.env['mw.attendance'].sudo().search([('employee_id', '=',emp['emp_id']),
															('date', '=',emp['date']),('day_shift', '=',True)], order='attendance_time desc',limit=1)
				# hr_n_in = datetime.strptime(str(att_in_id.attendance_time), DATETIME_FORMAT)
				
				tt_ll = self.env['hr.timetable.line.line'].search([('employee_id', '=', emp['emp_id']), ('date', '=', emp['date'])])
				tt_ll.update({
							'sign_in_emp': att_in_id.attendance_time,
							'sign_out_emp': att_out_id.attendance_time,
						})
				# print('-=-=-=-=-=',att_in_id.attendance_time , att_out_id.attendance_time)
				if att_in_id.attendance_time and att_out_id.attendance_time:
					# s_in = datetime.strptime(str(att_in_id.attendance_time), DATETIME_FORMAT) + timedelta(hours=0.1)
					search_query = """
						SELECT 
								ha.id as ha_id,
								ha.check_out as check_out
						FROM 
								hr_attendance ha
								LEFT JOIN hr_employee emp ON ha.employee_id = emp.id
						WHERE 
								ha.check_out >= '%s' 
							AND ha.check_out <= '%s' 
							AND ha.employee_id = '%s' 
							AND ha.day_shift = True
					"""%(att_in_id.attendance_time,att_out_id.attendance_time, emp['emp_id'])
					self.env.cr.execute(search_query)
					search_set = self.env.cr.dictfetchall()
					# if  not search_set:
					if  not search_set : 
						if not self.env['hr.attendance'].search([('employee_id', '=', emp['emp_id']), ('in_date', '=', emp['date']), ('day_shift', '=', True)]):
							if att_in_id.attendance_time==att_out_id.attendance_time:
								leave_id = self.env['hr.leave.mw'].search([('employee_id', '=', emp['emp_id']), ('shift_plan_id.is_work', '=', 'attendance_out'), ('date_to', '=', emp['date'])])
								leave_query = """
									SELECT 
											hlw.date_to as out_att,
											hlw.date_from as in_att,
											hst.is_work as is_work
									FROM 
											hr_leave_mw hlw
									LEFT JOIN 
											hr_shift_time hst ON hst.id=hlw.shift_plan_id
									WHERE 
										(date(hlw.date_to+ interval '8 hour') = '%s' or date(hlw.date_from+ interval '8 hour') = '%s')
										AND hlw.employee_id = '%s'
										AND hst.is_work in ('attendance_out','attendance') AND hlw.state_type = 'done'
								"""%(emp['date'],emp['date'], emp['emp_id'])
								self.env.cr.execute(leave_query)
								leave_set = self.env.cr.dictfetchall()
								if leave_set:
									if leave_set[0]['is_work'] == 'attendance_out':
										attendance_id = attendance_pool.create({
											'date': emp['date'],
											'in_date': emp['date'],
											'employee_id': emp['emp_id'],
											'day_shift': emp['day_shift'],
											'work_location_id': self.work_location_id.id,
											'check_in': att_in_id.attendance_time,
											'check_out': leave_set[0]['out_att'] ,
											})
									else:
										if leave_set[0]['in_att']>att_out_id.attendance_time:
											empl = self.env['hr.employee'].search([('id','=',emp['emp_id'])])
											raise UserError(_('%s ажилтны %s өдрийн орсон ирц нөхөх хүсэлтийн цаг буруу байна.')%(empl.name, emp['date']))
										else:
											attendance_id = attendance_pool.create({
												'date': emp['date'],
												'in_date': emp['date'],
												'employee_id': emp['emp_id'],
												'day_shift': emp['day_shift'],
												'work_location_id': self.work_location_id.id,
												'check_in': leave_set[0]['in_att'],
												'check_out': att_out_id.attendance_time,
												})
								else:
									attendance_id = attendance_pool.create({
										'date': emp['date'],
										'in_date': emp['date'],
										'employee_id': emp['emp_id'],
										'day_shift': emp['day_shift'],
										'work_location_id': self.work_location_id.id,
										'check_in': att_in_id.attendance_time,
										'check_out': att_out_id.attendance_time,
										})
								leave_query_line = """
									SELECT 
											htc.in_out_time as out_att,
											hst.is_work as is_work
									FROM 
											hr_leave_mw hlw
									LEFT JOIN 
											hr_shift_time hst ON hst.id=hlw.shift_plan_id
                                    LEFT JOIN 
											hr_time_compute htc ON htc.hr_parent_id=hlw.id
									WHERE 
										date(htc.in_out_time+ interval '8 hour') = '%s' 
										AND hlw.employee_id = %s
										AND hst.is_work in ('attendance_out','attendance') AND hlw.state_type = 'done'
								"""%(emp['date'], emp['emp_id'])
								self.env.cr.execute(leave_query_line)
								leave_line_set = self.env.cr.dictfetchall()
								if leave_line_set:
									hr_att_id = self.env['hr.attendance'].search([('employee_id', '=', emp['emp_id']), ('in_date', '=', emp['date'])])
									if not hr_att_id:
										if leave_line_set[0]['is_work'] == 'attendance_out':
											attendance_id = attendance_pool.create({
												'date': emp['date'],
												'in_date': emp['date'],
												'employee_id': emp['emp_id'],
												'day_shift': emp['day_shift'],
												'work_location_id': self.work_location_id.id,
												'check_in': att_in_id.attendance_time,
												'check_out': leave_line_set[0]['out_att'] ,
												})
										else:
											attendance_id = attendance_pool.create({
												'date': emp['date'],
												'in_date': emp['date'],
												'employee_id': emp['emp_id'],
												'day_shift': emp['day_shift'],
												'work_location_id': self.work_location_id.id,
												'check_in': leave_line_set[0]['out_att'],
												'check_out': att_out_id.attendance_time,
												})
									else:
										attendance_obj = self.env['hr.attendance'].browse(hr_att_id.id)
										if leave_line_set[0]['is_work'] == 'attendance_out':
											attendance_obj.update({
												'check_out': leave_line_set[0]['out_att'],
											})
										else:
											attendance_obj.update({
												'check_in': leave_line_set[0]['out_att'],
											})
							else:
								attendance_id = attendance_pool.create({
									'date': emp['date'],
									'in_date': emp['date'],
									'employee_id': emp['emp_id'],
									'day_shift': emp['day_shift'],
									'work_location_id': self.work_location_id.id,
									'check_in': att_in_id.attendance_time,
									'check_out': att_out_id.attendance_time,
									})
					else:
						hr_att_id = self.env['hr.attendance'].search([('employee_id', '=', emp['emp_id']), ('in_date', '=', emp['date'])], limit=1)

						if hr_att_id:
							if hr_att_id.check_in<att_out_id.attendance_time:
								attendance_obj = self.env['hr.attendance'].browse(hr_att_id.id)
								attendance_obj.update({
										'check_out': att_out_id.attendance_time,
									})
			else:
				att_n_in_id = self.env['mw.attendance'].sudo().search([('employee_id', '=',emp['emp_id']),
																('date', '=',emp['date']),('day_shift', '!=',True)], order='attendance_time desc',limit=1)
				att_n_out_id = self.env['mw.attendance'].sudo().search([('employee_id', '=', emp['emp_id']), 
												('date', '=',  emp['date']+ timedelta(days=1)),('day_shift', '!=',True)], order='attendance_time asc', limit=1)
				
				tt_ll = self.env['hr.timetable.line.line'].search([('employee_id', '=', emp['emp_id']), ('date', '=', emp['date'])])
				tt_ll.update({
							'sign_in_emp': att_n_in_id.attendance_time,
							'sign_out_emp': att_n_out_id.attendance_time,
						})
				search_n_query = """
					SELECT 
							ha.id as ha_id,
							ha.check_out as check_out
					FROM 
							hr_attendance ha
							LEFT JOIN hr_employee emp ON ha.employee_id = emp.id
					WHERE 
							ha.check_out = '%s' 
						AND ha.employee_id = '%s'
						AND ha.day_shift != True
				"""%(att_n_in_id.attendance_time, emp['emp_id'])
				self.env.cr.execute(search_n_query)
				search_n_set = self.env.cr.dictfetchall()
				if not search_n_set:
					if not self.env['hr.attendance'].search([('employee_id', '=', emp['emp_id']), ('in_date', '=', emp['date'])]):
						if att_n_in_id.attendance_time==att_n_out_id.attendance_time:
							# leave_i  d = self.env['hr.leave.mw'].search([('employee_id', '=', emp['emp_id']), ('shift_plan_id.is_work', '=', 'attendance_out'), ('date_to', '=', emp['date'])])
							leave_query = """
								SELECT 
										hlw.date_to as out_att,
										hlw.date_from as in_att,
										hst.is_work as is_work
								FROM 
										hr_leave_mw hlw
								LEFT JOIN 
										hr_shift_time hst ON hst.id=hlw.shift_plan_id
								WHERE 
										(date(hlw.date_to) = '%s' or date(hlw.date_from) = '%s')
									AND hlw.employee_id = '%s'
									AND hst.is_work in ('attendance_out','attendance') AND hlw.state_type = 'done'
							"""%(emp['date'], emp['date'],emp['emp_id'])
							self.env.cr.execute(leave_query)
							leave_set = self.env.cr.dictfetchall()
							if leave_set:
								if leave_set[0]['is_work'] == 'attendance_out':
									attendance_id = attendance_pool.create({
										'date': emp['date'],
										'in_date': emp['date'],
										'employee_id': emp['emp_id'],
										'day_shift': emp['day_shift'],
										'work_location_id': self.work_location_id.id,
										'check_in': att_n_in_id.attendance_time,
										'check_out': leave_set[0]['out_att'],
										})
								else:
									attendance_id = attendance_pool.create({
										'date': emp['date'],
										'in_date': emp['date'],
										'employee_id': emp['emp_id'],
										'day_shift': emp['day_shift'],
										'work_location_id': self.work_location_id.id,
										'check_in': leave_set[0]['in_att'],
										'check_out': att_out_id.attendance_time,
										})
							else:
								attendance_id = attendance_pool.create({
									'date': emp['date'],
									'in_date': emp['date'],
									'employee_id': emp['emp_id'],
									'day_shift': emp['day_shift'],
									'work_location_id': self.work_location_id.id,
									'check_in': att_n_in_id.attendance_time,
									'check_out': att_out_id.attendance_time,
									})
						else:
							if att_n_out_id.attendance_time:
								is_time = datetime.strptime(str(att_n_out_id.attendance_time), '%Y-%m-%d %H:%M:%S')+ timedelta(hours=8)
								if is_time.hour<10:
									attendance_id = attendance_pool.create({
										'date': emp['date'],
										'in_date': emp['date'],
										'employee_id': emp['emp_id'],
										'work_location_id': self.work_location_id.id,
										'day_shift': emp['day_shift'],
										'check_in': att_n_in_id.attendance_time,
										'check_out': att_n_out_id.attendance_time,
										})
								else:
									attendance_id = attendance_pool.create({
										'date': emp['date'],
										'in_date': emp['date'],
										'employee_id': emp['emp_id'],
										'work_location_id': self.work_location_id.id,
										'day_shift': emp['day_shift'],
										'check_in': att_n_in_id.attendance_time,
										# 'check_out': att_n_out_id.attendance_time,
										})
							else:
									attendance_id = attendance_pool.create({
										'date': emp['date'],
										'in_date': emp['date'],
										'employee_id': emp['emp_id'],
										'work_location_id': self.work_location_id.id,
										'day_shift': emp['day_shift'],
										'check_in': att_n_in_id.attendance_time,
										'check_out': att_n_out_id.attendance_time,
										})
				else:
					hr_att_id = self.env['hr.attendance'].search([('employee_id', '=', emp['emp_id']), ('in_date', '=', emp['date']), ('day_shift', '!=', True)])

					if hr_att_id and att_out_id:
						if hr_att_id.check_in<att_out_id.attendance_time:
							hr_att_id.update({
								# 'check_in': att_n_in_id.attendance_time,
								'check_out': att_n_out_id.attendance_time,
							})

				# else:
				# 	hr_att_id = self.env['hr.attendance'].search([('employee_id', '=', emp['emp_id']), ('in_date', '=', emp['date'])])
				# 	if hr_att_id:
				# 		attendance_obj = self.env['hr.attendance'].browse(hr_att_id.id)
				# 		attendance_obj.update({
				# 					'check_out': att_out_id.attendance_time,
				# 			})

		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'target': 'new',
			'nodestroy': True,
		}

	# Авто ирц хөрвүүлэх === CRON ================
	@api.model
	def cron_create_hr_attendance(self):
		com_ids = self.env['res.company'].sudo().search([('active','=',True)])
		for com in com_ids:
			loc_ids = self.env['hr.work.location'].sudo().search([('active','=',True)])
			for loc in loc_ids:
				att_id = self.env['attendance.generator'].sudo().create({
					'start_date':datetime.today()-timedelta(days=3),
					'end_date': datetime.today(),
					'company_id': com.id,
					'work_location_id': loc.id
				})
				att_id.sudo().create_attendance()











