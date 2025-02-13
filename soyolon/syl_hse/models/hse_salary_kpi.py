from odoo import api, fields, models, _
from datetime import datetime, timedelta

class HSESalaryKPILine(models.Model):
	_inherit = 'hse.salary.kpi.line'


	entered = fields.Integer(string='Өдөр тутмын хуралд оролцсон', readonly=True)
	information_disclosed = fields.Integer(string='Өдөр тутмын хуралд мэдээлэл танилцуулсан')
	previous_inspection = fields.Integer(string='Ажлын өмнөх үзлэг', readonly=True)
	occupational_safety_inspection = fields.Integer(string='Ажлын аюулгын шинжилгээ', readonly=True)
	reported_hazard = fields.Integer(string='Аюулыг мэдээлээсэн', readonly=True)
	resolved_hazard = fields.Integer(string='Аюулыг зассан', readonly=True)

	used_correctly = fields.Integer(string ='НБХХ бүрэн зөв өмсөж хэрэглэсэн', readonly=True)
	qualified_for_job = fields.Integer(string='Ажлын байрны эмч цэгцийг хангасан')
	environment_protection = fields.Integer(string = 'Байгаль орчныг хамгаалахад хувь нэмрээ оруулсан')
	attended_training = fields.Integer(string='ХЭМАБ-н сургалтанд хамрагдсан')
	new_proposal = fields.Integer(string='ХЭМАБ-н шинэ санал санаачлага гаргасан')
	entered_training = fields.Integer(string='ХЭМАБ-н тэргүүн туршлага нэвтрүүлсэн')
	


class HseSalaryKpi(models.Model):
	_inherit = 'hse.salary.kpi'


	salary_kpi_line = fields.One2many('hse.salary.kpi.line', 'kpi_id', ' Salary kpi line', readonly=True, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True, required=True, default=lambda self: self.env.user.branch_id)


	def action_to_download(self):
		salary_kpi_line =  self.env['hse.salary.kpi.line']
		daily_instrution_line = self.env['hse.employee.daily.instruction.line']
		hazard_report = self.env['hse.hazard.report']
		if self.salary_kpi_line:
			self.salary_kpi_line.unlink()
		
		s_date = self.start_date.strftime("%Y-%m-%d %H:%M:%S")
		e_date = (self.end_date + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
		if self.branch_id:
			emp_obj = self.env['hr.employee'].search([
				('employee_type','in',['working','student','trainee']),
				('department_id.branch_id','=',self.branch_id.id)
			])
			l=0
			r=0
			s=0

			for ajiltan in emp_obj:
				daily_line_pool = daily_instrution_line.search([
					('date','>=',self.start_date),
					('date','<=',self.end_date),
					('employee_id','in',[ajiltan.id])])
				if daily_line_pool:
					l += 10
				
				hazard_report_notify = hazard_report.search([
					('datetime','>=',s_date),
					('datetime','<=',e_date),
					('notify_emp_id','in',[ajiltan.id])])
				if hazard_report_notify:
					r += 10
				
				hazard_report_emp = hazard_report.search([
					('datetime','>=',self.start_date),
					('datetime','<=',self.end_date),
					('employee_id','in',[ajiltan.id])])
				if hazard_report_emp:
					s += 20

				dvn = ajiltan.job_id.employee_hse_point+l+r+s
				line_line_conf = salary_kpi_line.create({
					'kpi_id': self.id,
					'employee_id': ajiltan.id,
					'department_id': ajiltan.department_id.id,
					'job_id': ajiltan.job_id.id,
					'emp_hse_point': dvn
				})
			l=0
			r=0
			s=0