# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE


class report_mining_mrp_cost_analyze(models.TransientModel):
    _name = 'report.mining.mrp.cost.analyze'
    _description = 'MRP cost Production'
    # _auto = False

    date = fields.Date('Date', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
    # technic_id = fields.Many2one('technic.equipment', 'Technic', readonly=True)
    account_amount = fields.Float('Санхүү дүн', readonly=True)
    analytic_amount = fields.Float('Шинжилгээний дүн', readonly=True)
    # petram_amount = fields.Float('Петрам дүн', readonly=True)
    aml_id = fields.Many2one('account.move.line','Санхүү гүйлгээ', readonly=True)
    analytic_move_id = fields.Many2one('account.analytic.line','Шинжилгээний гүйлгээ', readonly=True)
    analytic_acc = fields.Many2one('account.analytic.account','Шинжилгээний данс', readonly=True)
    # production_line_id = fields.Many2one('mining.production.entry.line', 'Prodcution line', readonly=True)
    # material_id = fields.Many2one('mining.material', 'Материал', readonly=True)
    product_id = fields.Many2one('product.product', 'Бараа', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Салбар', readonly=True)
    
    gl_acc = fields.Many2one('account.account', 'Данс', readonly=True)
    wizard_id = fields.Many2one('report.mining.mrp.wizard', 'Wizard', readonly=True)
    # average_haul_distance = fields.Float(string='Талын зай жигнэсэн дундаж', readonly=True, group_operator='avg')

    sum_m3 = fields.Float('Нийт м3 Мэдээгээр', readonly=True)
    res_count = fields.Float('Нийт ресс Мэдээгээр', readonly=True)
    sum_tn = fields.Float('Нийт тн Мэдээгээр', readonly=True)
    sum_m3_sur = fields.Float('Нийт м3 Хэмжилтээр', readonly=True)
    sum_tn_sur = fields.Float('Нийт тн Хэмжилтээр', readonly=True)
    sum_m3_petram = fields.Float('Нийт м3 Петрам', readonly=True)
    sum_tn_petram = fields.Float('Нийт тн Петрам', readonly=True)
    sum_m3_avg = fields.Float('Нийт м3 Бүтээл', readonly=True)
    sum_tn_avg = fields.Float('Нийт тн Бүтээл', readonly=True)

    sum_m3_unit = fields.Float('Нийт м3 Мэдээгээр / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    res_count_unit = fields.Float('Нийт ресс Мэдээгээр / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    sum_tn_unit = fields.Float('Нийт тн Мэдээгээр / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    sum_m3_sur_unit = fields.Float('Нийт м3 Хэмжилтээр / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    sum_tn_sur_unit = fields.Float('Нийт тн Хэмжилтээр / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    sum_m3_petram_unit = fields.Float('Нийт м3 Петрам / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    sum_tn_petram_unit = fields.Float('Нийт тн Петрам / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    
    sum_m3_avg_unit = fields.Float('Нийт м3 Бүтээл / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    sum_tn_avg_unit = fields.Float('Нийт тн Бүтээл / нэгж', readonly=True,compute='_compute_units', store=True, copy=False)
    
    @api.depends('wizard_id')
    def _compute_units(self):
        for report in self:
            print ('report ',report)
            if report.sum_m3:
                query = """
                            select 
                                    sum(account_amount)/sum(sum_m3) as am
                                    from report_mining_mrp_cost_analyze 
                                    where  wizard_id={0} and product_id={1}
                """.format(report.wizard_id.id,report.product_id.id) 
                self.env.cr.execute(query)  
                m_data = self.env.cr.dictfetchall()
                report.sum_m3_unit = m_data[0]['am']                 
                # report.sum_m3_unit = report.account_amount / report.sum_m3
            else:
                report.sum_m3_unit = 0
            if report.res_count:
                query = """
                            select 
                                    sum(account_amount)/sum(res_count) as am
                                    from report_mining_mrp_cost_analyze 
                                    where  wizard_id={0} and product_id={1}
                """.format(report.wizard_id.id,report.product_id.id) 
                self.env.cr.execute(query)  
                m_data = self.env.cr.dictfetchall()
                report.res_count_unit = m_data[0]['am']                 
                # report.res_count_unit = report.account_amount / report.res_count
            else:
                report.res_count_unit = 0
            if report.sum_tn:
                query = """
                            select 
                                    sum(account_amount)/sum(sum_tn) as am
                                    from report_mining_mrp_cost_analyze 
                                    where  wizard_id={0} and product_id={1}
                """.format(report.wizard_id.id,report.product_id.id) 
                self.env.cr.execute(query)  
                m_data = self.env.cr.dictfetchall()
                report.sum_tn_unit = m_data[0]['am']                  
                # report.sum_tn_unit = report.account_amount / report.sum_tn
            else:
                report.sum_tn_unit = 0
            if report.sum_m3_sur:
                query = """
                            select 
                                    sum(account_amount)/sum(sum_m3_sur) as am
                                    from report_mining_mrp_cost_analyze 
                                    where  wizard_id={0} and product_id={1}
                """.format(report.wizard_id.id,report.product_id.id) 
                self.env.cr.execute(query)  
                m_data = self.env.cr.dictfetchall()
                report.sum_m3_sur_unit = m_data[0]['am']                 
                # report.sum_m3_sur_unit = report.account_amount / report.sum_m3_sur
            else:
                report.sum_m3_sur_unit = 0
            if report.sum_tn_sur:
                query = """
                            select 
                                    sum(account_amount)/sum(sum_tn_sur) as am
                                    from report_mining_mrp_cost_analyze 
                                    where  wizard_id={0} and product_id={1}
                """.format(report.wizard_id.id,report.product_id.id) 
                self.env.cr.execute(query)  
                m_data = self.env.cr.dictfetchall()
                report.sum_tn_sur_unit = m_data[0]['am']                 
                # report.sum_tn_sur_unit = report.account_amount / report.sum_tn_sur
            else:
                report.sum_tn_sur_unit = 0
            if report.sum_m3_petram:
                query = """
                            select 
                                    sum(account_amount)/sum(sum_m3_petram) as am
                                    from report_mining_mrp_cost_analyze 
                                    where  wizard_id={0} and product_id={1}
                """.format(report.wizard_id.id,report.product_id.id) 
                self.env.cr.execute(query)  
                m_data = self.env.cr.dictfetchall()
                report.sum_m3_petram_unit = m_data[0]['am']                
                # report.sum_m3_petram_unit = report.account_amount / report.sum_m3_petram
            else:
                report.sum_m3_petram_unit = 0
            if report.sum_tn_petram:
                report.sum_tn_petram_unit = report.account_amount / report.sum_tn_petram
            else:
                report.sum_tn_petram_unit = 0
            if report.sum_m3_avg:
                report.sum_m3_avg_unit = report.account_amount / report.sum_m3_avg
            else:
                report.sum_m3_avg_unit = 0
            if report.sum_tn_avg:
                report.sum_tn_avg_unit = report.account_amount / report.sum_tn_avg
            else:
                report.sum_tn_avg_unit = 0

    _order = 'date desc'
    #
    # def _from(self):
    #     return """
    #         from mining_cost_mrp_config_account_account_rel r 
    #             left join account_move_line l on r.account_id=l.account_id 
    #             left join mining_cost_mrp_config c on r.cost_id=c.id  
    #             left join account_analytic_line al on  al.move_line_id=l.id 
    #             left join mining_cost_mrp_config_account_analytic_rel ar on ar.account_id=al.account_id         
    #      """
    #
    # def _group_by(self):
    #     return """
    #             group by l.account_id ,al.account_id,
    #                 al.id ,
    #                 l.id ,    c.product_id, l.date,    l.branch_id """
    #
    # def _having(self):
    #     return """ """
    #
    # def _where(self):
    #     # l.date between '2023-10-01' and '2023-10-31'
    #     return """
    #     where  
    #         l.debit>0 
    #         and ar.account_id notnull """
    #
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, self._table)
    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW {0} AS (
    #             select foo.*,ml.petram_amount from(
    #             select 
    #                 l.id,
    #                 l.date,
    #                 l.branch_id,
    #                 l.account_id gl_account,
    #                 sum(debit) as account_amount,
    #                 sum(al.amount) as analytic_amount,
    #                 l.account_id as gl_acc,
    #                 al.account_id as analytic_acc,
    #                 al.id as analytic_move_id,
    #                 l.id as aml_id,
    #                 c.product_id as product_id
    #             from mining_cost_mrp_config_account_account_rel r 
    #                 left join account_move_line l on r.account_id=l.account_id 
    #                 left join mining_cost_mrp_config c on r.cost_id=c.id  
    #                 left join account_analytic_line al on  al.move_line_id=l.id 
    #                 left join mining_cost_mrp_config_account_analytic_rel ar on ar.account_id=al.account_id 
    #             where  
    #             l.debit>0 
    #             and ar.account_id notnull
    #             group by l.account_id ,al.account_id,
    #                 al.id ,
    #                 l.id ,    c.product_id,l.date,    l.branch_id
    #             ) as foo
    #             left join 
    #              (
    #                 select ml.material_id, sum(ml.sum_m3_petram) as petram_amount
    #                 from
    #                 mining_production_entry_line ml
    #                 group by ml.material_id
    #                 ) ml on foo.product_id = (select product_id from mining_material where id=ml.material_id )      )
    #
    #     """.format(
    #     self._table
    #     ))    
