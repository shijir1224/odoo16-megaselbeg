# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # expected_date = fields.Date(string=u'Expected date')
    picking_date = fields.Date(string=u'Picking Date')
    picking_datetime = fields.Datetime(string=u'Picking Date')

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     result = super(SaleOrder, self).onchange_partner_id()
    #     # user_id get from current user only
    #     self.update({'user_id': self.env.uid})
    #     # Үнэ дахин бодох
    #     for line in self.order_line:
    #         line.product_id_change()
    #     return result

    @api.model
    def _default_warehouse_id(self):
        if self.company_id and self.env.user.warehouse_id and self.env.user.warehouse_id.company_id == self.company_id:
            return self.env.user.warehouse_id
        else:
            False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id and self.env.user.warehouse_id and self.env.user.warehouse_id.company_id == self.company_id:
            self.warehouse_id = self.env.user.warehouse_id
        else:
            self.warehouse_id = False

    def create_auto_return_invoice(self, picking):
        self.ensure_one()

        invoices = self.env['account.move']
        stock_moves = picking.move_ids.filtered(lambda m: m.quantity_done > 0)

        # Хэрэв MOVE дээр нь sale_line_id байхгүй буюу
        # борлуулалтын буцаалтын хөдөлгөөн биш бол INV үүсгэхгүй болгох
        for move in stock_moves:
            if not move.sale_line_id:
                return False

        return_products = stock_moves.mapped('product_id')

        out_invoices = self.invoice_ids.filtered(lambda i: i.type == 'out_invoice' and i.state == 'posted')

        # get tobe return invoices
        tobe_return_out_invoices = self.env['account.move']
        down_payment_product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        if down_payment_product_id:
            down_payment_product_id = int(down_payment_product_id)
        for out_invoice in out_invoices:
            out_invoice_sale_lines = out_invoice.invoice_line_ids.mapped('sale_line_ids')
            for out_invoice_sale_line in out_invoice_sale_lines:
                if out_invoice_sale_line.product_id.id != down_payment_product_id and out_invoice_sale_line.product_id in return_products:
                    tobe_return_out_invoices |= out_invoice
                    break

        for tobe_return_out_invoice in tobe_return_out_invoices:
            context = {
                "active_model": 'account.move',
                "active_ids": tobe_return_out_invoice.ids
            }
            reversal = self.env['account.move.reversal'].with_context(context).create({})
            action = reversal.reverse_moves()
            if action:
                invoice = self.env['account.move'].browse(action.get('res_id'))
                invoices |= invoice

                # compute qty
                invoice_lines = self.env['account.move.line']
                for stock_move in stock_moves:
                    exist_invoice_line = invoice.invoice_line_ids.filtered(lambda il: stock_move.sale_line_id in il.sale_line_ids)
                    if stock_move.product_uom == stock_move.sale_line_id.product_uom:
                        qty = stock_move.quantity_done
                    else:
                        qty = stock_move.product_uom._compute_quantity(stock_move.quantity_done, stock_move.sale_line_id.product_uom)
                    exist_invoice_line.with_context(check_move_validity=False).write({'quantity': qty})
                    invoice_lines |= exist_invoice_line

                invoice.with_context(check_move_validity=False).write({'invoice_line_ids': [(6, 0, invoice_lines.ids)]})

        return invoices

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    expected_date = fields.Date(related = "order_id.picking_date", string=u'Expected date')