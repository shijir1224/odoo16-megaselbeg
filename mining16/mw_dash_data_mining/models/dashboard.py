# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class mw_dash_data_oil_fuel_line(models.Model):
    _inherit = 'oil.fuel.line'

    par_date = fields.Date(related='parent_id.date', readonly=True, store=True)
    par_shift = fields.Selection(related='parent_id.shift', readonly=True, store=True)
    par_state = fields.Selection(related='parent_id.state', readonly=True, store=True)
    par_partner_id = fields.Many2one('res.partner', related='parent_id.partner_id', readonly=True, store=True)
    par_warehouse_id = fields.Many2one('stock.warehouse', related='parent_id.warehouse_id', readonly=True, store=True)
    par_location_id = fields.Many2one('stock.location', related='parent_id.location_id', readonly=True, store=True)
    par_type = fields.Selection(related='parent_id.type', readonly=True, store=True)

class mw_dash_data_oil_fuel_orlogo_uld(models.Model):
    _name = 'mw.dash.data.oil.fuel.orlogo.uld'
    _auto = False
    _description = 'mw_dash_data Oil fuel orlogo uld'
    _order = 'date, shift'
    _rec_name = 'id'

    date = fields.Date(string='Огноо', readonly=True)
    shift = fields.Selection([('day','Өдөр'), ('night','Шөнө')], string='Ээлж', readonly=True)
    state = fields.Selection([('draft','Ноорог'), ('done','Дууссан')], readonly=True, string='Төлөв')
    partner_id = fields.Many2one('res.partner', string='Нийлүүлэгч', readonly=True)
    product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
    categ_id = fields.Many2one('product.category', string='Барааны Ангилал', readonly=True)
    location_id = fields.Many2one('stock.location', string='Байрлал', readonly=True)
    product_qty_in = fields.Float(string='Орлого', readonly=True)
    product_qty_out = fields.Float(string='Зарлага', readonly=True)
    type = fields.Char('Төрөл', readonly=True)
    uldegdel = fields.Float(string='Үлдэгдэл', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        
        self._cr.execute("""
                CREATE OR REPLACE VIEW %s AS (
                SELECT
                    max(ofl.id) as id,
                    of.shift,
                    of.state,
                    of.date,
                    of.location_id,
                    of.partner_id,
                    of.type,
                    ofl.product_id,
                    pt.categ_id,
                    sum(case when  of.type='fuel' then ofl.product_qty else 0 end) as product_qty_out,
                    sum(case when  of.type='fuel_in' then ofl.product_qty else 0 end) as product_qty_in,
                    sum(case when  of.type='fuel' then -ofl.product_qty else ofl.product_qty end) as uldegdel
                    FROM oil_fuel_line AS ofl 
                    LEFT JOIN oil_fuel AS of ON (ofl.parent_id=of.id)
                    LEFT JOIN product_product AS pp ON (ofl.product_id=pp.id)
                    LEFT JOIN product_template AS pt ON (pp.product_tmpl_id=pt.id)
                WHERE of.type in ('fuel','fuel_in')
                group by 2,3,4,5,6,7,8,9
                )
        """ % (self._table)
        )


class mw_dash_data_fuel(models.Model):
    _name = 'mw.dash.data.fuel'
    _auto = False
    _description = 'Oil fuel fuel report'
    _order = 'date, shift'

    _rec_name = 'id'

    date = fields.Date(string='Огноо', readonly=True)
    shift = fields.Selection([('day','Өдөр'), ('night','Шөнө')], string='Ээлж', readonly=True)
    technic_id = fields.Many2one('technic.equipment', string='Техник', readonly=True)
    product_qty = fields.Float(string='Авсан түлш', readonly=True)
    location_id_chars = fields.Char('Байрлал', readonly=True)
    technic_type = fields.Char(string ='Техникийн төрөл', readonly=True, required=False)
    technic_type_mine = fields.Char(string ='Техникийн төрөл уул', readonly=True, required=False)
    technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True,)
    owner_type = fields.Selection([
        ('own_asset',u'Өөрийн хөрөнгө'),
        ('rent',u'Түрээс'),
        ('contracted',u'Гэрээт')], 
        string=u'Эзэмшлийн төрөл', readonly=True,)
    run_hour = fields.Float('АМЦ', readonly=True)
    avg_epx = fields.Float(string='1МЦЗ', readonly=True, group_operator='avg')
    avg_epx_niit = fields.Float(string='1 Мото цагийн зарцуулалт', readonly=True)
    m3_zartsuulalt = fields.Float(string='1 м3 зарцуулалт', readonly=True)
    res_count = fields.Float(string='Ресс', readonly=True)
    production_amount = fields.Float(string='Бүтээл', readonly=True)
    technic_partner_id = fields.Many2one('res.partner', string='Technic Partner', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
            select 
            max(orep.id) as id,
            orep.date,
            orep.shift,
            orep.technic_id,
            array_agg(distinct orep.location_id) as location_id_chars,
            orep.technic_type,
            orep.technic_setting_id,
            orep.owner_type,
            orep.technic_partner_id,
            sum(orep.product_qty) as product_qty,
            sum(run_hour) as run_hour,
            sum(avg_epx) as avg_epx,
            sum(avg_epx) as avg_epx_niit,
            case when sum(production_amount)!=0 then sum(orep.product_qty)/sum(production_amount) else 0 end as  m3_zartsuulalt,
            sum(res_count) as res_count,
            sum(production_amount) as production_amount,
            case when orep.technic_type in ('grader','loader','dozer') then 'support technic'
                    when orep.technic_type in ('dump','excavator') then orep.technic_type
                    else 'other' end technic_type_mine
            from 
            oil_fuel_fuel_report as orep
            group by 
            orep.date,
            orep.shift,
            orep.technic_id,
            orep.technic_type,
            orep.technic_setting_id,
            orep.owner_type,
            orep.technic_partner_id
            )
        """ % (self._table)
        )