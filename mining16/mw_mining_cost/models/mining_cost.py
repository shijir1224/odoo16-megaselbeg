# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api
from odoo.tools import pycompat, OrderedSet
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class mining_cost_report_date(models.Model):
    _name = 'mining.cost.report.date'
    _description = 'Mining cost report date'
    _auto = False
    
    date = fields.Date('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    technic_id = fields.Many2one('technic.equipment', 'Technic', readonly=True)
    technic_setting_id = fields.Many2one('technic.equipment.setting', 'Technic Config', readonly=True)
    owner_type = fields.Selection(OWNER_TYPE, 'Owner Type',readonly=True)
    technic_type = fields.Char('Technic Type', readonly=True)
    sum_m3_sur = fields.Float('Total BCM (Surveyor measurement)', readonly=True)
    sum_tn_sur = fields.Float('Surveyor tn', readonly=True)
    hauling_distance = fields.Float('Hauling distance', group_operator='avg')
    
    fuel_amount = fields.Float('Fuel cost', readonly=True)
    fuel_amount_cost_unit = fields.Float('Fuel BCM Cost', readonly=True, group_operator='avg')
    
    selbeg_amount = fields.Float('Parts cost', readonly=True)
    selbeg_amount_cost_unit = fields.Float('Part BCM Cost', readonly=True, group_operator='avg')
    
    tire_amount = fields.Float('Tire cost', readonly=True)
    tire_amount_cost_unit = fields.Float('Tire BCM Cost', readonly=True, group_operator='avg')
    
    oil_amount = fields.Float('Oil cost', readonly=True)
    oil_amount_cost_unit = fields.Float('Oil BCM Cost', readonly=True, group_operator='avg')
    
    dep_amount = fields.Float('Depreciation cost', readonly=True)
    dep_amount_cost_unit = fields.Float('Depreciation BCM Cost', readonly=True, group_operator='avg')
    
    insurance_amount = fields.Float('Inrsurance', readonly=True)
    insurance_amount_cost_unit = fields.Float('Inrsurance BCM Cost', readonly=True, group_operator='avg')
    
    contract_amount = fields.Float('Contract service cost', readonly=True)
    contract_amount_cost_unit = fields.Float('Contract service BCM Cost', readonly=True, group_operator='avg')
    
    tax_amount = fields.Float('Tax', readonly=True)
    tax_amount_cost_unit = fields.Float('Tax BCM Cost', readonly=True, group_operator='avg')
    
    sum_amount = fields.Float('Total cost', readonly=True)
    cost_unit = fields.Float('BCM Cost', readonly=True, group_operator='avg')
    
    indirect_cost_amount = fields.Float('Indirect cost', readonly=True)
    indirect_cost_amount_cost_unit = fields.Float('Indirect BCM Cost', readonly=True, group_operator='avg')
    
    overhead_cost_amount = fields.Float('Overhead cost', readonly=True)
    overhead_cost_amount_cost_unit = fields.Float('Overhead BCM Cost', readonly=True, group_operator='avg')
    
    ancillary_cost_amount = fields.Float('Ancillary Cost', readonly=True)
    ancillary_cost_amount_cost_unit = fields.Float('Ancillary BCM Cost', readonly=True, group_operator='avg')
    
    salary_cost_amount = fields.Float('Salary cost', readonly=True)
    salary_cost_amount_cost_unit = fields.Float('Salary BCM Cost', readonly=True, group_operator='avg')
    
    accomodation_cost_amount = fields.Float('Accomodation cost', readonly=True)
    accomodation_cost_amount_cost_unit = fields.Float('Accomodation BCM Cost', readonly=True, group_operator='avg')
    
    electrical_amount = fields.Float('Electrical cost', readonly=True)
    electrical_amount_cost_unit = fields.Float('Electrical BCM Cost', readonly=True, group_operator='avg')

    _order = 'date desc'

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW %s AS (
    #             SELECT 
    #             max(id) as id,
    #             date,
    #             branch_id,
    #             technic_id,
    #             technic_setting_id,
    #             owner_type,
    #             technic_type,
    #             sum(fuel_amount) as fuel_amount,
    #             sum(selbeg_amount) as selbeg_amount,
    #             sum(electrical_amount) as electrical_amount,
    #             sum(tire_amount) as tire_amount,
    #             sum(oil_amount) as oil_amount,
    #             sum(sum_m3_sur) as sum_m3_sur,
    #             sum(sum_tn_sur) as sum_tn_sur,
    #             sum(dep_amount) as dep_amount,
    #             sum(insurance_amount) as insurance_amount,
    #             sum(contract_amount) as contract_amount,
    #             sum(tax_amount) as tax_amount,
    #             sum(indirect_cost) as indirect_cost_amount,
    #             sum(overhead_cost) as overhead_cost_amount,
    #             sum(ancillary_cost) as ancillary_cost_amount,
    #             sum(salary_amount) as salary_cost_amount,
    #             sum(accomodation_amount) as accomodation_cost_amount,
    #             max(hauling_distance) as hauling_distance,
    #             sum(coalesce(fuel_amount,0)
    #             +coalesce(selbeg_amount,0)+coalesce(electrical_amount,0)+coalesce(tire_amount,0)+coalesce(oil_amount,0)+coalesce(dep_amount,0)
    #             +coalesce(insurance_amount,0)+coalesce(contract_amount,0)+coalesce(tax_amount,0)+coalesce(indirect_cost,0)+
    #             coalesce(overhead_cost,0)+coalesce(salary_amount,0)+coalesce(accomodation_amount,0)) as sum_amount,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(fuel_amount,0)+coalesce(selbeg_amount,0)+coalesce(electrical_amount,0)+coalesce(tire_amount,0)+coalesce(oil_amount,0)
    #     +coalesce(dep_amount,0)+coalesce(insurance_amount,0)+coalesce(contract_amount,0)
    #     +coalesce(tax_amount,0)+coalesce(indirect_cost,0)+coalesce(overhead_cost,0)
    #     +coalesce(salary_amount,0)+coalesce(accomodation_amount,0))/sum(sum_m3_sur) ELSE 0 END as cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(fuel_amount,0))/sum(sum_m3_sur) ELSE 0 END as fuel_amount_cost_unit, 
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(selbeg_amount,0))/sum(sum_m3_sur) ELSE 0 END as selbeg_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(electrical_amount,0))/sum(sum_m3_sur) ELSE 0 END as electrical_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(tire_amount,0))/sum(sum_m3_sur) ELSE 0 END as tire_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(oil_amount,0))/sum(sum_m3_sur) ELSE 0 END as oil_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(dep_amount,0))/sum(sum_m3_sur) ELSE 0 END as dep_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(insurance_amount,0))/sum(sum_m3_sur) ELSE 0 END as insurance_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(contract_amount,0))/sum(sum_m3_sur) ELSE 0 END as contract_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(indirect_cost,0))/sum(sum_m3_sur) ELSE 0 END as indirect_cost_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(overhead_cost,0))/sum(sum_m3_sur) ELSE 0 END as overhead_cost_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(ancillary_cost,0))/sum(sum_m3_sur) ELSE 0 END as ancillary_cost_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(tax_amount,0))/sum(sum_m3_sur) ELSE 0 END as tax_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(salary_amount,0))/sum(sum_m3_sur) ELSE 0 END as salary_cost_amount_cost_unit,
    #             CASE WHEN sum(sum_m3_sur)>0 THEN sum(coalesce(accomodation_amount,0))/sum(sum_m3_sur) ELSE 0 END as accomodation_cost_amount_cost_unit
                
    #             FROM (
    #                SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              sum(aml.debit-aml.credit) as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='fuel'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #             SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              sum(aml.debit-aml.credit) as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='selbeg'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #             SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              sum(aml.debit-aml.credit) as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='electrical'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #             SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              sum(aml.debit-aml.credit) as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='tire'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #              SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              sum(aml.debit-aml.credit) as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='insurance'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #              SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              sum(aml.debit-aml.credit) as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='oil'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #              SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              sum(aml.debit-aml.credit) as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #              null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='tax'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #              SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              null::int as dep_amount,
    #              null::int as insurance_amount,
    #              sum(aml.debit-aml.credit) as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #              null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_move_line AS aml ON (aml.technic_id = te.id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.technic_id is not null and am.state='posted'
    #                and conf.type='contract'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #             SELECT
    #              min(aml.id) as id,
    #              te.id as technic_id,
    #              te.technic_setting_id,
    #              te.branch_id,
    #              te.owner_type,
    #              te.technic_type,
    #              aml.date,
    #              null::int as fuel_amount,
    #              null::int as selbeg_amount,
    #              null::int as electrical_amount,
    #              null::int as tire_amount,
    #              null::int as oil_amount,
    #              sum(aml.debit-aml.credit) as dep_amount,
    #              null::int as insurance_amount,
    #              null::int as contract_amount,
    #              null::int as tax_amount,
    #              null::int as sum_m3_sur,
    #              null::int as sum_tn_sur,
    #              null::int as indirect_cost,
    #              null::int as overhead_cost,
    #              null::int as ancillary_cost,
    #              null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                 FROM technic_equipment AS te
    #                 LEFT JOIN account_asset_asset AS aaa ON (aaa.id = te.asset_id)
    #                 LEFT JOIN account_move_line AS aml ON (aaa.id = aml.asset_id)
    #                 LEFT JOIN account_move AS am ON (aml.move_id = am.id)
                   
    #                 LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #                 LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #                WHERE aml.asset_id  is not null and am.state='posted'
    #                and conf.type='depreciation'
    #                group by 2,3,4,5,6,7
    #             UNION ALL
    #              SELECT 
    #                  min(t_msml.id*-333) as id,
    #                  t_msml.excavator_id as technic_id,
    #                  te.technic_setting_id,
    #                  te.branch_id,
    #                  te.owner_type,
    #                  te.technic_type,
    #                  t_msml.date,
    #                  null::int as fuel_amount,
    #                  null::int as selbeg_amount,
    #                  null::int as electrical_amount,
    #                  null::int as tire_amount,
    #                  null::int as oil_amount,
    #                  null::int as dep_amount,
    #                  null::int as insurance_amount,
    #                  null::int as contract_amount,
    #                  null::int as tax_amount,
    #                  sum(msml.amount_by_measurement) as sum_m3_sur,
    #                  sum(msml.amount_by_measurement_tn) as sum_tn_sur,
    #                  null::int as indirect_cost,
    #                  null::int as overhead_cost,
    #                  null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                     from 
    #                     (SELECT 
    #                     msm1.date,
    #                     msml1.id,
    #                     msm1.excavator_id,
    #                     msm1.branch_id,
    #                     msm1.id as parent_id
    #                     from mining_surveyor_measurement_line msml1 
    #                     left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #                     where msm1.excavator_id is not null
    #                     order by date
    #                     ) as t_msml
    #                     left join  mining_surveyor_measurement_line msml on (msml.id=t_msml.id)
    #                     left join  mining_surveyor_measurement msm on (msm.id=msml.mining_surveyor_measurement_id)
    #                     left join technic_equipment te on (t_msml.excavator_id=te.id)
    #                 group by 2,3,4,5,6,7

    #             UNION ALL
    #               SELECT
    #                  min(te.id*-333) as id,
    #                  te.id as technic_id,
    #                  te.technic_setting_id,
    #                  te.branch_id,
    #                  te.owner_type,
    #                  te.technic_type,
    #                  indirect_conf.date,
    #                  null::int as fuel_amount,
    #                  null::int as selbeg_amount,
    #                  null::int as electrical_amount,
    #                  null::int as tire_amount,
    #                  null::int as oil_amount,
    #                  null::int as dep_amount,
    #                  null::int as insurance_amount,
    #                  null::int as contract_amount,
    #                  null::int as tax_amount,
    #                  null::int as sum_m3_sur,
    #                  null::int as sum_tn_sur,
    #                  sum(indirect_conf.amount_aml) AS indirect_cost,
    #                  null::int as overhead_cost,
    #                  null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                  FROM mining_cost_config_indirect_amount indirect_conf 
    #                  LEFT JOIN technic_equipment te ON (indirect_conf.technic_id = te.id)
                  
    #               GROUP BY 2,3,4,5,6,7
    #             UNION ALL
    #               SELECT
    #                  min(te.id*-777) as id,
    #                  te.id as technic_id,
    #                  te.technic_setting_id,
    #                  te.branch_id,
    #                  te.owner_type,
    #                  te.technic_type,
    #                  overhead_conf.date,
    #                  null::int as fuel_amount,
    #                  null::int as selbeg_amount,
    #                  null::int as electrical_amount,
    #                  null::int as tire_amount,
    #                  null::int as oil_amount,
    #                  null::int as dep_amount,
    #                  null::int as insurance_amount,
    #                  null::int as contract_amount,
    #                  null::int as tax_amount,
    #                  null::int as sum_m3_sur,
    #                  null::int as sum_tn_sur,
    #                  null::int as indirect_cost,
    #                  sum(overhead_conf.amount_aml)  as overhead_cost,
    #                  null::int as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                  FROM mining_cost_config_overhead_amount overhead_conf 
    #                  LEFT JOIN technic_equipment te ON (overhead_conf.technic_id = te.id)
                  
    #               GROUP BY 2,3,4,5,6,7

    #             UNION ALL
    #               SELECT
    #                  min(te.id*-999) as id,
    #                  te.id as technic_id,
    #                  te.technic_setting_id,
    #                  te.branch_id,
    #                  te.owner_type,
    #                  te.technic_type,
    #                  ancillary_conf.date,
    #                  null::int as fuel_amount,
    #                  null::int as selbeg_amount,
    #                  null::int as electrical_amount,
    #                  null::int as tire_amount,
    #                  null::int as oil_amount,
    #                  null::int as dep_amount,
    #                  null::int as insurance_amount,
    #                  null::int as contract_amount,
    #                  null::int as tax_amount,
    #                  null::int as sum_m3_sur,
    #                  null::int as sum_tn_sur,
    #                  null::int as indirect_cost,
    #                  0  as overhead_cost,
    #                 sum(ancillary_conf.amount_aml) as ancillary_cost,
    #                  null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                  FROM mining_cost_config_ancillary_amount_exca ancillary_conf 
    #                  LEFT JOIN technic_equipment te ON (ancillary_conf.technic_id = te.id)
    #               GROUP BY 2,3,4,5,6,7

    #               UNION ALL
    #               SELECT
    #                  min(te.id*-999) as id,
    #                  te.id as technic_id,
    #                  te.technic_setting_id,
    #                  te.branch_id,
    #                  te.owner_type,
    #                  te.technic_type,
    #                  ancillary_conf.date,
    #                  null::int as fuel_amount,
    #                  null::int as selbeg_amount,
    #                  null::int as electrical_amount,
    #                  null::int as tire_amount,
    #                  null::int as oil_amount,
    #                  null::int as dep_amount,
    #                  null::int as insurance_amount,
    #                  null::int as contract_amount,
    #                  null::int as tax_amount,
    #                  null::int as sum_m3_sur,
    #                  null::int as sum_tn_sur,
    #                  null::int as indirect_cost,
    #                  null::int as overhead_cost,
    #                 sum(ancillary_conf.amount_aml) as ancillary_cost,
    #                 null::int as hauling_distance,
    #                 null::int as salary_amount,
    #                 null::int as accomodation_amount
    #                  FROM mining_cost_config_ancillary_amount_dump ancillary_conf 
    #                  LEFT JOIN technic_equipment te ON (ancillary_conf.technic_id = te.id)
    #               GROUP BY 2,3,4,5,6,7
    #               UNION ALL
    #              SELECT 
    #             min(aml.id*t_msml.excavator_id*-1) as id,
    #             t_msml.excavator_id as technic_id,
    #             te.technic_setting_id,
    #             te.branch_id,
    #             te.owner_type,
    #             te.technic_type,
    #             aml.date,
    #             null::int as fuel_amount,
    #             null::int as selbeg_amount,
    #             null::int as electrical_amount,
    #             null::int as tire_amount,
    #             null::int as oil_amount,
    #             null::int as dep_amount,
    #             null::int as insurance_amount,
    #             null::int as contract_amount,
    #             null::int as tax_amount,
    #             null::int as sum_m3_sur,
    #             null::int as sum_tn_sur,
    #             null::int as indirect_cost,
    #             null::int as overhead_cost,
    #             null::int as ancillary_cost,
    #             null::int as hauling_distance,
    #             sum(aml.debit-aml.credit)/count(distinct t_msml2.excavator_id)/count(distinct t_msml2.excavator_id) as salary_amount,
    #             null::int as accomodation_amount
    #             FROM
    #             account_move_line AS aml 
    #             LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #             LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #             LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='excavator'
    #             order by date
    #             ) as t_msml on (t_msml.date=aml.date)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='excavator'
    #             order by date
    #             ) as t_msml2 on (t_msml2.date=aml.date)
    #             left join technic_equipment te on (t_msml.excavator_id=te.id)
    #         WHERE am.state='posted'
    #         and conf.type='salary_digging'
    #         and t_msml2.excavator_id is not null and te.technic_type='excavator'
    #         group by 2,3,4,5,6,7
    #             UNION ALL
    #             SELECT 
    #             min(aml.id*t_msml.excavator_id) as id,
    #             t_msml.excavator_id as technic_id,
    #             te.technic_setting_id,
    #             te.branch_id,
    #             te.owner_type,
    #             te.technic_type,
    #             aml.date,
    #             null::int as fuel_amount,
    #             null::int as selbeg_amount,
    #             null::int as electrical_amount,
    #             null::int as tire_amount,
    #             null::int as oil_amount,
    #             null::int as dep_amount,
    #             null::int as insurance_amount,
    #             null::int as contract_amount,
    #             null::int as tax_amount,
    #             null::int as sum_m3_sur,
    #             null::int as sum_tn_sur,
    #             null::int as indirect_cost,
    #             null::int as overhead_cost,
    #             null::int as ancillary_cost,
    #             null::int as hauling_distance,
    #             sum(aml.debit-aml.credit)/count(distinct t_msml2.excavator_id)/count(distinct t_msml2.excavator_id) as salary_amount,
    #             null::int as accomodation_amount
    #             FROM
    #             account_move_line AS aml 
    #             LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #             LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #             LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='dump'
    #             order by date
    #             ) as t_msml on (t_msml.date=aml.date)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='dump'
    #             order by date
    #             ) as t_msml2 on (t_msml2.date=aml.date)
    #             left join technic_equipment te on (t_msml.excavator_id=te.id)
    #         WHERE am.state='posted'
    #         and conf.type='salary_tracking'
    #         and t_msml2.excavator_id is not null and te.technic_type='dump'
    #         group by 2,3,4,5,6,7
    #              UNION ALL
    #              SELECT 
    #             min(aml.id*t_msml.excavator_id*-1) as id,
    #             t_msml.excavator_id as technic_id,
    #             te.technic_setting_id,
    #             te.branch_id,
    #             te.owner_type,
    #             te.technic_type,
    #             aml.date,
    #             null::int as fuel_amount,
    #             null::int as selbeg_amount,
    #             null::int as electrical_amount,
    #             null::int as tire_amount,
    #             null::int as oil_amount,
    #             null::int as dep_amount,
    #             null::int as insurance_amount,
    #             null::int as contract_amount,
    #             null::int as tax_amount,
    #             null::int as sum_m3_sur,
    #             null::int as sum_tn_sur,
    #             null::int as indirect_cost,
    #             null::int as overhead_cost,
    #             null::int as ancillary_cost,
    #             null::int as hauling_distance,
    #             null::int as salary_amount,
    #             sum(aml.debit-aml.credit)/count(distinct t_msml2.excavator_id)/count(distinct t_msml2.excavator_id) as accomodation_amount
    #             FROM
    #             account_move_line AS aml 
    #             LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #             LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #             LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='excavator'
    #             order by date
    #             ) as t_msml on (t_msml.date=aml.date)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='excavator'
    #             order by date
    #             ) as t_msml2 on (t_msml2.date=aml.date)
    #             left join technic_equipment te on (t_msml.excavator_id=te.id)
    #         WHERE am.state='posted'
    #         and conf.type='accomodation_digging'
    #         and t_msml2.excavator_id is not null and te.technic_type='excavator'
    #         group by 2,3,4,5,6,7
    #             UNION ALL
    #             SELECT 
    #             min(aml.id*t_msml.excavator_id) as id,
    #             t_msml.excavator_id as technic_id,
    #             te.technic_setting_id,
    #             te.branch_id,
    #             te.owner_type,
    #             te.technic_type,
    #             aml.date,
    #             null::int as fuel_amount,
    #             null::int as selbeg_amount,
    #             null::int as electrical_amount,
    #             null::int as tire_amount,
    #             null::int as oil_amount,
    #             null::int as dep_amount,
    #             null::int as insurance_amount,
    #             null::int as contract_amount,
    #             null::int as tax_amount,
    #             null::int as sum_m3_sur,
    #             null::int as sum_tn_sur,
    #             null::int as indirect_cost,
    #             null::int as overhead_cost,
    #             null::int as ancillary_cost,
    #             null::int as hauling_distance,
    #             null::int as salary_amount,
    #             sum(aml.debit-aml.credit)/count(distinct t_msml2.excavator_id)/count(distinct t_msml2.excavator_id) as accomodation_amount
    #             FROM
    #             account_move_line AS aml 
    #             LEFT JOIN account_move AS am ON (aml.move_id = am.id)
    #             LEFT JOIN mining_cost_config_account_account_rel conf_rel on (conf_rel.account_id=aml.account_id)
    #             LEFT JOIN mining_cost_config conf on (conf.id=conf_rel.cost_id)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='dump'
    #             order by date
    #             ) as t_msml on (t_msml.date=aml.date)
    #             left join (SELECT 
    #             msm1.date,
    #             msml1.id,
    #             msm1.excavator_id,
    #             msm1.branch_id,
    #             msm1.id as parent_id
    #             from mining_surveyor_measurement_line msml1 
    #             left join mining_surveyor_measurement msm1 on (msm1.id=msml1.mining_surveyor_measurement_id)
    #             left join technic_equipment te on (msm1.excavator_id=te.id)
    #             where msm1.excavator_id is not null and te.owner_type='own_asset' and msml1.amount_by_measurement>0 and te.technic_type='dump'
    #             order by date) as t_msml2 on (t_msml2.date=aml.date)
    #             left join technic_equipment te on (t_msml.excavator_id=te.id)
    #         WHERE am.state='posted'
    #         and conf.type='accomodation_tracking'
    #         and t_msml2.excavator_id is not null and te.technic_type='dump'
    #         group by 2,3,4,5,6,7
                
    #             ) as cooost 
    #             WHERE owner_type='own_asset'
    #             group by date,
    #             branch_id,
    #             technic_id,
    #             technic_setting_id,
    #             owner_type,
    #             technic_type
    #                )
    # """
    #          % (self._table)
    #     )
    
    # @api.model
    # def _read_group_raw(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     self.check_access_rights('read')
    #     query = self._where_calc(domain)
    #     fields = fields or [f.name for f in self._fields.values() if f.store]

    #     groupby = [groupby] if isinstance(groupby, pycompat.string_types) else list(OrderedSet(groupby))
    #     groupby_list = groupby[:1] if lazy else groupby
    #     annotated_groupbys = [self._read_group_process_groupby(gb, query) for gb in groupby_list]
    #     groupby_fields = [g['field'] for g in annotated_groupbys]
    #     order = orderby or ','.join([g for g in groupby_list])
    #     groupby_dict = {gb['groupby']: gb for gb in annotated_groupbys}

    #     self._apply_ir_rules(query, 'read')
    #     for gb in groupby_fields:
    #         assert gb in fields, "Fields in 'groupby' must appear in the list of fields to read (perhaps it's missing in the list view?)"
    #         assert gb in self._fields, "Unknown field %r in 'groupby'" % gb
    #         gb_field = self._fields[gb].base_field
    #         assert gb_field.store and gb_field.column_type, "Fields in 'groupby' must be regular database-persisted fields (no function or related fields), or function fields with store=True"

    #     aggregated_fields = [
    #         f for f in fields
    #         if f != 'sequence'
    #         if f not in groupby_fields
    #         for field in [self._fields.get(f)]
    #         if field
    #         if field.group_operator
    #         if field.base_field.store and field.base_field.column_type
    #     ]

    #     field_formatter = lambda f: (
    #         self._fields[f].group_operator,
    #         self._inherits_join_calc(self._table, f, query),
    #         f,
    #     )
    #     select_terms = ['%s(%s) AS "%s" ' % field_formatter(f) for f in aggregated_fields]

    #     for gb in annotated_groupbys:
    #         select_terms.append('%s as "%s" ' % (gb['qualified_field'], gb['groupby']))

    #     groupby_terms, orderby_terms = self._read_group_prepare(order, aggregated_fields, annotated_groupbys, query)
    #     from_clause, where_clause, where_clause_params = query.get_sql()
    #     if lazy and (len(groupby_fields) >= 2 or not self._context.get('group_by_no_leaf')):
    #         count_field = groupby_fields[0] if len(groupby_fields) >= 1 else '_'
    #     else:
    #         count_field = '_'
    #     count_field += '_count'

    #     prefix_terms = lambda prefix, terms: (prefix + " " + ",".join(terms)) if terms else ''
    #     prefix_term = lambda prefix, term: ('%s %s' % (prefix, term)) if term else ''
    #     # print ('self._table',self._table)
    #     if self._table=='mining_cost_report_date': 
    #         find_list = [u'avg("mining_cost_report_date"."cost_unit") AS "cost_unit" ',
    #         u'avg("mining_cost_report_date"."fuel_amount_cost_unit") AS "fuel_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."selbeg_amount_cost_unit") AS "selbeg_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."electrical_amount_cost_unit") AS "electrical_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."tire_amount_cost_unit") AS "tire_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."oil_amount_cost_unit") AS "oil_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."dep_amount_cost_unit") AS "dep_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."insurance_amount_cost_unit") AS "insurance_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."contract_amount_cost_unit") AS "contract_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."tax_amount_cost_unit") AS "tax_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."indirect_cost_amount_cost_unit") AS "indirect_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."overhead_cost_amount_cost_unit") AS "overhead_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."ancillary_cost_amount_cost_unit") AS "ancillary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."salary_cost_amount_cost_unit") AS "salary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."accomodation_cost_amount_cost_unit") AS "accomodation_cost_amount_cost_unit" ',
    #         ]
    #         find_dict = {u'avg("mining_cost_report_date"."cost_unit") AS "cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."sum_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "cost_unit"',
    #         u'avg("mining_cost_report_date"."fuel_amount_cost_unit") AS "fuel_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."fuel_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "fuel_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."selbeg_amount_cost_unit") AS "selbeg_amount_cost_unit" ' :  u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."selbeg_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "selbeg_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."electrical_amount_cost_unit") AS "electrical_amount_cost_unit" ' :  u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."electrical_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "electrical_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."tire_amount_cost_unit") AS "tire_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."tire_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "tire_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."oil_amount_cost_unit") AS "oil_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."oil_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "oil_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."dep_amount_cost_unit") AS "dep_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."dep_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "dep_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."insurance_amount_cost_unit") AS "insurance_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."insurance_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "insurance_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."contract_amount_cost_unit") AS "contract_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."contract_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "contract_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."tax_amount_cost_unit") AS "tax_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."tax_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "tax_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."indirect_cost_amount_cost_unit") AS "indirect_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."indirect_cost_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "indirect_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."overhead_cost_amount_cost_unit") AS "overhead_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."overhead_cost_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "overhead_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."ancillary_cost_amount_cost_unit") AS "ancillary_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."ancillary_cost_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "ancillary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."salary_cost_amount_cost_unit") AS "salary_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."salary_cost_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "salary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date"."accomodation_cost_amount_cost_unit") AS "accomodation_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date"."sum_m3_sur")!=0 then sum("mining_cost_report_date"."accomodation_cost_amount")/sum("mining_cost_report_date"."sum_m3_sur") else null::int end  AS "accomodation_cost_amount_cost_unit" ',
    #         }
    #         in_ok = False
    #         for ff in find_list:
    #             if ff in select_terms:
    #                 in_ok = True
    #                 break
    #         if in_ok:
    #             for item_fi in  find_list:
    #                 if item_fi in select_terms:
    #                     get_index = select_terms.index(item_fi)
    #                     if get_index:
    #                         find_field = item_fi
    #                         set_field = find_dict[find_field]
    #                         select_terms[get_index] = set_field
                    
    #     query = """
    #         SELECT min("%(table)s".id) AS id, count("%(table)s".id) AS "%(count_field)s" %(extra_fields)s
    #         FROM %(from)s
    #         %(where)s
    #         %(groupby)s
    #         %(orderby)s
    #         %(limit)s
    #         %(offset)s
    #     """ % {
    #         'table': self._table,
    #         'count_field': count_field,
    #         'extra_fields': prefix_terms(',', select_terms),
    #         'from': from_clause,
    #         'where': prefix_term('WHERE', where_clause),
    #         'groupby': prefix_terms('GROUP BY', groupby_terms),
    #         'orderby': prefix_terms('ORDER BY', orderby_terms),
    #         'limit': prefix_term('LIMIT', int(limit) if limit else None),
    #         'offset': prefix_term('OFFSET', int(offset) if limit else None),
    #     }
    #     self._cr.execute(query, where_clause_params)
    #     fetched_data = self._cr.dictfetchall()

    #     if not groupby_fields:
    #         return fetched_data

    #     self._read_group_resolve_many2one_fields(fetched_data, annotated_groupbys)

    #     data = ({k: self._read_group_prepare_data(k,v, groupby_dict) for k,v in r.items()} for r in fetched_data)
    #     result = [self._read_group_format_result(d, annotated_groupbys, groupby, domain) for d in data]
    #     if lazy:
    #         # Right now, read_group only fill results in lazy mode (by default).
    #         # If you need to have the empty groups in 'eager' mode, then the
    #         # method _read_group_fill_results need to be completely reimplemented
    #         # in a sane way 
    #         result = self._read_group_fill_results(
    #             domain, groupby_fields[0], groupby[len(annotated_groupbys):],
    #             aggregated_fields, count_field, result, read_group_order=order,
    #         )
    #     return result