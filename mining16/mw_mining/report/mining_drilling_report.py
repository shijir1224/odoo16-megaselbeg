# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class MiningDrillingreport(models.Model):
    """ CRM Lead Analysis """

    _name = "mining.drilling.report"
    _auto = False
    _description = "Mining driling report"
    _rec_name = 'id'

    state = fields.Selection([('draft','Draft'),('done','Done')], 'State', readonly=True)
    date = fields.Date('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    desc = fields.Text('Description', readonly=True)
    drilling_id = fields.Many2one('mining.drilling', 'Drilling', readonly=True)
    drilling_line_id = fields.Many2one('mining.drilling.line', 'Drilling line', readonly=True)
    
    shift = fields.Selection([('day','Day'),('night','Night')], 'Shift', readonly=True)
    user_id = fields.Many2one('res.users', 'Registered', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    
    location_id = fields.Many2one('mining.location', 'Block number', readonly=True)
    # hole_id = fields.Many2one('mining.hole', 'Hole', readonly=True)
    hole = fields.Integer('Hole', required=True)
    tusliin_gun_m = fields.Float(string='Tusliin gun', readonly=True)
    bodit_urumdsun_gun_m = fields.Float('Urumdsun gun', readonly=True)
    urtaashd_tootsoh_gun_m = fields.Float('Batalgaajsan urtaash', readonly=True)
    hatuu_chuluulag_ehelsen_gun_m = fields.Float('Hatuu chuluulag ehelsen gun', readonly=True)
    hatuu_chuluulag_duussan_gun_m = fields.Float('Hatuu chuluulag duussan gun', readonly=True)
    nuurs_ehelsen_gun_m = fields.Float('Nuurs ehelsen gun', readonly=True)
    nuurs_duussan_gun_m = fields.Float('Nuurs duussan gun', readonly=True)
    is_water = fields.Boolean('Is Water', readonly=True)
    is_baarah = fields.Boolean('Baarsan eseh', readonly=True)
    description = fields.Text('Description')
    is_production = fields.Boolean('Is Production', readonly=True)
    
    employee_id = fields.Many2one('hr.employee', 'Drilling man', readonly=True)
    employee_sub_id = fields.Many2one('hr.employee', 'Drilling sub man', readonly=True)
    drill_technic_id = fields.Many2one('technic.equipment', 'Drilling car', readonly=True)
    drill_diameter_mm = fields.Float(string='Urmiin diameter', readonly=True)
    
    def _select(self):
        return """
            SELECT
                mdl.id,
                mdl.id as drilling_line_id,
                md.drill_diameter_mm,
                md.drill_technic_id,
                md.location_id,
                mdl.hole,
                mdl.tusliin_gun_m,
                mdl.bodit_urumdsun_gun_m,
                mdl.urtaashd_tootsoh_gun_m::float,
                mdl.hatuu_chuluulag_ehelsen_gun_m::float,
                mdl.hatuu_chuluulag_duussan_gun_m::float,
                mdl.nuurs_ehelsen_gun_m,
                mdl.nuurs_duussan_gun_m,
                mdl.is_water,
                mdl.is_baarah,
                mdl.description,
                md.employee_id,
                md.employee_sub_id,
                mdl.is_production,
                md.id as drilling_id,
                md.state,
                md.date,
                md.branch_id,
                md.desc,
                md.shift,
                md.user_id,
                md.company_id
        """


    def _from(self):
        return """
            FROM mining_drilling_line AS mdl
        """

    def _join(self):
        return """
            JOIN mining_drilling AS md ON mdl.drilling_id = md.id
        """

    def _where(self):
        return """
            
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where())
        )
