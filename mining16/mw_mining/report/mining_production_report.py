# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE

class mining_production_report(models.Model):

    _name = "mining.production.report"
    _auto = False
    _description = "Mining production report"
    _rec_name = 'id'

    date = fields.Date('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    production_id = fields.Many2one('mining.production.entry.line', 'Бүтээлийн мөр', readonly=True)
    state = fields.Selection([('draft', 'Өдөр'),('approved', 'Батлагдсан')], 'State', readonly=True)
    shift = fields.Selection([('day', 'Өдөр'),('night', 'Шөнө')], 'Shift', readonly=True)
    part = fields.Char('Part', readonly=True)
    dump_id = fields.Many2one('technic.equipment', 'Dump', readonly=True)
    excavator_id = fields.Many2one('technic.equipment', 'Exacavator', readonly=True)
    # technic_id = fields.Many2one('technic.equipment', 'Technic', readonly=True)
    sum_m3 = fields.Float('Нийт м3 Мэдээгээр', readonly=True)
    res_count = fields.Float('Нийт ресс Мэдээгээр', readonly=True)
    sum_tn = fields.Float('Нийт тн Мэдээгээр', readonly=True)
    sum_m3_sur = fields.Float('Нийт м3 Хэмжилтээр', readonly=True)
    sum_tn_sur = fields.Float('Нийт тн Хэмжилтээр', readonly=True)
    sum_m3_petram = fields.Float('Нийт м3 Петрам', readonly=True)
    sum_tn_petram = fields.Float('Нийт тн Петрам', readonly=True)
    sum_m3_puu = fields.Float('Нийт м3 Пүү', readonly=True)
    sum_tn_puu = fields.Float('Нийт тн Пүү', readonly=True)
    
    sum_m3_avg = fields.Float('Нийт м3 Бүтээл', readonly=True)
    sum_tn_avg = fields.Float('Нийт тн Бүтээл', readonly=True)

    sum_m3_plan_master = fields.Float('Нийт м3 Төлөвлөгөө ЗАХИАЛАГЧ', readonly=True)
    sum_tn_plan_master = fields.Float('Нийт тн Төлөвлөгөө ЗАХИАЛАГЧ', readonly=True)
    sum_m3_plan = fields.Float('Нийт м3 Төлөвлөгөө', readonly=True)
    sum_tn_plan = fields.Float('Нийт тн Төлөвлөгөө', readonly=True)

    sum_m3_plan_exc = fields.Float('Нийт м3 Төлөвлөгөө Экскаватор', readonly=True)
    sum_tn_plan_exc = fields.Float('Нийт тн Төлөвлөгөө Экскаватор', readonly=True)

    material_id = fields.Many2one('mining.material','Material', readonly=True)

    from_pile = fields.Many2one('mining.pile','Овоолгоос', readonly=True)
    from_location = fields.Many2one('mining.location','Блокоос', readonly=True)
    for_pile = fields.Many2one('mining.pile','Овоолгоруу', readonly=True)
    for_location = fields.Many2one('mining.location','Байрлал', readonly=True)

    level = fields.Char('Level', readonly=True)
    is_stone = fields.Boolean('Чулуутай?', readonly=True)
    # is_sulfur = fields.Boolean('Хүхэртэй?', readonly=True)
    coal_layer = fields.Selection([('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10')],'Давхарга', readonly=True)
    master_id = fields.Many2one('res.users','Мастер', readonly=True)
    is_production = fields.Boolean('Бүтээлд', readonly=True)
    
    owner_type = fields.Selection(OWNER_TYPE, string='DUMP Technic owner type',readonly=True, store=True)
    technic_type = fields.Selection(TECHNIC_TYPE, string='DUMP Technic type', readonly=True, store=True)
    partner_id = fields.Many2one('res.partner','DUMP Technic partner', readonly=True)    
    technic_setting_id = fields.Many2one('technic.equipment.setting', string='DUMP Technic setting', readonly=True, store=True)

    owner_type2 = fields.Selection(OWNER_TYPE, string='EXCA Technic owner type',readonly=True, store=True)
    technic_type2 = fields.Selection(TECHNIC_TYPE, string='EXCA Technic type', readonly=True, store=True)
    partner_id2 = fields.Many2one('res.partner','EXCA Technic partner', readonly=True)
    technic_setting_id2 = fields.Many2one('technic.equipment.setting', string='EXCA Technic setting', readonly=True, store=True)

    def _select(self):
        return """
            SELECT
                id,
                production_id,
                dump_id,
                is_production,
                sum_m3,
                sum_tn,
                res_count,
                excavator_id,
                material_id,
                date,
                shift,
                part,
                branch_id,
                from_location,
                for_pile,
                for_location,
                from_pile,
                level,
                master_id,
                is_stone,
                coal_layer,
                state,
                sum_m3_plan,
                sum_tn_plan,
                sum_m3_plan_exc,
                sum_tn_plan_exc,
                sum_m3_sur,
                sum_tn_sur,
                sum_m3_petram,
                sum_tn_petram,
                sum_m3_puu,
                sum_tn_puu,
                sum_m3_avg,
                sum_tn_avg,
                sum_m3_plan_master,
                sum_tn_plan_master,
                owner_type,
                technic_type,
                partner_id,
                technic_setting_id,

                owner_type2,
                technic_type2,
                partner_id2,
                technic_setting_id2,
                
                haul_distance,
                fuel
        """
    
    def _from(self):
        return """ """
    def _group_by(self):
        return """ """

    def _having(self):
        return """ """

    def _where(self):
        return """ """


    def _select2(self):
        return """
            SELECT
                10000000000000000+mpel.id as id,
                mpel.id AS production_id,
                mpel.dump_id as dump_id,
                mpel.is_production,
                mpel.sum_m3 as sum_m3,
                mpel.sum_tn AS sum_tn,
                mpel.res_count AS res_count,
                mpel.excavator_id as excavator_id,
                mpel.material_id,
                mde.date,
                mde.shift,
                mde.part,
                mde.branch_id,
                mpel.from_location,
                mpel.for_pile,
                mpel.for_location,
                mpel.from_pile,
                mpel.level,
                mde.master_id,
                mpel.is_stone,
                mpel.coal_layer,
                mde.state,
                0 as sum_m3_plan,
                0 as sum_tn_plan,
                0 as sum_m3_plan_exc,
                0 as sum_tn_plan_exc,
                0 as sum_m3_sur,
                0 as sum_tn_sur,
                mpel.sum_m3_petram as sum_m3_petram,
                mpel.sum_tn_petram as sum_tn_petram,
                mpel.sum_m3_puu as sum_m3_puu,
                mpel.sum_tn_puu as sum_tn_puu,
                0 as sum_m3_avg,
                0 as sum_tn_avg,
                0 as sum_m3_plan_master,
                0 as sum_tn_plan_master,
                te.owner_type,
                te.technic_type,
                te.partner_id,
                te.technic_setting_id,

                te2.owner_type as owner_type2,
                te2.technic_type as technic_type2,
                te2.partner_id as partner_id2,
                te2.technic_setting_id as technic_setting_id2,
                
                null::int as haul_distance,
                0 as fuel
        """
    def _from2(self):
        return """
            FROM mining_production_entry_line mpel
            LEFT JOIN  mining_daily_entry mde on (mde.id=mpel.production_id)
            LEFT JOIN technic_equipment te on (te.id=mpel.dump_id)
            LEFT JOIN technic_equipment te2 on (te2.id=mpel.excavator_id)
        """

    def _group_by2(self):
        return """
            
        """

    def _having2(self):
        return """ """
    
    def _union2(self):
        return """ UNION ALL """

    def _where2(self):
        return """ """

    def _select22(self):
        return """
            SELECT
                20000000000000000+mpel.id as id,
                mpel.id AS production_id,
                mpel.dump_id as dump_id,
                mpel.is_production,
                mpel.sum_m3 as sum_m3,
                mpel.sum_tn AS sum_tn,
                mpel.res_count AS res_count,
                null as excavator_id,
                mpel.material_id,
                mde.date,
                mde.shift,
                mde.part,
                mde.branch_id,
                mpel.from_location,
                mpel.for_pile,
                mpel.for_location,
                mpel.from_pile,
                mpel.level,
                mde.master_id,
                mpel.is_stone,
                mpel.coal_layer,
                mde.state,
                0 as sum_m3_plan,
                0 as sum_tn_plan,
                0 as sum_m3_plan_exc,
                0 as sum_tn_plan_exc,
                0 as sum_m3_sur,
                0 as sum_tn_sur,
                0 as sum_m3_petram,
                0 as sum_tn_petram,
                0 as sum_m3_puu,
                0 as sum_tn_puu,
                0 as sum_m3_avg,
                0 as sum_tn_avg,
                0 as sum_m3_plan_master,
                0 as sum_tn_plan_master,
                te.owner_type,
                te.technic_type,
                te.partner_id,
                te.technic_setting_id,

                te.owner_type as owner_type2,
                te.technic_type as technic_type2,
                te.partner_id as partner_id2,
                te.technic_setting_id as technic_setting_id2,
                
                null::int as haul_distance,
                0 as fuel
        """
    def _from22(self):
        return """
            FROM mining_production_entry_line mpel
            LEFT JOIN  mining_daily_entry mde on (mde.id=mpel.production_id)
            LEFT JOIN technic_equipment te on (te.id=mpel.dump_id)
        """

    def _group_by22(self):
        return """
            
        """

    def _having22(self):
        return """ """
    
    def _union22(self):
        return """ UNION ALL """

    def _where22(self):
        return """ """

    def _select3(self):
        return """
            SELECT
                       30000000000000000+mpl.id as id,
                       null as production_id,
                       case when te.technic_type='dump' then mpl.technic_id else null end as dump_id,
                       mpl.is_production,
                       0 as sum_m3,
                       0 as sum_tn,
                       0 as res_count,
                       case when te.technic_type='excavator' then mpl.technic_id else null end as excavator_id,
                       mpl.material_id,
                       mpl.date,
                       null as shift,
                       null as part,
                       mpl.branch_id,
                       null as from_location,
                       null as for_pile,
                       null as for_location,
                       null as from_pile,
                       null as level,
                       null as master_id,
                       null as is_stone,
                       null as coal_layer,
                       mpl.state,
                       mpl.production as sum_m3_plan,
                       0 as sum_tn_plan,
                       0 as sum_m3_plan_exc,
                       0 as sum_tn_plan_exc,
                       0 as sum_m3_sur,
                       0 as sum_tn_sur,
                       0 as sum_m3_petram,
                       0 as sum_tn_petram,
                       0 as sum_m3_puu,
                       0 as sum_tn_puu,
                       0 as sum_m3_avg,
                       0 as sum_tn_avg,
                       0 as sum_m3_plan_master,
                       0 as sum_tn_plan_master,

                       te.owner_type,
                       te.technic_type,
                        te.partner_id,
                        te.technic_setting_id,

                        te.owner_type as owner_type2,
                        te.technic_type as technic_type2,
                        te.partner_id as partner_id2,
                        te.technic_setting_id as technic_setting_id2,

                        null::int as haul_distance,
                        0 as fuel
                   
        """
    def _from3(self):
        return """
            from mining_plan_technic_line mpl
            left join technic_equipment te on (te.id=mpl.technic_id)
            where mpl.line_type='plan'
        """

    def _group_by3(self):
        return """
        """

    def _having3(self):
        return """ """

    def _union3(self):
        return """ UNION ALL """

    def _where3(self):
        return """ """
    
    def _select4(self):
        return """
        SELECT
                       40000000000000000+mp.id as id,
                       null as production_id,
                       null as dump_id,
                       true as is_production,
                       0 as sum_m3,
                       0 as sum_tn,
                       0 as res_count,
                       null as excavator_id,
                       mp.material_id,
                       mp.date_start,
                       null as shift,
                       null as part,
                       mp.branch_id,
                       null as from_location,
                       null as for_pile,
                       null as for_location,
                       null as from_pile,
                       null as level,
                       null as master_id,
                       null as is_stone,
                       null as coal_layer,
                       mp.state,
                       0 as sum_m3_plan,
                       0 as sum_tn_plan,
                       0 as sum_m3_plan_exc,
                       0 as sum_tn_plan_exc,
                       0 as sum_m3_sur,
                       0 as sum_tn_sur,
                       0 as sum_m3_petram,
                       0 as sum_tn_petram,
                       0 as sum_m3_puu,
                       0 as sum_tn_puu,
                       0 as sum_m3_avg,
                       0 as sum_tn_avg,
                       mp.total_amount_m3 as sum_m3_plan_master,
                       mp.total_amount_tn as sum_tn_plan_master,
                       null as owner_type,
                       null as technic_type,
                       null as technic_setting_id,
                        null as partner_id,

                        null as owner_type2,
                        null as technic_type2,
                        null as partner_id2,
                        null as technic_setting_id2,

                        null::int as haul_distance,
                        0 as fuel
                   
         """
    def _from4(self):
        return """ 
        from mining_plan_customer mp
        """

    def _group_by4(self):
        return """
            GROUP BY mp.id, mp.date_start, mp.branch_id, mp.state
        """

    def _having4(self):
        return """ """

    def _where4(self):
        return """ """
    
    def _union4(self):
        return """ UNION ALL """
    

    def _select5(self):
        return """
        SELECT
                       50000000000000000+mp.id as id,
                       null as production_id,
                       null as dump_id,
                       true as is_production,
                       0 as sum_m3,
                       0 as sum_tn,
                       0 as res_count,
                       null as excavator_id,
                       mp.material_id,
                       mp.date_start,
                       null as shift,
                       null as part,
                       mp.branch_id,
                       null as from_location,
                       null as for_pile,
                       null as for_location,
                       null as from_pile,
                       null as level,
                       null as master_id,
                       null as is_stone,
                       null as coal_layer,
                       mp.state,
                       0 as sum_m3_plan,
                       0 as sum_tn_plan,
                       0 as sum_m3_plan_exc,
                       0 as sum_tn_plan_exc,
                       0 as sum_m3_sur,
                       0 as sum_tn_sur,
                       0 as sum_m3_petram,
                       0 as sum_tn_petram,
                       0 as sum_m3_puu,
                       0 as sum_tn_puu,
                       0 as sum_m3_avg,
                       0 as sum_tn_avg,
                       mp.total_amount_m3 as sum_m3_plan_master,
                       mp.total_amount_tn as sum_tn_plan_master,
                       null as owner_type,
                       null as technic_type,
                        null as partner_id,
                        null as technic_setting_id,

                        te.owner_type as owner_type2,
                        te.technic_type as technic_type2,
                        te.partner_id as partner_id2,
                        te.technic_setting_id as technic_setting_id2,

                        null::int as haul_distance,
                        0 as fuel
                   
         """
    def _from5(self):
        return """ 
        from mining_plan_customer mp
        """

    def _group_by5(self):
        return """
            GROUP BY mp.id, mp.date_start, mp.branch_id, mp.state
        """

    def _having5(self):
        return """ """

    def _where5(self):
        return """ """
    
    def _union5(self):
        return """ UNION ALL """

    def _select6(self):
        return """
        SELECT
                       60000000000000000+msml.id as id,
                       null as production_id,
                       case when te.technic_type='dump' then msm.excavator_id else null end as dump_id,
                       msml.is_production,
                       0 as sum_m3,
                       0 as sum_tn,
                       0 as res_count,
                       case when te.technic_type='excavator' then msm.excavator_id else null end as excavator_id,
                       msml.material_id,
                       msm.date,
                       null as shift,
                       null as part,
                       msm.branch_id,
                       null as from_location,
                       null as for_pile,
                       null as for_location,
                       null as from_pile,
                       null as level,
                       null as master_id,
                       null as is_stone,
                       null as coal_layer,
                       msm.state,
                        0 as sum_m3_plan,
                       0 as sum_tn_plan,
                       0 as sum_m3_plan_exc,
                        0 as sum_tn_plan_exc,
                        msml.amount_by_measurement as sum_m3_sur,
                        msml.amount_by_measurement_tn as sum_tn_sur,
                        0 as sum_m3_petram,
                        0 as sum_tn_petram,
                        0 as sum_m3_puu,
                        0 as sum_tn_puu,
                        0 as sum_m3_avg,
                        0 as sum_tn_avg,
                        0 as sum_m3_plan_master,
                        0 as sum_tn_plan_master,
                        te.owner_type,
                        te.technic_type,
                        te.partner_id,
                        te.technic_setting_id,

                        null as owner_type2,
                        null as technic_type2,
                        null as partner_id2,
                        null as technic_setting_id2,

                        null::int as haul_distance,
                        0 as fuel
                        
         """
    def _from6(self):
        return """ 
        from
        mining_surveyor_measurement_line msml
        left join mining_surveyor_measurement msm on (msm.id=msml.mining_surveyor_measurement_id)
        left join technic_equipment te on (te.id=msm.excavator_id)
        """

    def _group_by6(self):
        return """
        
        """

    def _having6(self):
        return """ """

    def _where6(self):
        return """ """
    
    def _union6(self):
        return """ UNION ALL """
    
    def _select7(self):
        return """ """
    def _from7(self):
        return """ """

    def _group_by7(self):
        return """ """

    def _having7(self):
        return """ """

    def _where7(self):
        return """ """
    
    def _union7(self):
        return """ """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW {0} AS (
                {1}
                FROM
                (
                {4}
                {5}
                {6}
                {7}
                UNION ALL
                {8}
                {9}
                {10}
                {11}

            
            {17}
                {18}
                {19}
                {20}
                {21}
            {27}
                {28}
                {29}
                {30}
                {31}
            {32}
                {33}
                {34}
                {35}
                {36}

            
                ) AS temp_mining_table_production
                {2}
                {3}

            )
        """.format(
        self._table,     self._select(),  self._where(),  self._group_by(),
        self._select2(), self._from2(),   self._where2(), self._group_by2(),
        self._select3(), self._from3(),   self._where3(), self._group_by3(),
        self._union3(),  self._select3(), self._from3(),  self._where3(),  self._group_by3(),
        self._union4(),  self._select4(), self._from4(),  self._where4(),  self._group_by4(),
        self._union5(),  self._select5(), self._from5(),  self._where5(),  self._group_by5(),
        self._union6(),  self._select6(), self._from6(),  self._where6(),  self._group_by6(),
        self._union7(),  self._select7(), self._from7(),  self._where7(),  self._group_by7(),
        # self._union22(),  self._select22(), self._from22(),  self._where22(),  self._group_by22(),
        ))

    # --{37}
    #             --{38}
    #             --{39}
    #             --{40}
    #             --{41}