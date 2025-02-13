# -*- coding: utf-8 -*-
from odoo import tools
from odoo import models, fields, api

#Судалгааны тайлангууд

class HrReportStatistics(models.Model):
	_name = 'hr.reports.statistics.view'
	_description = "HR Reports - Statistics"
	_auto = False
	_order = 'id'

	id = fields.Many2one('hr.employee', 'Ажилтан', readonly=True)
	emp_id = fields.Many2one('hr.employee', 'Ажилтан', readonly=True)
	work_year = fields.Selection([
		('A', '0-1 жил'),
		('B', '1-3 жил'),
		('C', '3-5 жил'),
		('D', '5-8 жил'),
		('E', '8-10 жил'),
		('F', '10 ба дээш жил')], string='Work Year')
	age = fields.Char('Нас')
	name = fields.Char('Компани')
	percent = fields.Float('Percent')
	start_date = fields.Date('Ажилд орсон  огноо')
	fired_date = fields.Date('Ажилаас гарсан огноо')
	employee_type = fields.Selection([
		('employee', 'Үндсэн ажилтан'),
		('student', 'Цагийн ажилтан'),
		('trainee', 'Туршилтын ажилтан'),
		('contractor', 'Гэрээт'),
		('longleave', 'Урт хугацааны чөлөөтэй'),
		('maternity', 'Хүүхэд асрах чөлөөтэй'),
		('pregnant_leave', 'Жирэмсний амралт'),
		('resigned', 'Ажлаас гарсан'),
		('waiting', 'Хүлээгдэж буй'),
		('blacklist', 'Blacklist'),
		('freelance', 'Бусад'),
		], string='Ажилтны төлөв')
	gender = fields.Selection([
		('male', 'Эрэгтэй'),
		('female', 'Эмэгтэй')], string='Хүйс')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self._cr.execute("""
			CREATE or REPLACE view %s as 
				SELECT hr.id as id, 
					hr.id as emp_id, 
					hr.gender as gender,
					hr.engagement_in_company as start_date,
					hr.work_end_date as fired_date,
					hr.employee_type as employee_type,
					c.name as name,
				CASE WHEN (select extract(year from age(hr.engagement_in_company)))<1 THEN 'A' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<3 THEN 'B' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<5 THEN 'C' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<8 THEN 'D' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<10 THEN 'E'
					ELSE 'F' END AS work_year,
				CASE WHEN hr.birthday IS NULL THEN 'Тодорхойгүй'
					WHEN (select extract(year from age(hr.birthday)))<24 THEN '18-24 нас' 
					WHEN  (select extract(year from age(hr.birthday)))<35 THEN '25-34 нас' 
					WHEN  (select extract(year from age(hr.birthday)))<45 THEN '35-44 нас' 
					WHEN  (select extract(year from age(hr.birthday)))<61 THEN '45-60 нас' 
					ELSE '61 ба дээш' END AS age
				FROM hr_employee hr
				LEFT JOIN hr_department d ON hr.department_id=d.id
				LEFT JOIN res_company c ON d.company_id=c.id
				WHERE (hr.employee_type IS NULL OR hr.employee_type NOT IN ('resigned', 'contract','student'))
				UNION
				SELECT hr.id as  id,
					hr.id as emp_id, 
					hr.gender as gender,
					hr.engagement_in_company as start_date,
					hr.work_end_date as fired_date,
					hr.employee_type as employee_type,
					c.name as name,
				CASE WHEN (select extract(year from age(hr.engagement_in_company)))<1 THEN 'A' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<3 THEN 'B' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<5 THEN 'C' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<8 THEN 'D' 
					WHEN  (select extract(year from age(hr.engagement_in_company)))<10 THEN 'E'
					ELSE 'F' END AS work_year,
				CASE WHEN hr.birthday IS NULL THEN 'Тодорхойгүй'
					WHEN (select extract(year from age(hr.birthday)))<24 THEN '18-24 нас' 
					WHEN  (select extract(year from age(hr.birthday)))<35 THEN '25-34 нас' 
					WHEN  (select extract(year from age(hr.birthday)))<45 THEN '35-44 нас' 
					WHEN  (select extract(year from age(hr.birthday)))<61 THEN '45-60 нас' 
					ELSE '61 ба дээш' END AS age
				FROM hr_employee hr 
				LEFT JOIN hr_department d ON hr.department_id=d.id
				LEFT JOIN res_company c ON d.company_id=c.id
				WHERE (hr.employee_type IS NULL OR hr.employee_type NOT IN ('resigned','contract','student'))
				""" % (self._table))

# class HrReportShiptLeave(models.Model):
#     _name = 'hr.reports.shipt.view'
#     _description = "Hr Report Shipt Leave"
#     _auto = False
#     _order = 'id'

#     id = fields.Many2one('hr.employee', 'Ажилтан', readonly=True)
#     emp_id = fields.Many2one('hr.employee', 'Ажилтан', readonly=True)
#     name = fields.Char('Компани')
#     year = fields.Char('Жил')
#     month = fields.Char('Сар')

#     def init(self):
#         tools.drop_view_if_exists(self.env.cr, self._table)
#         self._cr.execute("""
#             CREATE or REPLACE view %s as 
#                 SELECT 
#                     e.id as id,
#                     e.id as emp_id,
#                     c.name as name,
#                     DATE_PART('year', r.starttime) AS year,
#                     DATE_PART('month', r.starttime) AS month
#                 FROM hr_order_line l
#                 LEFT JOIN hr_order r ON l.order=r.id
#                 LEFT JOIN hr_order_type rt ON rt.id=r.order_type_id
#                 LEFT JOIN hr_employee e ON e.id = l.employee_id
#                 LEFT JOIN hr_department d ON d.id = e.department_id
#                 LEFT JOIN res_company c ON c.id = e.company_id
#                 WHERE (e.employee_type NOT IN ('resigned','longleave','student','contractor')) AND r.state='done' and r.is_many_emp = True """ % (self._table))
        
    
