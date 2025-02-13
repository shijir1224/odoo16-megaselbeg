# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, tools, api

class mining_cost_overhead_month(models.Model):
    _name = 'mining.cost.overhead.month'
    _description = 'Mining cost overhead month'
    _auto = False
    
    year_month = fields.Char('Year Month', readonly=True)
    exca_percent = fields.Float('Exca Percent', readonly=True)
    dump_percent = fields.Float('Dump Percent', readonly=True)
    exca_amount = fields.Float('Exca Amount', readonly=True)
    dump_amount = fields.Float('Dump Amount', readonly=True)
    sum_amount = fields.Float('Sum Amount', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW mining_cost_overhead_month AS (
select 
to_char(aml.date, 'YYYY-MM') as year_month,
mcc.exca_percent,
mcc.dump_percent,
max(aml.id) as id,
sum(aml.debit- aml.credit)/count(distinct mccar.cost_id)*mcc.exca_percent/100 as exca_amount,
sum(aml.debit- aml.credit)/count(distinct mccar.cost_id)*mcc.dump_percent/100 as dump_amount,
(sum(aml.debit- aml.credit)/count(distinct mccar.cost_id)*mcc.exca_percent/100+sum(aml.debit- aml.credit)/count(distinct mccar.cost_id)*mcc.dump_percent/100) as sum_amount 
from 
mining_cost_config_account_account_rel as mccar
left join account_move_line as aml on (mccar.account_id=aml.account_id)
left join account_move as am on (am.id=aml.move_id)
left join mining_cost_config as mcc on (mcc.id=mccar.cost_id and to_char(aml.date, 'YYYY-MM') = to_char(mcc.date_start, 'YYYY-MM'))
where mcc.type='overhead_cost' and am.state='posted'
group by 1,2,3
order by 1
);
        """)


class mining_cost_config_overhead_amount(models.Model):
    _name = 'mining.cost.config.overhead.amount'
    _description = 'Mining cost config overhead amount'
    _auto = False

    date = fields.Date('Date', readonly=True)
    technic_id = fields.Many2one('technic.equipment','Technic', readonly=True)
    amount_aml = fields.Float('Amount aml', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW mining_cost_config_overhead_amount AS (
select 
by_date.mccl_id as id,
by_date.date,
by_date.technic_id,
case when by_date.exca_or_dump='dump' then by_month.dump_amount*by_date.percent/100 else by_month.exca_amount*by_date.percent/100 end as amount_aml
from(
select 
to_char(generate_series(
           (mcc.date_start)::date,
           (mcc.date_end)::date,
           interval '1 day'
         )::date, 'YYYY-MM') as year_month,
generate_series(
           (mcc.date_start)::date,
           (mcc.date_end)::date,
           interval '1 day'
         )::date as date,
         mccl.technic_id,
         mcc.id as mcc_id,
         case when mccl.parent_id is not null then 'exca' else 'dump' end exca_or_dump,
         min(mcc.date_end),
         min(mcc.date_start),
         max(mccl.id) as mccl_id,
         --array_agg(mccar.account_id) as account_ids,
         max(mccl."percent"/(DATE_PART('day', mcc.date_end::date) - DATE_PART('day', mcc.date_start::date) +1)) as percent
         from
      mining_cost_config as mcc 
left join mining_cost_config_line as mccl on (mcc.id=mccl.parent_id or mcc.id=mccl.parent_id2)
where mcc."type" in ('overhead_cost')
group by 1,2,3,4,5
order by 1
) as by_date
left join mining_cost_overhead_month as by_month on 
(by_date.year_month=by_month.year_month)
);
        """)