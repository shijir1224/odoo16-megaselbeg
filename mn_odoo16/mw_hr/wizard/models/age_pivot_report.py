
# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class age_pivot_report_count(models.Model):
    _name = 'hr.age.pivot.report'
    _description = 'age Pivot report'
    _auto = False

    id = fields.Many2one('hr.employee', 'Ажилтан', readonly=True)
    emp_id = fields.Many2one('hr.employee', 'Ажилтан', readonly=True)

    birthday = fields.Date('Төрсөн өдөр', readonly=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс', readonly=True)
    gender = fields.Selection(
        [('male', 'Эрэгтэй'), ('felame', 'Эмэгтэй')], 'Хүйс')
    age_category = fields.Selection([('age1', '20 хүртэлх нас'),
                                     ('age2', '20-30 нас'),
                                     ('age3', '30-40 нас'),
                                     ('age4', '40-50 нас'),
                                     ('age5', '50-с дээш нас')], 'Насны ангилал', readonly=True)

    age_average = fields.Char('Дундаж нас')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE or REPLACE view  %s as
            SELECT 
                hr.id as id,
                hr.id as emp_id,
                hr.birthday as birthday,
                hr.gender as gender,
                hd.id as department_id,
                hj.id as job_id,
                CASE WHEN (select extract(year from age(hr.birthday))) < 20 THEN 'age1' 
                     WHEN (select extract(year from age(hr.birthday))) < 30 THEN 'age2'
                     WHEN (select extract(year from age(hr.birthday))) < 40 THEN 'age3'
                     WHEN (select extract(year from age(hr.birthday))) < 50 THEN 'age4'
                     ELSE 'age5'   
                END
                as age_category,
                sum(extract(year from age(hr.birthday)))/count(hr.id) as age_average
                FROM hr_employee hr
                LEFT JOIN hr_department hd ON hr.department_id = hd.id
                LEFT JOIN hr_department hdep on (hdep.id = hd.parent_id) 
                LEFT JOIN hr_job hj ON hr.job_id = hj.id 
                WHERE hr.employee_type in ('employee','trainee','contractor')
                GROUP BY hr.id,hr.employee_type,hd.id,hj.id
                """ % (self._table))
