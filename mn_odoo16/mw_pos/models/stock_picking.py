from odoo.models import Model
from odoo import fields


class StockPicking(Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        res = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        res['price_unit_sale'] = sum(order_lines.mapped('price_subtotal_incl')) / res.get('product_uom_qty')
        return res
