from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # @api.model_create_multi
    #test
    # def create(self, vals_list):
    #     lines = super(SaleOrderLine, self).create(vals_list)
    #     lines.filtered(lambda line: line.state == 'sale')._action_launch_stock_rule()
    #     return lines
    amount_total_sale = fields.Float(string=u'Дэд дүн', compute='_compute_price_unit_sale', store=True)

    @api.depends('move_ids.sub_total_sale')
    def _compute_price_unit_sale(self):
        for item in self:
            if not item.sale_id:
                item.amount_total_sale = 0
                continue
            item.amount_total_sale = sum(item.move_ids.mapped('sub_total_sale'))

    def action_view_sale_order(self):
        view = self.env.ref('sale.view_order_form')

        return {
            'name': 'Борлуулалтын захиалга',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            # 'target': 'new',
            'res_id': self.sale_id.id,
            'context': dict(
                self.env.context

            ),
        }

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for picking in self:
            # Буцаалтын нэхэмжлэх үүсгэх
            if picking.picking_type_id.code == 'incoming':
                if picking.sale_id and picking.sale_id.company_id.auto_create_return_invoice:
                    invoices = picking.sale_id.create_auto_return_invoice(picking)
                    if invoices and picking.sale_id.company_id.auto_validate_return_invoice:
                        invoices.action_post()
        return res
