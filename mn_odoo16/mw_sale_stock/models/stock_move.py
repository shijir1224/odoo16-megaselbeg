from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    price_unit_sale = fields.Float(string=u'Зарах үнэ', compute='_compute_price_unit_sale', store=True)
    sub_total_sale = fields.Float(string=u'Нийт дүн', compute='_compute_price_unit_sale', store=True)
    
    
    @api.depends('sale_line_id.price_unit', 'product_id', 'product_uom_qty', 'quantity_done', 'state')
    def _compute_price_unit_sale(self):
        for item in self:
            if item.sale_line_id:
                price_unit = item.sale_line_id.price_unit
            else:
                price_unit = item.get_other_price()
            item.price_unit_sale = price_unit
            if item.state in ['done', 'cancel']:
                item.sub_total_sale = price_unit * item.quantity_done
            elif item.state == 'assigned':
                item.sub_total_sale = price_unit * item.reserved_availability
            else:
                item.sub_total_sale = price_unit * item.product_uom_qty

    def get_other_price(self):
        return self.product_id.lst_price
