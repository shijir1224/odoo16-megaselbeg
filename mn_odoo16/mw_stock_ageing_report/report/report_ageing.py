# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class stock_ageing_report_balance(models.Model):
    _name = "stock.ageing.report.balance"
    _description = "stock ageing report balance"
    _auto = False
    
    date = fields.Date(u'Үлдэгдлийн Огноо', readonly=True, )
    max_date = fields.Date(string='Насжилт огноо')
    warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True)
    location_id = fields.Many2one('stock.location', u'Байрлал', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/template', readonly=True)
    qty = fields.Float(u'Тоо хэмжээ', readonly=True)
    price_unit = fields.Float(u'Нэгж өртөг', readonly=True, group_operator='avg')
    total_price = fields.Float(u'Нийт өртөг', readonly=True)
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')

    # @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
                 
SELECT 
                    sml.id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_dest_id as location_id, 
                    pt.categ_id as categ_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sml.qty_done/uu.factor as qty,
                    sm.price_unit,
                    sm.first_date as max_date,
                    sml.qty_done/uu.factor * sm.price_unit as total_price,
                    (sml.date + interval '8 hour')::date as date,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage='internal' 
                    and sl2.usage='supplier' then 'incoming' else 'outgoing' end as transfer_type
                FROM stock_move_line as sml
                LEFT JOIN product_product as pp on (pp.id = sml.product_id)
                LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
                LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
                LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
                LEFT JOIN stock_move as sm on (sml.move_id = sm.id)
                LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
                WHERE sml.state = 'done'
                UNION ALL
                SELECT 
                    sml.id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_id as location_id,
                    pt.categ_id as categ_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    -(sml.qty_done/uu.factor) as qty,
                    sm.price_unit,
                    sm.first_date as max_date,
                    -(sml.qty_done/uu.factor * abs(sm.price_unit)) as total_price,
                    (sml.date + interval '8 hour')::date as date,
                    case when sl2.usage='internal' and sl.usage='internal' then 'internal' when sl2.usage='internal' 
                    and sl.usage='supplier' then 'incoming' else 'outgoing' end as transfer_type
                FROM stock_move_line as sml
                LEFT JOIN product_product as pp on (pp.id = sml.product_id)
                LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
                LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
                LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
                LEFT JOIN stock_move as sm on (sml.move_id = sm.id)
                LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
                WHERE sml.state = 'done'

        )""" % self._table)

class stock_ageing_report(models.Model):
    _name = "stock.ageing.report"
    _description = "stock ageing report"
    _order = 'in_date_count desc, product_id'

    report_id = fields.Integer(u'Report ID', readonly=True, default=0, index=True)
    date = fields.Date(u'Худалдан авсан огноо', readonly=True, index=True)
    report_date = fields.Date(u'Тайлан огноо', readonly=True, index=True)
    warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True, index=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True, index=True)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True, index=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/template', readonly=True, index=True)
    qty = fields.Float(u'Тоо хэмжээ', readonly=True)
    in_date_count = fields.Integer(u'Агуулахад Байсан Хоног Нийт', readonly=True, )
    in_date_count_mid = fields.Integer(u'Агуулахад Байсан Хоног Дундаж', group_operator="avg", readonly=True, )
    date_range = fields.Selection([
            ('1_0_30', '0-30'), 
            ('2_31_180', '31-180'), 
            ('3_181_365', '181-365'), 
            ('4_366_730', '366-730'), 
            ('5_731_up', '731-дээш'), 
        ], readonly=True, string=u'Хугацааны төрөл')
    price_unit = fields.Float(u'Нэгж өртөг', readonly=True, group_operator='avg')
    total_price = fields.Float(u'Нийт өртөг', readonly=True)
    