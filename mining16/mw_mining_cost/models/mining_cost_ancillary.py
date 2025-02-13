# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, tools, api

class mining_cost_ancillary_month_exca(models.Model):
    _name = 'mining.cost.ancillary.month.exca'
    _description = 'mining_cost_ancillary_month_exca'
    _auto = False
    
    year_month = fields.Char('Year Month', readonly=True)
    exca_amount = fields.Float('Exca Amount', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW mining_cost_ancillary_month_exca AS (
# select 
# to_char(aml.date, 'YYYY-MM') as year_month,
# max(aml.id) as id,
# sum(aml.debit- aml.credit)/count(distinct dig_rel.cost_id) as exca_amount
# from 
# mining_cost_config_ancillary_digging_technic_rel as dig_rel
# left join account_move_line as aml on (dig_rel.technic_id=aml.technic_id)
# left join account_move as am on (am.id=aml.move_id)
# left join mining_cost_config as mcc on (dig_rel.cost_id=mcc.id)
# where am.state='posted' and  
# aml.account_id in (select account_id from mining_cost_config_account_account_rel as rel 
# left join mining_cost_config mc_conf on(mc_conf.id=rel.cost_id) where mc_conf.type not in ('overhead_cost','indirect_cost'))
# group by 1
# );
#         """)


class mining_cost_config_ancillary_amount_exca(models.Model):
    _name = 'mining.cost.config.ancillary.amount.exca'
    _description = 'mining_cost_config_ancillary_amount_exca'
    _auto = False

    date = fields.Date('Date', readonly=True)
    technic_id = fields.Many2one('technic.equipment','Technic', readonly=True)
    amount_aml = fields.Float('Amount aml', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

#         self._cr.execute("""
#             CREATE OR REPLACE VIEW mining_cost_config_ancillary_amount_exca AS (
# select 
# by_date.date,
# by_date.technic_id,
# by_date.mccl_id as id,
# coalesce(by_month.exca_amount*by_date.percent/100,0) as amount_aml
# from(
# select 
# to_char(generate_series(
#            (mcc.date_start)::date,
#            (mcc.date_end)::date,
#            interval '1 day'
#          )::date, 'YYYY-MM') as year_month,
# generate_series(
#            (mcc.date_start)::date,
#            (mcc.date_end)::date,
#            interval '1 day'
#          )::date as date,
#          mccl.technic_id,
#          min(mcc.date_end),
#          min(mcc.date_start),
#          max(mccl.id) as mccl_id,
#          --array_agg(mccar.account_id) as account_ids,
#          max(mccl."percent"/(DATE_PART('day', mcc.date_end::date) - DATE_PART('day', mcc.date_start::date) +1)) as percent
#          from
#       mining_cost_config as mcc 
# left join mining_cost_config_line as mccl on (mcc.id=mccl.parent_id)
# left join mining_cost_config_ancillary_digging_technic_rel as mccadtr on (mcc.id=mccadtr.cost_id)
# where mcc."type" in ('indirect_cost') and mccadtr.cost_id is not null
# group by 1,2,3
# order by 1
# ) as by_date
# left join mining_cost_ancillary_month_exca as by_month on 
# (by_date.year_month=by_month.year_month)
# );
#         """)



class mining_cost_ancillary_month_dump(models.Model):
    _name = 'mining.cost.ancillary.month.dump'
    _description = 'mining_cost_ancillary_month_dump'
    _auto = False
    
    year_month = fields.Char('Year Month', readonly=True)
    dump_amount = fields.Float('Exca Amount', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW mining_cost_ancillary_month_dump AS (
# select 
# to_char(aml.date, 'YYYY-MM') as year_month,
# max(aml.id) as id,
# sum(aml.debit- aml.credit)/count(distinct dig_rel.cost_id) as dump_amount
# from 
# mining_cost_config_ancillary_tracking_technic_rel as dig_rel
# left join account_move_line as aml on (dig_rel.technic_id=aml.technic_id)
# left join account_move as am on (am.id=aml.move_id)
# left join mining_cost_config as mcc on (dig_rel.cost_id=mcc.id)
# where am.state='posted' and  
# aml.account_id in (select account_id from mining_cost_config_account_account_rel as rel 
# left join mining_cost_config mc_conf on(mc_conf.id=rel.cost_id) where mc_conf.type not in ('overhead_cost','indirect_cost'))
# group by 1
# );
#         """)


class mining_cost_config_ancillary_amount_dump(models.Model):
    _name = 'mining.cost.config.ancillary.amount.dump'
    _description = 'mining_cost_config_ancillary_amount_dump'
    _auto = False

    date = fields.Date('Date', readonly=True)
    technic_id = fields.Many2one('technic.equipment','Technic', readonly=True)
    amount_aml = fields.Float('Amount aml', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
#         self._cr.execute("""
#             CREATE OR REPLACE VIEW mining_cost_config_ancillary_amount_dump AS (
# select 
# by_date.date,
# by_date.technic_id,
# by_date.mccl_id as id,
# coalesce(by_month.dump_amount*by_date.percent/100,0) as amount_aml
# from(
# select 
# to_char(generate_series(
#            (mcc.date_start)::date,
#            (mcc.date_end)::date,
#            interval '1 day'
#          )::date, 'YYYY-MM') as year_month,
# generate_series(
#            (mcc.date_start)::date,
#            (mcc.date_end)::date,
#            interval '1 day'
#          )::date as date,
#          mccl.technic_id,
#          min(mcc.date_end),
#          min(mcc.date_start),
#          max(mccl.id) as mccl_id,
#          --array_agg(mccar.account_id) as account_ids,
#          max(mccl."percent"/(DATE_PART('day', mcc.date_end::date) - DATE_PART('day', mcc.date_start::date) +1)) as percent
#          from
#       mining_cost_config as mcc 
# left join mining_cost_config_line as mccl on (mcc.id=mccl.parent_id2)
# left join mining_cost_config_ancillary_tracking_technic_rel as mccadtr on (mcc.id=mccadtr.cost_id)
# where mcc."type" in ('indirect_cost') and mccadtr.cost_id is not null
# group by 1,2,3
# order by 1
# ) as by_date
# left join mining_cost_ancillary_month_dump as by_month on 
# (by_date.year_month=by_month.year_month)
# );
#         """)
