# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval as eval
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64
import time, odoo.netsvc, odoo.tools, re
from odoo.exceptions import UserError, ValidationError

class SalaryUpdate(models.Model):
	_inherit = 'salary.update'

	def action_confirm_hr_director(self):

		for line in self.line_ids:
			contract_id = self.env['hr.contract'].search([('employee_id', '=', line.employee_id.id)])
			contract_id.update({'wage':line.new_wage})
			line.write({'state':'confirm_hr_director'})
			
		self.write({'state': 'confirm_hr_director'})

	def create_update_line(self):
		line_pool =  self.env['salary.update.line']
		if self.line_ids:
			self.line_ids.unlink()
		for obj in self:
			query = """SELECT 
				hr.id as hr_id,
				hd.id as hd_id,
				ho.id as ho_id,
				ho.prize_date as prize_date,
				sl.skills_allounce as skills_allounce,
				hj.id as hj_id,
				sl.id as sl_id,
				sl.amount as amount
				FROM hr_order ho
				LEFT JOIN salary_level sl ON sl.id=ho.salary_code
				LEFT JOIN hr_employee hr ON hr.id=ho.order_employee_id
				LEFT JOIN hr_department hd ON hd.id=hr.department_id
				LEFT JOIN hr_job hj ON hj.id=hr.job_id
				WHERE ho.starttime >='%s' and ho.starttime <='%s' and ho.is_wage_change =True"""%(obj.date,obj.end_date)
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			desc={}
			amount=0
			for rec in records:
				contract_id = self.env['hr.contract'].search([('employee_id','=',rec['hr_id'])],limit=1)
				line_data_id = line_pool.create({
					'department_id' : rec['hd_id'],
					'job_id' : rec['hj_id'],
					'employee_id' : rec['hr_id'],
					'date' : rec['prize_date'],
					'order_id' : rec['ho_id'],
					'old_wage_ur':contract_id.skills_allounce,
					'new_wage_ur':rec['skills_allounce'],
					'old_wage':contract_id.wage,
					'new_wage':rec['amount'],
					'old_level_id':contract_id.level_id.id,
					'new_level_id':rec['sl_id'],
					'parent_id': obj.id,
					# 'description': desc
				})

class SalaryUpdateLine(models.Model):
	_inherit = 'salary.update.line'

	old_wage_ur = fields.Float('Хуучин ур чадварын нэмэгдэл', digits=(16, 2))
	new_wage_ur = fields.Float('Шинэ ур чадварын нэмэгдэл', digits=(16, 2))
	old_level_id = fields.Many2one('salary.level','Хуучин цалингийн шатлал')
	new_level_id = fields.Many2one('salary.level','Шинэ цалингийн шатлал')

class VacationSalary(models.Model):
	_inherit = "vacation.salary"
	_description = "vacation salary"


	def create_plan_line(self):
		balance_data_pool =  self.env['vacation.salary.line']
		line_line_pool =  self.env['vacation.salary.detail']
		dep_pool = self.env['hr.department']
		balance_id = None
		month = None
		if self.emp_balance_ids:
			self.emp_balance_ids.unlink()
			if self.emp_balance_ids.detail_ids:
				self.emp_balance_ids.detail_ids.unlink()
		this_year_day=0
		vac_day=0
		year=0
		for obj in self:
			balance_id = obj.id
			
			query = """SELECT 
				hr.id as hr_id,
				line.department_id as dep_id,
				line.job_id as job_id,
				line.count_day as count_day,
				line.before_shift_vac_date as before_shift_vac_date,
				parent.id as p_id,
				hr.employee_type as employee_type,
				parent.start_date as s_date,
				parent.end_date as e_date
				FROM shift_vacation_schedule parent
				LEFT JOIN shift_vacation_schedule_line line ON line.schedule_id=parent.id
				LEFT JOIN res_company hc ON hc.id=parent.company_id
				LEFT JOIN hr_employee hr ON hr.id=line.employee_id
				WHERE parent.start_date>='%s' and parent.start_date<='%s' and hc.id=%s"""%(obj.s_date,obj.e_date,obj.company_id.id)
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			sum_day=0
			vacation_day=0
			dddd=0
			before_shift_vac_date = 0
			for record in records:
				emp_date_line = self.env['hr.employee'].search([('id','=',record['hr_id'])], limit=1)
				# print('=-=-==-=',sal_line_line)
				querysooa = """SELECT
					so.date_invoice as before_shift_vac_date
					FROM salary_order_line sol
					LEFT JOIN salary_order so on so.id=sol.order_id
					LEFT JOIN salary_order_line_line sll on sol.id=sll.order_line_id1
					WHERE sol.employee_id=%s  and  so.date_invoice<'%s' and sll.code='SOOA' and sll.amount>0
					ORDER BY so.date_invoice"""%(record['hr_id'],self.e_date)
				self.env.cr.execute(querysooa)
				sooa = self.env.cr.dictfetchall()
				if sooa:
					before_shift_vac_date = sooa[0]['before_shift_vac_date']
				else:
					before_shift_vac_date = emp_date_line.engagement_in_company
				query = """SELECT
					sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD')) as vacation_worked_day,
					sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='SUMH')) as vacation_worked_hour,
					sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS')) as amount_tootsson
					FROM salary_order_line sol
					LEFT JOIN salary_order so on so.id=sol.order_id
					WHERE sol.employee_id=%s and sol.type='final' and so.date_invoice>'%s' and so.date_invoice<'%s'"""%(record['hr_id'],before_shift_vac_date,self.e_date)
				self.env.cr.execute(query)
				vacation = self.env.cr.dictfetchall()
				balance_data_id = balance_data_pool.create({
					'employee_id': record['hr_id'],
					'department_id':record['dep_id'],
					'job_id':record['job_id'],
					# 'date':record[''],
					'vacation_day':record['count_day'],
					'sum_day':vacation[0]['vacation_worked_hour'],
					'sum_wage':vacation[0]['amount_tootsson'],
					'before_shift_vac_date':before_shift_vac_date,
					'vacation_id': balance_id,
					# 'employee_type':record[7],
					# 's_date':record[8],
					# 'e_date':record[9]
				})
				line_obj=balance_data_pool.browse(balance_data_id)
				for ll in line_obj:
					query1 = """SELECT
						(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD') as vacation_worked_day,
						(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='SUMH') as vacation_worked_hour,
						(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS') as amount_tootsson,
						sol.employee_id as employee_id,
						so.year as year,
						so.month as month
						FROM salary_order_line sol
						LEFT JOIN salary_order so ON so.id=sol.order_id
						WHERE sol.employee_id=%s and sol.type='final' and so.date_invoice>'%s' and so.date_invoice<'%s'
						ORDER BY so.year, so.month"""%(record['hr_id'],before_shift_vac_date,self.e_date)
					self.env.cr.execute(query1)
					vac = self.env.cr.dictfetchall()
					total_day=0
					for vc in vac:
							
						line_line_conf = line_line_pool.create({
								'employee_id':vc['employee_id'],
								'amount_tootsson':vc['amount_tootsson'],
								'year':vc['year'],
								'month':vc['month'],
								# 'worked_day':total,
								'worked_day':vc['vacation_worked_hour'],
								'parent_id':ll.id.id,
								})
		# EA tushaalas
			query_order = """SELECT hr.id as hr_id,
				hr.department_id as dep_id,
				hr.job_id as job_id,
				ho.con_day as con_day
				FROM hr_order ho 
				LEFT JOIN hr_employee hr ON hr.id=ho.order_employee_id 
				LEFT JOIN hr_order_type hot ON hot.id=ho.order_type_id 
				WHERE hot.type='type6'  and ho.starttime>='%s' and ho.starttime<='%s' and ho.company_id=%s and ho.state='done'"""%(obj.s_date,obj.e_date,obj.company_id.id)
			self.env.cr.execute(query_order)
			records_order = self.env.cr.dictfetchall()
			sum_day=0
			vacation_day=0
			dddd=0
			before_shift_vac_date = 0
			for rec_o in records_order:
				emp_date_line = self.env['hr.employee'].search([('id','=',rec_o['hr_id'])], limit=1)
				# print('=-=-==-=',sal_line_line)
				querysooa = """SELECT
					so.date_invoice as before_shift_vac_date,
					so.id as so_id
					FROM salary_order_line sol
					LEFT JOIN salary_order so on so.id=sol.order_id
					LEFT JOIN salary_order_line_line sll on sol.id=sll.order_line_id1
					WHERE sol.employee_id=%s  and  so.date_invoice<'%s' and sll.code='SOOA' and sll.amount>0 
					ORDER BY so.date_invoice desc LIMIT 1"""%(rec_o['hr_id'],self.e_date)
				self.env.cr.execute(querysooa)
				sooa = self.env.cr.dictfetchall()
				if sooa:
					before_shift_vac_date = sooa[0]['before_shift_vac_date']
					query = """SELECT
						sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD')) as vacation_worked_day,
						sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='SUMH')) as vacation_worked_hour,
						sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS')) as amount_tootsson
						FROM salary_order_line sol
						LEFT JOIN salary_order so on so.id=sol.order_id
						WHERE sol.employee_id=%s and sol.type='final' and so.date_invoice>'%s' and so.date_invoice<'%s'"""%(rec_o['hr_id'],before_shift_vac_date,self.e_date)
					self.env.cr.execute(query)
					vacation = self.env.cr.dictfetchall()
				else:
					before_shift_vac_date = emp_date_line.engagement_in_company
					query = """SELECT
						sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD')) as vacation_worked_day,
						sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='SUMH')) as vacation_worked_hour,
						sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS')) as amount_tootsson
						FROM salary_order_line sol
						LEFT JOIN salary_order so on so.id=sol.order_id
						WHERE sol.employee_id=%s and sol.type='final' and so.date_invoice>='%s' and so.date_invoice<'%s'"""%(rec_o['hr_id'],before_shift_vac_date,self.e_date)
					self.env.cr.execute(query)
					vacation = self.env.cr.dictfetchall()
				balance_data_id = balance_data_pool.create({
					'employee_id': rec_o['hr_id'],
					'department_id':rec_o['dep_id'],
					'job_id':rec_o['job_id'],
					# 'date':record[''],
					'vacation_day':rec_o['con_day'],
					'sum_day':vacation[0]['vacation_worked_hour'],
					'sum_wage':vacation[0]['amount_tootsson'],
					'before_shift_vac_date':before_shift_vac_date,
					'vacation_id': balance_id,
					'employee_type':'resigned',
					# 's_date':record[8],
					# 'e_date':record[9]
				})
				line_obj=balance_data_pool.browse(balance_data_id)
				for ll in line_obj:
					if sooa:
						query1 = """SELECT
							(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD') as vacation_worked_day,
							(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='SUMH') as vacation_worked_hour,
							(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS') as amount_tootsson,
							sol.employee_id as employee_id,
							so.year as year,
							so.month as month
							FROM salary_order_line sol
							LEFT JOIN salary_order so ON so.id=sol.order_id
							WHERE sol.employee_id=%s and so.type='final' and so.date_invoice>'%s' and so.date_invoice<'%s'
							ORDER BY so.year, so.month"""%(rec_o['hr_id'],before_shift_vac_date,self.e_date)
						self.env.cr.execute(query1)
						vac = self.env.cr.dictfetchall()
					else:
						query1 = """SELECT
							(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD') as vacation_worked_day,
							(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='SUMH') as vacation_worked_hour,
							(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS') as amount_tootsson,
							sol.employee_id as employee_id,
							so.year as year,
							so.month as month
							FROM salary_order_line sol
							LEFT JOIN salary_order so ON so.id=sol.order_id
							WHERE sol.employee_id=%s and so.type='final' and so.date_invoice>='%s' and so.date_invoice<'%s'
							ORDER BY so.year, so.month"""%(rec_o['hr_id'],before_shift_vac_date,self.e_date)
						self.env.cr.execute(query1)
						vac = self.env.cr.dictfetchall()
					total_day=0
					for vc in vac:
							
						line_line_conf = line_line_pool.create({
								'employee_id':vc['employee_id'],
								'amount_tootsson':vc['amount_tootsson'],
								'year':vc['year'],
								'month':vc['month'],
								# 'worked_day':total,
								'worked_day':vc['vacation_worked_hour'],
								'parent_id':ll.id.id,
								})

				# order = self.env['hr.order'].search([('id','=',record['ho_id'])],limit=1)
				# balance_data_id = balance_data_pool.create({
				# 	'employee_id': record['hr_id'],
				# 	'department_id':record['dep_id'],
				# 	'job_id':record['job_id'],
				# 	'date':record['starttime'],
				# 	'vacation_niit_day':order.vac_days,
				# 	'vacation_day':order.start_days,
				# 	'vacation_over_day':order.end_days,
				# 	'before_shift_vac_date':record['before_shift_vac_date'],
				# 	'vacation_id': balance_id,
				# })



	# def create_plan_line(self):
	# 	balance_data_pool =  self.env['vacation.salary.line']
	# 	line_line_pool =  self.env['vacation.salary.detail']
	# 	dep_pool = self.env['hr.department']
	# 	balance_id = None
	# 	month = None
	# 	if self.emp_balance_ids:
	# 		self.emp_balance_ids.unlink()
	# 		if self.emp_balance_ids.detail_ids:
	# 			self.emp_balance_ids.detail_ids.unlink()
	# 	this_year_day=0
	# 	vac_day=0
	# 	year=0
	# 	for obj in self:
	# 		balance_id = obj.id           
	# 		query = """SELECT 
	# 			hr.id as hr_id,
	# 			hr.department_id as dep_id,
	# 			hr.job_id as job_id,
	# 			hr.before_shift_vac_date as before_shift_vac_date,
	# 			ho.starttime as starttime,
	# 			ho.id as ho_id
	# 			FROM hr_order ho
	# 			LEFT JOIN hr_order_type t ON t.id=ho.order_type_id
	# 			LEFT JOIN hr_employee hr ON hr.id=ho.order_employee_id
	# 			WHERE ho.starttime>='%s' and ho.starttime<='%s' and t.type in ('type14', 'type6')"""%(obj.s_date,obj.e_date)
	# 		self.env.cr.execute(query)
	# 		records = self.env.cr.dictfetchall()
	# 		sum_day=0
	# 		vacation_day=0
	# 		dddd=0
	# 		for record in records:
	# 			order = self.env['hr.order'].search([('id','=',record['ho_id'])],limit=1)
	# 			balance_data_id = balance_data_pool.create({
	# 				'employee_id': record['hr_id'],
	# 				'department_id':record['dep_id'],
	# 				'job_id':record['job_id'],
	# 				'date':record['starttime'],
	# 				'vacation_niit_day':order.vac_days,
	# 				'vacation_day':order.start_days,
	# 				'vacation_over_day':order.end_days,
	# 				'before_shift_vac_date':record['before_shift_vac_date'],
	# 				'vacation_id': balance_id,
	# 			})


