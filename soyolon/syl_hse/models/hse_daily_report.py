from odoo import  api, fields, models, _
from datetime import datetime, timedelta


class DailyReport(models.Model):
	_inherit ='hse.daily.report'

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
		work_hazard_analysis_obj = self.env['hse.work.hazard.analysis']
		preliminary_obj = sum(self.env['preliminary.notice'].sudo().search([('date','=',self.date)]))
		warning_obj = sum(self.env['hse.warning.page'].sudo().search([('date','=',self.date)]))
		for item in self:
			if item.date:
				item.ita_count = len(time_obj.sudo().search([
					('date','=',item.date),
					('employee_id.is_ita','=',True),
					('is_work_schedule','in',['day','night']),
					('hour_to_work','>=',0),
					('shift_plan_id.is_work','=','day'),
					('parent_id.department_id.branch_id','=',self.branch_id.id),
				]).ids)
				item.employee_count = len(time_obj.sudo().search([
					('date','=',item.date),
					('employee_id.is_ita','=',False),
					('is_work_schedule','in',['day','night']),
					('hour_to_work','>=',0),
					('shift_plan_id.is_work','=','day'),
					('parent_id.department_id.branch_id','=',self.branch_id.id),
					]).ids)
				item.guest_count = len(training_obj.sudo().search([('date','=',item.date),('type','=','guest')]).ids)
				item.total_employee = item.ita_count + item.employee_count +item.guest_count + item.gereet_employee_count
				item.uildver_osol = len(injury_obj.search([('date','like',item.date),('branch_id','=',self.branch_id.id)]).ids)
				# item.first_help = len(ambulance_line_obj.sudo().search([('date_day','=',item.date),('employee_id.department_id.branch_id','=',self.branch_id.id)]).ids)
				# item.hosp_help = len(ambulance_line_obj.sudo().search([
				# 		# ('date_day','=',item.date),
				# 		('employee_id.department_id.branch_id','=',self.branch_id.id)
				# 										   ]).ids)
			
				# item.hosp_help = 100
				# item.timed_damage = len(ambulance_line_obj.sudo().search([('date_day','=',item.date),('employee_id.department_id.branch_id','=',self.branch_id.id)]).ids)
				item.fire_incident = len(fire_obj.sudo().search([('date','=',item.date),('employee_id.user_id.branch_id','=',self.branch_id.id)]).ids)
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
				item.high_risk = len(work_hazard_analysis_obj.search([('date','=',item.date),('consent_ids','!=',False),('branch_id','=',self.branch_id.id)]).ids)
