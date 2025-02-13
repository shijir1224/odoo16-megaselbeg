# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):

    _inherit = "sale.order"

    discount_total = fields.Monetary(
        compute="_compute_discount_total",
        string="Discount Subtotal",
        currency_field="currency_id",
        store=True,
    )
    price_total_no_discount = fields.Monetary(
        compute="_compute_discount_total",
        string="Subtotal Without Discount",
        currency_field="currency_id",
        store=True,
    )

    @api.depends("order_line.discount_total", "order_line.price_total_no_discount")
    def _compute_discount_total(self):
        for order in self:
            discount_total = sum(order.order_line.mapped("discount_total"))
            price_total_no_discount = sum(
                order.order_line.mapped("price_total_no_discount")
            )
            order.update(
                {
                    "discount_total": discount_total,
                    "price_total_no_discount": price_total_no_discount,
                }
            )

    def _prepare_discount_so_line(self, product, amount):
        context = {'lang': self.partner_id.lang}
        # product = self.env['product.product'].browse(34763)
        so_values = {
            'name': product.name,
            'price_unit': -amount,
            'product_uom_qty': 0.0,
            'order_id': self.id,
            'discount': 0.0,
            'product_uom': product.uom_id.id,
            'product_id': product.id,
            'tax_id': [(6, 0, product.taxes_id.ids)],
            'is_discount_line': True,
            'sequence': self.order_line and self.order_line[-1].sequence + 1 or 10,
        }
        del context
        return so_values

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        values = super(SaleOrder, self)._get_invoiceable_lines(final=final)
        so_line_ids = []
        if values:
            discount_accounts = []
            discount_add_line = {}
            discount_total = 0.0
            for line in values:
                # if line.discount > 0.0:
                discount_total += line.discount_total
                so_line_ids.append(line.id)

                if line.discount_total > 0.0:

                    categ_disc_account = line.product_id.categ_id.property_account_income_discount_id
                    if line.product_id.categ_id and categ_disc_account:
                        if categ_disc_account.id in discount_accounts:
                            discount_total0 = discount_add_line[categ_disc_account.id] + line.discount_total
                            discount_add_line.update({categ_disc_account.id: discount_total0})
                        else:
                            discount_add_line.update({categ_disc_account.id: line.discount_total})
                            discount_accounts.append(categ_disc_account.id)
            for disc_line in discount_add_line:
                disc_product = self.env['product.product'].search([('property_account_income_id', '=', disc_line),
                                                    ('detailed_type', '=', 'service')], limit=1)

                if not disc_product:
                    raise ValidationError('%s - ID тай данс дээр бүтээгдэхүүн үүсгээгүй байна.'%(disc_line))

                disc_so_line = self.env['sale.order.line'].create(self._prepare_discount_so_line(disc_product, discount_add_line[disc_line]))
                if disc_so_line:
                    so_line_ids.append(disc_so_line.id)

            # if discount_total > 0.0:
            #     disc_so_line = self.env['sale.order.line'].create(self._prepare_discount_so_line(discount_total))
            #     if disc_so_line:
            #         so_line_ids.append(disc_so_line.id)
        return self.env['sale.order.line'].browse(so_line_ids)

        # down_payment_line_ids = []
        # invoiceable_line_ids = []
        # pending_section = None
        # precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        #
        # for line in self.order_line:
        #     if line.display_type == 'line_section':
        #         # Only invoice the section if one of its lines is invoiceable
        #         pending_section = line
        #         continue
        #     if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
        #         continue
        #     if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
        #         if line.is_downpayment:
        #             # Keep down payment lines separately, to put them together
        #             # at the end of the invoice, in a specific dedicated section.
        #             down_payment_line_ids.append(line.id)
        #             continue
        #         if pending_section:
        #             invoiceable_line_ids.append(pending_section.id)
        #             pending_section = None
        #         invoiceable_line_ids.append(line.id)
        #
        # return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)