class VacationSalaryLine(models.Model):
	_inherit = "vacation.salary.line"	

	@api.depends('sum_wage','sum_day')
	def _wage_day(self):
		for obj in self:
			if obj.sum_day>0:
				obj.one_day_wage = (obj.sum_wage/obj.sum_day)*8
			else:
				obj.one_day_wage = 0

class Department(models.Model):
	_inherit = "hr.department"

	is_salhit = fields.Boolean('Салхит эсэх')
	branch_id = fields.Many2one('res.branch', 'Салбар')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Аналитик')
	partner_id =fields.Many2one('res.partner', 'Харилцагч')
	vacation_id=fields.Many2one('account.account','Олгосон ээлжийн амралтын цалин')
	advance_id=fields.Many2one('account.account','Суутгал-Цалингийн урьдчилгаа')
	account_health_id=fields.Many2one('account.account','Ажилчидаас авах авлага /Сайн дурын ЭМД/')
	account_phone_id=fields.Many2one('account.account','Ажилчидаас авах авлага/Утасны ярианы төлбөр')
	account_car_id=fields.Many2one('account.account','Ажилчидаас авах авлага/Автомашины торгууль')
	account_clothes_id=fields.Many2one('account.account','Ажилчидаас авах авлага/Ажлын хувцас, гутал')
	account_employee_rec_id=fields.Many2one('account.account','Ажилчидаас авах авлага')
	analytic_shi_account_id = fields.Many2one('account.analytic.account', 'НДШ аналитик')
	account_advance_id=fields.Many2one('account.account','Урьдчилгаа цалин')



class Contract(models.Model):
	_inherit = 'hr.contract'

	skills_allounce = fields.Float('Ур чадварын нэмэгдэл')
	sum_wage = fields.Float('Нэг цагийн дундаж цалин', digits=(16, 2), readonly=True, compute='_compute_sum_wage')
	level_id = fields.Many2one('salary.level','Цалингийн шатлал')
	wage = fields.Float('Үндсэн цалин',)

	@api.depends('skills_allounce','wage')
	def _compute_sum_wage(self):
		for obj in self:
			obj.sum_wage=obj.skills_allounce+obj.wage

	
	@api.onchange('level_id')
	def populate_wage(self):
		if self.level_id:
			self.skills_allounce = self.level_id.skills_allounce
			self.wage = self.level_id.amount
			self.salary_type = 'hour'
  

