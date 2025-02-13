
# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api

class child_pivot_report_count(models.Model):
    _name = 'child.pivot.report'
    _description = 'Child Pivot report'
    _auto = False

    id=fields.Many2one('hr.employee.family.steppe', 'Гэр бүл',readonly=True)
    emp_id=fields.Many2one('hr.employee', 'Ажилтан',readonly=True)

    birthday=fields.Date('Төрсөн өдөр', readonly=True)
    department_id=fields.Many2one('hr.department', 'Хэлтэс',readonly=True)
    gender=fields.Selection([('male','Эрэгтэй'),('felame','Эмэгтэй')],'Хүйс')
    age_category= fields.Selection([('age0','0-7 нас'),
                                      ('age8','8-12 нас'),
                                      ('age13','13-16 нас'),
                                      ('age16','16-с дээш нас')], 'Насны ангилал', readonly=True)
    age_category1= fields.Selection([('age0','0 нас'),
                                      ('age1','1 нас'),
                                      ('age2','2 нас'),
                                      ('age3','3 нас'),
                                      ('age4','4 нас'),
                                      ('age5','5 нас'),
                                      ('age6','6 нас'),
                                      ('age7','7 нас'),
                                      ('age8','8 нас'),
                                      ('age9','9 нас'),
                                      ('age10','10 нас'),
                                      ('age11','11 нас'),
                                      ('age12','12 нас'),
                                      ('age13','13 нас'),
                                      ('age14','14 нас'),
                                      ('age15','15 нас'),
                                      ('age16','16 нас'),
                                      ('age17','17 нас'),
                                      ('age18','18 нас'),
                                      ('age19','18-аас дээш'),], 'Насаар', readonly=True)

    age_average = fields.Char('Дундаж нас')

      

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""
            CREATE or REPLACE view  %s as
            SELECT 
                child.id as id,
                emp1.id as emp_id,
                mem.name as gender,
                hd.id as department_id,
                hj.id as job_id,
                CASE WHEN (select extract(year from age(child.birth_date))) < 7 THEN 'age0' 
                     WHEN (select extract(year from age(child.birth_date))) < 12 THEN 'age8'
                     WHEN (select extract(year from age(child.birth_date))) < 16 THEN 'age13'
                     ELSE 'age16'   
                END
                as age_category,
                CASE WHEN (select extract(year from age(child.birth_date))) = 0 THEN 'age0' 
                     WHEN (select extract(year from age(child.birth_date))) = 1 THEN 'age1'
                     WHEN (select extract(year from age(child.birth_date))) = 2 THEN 'age2'
                     WHEN (select extract(year from age(child.birth_date))) = 3 THEN 'age3'
                     WHEN (select extract(year from age(child.birth_date))) = 4 THEN 'age4' 
                     WHEN (select extract(year from age(child.birth_date))) = 5 THEN 'age5'
                     WHEN (select extract(year from age(child.birth_date))) = 6 THEN 'age6'
                     WHEN (select extract(year from age(child.birth_date))) = 7 THEN 'age7'
                     WHEN (select extract(year from age(child.birth_date))) = 8 THEN 'age8' 
                     WHEN (select extract(year from age(child.birth_date))) = 9 THEN 'age9'
                     WHEN (select extract(year from age(child.birth_date))) = 10 THEN 'age10'
                     WHEN (select extract(year from age(child.birth_date))) = 11 THEN 'age11'
                     WHEN (select extract(year from age(child.birth_date))) = 12 THEN 'age12' 
                     WHEN (select extract(year from age(child.birth_date))) = 13 THEN 'age13'
                     WHEN (select extract(year from age(child.birth_date))) = 14 THEN 'age14'
                     WHEN (select extract(year from age(child.birth_date))) = 15 THEN 'age15'
                     ELSE 'age19'   
                END
                as age_category1,
                sum(extract(year from age(child.birth_date)))/count(emp1.id) as age_average
                FROM hr_employee_family_line child
                LEFT JOIN hr_employee emp1 ON emp1.id=child.employee_id
                LEFT JOIN hr_department hd ON emp1.department_id = hd.id
                LEFT JOIN hr_department hdep on (hdep.id = hd.parent_id) 
                LEFT JOIN hr_employee_family_member mem ON mem.id=child.family_member_id
                LEFT JOIN hr_job hj ON emp1.job_id = hj.id 
                WHERE mem.is_children = True and emp1.employee_type in ('employee','trainee','contractor')
                GROUP BY child.id, emp1.id,emp1.engagement_in_company, hdep.id,hd.id, child.birth_year, hj.id,mem.name
                """% (self._table))
