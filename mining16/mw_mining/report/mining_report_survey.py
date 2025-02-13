# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE

class mining_report_survey(models.Model):
    _name = "mining.report.survey"
    _auto = False
    _description = "mining report survey"
    
    mining_surveyor_measurement_id = fields.Many2one('mining.surveyor.measurement','Маркшейдерын Хэмжилт', readonly=True)
    material_id = fields.Many2one('mining.material','Material', readonly=True)
    amount_by_measurement = fields.Float('Measurement result',  readonly=True)
    amount_by_measurement_tn = fields.Float(string='By measurement tn', readonly=True)
    is_production = fields.Boolean('Бүтээлд', readonly=True)
    location_id = fields.Many2one('mining.location','Блок', readonly=True)
    is_reclamation = fields.Boolean('Нөхөн сэргээлт эсэх', readonly=True)
    bcm_coefficient = fields.Float(compute='_sum_all', string='BCM Коэффициент', group_operator="avg", readonly=True)
    

    date = fields.Date('Date', readonly=True)
    branch_id = fields.Many2one('res.branch','Branch', readonly=True)
    state = fields.Selection([('draft', 'Ноорог'),('approved', 'Батлагдсан')], 'State',  default='draft', readonly=True)
    description = fields.Text('Тайлбар', readonly=True)
    excavator_id =fields.Many2one('technic.equipment', 'Exac', readonly=True)
    technic_type =fields.Selection(OWNER_TYPE, string='Technic Type', readonly=True, store=True)
    owner_type =fields.Selection(TECHNIC_TYPE, string='Owner type', readonly=True, store=True)
    user_id = fields.Many2one('res.users','User', readonly=True)
    month_diff = fields.Float(string='Month DIFF')
    total_amount_month = fields.Float(string='Total m3 MONTH')
    
    partner_id = fields.Many2one('res.partner','Technic partner', readonly=True)

    def _union_all(self):
        return ''

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        self._cr.execute("""
                   CREATE or REPLACE view %s as
            SELECT
                l.id,
                l.mining_surveyor_measurement_id,
                l.material_id,
                l.amount_by_measurement,
                l.amount_by_measurement_tn,
                l.is_production,
                l.location_id,
                l.is_reclamation,
                l.bcm_coefficient,
                
                
                p.date,
                p.branch_id,
                p.state,
                p.description,
                p.excavator_id,
                te.technic_type,
                te.owner_type,
                te.partner_id,
                p.user_id,
                p.month_diff,
                p.total_amount_month

    FROM mining_surveyor_measurement_line l
    LEFT JOIN  mining_surveyor_measurement p on (p.id=l.mining_surveyor_measurement_id)
    LEFT JOIN technic_equipment te on (te.id = p.excavator_id)

    """
             % (self._table)
        )
