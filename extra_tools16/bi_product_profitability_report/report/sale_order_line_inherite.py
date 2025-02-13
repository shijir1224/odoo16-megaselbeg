# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models

class sale_order_line_inherite(models.Model):
    _inherit = "sale.order.line"

    product_cost = fields.Float(string="Cost",compute="_compute_cost_product",store=True)
    profit = fields.Float(string="Profit",compute="_compute_profit",store=True)
    return_qty = fields.Float(string="Return Quantity",compute="_compute_return_qty",store=True,default=0.0)
    return_rate = fields.Float(string="Return Rate",compute="_compute_return_rate",store=True)
    profitability = fields.Float(string="Profitability",compute="_compute_profitability",store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Sales Value', readonly=True, store=True)
    order_place_date = fields.Datetime(string="Order Date", related='order_id.date_order', store=True)
    discount_amount = fields.Float(string="Dis. Amount",compute="_compute_dis_amount",store=True)
    tax_per = fields.Float(string="Tax %", compute="_compute_per",store=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)

    @api.depends('price_subtotal','tax_id', 'product_uom_qty', 'price_unit',)
    def _compute_per(self):
        for line in self:
            line.update({'tax_per': 0.0})
            if line.tax_id:
                if line.price_unit and line.product_uom_qty:
                    line.update({'tax_per' : ((line.price_tax  * 100)/(line.price_unit * line.product_uom_qty))})


    @api.depends('price_subtotal','discount', 'product_uom_qty', 'price_unit')
    def _compute_dis_amount(self):
        for line in self:
            line.update({'discount_amount' : 0.00})
            if line.discount:
                line.update({'discount_amount' : ((line.price_unit * line.discount)/100) * line.product_uom_qty})

    
    @api.depends('profit','product_cost')
    def _compute_profitability(self):
        for line in self:
            line.update({'profitability' : 0.00})
            if line.product_cost > 0.0:
                line.update({
                    'profitability' : (line.profit/line.product_cost) or 0.00
                    }) 
    
    @api.depends('qty_delivered','return_qty')
    def _compute_return_rate(self):
        for line in self:
            line.update({'return_rate' : 0.00})
            if line.return_qty > 0.0:

                rate =  (line.qty_delivered - line.return_qty)/(line.return_qty)
                line.update({
                    'return_rate' : (rate/100) or 0.00
                })

    @api.depends('qty_delivered')
    def _compute_return_qty(self):
        for line in self:
            picking = self.env['stock.picking'].search([])
            line.update({'return_qty' : 0.00})
            for i in picking:
                if i.origin == line.order_id.name:
                    for j in  i.move_ids_without_package:
                        if j.move_dest_ids:
                            for k in j.move_dest_ids:
                                if k.product_id.id == line.product_id.id and k.state == "done":
                                    line.update({
                                        'return_qty' : (line.return_qty + k.product_uom_qty) or 0.00
                                        })

    
    @api.depends('product_id','product_uom_qty','company_id')
    def _compute_cost_product(self):
        for line in self:
            line.update({
                'product_cost' : (line.product_id.with_company(line.company_id).standard_price * line.product_uom_qty) or 0.00
                })
    
    @api.depends('product_cost','price_subtotal')
    def _compute_profit(self):
        for line in self:
            line.update({
                'profit' : (line.price_subtotal - line.product_cost) or 0.00
            })