class salary_order(models.Model):
	_inherit = "salary.order"


	state = fields.Selection(
		[
			("draft", "Ноорог"),
			("send", "Илгээсэн"),
			("nybo", "Ерөнхий нябо хянасан"),
			("done", "Санхүү хариуцсан захирал баталсан"),
		],
		"Status",
		readonly=True,
		default="draft",
		tracking=True,
		copy=False,
	)
	
	clothes_move_id = fields.Many2one('account.move', string='Ажилчидын хувцас, хэрэгсэл бичилт',readonly=True)
	phone_move_id = fields.Many2one('account.move', string='Утасны бичилт',readonly=True)
	car_move_id = fields.Many2one('account.move', string='Торгуулийн бичилт',readonly=True)
	health_move_id = fields.Many2one('account.move', string='Сайн дурын-ЭМД бичилт',readonly=True)
	advance_move_id = fields.Many2one('account.move', string='Суутгал-Урьдчилгаа цалин',readonly=True)
	account_emp_move_id = fields.Many2one('account.move', string='Ажилчдын авлагын бичилт',readonly=True)
	account_hhoat_move_id = fields.Many2one('account.move', string='ХХОАТ бичилт',readonly=True)
	account_vacation_move_id = fields.Many2one('account.move', string='ЭА цалин хаав',readonly=True)
	account_advance_move_id = fields.Many2one('account.move', string='Урьдчилгаа цалин хаав',readonly=True)
	account_salary_cost_id=fields.Many2one('account.account','Урьдчилж гарсан зардал-Цалин')
	account_shi_cost_id=fields.Many2one('account.account','Урьдчилж гарсан зардал-НДШ')
	account_advance_cost_id=fields.Many2one('account.account','Урьдчилгаа цалингийн данс')

	@api.onchange('work_location_id', 'type')
	def _get_account(self):
		res = super(salary_order, self)._onchange_account()
		obj = self.env['salary.account.conf'].search([('company_id', '=', self.company_id.id)], limit=1)
		if obj:
			self.account_salary_cost_id = obj.account_salary_cost_id.id
			self.account_shi_cost_id = obj.account_shi_cost_id.id
			self.account_advance_cost_id = obj.account_advance_cost_id.id
		else:
			self.account_salary_cost_id= False
			self.account_shi_cost_id=False
			self.account_advance_cost_id=False
		return res

	def draft_action(self):
		return super().draft_action()

	def send_action(self):
		return super().send_action()
	
	def nybo_action(self):
		self.state = 'nybo'

	def done_action(self):
		self.state = 'done'
	
	def action_send_mail(self):
		return super().action_send_mail()

	def compute_create(self, context=None):
		def _sum_salary_category(tomyo, code, line):
			localdict2 = {}
			for l in line.so_line_line:
				localdict2[code] = l.amount

			return localdict2

		cont = self.env["hr.contract"]
		order_line = self.env["salary.order.line"]
		salary_order = self.env["salary.order"]
		line_line_pool = self.env["payroll.fixed.allounce.deduction.line.line"]
		line_pool = self.env["payroll.fixed.allounce.deduction.line"]
		allounce_deduction_pool = self.env["payroll.fixed.allounce.deduction"]
		balance_pool = self.env["hour.balance.dynamic.line.line"]
		balance_vacation_pool = self.env["vacation.salary.line"]
		employee_pool = self.env["hr.employee"]
		iswrite = False
		if self.order_line:
			self.order_line.unlink()
			if self.order_line.so_line_line:
				self.order_line.so_line_line.unlink()
		if self.type == "final":
			if self.company_id:
				allounce_deductions = allounce_deduction_pool.search([("year", "=", self.year), ("month", "=", self.month)])
				setups = []
				allounce_deduction_ids = allounce_deductions.mapped("id")
				self_ads = self.search([("month", "=", self.month)])
				self_ad_ids = self_ads.mapped("id")

				ctx = dict(self._context)
				if self.work_location_id:
					query_salary = """SELECT 
						l.id as id,
						l.employee_id as emp_id,
						hr.identification_id as identification_id
						FROM hour_balance_dynamic_line_line ll
						LEFT JOIN hour_balance_dynamic_line l on ll.parent_id=l.id
						LEFT JOIN hour_balance_dynamic hb on l.parent_id=hb.id
						LEFT JOIN hr_employee hr on l.employee_id=hr.id
						WHERE hb.year='%s' and hb.month='%s' and hb.type='final' and hb.work_location_id='%s' and hb.state='done'
						GROUP BY l.employee_id,l.id,hr.identification_id""" % (
						self.year,
						self.month,
						self.work_location_id.id,
					)
					self.env.cr.execute(query_salary)
					recs = self.env.cr.dictfetchall()
				else:
					query_salary = """SELECT 
						l.id as id,
						l.employee_id as emp_id,
						hr.identification_id as identification_id
						FROM hour_balance_dynamic_line_line ll
						LEFT JOIN hour_balance_dynamic_line l on ll.parent_id=l.id
						LEFT JOIN hour_balance_dynamic hb on l.parent_id=hb.id
						LEFT JOIN hr_employee hr on l.employee_id=hr.id
						WHERE hb.year='%s' and hb.month='%s' and hb.type='final' and hb.state='done'
						GROUP BY l.employee_id,l.id,hr.identification_id""" % (
						self.year,
						self.month,
					)
					self.env.cr.execute(query_salary)
					recs = self.env.cr.dictfetchall()
				n=1
				for balance in recs:
					balance_id = self.env["hour.balance.dynamic.line"].search([("id", "=", balance["id"])])
					balance_line_ids = self.env["hour.balance.dynamic.line.line"].search([("parent_id", "=", balance["id"])])
					cont_ids = cont.search([("employee_id", "=", balance["emp_id"])])
					punishment_id = self.env["hr.order"].search([("order_employee_id", "=", balance["emp_id"]),("start_date", "<=", self.date_invoice),
								("end_date", ">=", self.date_invoice),("state", "=", 'done'),("deduct", ">", 0)],limit=1)

					if len(cont_ids) == 1:
						cont_id = cont_ids[0]
					else:
						raise UserError(("%s кодтой ажилтны гэрээ байхгүй эсвэл олон бүртгэгдсэн байна"% (balance["identification_id"])))
					rate_id = self.env["res.currency.rate"].search([("currency_id", "=", cont_id.res_currency_id.id),("name", "<=", self.date_invoice),],order="name desc",)
					rate = 0
					if rate_id:
						rate = rate_id[0].rate
						basic = cont_id.wage * rate
					else:
						basic = cont_id.wage
					insured_id = cont_id.insured_type_id
					query = """select 
						sum(ll.amount)
						from payroll_fixed_allounce_deduction_line l
						left join payroll_fixed_allounce_deduction_line_line ll on ll.setup_line_id=l.id
						left join payroll_fixed_allounce_deduction al on al.id=l.setup_id
						where ll.type='debt' and l.employee_id=%s and al.year='%s' and al.month='%s'""" % (cont_id.employee_id.id,self.year,self.month,)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
					pit_disc = records[0][0]
					
					vals = {
						"name": cont_id.employee_id.name,
						"number": n,
						"last_name": cont_id.employee_id.last_name,
						"ident_id": cont_id.employee_id.identification_id,
						"year": self.year,
						"month": self.month,
						"day_to_work": balance_id.day_to_work_month,
						"hour_to_work": balance_id.hour_to_work_month,
						"date": self.date_invoice,
						"type": self.type,
						"insured_type_id": insured_id.id,
						"employee_id": cont_id.employee_id.id,
						"basic": basic,
						"pit_discount": pit_disc,
						"pit_procent": cont_id.insured_type_id.shi_procent,
						"order_id": self.id,
						"contract_id": cont_id.id,
						"email_address": cont_id.employee_id.private_email,
						'punishment_procent':punishment_id.deduct,
						# 'tree_month_average_wage': cont_id.average_wage,
						# "tree_month_average_wage": tree_average_wage,
						# "tree_month_sum_hour": tree_hour,
						# "tree_month_sum_wage": tree_wage,
						"is_pit": cont_id.is_pit,
						"levelname": cont_id.level_id.name,
					}
					if not iswrite:
						move = order_line.with_context(ctx).create(vals)
					else:
						move = iswrite
					balance_id.write({"balance_line_id": move.id})
					for bal_l_l in balance_line_ids:
						balance_line_id = self.env[
							"hour.balance.dynamic.line.line"
						].search([("id", "=", bal_l_l.id)])
						balance_line_id.write({"order_balance_line_id": move.id})
					# Нэмэгдэл суутгал
					lines = line_pool.search([("employee_id", "=", cont_id.employee_id.id),
							("setup_id", "in", allounce_deduction_ids),])
					line_line_ids = []
					for cl in lines:
						for l in cl.setup_line_line:
							if not l.category_id.is_advance:
								v = {"order_line_id1": move.id}
								v["name"] = l.name
								v["is_tree"] = l.category_id.is_tree
								v["category_id"] = l.category_id.id
								v["every_month"] = l.every_month
								v["type"] = l.type
								# if l.category_id.fixed_type == "hour_balance":
								#     all_conf = self.env['hr.allounce.deduction.category'].search([('id','=',l.category_id.id)])
								#     conf_ids = all_conf.mapped('hour_ids')
								#     all_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
								#                                     ('parent_id.parent_id.month','=',self.month),
								#                                     ('parent_id.parent_id.type','=','final'),
								#                                     ('parent_id.employee_id','=',balance["emp_id"]),
								#                                     ('conf_id','in',conf_ids.ids)])

								#     hour_ids = all_hours.mapped('conf_id')
								#     hour_sum = sum(all_hours.mapped('hour'))
								#     localdict={'move':move,'hour':hour_sum,'result':None}
								#     tomyo=l.category_id.tomyo.replace(u'үндсэн цалин','move.basic')
								#     if '/' in tomyo:
								#         try:
								#             eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  
								#         except ValueError:
								#             raise UserError((u'%s ажилтны %s ийн цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.employee_id.name,l.category_id.name)))
								#     else:
								#         eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  

								#     v['amount']=localdict['result']
								if l.category_id.fixed_type == "hour_balance":
									all_conf = self.env['hr.allounce.deduction.category'].search([('id','=',l.category_id.id)])
									conf_ids = all_conf.mapped('hour_ids')
									all_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																	('parent_id.parent_id.month','=',self.month),
																	('parent_id.parent_id.type','=','final'),
																	('parent_id.employee_id','=',balance["emp_id"]),
																	('conf_id','in',conf_ids.ids)])
									conf_min_ids = all_conf.mapped('hour_minus_ids')
									all_min_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																	('parent_id.parent_id.month','=',self.month),
																	('parent_id.parent_id.type','=','final'),
																	('parent_id.employee_id','=',balance["emp_id"]),
																	('conf_id','in',conf_min_ids.ids)])
									conf_is_ids = all_conf.mapped('hour_is_ids')
									all_is_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																	('parent_id.parent_id.month','=',self.month),
																	('parent_id.parent_id.type','=','final'),
																	('parent_id.employee_id','=',balance["emp_id"]),
																	('conf_id','in',conf_is_ids.ids)])

									hour_ids = all_hours.mapped('conf_id')
									hour_sum = sum(all_hours.mapped('hour'))
									is_hour = sum(all_is_hours.mapped('hour'))
									hour_minus = sum(all_min_hours.mapped('hour'))
									localdict={'move':move,'hour':hour_sum,'is_hour':is_hour,'hour_minus':hour_minus,'result':None}
									tomyo=l.category_id.tomyo.replace(u'үндсэн цалин','move.basic')
									if '/' in tomyo:
										try:
											eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  
										except ValueError:
											raise UserError((u'%s ажилтны %s ийн цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.employee_id.name,l.category_id.name)))
									else:
										eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  

									v['amount']=localdict['result']

								if l.category_id.fixed_type == "tomyo":
									localdict = {"cl": cl, "move": move, "result": None}
									"resutl=basic*0.1 гм байна"
									tomyo = l.category_id.tomyo.replace("үндсэн цалин", "move.basic")
									if "/" in tomyo:
										try:
											eval("%s" % (tomyo), localdict, mode="exec", nocopy=True,)
										except ValueError:
											raise UserError(("%s ажилтны %s ийн томъёонд 0 өгөгдөл орсоноос алдаа гарлаа."% (cl.employee_id.name,l.category_id.name,)))
									else:
										eval("%s" % (tomyo),localdict,mode="exec",nocopy=True,)
									v["amount"] = localdict["result"]
								if l.category_id.fixed_type == "depend":
									depend_ids = []
									for i in l.category_id.depend_ids:
										depend_ids.append(i.id)
									# if move.employee_id.employee_type!='resigned':
									if l.amount>0:
										v["amount"] = l.amount
									else:
										line_lines = order_line.search([("order_id.year", "=", self.year),
										("order_id.month", "=", self.month),
										("order_id.type", "=", "advance"),
										("employee_id", "=", move.employee_id.id), ('is_advance_check', '=', False),])
										if line_lines.amount_net:
											v["amount"] = line_lines.amount_net
										else:
											v["amount"]=0

								if l.category_id.fixed_type == "fixed":
									v["amount"] = l.amount

								# if l.category_id.code == "SOOA":
								#     balance_vacation_lines = (balance_vacation_pool.search([("vacation_id.e_date","=",self.date_invoice,),
								#                 ("employee_id", "=", cl.employee_id.id),]))
								#     for balance_vacation in balance_vacation_lines:
								#         v["amount"] = balance_vacation.wage_sum_amount
								if l.category_id.code == "SOOA":
									balance_vacation_lines = self.env['vacation.salary.line'].search([("vacation_id.e_date","=",self.date_invoice,),
												("employee_id", "=", cl.employee_id.id)])
									if balance_vacation_lines:
										for balance_vacation in balance_vacation_lines:
											v["amount"] = balance_vacation.wage_sum_amount

								if l.category_id.code == "DEEARLY":
									ded_line = self.env['deductioin.plan.line'].search([("date","=",self.date_invoice),
												("parent_id.employee_id", "=", cl.employee_id.id)])
									if ded_line:
										for ded in ded_line:
											v["amount"] = ded.amount
									else:
										v["amount"]=0
										

								if l.category_id.code == "DEHI":
									health_line = self.env['health.insurance.line'].search([("date","=",self.date_invoice),
												("parent_id.employee_id", "=", cl.employee_id.id)])
									if health_line:
										for health in health_line:
											v["amount"] = health.amount
									else:
										v["amount"]=0

								if l.category_id.code == "UDAAN":
									udaan = self.env['long.year.salary.line'].search([("parent_id.salary_date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id)])
									if udaan:
										for ud in udaan:
											v["amount"] = ud.amount
									else:
										v["amount"]=0

								if l.category_id.code == "DEUDAAN":
									udaan_line = self.env['long.year.salary.line'].search([("parent_id.salary_date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id),('parent_id.is_salary','=', True)])
									if udaan_line:
										for ud_l in udaan_line:
											v["amount"] = ud_l.amount_net_round
									else:
										v["amount"]=0

								if l.category_id.code == "SALESPAY":
									sales = self.env['sales.salary.line'].search([("parent_id.end_date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id)])
									if sales:
										for ud in sales:
											v["amount"] = ud.amount
									else:
										v["amount"]=0

								if l.category_id.code == "DESALES":
									sales_line = self.env['sales.salary.line'].search([("parent_id.end_date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id),('parent_id.is_salary','=', True)])
									if sales_line:
										for ud_l in sales_line:
											v["amount"] = ud_l.amount_net_round
									else:
										v["amount"]=0

								# if l.category_id.code == "UJ":
								# 	v["amount"] = cont_id.long_year_wage
								# line_ids = order_line.search([("employee_id", "=", cont_id.employee_id.id),
								# 		("order_id.month", "=", self.month)],limit=1,)
								

								if l.category_id.code == "DECEL":
									# partner = self.env['res.partner'].search([("vat","=",cl.employee_id.passport_id,)],limit=1)
									phone = self.env['receivable.payable.line'].search([("employee_id","=",cl.employee_id.id), ('parent_id.date_invoice','=', self.date_invoice ), ("mobile_payable", "!=", 0)])
									if phone:
										for shop in phone:
											v["amount"] = shop.mobile_payable
									else:
										v['amount'] =0
								


								if l.category_id.code == "DECAR":
									pay = self.env['receivable.payable.line'].search([("employee_id","=",cl.employee_id.id), ('parent_id.date_invoice','=', self.date_invoice),("payment_payable", "!=", 0) ])
									if pay:
										for shop in pay:
											v["amount"] = shop.payment_payable
									else:
										v['amount'] = 0
								

								if l.category_id.code == "DECLOTH":
									cloth= self.env['receivable.payable.line'].search([("employee_id","=",cl.employee_id.id), ('parent_id.date_invoice','=', self.date_invoice ),("clothes_payable", "!=", 0)])
									if cloth:
										for shop in cloth:
											v["amount"] = shop.clothes_payable
									
									


								if l.category_id.code == "OTHSUU":
									av= self.env['receivable.payable.line'].search([("employee_id","=",cl.employee_id.id), ('parent_id.date_invoice','=', self.date_invoice ),("receivable_payable", "!=", 0)])
									if av:
										for shop in av:
											v["amount"] = shop.receivable_payable
									else:
										v["amount"]=0

								if l.category_id.code == "SKILLPAY":
									perpormance = self.env['perpormance.salary.line'].search([("parent_id.date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id),("amount", "!=", 0)])
									if perpormance:
										for per in perpormance:
												v["amount"] = per.amount
									else:
										v["amount"]=0
								
								# ene sar 0 bh ystoi gsn uchir daraw
								if l.category_id.code == "DESKILL":
									perpormance = self.env['perpormance.salary.line'].search([("parent_id.date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id),("amount_net_round", "!=", 0),('parent_id.is_salary','=', True) ])
									if perpormance:
										for per in perpormance:
											v["amount"] = per.amount_net_round
									else:
										v["amount"] =0

								if l.category_id.code == "PROJECTPAY":
									perpormance = self.env['perpormance.salary.line'].search([("parent_id.date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id),("amount_net_round", "!=", 0)])
									if perpormance:
										for per in perpormance:
											v["amount"] = per.amount
									else:
										v["amount"] =0

								if l.category_id.code == "KPIN":
									kpi = self.env['kpi.salary.line'].search([("parent_id.end_date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id), ("amount", "!=", 0) ])
									if kpi:
										for k in kpi:
											v["amount"] = k.amount
									else:
										v['amount'] =0

								
								if l.category_id.code == "DAD":
									line = self.env['dad.salary.line'].search([("parent_id.salary_date","=",self.date_invoice),
												("employee_id", "=", cl.employee_id.id),('amount', '!=', 0)])
									if line:
										for per in line:
											v["amount"] = per.amount
									else:
										v["amount"]=0

								v1 = {"order_line_id2": move.id}
								v1["name"]=v["amount"]
								move.so_line_line.create(v)
								move.so_line_line1.create(v1)
								l.write(v)
					n+=1
			else:
				raise UserError(("Компани сонгоно уу!"))
		elif self.type == "advance":
			allounce_deductions = allounce_deduction_pool.search([("year", "=", self.year), ("month", "=", self.month)])
			setups = []
			allounce_deduction_ids = allounce_deductions.mapped("id")
			self_ads = self.search([("month", "=", self.month)])
			self_ad_ids = self_ads.mapped("id")

			ctx = dict(self._context)
			if self.work_location_id:
				query_salary = """SELECT 
					l.id as id,
					l.employee_id as emp_id,
					hr.identification_id as identification_id
					FROM hour_balance_dynamic_line_line ll
					LEFT JOIN hour_balance_dynamic_line l on ll.parent_id=l.id
					LEFT JOIN hr_employee hr on l.employee_id=hr.id
					LEFT JOIN hour_balance_dynamic hb on l.parent_id=hb.id
					WHERE hb.year='%s' and hb.month='%s' and hb.type='advance' and hb.work_location_id='%s' and hb.state='done'
					GROUP BY l.employee_id,l.id,hr.identification_id""" % (self.year,self.month,self.work_location_id.id,)
				self.env.cr.execute(query_salary)
				recs = self.env.cr.dictfetchall()
			else:
				query_salary = """SELECT 
					l.id as id,
					l.employee_id as emp_id,
					hr.identification_id as identification_id
					FROM hour_balance_dynamic_line_line ll
					LEFT JOIN hour_balance_dynamic_line l on ll.parent_id=l.id
					LEFT JOIN hr_employee hr on l.employee_id=hr.id
					LEFT JOIN hour_balance_dynamic hb on l.parent_id=hb.id
					WHERE hb.year='%s' and hb.month='%s' and hb.type='advance' and hb.state='done'
					GROUP BY l.employee_id,l.id,hr.identification_id""" % (self.year,self.month)
				self.env.cr.execute(query_salary)
				recs = self.env.cr.dictfetchall()
			n=1
			for balance in recs:
				balance_id = self.env["hour.balance.dynamic.line"].search([("id", "=", balance["id"])])
				balance_line_ids = self.env["hour.balance.dynamic.line.line"].search([("parent_id", "=", balance["id"])])
				cont_ids = cont.search([("employee_id", "=", balance["emp_id"])])
				punishment_id = self.env["hr.order"].search([("order_employee_id", "=", balance["emp_id"]),("start_date", "<=", self.date_invoice),
								("end_date", ">=", self.date_invoice),("state", "=", 'done'),("deduct", ">", 0)],limit=1)

				if len(cont_ids) == 1:
					cont_id = cont_ids[0]
				else:
					raise UserError(("%s кодтой ажилтны гэрээ байхгүй эсвэл олон бүртгэгдсэн байна"% (balance["identification_id"])))
				rate_id = self.env["res.currency.rate"].search([("currency_id", "=", cont_id.res_currency_id.id),
								("name", "<=", self.date_invoice),],order="name desc",)
				rate = 0
				if rate_id:
					rate = rate_id[0].rate
					basic = cont_id.wage * rate
				else:
					basic = cont_id.wage
				insured_id = cont_id.insured_type_id
				query = """select 
						sum(ll.amount)
						from payroll_fixed_allounce_deduction_line l
						left join payroll_fixed_allounce_deduction_line_line ll on ll.setup_line_id=l.id
						left join payroll_fixed_allounce_deduction al on al.id=l.setup_id
						where ll.type='debt' and l.employee_id=%s and al.year='%s' and al.month='%s'""" % (
					cont_id.employee_id.id,
					self.year,
					self.month,
				)
				self.env.cr.execute(query)
				records = self.env.cr.fetchall()
				pit_disc = records[0][0]
				vals = {
					"name": cont_id.employee_id.name,
					"number": n,
					"last_name": cont_id.employee_id.last_name,
					"ident_id": cont_id.employee_id.identification_id,
					"year": self.year,
					"month": self.month,
					"day_to_work": balance_id.day_to_work_month,
					"hour_to_work": balance_id.hour_to_work_month,
					"hour_to_work_all": balance_id.hour_to_work,
					"date": self.date_invoice,
					"type": self.type,
					"insured_type_id": insured_id.id,
					"employee_id": cont_id.employee_id.id,
					"basic": basic,
					"pit_discount": pit_disc,
					"pit_procent": cont_id.insured_type_id.shi_procent,
					"order_id": self.id,
					"contract_id": cont_id.id,
					"punishment_procent":punishment_id.deduct,
					"email_address": cont_id.employee_id.private_email,
					"tree_month_average_wage": cont_id.average_wage,
					"is_pit": cont_id.is_pit,
					"levelname": cont_id.level_id.name,
				}
				if not iswrite:
					move = order_line.with_context(ctx).create(vals)
				else:
					move = iswrite
				balance_id.write({"balance_line_id": move.id})
				for bal_l_l in balance_line_ids:
					balance_line_id = self.env["hour.balance.dynamic.line.line"].search([("id", "=", bal_l_l.id)])
					balance_line_id.write({"order_balance_line_id": move.id})
				# Нэмэгдэл суутгал
				lines = line_pool.search([("employee_id", "=", cont_id.employee_id.id),("setup_id", "in", allounce_deduction_ids),])
				line_line_ids = []
				for cl in lines:
					for l in cl.setup_line_line:
						if l.category_id.is_advance:
							v = {"order_line_id1": move.id}
							v["name"] = l.name
							v["is_tree"] = l.category_id.is_tree
							v["category_id"] = l.category_id.id
							v["every_month"] = l.every_month
							v["type"] = l.type
							# if l.category_id.fixed_type == "hour_balance":
							#     all_conf = self.env['hr.allounce.deduction.category'].search([('id','=',l.category_id.id)])
							#     conf_ids = all_conf.mapped('hour_ids')
							#     all_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
							#                                     ('parent_id.parent_id.month','=',self.month),
							#                                     ('parent_id.parent_id.type','=','advance'),
							#                                     ('parent_id.employee_id','=',balance["emp_id"]),
							#                                     ('conf_id','in',conf_ids.ids)])

							#     hour_ids = all_hours.mapped('conf_id')
							#     hour_sum = sum(all_hours.mapped('hour'))
							#     localdict={'move':move,'hour':hour_sum,'result':None}
							#     tomyo=l.category_id.tomyo.replace(u'үндсэн цалин','move.basic')
							#     if '/' in tomyo:
							#         try:
							#             eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  
							#         except ValueError:
							#             raise UserError((u'%s ажилтны %s ийн цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.employee_id.name,l.category_id.name)))
							#     else:
							#         eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  

							#     v['amount']=localdict['result']
								# v["amount"] = hour_sum
							if l.category_id.fixed_type == "hour_balance":
								all_conf = self.env['hr.allounce.deduction.category'].search([('id','=',l.category_id.id)])
								conf_ids = all_conf.mapped('hour_ids')
								all_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																('parent_id.parent_id.month','=',self.month),
																('parent_id.parent_id.type','=','advance'),
																('parent_id.employee_id','=',balance["emp_id"]),
																('conf_id','in',conf_ids.ids)])
								conf_min_ids = all_conf.mapped('hour_minus_ids')
								all_min_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																('parent_id.parent_id.month','=',self.month),
																('parent_id.parent_id.type','=','advance'),
																('parent_id.employee_id','=',balance["emp_id"]),
																('conf_id','in',conf_min_ids.ids)])
								conf_is_ids = all_conf.mapped('hour_is_ids')
								all_is_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																('parent_id.parent_id.month','=',self.month),
																('parent_id.parent_id.type','=','advance'),
																('parent_id.employee_id','=',balance["emp_id"]),
																('conf_id','in',conf_is_ids.ids)])

								hour_ids = all_hours.mapped('conf_id')
								hour_sum = sum(all_hours.mapped('hour'))
								is_hour = sum(all_is_hours.mapped('hour'))
								hour_minus = sum(all_min_hours.mapped('hour'))
								localdict={'move':move,'hour':hour_sum,'is_hour':is_hour,'hour_minus':hour_minus,'result':None}
								tomyo=l.category_id.tomyo.replace(u'үндсэн цалин','move.basic')
								if '/' in tomyo:
									try:
										eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  
									except ValueError:
										raise UserError((u'%s ажилтны %s ийн цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.employee_id.name,l.category_id.name)))
								else:
									eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  

								v['amount']=localdict['result']
							if l.category_id.fixed_type == "tomyo":
								localdict = {"cl": cl, "move": move, "result": None}
								"resutl=basic*0.1 гм байна"
								tomyo = l.category_id.tomyo.replace("үндсэн цалин", "move.basic")
								if "/" in tomyo:
									try:
										eval("%s" % (tomyo), localdict, mode="exec", nocopy=True,)
									except ValueError:
										raise UserError(( "%s ажилтны %s ийн томъёонд 0 өгөгдөл орсоноос алдаа гарлаа."% (cl.employee_id.name,l.category_id.name,)))
								else:
									eval( "%s" % (tomyo), localdict, mode="exec", nocopy=True,)
								v["amount"] = localdict["result"]
							if l.category_id.fixed_type == "depend":
								depend_ids = []
								for i in l.category_id.depend_ids:
									depend_ids.append(i.id)

								
								line_lines = order_line.search([
										("order_id.year", "=", self.year),
										("order_id.month", "=", self.month),
										("order_id.type", "=", "advance"),
										("employee_id", "=", move.employee_id.id),])
							
								v["amount"] = line_lines.amount_net
							if l.category_id.fixed_type == "fixed":
								v["amount"] = l.amount

							if l.category_id.code == "UJ":
								v["amount"] = cont_id.long_year_wage
							line_ids = order_line.search([("employee_id", "=", cont_id.employee_id.id),
									("order_id.month", "=", self.month),],limit=1,)
							move.so_line_line.create(v)
							v1 = {"order_line_id2": move.id}
							v1['name']=v["amount"]
							move.so_line_line1.create(v1)
							l.write(v)
			n+=1
		return True

	def create_expense_invoice_syl(self):
		move_pool = self.env['account.move']
		dep_id = self.env['hr.department']
		user_bool = self.env['res.users']
		partner_bool = self.env['res.partner']
		timenow = time.strftime('%Y-%m-%d')
		
		for obj in self:
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}
			self.env.cr.execute('''SELECT 
				aa.name as hd_name,
				aa.id as aa_id, 
				sum(ll.amount) as amount,
				cat.expense_type as expense_type
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
				LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN hr_department hd ON hd.id=he.department_id
				LEFT JOIN account_analytic_account aa ON aa.id=hd.analytic_account_id
				WHERE so.id='''+str(obj.id)+'''  and cat.expense_type is not null
				GROUP BY aa.id, cat.expense_type
				ORDER BY aa.id
					''')
				
			origin=''
			records = self.env.cr.dictfetchall()
			inv_ids=[]
			amount = 0
			all_amount = 0
			shi = 0
			analityc_lines={}
			for rec in records:
				# analytic_id = self.env['account.analytic.account'].search([('id','=',rec['aa_id'])],limit=1)
				# analytic_ids = analytic_id.mapped("id")

				if rec['expense_type']=='expense':
					if obj.account_salary_cost_id:
						amount += rec['amount']
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Цалин',
						'date': obj.date_invoice,
						'partner_id': obj.partner_id.id,
						'branch_id':False,
						'account_id': obj.account_salary_cost_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': rec['amount'],
						'credit': 0
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Урьдчилж гарсан цалингийн зардлын данс тохируулна уу.')%(obj.account_salary_cost_id))
				elif rec['expense_type']=='shi':
					shi += rec['amount']
					if obj.account_shi_cost_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'БНДШ зардал',
						'date': obj.date_invoice,
						'partner_id': obj.partner_id.id,
						'branch_id':False,
						'account_id': obj.account_shi_cost_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': rec['amount'],
						'credit': 0
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Урьдчилж гарсан НДШ зардлын данс тохируулна уу.')%(obj.account_shi_cost_id))

			credit_line = (0, 0, {
			'name': 'Цалингийн өглөг',
			'date': obj.date_invoice,
			'partner_id': obj.partner_id.id,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': 0,
			'credit': amount,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			credit_line = (0, 0, {
			'name': 'НДШ өглөг',
			'date': obj.date_invoice,
			'partner_id': obj.pit_partner_id.id,
			'branch_id':False,
			'account_id': obj.account_ndsh_id.id,
			'journal_id': obj.journal_id.id,
			'debit': 0,
			'credit': shi,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']
			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'move_id': move_id.id,})
			# move_pool.post()
		return True


	def create_expense_invoice_clothes_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.clothes_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DECLOTH')) as decloth
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			decloth = 0
		
			for rec in records_avlaga:
				decloth += rec['decloth']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['decloth']>0:
					if employee_id.department_id.account_clothes_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Суутгал-Ажлын хувцас, гутал',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.account_clothes_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['decloth']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Ажлын хувцас, гутал данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'Ажилтны авлага-Хувцас гутал',
			'date': obj.date_invoice,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': decloth,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']
			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'clothes_move_id': move_id.id,})
		return True

	def create_expense_invoice_health_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.health_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DEHI')) as dehi
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			inv_ids=[]
			dehi = 0
		
		
			for rec in records_avlaga:
				dehi += rec['dehi']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['dehi']>0:
					if employee_id.department_id.account_health_id:
						debit_line = (0, 0, {
						'name': 'Сайн дурын ЭМД-г цалингаас суутгав',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.account_health_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['dehi']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Сайн дурын ЭМД суутгалын данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'Сайн дурын ЭМД-г цалингаас суутгав',
			'date': obj.date_invoice,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': dehi,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'health_move_id': move_id.id,})
		
		return True

	def create_expense_invoice_phone_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.phone_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DECEL')) as decel
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			decel = 0
		
			for rec in records_avlaga:
				decel += rec['decel']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['decel']>0:
					if employee_id.department_id.account_phone_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Лимитээс хэтэрсэн ярианы төлбөрийг цалингаас суутгав	',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.account_phone_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['decel']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Ажлын утасны суутгалын данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'Лимитээс хэтэрсэн ярианы төлбөрийг цалингаас суутгав	',
			'date': obj.date_invoice,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': decel,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'phone_move_id': move_id.id,})
		return True

	def create_expense_invoice_car_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.car_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DECAR')) as decar
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			decar = 0
		
			for rec in records_avlaga:
				decar += rec['decar']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['decar']>0:
					if employee_id.department_id.account_car_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Суутгал-Ажлын торгууль',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.account_car_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['decar']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Ажлын торгуулийн суутгалын данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'Ажилтны авлага-Торгууль',
			'date': obj.date_invoice,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': decar,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'car_move_id': move_id.id,})
		return True

	def create_expense_invoice_advance_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.advance_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DEEARLY')) as deearly
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			deearly = 0
		
			for rec in records_avlaga:
				deearly += rec['deearly']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['deearly']>0:
					if employee_id.department_id.advance_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Цалингийн урьдчилгаа суутгал',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.advance_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['deearly']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Цалингийн урьдчилгаа суутгалыны данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'Цалингийн урьдчилгаа суутгал',
			'date': obj.date_invoice,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': deearly,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'advance_move_id': move_id.id,})
		return True

	def create_expense_invoice_avlaga_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.account_emp_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='OTHSUU')) as othsuu
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			othsuu = 0
		
			for rec in records_avlaga:
				othsuu += rec['othsuu']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['othsuu']>0:
					if employee_id.department_id.account_employee_rec_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Авлагын тооцоог цалингаас суутгав',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.account_employee_rec_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['othsuu']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Цалингийн урьдчилгаа суутгалын данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'Авлагын тооцоог цалингаас суутгав',
			'date': obj.date_invoice,
			'branch_id':False,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': othsuu,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'account_emp_move_id': move_id.id,})
		return True

	def create_expense_invoice_hhoat_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.account_hhoat_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT')) as pit
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN hr_department hd ON hd.id=he.department_id
				LEFT JOIN account_analytic_account aa ON aa.id=hd.analytic_account_id
				WHERE so.id='''+str(obj.id)+''' 
					''')
			records_avlaga = self.env.cr.dictfetchall()
			
			pit = 0
		
			for rec in records_avlaga:
				pit += rec['pit']

				if rec['pit']>0:
					debit_line = (0, 0, {
					'name': obj.year+'-'+month+' '+u'ХХОАТ',
					'date': obj.date_invoice,
					'partner_id': obj.pit_partner_id.id,
					'branch_id':False,
					'account_id': obj.account_pit_payable_id.id,
					'journal_id': obj.journal_id.id,
					# 'analytic_distribution': {str(analytic_id.id): 100.00},
					'debit': 0,
					'credit': rec['pit']
					})
					order_line.append(debit_line)
					debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			credit_line = (0, 0, {
			'name': 'ХХОАТ',
			'date': obj.date_invoice,
			'branch_id':False,
			'partner_id': obj.partner_id.id,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': pit,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'account_hhoat_move_id': move_id.id,})
		return True

	def create_expense_invoice_vacation_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.account_vacation_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				he.id as hr_id,
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='	DEREST')) as pit
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				GROUP BY he.id
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			pit = 0
		
			for rec in records_avlaga:
				pit += rec['pit']
				employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)

				if rec['pit']>0:
					if employee_id.department_id.account_clothes_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'ЭА цалингийн тооцоо хаав',
						'date': obj.date_invoice,
						'partner_id': employee_id.partner_id.id,
						'branch_id':employee_id.department_id.branch_id.id,
						'account_id': employee_id.department_id.advace_id.id,
						'journal_id': obj.journal_id.id,
						'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['pit']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Цалингийн урьдчилгаа  данс тохируулна уу.')%(employee_id.department_id.name))
			credit_line = (0, 0, {
			'name': 'ЭА цалингийн тооцоо хаав',
			'date': obj.date_invoice,
			'branch_id':False,
			'partner_id': obj.partner_id.id,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': pit,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'account_vacation_move_id': move_id.id,})
		return True

	def create_expense_invoice_ndsh_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.ndsh_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI')) as shi 
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN hr_department hd ON hd.id=he.department_id
				LEFT JOIN account_analytic_account aa ON aa.id=hd.analytic_account_id
				WHERE so.id='''+str(obj.id)+''' 
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			shi = 0
		
			for rec in records_avlaga:
				shi += rec['shi']
				debit_line = (0, 0, {
				'name': obj.year+'-'+month+' '+u'НДШ',
				'date': obj.date_invoice,
				'partner_id': obj.ndsh_partner_id.id,
				'branch_id': False,
				'account_id': obj.account_ndsh_id.id,
				'journal_id': obj.journal_id.id,

				# 'analytic_distribution': {str(analytic_id.id): 100.00},
				'debit': 0,
				'credit': shi
				})
				order_line.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			credit_line = (0, 0, {
			'name': 'НДШ',
			'date': obj.date_invoice,
			'branch_id':False,
			'partner_id': obj.partner_id.id,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': shi,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'ndsh_move_id': move_id.id,})
		return True

	def create_expense_invoice_advance_suut_syl(self):
		for obj in self:
			move_pool = self.env['account.move']
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0

			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month

			if obj.account_advance_move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': obj.date_invoice,
					'ref': obj.name,
					'journal_id': obj.journal_id.id,
				}

			self.env.cr.execute('''SELECT 
				sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='URIDSUU')) as uridsuu
				FROM salary_order so
				LEFT JOIN salary_order_line line ON line.order_id=so.id
				LEFT JOIN hr_employee he ON he.id=line.employee_id
				LEFT JOIN res_partner rp ON rp.id=he.partner_id
				WHERE so.id='''+str(obj.id)+''' 
				
					''')
				
			origin=''
			records_avlaga = self.env.cr.dictfetchall()
			
			uridsuu = 0
		
			for rec in records_avlaga:
				if rec['uridsuu']>0:
					uridsuu += rec['uridsuu']
					if obj.account_advance_cost_id:
						debit_line = (0, 0, {
						'name': obj.year+'-'+month+' '+u'Урьдчилгаа цалин',
						'date': obj.date_invoice,
						'partner_id': obj.partner_id.id,
						'branch_id':False,
						'account_id': obj.account_advance_cost_id.id,
						'journal_id': obj.journal_id.id,
						# 'analytic_distribution':employee_id.department_id.analytic_account_id.id,

						# 'analytic_distribution': {str(analytic_id.id): 100.00},
						'debit': 0,
						'credit': rec['uridsuu']
						})
						order_line.append(debit_line)
						debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
					else:
						raise UserError(_('%s хэлтсийн Урьдчилгаа цалингийн данс тохируулна уу.')%(obj.account_advance_cost_id))
			credit_line = (0, 0, {
			'name': 'Урьдчилгаа цалин хаав',
			'date': obj.date_invoice,
			'branch_id':False,
			'partner_id': obj.partner_id.id,
			'account_id': obj.account_payable_id.id,
			'journal_id': obj.journal_id.id,
			'debit': uridsuu,
			'credit': 0,
			})
			order_line.append(credit_line)
			credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'account_advance_move_id': move_id.id,})
		return True


# hewleh zagwar
	def print_salary(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'salary_order'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		left_h1 = workbook.add_format({'bold': 1})
		left_h1.set_font_size(10)
		left_h1.set_font('Times new roman')
		left_h1.set_align('left')

		h2 = workbook.add_format()
		h2.set_font_size(11)
		h2.set_font('Times new roman')
		h2.set_align('left')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({'num_format': '###,###,###.##'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
		center = workbook.add_format({'num_format': '###,###,###.##'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)
		
		center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
		center_bold.set_text_wrap()
		center_bold.set_font('Times new roman')
		center_bold.set_font_size(9)
		center_bold.set_align('right')
		center_bold.set_border(style=1)
		

		fooder = workbook.add_format({'bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')

		sheet = workbook.add_worksheet(u'Цалин')


		month_code=0
		if self.month=='1':
			month_code=1
		if self.month=='2':
			month_code=2
		if self.month=='3':
			month_code=3
		if self.month=='4':
			month_code=4
		if self.month=='5':
			month_code=5
		if self.month=='6':
			month_code=6
		if self.month=='7':
			month_code=7
		if self.month=='8':
			month_code=8 
		if self.month=='9':
			month_code=9
		if self.month=='90':
			month_code=10
		if self.month=='91':
			month_code=11
		if self.month=='92':
			month_code=12 

		sheet.merge_range(0,0,0,3, u'Байгууллагын нэр:'+ ' ' + self.company_id.name, content_right),
		if self.type=='advance':
			sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН УРЬДЧИЛГАА ЦАЛИНГИЙН ХҮСНЭЛТ'%(self.year,month_code), h1)
			# sheet.merge_range(5, 0, 5, 3, u'Хэлтэс: %s / %s'%(self.department_id.parent_id.name,self.department_id.name), left_h1)
		elif self.type=="final":
			sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН СҮҮЛ ЦАЛИНГИЙН ХҮСНЭЛТ'%(self.year,month_code), h1)

		rowx=6
		save_row=7
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Алба нэгж', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Албан тушаал', theader),
		sheet.merge_range(rowx,6,rowx+2,6, u'Даатгуулагчийн төрөл', theader),
		sheet.merge_range(rowx,7,rowx+2,7, u'Регистрийн дугаар', theader),
		sheet.merge_range(rowx,8,rowx+2,8, u'Татвар төлөгчийн дугаар', theader),
		sheet.merge_range(rowx,9,rowx+2,9, u'Цалингийн шатлал', theader),

		so_l_pool = self.env['salary.order.line'].search([('order_id','=',self.id)],limit=1)
		col=10
		for c in so_l_pool.so_line_line:
			sheet.merge_range(rowx,col,rowx+2,col, c.category_id.name, theader),
			col+=1

		n=1
		rowx+=3
		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 6)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 25)
		sheet.set_column('F:F', 25)
		if self.department_id:
			if self.salary_type:
				order_line = self.env['salary.order.line'].search([('order_id','=',self.id),('employee_id.department_id','=',self.department_id.id),('contract_id.salary_type','=',self.salary_type)])
			else:
				order_line = self.env['salary.order.line'].search([('order_id','=',self.id),('employee_id.department_id','=',self.department_id.id)])
		else:
			if self.salary_type:
				order_line = self.env['salary.order.line'].search([('order_id','=',self.id),('contract_id.salary_type','=',self.salary_type)])
			else:
				order_line = self.env['salary.order.line'].search([('order_id','=',self.id)])
		for data in order_line:
			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.department_id.name,content_left)
			sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 6,data.insured_type_id.code,center)
			sheet.write(rowx, 7,data.employee_id.passport_id,content_left)
			sheet.write(rowx, 8,data.employee_id.ttd_number,content_left)
			sheet.write(rowx, 9,data.levelname,content_left)
			colx=10
			for line in data.so_line_line:
				sheet.write(rowx, colx,line.amount,center)
				colx+=1
			rowx+=1
			n+=1

		sheet.merge_range(rowx, 0, rowx, 7, u'НИЙТ', fooder)
		l=4
		while l <= colx-1:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', fooder)
			l+=1
		# 	sheet.write_formula(rowx, 5, "{=SUM(F%d:F%d)}" % (5, rowx), center_bold)

		# rowx += 1

		rowx+=2
		sheet.write(rowx, 2, u'Бэлтгэсэн:', h2)
		sheet.merge_range(rowx, 3, rowx, 5, u'Нягтлан бодогч:......................../%s.%s/'%(self.preparatory.last_name[:1],self.preparatory.name), h2)

		sheet.write(rowx+1, 2, u'Хянасан:', h2)
		sheet.merge_range(rowx+1, 3, rowx+1, 5, u'%s:....................../%s.%s/'%(self.compute_controller.job_id.name,self.compute_controller.last_name[:1],self.compute_controller.name), h2)
		
		sheet.write(rowx+2, 2, u'Баталсан:', h2)
		sheet.merge_range(rowx+2, 3, rowx+2, 5, u'Гүйцэтгэх захирал:.................../%s.%s/'%(self.done_director.last_name[:1],self.done_director.name), h2)
		
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol


# Мэйл тоxиргоо
	def action_salary_email_data(self):
		for obj in self.order_line:

# Цалин           
			email_char_one = 0
			email_char_wage2 = 0
			# email_char_skill_per = 0
			email_char_discipline = 0
# Цаг
			email_char_worked_day = 0
			email_char_worked_hour = 0
			email_char_count_worked_hour = 0
			email_char_over = 0
			email_char_nigth_hour = 0
			email_char_celebrate_work_hour = 0
			email_char_no_work_hr= 0
# Нэмэгдэл
			email_char_pay = 0
			# email_char_kpi_per= 0
			email_char_kpi= 0
			email_char_over_nemegdel= 0
			email_char_celebrate_work_pay = 0
			email_char_nigth = 0
			email_char_no_work_pay= 0
			# email_char_long_per= 0
			email_char_long= 0
			email_char_reward= 0
			email_char_other_pay= 0
			email_char_skill_pay= 0
			email_char_project_pay= 0
			email_char_sales_pay= 0
			email_char_rest_pay= 0
			email_char_dad= 0
			email_char_other = 0
#Суутгал
			email_char_advance = 0
			email_char_deudaan = 0
			email_char_deskill = 0
			email_char_deproject = 0
			email_char_desales= 0
			email_char_derest = 0
			email_char_dedad = 0
			email_char_deother = 0
			email_char_deuridsuu = 0
			email_char_deearly = 0
			email_char_dehi = 0
			email_char_decel = 0
			email_char_decar = 0
			email_char_detor = 0
			email_char_decloth = 0
			email_char_othususu = 0

			email_char_shi = 0
			email_char_pit = 0
			email_char_pitt = 0

			for line in obj.so_line_line:
				if line.category_id.code == 'TW':
					email_char_one = line.amount
				elif line.category_id.code == 'WAGE2':
					email_char_wage2 = line.amount
				# elif line.category_id.code == 'SKILL':
				# 	email_char_skill_per = line.amount
				elif line.category_id.code == 'DISCIPLINE':
					email_char_discipline = line.amount
				elif line.category_id.code == 'SUMD':
					email_char_worked_day = line.amount
				elif line.category_id.code == 'SUMH':
					email_char_worked_hour = line.amount
				elif line.category_id.code == 'WH':
					email_char_count_worked_hour = line.amount
				elif line.category_id.code == 'OVTI':
					email_char_over = line.amount
				elif line.category_id.code == 'NIH':
					email_char_nigth_hour = line.amount
				elif line.category_id.code == 'CELDAY':
					email_char_celebrate_work_hour = line.amount
				elif line.category_id.code == 'NWTI':
					email_char_no_work_hr = line.amount
				elif line.category_id.code == 'PAY':
					email_char_pay = line.amount
				elif line.category_id.code == 'KPIN':
					email_char_kpi = line.amount
				elif line.category_id.code == 'OV':
					email_char_over_nemegdel = line.amount
				elif line.category_id.code == 'CELBPAY':
					email_char_celebrate_work_pay = line.amount
				elif line.category_id.code == 'NIA':
					email_char_nigth = line.amount
				elif line.category_id.code == 'NWPAY':
					email_char_no_work_pay = line.amount
				elif line.category_id.code == 'UDAAN':
					email_char_long = line.amount
				elif line.category_id.code == 'REWARD':
					email_char_reward = line.amount
				elif line.category_id.code == 'OTHERPAY':
					email_char_other_pay = line.amount
				elif line.category_id.code == 'SKILLPAY':
					email_char_skill_pay = line.amount
				elif line.category_id.code == 'PROJECTPAY':
					email_char_project_pay = line.amount
				elif line.category_id.code == 'SALESPAY':
					email_char_sales_pay = line.amount
				elif line.category_id.code == 'SOOA':
					email_char_rest_pay = line.amount
				elif line.category_id.code == 'DAD':
					email_char_dad = line.amount
				elif line.category_id.code == 'OTHER':
					email_char_other = line.amount
				elif line.category_id.code == 'URIDSUU':
					email_char_advance  = line.amount
				elif line.category_id.code == 'DEUDAAN':
					email_char_deudaan  = line.amount
				elif line.category_id.code == 'DESKILL':
					email_char_deskill = line.amount
				elif line.category_id.code == 'DEPROJECT':
					email_char_deproject = line.amount
				elif line.category_id.code == 'DESALES':
					email_char_desales = line.amount
				elif line.category_id.code == 'DEREST':
					email_char_derest = line.amount
				elif line.category_id.code == 'DEDAD':
					email_char_dedad = line.amount
				elif line.category_id.code == 'DEOTHER':
					email_char_deother = line.amount

				elif line.category_id.code == 'DEURIDSUU':
					email_char_deuridsuu = line.amount
				elif line.category_id.code == 'DEEARLY':
					email_char_deearly = line.amount
				elif line.category_id.code == 'DEHI':
					email_char_dehi = line.amount
				elif line.category_id.code == 'DECEL':
					email_char_decel = line.amount
				elif line.category_id.code == 'DECAR':
					email_char_decar = line.amount
				elif line.category_id.code == 'DETOR':
					email_char_detor = line.amount
				elif line.category_id.code == 'DECLOTH':
					email_char_decloth = line.amount
				elif line.category_id.code == 'OTHSUU':
					email_char_othususu = line.amount
				elif line.category_id.code == 'SHI':
					email_char_shi = line.amount
				elif line.category_id.code == 'PIT':
					email_char_pit = line.amount
				elif line.category_id.code == 'PITT':
					email_char_pitt = line.amount

			obj.update({
				'email_char_one' : self.too(email_char_one),
				# 'email_char_skill_per' : self.too(email_char_skill_per),
				'email_char_discipline' : self.too(email_char_discipline),
				'email_char_wage2' : self.too(email_char_wage2),
				'email_char_worked_day' : self.too(email_char_worked_day),
				'email_char_worked_hour' : self.too(email_char_worked_hour),
				'email_char_count_worked_hour' : self.too(email_char_count_worked_hour),
				'email_char_over' : self.too(email_char_over),
				'email_char_nigth_hour' : self.too(email_char_nigth_hour),
				'email_char_celebrate_work_hour' : self.too(email_char_celebrate_work_hour),
				'email_char_no_work_hr': self.too(email_char_no_work_hr),
				'email_char_pay' : self.too(email_char_pay),
				'email_char_kpi': self.too(email_char_kpi),  
				'email_char_over_nemegdel': self.too(email_char_over_nemegdel),
				'email_char_celebrate_work_pay': self.too(email_char_celebrate_work_pay),
				'email_char_nigth' : self.too(email_char_nigth),    
				'email_char_no_work_pay': self.too(email_char_no_work_pay),
				'email_char_long':self.too(email_char_long),
				'email_char_other_pay':self.too(email_char_other_pay),
				'email_char_skill_pay':self.too(email_char_skill_pay),
				'email_char_project_pay':self.too(email_char_project_pay),
				'email_char_sales_pay':self.too(email_char_sales_pay),
				'email_char_rest_pay':self.too(email_char_rest_pay),
				'email_char_dad': self.too(email_char_dad),
				'email_char_other' : self.too(email_char_other),

				'email_char_advance': self.too(email_char_advance),
				'email_char_deudaan': self.too(email_char_deudaan),
				'email_char_deskill': self.too(email_char_deskill),
				'email_char_deproject': self.too(email_char_deproject),
				'email_char_desales': self.too(email_char_desales),
				'email_char_derest': self.too(email_char_derest),
				'email_char_dedad': self.too(email_char_dedad),
				'email_char_deother': self.too(email_char_deother),
				'email_char_deuridsuu': self.too(email_char_deuridsuu),
				'email_char_deearly': self.too(email_char_deearly),
				'email_char_dehi': self.too(email_char_dehi),
				'email_char_decel': self.too(email_char_decel),
				'email_char_decar': self.too(email_char_decar),
				'email_char_detor': self.too(email_char_detor),
				'email_char_decloth': self.too(email_char_decloth),
				'email_char_othususu': self.too(email_char_othususu),
				'email_char_shi': self.too(email_char_shi),
				'email_char_pit': self.too(email_char_pit),
				'email_char_pitt': self.too(email_char_pitt),

				'email_char_amount_tootsson':  self.too(obj.amount_tootsson),
				'email_char_amount_allounce':  self.too(obj.amount_allounce),
				'email_char_amount_deduction':  self.too(obj.amount_deduction),
				'email_char_amount_net':  self.too(obj.amount_net),
				'email_char_basic':  self.too(obj.basic),
				'email_char_day_to_work':  self.too(obj.day_to_work),
				'email_char_hour_to_work':  self.too(obj.hour_to_work),
				'department_id': obj.contract_id.employee_id.department_id.name,
				'job_id': obj.contract_id.employee_id.job_id.name,
			})
		return True
			

# Суутгалын төлөвлөгөө
class DeductionPlan(models.Model):
	_name = 'deductioin.plan'
	_description = "deductioin.plan"

	@api.depends('year','month')
	def _name_write(self):
		for obj in self:
			if obj.month=='90':
				month = '10'
			elif obj.month=='91':
				month = '11'
			elif obj.month=='92':
				month = '12'
			else:
				month = obj.month

			if obj.year and obj.month:
				obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u' сарын цалингийн урьдчилгаа'
			else:
				obj.name=''

	name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
	date = fields.Date('Огноо')
	end_date = fields.Date('Дуусах огноо')
	year = fields.Char('Жил')
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
	line_ids = fields.One2many('deductioin.plan.line','parent_id','Lines')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	data = fields.Binary('Exsel file')
	file_fname = fields.Char(string='File name')

	employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
	department_id = fields.Many2one('hr.department','Хэлтэс')
	job_id = fields.Many2one('hr.job','Албан тушаал')

	# @api.depends('line_ids')
	# def _compute_suutgasan(self):
	#   for obj in self:
	#       for l in obj.line_ids:
	#           obj.suutgasan+=l.done_amount

	@api.depends('zohih','suutgasan')
	def _compute_uldegdel(self):
		for obj in self:
			obj.uldegdel=obj.zohih-obj.suutgasan

	zohih = fields.Float('Суутгавал зохих')
	# suutgasan = fields.Float('Суутгасан', digits=(16, 2), readonly=True, compute=_compute_suutgasan)
	suutgasan = fields.Float('Суутгасан')
	uldegdel = fields.Float('Үлдэгдэл', digits=(16, 2), readonly=True, compute=_compute_uldegdel)

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id
			self.work_location_id = self.employee_id.work_location_id.id

	@api.onchange('data')
	@api.depends('data','file_fname')

	def check_file_type(self):
		if self.data:
			filename,filetype = os.path.splitext(self.file_fname)

	def action_import_line(self):
		deductioin_line_pool =  self.env['deductioin.plan.line']
		if self.line_ids:
			self.line_ids.unlink()
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
		
		rowi = 0
		data = []
		r=0
		for item in range(7,nrows):

			row = sheet.row(item)
			default_code = row[6].value
			cont = row[2].value
			ball = row[3].value
			napt = row[4].value
			weight = row[10].value
			date = row[11].value
			difference = row[12].value
			tn_allounce = row[13].value
			car_number = row[9].value
			employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
			if employee_ids:
				deductioin_line_id = deductioin_line_pool.create({'employee_id':employee_ids.id,
							'parent_id': self.id,
							'department_id': employee_ids.department_id.id,
							'job_id': employee_ids.job_id.id,
							'cont':cont,
							'ball':ball,
							'napt':napt,
							'car_number':car_number,
							'date':date,
							# 'weight':weight,
							'difference':difference,
							'tn_allounce':tn_allounce,
							})
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

	def print_deductioin_plan(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		sheet = workbook.add_worksheet(u'РЭЙС')

		file_name = 'РЭЙС'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')


		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		rowx=0
		save_row=3
		
		sheet.merge_range(rowx+1,0,rowx+1,10, self.name, theader1),
		
		rowx=3
		sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
		sheet.merge_range(rowx,2,rowx+3,2, u'Гэрээ', theader),
		sheet.merge_range(rowx,3,rowx+3,3, u'Бөмбөлөг', theader),
		sheet.merge_range(rowx,4,rowx+3,4, u'НАБТ талбай', theader),
		sheet.merge_range(rowx,5,rowx+3,5, u'Регистр', theader),
		sheet.merge_range(rowx,6,rowx+3,6, u'Ажилтны код', theader),
		sheet.merge_range(rowx,7,rowx+3,7, u'Овог', theader),
		sheet.merge_range(rowx,8,rowx+3,8, u'Нэр', theader),
		sheet.merge_range(rowx,9,rowx+3,9, u'Машины дугаар', theader),
		sheet.merge_range(rowx,10,rowx+3,10, u'Цэвэр жин', theader),    
		sheet.merge_range(rowx,11,rowx+3,11, u'Буулгасан огноо', theader),
		sheet.merge_range(rowx,12,rowx+3,12, u'Зөрүү', theader),    
		sheet.merge_range(rowx,13,rowx+3,13, u'Тн тутмын нэмэгдэл', theader),   
		sheet.merge_range(rowx,14,rowx+3,14, u'Нийт нэмэгдэл', theader),    

		
		
		sheet.freeze_panes(7, 6)
		rowx+=4
		
		sheet.set_column('A:A', 1)
		sheet.set_column('B:B', 4)
		sheet.set_column('F:F', 12)
		sheet.set_column('D:D', 12)
		sheet.set_column('E:E', 12)
		sheet.set_column('H:U', 10)
		n=1
		des=''
		status=''
		for data in self.line_ids:

			sheet.write(rowx, 1, n,contest_left)
			sheet.write(rowx, 2, data.cont,contest_left)
			sheet.write(rowx, 3, data.ball,contest_left)
			sheet.write(rowx, 4, data.napt,contest_left)
			sheet.write(rowx, 5, data.employee_id.passport_id,contest_left)
			sheet.write(rowx, 6, data.employee_id.identification_id,contest_left)
			sheet.write(rowx, 7, data.employee_id.last_name,contest_left)
			sheet.write(rowx, 8, data.employee_id.name,contest_left)
			sheet.write(rowx, 9, data.car_number,contest_left)
			sheet.write(rowx, 10, data.weight,contest_left)
			sheet.write(rowx, 11, str(data.date),contest_left)
			sheet.write(rowx, 12, data.difference,contest_left)
			sheet.write(rowx, 13, data.tn_allounce,contest_left)
			sheet.write(rowx, 14, data.sum_alloune,contest_left)

			rowx+=1
			n+=1

		workbook.close()
		out = base64.encodestring(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}


class DeductioinPlanLine(models.Model):
	_name = 'deductioin.plan.line'
	_description = "deductioin.plan Line"

	# @api.depends('weight')
	# def _compute_difference(self):
	#   for obj in self:
	#       obj.difference=obj.weight*0.99

	# @api.depends('difference','tn_allounce')
	# def _compute_sum_alloune(self):
	#   for obj in self:
	#       obj.sum_alloune=obj.difference*obj.tn_allounce

	parent_id = fields.Many2one('deductioin.plan','Parent', ondelete='cascade')
	date = fields.Date('Огноо')
	amount = fields.Float('Суутгах дүн', digits=(16, 2))
	done_amount = fields.Float('Суутгасан дүн', digits=(16, 2))


class SalaryOrderLine(models.Model):
	_inherit = "salary.order.line"


	
	department_id=  fields.Char('department_id')
	job_id= fields.Char('job_id')
	levelname= fields.Char('Цалингийн шатлал')
	is_advance_check=fields.Boolean('УЦ хаасан эсэх')


	@api.depends('so_line_line','so_line_line.type','so_line_line.amount')
	def _compute_amount_toot(self):
	
		for obj in self:
			amount_toot=0
			pit_amount=0
			bndsh=0
			for line in obj.so_line_line:
				if line.type =='allounce':
					amount_toot+=line.amount

			if obj.insured_type_id.code=='221':
				pit_amount=0
			else:
				pit_amount=amount_toot

			if obj.insured_type_id.code=='20' or obj.insured_type_id.code=='06' or obj.insured_type_id.code=='17' or obj.insured_type_id.code=='21':
				if amount_toot==0:
					bndsh=(660000 * (obj.insured_type_id.o_shi_procent+obj.employee_id.job_id.job_conf.percent)) / 100
				elif amount_toot>0:
					bndsh=(amount_toot * (obj.insured_type_id.o_shi_procent+obj.employee_id.job_id.job_conf.percent)) / 100
			elif obj.insured_type_id.code=='40001':
				bndsh=(amount_toot * obj.insured_type_id.o_shi_procent) / 100
			else:
				bndsh=(amount_toot * (obj.insured_type_id.o_shi_procent+obj.employee_id.job_id.job_conf.percent)) / 100

			obj.amount_tootsson = amount_toot
			obj.pit_amount = pit_amount
			obj.bndsh = bndsh



# email ingeeh talbaruud

 # ------------------------------------------------------------------------------------------   
	email_char_basic = fields.Char('Үндсэн цалин')
	email_char_discipline = fields.Char('Сахилгын шийтгэлийн хувь')
	email_char_wage2 = fields.Char('Үндсэн цалин - Сахилгын шийтгэлийн дараах')
	email_char_skill_per = fields.Char('Ур чадварын нэмэгдэл')
	email_char_one = fields.Char('Нэг цагийн цалин')

	email_char_day_to_work = fields.Char('Сарын ажлын хоног')
	email_char_hour_to_work = fields.Char('Сарын ажлын фонд цаг')
	email_char_worked_day = fields.Char('Ажилласан хоног')
	email_char_worked_hour = fields.Char('Нийт ажилласан цаг')
	email_char_count_worked_hour = fields.Char('Тооцох ажилласан цаг')
	email_char_over = fields.Char('Тооцох илүү цаг')
	email_char_nigth_hour = fields.Char('Шөнө ажилласан цаг')
	email_char_celebrate_work_hour = fields.Char('Баяраар ажилласан цаг')
	email_char_no_work_hr = fields.Char('Сул зогсолт цаг')

	email_char_pay = fields.Char('Бодогдсон үндсэн цалин')
	email_char_kpi = fields.Char('Бодогдсон (ур чадварын нэмэгдэл)')
	email_char_over_nemegdel = fields.Char('Илүү цагийн нэмэгдэл')
	email_char_nigth = fields.Char('Шөнийн цагийн нэмэгдэл')
	email_char_celebrate_work_pay = fields.Char('Баярын нэмэгдэл')
	email_char_no_work_pay = fields.Char('Сул зогсолтын олговор')
	email_char_long = fields.Char('Удаан жилийн урамшуулал')
	email_char_reward = fields.Char('Шагнал урамшуулал')
	email_char_other_pay = fields.Char('Бусад олговор')
	email_char_skill_pay = fields.Char('Гүйцэтгэлийн урамшуулал')
	email_char_project_pay = fields.Char('Төсөлийн урамшуулал')
	email_char_sales_pay = fields.Char('Борлуулалтын урамшуулал')
	email_char_rest_pay = fields.Char('Ээлжийн амралтын цалин')
	email_char_dad = fields.Char('Эцгийн чөлөөний олговор')
	email_char_other = fields.Char('Бусад нэмэгдэл')

	email_char_advance = fields.Char('Урьдчилгаа цалин')
	email_char_deudaan = fields.Char('Олгосон удаан жилийн урамшуулал')
	email_char_deskill = fields.Char('Олгосон гүй.урамшуулал')
	email_char_deproject = fields.Char('Олгосон төсөлийн  урамшуулал')
	email_char_desales = fields.Char('Олгосон борлуулалтын урамшуулал')
	email_char_derest = fields.Char('Олгосон ээлжийн амралтын цалин')
	email_char_dedad = fields.Char('Олгосон эцгийн чөлөөний олговор')
	email_char_deother = fields.Char('Олгосон бусад олговор')
	email_char_deuridsuu = fields.Char('Олгосон бусад урьдчилгаа')
	email_char_deearly = fields.Char('Суутгал-Цалингийн урьдчилгаа')
	email_char_dehi = fields.Char('Суутгал-Сайн дурын ЭМД')    
	email_char_decel = fields.Char('Суутгал-Утасны ярианы төлбөр')
	email_char_decar = fields.Char('Суутгал-Автомашины торгууль')
	email_char_detor = fields.Char('Суутгал-Торгууль')
	email_char_decloth = fields.Char('Суутгал-Ажлын хувцас, гутал')
	email_char_othususu = fields.Char('Бусад суутгал')
	email_char_shi = fields.Char('НДШ')
	email_char_pit = fields.Char('ХАОАТ хөнгөлөлт')
	email_char_pitt = fields.Char('ХАОАТ')

	email_char_amount_allounce = fields.Char('Нийт нэмэгдэл')
	email_char_amount_tootsson = fields.Char('Олговол зохих')
	email_char_amount_deduction = fields.Char('Нийт суутгал')
	email_char_amount_net = fields.Char('Гарт олгох')




	total_day = fields.Float("Ажилласан хоног", digits=(16, 2), store=True, readonly=True, compute='_compute_day',)
	total_hr = fields.Float("Нийт а-сан цаг ", digits=(16, 2), store=True, readonly=True, compute='_compute_hr',)
	wage_two = fields.Float("Ү/ц - С/ш дараах", digits=(16, 2), store=True, readonly=True, compute='_compute_wage_two',)
	one_hour_tarif = fields.Float("Нэг цагийн тариф", digits=(16, 2), store=True, readonly=True, compute='_compute_one_hour_tarif',)
	fond_overtime = fields.Float("Фонд илүү цаг", digits=(16, 2), store=True, readonly=True, compute='_compute_fond_overtime',)
	oz_advance = fields.Float("ОЗ урьдчилгаа", digits=(16, 2), store=True, readonly=True, compute='_compute_oz_advance',)
	tootsoh_hour = fields.Float("Тооцох ажилласан цаг", digits=(16, 2), store=True, readonly=True, compute='_compute_tootsoh_hour',)
	amount_net = fields.Float(string='Гарт олгох', digits=(16, 2), store=True, readonly=True, compute='_compute_amount_net',)
	hour_to_work_all  = fields.Float(string='АЗЦ бүтэн')
	project_salary  = fields.Float(string='ТУ цалин' , digits=(16, 2), store=True, readonly=True, compute='_compute_project_wage')
	kpi_salary  = fields.Float(string='KPI цалин' , digits=(16, 2), store=True, readonly=True, compute='_compute_kpi_wage')

	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_amount_net(self):
		for obj in self:
			# if obj.order_id.type=='advance':
			#     amount_net = 0
			#     for line in obj.so_line_line:
			#         if line.category_id.code in ('NETU','NET'):
			#             amount_net += line.amount
			#     obj.amount_net=obj.amount_tootsson-obj.amount_deduction+avlaga
			#     # obj.update({"amount_net": amount_net,})
			# else:
			avlaga=0
			for line in obj.so_line_line:
				if line.category_id.code=='OR':
					avlaga+=line.amount
			obj.amount_net=obj.amount_tootsson-obj.amount_deduction+avlaga
	# @api.depends('amount_tootsson','amount_deduction')
	# def _compute_amount_net(self):
	
	#     for obj in self:
	#         avlaga=0
	#         for line in obj.so_line_line:
	#             if line.category_id.code=='OR':
	#                 avlaga+=line.amount
	#         obj.amount_net=obj.amount_tootsson-obj.amount_deduction+avlaga

	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_tootsoh_hour(self):
		for obj in self:
			tootsoh_hour = 0
			for line in obj.so_line_line:
				if line.category_id.code =='TWHA':
					tootsoh_hour += line.amount
			obj.update({"tootsoh_hour": tootsoh_hour,})

	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_kpi_wage(self):
		for obj in self:
			kpi_salary = 0
			for line in obj.so_line_line:
				if line.category_id.code =='KPIN':
					kpi_salary += line.amount
			obj.update({"kpi_salary": kpi_salary,})

	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_project_wage(self):
		for obj in self:
			project_salary = 0
			for line in obj.so_line_line:
				if line.category_id.code =='PROJECTPAY':
					project_salary += line.amount
			obj.update({"project_salary": project_salary,})
			
	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_oz_advance(self):
		for obj in self:
			oz_advance = 0
			for line in obj.so_line_line:
				if line.category_id.code =='URID':
					oz_advance += line.amount
			obj.update({"oz_advance": oz_advance,})


	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_fond_overtime(self):
		for obj in self:
			fond_overtime = 0
			for line in obj.so_line_line:
				if line.category_id.code =='OVTIA':
					fond_overtime += line.amount
			obj.update({"fond_overtime": fond_overtime,})

	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_day(self):
		for obj in self:
			total_day = 0
			for line in obj.so_line_line:
				if line.category_id.code in ('SUMD','SUMDU'):
					total_day += line.amount
			obj.update({"total_day": total_day,})
	

	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_hr(self):
		for obj in self:
			total_hr = 0
			for line in obj.so_line_line:
				if line.category_id.code == "SUMH":
					total_hr += line.amount
			obj.update({"total_hr": total_hr,})
	
	
	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_wage_two(self):
		for obj in self:
			wage_two = 0
			for line in obj.so_line_line:
				if line.category_id.code == "WAGE2":
					wage_two += line.amount
			obj.update({"wage_two": wage_two,})


	@api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	def _compute_one_hour_tarif(self):
		for obj in self:
			one_hour_tarif = 0
			for line in obj.so_line_line:
				if line.category_id.code == "TW":
					one_hour_tarif += line.amount
			obj.update({"one_hour_tarif": one_hour_tarif,})

	# send email 
	def _send_mail_to_salary(self,template):
		template = False
		if not template:
			print(template)
			template = self.env.ref('syl_salary.syl_salary_emails')
		assert template._name == 'mail.template'
		email_values = {
			'email_cc': False,
			'email_from': self.order_id.company_id.email,
			'auto_delete': False,
			'recipient_ids': [],
			'partner_ids': [],
			'scheduled_date': False,
		}
		for line in self:
			if line.email_address:
				# raise UserError(_("Cannot send email: user %s has no email address.", user.name))
				email_values['email_to'] = line.email_address
				# TDE FIXME: make this template technical (qweb)
				with self.env.cr.savepoint():
					# force_send = not(self.env.context.get('import_file', False))
					template.send_mail(line.id,  raise_exception=True, email_values=email_values)

	def action_send_mail_erdes_emp(self):
		for obj in self:
			obj._send_mail_to_salary('mw_salary.salary_email')
		return True


class SalaryAccountConf(models.Model):
	_inherit='salary.account.conf'

	account_salary_cost_id=fields.Many2one('account.account','Урьдчилж гарсан зардал-Цалин')
	account_shi_cost_id=fields.Many2one('account.account','Урьдчилж гарсан зардал-НДШ')
	account_advance_cost_id=fields.Many2one('account.account','Урьдчилгаа цалингийн данс')
