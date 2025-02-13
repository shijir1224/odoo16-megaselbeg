# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models


class TransferBalanceReportAccountPivot(models.TransientModel):

    _name = 'pivot.report.transfer.balance.account'
    _description = "pivot report transfer balance account"
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='account.transaction.balance.report.new',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )
    branch_id = fields.Many2one(
        'res.branch',
        index=True
    )

    # Data fields, used for report display
#     code = fields.Char()
#     name = fields.Char()
    initial_debit = fields.Float(digits=(16, 2))
    initial_credit = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    final_debit = fields.Float(digits=(16, 2))
    final_credit = fields.Float(digits=(16, 2))

class account_transaction_balance_pivot(models.Model):
    _name = "account.transaction.balance.pivot"
    _description = "Guilgee balance pivot"
    _auto = False
    _order = 'account_id'

    account_id = fields.Many2one('account.account', u'Данс', readonly=True)
    date = fields.Date(u'Огноо', readonly=True, help=u"Огноо")
    date_init = fields.Date(u'Эхний үлдэгдэл огноо', readonly=True)
    partner_id = fields.Many2one('res.partner', u'харилцагч', readonly=True)
    initial_debit = fields.Float(u'Эхний дебит', readonly=True)
    initial_credit = fields.Float(u'Эхний кредит', readonly=True)
    debit = fields.Float(u'Дебит', readonly=True)
    credit = fields.Float(u'Кредит', readonly=True)
    final_debit = fields.Float(u'Эцсийн дебит', readonly=True)
    final_credit = fields.Float(u'Эцсийн кредит', readonly=True)
    move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
    ref = fields.Char(string='Гүйлгээний утга')
#     journal_id = fields.Many2one('account.journal', u'Журнал', readonly=True)
#     net_move = fields.Float(u'Цэвэр гүйлгээ', readonly=True)
    branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True)
#     state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], default='posted', string='Status')
    report_id = fields.Many2one(
        comodel_name='account.transaction.balance.report.new',
        ondelete='cascade',
        index=True
    )
