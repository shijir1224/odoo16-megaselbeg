# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class stock_ageing_report_balance(models.Model):
    _name = "stock.turn.report.balance1"
    _description = "stock turn report balance"
    _auto = False
    
    date = fields.Date(u'Үлдэгдлийн Огноо', readonly=True, )
    warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True)
    location_id = fields.Many2one('stock.location', u'Байрлал', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/template', readonly=True)
    # qty = fields.Float(u'Тоо хэмжээ', readonly=True)
    # price_unit = fields.Float(u'Нэгж өртөг', readonly=True, group_operator='avg')
    # total_price = fields.Float(u'Нийт өртөг', readonly=True)
    onhand_qty = fields.Integer(string=u'Нөөц тоо хэмжээ', readonly=True)
    onhand_price_unit = fields.Float(string=u'Нөөцний өртөг', readonly=True)
    onhand_total_price = fields.Float(string=u'Нөөцний нийт өртөг', readonly=True)
    used_qty = fields.Float(string=u'Хэрэглэсэн тоо хэмжээ', readonly=True)
    used_price_unit = fields.Float(string=u'Хэрэлгэсэн өртөг', readonly=True)
    used_total_price = fields.Float(string=u'Хэрэглэсэн нийт өртөгя', readonly=True)
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
                    sq.quantity as onhand_qty,
                    pt.list_price as onhand_price_unit,
                    sq.quantity/uu.factor * 1 as onhand_total_price,
                    sml.qty_done/uu.factor as used_qty,
                    sm.price_unit as used_price_unit,
                    sml.qty_done/uu.factor * sm.price_unit as used_total_price,
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
                LEFT JOIN stock_quant as sq on (sq.product_id = pp.id)
                WHERE sml.state = 'done' and sq.company_id is not null and sl.usage = 'supplier' and sl2.usage = 'internal'
                --GROUP BY sml.product_id, sml.id
                UNION ALL
                SELECT 
                    sml.id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_id as location_id,
                    pt.categ_id as categ_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sq.quantity as onhand_qty,
                    pt.list_price as onhand_price_unit,
                    sq.quantity/uu.factor * 1 as onhand_total_price,
                    sml.qty_done/uu.factor as used_qty,
                    sm.price_unit as used_price_unit,
                    sml.qty_done/uu.factor * sm.price_unit as used_total_price,
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
                LEFT JOIN stock_quant as sq on (sq.product_id = pp.id)
                WHERE sml.state = 'done' and sq.company_id is not null and sl.usage = 'supplier' and sl2.usage = 'internal' 
                --and sm.date >={1}

        )""" % (self._table))

class stock_turn_report(models.Model):
    _name = "stock.turn.report"
    _description = "stock turn report"
    _order = 'product_id'

    product_id = fields.Many2one('product.product',string=u'Бараа', readonly=True)
    category_id = fields.Many2one('product.category',string=u'Бараа', readonly=True)
    onhand_qty = fields.Integer(string=u'Бараа', readonly=True)
    onhand_price_unit = fields.Float(string=u'Бараа', readonly=True)
    onhand_total_price = fields.Float(string=u'Бараа', readonly=True)
    used_qty = fields.Float(string=u'Бараа', readonly=True)
    used_price_unit = fields.Float(string=u'Бараа', readonly=True)
    used_total_price = fields.Float(string=u'Бараа', readonly=True)
    stock_turn = fields.Float(string=u'Бараа', readonly=True)
    category = fields.Selection([('0','Non Moving'),('0_1','Slow Moving'),('1_3','Sales Moving'),('3_up','Fast Moving')],string=u'Ангилал', readonly=True)

    report_id = fields.Integer(u'Report ID', readonly=True, default=0, index=True)
    report_date = fields.Date(u'Тайлан огноо', readonly=True, index=True)
    date = fields.Date(u'Худалдан авсан огноо', readonly=True, index=True)
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
