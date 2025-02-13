# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class stock_move(models.Model):

    _inherit = "stock.move"

    # def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
    #     print('================', quantity)
    #     print('================ stock move reserved quant', reserved_quant)
    #     res = super(stock_move, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
    #     if self.location_id.usage == 'supplier' and self.purchase_line_id and self.purchase_line_id.order_id.auto_generated:
    #         res.update({
    #             'lot_id': self.get_lot_id_from_sale_order_picking(self.purchase_line_id.order_id.auto_sale_order_id)
    #         })
    #     return res

    def _action_assign(self):
        # call super
        res = super(stock_move, self)._action_assign()

        # recreate move lines
        for move in self:
            if move.location_id.usage == 'supplier' and move.purchase_line_id and move.purchase_line_id.order_id.auto_generated:
                move.move_line_ids.unlink()
                src_move_lines = move.get_src_move_lines_from_sale_order_picking(move.purchase_line_id.order_id.auto_sale_order_id)
                for src_move_line in src_move_lines:
                    move_line_vals = move._prepare_move_line_vals(quantity=src_move_line.qty_done)
                    move_line_vals.update({
                        'qty_done': src_move_line.qty_done,
                        'lot_id': move.get_lot_id_for_target_company(src_move_line)
                    })
                    self.env['stock.move.line'].create(move_line_vals)
        return res

    def get_src_move_lines_from_sale_order_picking(self, sale_order):
        self.ensure_one()
        stock_move_lines = self.env['stock.move.line']
        out_pickings = sale_order.picking_ids.filtered(lambda x: x.picking_type_code == 'outgoing')
        for picking in out_pickings:
            stock_move_lines |= picking.move_line_ids.filtered(lambda x: x.state == 'done' and x.product_id == self.product_id and not x.move_id.origin_returned_move_id)
        return stock_move_lines

    def get_lot_id_for_target_company(self, src_move_line):
        self.ensure_one()
        lot = src_move_line.lot_id
        if lot:
            if src_move_line.lot_id.company_id != self.company_id:
                lot = self.env['stock.production.lot'].search([
                    ('company_id', '=', self.company_id.id),
                    ('product_id', '=', self.product_id.id),
                    ('name', '=', lot.name)
                ], limit=1)
                if not lot:
                    lot = self.env['stock.production.lot'].create({
                        'company_id': self.company_id.id,
                        'product_id': self.product_id.id,
                        'name': src_move_line.lot_id.name,
                        'life_date': src_move_line.lot_id.life_date,
                        'alert_date': src_move_line.lot_id.alert_date
                    })
        return lot and lot.id or False
