# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    discount_total = fields.Monetary(
        compute="_compute_amount", string="Discount Subtotal", store=True
    )
    price_total_no_discount = fields.Monetary(
        compute="_compute_amount", string="Subtotal Without Discount", store=True
    )
    is_discount_line = fields.Boolean(default=False)

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.discount > 0.0:
            values.update({'discount': 0.0})

        if self.is_discount_line:
            values.update({'quantity': 1})
        return values


    def _update_discount_display_fields(self):
        for line in self:
            line.price_total_no_discount = 0
            line.discount_total = 0
            if not line.discount:
                line.price_total_no_discount = line.price_total
                continue
            price = line.price_unit
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )

            price_total_no_discount = taxes["total_included"]
            discount_total = price_total_no_discount - line.price_total

            line.update(
                {
                    "discount_total": discount_total,
                    "price_total_no_discount": price_total_no_discount,
                }
            )

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_id")
    def _compute_amount(self):
        res = super(SaleOrderLine, self)._compute_amount()
        self._update_discount_display_fields()
        return res
