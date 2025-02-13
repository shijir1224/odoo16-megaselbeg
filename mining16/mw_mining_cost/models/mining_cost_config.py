# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime as DT
from odoo import fields, models, tools, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

class mining_cost_config(models.Model):
    _name = 'mining.cost.config'
    _description = 'Mining cost config'
    _order = 'year, month'
    
    type = fields.Selection([
        ('fuel', 'Fuel'),
        ('selbeg', 'Parts'),
        ('tire', 'Tire'),
        ('oil', 'Oil'),
        ('depreciation', 'Depreciation'),
        ('insurance', 'Insurance'),
        ('salary_digging', 'Salary Digging'),
        ('salary_tracking', 'Salary Tracking'),
        ('accomodation_digging', 'Accomodation Digging'),
        ('accomodation_tracking', 'Accomodation Tracking'),
        ('indirect_cost', 'Indirect cost'),
        ('overhead_cost', 'Overhead cost'),
        ('contract', 'Contract service'),
        ('tax', 'Tax'),
        ('electrical', 'Electrical'),
        # ('loading_ancillary', 'Loading Ancillary'),
        ], 'Cost Type', required=True)
    year = fields.Selection([
        ('2018','2018'),
        ('2019','2019'),
        ('2020','2020'),
        ('2021','2021'),
        ('2022','2022'),
        ('2023','2023'),
        ('2024','2024'),
        ('2025','2025'),
        ('2026','2026'),
        ('2027','2027'),
        ('2028','2028'),
        ], 'Жил')
    month = fields.Selection([
        ('01', '01'),
        ('02', '02'),
        ('03', '03'),
        ('04', '04'),
        ('05', '05'),
        ('06', '06'),
        ('07', '07'),
        ('08', '08'),
        ('09', '09'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ], 'Сар')
    date_start = fields.Date('Эхлэх Огноо')
    date_end = fields.Date('Дуусах Огноо')
    exca_percent = fields.Float('Эксаватор эзлэх %')
    dump_percent = fields.Float('Дамп эзлэх %')
    categ_ids = fields.Many2many('product.category', 'mining_cost_config_product_product_rel', 'cost_id','categ_id',  'Хамаарах Барааны ангилал')
    account_ids = fields.Many2many('account.account', 'mining_cost_config_account_account_rel', 'cost_id','account_id',  'Хамаарах Данснууд')
    technic_config_line = fields.One2many('mining.cost.config.line', 'parent_id', 'Экскаваторын хувь оруулах', copy=True)
    technic_config_line2 = fields.One2many('mining.cost.config.line', 'parent_id2', 'Дампын хувь оруулах', copy=True)

    ancillary_digging_technic_ids = fields.Many2many('technic.equipment', 'mining_cost_config_ancillary_digging_technic_rel', 'cost_id','technic_id',  'Digging Ancillary Equipment')
    ancillary_tracking_technic_ids = fields.Many2many('technic.equipment', 'mining_cost_config_ancillary_tracking_technic_rel', 'cost_id','technic_id',  'Tracking Ancillary Equipment')
    currency_dollar = fields.Float('Dollar', default=2000)

    @api.onchange('year', 'month')
    def _onchange_year_month(self):
        if self.year and self.month:
            date_start = DT.date(int(self.year), int(self.month), 1)
            date_end = self.last_day_of_month(date_start)
            self.date_start = date_start
            self.date_end = date_end

    def last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    def action_view_aml(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        action['domain']= [('move_id.state','=','posted'),('account_id','in',self.account_ids.ids)]
        res = self.env.ref('account.view_move_line_tree', False)
        print(res)
        action['views'] = [(res and res.id or False, 'tree')]
        action['res_id'] = self.id
        # if self.date_start and self.type in ['indirect_cost','overhead_cost']:
        #     action['domain'].append(('date', '>=', self.date_start))
        # if self.date_end and self.type in ['indirect_cost','overhead_cost']:
        #     action['domain'].append(('date', '<=', self.date_end))
        print(action['views'])
        print(action['res_id'])
        return action

    def action_view_aml_ancillary_exca(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        account_ids = self.env['mining.cost.config'].search([('type','not in',['indirect_cost','overhead_cost'])]).mapped('account_ids')
        domain = [('move_id.state','=','posted'),
        # ('date', '<=', self.date_end),('date', '>=', self.date_start),
        ('account_id','in',account_ids.ids),
        ('technic_id','in',self.ancillary_digging_technic_ids.ids)]
        action['domain'] = domain
        return action

    def action_view_aml_ancillary_dump(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        account_ids = self.env['mining.cost.config'].search([('type','not in',['indirect_cost','overhead_cost'])]).mapped('account_ids')
        action['domain']= [('move_id.state','=','posted'),
        # ('date', '<=', self.date_end),('date', '>=', self.date_start),
        ('account_id','in',account_ids.ids),
        ('technic_id','in',self.ancillary_digging_technic_ids.ids)]
        return action
        
        

class mining_cost_config_line(models.Model):
    _name = 'mining.cost.config.line'
    _description = 'Mining cost config line'
    
    parent_id = fields.Many2one('mining.cost.config', 'Эцэг байрлал', ondelete='cascade')
    parent_id2 = fields.Many2one('mining.cost.config', 'Эцэг байрлал', ondelete='cascade')
    technic_id = fields.Many2one('technic.equipment', 'Техник', required=True)
    percent = fields.Float('Хувь', required=True)
    date_start = fields.Date(related='parent_id.date_start', store=True)
    date_end = fields.Date(related='parent_id.date_end', store=True)
    exca_percent = fields.Float(related='parent_id.exca_percent', store=True)
    dump_percent = fields.Float(related='parent_id.dump_percent', store=True)
    type = fields.Selection(related='parent_id.type', store=True)
    owner_type = fields.Selection(related='technic_id.owner_type', store=True)





class mining_cost_mrp_config(models.Model):
    _name = 'mining.cost.mrp.config'
    _description = 'Mining cost mrp config'
    
    name = fields.Char('нэр', required=True)
 # material_id = fields.Many2one('mining.material', 'Материал', required=True)
    product_id = fields.Many2one('product.product', 'Бараа', required=True)
    account_ids = fields.Many2many('account.account', 'mining_cost_mrp_config_account_account_rel', 'cost_id','account_id',  'Хамаарах Данснууд')

    analytic_ids = fields.Many2many('account.analytic.account', 'mining_cost_mrp_config_account_analytic_rel', 'cost_id','account_id',  'Шинжилгээний данс')
    branch_ids = fields.Many2many('res.branch', 'mining_cost_mrp_config_res_branch_rel', 'cost_id','branch_id',  'Салбар')