#     analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    code_group_id = fields.Many2one('account.code.type', string="Дансны бүлэг", copy=False)
    tax_id = fields.Many2one('account.tax', string="НӨАТ-ын үзүүлэлтээр")

    def _select(self):
        return """
                select id,
                    date,
                    date_init,
--                    (case when initial_dt>initial_cr  then initial_dt-initial_cr else 0 end) as initial_debit,
--                    (case when initial_dt<initial_cr  then initial_cr-initial_dt else 0 end) as initial_credit,
                    (initial_dt) as initial_debit,
                    (initial_cr) as initial_credit,
                    debit,
                    credit,
                    account_id,
                    tax_id,
                    (case when internal_group in ('asset','expense') then (initial_dt-initial_cr+debit-credit) else 0 end) as final_debit,
                    (case when  internal_group  not in ('asset','expense') then (initial_cr-initial_dt-debit+credit) else 0 end) as final_credit,
                    move_id,
                    report_id,
                    internal_group,
                    branch_id,
                    partner_id,
                    --analytic_account_id,
                    product_id,
                    code_group_id,
                    ref
        """

    def _select2(self):
        return """
            select aml.id*-11 as id, 
--                sum(aml.debit) as initial_dt,
--                sum(aml.credit) as initial_cr,
                (case when a.internal_group in ('asset','expense') then aml.debit-aml.credit else 0 end) as initial_dt,
                (case when  a.internal_group  not in ('asset','expense') then aml.credit-aml.debit else 0 end) as initial_cr,
                0 as debit,
                0 as credit,
                account_id,
                aml.tax_line_id as tax_id,
                null as report_id,
                null::date as date,
                (aml.date + interval '8 hour')::date as date_init,
                move_id,
                a.internal_group,
                aml.branch_id,
                aml.partner_id,
                --aml.analytic_account_id,
                aml.product_id,
                a.code_group_id,
                aml.name as ref
        """

    def _select3(self):
        return """
            select aml.id as id, 
                0 as initial_debit,
                0 as initial_credit,
                debit as debit,
                credit as credit,
                account_id,
                aml.tax_line_id    as tax_id,
                null as report_id,                
                aml.date as date,
                null::date as date_init,
                move_id,
                a.internal_group,
                aml.branch_id,
                aml.partner_id,
                --aml.analytic_account_id,
                aml.product_id,
                a.code_group_id,
                aml.name as ref
        """

    def _from(self):
        return """
            from account_move_line aml 
                left join account_account a on a.id=aml.account_id 
                --group by account_id,aml.tax_line_id,date,move_id,a.internal_group,aml.branch_id,aml.partner_id,aml.name,
                --aml.analytic_account_id,
                --aml.product_id,code_group_id
        """

    def _from2(self):
        return """
            from account_move_line aml  
            left join account_account a on a.id=aml.account_id 
            --group by account_id,aml.tax_line_id,date,move_id,a.internal_group,aml.branch_id,aml.partner_id,aml.name,
            --aml.analytic_account_id,
            --aml.product_id,code_group_id
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'account_transaction_balance_pivot')
        self.env.cr.execute("""CREATE or REPLACE VIEW account_transaction_balance_pivot as (
                %s
                 from (
                (
                %s
                %s
                ) 
                union all
                (                
                %s
                %s
                ) 
                ) as tmp_acc_tran_table
                ) 
            """ % (self._select(), self._select2(), self._from(),
                   self._select3(), self._from2()
                   ))

# select id,
#     date,
#     date_init,
#     initial_debit AS initial_debit,
#     initial_credit AS initial_credit,
#     debit,
#     credit,
#     account_id,
#     tax_id from (
# SELECT id,
#     date,
#     date_init,
#     initial_dt AS initial_debit,
#     initial_cr AS initial_credit,
#     debit,
#     credit,
#     account_id,
#     tax_id,
#         CASE
#             WHEN internal_group::text = ANY (ARRAY['asset'::character varying::text, 'expense'::character varying::text]) THEN initial_dt - initial_cr + debit - credit
#             ELSE 0::numeric
#         END AS final_debit,
#         CASE
#             WHEN internal_group::text <> ALL (ARRAY['asset'::character varying::text, 'expense'::character varying::text]) THEN initial_cr - initial_dt - debit + credit
#             ELSE 0::numeric
#         END AS final_credit,
#     move_id,
#     report_id,
#     internal_group,
#     branch_id,
#     partner_id,
#     product_id,
#     code_group_id,
#     ref,
#     brand_id,
#     produced_qty
#    FROM ( SELECT min(aml.id) AS id,
#                 CASE
#                     WHEN a.internal_group::text = ANY (ARRAY['asset'::character varying::text, 'expense'::character varying::text]) THEN sum(aml.debit - aml.credit)
#                     ELSE 0::numeric
#                 END AS initial_dt,
#                 CASE
#                     WHEN a.internal_group::text <> ALL (ARRAY['asset'::character varying::text, 'expense'::character varying::text]) THEN sum(aml.credit - aml.debit)
#                     ELSE 0::numeric
#                 END AS initial_cr,
#             0 AS debit,
#             0 AS credit,
#             aml.account_id,
#             aml.tax_line_id AS tax_id,
#             NULL::text AS report_id,
#             NULL::date AS date,
#             (aml.date + '08:00:00'::interval)::date AS date_init,
#             aml.move_id,
#             a.internal_group,
#             aml.branch_id,
#             aml.partner_id,
#             aml.product_id,
#             a.code_group_id,
#             aml.name AS ref,
#             aml.brand_id,
#             aml.produced_qty
#            FROM account_move_line aml
#              LEFT JOIN account_account a ON a.id = aml.account_id
#           GROUP BY aml.account_id, aml.tax_line_id, aml.date, aml.move_id, a.internal_group, aml.branch_id, aml.partner_id, aml.name, aml.product_id, a.code_group_id, aml.brand_id, aml.produced_qty
#         UNION ALL
#          SELECT min(aml.id) AS id,
#             0 AS initial_debit,
#             0 AS initial_credit,
#             sum(aml.debit) AS debit,
#             sum(aml.credit) AS credit,
#             aml.account_id,
#             aml.tax_line_id AS tax_id,
#             NULL::text AS report_id,
#             aml.date,
#             NULL::date AS date_init,
#             aml.move_id,
#             a.internal_group,
#             aml.branch_id,
#             aml.partner_id,
#             aml.product_id,
#             a.code_group_id,
#             aml.name AS ref,
#             aml.brand_id,
#             aml.produced_qty
#            FROM account_move_line aml
#              LEFT JOIN account_account a ON a.id = aml.account_id
#           GROUP BY aml.account_id, aml.tax_line_id, aml.date, aml.move_id, a.internal_group, aml.branch_id, aml.partner_id, aml.name, aml.product_id, a.code_group_id, aml.brand_id, aml.produced_qty) tmp_acc_tran_table
#    ) as foo where account_id=38 

