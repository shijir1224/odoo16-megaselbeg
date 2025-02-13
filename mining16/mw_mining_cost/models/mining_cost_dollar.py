# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, tools, api
from odoo.tools import pycompat, OrderedSet
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class mining_cost_report_date_dollar(models.Model):
    _name = 'mining.cost.report.date.dollar'
    _description = 'Mining cost report date dollar'
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

    electrical_amount = fields.Float('Electrical cost', readonly=True)
    electrical_amount_cost_unit = fields.Float('Electrical BCM Cost', readonly=True, group_operator='avg')
    
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
    
    currency_dollar = fields.Float('Dollar', readonly=True, group_operator='avg')
    
    _order = 'date desc'

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)

    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW %s AS (
    #             SELECT 
    #             rep.id,
    #             rep.date,
    #             rep.branch_id,
    #             rep.technic_id,
    #             rep.technic_setting_id,
    #             rep.owner_type,
    #             rep.technic_type,
    #             rep.fuel_amount/con.currency_dollar as fuel_amount,
    #             rep.selbeg_amount/con.currency_dollar as selbeg_amount,
    #             rep.electrical_amount/con.currency_dollar as electrical_amount,
    #             rep.tire_amount/con.currency_dollar as tire_amount,
    #             rep.oil_amount/con.currency_dollar as oil_amount,
    #             rep.sum_m3_sur,
    #             rep.sum_tn_sur,
    #             rep.dep_amount/con.currency_dollar as dep_amount,
    #             rep.insurance_amount/con.currency_dollar as insurance_amount,
    #             rep.contract_amount/con.currency_dollar as contract_amount,
    #             rep.tax_amount/con.currency_dollar as tax_amount,
    #             rep.indirect_cost_amount/con.currency_dollar as indirect_cost_amount,
    #             rep.overhead_cost_amount/con.currency_dollar as overhead_cost_amount,
    #             rep.ancillary_cost_amount/con.currency_dollar as ancillary_cost_amount,
    #             rep.salary_cost_amount/con.currency_dollar as salary_cost_amount,
    #             rep.accomodation_cost_amount/con.currency_dollar as accomodation_cost_amount,
    #             rep.hauling_distance,
    #             rep.sum_amount/con.currency_dollar as sum_amount,
    #             rep.cost_unit/con.currency_dollar as cost_unit,
    #             rep.fuel_amount_cost_unit/con.currency_dollar as fuel_amount_cost_unit, 
    #             rep.selbeg_amount_cost_unit/con.currency_dollar as selbeg_amount_cost_unit,
    #             rep.electrical_amount_cost_unit/con.currency_dollar as electrical_amount_cost_unit,
    #             rep.tire_amount_cost_unit/con.currency_dollar as tire_amount_cost_unit,
    #             rep.oil_amount_cost_unit/con.currency_dollar as oil_amount_cost_unit,
    #             rep.dep_amount_cost_unit/con.currency_dollar as dep_amount_cost_unit,
    #             rep.insurance_amount_cost_unit/con.currency_dollar as insurance_amount_cost_unit,
    #             rep.contract_amount_cost_unit/con.currency_dollar as contract_amount_cost_unit,
    #             rep.indirect_cost_amount_cost_unit/con.currency_dollar as indirect_cost_amount_cost_unit,
    #             rep.overhead_cost_amount_cost_unit/con.currency_dollar as overhead_cost_amount_cost_unit,
    #             rep.ancillary_cost_amount_cost_unit/con.currency_dollar as ancillary_cost_amount_cost_unit,
    #             rep.salary_cost_amount_cost_unit/con.currency_dollar as salary_cost_amount_cost_unit,
    #             rep.tax_amount_cost_unit/con.currency_dollar as tax_amount_cost_unit,
    #             rep.accomodation_cost_amount_cost_unit/con.currency_dollar as accomodation_cost_amount_cost_unit,
    #             con.currency_dollar
    #             FROM
    #             mining_cost_report_date as rep
    #             LEFT JOIN mining_cost_config as con on (rep.date>=con.date_start and rep.date<=con.date_end)
    #             where con.type='indirect_cost'
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
    #     # print ('----- eend self._table',self._table)
    #     if self._table=='mining_cost_report_date_dollar': 
    #         find_list = [u'avg("mining_cost_report_date_dollar"."cost_unit") AS "cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."fuel_amount_cost_unit") AS "fuel_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."selbeg_amount_cost_unit") AS "selbeg_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."electrical_amount_cost_unit") AS "electrical_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."tire_amount_cost_unit") AS "tire_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."oil_amount_cost_unit") AS "oil_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."dep_amount_cost_unit") AS "dep_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."insurance_amount_cost_unit") AS "insurance_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."contract_amount_cost_unit") AS "contract_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."tax_amount_cost_unit") AS "tax_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."indirect_cost_amount_cost_unit") AS "indirect_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."overhead_cost_amount_cost_unit") AS "overhead_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."ancillary_cost_amount_cost_unit") AS "ancillary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."salary_cost_amount_cost_unit") AS "salary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."accomodation_cost_amount_cost_unit") AS "accomodation_cost_amount_cost_unit" ',
    #         ]
    #         find_dict = {u'avg("mining_cost_report_date_dollar"."cost_unit") AS "cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."sum_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "cost_unit"',
    #         u'avg("mining_cost_report_date_dollar"."fuel_amount_cost_unit") AS "fuel_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."fuel_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "fuel_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."selbeg_amount_cost_unit") AS "selbeg_amount_cost_unit" ' :  u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."selbeg_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "selbeg_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."electrical_amount_cost_unit") AS "electrical_amount_cost_unit" ' :  u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."electrical_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "electrical_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."tire_amount_cost_unit") AS "tire_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."tire_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "tire_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."oil_amount_cost_unit") AS "oil_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."oil_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "oil_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."dep_amount_cost_unit") AS "dep_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."dep_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "dep_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."insurance_amount_cost_unit") AS "insurance_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."insurance_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "insurance_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."contract_amount_cost_unit") AS "contract_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."contract_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "contract_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."tax_amount_cost_unit") AS "tax_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."tax_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "tax_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."indirect_cost_amount_cost_unit") AS "indirect_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."indirect_cost_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "indirect_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."overhead_cost_amount_cost_unit") AS "overhead_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."overhead_cost_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "overhead_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."ancillary_cost_amount_cost_unit") AS "ancillary_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."ancillary_cost_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "ancillary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."salary_cost_amount_cost_unit") AS "salary_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."salary_cost_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "salary_cost_amount_cost_unit" ',
    #         u'avg("mining_cost_report_date_dollar"."accomodation_cost_amount_cost_unit") AS "accomodation_cost_amount_cost_unit" ': u'case when sum("mining_cost_report_date_dollar"."sum_m3_sur")!=0 then sum("mining_cost_report_date_dollar"."accomodation_cost_amount")/sum("mining_cost_report_date_dollar"."sum_m3_sur") else null::int end  AS "accomodation_cost_amount_cost_unit" ',
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