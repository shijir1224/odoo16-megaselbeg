# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE


class report_mining_technic_analyze(models.Model):
    _name = 'report.mining.technic.analyze'
    _description = 'Technic Fuel Motohour Production'
    _auto = False

    date = fields.Date('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    technic_id = fields.Many2one('technic.equipment', 'Technic', readonly=True)
    owner_type = fields.Selection(OWNER_TYPE, string='Ownership status',readonly=True, store=True)
    technic_type = fields.Selection(TECHNIC_TYPE, string='Technic type', readonly=True, store=True)
    technic_setting_id = fields.Many2one('technic.equipment.setting', string='Technic setting', readonly=True, store=True)
    sum_motohour_time = fields.Float('Мотоцаг гүйсэн', readonly=True)
    sum_diff_odometer_value = fields.Float('Зөрүү гүйсэн мотоцаг', readonly=True)
    sum_work_time = fields.Float('Working time', readonly=True)
    sum_repair_time = fields.Float('Repair time', readonly=True)
    sum_production_time = fields.Float('Productivity time', readonly=True)
    sum_production = fields.Float('Productivity', readonly=True)
    sum_fuel = fields.Float('Авсан Түлш', readonly=True)
    sum_expense = fields.Float('Нийт Зардал', readonly=True)
    first_odometer_value = fields.Float('Мотоцаг Эхэнд', readonly=True, group_operator="min")
    last_odometer_value = fields.Float('Дууссан Мотоцаг', readonly=True, group_operator="max")
    last_km = fields.Float('Дууссан Км', readonly=True, group_operator="max")
    tbbk = fields.Float('ТББК', readonly=True, group_operator="avg")
    is_tbbk = fields.Boolean(string='ТББК-д орох эсэх', readonly=True)
    run_day = fields.Integer('Days worked', readonly=True)
    shift = fields.Selection([('day', 'Өдөр'),('night', 'Шөнө')], 'Shift', readonly=True)
    part = fields.Selection([('a', 'A'),('b', 'B'),('c', 'C'),('d', 'D')], 'Part', readonly=True)
    partner_id = fields.Many2one('res.partner','Technic partner', readonly=True)
    daily_entry_id = fields.Many2one('mining.daily.entry', 'Entry', readonly=True)
    production_line_id = fields.Many2one('mining.production.entry.line', 'Prodcution line', readonly=True)
    motorhour_line_id = fields.Many2one('mining.production.entry.line', 'Motohour line', readonly=True)
    
    plan_production = fields.Float('Plan Productivity', readonly=True)
    plan_repair_hour = fields.Float('Plan Repair hour', readonly=True)
    plan_run_hour = fields.Float(string='Plan Availability hour', readonly=True)
    plan_run_hour_util = fields.Float(string='Plan Utilization hour', readonly=True)
    technic_working_percent = fields.Float(string='Цаг ашиглалт хувь', readonly=True, group_operator='avg')
    haul_distance = fields.Float(string="Талын зай", readonly=True)
    # average_haul_distance = fields.Float(string='Талын зай жигнэсэн дундаж', readonly=True, group_operator='avg')

    _order = 'date desc'

    def _select(self):
        return """
            SELECT
                id,
                production_line_id,
                motorhour_line_id,
                date,
                branch_id,
                technic_id,
                owner_type,
                technic_type,
                technic_setting_id,
                sum_motohour_time,
                sum_diff_odometer_value,
                sum_work_time,
                sum_repair_time,
                sum_production_time,
                sum_production,
                sum_fuel,
                sum_expense,
                first_odometer_value,
                last_odometer_value,
                last_km,
                tbbk,
                is_tbbk,
                run_day,
                shift,
                part,
                partner_id,
                daily_entry_id,
                plan_production,
                plan_repair_hour,
                plan_run_hour,
                plan_run_hour_util,
                plan_hour_prod,
                technic_working_percent,
                haul_distance,
                average_haul_distance
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
                10000000000000000+mmel.id as id,
                null::int as production_line_id,
                mmel.id as motorhour_line_id,
                mde.date,
                mde.branch_id,
                mmel.technic_id,
                te.owner_type,
                te.technic_type,
                te.technic_setting_id,
                mmel.motohour_time as sum_motohour_time,
                mmel.diff_odometer_value as sum_diff_odometer_value,
                mmel.work_time as sum_work_time,
                mmel.repair_time as sum_repair_time,
                mmel.production_time as sum_production_time,
                0 as sum_production,
                0 as sum_fuel,
                0 as sum_expense,
                mmel.first_odometer_value as first_odometer_value,
                mmel.last_odometer_value as last_odometer_value,
                mmel.last_km,
                mmel.tbbk,
                case when (12-mmel.repair_time)!=0 and mmel.production_time!=0 then mmel.production_time*100/(12-mmel.repair_time) else null::float end as technic_working_percent,
                mmel.is_tbbk,
                0 as run_day,
                mde.shift,
                mde.part,
                te.partner_id,
                mde.id as daily_entry_id,
                null::float as plan_production,
                null::float as plan_repair_hour,
                null::float as plan_run_hour,
                null::float as plan_run_hour_util,
                null::float as plan_hour_prod,
                null::float as haul_distance,
                null::float as average_haul_distance
        """
    def _from2(self):
        return """
            FROM mining_motohour_entry_line AS mmel
            LEFT JOIN mining_daily_entry mde ON (mde.id=mmel.motohour_id)
            LEFT JOIN technic_equipment te on (te.id = mmel.technic_id)
        """

    def _group_by2(self):
        return """ """

    def _having2(self):
        return """ """

    def _where2(self):
        return """ """

    def _select3(self):
        return """
            SELECT
                20000000000000000+mpel.id as id,
                mpel.id as production_line_id,
                null::int as motorhour_line_id,
                mde.date,
                mde.branch_id,
                mpel.dump_id as technic_id,
                te.owner_type,
                te.technic_type,
                te.technic_setting_id,
                null::int as sum_motohour_time,
                null::int as sum_diff_odometer_value,
                null::int as sum_work_time,
                null::int as sum_repair_time,
                null::int as sum_production_time,
                mpel.sum_m3 as sum_production,
                0 as sum_fuel,
                0 as sum_expense,
                null::int as first_odometer_value,
                null::int as last_odometer_value,
                null::int as last_km,
                null::int as tbbk,
                null::float as technic_working_percent,
                null as is_tbbk,
                null::int  as run_day,
                mde.shift,
                mde.part,
                te.partner_id,
                mde.id as daily_entry_id,
                null::float as plan_production,
                null::float as plan_repair_hour,
                null::float as plan_run_hour,
                null::float as plan_run_hour_util,
                null::float as plan_hour_prod,
                mpel.haul_distance,
                mde.average_haul_distance
        """
    def _from3(self):
        return """
            FROM mining_production_entry_line AS mpel
            LEFT JOIN mining_daily_entry mde ON (mde.id=mpel.production_id)
            LEFT JOIN technic_equipment te on (te.id = mpel.dump_id)
        """

    def _group_by3(self):
        return """ """

    def _having3(self):
        return """ """

    def _union3(self):
        return """ UNION ALL """

    def _where3(self):
        return """ """
    


    def _select33(self):
        return """
            SELECT
                30000000000000000+mpel.id as id,
                mpel.id as production_line_id,
                null::int as motorhour_line_id,
                mde.date,
                mde.branch_id,
                mpel.excavator_id as technic_id,
                te.owner_type,
                te.technic_type,
                te.technic_setting_id,
                null::int as sum_motohour_time,
                null::int as sum_diff_odometer_value,
                null::int as sum_work_time,
                null::int as sum_repair_time,
                null::int as sum_production_time,
                mpel.sum_m3 as sum_production,
                0 as sum_fuel,
                0 as sum_expense,
                null::int as first_odometer_value,
                null::int as last_odometer_value,
                null::int as last_km,
                null::int as tbbk,
                null::float as technic_working_percent,
                null as is_tbbk,
                null::int  as run_day,
                mde.shift,
                mde.part,
                te.partner_id,
                mde.id as daily_entry_id,
                null::float as plan_production,
                null::float as plan_repair_hour,
                null::float as plan_run_hour,
                null::float as plan_run_hour_util,
                null::float as plan_hour_prod,
                null::float as haul_distance,
                null::float as average_haul_distance
        """
    def _from33(self):
        return """
            FROM mining_production_entry_line AS mpel
            LEFT JOIN mining_daily_entry mde ON (mde.id=mpel.production_id)
            LEFT JOIN technic_equipment te on (te.id = mpel.excavator_id)
        """

    def _group_by33(self):
        return """ """

    def _having33(self):
        return """ """

    def _union33(self):
        return """ UNION ALL """

    def _where33(self):
        return """ """


    def _select4(self):
        return """ """
    def _from4(self):
        return """ """

    def _group_by4(self):
        return """ """

    def _having4(self):
        return """ """

    def _where4(self):
        return """ """
    
    def _union4(self):
        return """ """



    def _select5(self):
        return """
            SELECT
                40000000000000000+mptl.id as id,
                null::int as production_line_id,
                null::int as motorhour_line_id,
                mptl.date,
                mptl.branch_id,
                mptl.technic_id as technic_id,
                te.owner_type,
                te.technic_type,
                te.technic_setting_id,
                null::int as sum_motohour_time,
                null::int as sum_diff_odometer_value,
                null::int as sum_work_time,
                null::int as sum_repair_time,
                null::int as sum_production_time,
                null::int as sum_production,
                0 as sum_fuel,
                0 as sum_expense,
                null::int as first_odometer_value,
                null::int as last_odometer_value,
                null::int as last_km,
                null::int as tbbk,
                null::float as technic_working_percent,
                null as is_tbbk,
                null::int  as run_day,
                null::text as shift,
                null::text as part,
                te.partner_id,
                null as daily_entry_id,
                mptl.production as plan_production,
                mptl.repair_hour as plan_repair_hour,
                mptl.run_hour as plan_run_hour,
                mptl.run_hour_util as plan_run_hour_util,
                mptl.hour_prod as plan_hour_prod,
                null::float as haul_distance,
                null::float as average_haul_distance
         """
    def _from5(self):
        return """
            FROM mining_plan_technic_line AS mptl
            LEFT JOIN technic_equipment te on (te.id = mptl.technic_id)
        """

    def _group_by5(self):
        return """ """

    def _having5(self):
        return """ """

    def _where5(self):
        return """ 
            where mptl.line_type='plan'
        """
    
    def _union5(self):
        return """ UNION ALL """

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

            {12}
                {13}
                {14}
                {15}
                {16}
            {17}
                {18}
                {19}
                {20}
                {21}
             {22}
                {23}
                {24}
                {25}
                {26}

             {27}
                {28}
                {29}
                {30}
                {31}

                ) AS temp_mining_table
                {2}
                {3}

            )

        """.format(
        self._table, self._select(), self._where(), self._group_by(),
        self._select2(), self._from2(), self._where2(), self._group_by2(),
        self._select3(), self._from3(), self._where3(), self._group_by3(),
        '', '', '', '', '',
        # self._union3(), self._select3(), self._from3(), self._where3(), self._group_by3(),
        self._union4(), self._select4(), self._from4(), self._where4(), self._group_by4(),
        self._union33(), self._select33(), self._from33(), self._where33(), self._group_by33(),
        self._union5(), self._select5(), self._from5(), self._where5(), self._group_by5(),
        ))
