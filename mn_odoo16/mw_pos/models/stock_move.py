from odoo.models import Model
from odoo import api


class StockMove(Model):
    _inherit = 'stock.move'

    @api.depends('picking_id.pos_order_id')
    def _compute_price_unit_sale(self):
        super(StockMove, self)._compute_price_unit_sale()

    def get_other_price(self):
        order_lines = self.picking_id.mapped('pos_order_id.lines').filtered(lambda l: l.product_id == self.product_id)
        if order_lines:
            if self.state in ['done', 'cancel']:
                quantity = self.quantity_done
            elif self.state == 'assigned':
                quantity = self.reserved_availability
            else:
                quantity = self.product_uom_qty
            return sum(order_lines.mapped('price_subtotal_incl')) / quantity
        return super(StockMove, self).get_other_price()
