# -*- coding: utf-8 -*-
from odoo import tools
from odoo import fields, models

class SaleOrderWarehouseReport(models.Model):
    _name = "sale.order.warehouse.report"
    _description = "sale order warehouse report"
    _auto = False
    _order = 'product_id'

    sale_order_id = fields.Many2one('sale.order', string='S0 дугаар', readonly=True)
    sale_order_line_id = fields.Many2one('sale.order.line', string='S0 мөр', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'Харилцагч', readonly=True)
    categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True)
    default_code = fields.Char(string=u'Барааны код', readonly=True)
    sale_date = fields.Datetime(string='Борлуулалтын огноо', readonly=True)
    qty_so = fields.Float(string='Тоо хэмжээ SO', readonly=True)
    price_unit_so = fields.Float('Нэгж үнэ SO', readonly=True, group_operator="avg")
    sub_total_so = fields.Float('Нийт үнэ SO', readonly=True)
    stock_date = fields.Datetime(string='БМ зарлагын огноо', readonly=True)
    scheduled_date = fields.Datetime(string='Борлуулалтын хүргэх огноо', readonly=True)
    state_delivery = fields.Selection([('ontime','On Time'),('overdue','Оverdue'),('backorder','Back Order')],string=u'Ratio')
    picking_id = fields.Many2one('stock.picking', string='БМ зарлагын дугаар', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='БМ зарлагадсан агуулах', readonly=True)
    qty_stock = fields.Float(string='Тоо хэмжээ Агуулах', readonly=True)
    qty_uom = fields.Float(string='Хэмжих нэгж тоо ширхэг', readonly=True)
    price_unit_stock = fields.Float('Нэгж үнэ Агуулах', readonly=True, group_operator="avg")
    sub_total_stock = fields.Float('Нийт үнэ Агуулах', readonly=True)
    total_ashig = fields.Float('Нийт ашиг', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT
                sm.id,
                so.company_id,
                so.id as sale_order_id,
                sol.id as sale_order_line_id,
                so.partner_id,
                so.picking_date as scheduled_date,
                sp.date_done as date_done,
                sm.product_id,
                pt.categ_id,
                pp.default_code,
                so.date_order as sale_date,
                sol.reserved_uom_qty as qty_so,
                case when uu.factor!=0 then sol.reserved_uom_qty/uu.factor else sol.reserved_uom_qty end as qty_uom,
                sol.price_unit as price_unit_so,
                sol.price_total as sub_total_so,
                sp.date_done as stock_date,
                CASE 
                    WHEN (sm.date::TIMESTAMP::DATE - so.picking_date) > 0 AND sol.reserved_uom_qty - sol.qty_delivered = 0 THEN 'overdue' 
                    WHEN (sm.date::TIMESTAMP::DATE - so.picking_date) <= 0 AND sol.reserved_uom_qty - sol.qty_delivered = 0 THEN 'ontime'
                    WHEN sol.reserved_uom_qty - sol.qty_delivered != 0 THEN 'backorder' 
                END as state_delivery,
                sm.picking_id,
                so.warehouse_id,
                sol.qty_delivered as qty_stock,
                sm.price_unit as price_unit_stock,
                sm.price_unit*sm.product_uom_qty as sub_total_stock,
                sol.price_subtotal - (sm.price_unit*sm.product_uom_qty) as total_ashig
            FROM stock_move sm
            LEFT JOIN stock_picking as sp on (sp.id=sm.picking_id)
            LEFT JOIN sale_order_line sol on (sm.sale_line_id=sol.id)
            LEFT JOIN sale_order so on (sol.order_id=so.id)
            LEFT JOIN product_product pp on (pp.id=sm.product_id)
            LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
            LEFT JOIN uom_uom uu on (pt.uom_id=uu.id)
            LEFT JOIN stock_location sl on (sl.id=sm.location_id)
            where sm.state='done' and sm.sale_line_id is not null
            and sl.usage='internal'
        )""" % self._table)
