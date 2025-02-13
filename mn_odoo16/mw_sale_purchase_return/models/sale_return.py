# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _, tools
from odoo.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class SaleReturn(models.Model):
    _inherit = 'sale.return'

    company_partner_id = fields.Many2one('res.partner', related='company_id.partner_id')
    is_create_from_inter_company = fields.Boolean(compute='_compute_is_create_from_inter_company', string='Дотоод буцаалт эсэх', store=True)
    purchase_return_id = fields.Many2one('purchase.return', 'ХА-н буцаалт')
    src_warehouse_id = fields.Many2one('stock.warehouse', related='purchase_return_id.warehouse_id', string='Буцаасан агуулах')

    @api.depends('partner_id')
    def _compute_is_create_from_inter_company(self):
        for rs in self:
            company = self.env['res.company']._find_company_from_partner(rs.partner_id.id)
            if company:
                rs.is_create_from_inter_company = True
            else:
                rs.is_create_from_inter_company = False

    @api.onchange('is_create_from_inter_company')
    def onchange_is_create_from_inter_company(self):
        if not self.is_create_from_inter_company:
            self.purchase_return_id = False

    def write(self, vals):
        res = super(SaleReturn, self).write(vals)
        if 'purchase_return_id' in vals:
            self.return_line.unlink()
        return res

    def import_purchase_return(self):
        self.ensure_one()
        self.return_line.unlink()
        pickings = self.env['stock.picking'].search([
            ('purchase_return_id', '=', self.purchase_return_id.id),
            ('state', '=', 'done')
        ])
        for picking in pickings:
            for move_line in picking.move_line_ids:
                delivered_qty = 0
                other_delivered_sale_return_line_ids = move_line.delivered_sale_return_line_ids.filtered(lambda x: x.return_id != self)
                for srl in other_delivered_sale_return_line_ids:
                    if move_line.product_uom_id == srl.product_uom:
                        delivered_qty += move_line.qty_done
                    else:
                        delivered_qty += srl.product_uom._compute_quantity(srl.qty, move_line.product_uom_id, round=False)
                qty = move_line.qty_done - delivered_qty
                if qty > 0:
                    prl = move_line.move_id.purchase_return_line_id
                    if prl.product_uom != move_line.product_uom_id:
                        qty = move_line.product_uom_id._compute_quantity(qty, prl.product_uom, round=False)
                    lot_id = False
                    if move_line.lot_id:
                        lot_id = self.env['stock.production.lot'].search([
                            ('company_id', '=', self.company_id.id),
                            ('name', '=', move_line.lot_id.name),
                            ('product_id', '=', move_line.product_id.id)
                        ], limit=1)
                        if not lot_id:
                            lot_id = self.env['stock.production.lot'].create({
                                'company_id': self.company_id.id,
                                'name': move_line.lot_id.name,
                                'product_id': move_line.product_id.id,
                                'life_date': move_line.lot_id.life_date,
                                'alert_date': move_line.lot_id.alert_date
                            })
                    self.env['sale.return.line'].create({
                        'return_id': self.id,
                        'product_id': move_line.product_id.id,
                        'qty': qty,
                        'product_uom': prl.product_uom.id,
                        'lot_id': lot_id and lot_id.id or False,
                        'taxes_id': [(6, 0, self.taxes_id.ids)],
                        'purchase_return_line_id': prl.id,
                        'purchase_return_stock_move_line': move_line.id
                    })
        self.return_line._compute_price_unit()


class SaleReturnLine(models.Model):
    _inherit = 'sale.return.line'

    purchase_return_line_id = fields.Many2one('purchase.return.line', 'ХА-н буцаалтын мөр')
    purchase_return_stock_move_line = fields.Many2one('stock.move.line', 'ХА-н буцаалтын зарлагын мөр')

    @api.onchange('product_id', 'taxes_id', 'sale_line_id', 'product_uom')
    def _compute_price_unit(self):
        res = super(SaleReturnLine, self)._compute_price_unit()
        # TODO: tax price_include calculation missing for all price
        for line in self:
            if line.purchase_return_line_id:
                price_unit = line.purchase_return_line_id.price_unit
                if line.purchase_return_line_id.taxes_id:
                    price_unit = line.purchase_return_line_id.taxes_id.with_context(round=False).compute_all(
                        price_unit,
                        currency=line.purchase_return_line_id.return_id.currency_id,
                        quantity=1.0
                    )['total_included']

                # update list price according uom
                if line.purchase_return_line_id:
                    if line.product_uom and line.product_uom != line.purchase_return_line_id.product_uom:
                        price_unit *= line.purchase_return_line_id.product_uom.factor / line.product_uom.factor
                else:
                    if line.product_uom and line.product_uom != line.product_id.uom_id:
                        price_unit *= line.product_id.uom_id.factor / line.product_uom.factor

                # calculate tax
                if line.taxes_id:
                    price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.return_id.currency_id, quantity=1.0)['total_included']

                line.price_unit = price_unit

        return res

    def get_current_cost(self):
        cost = super(SaleReturnLine, self).get_current_cost()
        if not cost and self.purchase_return_line_id:
            cost = self.price_unit
            if self.purchase_return_line_id.taxes_id:
                cost = self.purchase_return_line_id.taxes_id.with_context(round=False).compute_all(
                    cost,
                    currency=self.purchase_return_line_id.return_id.currency_id,
                    quantity=1.0
                )['total_excluded']
        return cost
