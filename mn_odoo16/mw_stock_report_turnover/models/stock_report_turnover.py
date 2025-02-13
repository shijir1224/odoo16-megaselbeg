# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class StockReportTurnover(models.Model):
    _name = "stock.report.turnover"
    _description = "stock report turnover"
    _auto = False
    _order = 'product_id'

    date_expected = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
    warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True)
    picking_id = fields.Many2one('stock.picking', u'Баримт', readonly=True)
    stock_move_id = fields.Many2one('stock.move', u'Хөдөлгөөн', readonly=True)
    location_id = fields.Many2one('stock.location', u'Байрлал', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string=u'Цуврал', readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/Template', readonly=True)
    qty = fields.Float(u'Тоо хэмжээ', readonly=True, digits=(16, 2))
    standart_amount = fields.Float(u'Нийт өртөг /Одоогийн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit", digits=(16, 2))
    amount = fields.Float(u'Нийт өртөг/Тухайн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit", digits=(16, 2))
    dirty_profit = fields.Float(u'Бохир ашиг/Тухайн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit", digits=(16, 2))
    standart_dirty_profit = fields.Float(u'Бохир ашиг/Одоогийн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit", digits=(16, 2))
    amount_sale = fields.Float(u'Нийт зарах', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit", digits=(16, 2))
    state = fields.Char(readonly=True, string=u'Төлөв')
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')
    partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True)





    qty_sale_out = fields.Float(u'Зарлага Бор', readonly=True)
    total_price_sale_out = fields.Float(u'Өртөг Зарлага Бор', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_sale_in = fields.Float(u'Бор Буцаалт', readonly=True)
    total_price_sale_in = fields.Float(u'Өртөг Бор Буцаалт', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    
    qty_purchase_out = fields.Float(u'Ху/Авалт Буцаалт', readonly=True)
    total_price_purchase_out = fields.Float(u'Өртөг Ху/Авалт Буцаалт', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_purchase_in = fields.Float(u'Орлого Ху/Авалт', readonly=True)
    total_price_purchase_in = fields.Float(u'Өртөг Орлого Ху/Авалт', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    
    qty_inventory_out = fields.Float(u'Зарлага Тооллого', readonly=True)
    total_price_inventory_out = fields.Float(u'Зарлага Өртөг Тооллого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_inventory_in = fields.Float(u'Орлого Тооллого', readonly=True)
    total_price_inventory_in = fields.Float(u'Өртөг Орлого Тооллого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    
    qty_internal_in = fields.Float(u'Орлого Дотоод', readonly=True)
    total_price_internal_in = fields.Float(u'Өртөг Орлого Дотоод', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_internal_out = fields.Float(u'Зарлага Дотоод', readonly=True)
    total_price_internal_out = fields.Float(u'Өртөг Зарлага Дотоод', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_production_in = fields.Float(u'Орлого Үйлдвэр', readonly=True)
    total_price_production_in = fields.Float(u'Өртөг Орлого Үйлдвэр', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_production_out = fields.Float(u'Зарлага Үйлдвэр', readonly=True)
    total_price_production_out = fields.Float(u'Өртөг Үйлдвэр Зарлага', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_other_move_in = fields.Float(u'Орлого БМ Шаард', readonly=True)
    total_price_other_move_in = fields.Float(u'Өртөг Орлого БМ Шаард', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_other_move_out= fields.Float(u'Зарлага БМ Шаард', readonly=True)
    total_price_other_move_out = fields.Float(u'Зарлага Өртөг БМ Шаард', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    def _select(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id,
                    sml.picking_id,
                    sml.move_id as stock_move_id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_dest_id as location_id, 
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as amount,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(ip.value_float)) as standart_amount,
                    (coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(sm.price_unit),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as dirty_profit,
                    (coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(ip.value_float),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as standart_dirty_profit,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * pt.list_price) as amount_sale,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty,
                    (sml.date + interval '8 hour')::date as date_expected,
                    sml.state,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type,


                    CASE WHEN sl2.usage = 'customer' and sp.other_expense_id is null then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_sale_out,
                    CASE WHEN sl2.usage = 'customer' and sp.other_expense_id is null then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_sale_out,
                    0 as qty_sale_in,
                    0 as total_price_sale_in,
                    CASE WHEN sl2.usage = 'supplier' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_purchase_out,
                    CASE WHEN sl2.usage = 'supplier' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_purchase_out,
                    0 as qty_purchase_in,
                    0 as total_price_purchase_in,
                    CASE WHEN sl2.usage = 'inventory' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_inventory_out,
                    CASE WHEN sl2.usage = 'inventory' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_inventory_out,
                    0 as qty_inventory_in,
                    0 as total_price_inventory_in,
                    CASE WHEN sl2.usage = 'internal' and sl.usage='internal' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_internal_out,
                    CASE WHEN sl2.usage = 'internal' and sl.usage='internal' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_internal_out,
                    0 as qty_internal_in,
                    0 as total_price_internal_in,
                    CASE WHEN sl2.usage = 'production' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_production_out,
                    CASE WHEN sl2.usage = 'production' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_production_out,
                    0 as qty_production_in,
                    0 as total_price_production_in,
                    CASE WHEN sl2.usage = 'customer' and sp.other_expense_id is not null then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_other_move_out,
                    CASE WHEN sl2.usage = 'customer' and sp.other_expense_id is not null then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_other_move_out,
                    0 as qty_other_move_in,
                    0 as total_price_other_move_in
        """
    def _select2(self):
        return """
            SELECT 
                    sml.id*-1 as id,
                    sp.partner_id,
                    sml.picking_id,
                    sml.move_id as stock_move_id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_id as location_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as amount,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(ip.value_float)) as standart_amount,
                    -(coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(sm.price_unit),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as dirty_profit,
                    -(coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(ip.value_float),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as standart_dirty_profit,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * pt.list_price) as amount_sale,
                    -(case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty,
                    (sml.date + interval '8 hour')::date as date_expected,
                    sml.state,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type,


                    0 as qty_sale_out,
                    0 as total_price_sale_out,
                    CASE WHEN sl.usage = 'customer' and sp.other_expense_id is null then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_sale_in,
                    CASE WHEN sl.usage = 'customer' and sp.other_expense_id is null then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_sale_in,
                    0 as qty_purchase_out,
                    0 as total_price_purchase_out,
                    CASE WHEN sl.usage = 'supplier' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as total_price_sale_in,
                    CASE WHEN sl.usage = 'supplier' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_purchase_in,
                    0 as qty_inventory_out,
                    0 as total_price_inventory_out,
                    CASE WHEN sl.usage = 'inventory' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_inventory_in,
                    CASE WHEN sl.usage = 'inventory' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_inventory_in,
                    0 as qty_internal_out,
                    0 as total_price_internal_out,
                    CASE WHEN sl2.usage = 'internal' and sl.usage='internal' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_internal_in,
                    CASE WHEN sl2.usage = 'internal' and sl.usage='internal' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_internal_in,
                    0 as qty_production_out,
                    0 as total_price_production_out,
                    CASE WHEN sl.usage = 'production' then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_production_in,
                    CASE WHEN sl.usage = 'production' then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_production_in,
                    0 as qty_other_move_out,
                    0 as total_price_other_move_out,
                    CASE WHEN sl.usage = 'customer' and sp.other_expense_id is not null then (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) else 0 end as qty_other_move_in,
                    CASE WHEN sl.usage = 'customer' and sp.other_expense_id is not null then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_other_move_in
        """
    def _from(self):
        return """
            FROM stock_move_line as sml
        """
    def _from2(self):
        return """
            FROM stock_move_line as sml
        """
    def _join(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sml.picking_id = sp.id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN ir_property as ip on (ip.res_id = 'product.product,'||sml.product_id and ip.name = 'standard_price')
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join2(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sml.picking_id = sp.id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN ir_property as ip on (ip.res_id = 'product.product,'||sml.product_id and ip.name = 'standard_price')
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _where(self):
        return """"""
    def _where2(self):
        return """"""
        
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
            )
        """ % (self._table,self._select(), self._from(), self._join(), self._where(),
        self._select2(), self._from2(), self._join2(), self._where2())
        )