# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api

class report_hse_injury_entry(models.Model):
    _name = 'report.hse.injury.entry'
    _description = 'Injury entry'
    _auto = False
    
    datetime = fields.Datetime('Огноо', readonly=True)
    name = fields.Char('Дугаар', readonly=True)
    accident_name = fields.Char('Ослын нэр', readonly=True)
    lost_day = fields.Integer('Алдсан ажлын өдөр')
    branch_id = fields.Many2one('res.branch','Салбар', readonly=True)
    department_id = fields.Many2one('hr.department','Хэлтэс', readonly=True)
    branch_manager_id = fields.Many2one('hr.employee','Төслийн менежер', readonly=True)
    dep_manager_id = fields.Many2one('hr.employee','Хэлтсийн менежер', readonly=True)
    general_master_id = fields.Many2one('hr.employee','Ерөнхий мастер', readonly=True)
    master_id = fields.Many2one('hr.employee','Ээлжийн мастер', readonly=True)
    accident_type = fields.Many2one('hse.accident.type', 'Ослын төрөл', readonly=True)
    location_accident = fields.Char('Осол гарсан газар', readonly=True)
    consequence_id = fields.Many2one('hse.consequence', 'Болзошгүй үр дагавар', readonly=True)
    likelihood_id = fields.Many2one('hse.likelihood', 'Дахин тохиолдох магадлал',readonly=True)
    is_lti = fields.Boolean('ХЧТА эсэх?', readonly=True)
    accident_cause_id = fields.Many2one('hse.accident.cause','Ослын шалтгаан', readonly=True)
    factor_id = fields.Many2one('hse.accident.factor', 'Нөлөө', readonly=True)
    
    _order = 'name asc'

   
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            select 
            COALESCE(hial.id, hie.id*-1) as id,
            hie.datetime,
            hie.consequence_id,
            hie.likelihood_id,
            hie.is_lti,
            hie.department_id,
            hie.branch_manager_id,
            hie.dep_manager_id,
            hie.general_master_id,
            hie.master_id,
            hie.accident_name,
            hie.lost_day,
            hie.branch_id,
            hie.accident_type,
            hie.name,
            hie.location_accident,
            hial.accident_cause_id,
            hial.factor_id
            from hse_injury_entry hie
            left join hse_injury_accident_line hial on (hie.id=hial.injury_id)
            where hial.check='t'
            )""" % (self._table))
