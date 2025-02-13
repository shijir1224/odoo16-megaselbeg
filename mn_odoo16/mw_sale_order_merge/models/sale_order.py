from odoo.models import Model
from odoo import api


class SaleOrder(Model):
    _inherit = 'sale.order'

    @api.model
    def action_sale_order_merge(self):
        active_ids = self.env.context.get('active_ids')
        wizard = self.env['sale.order.merge'].create({'sale_order_ids': active_ids})
        action = self.sudo().env.ref('mw_sale_order_merge.action_sale_order_merge').read()[0]
        action['res_id'] = wizard.id
        return action

    def change_product_pricelist(self):
        for obj in self:
            obj.update_prices()
