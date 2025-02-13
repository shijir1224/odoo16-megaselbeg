# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class StockReportDetailFull(models.Model):
    _name = "stock.report.detail.full"
    _description = "Stock Report Detailt Full"
    _auto = False
    _order = 'product_id'

    picking_id = fields.Many2one('stock.picking', string=u'Баримт', readonly=True)
    stock_move_id = fields.Many2one('stock.move', string=u'Хөдөлгөөн', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'Харилцагч', readonly=True)
    location_id = fields.Many2one('stock.location', string=u'Байрлал', readonly=True)
    location_dest_id = fields.Many2one('stock.location', string=u'Хүрэх Байрлал', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u'Агуулах', readonly=True)
    date_expected = fields.Date(string=u'Огноо', readonly=True)
    date_balance = fields.Date(string=u'Үлдэгдлийн Огноо', readonly=True)
    product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string=u'Бараа/Template', readonly=True)
    categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True,)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string=u'Цуврал',readonly=True)
    description = fields.Char(string=u'Тайлбар', readonly=True)
    qty_first = fields.Float(string=u'Эхний Үлдэгдэл', readonly=True)
    price_unit_first = fields.Float(string=u'Нэгж Өртөг Эхний', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price_first = fields.Float(string=u'Өртөг Эхний Үлдэгдэл ', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_last = fields.Float(string=u'Эцсийн Үлдэгдэл', readonly=True)
    total_price_last = fields.Float(string=u'Өртөг Эцсийн Үлдэгдэл ', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_income = fields.Float(string=u'Нийт Орлого', readonly=True)
    price_unit_income = fields.Float(string=u'Нийт Нэгж Өртөг Орлого', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price_income = fields.Float(string=u'Нийт Өртөг Орлого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_expense = fields.Float(string=u'Нийт Зарлага', readonly=True)
    price_unit_expense = fields.Float(string=u'Нийт Нэгж Өртөг Зарлага', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    price_unit = fields.Float(string=u'Нэгж Өртөг', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price_expense = fields.Float(string=u'Нийт Өртөг Зарлага', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    state = fields.Selection([
            ('draft', u'Бүгд'),
            ('confirmed', u'Бэлэн болохыг хүлээж байгаа'), 
            ('assigned', u'Бэлэн'),
            ('done', u'Дууссан'),
        ], default='done', string=u'Төлөв', required=True,)
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')
    
    qty_sale_out = fields.Float(string=u'Зарлага Бор', readonly=True)
    total_price_sale_out = fields.Float(string=u'Өртөг Зарлага Бор', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_sale_in = fields.Float(string=u'Бор Буцаалт', readonly=True)
    total_price_sale_in = fields.Float(string=u'Өртөг Бор Буцаалт', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    
    qty_purchase_out = fields.Float(string=u'Ху/Авалт Буцаалт', readonly=True)
    total_price_purchase_out = fields.Float(string=u'Өртөг Ху/Авалт Буцаалт', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_purchase_in = fields.Float(string=u'Орлого Ху/Авалт', readonly=True)
    total_price_purchase_in = fields.Float(string=u'Өртөг Орлого Ху/Авалт', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    
    qty_inventory_out = fields.Float(string=u'Зарлага Тооллого', readonly=True)
    total_price_inventory_out = fields.Float(string=u'Зарлага Өртөг Тооллого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_inventory_in = fields.Float(string=u'Орлого Тооллого', readonly=True)
    total_price_inventory_in = fields.Float(string=u'Өртөг Орлого Тооллого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    
    qty_internal_in = fields.Float(string=u'Орлого Дотоод', readonly=True)
    total_price_internal_in = fields.Float(string=u'Өртөг Орлого Дотоод', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_internal_out = fields.Float(string=u'Зарлага Дотоод', readonly=True)
    total_price_internal_out = fields.Float(string=u'Өртөг Зарлага Дотоод', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_production_in = fields.Float(string=u'Орлого Үйлдвэр', readonly=True)
    total_price_production_in = fields.Float(string=u'Өртөг Орлого Үйлдвэр', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_production_out = fields.Float(string=u'Зарлага Үйлдвэр', readonly=True)
    total_price_production_out = fields.Float(string=u'Өртөг Үйлдвэр Зарлага', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    qty_other_move_in = fields.Float(string=u'Орлого БМ Шаард', readonly=True)
    total_price_other_move_in = fields.Float(string=u'Өртөг Орлого БМ Шаард', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_other_move_out= fields.Float(string=u'Зарлага БМ Шаард', readonly=True)
    total_price_other_move_out = fields.Float(string=u'Зарлага Өртөг БМ Шаард', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")

    def _select(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl.id as location_id,
                    sl2.id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    0 as qty_first,
                    0 as price_unit_first,
                    0 as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_expense,
                    sm.price_unit as price_unit_expense,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_expense,

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
                    0 as total_price_other_move_in,
                    
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    sl.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _select2(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl2.id as location_id,
                    sl.id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    0 as qty_first,
                    0 as price_unit_first,
                    0 as total_price_first,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_income,
                    sm.price_unit as price_unit_income,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    
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
                    CASE WHEN sl.usage = 'customer' and sp.other_expense_id is not null then ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) else 0 end as total_price_other_move_in,
                    
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    sl2.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    
    def _select3(self):
        return """
            SELECT 
                    sml.id*-1 as id,
                    sp.partner_id as partner_id,
                    sml.location_dest_id as location_id, 
                    sml.location_id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_first,
                    sm.price_unit as price_unit_first,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,

                    0 as qty_sale_out,
                    0 as total_price_sale_out,
                    0 as qty_sale_in,
                    0 as total_price_sale_in,
                    0 as qty_purchase_out,
                    0 as total_price_purchase_out,
                    0 as qty_purchase_in,
                    0 as total_price_purchase_in,
                    0 as qty_inventory_out,
                    0 as total_price_inventory_out,
                    0 as qty_inventory_in,
                    0 as total_price_inventory_in,
                    0 as qty_internal_out,
                    0 as total_price_internal_out,
                    0 as qty_internal_in,
                    0 as total_price_internal_in,
                    0 as qty_production_out,
                    0 as total_price_production_out,
                    0 as qty_production_in,
                    0 as total_price_production_in,
                    0 as qty_other_move_out,
                    0 as total_price_other_move_out,
                    0 as qty_other_move_in,
                    0 as total_price_other_move_in,
                    
                    null::date as date_expected,
                    (sml.date + interval '8 hour')::date as date_balance,
                    sl.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    
    def _select4(self):
        return """
            SELECT 
                    sml.id*-33 as id,
                    sp.partner_id as partner_id,
                    sml.location_id as location_id,
                    sml.location_dest_id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end)) as qty_first,
                    sm.price_unit as price_unit_first,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    0 as qty_sale_out,
                    0 as total_price_sale_out,
                    0 as qty_sale_in,
                    0 as total_price_sale_in,
                    0 as qty_purchase_out,
                    0 as total_price_purchase_out,
                    0 as qty_purchase_in,
                    0 as total_price_purchase_in,
                    0 as qty_inventory_out,
                    0 as total_price_inventory_out,
                    0 as qty_inventory_in,
                    0 as total_price_inventory_in,
                    0 as qty_internal_out,
                    0 as total_price_internal_out,
                    0 as qty_internal_in,
                    0 as total_price_internal_in,
                    0 as qty_production_out,
                    0 as total_price_production_out,
                    0 as qty_production_in,
                    0 as total_price_production_in,
                    0 as qty_other_move_out,
                    0 as total_price_other_move_out,
                    0 as qty_other_move_in,
                    0 as total_price_other_move_in,
                    
                    null::date as date_expected,
                    (sml.date + interval '8 hour')::date as date_balance,
                    sl.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _select_main(self):
        return """
            SELECT 
                    id,
                    partner_id,
                    location_id, 
                    location_dest_id,
                    description,
                    state,
                    picking_id,
                    stock_move_id,
                    categ_id,
                    uom_id,
                    lot_id,
                    barcode,
                    default_code,
                    product_id,
                    product_tmpl_id,
                    price_unit,
                    qty_first,
                    price_unit_first,
                    total_price_first,
                    qty_income,
                    price_unit_income,
                    total_price_income,
                    qty_expense,
                    price_unit_expense,
                    total_price_expense,
                    qty_sale_out,
                    total_price_sale_out,
                    qty_sale_in,
                    total_price_sale_in,
                    qty_purchase_out,
                    total_price_purchase_out,
                    qty_purchase_in,
                    total_price_purchase_in,
                    qty_inventory_out,
                    total_price_inventory_out,
                    qty_inventory_in,
                    total_price_inventory_in,
                    qty_internal_out,
                    total_price_internal_out,
                    qty_internal_in,
                    total_price_internal_in,
                    qty_production_out,
                    total_price_production_out,
                    qty_production_in,
                    total_price_production_in,
                    qty_other_move_out,
                    total_price_other_move_out,
                    qty_other_move_in,
                    total_price_other_move_in,
                    (qty_first+qty_income-qty_expense) as qty_last,
                    (total_price_first+total_price_income-total_price_expense) as total_price_last,
                    date_expected,
                    date_balance,
                    warehouse_id,
                    transfer_type
        """
    def _from(self):
        return """
            FROM stock_move_line as sml
        """
    def _from2(self):
        return """
            FROM stock_move_line as sml
        """
    def _from3(self):
        return """
            FROM stock_move_line as sml
        """
    def _from4(self):
        return """
            FROM stock_move_line as sml
        """
    def _join(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join2(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join3(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join4(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    

    def _where(self):
        return """"""
    def _where2(self):
        return """"""
    def _where3(self):
        return """  """
    def _where4(self):
        return """  """
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                FROM (
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                ) as temp_bayasaa
            )
        """ % (self._table,self._select_main(), self._select(), self._from(), self._join(), self._where(),
        self._select2(), self._from2(), self._join2(), self._where2(),
        self._select3(), self._from3(), self._join3(), self._where3(),
        self._select4(), self._from4(), self._join4(), self._where4())
        )
