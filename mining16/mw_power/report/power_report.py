# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api

class power_report_exca(models.Model):
    """ CRM Lead Analysis """
    _name = "power.report.exca"
    _description = "power report exca"
    _auto = False

    parent_id = fields.Many2one('power.hats', string='Бүртгэл', readonly=True)
    object_selection_id = fields.Many2one('power.selection', string='фидер')
    coef = fields.Integer(string='КОЭФ', readonly=True)
    zaalt_e = fields.Float(string='ЗААЛТ ЭХНИЙ', readonly=True)
    zaalt_s = fields.Float(string='ЗААЛТ СҮҮЛИЙН', readonly=True)
    hats_kv = fields.Float(string='ХАЦ кВт.ц', readonly=True)
    tarip = fields.Selection([('udur','өдөр'),('orgil','оргил'),('shunu','шөнө')], string='Тариф', readonly=True)
    date = fields.Date(string='Огноо', readonly=True)
    sum_m3 = fields.Float('Нийт м3 Мэдээгээр', readonly=True)
    sum_m3_sur = fields.Float('Нийт м3 Хэмжилтээр', readonly=True)
    haritsaa1 = fields.Float('м3/кВт', readonly=True)
    haritsaa2 = fields.Float('кВт/м3', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    pp.id,
                    max(pp.parent_id) as parent_id,
                    max(pp.object_selection_id) as object_selection_id,
                    max(pp.coef) as coef,
                    max(pp.zaalt_e) as zaalt_e,
                    max(pp.zaalt_s) as zaalt_s,
                    max(pp.hats_kv) as hats_kv,
                    max(pp.tarip) as tarip,
                    pp.date,
                    SUM(coalesce(sum_m3,0)) as sum_m3, 
                    SUM(coalesce(sum_m3_sur,0)) as sum_m3_sur,
                    case when SUM(coalesce(sum_m3,0))!=0 then pp.hats_kv/SUM(coalesce(sum_m3,0)) else 0 end as haritsaa1,
                    case when pp.hats_kv!=0 then SUM(coalesce(sum_m3,0))/pp.hats_kv end as haritsaa2
                    FROM power_hats_line AS pp
                    left join power_hats ph on ph.id=pp.parent_id
                    left join power_selection ps on ps.id=pp.object_selection_id
                    LEFT JOIN mining_production_report AS mpr  ON (ps.technic_id=mpr.excavator_id and mpr.date=pp.date)
                    where ph.type='technic'
                    group by 
                    pp.id,
                    pp.date
            )
        """ % (self._table)
        )
