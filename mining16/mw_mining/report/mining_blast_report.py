# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class MiningBlastreport(models.Model):
    """ CRM Lead Analysis """

    _name = "mining.blast.report"
    _auto = False
    _description = "Mining blast report"
    _rec_name = 'id'

    date = fields.Datetime('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Brach', readonly=True)
    blast_id = fields.Many2one('mining.blast', 'Гүйцэтгэл бүртгэл', readonly=True)
    plan_id = fields.Many2one('mining.blast.plan', 'Plan registration', readonly=True)
    blast_volume_actual = fields.Float('Гүйцэтгэл', readonly=True)
    blast_volume_plan = fields.Float('Plan', readonly=True)
    blast_volume_plan_master = fields.Float('Master plan', readonly=True)
    diff_qty = fields.Float('Difference', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
            SELECT *,(blast_volume_plan-blast_volume_actual) as diff_qty FROM (
                SELECT
                    mb.id,
                    0 as plan_id,
                    mb.id as blast_id,
                    mb.date,
                    mb.branch_id,
                    mb.blast_volume as blast_volume_actual,
                    0 as blast_volume_plan,
                    0 as blast_volume_plan_master
                    FROM mining_blast AS mb
                UNION ALL
                SELECT
                    mbp.id,
                    mbp.id as plan_id,
                    0 as blast_id,
                    mbp.date,
                    mbp.branch_id,
                    0 as blast_volume_actual,
                    mbp.blast_volume as blast_volume_plan,
                    0 as blast_volume_plan_master
                    FROM mining_blast_plan AS mbp
                    where mbp.type='forecast'
                UNION ALL
                SELECT
                    mbp.id,
                    mbp.id as plan_id,
                    0 as blast_id,
                    mbp.date,
                    mbp.branch_id,
                    0 as blast_volume_actual,
                    0 as blast_volume_plan,
                    mbp.blast_volume as blast_volume_plan_master
                    FROM mining_blast_plan AS mbp
                    where mbp.type='master'
                    ) as mbr
            )
        """ % (self._table)
        )


    # def _select(self):
    #     return """
    #         SELECT
    #             mbl.id,
    #             mbl.id as blast_line_id,
    #             mb.id as blast_id,
    #             mb.state,
    #             mb.date,
    #             mb.branch_id,
    #             mb.desc
    #     """


    # def _from(self):
    #     return """
    #         FROM mining_blast_line AS mbl
    #     """

    # def _join(self):
    #     return """
    #         JOIN mining_blast AS mb ON mbl.blast_id = mb.id
    #     """

    # def _where(self):
    #     return """

    #     """

    # def init(self):
    #     tools.drop_view_if_exists(self._cr, self._table)

    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW %s AS (
    #             %s
    #             %s
    #             %s
    #             %s
    #         )
    #     """ % (self._table, self._select(), self._from(), self._join(), self._where())
    #     )


class MiningBlastProductReport(models.Model):
    """ CRM Lead Analysis """

    _name = "mining.blast.product.report"
    _auto = False
    _description = "Mining blast product report"
    _rec_name = 'id'

    date = fields.Datetime('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    blast_id = fields.Many2one('mining.blast', 'Гүйцэтгэл бүртгэл', readonly=True)
    master_plan_id = fields.Many2one('mining.blast.plan', 'Master plan registration', readonly=True)
    plan_id = fields.Many2one('mining.blast.plan', 'Plan registration', readonly=True)
    actual_qty = fields.Float('Гүйцэтгэл', readonly=True)
    plan_qty = fields.Float('Plan', readonly=True)
    plan_qty_master = fields.Float('Master plan', readonly=True)
    diff_qty = fields.Float('Difference', readonly=True)

    # diff_m3_qty = fields.Float('Зөрүү м3', readonly=True)

    product_id = fields.Many2one('product.product', 'Product', readonly=True)

    # blast_volume_actual = fields.Float('Уулын цул гүйцэтгэл', readonly=True)
    # blast_volume_plan = fields.Float('Уулын цул төлөвлөгөө', readonly=True)
    # blast_volume_plan_master = fields.Float('Уулын цул мастер Төлөвлөгөө ', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT *,(plan_qty-actual_qty) as diff_qty FROM (
                SELECT
                    mbel.id,
                    null::int as plan_id,
                    null::int as master_plan_id,
                    mbel.blast_id,
                    mb.date,
                    mb.branch_id,
                    mbel.product_id,
                    0 as plan_qty,
                    0 as plan_qty_master,
                    mbel.quantity as actual_qty

                    FROM mining_blast_expense_line AS mbel
                    LEFT JOIN mining_blast AS mb  ON (mbel.blast_id=mb.id)
                UNION ALL
                SELECT
                    mbpl.id,
                    mbp.id as plan_id,
                    null::int as master_plan_id,
                    null::int as blast_id,
                    mbp.date,
                    mbp.branch_id,
                    mbpl.product_id,
                    mbpl.quantity as plan_qty,
                    0 as plan_qty_master,
                    0 as actual_qty


                    FROM mining_blast_plan_line AS mbpl
                    LEFT JOIN mining_blast_plan AS mbp ON (mbpl.blast_id=mbp.id)
                    where mbp.type='forecast'
                UNION ALL
                SELECT
                    mbpl.id,
                    null::int as plan_id,
                    mbp.id as master_plan_id,
                    null::int as blast_id,
                    mbp.date,
                    mbp.branch_id,
                    mbpl.product_id,
                    0 as plan_qty,
                    mbpl.quantity as plan_qty_master,
                    0 as actual_qty



                    FROM mining_blast_plan_line AS mbpl
                    LEFT JOIN mining_blast_plan AS mbp ON (mbpl.blast_id=mbp.id)
                    where mbp.type='master'

                UNION ALL
                SELECT
                    mb.id,
                    null::int as plan_id,
                    null::int as master_plan_id,
                    mb.id as blast_id,
                    mb.date,
                    mb.branch_id,
                    mb.product_id,
                    0 as plan_qty,
                    0 as plan_qty_master,
                    mb.blast_volume as actual_qty

                    FROM mining_blast AS mb
                UNION ALL
                SELECT
                    mbp.id,
                    mbp.id as plan_id,
                    null::int as master_plan_id,
                    null::int as blast_id,
                    mbp.date,
                    mbp.branch_id,
                    mbp.product_id,
                    mbp.blast_volume as plan_qty,
                    0 as plan_qty_master,
                    0 as actual_qty

                    FROM mining_blast_plan AS mbp
                    where mbp.type='forecast'
                UNION ALL
                SELECT
                    mbp.id,
                    null::int as plan_id,
                    mbp.id as master_plan_id,
                    null::int as blast_id,
                    mbp.date,
                    mbp.branch_id,
                    mbp.product_id,
                    0 as plan_qty,
                    mbp.blast_volume  as plan_qty_master,
                    0 as actual_qty
                    FROM mining_blast_plan AS mbp
                    where mbp.type='master'
                    ) as tt_mbpr
            )
        """ % (self._table)
        )

